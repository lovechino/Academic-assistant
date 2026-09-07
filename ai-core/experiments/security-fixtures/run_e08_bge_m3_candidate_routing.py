"""Run E0.8 BGE-M3 hard-negative and staged candidate-routing diagnostics."""
from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import platform
import sys
import time

import numpy as np

from run_bge_m3_duplicate_ablation import (
    MODEL_DATA_SHA256,
    MODEL_DATA_SIZE,
    MODEL_DEFAULT,
    MODEL_FILE_SHA256,
    MODEL_FILE_SIZE,
    MODEL_REVISION,
    TOKENIZER_SHA256,
    encode_texts,
    file_digest,
    make_session,
    require,
)


ROOT = Path(__file__).resolve().parents[3]
CORPUS_DEFAULT = ROOT / "tmp" / "e08-candidate-routing" / "corpus.json"
OUTPUT_DEFAULT = (
    ROOT
    / "data"
    / "evaluation"
    / "synthetic"
    / "duplicate-detection-v0.1"
    / "e08-hard-negative-routing-results.json"
)
CUTOFFS = (1, 3, 5, 10)


def rank_dense(names: list[str], similarity: np.ndarray, query_name: str) -> list[dict[str, object]]:
    query_index = names.index(query_name)
    ranked = sorted(
        (
            (float(similarity[query_index, candidate_index]), candidate_name)
            for candidate_index, candidate_name in enumerate(names)
            if candidate_name != query_name
        ),
        key=lambda item: (-item[0], item[1]),
    )
    return [{"filename": name, "score": round(value, 6)} for value, name in ranked]


def ranking_metrics(
    qrels: list[dict[str, object]],
    rankings: dict[str, list[dict[str, object]]],
    labels: dict[str, dict[str, str]],
) -> dict[str, object]:
    expected = [qrel for qrel in qrels if qrel["candidate_expected"]]
    ranks: list[int] = []
    cutoff_results: dict[str, object] = {}
    for qrel in expected:
        ranking = rankings[str(qrel["pair_id"])]
        rank = next(
            index
            for index, row in enumerate(ranking, start=1)
            if row["filename"] == qrel["left"]
        )
        ranks.append(rank)

    for cutoff in CUTOFFS:
        hits = 0
        slots = 0
        hard_negative_count = 0
        hard_categories: Counter[str] = Counter()
        for qrel in expected:
            selected = rankings[str(qrel["pair_id"])][:cutoff]
            selected_names = {str(row["filename"]) for row in selected}
            hits += int(str(qrel["left"]) in selected_names)
            slots += len(selected)
            for row in selected:
                label = labels[str(row["filename"])]
                if label["role"] == "hard_negative":
                    hard_negative_count += 1
                    hard_categories[label["category"]] += 1
        cutoff_results[f"at_{cutoff}"] = {
            "recall": round(hits / len(expected), 6),
            "micro_candidate_precision": round(hits / slots, 6),
            "candidate_slots": slots,
            "false_candidate_slots": slots - hits,
            "mean_candidates_per_query": round(slots / len(expected), 6),
            "hard_negative_intrusions": hard_negative_count,
            "hard_negative_intrusion_rate": round(hard_negative_count / slots, 6),
            "hard_negative_categories": dict(sorted(hard_categories.items())),
        }

    return {
        "mean_relevant_rank": round(sum(ranks) / len(ranks), 6),
        "max_relevant_rank": max(ranks),
        "mrr": round(sum(1 / rank for rank in ranks) / len(ranks), 6),
        "candidate_budget_for_full_recall_on_dev": max(ranks),
        "cutoffs": cutoff_results,
    }


