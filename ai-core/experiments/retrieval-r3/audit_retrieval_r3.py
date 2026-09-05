"""Read-only integrity and metric audit for hybrid, reranker and packing R3."""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
R2_RUNNER = ROOT / "ai-core/experiments/dense-retrieval-r2/run_dense_retrieval.py"
HYBRID_CONFIG = HERE / "hybrid-config-v0.1.json"
RERANK_CONFIG = HERE / "reranker-config-v0.1.json"
PACKING_CONFIG = HERE / "packing-config-v0.1.json"
HYBRID_SCRIPT = HERE / "run_hybrid_retrieval.py"
RERANK_SCRIPT = HERE / "run_reranker.py"
PACKING_SCRIPT = HERE / "run_context_packing.py"
CORPUS = ROOT / "data/processed/voer-dsa-dense-r2-v0.1/corpus.json"
HYBRID = ROOT / "data/processed/voer-dsa-retrieval-r3-v0.1/hybrid-results.json"
RERANK = ROOT / "data/processed/voer-dsa-retrieval-r3-v0.1/reranker-results.json"
PACKING = ROOT / "data/processed/voer-dsa-retrieval-r3-v0.1/packing-results.json"
MODEL_DEFAULT = ROOT / "tmp/models/bge-reranker-v2-m3-953dc6f6f85a1b2dbfca4c34a2796e7dde08d41e/model.safetensors"
TOKENIZER_DEFAULT = ROOT / "tmp/tokenizers/bge-m3-5617a9f61b028005a4858fdac845db406aefb181/tokenizer.json"
OUTPUT_DEFAULT = ROOT / "data/processed/voer-dsa-retrieval-r3-v0.1/validation.json"


