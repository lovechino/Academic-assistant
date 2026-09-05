"""Measure reranker precision and batch-shape sensitivity on a frozen, qrel-free probe."""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
import platform
import statistics
import sys
import time


ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
CONFIG = HERE / "stability-config-v0.1.json"
CORPUS_DEFAULT = ROOT / "data/processed/voer-dsa-dense-r2-v0.1/corpus.json"
HYBRID_DEFAULT = ROOT / "data/processed/voer-dsa-retrieval-r3-v0.1/hybrid-results.json"
MODEL_DEFAULT = ROOT / "tmp/models/bge-reranker-v2-m3-953dc6f6f85a1b2dbfca4c34a2796e7dde08d41e"
OUTPUT_DEFAULT = ROOT / "data/processed/voer-dsa-retrieval-r4-v0.1/stability-results.json"


def digest(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def file_digest(path: Path) -> str:
    hasher = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(8 * 1024 * 1024), b""):
            hasher.update(block)
    return hasher.hexdigest()


def require(ok: bool, code: str) -> None:
    if not ok:
        raise ValueError(code)


def score(model, tokenizer, rows: list[dict], max_tokens: int, batch_size: int, label: str) -> tuple[dict, dict]:
    import torch

    scores: dict[tuple[str, str], float] = {}
    lengths: list[int] = []
    truncated = 0
    started = time.perf_counter()
    for offset in range(0, len(rows), batch_size):
        batch = rows[offset:offset + batch_size]
        queries = [row["query"] for row in batch]
        passages = [row["passage"] for row in batch]
        for query, passage in zip(queries, passages):
            pair_length = len(tokenizer(query, passage, add_special_tokens=True, truncation=False)["input_ids"])
            lengths.append(pair_length)
            truncated += pair_length > max_tokens
        inputs = tokenizer(
            queries,
            passages,
            padding=True,
            truncation="only_second",
            max_length=max_tokens,
            return_tensors="pt",
        )
        with torch.inference_mode():
            logits = model(**inputs, return_dict=True).logits.view(-1).float().cpu().tolist()
        for row, value in zip(batch, logits):
            scores[(row["case_id"], row["chunk_id"])] = float(value)
        completed = min(offset + batch_size, len(rows))
        if completed % 20 == 0 or completed == len(rows):
            print(f"{label}: {completed}/{len(rows)}", file=sys.stderr, flush=True)
    return scores, {
        "pairs": len(rows),
        "seconds": round(time.perf_counter() - started, 3),
        "batch_size": batch_size,
        "original_pair_tokens_min": min(lengths),
        "original_pair_tokens_max": max(lengths),
        "pairs_truncated": truncated,
    }


def ranked_ids(case_rows: list[dict], scores: dict) -> list[str]:
    return [
        row["chunk_id"]
        for row in sorted(
            case_rows,
            key=lambda row: (-scores[(row["case_id"], row["chunk_id"])], row["rrf_rank"], row["chunk_id"]),
        )
    ]


def rank_agreement(left: list[str], right: list[str]) -> dict:
    require(set(left) == set(right), "rank_sets_differ")
    right_pos = {chunk_id: index for index, chunk_id in enumerate(right)}
    inversions = 0
    pairs = 0
    for i in range(len(left)):
        for j in range(i + 1, len(left)):
            pairs += 1
            inversions += right_pos[left[i]] > right_pos[left[j]]
    kendall_tau = 1.0 if pairs == 0 else 1.0 - 2.0 * inversions / pairs
    return {
        "top1_same": left[:1] == right[:1],
        "top3_overlap": len(set(left[:3]) & set(right[:3])) / min(3, len(left)),
        "top5_overlap": len(set(left[:5]) & set(right[:5])) / min(5, len(left)),
        "pairwise_inversions": inversions,
        "kendall_tau": kendall_tau,
    }


