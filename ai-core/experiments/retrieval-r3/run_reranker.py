"""Rerank frozen RRF candidates with local BGE reranker v2 M3 on CPU."""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import platform
import sys
import time


ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
CONFIG = HERE / "reranker-config-v0.1.json"
R2_RUNNER = ROOT / "ai-core/experiments/dense-retrieval-r2/run_dense_retrieval.py"
CORPUS_DEFAULT = ROOT / "data/processed/voer-dsa-dense-r2-v0.1/corpus.json"
HYBRID_DEFAULT = ROOT / "data/processed/voer-dsa-retrieval-r3-v0.1/hybrid-results.json"
MODEL_DEFAULT = ROOT / "tmp/models/bge-reranker-v2-m3-953dc6f6f85a1b2dbfca4c34a2796e7dde08d41e"
OUTPUT_DEFAULT = ROOT / "data/processed/voer-dsa-retrieval-r3-v0.1/reranker-results.json"


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


def load_r2_runner():
    spec = importlib.util.spec_from_file_location("retrieval_r3_r2_runner_for_rerank", R2_RUNNER)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def score_candidates(model, tokenizer, selections: list[dict], max_tokens: int, batch_size: int) -> tuple[dict, dict]:
    """This function receives candidate IDs/text only and has no qrel/evaluator input."""
    import torch

    scores = {}
    lengths = []
    truncated = 0
    started = time.perf_counter()
    completed = 0
    for offset in range(0, len(selections), batch_size):
        batch = selections[offset:offset + batch_size]
        queries = [row["query"] for row in batch]
        passages = [row["passage"] for row in batch]
        for query, passage in zip(queries, passages):
            original = tokenizer(query, passage, add_special_tokens=True, truncation=False)["input_ids"]
            lengths.append(len(original))
            truncated += len(original) > max_tokens
        inputs = tokenizer(queries, passages, padding=True, truncation="only_second", max_length=max_tokens,
                           return_tensors="pt")
        with torch.inference_mode():
            logits = model(**inputs, return_dict=True).logits.view(-1).float().cpu().tolist()
        for row, score in zip(batch, logits):
            scores[(row["case_id"], row["chunk_id"])] = float(score)
        completed += len(batch)
        if completed % 20 == 0 or completed == len(selections):
            print(f"reranker scored {completed}/{len(selections)} pairs", file=sys.stderr, flush=True)
    return scores, {
        "pairs": len(selections),
        "seconds": round(time.perf_counter() - started, 3),
        "original_pair_tokens_min": min(lengths),
        "original_pair_tokens_max": max(lengths),
        "pairs_truncated": truncated,
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
    model_config = model_dir / "config.json"
    tokenizer_file = model_dir / "tokenizer.json"
    require(weights.stat().st_size == config["model"]["weights_size"], "weights_size_mismatch")
    require(file_digest(weights) == config["model"]["weights_sha256"], "weights_hash_mismatch")
    require(file_digest(model_config) == config["model"]["config_file_sha256"], "model_config_hash_mismatch")
    require(file_digest(tokenizer_file) == config["model"]["tokenizer_file_sha256"], "tokenizer_hash_mismatch")

    torch.set_num_threads(config["runtime"]["threads"])
    torch.set_num_interop_threads(1)
    torch.use_deterministic_algorithms(True)
    load_started = time.perf_counter()
    tokenizer = AutoTokenizer.from_pretrained(model_dir, local_files_only=True, use_fast=True)
    model = AutoModelForSequenceClassification.from_pretrained(
        model_dir, local_files_only=True, dtype=torch.float32
    )
    model.eval()
    model_load_seconds = round(time.perf_counter() - load_started, 3)
    parameter_count = sum(parameter.numel() for parameter in model.parameters())
    quantize_started = time.perf_counter()
    model = torch.ao.quantization.quantize_dynamic(model, {torch.nn.Linear}, dtype=torch.qint8)
    model.eval()
    quantization_seconds = round(time.perf_counter() - quantize_started, 3)

    chunks = {row["chunk_id"]: row for row in corpus["chunks"] if row["embedding_eligible"]}
    source_stage = hybrid["stages"][config["candidate_source"]["stage"]]["candidate_rankings"]
    maximum_pool = max(config["candidate_source"]["nested_pool_sizes"])
    selections = []
    candidate_rows = {}
    for case in corpus["cases"]:
        rows = source_stage[case["case_id"]][:maximum_pool]
        require(len(rows) == maximum_pool, "candidate_pool_too_small:" + case["case_id"])
        require(len({row["chunk_id"] for row in rows}) == maximum_pool, "duplicate_candidate:" + case["case_id"])
        candidate_rows[case["case_id"]] = rows
        selections.extend({
            "case_id": case["case_id"],
            "query": case["query"],
            "chunk_id": row["chunk_id"],
            "passage": chunks[row["chunk_id"]]["embedding_text"],
        } for row in rows)

    scores, scoring = score_candidates(
        model, tokenizer, selections, config["model"]["max_pair_tokens"], config["model"]["batch_size"]
    )
    first = selections[0]
    repeated, _ = score_candidates(model, tokenizer, [first], config["model"]["max_pair_tokens"], 1)
    deterministic_delta = abs(scores[(first["case_id"], first["chunk_id"])] -
                              repeated[(first["case_id"], first["chunk_id"])] )

    runner = load_r2_runner()
    stages = {}
    cutoffs = config["evaluation"]["cutoffs"]
    for pool_size in config["candidate_source"]["nested_pool_sizes"]:
        rankings = {}
        for case in corpus["cases"]:
            rows = candidate_rows[case["case_id"]][:pool_size]
            reranked = []
            for row in rows:
                reranked.append({
                    "chunk_id": row["chunk_id"],
                    "document_id": row["document_id"],
                    "reranker_score": scores[(case["case_id"], row["chunk_id"])],
                    "rrf_rank": row["rank"],
                    "rrf_score": row["rrf_score"],
                    "dense_rank": row["dense_rank"],
                    "bm25_rank": row["bm25_rank"],
                    "embedding_tokens": row["embedding_tokens"],
                    "preview": row["preview"],
                })
            reranked.sort(key=lambda row: (-row["reranker_score"], row["rrf_rank"], row["chunk_id"]))
            for rank, row in enumerate(reranked, 1):
                row["rank"] = rank
            rankings[case["case_id"]] = reranked
        metrics, per_case = runner.evaluate(corpus["cases"], rankings, cutoffs)
        before_metrics, _ = runner.evaluate(
            corpus["cases"], {case_id: rows[:pool_size] for case_id, rows in candidate_rows.items()}, [pool_size]
        )
        stages["reranker_pool_" + str(pool_size)] = {
            "candidate_pool_metrics_before_rerank": before_metrics[str(pool_size)],
            "metrics": metrics,
            "cases": per_case,
            "rankings": rankings,
        }

    result = {
        "run_id": config["experiment_id"] + "-run-001",
        "status": "completed_local_cross_encoder_rerank_only",
        "config": config,
        "config_sha256": digest(config_bytes),
        "implementation_sha256": digest(Path(__file__).read_bytes()),
        "inputs": {"corpus_sha256": digest(corpus_bytes), "hybrid_results_sha256": digest(hybrid_bytes)},
        "model": {
            "weights_sha256": file_digest(weights),
            "weights_size": weights.stat().st_size,
            "source_parameters": parameter_count,
            "runtime_precision": config["model"]["runtime_precision"],
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
            "scoring": scoring,
            "deterministic_probe_abs_delta": deterministic_delta,
        },
        "stages": stages,
        "limitations": [
            "qrels are assistant-silver and enter only after all candidate scores and rankings exist",
            "pool sizes are sensitivity diagnostics on the same ten dev queries, not a tuned production choice",
            "the reranker scores relevance of one passage at a time and does not guarantee multi-evidence completeness",
            "no context expansion, packing, generation or image understanding is included",
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
        "runtime": result["runtime"],
        "metrics": {stage: value["metrics"] for stage, value in result["stages"].items()},
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