def digest(path: Path) -> str:
    hasher = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(8 * 1024 * 1024), b""):
            hasher.update(block)
    return hasher.hexdigest()


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def audit(model_weights: Path, tokenizer_path: Path) -> dict:
    runner = load_module("retrieval_r3_audit_runner", R2_RUNNER)
    packer = load_module("retrieval_r3_audit_packer", PACKING_SCRIPT)
    corpus = json.loads(CORPUS.read_text(encoding="utf-8"))
    hybrid = json.loads(HYBRID.read_text(encoding="utf-8"))
    rerank = json.loads(RERANK.read_text(encoding="utf-8"))
    packing = json.loads(PACKING.read_text(encoding="utf-8"))
    checks = []
    warnings = []

    def check(code: str, ok: bool, detail: str = "") -> None:
        checks.append({"code": code, "passed": bool(ok), "detail": detail})

    check("hybrid_config_hash", hybrid["config_sha256"] == digest(HYBRID_CONFIG))
    check("reranker_config_hash", rerank["config_sha256"] == digest(RERANK_CONFIG))
    check("packing_config_hash", packing["config_sha256"] == digest(PACKING_CONFIG))
    check("hybrid_implementation_hash", hybrid["implementation_sha256"] == digest(HYBRID_SCRIPT))
    check("reranker_implementation_hash", rerank["implementation_sha256"] == digest(RERANK_SCRIPT))
    check("packing_implementation_hash", packing["implementation_sha256"] == digest(PACKING_SCRIPT))
    check("corpus_chain_hybrid", hybrid["inputs"]["corpus_sha256"] == digest(CORPUS))
    check("corpus_chain_reranker", rerank["inputs"]["corpus_sha256"] == digest(CORPUS))
    check("hybrid_chain_reranker", rerank["inputs"]["hybrid_results_sha256"] == digest(HYBRID))
    check("reranker_chain_packing", packing["inputs"]["reranker_results_sha256"] == digest(RERANK))
    check("model_weights_hash", digest(model_weights) == rerank["config"]["model"]["weights_sha256"] ==
          rerank["model"]["weights_sha256"])
    check("packet_tokenizer_hash", digest(tokenizer_path) == packing["config"]["tokenizer"]["file_sha256"])

    cutoffs = hybrid["config"]["evaluation"]["cutoffs"]
    for stage_name, stage in hybrid["stages"].items():
        if stage_name.startswith("rrf_depth_"):
            rankings = stage["candidate_rankings"]
        else:
            rankings = {case["case_id"]: case["top_results"] for case in stage["cases"]}
        metrics, _ = runner.evaluate(corpus["cases"], rankings, cutoffs)
        check("hybrid_metric_recompute:" + stage_name, metrics == stage["metrics"])

    source = hybrid["stages"][rerank["config"]["candidate_source"]["stage"]]["candidate_rankings"]
    for stage_name, stage in rerank["stages"].items():
        pool_size = int(stage_name.rsplit("_", 1)[1])
        rankings = stage["rankings"]
        selection_ok = True
        sorted_ok = True
        unique_ok = True
        for case_id, rows in rankings.items():
            selection_ok &= {row["chunk_id"] for row in rows} == {
                row["chunk_id"] for row in source[case_id][:pool_size]
            }
            sorted_ok &= all(rows[index - 1]["reranker_score"] >= rows[index]["reranker_score"]
                             for index in range(1, len(rows)))
            unique_ok &= len(rows) == len({row["chunk_id"] for row in rows}) == pool_size
        check("reranker_candidate_conservation:" + stage_name, selection_ok)
        check("reranker_score_order:" + stage_name, sorted_ok)
        check("reranker_unique_pool:" + stage_name, unique_ok)
        metrics, _ = runner.evaluate(corpus["cases"], rankings, cutoffs)
        check("reranker_metric_recompute:" + stage_name, metrics == stage["metrics"])
    check("reranker_no_truncation", rerank["runtime"]["scoring"]["pairs_truncated"] == 0)
    check("reranker_scored_expected_pairs", rerank["runtime"]["scoring"]["pairs"] == 800)
    delta = rerank["runtime"]["deterministic_probe_abs_delta"]
    warnings.append({"code": "dynamic_int8_batch_shape_sensitivity",
                     "detail": "first pair in batch=4 versus repeated alone; abs logit delta=" + str(delta)})

    tokenizer = __import__("tokenizers").Tokenizer.from_file(str(tokenizer_path))
    tokenizer.no_truncation()
    tokenizer.no_padding()
    chunks = {row["chunk_id"]: row for row in corpus["chunks"]}
    separator = packing["config"]["packet"]["separator"]
    for stage_name, stage in packing["stages"].items():
        budget = int(stage_name.rsplit("-b", 1)[1])
        packets = {case["case_id"]: case["packet"] for case in stage["cases"]}
        unique_ok = all(len(packet["chunk_ids"]) == len(set(packet["chunk_ids"])) for packet in packets.values())
        eligible_ok = all(all(chunks[chunk_id]["embedding_eligible"] for chunk_id in packet["chunk_ids"])
                          for packet in packets.values())
        token_ok = True
        for packet in packets.values():
            rebuilt = packer.token_count(tokenizer, [chunks[chunk_id]["embedding_text"]
                                                     for chunk_id in packet["chunk_ids"]], separator)
            token_ok &= rebuilt == packet["tokens"] and rebuilt <= budget
        check("packet_unique:" + stage_name, unique_ok)
        check("packet_text_eligible:" + stage_name, eligible_ok)
        check("packet_budget_recompute:" + stage_name, token_ok)
        rebuilt = packer.packet_metrics(runner, corpus["cases"], packets)
        check("packet_metric_recompute:" + stage_name, rebuilt["summary"] == stage["summary"])

    dependency_summary = packing["dependency_diagnostics"]["summary"]
    check("dependency_visual_not_silently_covered",
          all(row["visual_unsupported"] == 1 for row in dependency_summary.values()))
    check("dependency_labels_not_runtime_ready",
          packing["config"]["dependency_evaluator"]["runtime_ready"] is False)
    check("guard_reranker_pool20_ceiling",
          rerank["stages"]["reranker_pool_20"]["metrics"]["5"]["all_evidence_cases"] < 10)
    check("guard_packet_1024_not_declared_complete",
          packing["stages"]["x0-child-only-b1024"]["summary"]["all_evidence_cases"] < 10)
    failed = [row for row in checks if not row["passed"]]
    return {"status": "passed_with_warnings" if not failed and warnings else ("passed" if not failed else "failed"),
            "checks": len(checks), "passed": len(checks) - len(failed), "failed": failed,
            "warnings": warnings, "guards": 2,
            "artifacts": {"hybrid_sha256": digest(HYBRID), "reranker_sha256": digest(RERANK),
                          "packing_sha256": digest(PACKING)}}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model-weights", type=Path, default=MODEL_DEFAULT)
    parser.add_argument("--tokenizer", type=Path, default=TOKENIZER_DEFAULT)
    parser.add_argument("--output", type=Path, default=OUTPUT_DEFAULT)
    args = parser.parse_args()
    result = audit(args.model_weights.resolve(), args.tokenizer.resolve())
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False, indent=2))
    raise SystemExit(1 if result["status"] == "failed" else 0)


if __name__ == "__main__":
    main()
