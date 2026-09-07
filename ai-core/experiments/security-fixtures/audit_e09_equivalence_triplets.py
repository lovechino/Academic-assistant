"""Audit persisted E0.9 triplet results without re-encoding BGE-M3."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[3]
RESULT = ROOT / "data" / "evaluation" / "synthetic" / "duplicate-detection-v0.1" / "e09-equivalence-triplet-results.json"
PDF_MANIFEST = ROOT / "data" / "evaluation" / "synthetic" / "duplicate-detection-v0.1" / "e09-equivalence-triplet-pdf-manifest.json"
CORPUS = ROOT / "tmp" / "e09-equivalence-triplets" / "corpus.json"
GENERATOR = Path(__file__).with_name("generate_e09_equivalence_triplet_pdfs.py")
PREPARE = Path(__file__).with_name("prepare_e09_equivalence_corpus.py")
RUNNER = Path(__file__).with_name("run_e09_equivalence_triplet_ablation.py")


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    result = json.loads(RESULT.read_text(encoding="utf-8"))
    manifest = json.loads(PDF_MANIFEST.read_text(encoding="utf-8"))
    corpus = json.loads(CORPUS.read_text(encoding="utf-8"))
    issues: list[str] = []
    checks = 0

    def check(condition: bool, message: str) -> None:
        nonlocal checks
        checks += 1
        if not condition:
            issues.append(message)

    check(result["status"] == "completed_local_triplet_candidate_and_equivalence_diagnostic", "status")
    check(digest(CORPUS) == result["corpus"]["sha256"], "corpus hash")
    check(digest(GENERATOR) == result["implementation"]["generator_sha256"], "generator hash")
    check(digest(PREPARE) == result["implementation"]["prepare_corpus_sha256"], "prepare hash")
    check(digest(RUNNER) == result["implementation"]["runner_sha256"], "runner hash")
    check(result["corpus"]["documents"] == 96 and result["corpus"]["pages"] == 100, "corpus counts")
    check(result["corpus"]["triplet_documents"] == 36 and result["corpus"]["triplets"] == 12, "triplet counts")
    check(manifest["pdf_count"] == 36 and manifest["triplet_count"] == 12, "PDF manifest counts")
    check(manifest["visual_qa"]["status"] == "passed_manual_contact_sheet_review", "visual QA status")
    check(manifest["visual_qa"]["defects_observed"] == 0, "visual QA defects")
    check(len({row["pdf_sha256"] for row in manifest["documents"]}) == 36, "unique PDF hashes")
    check(all(row["role_present_in_model_text"] is False for row in manifest["documents"]), "role leakage PDF audit")
    check(corpus["labels_excluded_from_embedding_text"] is True, "model input label guard")
    check(len({row["triplet_id"] for row in corpus["triplets"]}) == 12, "unique triplet ids")

    for method_name, method in result["methods"].items():
        check(method["pairwise"]["triplets"] == 12, f"{method_name} denominator")
        check(method["pairwise"]["equivalent_preferred"] == 0, f"{method_name} equivalent preferences")
        check(method["pairwise"]["conflict_preferred"] == 12, f"{method_name} conflict preferences")
        check(method["cutoffs"]["at_2"]["dual_hits"] == 12, f"{method_name} dual coverage@2")
        check(method["mean_equivalent_rank"] == 2.0 and method["mean_conflict_rank"] == 1.0, f"{method_name} mean ranks")
        check(method["score_ranges"]["global_threshold_separates_equivalent_from_conflict"] is False, f"{method_name} threshold claim")

    bge = result["methods"]["bge_m3_dense"]
    check(bge["score_ranges"]["conflict_min"] > bge["score_ranges"]["equivalent_max"], "BGE reversed score separation")
    check(bge["pairwise"]["mean_equivalence_margin"] < 0, "BGE negative mean margin")
    check(result["within_session_repeat_max_abs_delta"] == 0.0, "within-session repeat")
    check(all(value is False for value in result["restrictions"].values()), "restriction flags")
    check(result["evaluation_semantics"]["second_stage_goal"] == "prefer equivalent over conflicting claim", "evaluation semantics")

    payload = {
        "status": "passed" if not issues else "failed",
        "checks": checks,
        "documents": result["corpus"]["documents"],
        "triplets": result["corpus"]["triplets"],
        "observed_outcome": "all_three_methods_ranked_conflict_first_and_equivalent_second",
        "issues": issues,
    }
    sys.stdout.reconfigure(encoding="utf-8")
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    if issues:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
