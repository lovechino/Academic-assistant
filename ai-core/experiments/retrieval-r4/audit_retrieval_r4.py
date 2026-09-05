"""Read-only integrity and metric audit for the R4 retrieval diagnostics."""
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
R3_PACKER = ROOT / "ai-core/experiments/retrieval-r3/run_context_packing.py"
CORPUS = ROOT / "data/processed/voer-dsa-dense-r2-v0.1/corpus.json"
R3_RERANK = ROOT / "data/processed/voer-dsa-retrieval-r3-v0.1/reranker-results.json"
ENRICHMENT = ROOT / "data/processed/voer-dsa-enrichment-v0.1/enrichment.json"
STABILITY_CONFIG = HERE / "stability-config-v0.1.json"
COMPARISON_CONFIG = HERE / "comparison-config-v0.1.json"
CODE_CONFIG = HERE / "code-prologue-config-v0.1.json"
STABILITY_SCRIPT = HERE / "run_reranker_stability.py"
BRANCH_SCRIPT = HERE / "run_comparison_branches.py"
COMPARISON_SCRIPT = HERE / "run_comparison_rerank.py"
CODE_SCRIPT = HERE / "run_code_prologue_packing.py"
STABILITY = ROOT / "data/processed/voer-dsa-retrieval-r4-v0.1/stability-results.json"
BRANCHES = ROOT / "data/processed/voer-dsa-retrieval-r4-v0.1/comparison-branches.json"
COMPARISON = ROOT / "data/processed/voer-dsa-retrieval-r4-v0.1/comparison-results.json"
CODE_RESULTS = ROOT / "data/processed/voer-dsa-retrieval-r4-v0.1/code-prologue-results.json"
MODEL_DEFAULT = ROOT / "tmp/models/bge-reranker-v2-m3-953dc6f6f85a1b2dbfca4c34a2796e7dde08d41e/model.safetensors"
TOKENIZER_DEFAULT = ROOT / "tmp/tokenizers/bge-m3-5617a9f61b028005a4858fdac845db406aefb181/tokenizer.json"
OUTPUT_DEFAULT = ROOT / "data/processed/voer-dsa-retrieval-r4-v0.1/validation.json"


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
    evaluator = load_module("retrieval_r4_audit_evaluator", R2_RUNNER)
    r3_packer = load_module("retrieval_r4_audit_r3_packer", R3_PACKER)
    stability_module = load_module("retrieval_r4_audit_stability", STABILITY_SCRIPT)
    branch_module = load_module("retrieval_r4_audit_branches", BRANCH_SCRIPT)
    comparison_module = load_module("retrieval_r4_audit_comparison", COMPARISON_SCRIPT)
    corpus = json.loads(CORPUS.read_text(encoding="utf-8"))
    baseline = json.loads(R3_RERANK.read_text(encoding="utf-8"))
    enrichment = json.loads(ENRICHMENT.read_text(encoding="utf-8"))
    stability = json.loads(STABILITY.read_text(encoding="utf-8"))
    branches = json.loads(BRANCHES.read_text(encoding="utf-8"))
    comparison = json.loads(COMPARISON.read_text(encoding="utf-8"))
    code_results = json.loads(CODE_RESULTS.read_text(encoding="utf-8"))
    checks = []
    findings = []

    def check(code: str, ok: bool, detail: str = "") -> None:
        checks.append({"code": code, "passed": bool(ok), "detail": detail})

    check("stability_config_hash", stability["config_sha256"] == digest(STABILITY_CONFIG))
    check("comparison_branch_config_hash", branches["config_sha256"] == digest(COMPARISON_CONFIG))
    check("comparison_result_config_hash", comparison["config_sha256"] == digest(COMPARISON_CONFIG))
    check("code_config_hash", code_results["config_sha256"] == digest(CODE_CONFIG))
    check("stability_implementation_hash", stability["implementation_sha256"] == digest(STABILITY_SCRIPT))
    check("branch_implementation_hash", branches["implementation_sha256"] == digest(BRANCH_SCRIPT))
    check("comparison_implementation_hash", comparison["implementation_sha256"] == digest(COMPARISON_SCRIPT))
    check("code_implementation_hash", code_results["implementation_sha256"] == digest(CODE_SCRIPT))
    for name, artifact in (("stability", stability), ("branches", branches), ("code", code_results)):
        check("corpus_chain:" + name, artifact["inputs"]["corpus_sha256"] == digest(CORPUS))
    check("corpus_chain:comparison", comparison["inputs"]["corpus_sha256"] == digest(CORPUS))
    check("branch_chain:comparison", comparison["inputs"]["comparison_branches_sha256"] == digest(BRANCHES))
    check("baseline_chain:comparison", comparison["inputs"]["r3_baseline_sha256"] == digest(R3_RERANK))
    check("baseline_chain:code", code_results["inputs"]["reranker_results_sha256"] == digest(R3_RERANK))
    check("reranker_weights_hash", digest(model_weights) == stability["config"]["model"]["weights_sha256"])
    check("packing_tokenizer_hash", digest(tokenizer_path) == code_results["config"]["tokenizer"]["file_sha256"])

    probe = stability["probe"]
    check("stability_probe_shape", probe["queries"] == 10 and probe["pairs"] == 80)
    check("stability_probe_unique_per_query", all(len(ids) == len(set(ids)) == 8
                                                   for ids in probe["candidate_ids"].values()))
    check("stability_no_truncation", all(row["pairs_truncated"] == 0
                                          for row in stability["runtime"]["timings"].values()))
    check("stability_same_variant_repeat", stability["same_variant_repeat_max_abs_delta"] ==
          {"f32_b4": 0.0, "int8_b4": 0.0})
    score_maps = {
        variant: {
            (case_id, chunk_id): score
            for case_id, values in case_scores.items()
            for chunk_id, score in values.items()
        }
        for variant, case_scores in stability["scores"].items()
    }
    probe_rows = {
        case_id: [{"case_id": case_id, "chunk_id": chunk_id, "rrf_rank": rank}
                  for rank, chunk_id in enumerate(chunk_ids, 1)]
        for case_id, chunk_ids in probe["candidate_ids"].items()
    }
    comparison_pairs = {
        "batch_shape_f32_b1_vs_b4": ("f32_b1", "f32_b4"),
        "batch_shape_int8_b1_vs_b4": ("int8_b1", "int8_b4"),
        "precision_f32_vs_int8_b1": ("f32_b1", "int8_b1"),
        "precision_f32_vs_int8_b4": ("f32_b4", "int8_b4"),
    }
    for name, (left, right) in comparison_pairs.items():
        rebuilt = stability_module.compare(score_maps[left], score_maps[right], probe_rows)
        check("stability_comparison_recompute:" + name, rebuilt == stability["comparisons"][name])
    f32 = stability["comparisons"]["batch_shape_f32_b1_vs_b4"]
    check("f32_batch_shape_rank_invariant", f32["ranking"]["total_pairwise_inversions"] == 0)
    check("f32_batch_shape_score_near_invariant", f32["score_delta"]["max_abs"] < 0.0001)
    int8 = stability["comparisons"]["batch_shape_int8_b1_vs_b4"]
    check("int8_sensitivity_observed", int8["ranking"]["total_pairwise_inversions"] > 0 and
          int8["score_delta"]["max_abs"] > 0.0)
    findings.append({
        "code": "dynamic_int8_batch_shape_sensitive",
        "detail": "batch 1 versus 4: max abs logit delta=" + str(int8["score_delta"]["max_abs"]) +
                  ", pairwise inversions=" + str(int8["ranking"]["total_pairwise_inversions"]),
    })

    decomposition_config = json.loads(COMPARISON_CONFIG.read_text(encoding="utf-8"))["decomposition"]
    rebuilt_decompositions = {
        case["case_id"]: branch_module.decompose(case["query"], decomposition_config)
        for case in corpus["cases"]
    }
    check("comparison_decomposition_recompute", rebuilt_decompositions == branches["decomposition_audit"])
    check("comparison_selected_cases", branches["selected_case_ids"] == ["VOER-ACA-007", "VOER-ACA-008"])
    branch_shape_ok = True
    for case_id in branches["selected_case_ids"]:
        for branch in branches["branches"][case_id].values():
            ids = [row["chunk_id"] for row in branch["candidates"]]
            branch_shape_ok &= len(ids) == len(set(ids)) == 20
    check("comparison_branch_candidate_shape", branch_shape_ok)
    check("comparison_branch_selection_qrel_free", branches["config"]["decomposition"]["uses_qrels"] is False)

    rerank_order_ok = True
    for case_rankings in comparison["branch_rankings"].values():
        for rows in case_rankings.values():
            rerank_order_ok &= len(rows) == 20
            rerank_order_ok &= all(rows[index - 1]["reranker_score"] >= rows[index]["reranker_score"]
                                   for index in range(1, len(rows)))
    check("comparison_branch_reranker_order", rerank_order_ok)
    merged_unique_ok = all(len(rows) == len({row["chunk_id"] for row in rows}) == 20
                           for rows in comparison["merged_rankings"].values())
    check("comparison_merged_unique_depth", merged_unique_ok)
    gates_ok = True
    for case_id, cutoff_rows in comparison["coverage_gates"].items():
        expected = {row["branch_id"] for row in branches["decomposition_audit"][case_id]["branches"]}
        for cutoff, stored in cutoff_rows.items():
            observed = {branch_id for row in comparison["merged_rankings"][case_id][:int(cutoff)]
                        for branch_id in row["branch_ids"]}
            gates_ok &= stored["passed"] == (observed == expected)
            gates_ok &= set(stored["observed_branch_ids"]) == observed
    check("comparison_coverage_gate_recompute", gates_ok)
    check("comparison_coverage_gate_top2", all(rows["2"]["passed"]
                                                for rows in comparison["coverage_gates"].values()))

    baseline_rankings = baseline["stages"]["reranker_pool_40"]["rankings"]
    combined = {
        case["case_id"]: comparison["merged_rankings"].get(case["case_id"], baseline_rankings[case["case_id"]])
        for case in corpus["cases"]
    }
    cutoffs = comparison["config"]["evaluation"]["cutoffs"]
    all_metrics, _ = evaluator.evaluate(corpus["cases"], combined, cutoffs)
    check("comparison_all_case_metrics_recompute",
          all_metrics == comparison["evaluation"]["all_cases_with_fallback"]["metrics"])
    selected_cases = [case for case in corpus["cases"] if case["case_id"] in branches["selected_case_ids"]]
    decomposed_metrics, _ = evaluator.evaluate(selected_cases, comparison["merged_rankings"], cutoffs)
    baseline_metrics, _ = evaluator.evaluate(
        selected_cases,
        {case["case_id"]: baseline_rankings[case["case_id"]] for case in selected_cases},
        cutoffs,
    )
    check("comparison_decomposed_metrics_recompute",
          decomposed_metrics == comparison["evaluation"]["comparison_cases_decomposed"]["metrics"])
    check("comparison_baseline_metrics_recompute",
          baseline_metrics == comparison["evaluation"]["comparison_cases_r3_baseline"]["metrics"])
    check("comparison_evidence_complete_at3", decomposed_metrics["3"]["evidence_groups_hit"] == 5 and
          decomposed_metrics["3"]["all_evidence_cases"] == 2)
    check("comparison_not_claimed_as_relevance_gain", decomposed_metrics["3"]["mean_binary_ndcg"] <
          baseline_metrics["3"]["mean_binary_ndcg"])

    tokenizer = __import__("tokenizers").Tokenizer.from_file(str(tokenizer_path))
    tokenizer.no_truncation()
    tokenizer.no_padding()
    chunks = {row["chunk_id"]: row for row in corpus["chunks"]}
    separator = code_results["config"]["packet"]["separator"]
    for stage_name, stage in code_results["stages"].items():
        budget = int(stage_name.rsplit("-b", 1)[1])
        packets = {row["case_id"]: row["packet"] for row in stage["cases"]}
        check("code_packet_unique:" + stage_name,
              all(len(packet["chunk_ids"]) == len(set(packet["chunk_ids"])) for packet in packets.values()))
        token_ok = True
        eligible_ok = True
        for packet in packets.values():
            rebuilt = r3_packer.token_count(
                tokenizer, [chunks[chunk_id]["embedding_text"] for chunk_id in packet["chunk_ids"]], separator
            )
            token_ok &= rebuilt == packet["tokens"] and rebuilt <= budget
            eligible_ok &= all(chunks[chunk_id]["embedding_eligible"] for chunk_id in packet["chunk_ids"])
        check("code_packet_budget_recompute:" + stage_name, token_ok)
        check("code_packet_text_eligible:" + stage_name, eligible_ok)
        rebuilt_metrics = r3_packer.packet_metrics(evaluator, corpus["cases"], packets)
        check("code_packet_metrics_recompute:" + stage_name, rebuilt_metrics["summary"] == stage["summary"])

    dependency = code_results["dependency_diagnostics"]
    check("code_dependency_text_coverage", dependency["summary"] ==
          {"covered": 6, "eligible": 6, "visual_unsupported": 1})
    dep03 = next(row for row in dependency["dependencies"] if row["dependency_id"] == "dep-03")
    check("code_dep03_prologue_restored", dep03["policy_covers_target"] and
          set(dep03["target_chunk_ids"]).issubset({item["chunk_id"] for trace in dep03["runtime_expansion_trace"]
                                                   for item in trace["added"]}))
    check("code_visual_not_silently_covered", all(not row["policy_covers_target"]
                                                   for row in dependency["dependencies"]
                                                   if row["visual_text_path_unsupported"]))
    check("dependency_labels_not_runtime_inputs", enrichment["runtime_ready"] is False and
          code_results["config"]["policy"]["dependency_labels_available_at_runtime"] is False)
    check("guard_code_packet_1024_incomplete",
          code_results["stages"]["x3-code-prologue-b1024"]["summary"]["all_evidence_cases"] == 9)

    malformed = branch_module.decompose("So sánh stack với queue", decomposition_config)
    check("guard_unsupported_comparison_falls_back", malformed["status"].startswith("unsupported_") and
          malformed["branches"] == [])
    sample = lambda chunk_id: {"chunk_id": chunk_id, "document_id": "d", "branch_rank": 1,
                               "reranker_score": 1.0, "embedding_tokens": 1, "preview": chunk_id}
    deduped = comparison_module.merge_round_robin(
        ["left", "right"], {"left": [sample("same"), sample("left-only")],
                            "right": [sample("same"), sample("right-only")]}, 3
    )
    check("guard_comparison_merge_deduplicates_with_provenance",
          len(deduped) == 3 and deduped[0]["branch_ids"] == ["left", "right"])

    failed = [row for row in checks if not row["passed"]]
    return {
        "status": "passed_with_findings" if not failed and findings else ("passed" if not failed else "failed"),
        "checks": len(checks),
        "passed": len(checks) - len(failed),
        "failed": failed,
        "findings": findings,
        "guards": 3,
        "artifacts": {
            "stability_sha256": digest(STABILITY),
            "comparison_branches_sha256": digest(BRANCHES),
            "comparison_results_sha256": digest(COMPARISON),
            "code_prologue_sha256": digest(CODE_RESULTS),
        },
    }


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
