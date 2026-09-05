"""Read-only integrity and metric recomputation for the local R2 dense run."""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

import numpy as np


ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
CONFIG = HERE / "config-v0.1.json"
RUNNER = HERE / "run_dense_retrieval.py"
CORPUS_DEFAULT = ROOT / "data/processed/voer-dsa-dense-r2-v0.1/corpus.json"
RESULT_DEFAULT = ROOT / "data/processed/voer-dsa-dense-r2-v0.1/results.json"
VECTOR_DEFAULT = ROOT / "data/processed/voer-dsa-dense-r2-v0.1/vectors.npz"


def digest(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def load_runner():
    spec = importlib.util.spec_from_file_location("dense_r2_runner_for_audit", RUNNER)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def audit(corpus_path: Path, result_path: Path, vector_path: Path) -> dict:
    checks = []

    def check(code: str, ok: bool, detail: str = "") -> None:
        checks.append({"code": code, "passed": bool(ok), "detail": detail})

    config_bytes = CONFIG.read_bytes()
    corpus_bytes = corpus_path.read_bytes()
    result_bytes = result_path.read_bytes()
    corpus = json.loads(corpus_bytes)
    result = json.loads(result_bytes)
    vectors = np.load(vector_path, allow_pickle=False)
    eligible = [row for row in corpus["chunks"] if row["embedding_eligible"]]
    chunk_ids = vectors["chunk_ids"].tolist()
    case_ids = vectors["case_ids"].tolist()
    chunk_vectors = vectors["chunk_vectors"]
    query_vectors = vectors["query_vectors"]

    check("config_identity", corpus["config_sha256"] == result["config_sha256"] == digest(config_bytes))
    check("corpus_identity", result["corpus_sha256"] == digest(corpus_bytes))
    check("vector_identity", result["vector_file_sha256"] == digest(vector_path.read_bytes()))
    check("chunk_id_order", chunk_ids == [row["chunk_id"] for row in eligible])
    check("case_id_order", case_ids == [case["case_id"] for case in corpus["cases"]])
    check("chunk_vector_shape", chunk_vectors.shape == (len(eligible), 1024), str(chunk_vectors.shape))
    check("query_vector_shape", query_vectors.shape == (len(corpus["cases"]), 1024), str(query_vectors.shape))
    check("vectors_finite", bool(np.isfinite(chunk_vectors).all() and np.isfinite(query_vectors).all()))
    check("chunk_vectors_unit_norm", bool(np.allclose(np.linalg.norm(chunk_vectors, axis=1), 1.0, atol=1e-5)))
    check("query_vectors_unit_norm", bool(np.allclose(np.linalg.norm(query_vectors, axis=1), 1.0, atol=1e-5)))
    check("deterministic_probe", result["runtime"]["deterministic_probe_max_abs_delta"] <= 1e-7,
          str(result["runtime"]["deterministic_probe_max_abs_delta"]))

    scores = query_vectors @ chunk_vectors.T
    rankings = {}
    max_cutoff = max(result["config"]["evaluation"]["cutoffs"])
    rank_match = True
    score_match = True
    for query_index, case_id in enumerate(case_ids):
        order = np.argsort(-scores[query_index], kind="stable")[:max_cutoff]
        rebuilt = []
        for rank, index in enumerate(order, 1):
            rebuilt.append({"rank": rank, "chunk_id": eligible[index]["chunk_id"]})
        stored_case = next(case for case in result["cases"] if case["case_id"] == case_id)
        stored = stored_case["top_results"]
        rank_match &= [row["chunk_id"] for row in rebuilt] == [row["chunk_id"] for row in stored]
        score_match &= all(abs(float(scores[query_index, index]) - stored[rank]["score"]) <= 1e-6
                           for rank, index in enumerate(order))
        rankings[case_id] = stored
    check("exact_rank_recomputation", rank_match)
    check("score_recomputation", score_match)

    runner = load_runner()
    metrics, per_case = runner.evaluate(corpus["cases"], rankings, result["config"]["evaluation"]["cutoffs"])
    check("metric_recomputation", metrics == result["metrics"])
    check("per_case_recomputation",
          all(a["by_cutoff"] == b["by_cutoff"] and a["first_qrel_chunk_rank"] == b["first_qrel_chunk_rank"]
              for a, b in zip(per_case, result["cases"])))

    group_guard = corpus["cases"][0]["required_groups"][0]
    all_qrel_chunks = {chunk_id for alternative in group_guard["alternatives"] for chunk_id in alternative["all_of_chunk_ids"]}
    non_qrel = next(chunk_id for chunk_id in chunk_ids if chunk_id not in all_qrel_chunks)
    check("guard_group_hit_rejects_non_qrel", not runner.group_hit(group_guard, {non_qrel}))
    check("guard_group_hit_accepts_complete_alternative",
          runner.group_hit(group_guard, set(group_guard["alternatives"][0]["all_of_chunk_ids"])))
    multi = next((group for case in corpus["cases"] for group in case["required_groups"]
                  for alternative in group["alternatives"] if len(alternative["all_of_chunk_ids"]) > 1), None)
    if multi:
        alternative = next(a for a in multi["alternatives"] if len(a["all_of_chunk_ids"]) > 1)
        check("guard_partial_multi_chunk_evidence_rejected",
              not runner.group_hit(multi, {alternative["all_of_chunk_ids"][0]}))
    else:
        check("guard_partial_multi_chunk_evidence_rejected", True, "no multi-chunk alternative in frozen qrels")

    failed = [row for row in checks if not row["passed"]]
    return {
        "status": "passed" if not failed else "failed",
        "checks": len(checks),
        "passed": len(checks) - len(failed),
        "failed": failed,
        "result_sha256": digest(result_bytes),
        "guards": 3,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--corpus", type=Path, default=CORPUS_DEFAULT)
    parser.add_argument("--result", type=Path, default=RESULT_DEFAULT)
    parser.add_argument("--vectors", type=Path, default=VECTOR_DEFAULT)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    report = audit(args.corpus.resolve(), args.result.resolve(), args.vectors.resolve())
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    raise SystemExit(0 if report["status"] == "passed" else 1)


if __name__ == "__main__":
    main()
