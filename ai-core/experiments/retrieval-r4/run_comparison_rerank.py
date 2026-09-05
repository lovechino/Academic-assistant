"""Rerank comparison branches, merge them fairly, then evaluate the frozen ranking."""
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
CONFIG = HERE / "comparison-config-v0.1.json"
R2_RUNNER = ROOT / "ai-core/experiments/dense-retrieval-r2/run_dense_retrieval.py"
R3_CONFIG = ROOT / "ai-core/experiments/retrieval-r3/reranker-config-v0.1.json"
CORPUS_DEFAULT = ROOT / "data/processed/voer-dsa-dense-r2-v0.1/corpus.json"
BRANCHES_DEFAULT = ROOT / "data/processed/voer-dsa-retrieval-r4-v0.1/comparison-branches.json"
BASELINE_DEFAULT = ROOT / "data/processed/voer-dsa-retrieval-r3-v0.1/reranker-results.json"
MODEL_DEFAULT = ROOT / "tmp/models/bge-reranker-v2-m3-953dc6f6f85a1b2dbfca4c34a2796e7dde08d41e"
OUTPUT_DEFAULT = ROOT / "data/processed/voer-dsa-retrieval-r4-v0.1/comparison-results.json"


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
    spec = importlib.util.spec_from_file_location("retrieval_r4_r2_evaluator", R2_RUNNER)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def score(model, tokenizer, rows: list[dict], max_tokens: int, batch_size: int) -> tuple[dict, dict]:
    import torch

    scores = {}
    lengths = []
    truncated = 0
    started = time.perf_counter()
    for offset in range(0, len(rows), batch_size):
        batch = rows[offset:offset + batch_size]
        queries = [row["query"] for row in batch]
        passages = [row["passage"] for row in batch]
        for query, passage in zip(queries, passages):
            length = len(tokenizer(query, passage, add_special_tokens=True, truncation=False)["input_ids"])
            lengths.append(length)
            truncated += length > max_tokens
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
            scores[(row["case_id"], row["branch_id"], row["chunk_id"])] = float(value)
        completed = min(offset + batch_size, len(rows))
        if completed % 20 == 0 or completed == len(rows):
            print(f"comparison reranker: {completed}/{len(rows)}", file=sys.stderr, flush=True)
    return scores, {
        "pairs": len(rows),
        "seconds": round(time.perf_counter() - started, 3),
        "original_pair_tokens_min": min(lengths),
        "original_pair_tokens_max": max(lengths),
        "pairs_truncated": truncated,
    }


def merge_round_robin(branch_order: list[str], rankings: dict[str, list[dict]], depth: int) -> list[dict]:
    pointers = {branch_id: 0 for branch_id in branch_order}
    merged: list[dict] = []
    by_chunk: dict[str, dict] = {}
    while len(merged) < depth:
        progressed = False
        for branch_id in branch_order:
            rows = rankings[branch_id]
            if pointers[branch_id] >= len(rows):
                continue
            progressed = True
            row = rows[pointers[branch_id]]
            pointers[branch_id] += 1
            existing = by_chunk.get(row["chunk_id"])
            if existing is not None:
                if branch_id not in existing["branch_ids"]:
                    existing["branch_ids"].append(branch_id)
                existing["branch_ranks"][branch_id] = row["branch_rank"]
                existing["branch_scores"][branch_id] = row["reranker_score"]
                continue
            merged_row = {
                "chunk_id": row["chunk_id"],
                "document_id": row["document_id"],
                "branch_ids": [branch_id],
                "branch_ranks": {branch_id: row["branch_rank"]},
                "branch_scores": {branch_id: row["reranker_score"]},
                "embedding_tokens": row["embedding_tokens"],
                "preview": row["preview"],
            }
            merged.append(merged_row)
            by_chunk[row["chunk_id"]] = merged_row
            if len(merged) >= depth:
                break
        if not progressed:
            break
    for rank, row in enumerate(merged, 1):
        row["rank"] = rank
    return merged


