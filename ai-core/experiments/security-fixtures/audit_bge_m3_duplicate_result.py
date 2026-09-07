"""Audit the persisted E0.7 BGE-M3 duplicate ablation result without re-encoding."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
RESULT = ROOT / "data" / "evaluation" / "synthetic" / "duplicate-detection-v0.1" / "e07-bge-m3-duplicate-results.json"
CORPUS = ROOT / "tmp" / "e07-bge-m3-duplicate" / "corpus.json"
PREPARE = Path(__file__).with_name("prepare_bge_m3_duplicate_corpus.py")
RUNNER = Path(__file__).with_name("run_bge_m3_duplicate_ablation.py")


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    result = json.loads(RESULT.read_text(encoding="utf-8"))
    issues: list[str] = []

    relations = result["relation_scores"]
    expected = [row for row in relations if row["candidate_expected"]]
    negatives = [row for row in relations if not row["candidate_expected"]]
    for cutoff in (1, 3, 5):
        measured = sum(row["rank"] <= cutoff for row in expected) / len(expected)
        if round(measured, 6) != result["dense_candidate_recall"][f"at_{cutoff}"]:
            issues.append(f"recall_at_{cutoff}_mismatch")

    if len(relations) != result["corpus"]["physical_relations"]:
        issues.append("relation_count_mismatch")
    if len(expected) != result["corpus"]["candidate_expected_relations"]:
        issues.append("expected_relation_count_mismatch")
    if len(negatives) != 2:
        issues.append("negative_relation_count_mismatch")
    if len({row["pair_id"] for row in relations}) != len(relations):
        issues.append("duplicate_pair_id")
    if digest(CORPUS) != result["corpus"]["sha256"]:
        issues.append("corpus_hash_mismatch")
    if digest(PREPARE) != result["implementation"]["prepare_script_sha256"]:
        issues.append("prepare_script_hash_mismatch")
    if digest(RUNNER) != result["implementation"]["runner_sha256"]:
        issues.append("runner_script_hash_mismatch")
    if result["deterministic_probe_max_abs_delta"] != 0.0:
        issues.append("deterministic_probe_nonzero")
    if any(result["restrictions"][key] for key in (
        "serving_index_written",
        "vectors_persisted",
        "external_processing",
        "auto_merge_or_publish",
        "threshold_selected",
        "security_detection_claim",
    )):
        issues.append("restriction_guard_failed")
    critical = {row["pair_id"]: row for row in result["critical_negatives"]}
    if critical["DUP-016"]["dense_pair_score"] != 0.997499:
        issues.append("critical_negative_score_mismatch")

    print(json.dumps({
        "status": "passed" if not issues else "failed",
        "checks": 13,
        "relations": len(relations),
        "candidate_expected": len(expected),
        "negatives": len(negatives),
        "issues": issues,
    }, ensure_ascii=False, indent=2))
    if issues:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