def union_metrics(
    qrels: list[dict[str, object]],
    left_rankings: dict[str, list[dict[str, object]]],
    right_rankings: dict[str, list[dict[str, object]]],
    labels: dict[str, dict[str, str]],
) -> dict[str, object]:
    expected = [qrel for qrel in qrels if qrel["candidate_expected"]]
    result: dict[str, object] = {}
    for cutoff in CUTOFFS:
        hits = 0
        total = 0
        overlaps = 0
        hard_negative_count = 0
        max_candidates = 0
        for qrel in expected:
            pair_id = str(qrel["pair_id"])
            left_names = {str(row["filename"]) for row in left_rankings[pair_id][:cutoff]}
            right_names = {str(row["filename"]) for row in right_rankings[pair_id][:cutoff]}
            union = left_names | right_names
            hits += int(str(qrel["left"]) in union)
            total += len(union)
            overlaps += len(left_names & right_names)
            max_candidates = max(max_candidates, len(union))
            hard_negative_count += sum(labels[name]["role"] == "hard_negative" for name in union)
        result[f"at_{cutoff}"] = {
            "recall": round(hits / len(expected), 6),
            "micro_candidate_precision": round(hits / total, 6),
            "mean_candidates_per_query": round(total / len(expected), 6),
            "mean_overlap_per_query": round(overlaps / len(expected), 6),
            "false_candidate_slots": total - hits,
            "hard_negative_intrusions": hard_negative_count,
            "max_candidates": max_candidates,
        }
    return result


def route_metrics(
    qrels: list[dict[str, object]],
    rankings: dict[str, list[dict[str, object]]],
    labels: dict[str, dict[str, str]],
    cutoff: int,
    *,
    canonical_stage: bool,
) -> dict[str, object]:
    expected = [qrel for qrel in qrels if qrel["candidate_expected"]]
    stages: Counter[str] = Counter()
    hits = 0
    candidate_count = 0
    false_candidates = 0
    hard_negative_count = 0
    misses: list[str] = []
    per_query: list[dict[str, object]] = []

    for qrel in expected:
        raw = [str(name) for name in qrel["raw_exact_candidates"]]
        canonical = [str(name) for name in qrel["canonical_exact_candidates"]]
        if raw:
            stage = "raw_exact"
            selected = raw
        elif canonical_stage and canonical:
            stage = "canonical_exact_candidate"
            selected = canonical
        else:
            stage = "retriever"
            selected = [str(row["filename"]) for row in rankings[str(qrel["pair_id"])][:cutoff]]
        stages[stage] += 1
        hit = str(qrel["left"]) in selected
        hits += int(hit)
        candidate_count += len(selected)
        false_candidates += len(selected) - int(hit)
        hard_negative_count += sum(labels[name]["role"] == "hard_negative" for name in selected)
        if not hit:
            misses.append(str(qrel["pair_id"]))
        per_query.append({
            "pair_id": qrel["pair_id"],
            "stage": stage,
            "hit": hit,
            "candidate_count": len(selected),
        })

    retriever_queries = stages["retriever"]
    return {
        "cutoff": cutoff,
        "canonical_stage_enabled": canonical_stage,
        "recall": round(hits / len(expected), 6),
        "micro_candidate_precision": round(hits / candidate_count, 6),
        "total_candidate_reviews": candidate_count,
        "mean_candidate_reviews_per_query": round(candidate_count / len(expected), 6),
        "false_candidate_reviews": false_candidates,
        "hard_negative_intrusions": hard_negative_count,
        "stage_query_counts": dict(sorted(stages.items())),
        "retriever_queries": retriever_queries,
        "retriever_queries_avoided": len(expected) - retriever_queries,
        "retriever_query_reduction": round((len(expected) - retriever_queries) / len(expected), 6),
        "miss_pair_ids": misses,
        "candidate_only_not_merge_or_security_decision": True,
        "per_query": per_query,
    }