def compare(left: dict, right: dict, rows_by_case: dict[str, list[dict]]) -> dict:
    deltas = {key: abs(left[key] - right[key]) for key in left}
    per_case = {}
    for case_id, rows in rows_by_case.items():
        agreement = rank_agreement(ranked_ids(rows, left), ranked_ids(rows, right))
        agreement["max_abs_score_delta"] = max(deltas[(case_id, row["chunk_id"])] for row in rows)
        per_case[case_id] = agreement
    values = list(deltas.values())
    return {
        "score_delta": {
            "mean_abs": statistics.fmean(values),
            "median_abs": statistics.median(values),
            "max_abs": max(values),
        },
        "ranking": {
            "queries": len(per_case),
            "top1_same_queries": sum(row["top1_same"] for row in per_case.values()),
            "mean_top3_overlap": statistics.fmean(row["top3_overlap"] for row in per_case.values()),
            "mean_top5_overlap": statistics.fmean(row["top5_overlap"] for row in per_case.values()),
            "mean_kendall_tau": statistics.fmean(row["kendall_tau"] for row in per_case.values()),
            "total_pairwise_inversions": sum(row["pairwise_inversions"] for row in per_case.values()),
        },
        "per_case": per_case,
    }


def build(corpus_path: Path, hybrid_path: Path, model_dir: Path, output_path: Path) -> dict:
    import torch
    import tokenizers
    import transformers
    from transformers import AutoModelForSequenceClassification, AutoTokenizer

    config_bytes = CONFIG.read_bytes()
    config = json.loads(config_bytes)
    corpus_bytes = corpus_path.read_bytes()
    corpus = json.loads(corpus_bytes)
    hybrid_bytes = hybrid_path.read_bytes()
    hybrid = json.loads(hybrid_bytes)
    require(torch.__version__.split("+")[0] == config["runtime"]["torch"], "torch_version_mismatch")
    require(transformers.__version__ == config["runtime"]["transformers"], "transformers_version_mismatch")
    require(tokenizers.__version__ == config["runtime"]["tokenizers"], "tokenizers_version_mismatch")
    require(hybrid["inputs"]["corpus_sha256"] == digest(corpus_bytes), "hybrid_corpus_hash_mismatch")

    weights = model_dir / config["model"]["weights_file"]
    require(weights.stat().st_size == config["model"]["weights_size"], "weights_size_mismatch")
    require(file_digest(weights) == config["model"]["weights_sha256"], "weights_hash_mismatch")
    torch.set_num_threads(config["runtime"]["threads"])
    torch.set_num_interop_threads(1)
    torch.use_deterministic_algorithms(True)

    tokenizer = AutoTokenizer.from_pretrained(model_dir, local_files_only=True, use_fast=True)
    load_started = time.perf_counter()
    f32_model = AutoModelForSequenceClassification.from_pretrained(
        model_dir, local_files_only=True, dtype=torch.float32
    ).eval()
    model_load_seconds = round(time.perf_counter() - load_started, 3)

    chunks = {row["chunk_id"]: row for row in corpus["chunks"] if row["embedding_eligible"]}
    stage = hybrid["stages"][config["candidate_source"]["stage"]]["candidate_rankings"]
    take = config["candidate_source"]["candidates_per_query"]
    selections: list[dict] = []
    rows_by_case: dict[str, list[dict]] = {}
    for case in corpus["cases"]:
        source_rows = stage[case["case_id"]][:take]
        require(len(source_rows) == take, "probe_pool_too_small:" + case["case_id"])
        rows_by_case[case["case_id"]] = []
        for row in source_rows:
            selected = {
                "case_id": case["case_id"],
                "query": case["query"],
                "chunk_id": row["chunk_id"],
                "rrf_rank": row["rank"],
                "passage": chunks[row["chunk_id"]]["embedding_text"],
            }
            selections.append(selected)
            rows_by_case[case["case_id"]].append(selected)

    scores = {}
    timings = {}
    scores["f32_b1"], timings["f32_b1"] = score(
        f32_model, tokenizer, selections, config["model"]["max_pair_tokens"], 1, "f32_b1"
    )
    scores["f32_b4"], timings["f32_b4"] = score(
        f32_model, tokenizer, selections, config["model"]["max_pair_tokens"], 4, "f32_b4"
    )
    repeated_rows = selections[:config["reproducibility_probe_pairs"]]
    f32_repeat, _ = score(f32_model, tokenizer, repeated_rows, config["model"]["max_pair_tokens"], 4, "f32_repeat")
    f32_repeat_delta = max(abs(scores["f32_b4"][key] - value) for key, value in f32_repeat.items())

    quantize_started = time.perf_counter()
    int8_model = torch.ao.quantization.quantize_dynamic(f32_model, {torch.nn.Linear}, dtype=torch.qint8).eval()
    quantization_seconds = round(time.perf_counter() - quantize_started, 3)
    scores["int8_b1"], timings["int8_b1"] = score(
        int8_model, tokenizer, selections, config["model"]["max_pair_tokens"], 1, "int8_b1"
    )
    scores["int8_b4"], timings["int8_b4"] = score(
        int8_model, tokenizer, selections, config["model"]["max_pair_tokens"], 4, "int8_b4"
    )
    int8_repeat, _ = score(int8_model, tokenizer, repeated_rows, config["model"]["max_pair_tokens"], 4, "int8_repeat")
    int8_repeat_delta = max(abs(scores["int8_b4"][key] - value) for key, value in int8_repeat.items())

    comparisons = {
        "batch_shape_f32_b1_vs_b4": compare(scores["f32_b1"], scores["f32_b4"], rows_by_case),
        "batch_shape_int8_b1_vs_b4": compare(scores["int8_b1"], scores["int8_b4"], rows_by_case),
        "precision_f32_vs_int8_b1": compare(scores["f32_b1"], scores["int8_b1"], rows_by_case),
        "precision_f32_vs_int8_b4": compare(scores["f32_b4"], scores["int8_b4"], rows_by_case),
    }
    serializable_scores = {
        variant: {
            case_id: {row["chunk_id"]: variant_scores[(case_id, row["chunk_id"])] for row in rows}
            for case_id, rows in rows_by_case.items()
        }
        for variant, variant_scores in scores.items()
    }
    result = {
        "run_id": config["experiment_id"] + "-run-001",
        "status": "completed_local_numerical_stability_probe",
        "config": config,
        "config_sha256": digest(config_bytes),
        "implementation_sha256": digest(Path(__file__).read_bytes()),
        "inputs": {"corpus_sha256": digest(corpus_bytes), "hybrid_results_sha256": digest(hybrid_bytes)},
        "probe": {
            "selection_rule": "first N RRF-depth-80 candidates per query; qrels unavailable to selection",
            "queries": len(rows_by_case),
            "pairs": len(selections),
            "candidate_ids": {case_id: [row["chunk_id"] for row in rows] for case_id, rows in rows_by_case.items()},
        },
        "runtime": {
            "python": platform.python_version(),
            "torch": torch.__version__,
            "transformers": transformers.__version__,
            "tokenizers": tokenizers.__version__,
            "device": "cpu",
            "threads": config["runtime"]["threads"],
            "model_load_seconds": model_load_seconds,
            "quantization_seconds": quantization_seconds,
            "timings": timings,
        },
        "same_variant_repeat_max_abs_delta": {"f32_b4": f32_repeat_delta, "int8_b4": int8_repeat_delta},
        "comparisons": comparisons,
        "scores": serializable_scores,
        "interpretation_limits": [
            "this probe isolates score/rank sensitivity on 80 frozen pairs and is not an end-to-end accuracy evaluation",
            "candidate selection uses no qrels; no thresholds were tuned from relevance labels",
            "agreement on this small development corpus does not establish stability on other hardware or corpora",
        ],
    }
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--corpus", type=Path, default=CORPUS_DEFAULT)
    parser.add_argument("--hybrid", type=Path, default=HYBRID_DEFAULT)
    parser.add_argument("--model-dir", type=Path, default=MODEL_DEFAULT)
    parser.add_argument("--output", type=Path, default=OUTPUT_DEFAULT)
    args = parser.parse_args()
    result = build(args.corpus.resolve(), args.hybrid.resolve(), args.model_dir.resolve(), args.output.resolve())
    print(json.dumps({
        "output": args.output.resolve().relative_to(ROOT).as_posix(),
        "probe": result["probe"],
        "same_variant_repeat_max_abs_delta": result["same_variant_repeat_max_abs_delta"],
        "comparisons": result["comparisons"],
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
