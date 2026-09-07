"""Run E0.9 equivalence-vs-conflict triplet ranking on the 96-document corpus."""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
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
CORPUS_DEFAULT = ROOT / "tmp" / "e09-equivalence-triplets" / "corpus.json"
OUTPUT_DEFAULT = (
    ROOT
    / "data"
    / "evaluation"
    / "synthetic"
    / "duplicate-detection-v0.1"
    / "e09-equivalence-triplet-results.json"
)
CUTOFFS = (1, 2, 3, 5, 10)


def dense_ranking(names: list[str], similarity: np.ndarray, query_name: str) -> list[dict[str, object]]:
    query_index = names.index(query_name)
    values = sorted(
        (
            (float(similarity[query_index, candidate_index]), candidate_name)
            for candidate_index, candidate_name in enumerate(names)
            if candidate_name != query_name
        ),
        key=lambda item: (-item[0], item[1]),
    )
    return [{"filename": name, "score": round(value, 6)} for value, name in values]


def find_row(ranking: list[dict[str, object]], filename: str) -> tuple[int, float]:
    for rank, row in enumerate(ranking, start=1):
        if row["filename"] == filename:
            return rank, float(row["score"])
    raise ValueError(f"Missing ranked document {filename}")


def evaluate_method(
    triplets: list[dict[str, object]],
    rankings: dict[str, list[dict[str, object]]],
) -> dict[str, object]:
    rows: list[dict[str, object]] = []
    category_rows: dict[str, list[dict[str, object]]] = defaultdict(list)
    outcomes: Counter[str] = Counter()
    for triplet in triplets:
        triplet_id = str(triplet["triplet_id"])
        ranking = rankings[triplet_id]
        equivalent = str(triplet["equivalent"])
        conflict = str(triplet["conflict_review_required"])
        equivalent_rank, equivalent_score = find_row(ranking, equivalent)
        conflict_rank, conflict_score = find_row(ranking, conflict)
        margin = equivalent_score - conflict_score
        outcome = "equivalent_preferred" if margin > 0 else "conflict_preferred" if margin < 0 else "tie"
        outcomes[outcome] += 1
        row = {
            "triplet_id": triplet_id,
            "category": triplet["category"],
            "layout_family": triplet["layout_family"],
            "equivalent_rank": equivalent_rank,
            "conflict_rank": conflict_rank,
            "equivalent_score": round(equivalent_score, 6),
            "conflict_score": round(conflict_score, 6),
            "equivalence_margin": round(margin, 6),
            "pairwise_outcome": outcome,
            "top_5": ranking[:5],
        }
        rows.append(row)
        category_rows[str(triplet["category"])].append(row)

    cutoff_metrics: dict[str, object] = {}
    for cutoff in CUTOFFS:
        equivalent_hits = sum(int(row["equivalent_rank"]) <= cutoff for row in rows)
        conflict_hits = sum(int(row["conflict_rank"]) <= cutoff for row in rows)
        dual_hits = sum(
            int(row["equivalent_rank"]) <= cutoff and int(row["conflict_rank"]) <= cutoff
            for row in rows
        )
        cutoff_metrics[f"at_{cutoff}"] = {
            "equivalent_recall": round(equivalent_hits / len(rows), 6),
            "conflict_candidate_recall": round(conflict_hits / len(rows), 6),
            "dual_review_candidate_coverage": round(dual_hits / len(rows), 6),
            "equivalent_hits": equivalent_hits,
            "conflict_hits": conflict_hits,
            "dual_hits": dual_hits,
        }

    categories = {}
    for category, items in sorted(category_rows.items()):
        categories[category] = {
            "triplets": len(items),
            "equivalent_preferred": sum(item["pairwise_outcome"] == "equivalent_preferred" for item in items),
            "conflict_preferred": sum(item["pairwise_outcome"] == "conflict_preferred" for item in items),
            "ties": sum(item["pairwise_outcome"] == "tie" for item in items),
            "mean_equivalence_margin": round(sum(float(item["equivalence_margin"]) for item in items) / len(items), 6),
            "dual_coverage_at_5": round(
                sum(int(item["equivalent_rank"]) <= 5 and int(item["conflict_rank"]) <= 5 for item in items) / len(items),
                6,
            ),
        }

    margins = [float(row["equivalence_margin"]) for row in rows]
    equivalent_scores = [float(row["equivalent_score"]) for row in rows]
    conflict_scores = [float(row["conflict_score"]) for row in rows]
    return {
        "pairwise": {
            "triplets": len(rows),
            "equivalent_preferred": outcomes["equivalent_preferred"],
            "conflict_preferred": outcomes["conflict_preferred"],
            "ties": outcomes["tie"],
            "equivalent_preference_accuracy": round(outcomes["equivalent_preferred"] / len(rows), 6),
            "unsafe_conflict_preference_rate": round(outcomes["conflict_preferred"] / len(rows), 6),
            "mean_equivalence_margin": round(sum(margins) / len(margins), 6),
            "min_equivalence_margin": round(min(margins), 6),
            "max_equivalence_margin": round(max(margins), 6),
        },
        "score_ranges": {
            "equivalent_min": min(equivalent_scores),
            "equivalent_max": max(equivalent_scores),
            "conflict_min": min(conflict_scores),
            "conflict_max": max(conflict_scores),
            "global_threshold_separates_equivalent_from_conflict": max(conflict_scores) < min(equivalent_scores),
        },
        "mean_equivalent_rank": round(sum(int(row["equivalent_rank"]) for row in rows) / len(rows), 6),
        "mean_conflict_rank": round(sum(int(row["conflict_rank"]) for row in rows) / len(rows), 6),
        "max_equivalent_rank": max(int(row["equivalent_rank"]) for row in rows),
        "max_conflict_rank": max(int(row["conflict_rank"]) for row in rows),
        "cutoffs": cutoff_metrics,
        "by_category": categories,
        "triplet_diagnostics": rows,
    }