def build(corpus_path: Path, branches_path: Path, baseline_path: Path, model_dir: Path, output_path: Path) -> dict:
    import torch
    import tokenizers
    import transformers
    from transformers import AutoModelForSequenceClassification, AutoTokenizer

    config_bytes = CONFIG.read_bytes()
    config = json.loads(config_bytes)
    r3_config = json.loads(R3_CONFIG.read_text(encoding="utf-8"))
    corpus_bytes = corpus_path.read_bytes()
    corpus = json.loads(corpus_bytes)
    branches_bytes = branches_path.read_bytes()
    branches = json.loads(branches_bytes)
    baseline_bytes = baseline_path.read_bytes()
    baseline = json.loads(baseline_bytes)
    require(branches["config_sha256"] == digest(config_bytes), "branch_config_hash_mismatch")
    require(branches["inputs"]["corpus_sha256"] == digest(corpus_bytes), "branch_corpus_hash_mismatch")
    require(baseline["inputs"]["corpus_sha256"] == digest(corpus_bytes), "baseline_corpus_hash_mismatch")
    require(torch.__version__.split("+")[0] == r3_config["runtime"]["torch"], "torch_version_mismatch")
    require(transformers.__version__ == r3_config["runtime"]["transformers"], "transformers_version_mismatch")
    require(tokenizers.__version__ == r3_config["runtime"]["tokenizers"], "tokenizers_version_mismatch")

    weights = model_dir / r3_config["model"]["weights_file"]
    require(weights.stat().st_size == r3_config["model"]["weights_size"], "weights_size_mismatch")
    require(file_digest(weights) == r3_config["model"]["weights_sha256"], "weights_hash_mismatch")
    torch.set_num_threads(r3_config["runtime"]["threads"])
    torch.set_num_interop_threads(1)
    torch.use_deterministic_algorithms(True)
    load_started = time.perf_counter()
    tokenizer = AutoTokenizer.from_pretrained(model_dir, local_files_only=True, use_fast=True)
    model = AutoModelForSequenceClassification.from_pretrained(
        model_dir, local_files_only=True, dtype=torch.float32
    ).eval()
    model_load_seconds = round(time.perf_counter() - load_started, 3)
    quantize_started = time.perf_counter()
    model = torch.ao.quantization.quantize_dynamic(model, {torch.nn.Linear}, dtype=torch.qint8).eval()
    quantization_seconds = round(time.perf_counter() - quantize_started, 3)

    chunks = {row["chunk_id"]: row for row in corpus["chunks"] if row["embedding_eligible"]}
    selections = []
    branch_order_by_case = {}
    for case_id in branches["selected_case_ids"]:
        branch_order = [row["branch_id"] for row in branches["decomposition_audit"][case_id]["branches"]]
        branch_order_by_case[case_id] = branch_order
        for branch_id in branch_order:
            branch = branches["branches"][case_id][branch_id]
            candidates = branch["candidates"]
            require(len(candidates) == config["retrieval"]["candidate_pool_per_branch"],
                    "branch_candidate_pool_too_small:" + case_id + ":" + branch_id)
            for row in candidates:
                selections.append({
                    "case_id": case_id,
                    "branch_id": branch_id,
                    "query": branch["query"],
                    "chunk_id": row["chunk_id"],
                    "passage": chunks[row["chunk_id"]]["embedding_text"],
                })
    scores, scoring_runtime = score(
        model,
        tokenizer,
        selections,
        config["reranker"]["max_pair_tokens"],
        config["reranker"]["batch_size"],
    )

    branch_rankings = {}
    merged_rankings = {}
    coverage_gates = {}
    for case_id in branches["selected_case_ids"]:
        branch_rankings[case_id] = {}
        for branch_id in branch_order_by_case[case_id]:
            ranked = []
            for candidate in branches["branches"][case_id][branch_id]["candidates"]:
                ranked.append({
                    "chunk_id": candidate["chunk_id"],
                    "document_id": candidate["document_id"],
                    "reranker_score": scores[(case_id, branch_id, candidate["chunk_id"])],
                    "branch_rrf_rank": candidate["rank"],
                    "embedding_tokens": candidate["embedding_tokens"],
                    "preview": candidate["preview"],
                })
            ranked.sort(key=lambda row: (-row["reranker_score"], row["branch_rrf_rank"], row["chunk_id"]))
            for rank, row in enumerate(ranked, 1):
                row["branch_rank"] = rank
            branch_rankings[case_id][branch_id] = ranked
        merged = merge_round_robin(
            branch_order_by_case[case_id],
            branch_rankings[case_id],
            config["merge"]["output_depth"],
        )
        merged_rankings[case_id] = merged
        expected = set(branch_order_by_case[case_id])
        coverage_gates[case_id] = {}
        for cutoff in config["merge"]["coverage_gate_cutoffs"]:
            observed = {branch_id for row in merged[:cutoff] for branch_id in row["branch_ids"]}
            coverage_gates[case_id][str(cutoff)] = {
                "passed": observed == expected,
                "expected_branch_ids": sorted(expected),
                "observed_branch_ids": sorted(observed),
            }

    baseline_rankings = baseline["stages"]["reranker_pool_40"]["rankings"]
    combined_rankings = {
        case["case_id"]: merged_rankings.get(case["case_id"], baseline_rankings[case["case_id"]])
        for case in corpus["cases"]
    }
    evaluator = load_r2_runner()
    cutoffs = config["evaluation"]["cutoffs"]
    metrics, cases = evaluator.evaluate(corpus["cases"], combined_rankings, cutoffs)
    selected_cases = [case for case in corpus["cases"] if case["case_id"] in branches["selected_case_ids"]]
    comparison_metrics, comparison_cases = evaluator.evaluate(selected_cases, merged_rankings, cutoffs)
    baseline_comparison_metrics, baseline_comparison_cases = evaluator.evaluate(
        selected_cases,
        {case["case_id"]: baseline_rankings[case["case_id"]] for case in selected_cases},
        cutoffs,
    )

    result = {
        "run_id": config["experiment_id"] + "-rerank-run-001",
        "status": "completed_comparison_branch_rerank_and_coverage_gate",
        "config": config,
        "config_sha256": digest(config_bytes),
        "implementation_sha256": digest(Path(__file__).read_bytes()),
        "inputs": {
            "corpus_sha256": digest(corpus_bytes),
            "comparison_branches_sha256": digest(branches_bytes),
            "r3_baseline_sha256": digest(baseline_bytes),
        },
        "runtime": {
            "python": platform.python_version(),
            "torch": torch.__version__,
            "transformers": transformers.__version__,
            "tokenizers": tokenizers.__version__,
            "model_load_seconds": model_load_seconds,
            "quantization_seconds": quantization_seconds,
            "scoring": scoring_runtime,
        },
        "branch_rankings": branch_rankings,
        "merged_rankings": merged_rankings,
        "coverage_gates": coverage_gates,
        "evaluation": {
            "all_cases_with_fallback": {"metrics": metrics, "cases": cases},
            "comparison_cases_decomposed": {"metrics": comparison_metrics, "cases": comparison_cases},
            "comparison_cases_r3_baseline": {
                "metrics": baseline_comparison_metrics,
                "cases": baseline_comparison_cases,
            },
        },
        "limitations": [
            "the coverage gate checks branch provenance, not whether each retained passage is correct evidence",
            "qrels are assistant-silver and enter only after scores, branch rankings and merged rankings exist",
            "the same two comparison dev cases are used for diagnostics; no production threshold is selected",
            "no answer generation, citation validation or unsupported-claim test is included",
        ],
    }
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--corpus", type=Path, default=CORPUS_DEFAULT)
    parser.add_argument("--branches", type=Path, default=BRANCHES_DEFAULT)
    parser.add_argument("--baseline", type=Path, default=BASELINE_DEFAULT)
    parser.add_argument("--model-dir", type=Path, default=MODEL_DEFAULT)
    parser.add_argument("--output", type=Path, default=OUTPUT_DEFAULT)
    args = parser.parse_args()
    result = build(
        args.corpus.resolve(),
        args.branches.resolve(),
        args.baseline.resolve(),
        args.model_dir.resolve(),
        args.output.resolve(),
    )
    print(json.dumps({
        "output": args.output.resolve().relative_to(ROOT).as_posix(),
        "runtime": result["runtime"],
        "coverage_gates": result["coverage_gates"],
        "comparison_baseline_metrics": result["evaluation"]["comparison_cases_r3_baseline"]["metrics"],
        "comparison_decomposed_metrics": result["evaluation"]["comparison_cases_decomposed"]["metrics"],
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