def run(corpus_path: Path, model_dir: Path, output_path: Path, intra_op_threads: int) -> dict[str, object]:
    import onnxruntime as ort
    from tokenizers import Tokenizer, __version__ as tokenizers_version

    corpus_bytes = corpus_path.read_bytes()
    corpus = json.loads(corpus_bytes)
    require(corpus["serving_index_allowed"] is False, "corpus_must_be_quarantine_only")
    require(corpus["labels_excluded_from_embedding_text"] is True, "label_leakage_guard_missing")
    require(corpus["hidden_test"] is False, "unexpected_hidden_test_claim")

    model_file = model_dir / "onnx" / "model.onnx"
    model_data = model_dir / "onnx" / "model.onnx_data"
    tokenizer_file = model_dir / "tokenizer.json"
    require(model_file.stat().st_size == MODEL_FILE_SIZE, "model_file_size_mismatch")
    require(model_data.stat().st_size == MODEL_DATA_SIZE, "model_data_size_mismatch")
    require(file_digest(model_file) == MODEL_FILE_SHA256, "model_file_hash_mismatch")
    require(file_digest(model_data) == MODEL_DATA_SHA256, "model_data_hash_mismatch")
    require(file_digest(tokenizer_file) == TOKENIZER_SHA256, "tokenizer_hash_mismatch")

    tokenizer = Tokenizer.from_file(str(tokenizer_file))
    tokenizer.no_truncation()
    tokenizer.no_padding()
    session_started = time.perf_counter()
    session = make_session(model_file, intra_op_threads)
    session_seconds = time.perf_counter() - session_started

    documents = corpus["documents"]
    names = [str(item["filename"]) for item in documents]
    vectors, encode_timing = encode_texts(session, tokenizer, [str(item["embedding_text"]) for item in documents])
    repeat_vector, repeat_timing = encode_texts(session, tokenizer, [str(documents[0]["embedding_text"])])
    deterministic_delta = float(np.max(np.abs(repeat_vector[0] - vectors[0])))
    matrix_started = time.perf_counter()
    similarity = vectors @ vectors.T
    matrix_seconds = time.perf_counter() - matrix_started

    qrels = corpus["qrels"]
    dense_rankings = {
        str(qrel["pair_id"]): rank_dense(names, similarity, str(qrel["right"]))
        for qrel in qrels
    }
    minhash_rankings = {
        str(qrel["pair_id"]): qrel["minhash_ranking"]
        for qrel in qrels
    }
    char5_rankings = {
        str(qrel["pair_id"]): qrel["char5_ranking"]
        for qrel in qrels
    }
    labels = corpus["document_eval_labels"]

    dense_metrics = ranking_metrics(qrels, dense_rankings, labels)
    minhash_metrics = ranking_metrics(qrels, minhash_rankings, labels)
    char5_metrics = ranking_metrics(qrels, char5_rankings, labels)

    expected = [qrel for qrel in qrels if qrel["candidate_expected"]]
    relation_diagnostics = []
    for qrel in expected:
        pair_id = str(qrel["pair_id"])
        dense = dense_rankings[pair_id]
        minhash = minhash_rankings[pair_id]
        dense_rank = next(index for index, row in enumerate(dense, start=1) if row["filename"] == qrel["left"])
        minhash_rank = next(index for index, row in enumerate(minhash, start=1) if row["filename"] == qrel["left"])
        hard_dense = next((row for row in dense if labels[str(row["filename"])]["role"] == "hard_negative"), None)
        relation_diagnostics.append({
            "pair_id": pair_id,
            "duplicate_class": qrel["duplicate_class"],
            "security_class": qrel["security_class"],
            "dense_relevant_rank": dense_rank,
            "minhash_relevant_rank": minhash_rank,
            "dense_relevant_score": next(row["score"] for row in dense if row["filename"] == qrel["left"]),
            "highest_dense_hard_negative": hard_dense,
            "dense_top_5": dense[:5],
            "minhash_top_5": minhash[:5],
        })

    result = {
        "evaluation_round": "E0.8-hard-negative-routing-2026-09-05",
        "status": "completed_local_hard_negative_and_candidate_routing_diagnostic",
        "corpus": {
            "path": corpus_path.relative_to(ROOT).as_posix(),
            "sha256": hashlib.sha256(corpus_bytes).hexdigest(),
            **corpus["counts"],
            "hidden_test": False,
        },
        "implementation": {
            "generator_sha256": file_digest(Path(__file__).with_name("generate_e08_hard_negative_pdf_fixtures.py")),
            "prepare_corpus_sha256": file_digest(Path(__file__).with_name("prepare_e08_candidate_corpus.py")),
            "runner_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        },
        "model": {
            "model_id": "BAAI/bge-m3",
            "revision": MODEL_REVISION,
            "format": "upstream_onnx_external_data_float32",
            "model_file_sha256": MODEL_FILE_SHA256,
            "model_data_sha256": MODEL_DATA_SHA256,
            "tokenizer_sha256": TOKENIZER_SHA256,
            "dimensions": int(vectors.shape[1]),
            "pooling": "cls_token",
            "normalization": "l2",
            "query_instruction": None,
            "runtime": f"onnxruntime-{ort.__version__}-cpu",
            "tokenizers_version": tokenizers_version,
            "intra_op_threads": intra_op_threads,
        },
        "timing": {
            "platform": platform.platform(),
            "session_load_seconds": round(session_seconds, 3),
            "encode": encode_timing,
            "repeat_probe": repeat_timing,
            "similarity_matrix_seconds": round(matrix_seconds, 6),
        },
        "deterministic_probe_max_abs_delta": deterministic_delta,
        "retrievers": {
            "char5_jaccard": char5_metrics,
            "minhash128_char5": minhash_metrics,
            "bge_m3_dense": dense_metrics,
        },
        "unions": {
            "minhash_bge_m3": union_metrics(qrels, minhash_rankings, dense_rankings, labels),
        },
        "routing": {
            "raw_then_bge_at_3": route_metrics(qrels, dense_rankings, labels, 3, canonical_stage=False),
            "raw_canonical_then_bge_at_3": route_metrics(qrels, dense_rankings, labels, 3, canonical_stage=True),
            "raw_canonical_then_minhash_at_3": route_metrics(qrels, minhash_rankings, labels, 3, canonical_stage=True),
        },
        "relation_diagnostics": relation_diagnostics,
        "restrictions": {
            "serving_index_written": False,
            "vectors_persisted": False,
            "external_processing": False,
            "auto_merge_or_publish": False,
            "threshold_selected": False,
            "security_detection_claim": False,
        },
        "claims_not_tested": [
            "hidden-test generalization",
            "precision on real documents",
            "security or prompt-injection detection",
            "OCR or image understanding",
            "production latency or concurrency",
            "authorization correctness",
        ],
    }
    output_path.parent.mkdir(parents=True, exist_ok=True)
    payload = json.dumps(result, ensure_ascii=False, indent=2).encode("utf-8") + b"\n"
    output_path.write_bytes(payload)
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--corpus", type=Path, default=CORPUS_DEFAULT)
    parser.add_argument("--model-dir", type=Path, default=MODEL_DEFAULT)
    parser.add_argument("--output", type=Path, default=OUTPUT_DEFAULT)
    parser.add_argument("--intra-op-threads", type=int, default=4)
    args = parser.parse_args()
    result = run(args.corpus.resolve(), args.model_dir.resolve(), args.output.resolve(), args.intra_op_threads)
    sys.stdout.reconfigure(encoding="utf-8")
    print(json.dumps({
        "status": result["status"],
        "output": args.output.resolve().relative_to(ROOT).as_posix(),
        "corpus": result["corpus"],
        "timing": result["timing"],
        "retrievers": result["retrievers"],
        "unions": result["unions"],
        "routing": {name: {key: value for key, value in metrics.items() if key != "per_query"} for name, metrics in result["routing"].items()},
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
