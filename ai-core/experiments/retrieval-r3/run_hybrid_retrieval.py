"""Run deterministic BM25 and RRF ablations over the frozen R2 corpus."""
from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import importlib.util
import json
import math
from pathlib import Path
import re
import sys
import time
import unicodedata

import numpy as np


ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
CONFIG = HERE / "hybrid-config-v0.1.json"
R2_RUNNER = ROOT / "ai-core/experiments/dense-retrieval-r2/run_dense_retrieval.py"
CORPUS_DEFAULT = ROOT / "data/processed/voer-dsa-dense-r2-v0.1/corpus.json"
VECTORS_DEFAULT = ROOT / "data/processed/voer-dsa-dense-r2-v0.1/vectors.npz"
R2_RESULTS_DEFAULT = ROOT / "data/processed/voer-dsa-dense-r2-v0.1/results.json"
OUTPUT_DEFAULT = ROOT / "data/processed/voer-dsa-retrieval-r3-v0.1/hybrid-results.json"
WORD = re.compile(r"[^\W_]+", re.UNICODE)


def digest(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def require(ok: bool, code: str) -> None:
    if not ok:
        raise ValueError(code)


def load_r2_runner():
    spec = importlib.util.spec_from_file_location("retrieval_r3_r2_runner", R2_RUNNER)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def tokenize(text: str) -> list[str]:
    return WORD.findall(unicodedata.normalize("NFKC", text).casefold())


class BM25:
    def __init__(self, texts: list[str], k1: float, b: float):
        self.k1 = k1
        self.b = b
        self.term_frequencies = [Counter(tokenize(text)) for text in texts]
        self.lengths = np.asarray([sum(tf.values()) for tf in self.term_frequencies], dtype=np.float64)
        self.average_length = float(self.lengths.mean())
        document_frequency = Counter(term for tf in self.term_frequencies for term in tf)
        count = len(texts)
        self.idf = {term: math.log(1.0 + (count - df + 0.5) / (df + 0.5))
                    for term, df in document_frequency.items()}

    def score(self, query: str) -> np.ndarray:
        query_terms = Counter(tokenize(query))
        scores = np.zeros(len(self.term_frequencies), dtype=np.float64)
        normalization = self.k1 * (1.0 - self.b + self.b * self.lengths / self.average_length)
        for term, query_count in query_terms.items():
            idf = self.idf.get(term)
            if idf is None:
                continue
            tf = np.asarray([doc.get(term, 0) for doc in self.term_frequencies], dtype=np.float64)
            scores += query_count * idf * (tf * (self.k1 + 1.0)) / (tf + normalization)
        return scores


def ranking_rows(order: np.ndarray, chunks: list[dict], scores: np.ndarray, score_name: str) -> list[dict]:
    return [{
        "rank": rank,
        "chunk_id": chunks[index]["chunk_id"],
        "document_id": chunks[index]["document_id"],
        score_name: float(scores[index]),
        "embedding_tokens": chunks[index]["embedding_tokens"],
        "preview": chunks[index]["embedding_text"][:240],
    } for rank, index in enumerate(order, 1)]


def rrf(dense_order: np.ndarray, sparse_order: np.ndarray, sparse_scores: np.ndarray,
        chunks: list[dict], depth: int, rrf_k: int) -> list[dict]:
    dense_prefetch = dense_order[:depth].tolist()
    sparse_prefetch = [int(index) for index in sparse_order if sparse_scores[index] > 0][:depth]
    dense_ranks = {index: rank for rank, index in enumerate(dense_prefetch, 1)}
    sparse_ranks = {index: rank for rank, index in enumerate(sparse_prefetch, 1)}
    candidates = set(dense_ranks) | set(sparse_ranks)
    rows = []
    missing = 10 ** 9
    for index in candidates:
        score = ((1.0 / (rrf_k + dense_ranks[index])) if index in dense_ranks else 0.0) + (
            (1.0 / (rrf_k + sparse_ranks[index])) if index in sparse_ranks else 0.0
        )
        rows.append({
            "chunk_index": index,
            "chunk_id": chunks[index]["chunk_id"],
            "document_id": chunks[index]["document_id"],
            "rrf_score": score,
            "dense_rank": dense_ranks.get(index),
            "bm25_rank": sparse_ranks.get(index),
            "embedding_tokens": chunks[index]["embedding_tokens"],
            "preview": chunks[index]["embedding_text"][:240],
        })
    rows.sort(key=lambda row: (-row["rrf_score"], row["dense_rank"] or missing,
                               row["bm25_rank"] or missing, row["chunk_id"]))
    for rank, row in enumerate(rows, 1):
        row["rank"] = rank
    return rows


def evaluate_stage(runner, cases: list[dict], rankings: dict[str, list[dict]], cutoffs: list[int]) -> dict:
    metrics, per_case = runner.evaluate(cases, rankings, cutoffs)
    return {"metrics": metrics, "cases": per_case}


def build(corpus_path: Path, vector_path: Path, r2_results_path: Path, output_path: Path) -> dict:
    config_bytes = CONFIG.read_bytes()
    config = json.loads(config_bytes)
    corpus_bytes = corpus_path.read_bytes()
    corpus = json.loads(corpus_bytes)
    r2_results_bytes = r2_results_path.read_bytes()
    r2_results = json.loads(r2_results_bytes)
    vector_bytes = vector_path.read_bytes()
    vectors = np.load(vector_path, allow_pickle=False)
    chunks = [row for row in corpus["chunks"] if row["embedding_eligible"]]
    chunk_ids = vectors["chunk_ids"].tolist()
    require(chunk_ids == [row["chunk_id"] for row in chunks], "chunk_vector_order_mismatch")
    require(vectors["case_ids"].tolist() == [case["case_id"] for case in corpus["cases"]], "query_vector_order_mismatch")
    require(r2_results["corpus_sha256"] == digest(corpus_bytes), "r2_corpus_hash_mismatch")
    require(r2_results["vector_file_sha256"] == digest(vector_bytes), "r2_vector_hash_mismatch")

    started = time.perf_counter()
    dense_scores = vectors["query_vectors"] @ vectors["chunk_vectors"].T
    bm25 = BM25([chunk["embedding_text"] for chunk in chunks], config["bm25"]["k1"], config["bm25"]["b"])
    cutoffs = config["evaluation"]["cutoffs"]
    max_output = max(max(cutoffs), max(config["fusion"]["prefetch_depths_per_retriever"]))
    dense_rankings = {}
    bm25_rankings = {}
    rrf_rankings = {str(depth): {} for depth in config["fusion"]["prefetch_depths_per_retriever"]}
    sparse_positive_counts = []
    for query_index, case in enumerate(corpus["cases"]):
        dense_order = np.argsort(-dense_scores[query_index], kind="stable")
        sparse_scores = bm25.score(case["query"])
        sparse_order = np.argsort(-sparse_scores, kind="stable")
        sparse_positive_counts.append(int(np.count_nonzero(sparse_scores > 0)))
        dense_rankings[case["case_id"]] = ranking_rows(
            dense_order[:max_output], chunks, dense_scores[query_index], "dense_score"
        )
        bm25_rankings[case["case_id"]] = ranking_rows(
            sparse_order[:max_output], chunks, sparse_scores, "bm25_score"
        )
        for depth in config["fusion"]["prefetch_depths_per_retriever"]:
            rrf_rankings[str(depth)][case["case_id"]] = rrf(
                dense_order, sparse_order, sparse_scores, chunks, depth, config["fusion"]["rrf_k"]
            )

    stored_top20 = {case["case_id"]: [row["chunk_id"] for row in case["top_results"]]
                    for case in r2_results["cases"]}
    require(all([row["chunk_id"] for row in dense_rankings[case_id][:20]] == ids
                for case_id, ids in stored_top20.items()), "dense_ranking_not_reproduced")
    runner = load_r2_runner()
    stages = {
        "dense_recomputed": evaluate_stage(runner, corpus["cases"], dense_rankings, cutoffs),
        "bm25": evaluate_stage(runner, corpus["cases"], bm25_rankings, cutoffs),
    }
    for depth, rankings in rrf_rankings.items():
        stage = evaluate_stage(runner, corpus["cases"], rankings, cutoffs)
        pool_metrics, _ = runner.evaluate(corpus["cases"], rankings, [int(depth)])
        stage["candidate_pool_metrics"] = pool_metrics[depth]
        stage["candidate_rankings"] = rankings
        stages["rrf_depth_" + depth] = stage

    result = {
        "run_id": config["experiment_id"] + "-run-001",
        "status": "completed_bm25_and_rrf_retrieval_only",
        "config": config,
        "config_sha256": digest(config_bytes),
        "implementation_sha256": digest(Path(__file__).read_bytes()),
        "inputs": {
            "corpus_sha256": digest(corpus_bytes),
            "vectors_sha256": digest(vector_bytes),
            "r2_results_sha256": digest(r2_results_bytes),
        },
        "runtime": {
            "seconds": round(time.perf_counter() - started, 3),
            "documents": len(chunks),
            "queries": len(corpus["cases"]),
            "bm25_average_document_terms": bm25.average_length,
            "bm25_vocabulary": len(bm25.idf),
            "bm25_positive_candidates_min": min(sparse_positive_counts),
            "bm25_positive_candidates_max": max(sparse_positive_counts),
        },
        "stages": stages,
        "limitations": [
            "qrels are assistant-silver dev labels and are evaluator-only",
            "BM25 tokenization has no Vietnamese word segmentation, stemming or stopword removal",
            "RRF depth sensitivity is reported without selecting a winner on these ten dev queries",
            "no reranker, context expansion, packing, generation or image understanding is included in this artifact",
        ],
    }
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--corpus", type=Path, default=CORPUS_DEFAULT)
    parser.add_argument("--vectors", type=Path, default=VECTORS_DEFAULT)
    parser.add_argument("--r2-results", type=Path, default=R2_RESULTS_DEFAULT)
    parser.add_argument("--output", type=Path, default=OUTPUT_DEFAULT)
    args = parser.parse_args()
    result = build(args.corpus.resolve(), args.vectors.resolve(), args.r2_results.resolve(), args.output.resolve())
    print(json.dumps({
        "output": args.output.resolve().relative_to(ROOT).as_posix(),
        "runtime": result["runtime"],
        "metrics": {stage: value["metrics"] for stage, value in result["stages"].items()},
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
