"""Audit persisted E0.8 hard-negative and routing results without re-encoding."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[3]
RESULT = ROOT / "data" / "evaluation" / "synthetic" / "duplicate-detection-v0.1" / "e08-hard-negative-routing-results.json"
PDF_MANIFEST = ROOT / "data" / "evaluation" / "synthetic" / "duplicate-detection-v0.1" / "e08-hard-negative-pdf-manifest.json"
CORPUS = ROOT / "tmp" / "e08-candidate-routing" / "corpus.json"
REPEAT = ROOT / "tmp" / "e08-candidate-routing" / "repeat-run.json"
GENERATOR = Path(__file__).with_name("generate_e08_hard_negative_pdf_fixtures.py")
PREPARE = Path(__file__).with_name("prepare_e08_candidate_corpus.py")
RUNNER = Path(__file__).with_name("run_e08_bge_m3_candidate_routing.py")


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    result = json.loads(RESULT.read_text(encoding="utf-8"))
    repeat = json.loads(REPEAT.read_text(encoding="utf-8"))
    corpus = json.loads(CORPUS.read_text(encoding="utf-8"))
    pdf_manifest = json.loads(PDF_MANIFEST.read_text(encoding="utf-8"))
    issues: list[str] = []
    checks = 0

    def check(condition: bool, message: str) -> None:
        nonlocal checks
        checks += 1
        if not condition:
            issues.append(message)

    check(result["status"] == "completed_local_hard_negative_and_candidate_routing_diagnostic", "status")
    check(digest(CORPUS) == result["corpus"]["sha256"], "corpus hash")
    check(digest(GENERATOR) == result["implementation"]["generator_sha256"], "generator hash")
    check(digest(PREPARE) == result["implementation"]["prepare_corpus_sha256"], "prepare hash")
    check(digest(RUNNER) == result["implementation"]["runner_sha256"], "runner hash")
    check(result["corpus"]["documents"] == 60, "document count")
    check(result["corpus"]["hard_negatives"] == 24, "hard-negative count")
    check(result["corpus"]["candidate_expected_relations"] == 19, "expected relation count")
    check(pdf_manifest["pdf_count"] == 24 and pdf_manifest["page_count"] == 24, "PDF manifest counts")
    check(pdf_manifest["visual_qa"]["status"] == "passed_manual_contact_sheet_review", "visual QA status")
    check(pdf_manifest["visual_qa"]["defects_observed"] == 0, "visual QA defects")
    check(len({item["pdf_sha256"] for item in pdf_manifest["documents"]}) == 24, "unique PDF hashes")

    diagnostics = result["relation_diagnostics"]
    check(len(diagnostics) == 19, "relation diagnostic count")
    dense_ranks = [int(item["dense_relevant_rank"]) for item in diagnostics]
    minhash_ranks = [int(item["minhash_relevant_rank"]) for item in diagnostics]
    check(sum(rank <= 1 for rank in dense_ranks) == 18, "dense recall@1 numerator")
    check(max(dense_ranks) == 2, "dense full-recall budget")
    check(all(rank == 1 for rank in minhash_ranks), "MinHash relevant ranks")

    labels = corpus["document_eval_labels"]
    dense_top3_hard = sum(
        labels[str(row["filename"])]["role"] == "hard_negative"
        for item in diagnostics
        for row in item["dense_top_5"][:3]
    )
    check(dense_top3_hard == result["retrievers"]["bge_m3_dense"]["cutoffs"]["at_3"]["hard_negative_intrusions"], "dense top-3 hard intrusions")

    route = result["routing"]["raw_canonical_then_bge_at_3"]
    check(route["recall"] == 1.0, "route recall")
    check(route["retriever_queries"] == 12 and route["retriever_queries_avoided"] == 7, "route query counts")
    check(route["total_candidate_reviews"] == 44 and route["false_candidate_reviews"] == 25, "route review counts")
    check(route["hard_negative_intrusions"] == 2, "route hard intrusions")
    check(result["unions"]["minhash_bge_m3"]["at_3"]["false_candidate_slots"] == 60, "union false candidates")
    check(result["deterministic_probe_max_abs_delta"] == 0.0, "determinism probe")
    check(all(value is False for value in result["restrictions"].values()), "restriction flags")
    check(corpus["labels_excluded_from_embedding_text"] is True, "label leakage guard")

    check(repeat["corpus"]["sha256"] == result["corpus"]["sha256"], "repeat corpus identity")
    repeat_score_deltas: list[float] = []
    repeat_order_changes: list[str] = []
    for saved_item, repeat_item in zip(result["relation_diagnostics"], repeat["relation_diagnostics"]):
        if saved_item["pair_id"] != repeat_item["pair_id"]:
            repeat_order_changes.append("relation_order")
            continue
        repeat_score_deltas.append(abs(float(saved_item["dense_relevant_score"]) - float(repeat_item["dense_relevant_score"])))
        if saved_item["dense_relevant_rank"] != repeat_item["dense_relevant_rank"]:
            repeat_order_changes.append(f"{saved_item['pair_id']}:relevant_rank")
        for rank, (saved_row, repeat_row) in enumerate(zip(saved_item["dense_top_5"], repeat_item["dense_top_5"]), start=1):
            repeat_score_deltas.append(abs(float(saved_row["score"]) - float(repeat_row["score"])))
            if saved_row["filename"] != repeat_row["filename"]:
                repeat_order_changes.append(f"{saved_item['pair_id']}:top_{rank}")
    repeat_max_delta = max(repeat_score_deltas)
    check(repeat_max_delta == 0.0, "cross-process score repeatability")
    check(not repeat_order_changes, "cross-process rank repeatability")
    check(repeat["retrievers"] == result["retrievers"], "cross-process aggregate repeatability")

    payload = {
        "status": "passed" if not issues else "failed",
        "checks": checks,
        "documents": result["corpus"]["documents"],
        "hard_negatives": result["corpus"]["hard_negatives"],
        "candidate_expected_relations": result["corpus"]["candidate_expected_relations"],
        "cross_process_repeat": {
            "max_abs_score_delta": repeat_max_delta,
            "rank_or_top5_order_changes": repeat_order_changes,
            "saved_encode_seconds": result["timing"]["encode"]["seconds"],
            "repeat_encode_seconds": repeat["timing"]["encode"]["seconds"],
        },
        "issues": issues,
    }
    sys.stdout.reconfigure(encoding="utf-8")
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    if issues:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