def run(corpus_path: Path, model_dir: Path, output_path: Path, intra_op_threads: int) -> dict[str, object]:
    import onnxruntime as ort
    from tokenizers import Tokenizer, __version__ as tokenizers_version

    corpus_bytes = corpus_path.read_bytes()
    corpus = json.loads(corpus_bytes)
    require(corpus["serving_index_allowed"] is False, "corpus_must_be_quarantine_only")
    require(corpus["labels_excluded_from_embedding_text"] is True, "label_leakage_guard_missing")
    require(corpus["hidden_test"] is False, "unexpected_hidden_test_claim")
    require(len(corpus["triplets"]) == 12, "unexpected_triplet_count")

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

    dense_rankings = {
        str(triplet["triplet_id"]): dense_ranking(names, similarity, str(triplet["query"]))
        for triplet in corpus["triplets"]
    }
    char5_rankings = {
        str(triplet["triplet_id"]): triplet["char5_ranking"]
        for triplet in corpus["triplets"]
    }
    minhash_rankings = {
        str(triplet["triplet_id"]): triplet["minhash_ranking"]
        for triplet in corpus["triplets"]
    }

    result = {
        "evaluation_round": "E0.9-equivalence-conflict-triplets-2026-09-05",
        "status": "completed_local_triplet_candidate_and_equivalence_diagnostic",
        "corpus": {
            "path": corpus_path.relative_to(ROOT).as_posix(),
            "sha256": hashlib.sha256(corpus_bytes).hexdigest(),
            **corpus["counts"],
            "hidden_test": False,
        },
        "evaluation_semantics": corpus["evaluation_semantics"],
        "implementation": {
            "generator_sha256": file_digest(Path(__file__).with_name("generate_e09_equivalence_triplet_pdfs.py")),
            "prepare_corpus_sha256": file_digest(Path(__file__).with_name("prepare_e09_equivalence_corpus.py")),
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
        "within_session_repeat_max_abs_delta": deterministic_delta,
        "methods": {
            "char5_jaccard": evaluate_method(corpus["triplets"], char5_rankings),
            "minhash128_char5": evaluate_method(corpus["triplets"], minhash_rankings),
            "bge_m3_dense": evaluate_method(corpus["triplets"], dense_rankings),
        },
        "restrictions": {
            "serving_index_written": False,
            "vectors_persisted": False,
            "external_processing": False,
            "auto_equivalence_or_merge": False,
            "threshold_selected": False,
            "gold_or_hidden_claim": False,
        },
        "claims_not_tested": [
            "teacher-reviewed academic correctness",
            "hidden-family generalization",
            "real-upload precision or recall",
            "cross-encoder or LLM adjudication",
            "OCR or image understanding",
            "production latency or authorization enforcement",
        ],
    }
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_bytes(json.dumps(result, ensure_ascii=False, indent=2).encode("utf-8") + b"\n")
    return result


def compact_method(method: dict[str, object]) -> dict[str, object]:
    return {
        "pairwise": method["pairwise"],
        "score_ranges": method["score_ranges"],
        "mean_equivalent_rank": method["mean_equivalent_rank"],
        "mean_conflict_rank": method["mean_conflict_rank"],
        "max_equivalent_rank": method["max_equivalent_rank"],
        "max_conflict_rank": method["max_conflict_rank"],
        "cutoffs": method["cutoffs"],
        "by_category": method["by_category"],
    }


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
        "within_session_repeat_max_abs_delta": result["within_session_repeat_max_abs_delta"],
        "methods": {name: compact_method(method) for name, method in result["methods"].items()},
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
