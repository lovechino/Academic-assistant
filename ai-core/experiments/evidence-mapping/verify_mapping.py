"""Read-only integrity and synthetic coverage checks; not a RAG evaluator."""
from __future__ import annotations

import ast
import hashlib
import html
import json
from pathlib import Path
import re


ROOT = Path(__file__).resolve().parents[3]
PACK = ROOT / "data/evaluation/silver/voer-dsa-evidence-map-v0.1"


def normalize(value: str) -> str:
    """Reproduce legacy silver text offsets, not production HTML parsing."""
    return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", value))).strip()


def sha(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def coverage(case: dict, locator_ids: set[str]) -> dict:
    """Toy set coverage on pre-matched locators; does not match retrieved text."""
    groups = case["evidence_groups"]
    covered = {
        group["id"] for group in groups
        if any(set(alt["all_of_locators"]).issubset(locator_ids) for alt in group["alternatives"])
    }
    return {
        "covered_groups": len(covered), "required_groups": len(groups),
        "all_evidence_present": all(group["id"] in covered for group in groups),
        "claims_with_all_evidence": sum(set(claim["all_of_groups"]).issubset(covered) for claim in case["claims"]),
        "required_claims": len(case["claims"]),
    }


def main() -> int:
    mapping = json.loads((PACK / "evidence-map.json").read_text(encoding="utf-8"))
    issues = json.loads((PACK / "review-issues.json").read_text(encoding="utf-8"))
    errors: list[str] = []
    checks = 0

    def check(condition: bool, label: str) -> None:
        nonlocal checks
        checks += 1
        if not condition:
            errors.append(label)

    def resolve(relative: str) -> Path:
        path = (ROOT / relative).resolve()
        if not path.is_relative_to(ROOT):
            raise ValueError("Reference outside repository")
        return path

    check(mapping["status"] == "silver_dev_mapping" and not mapping["human_reviewed"], "Silver status")
    check(mapping["normalization"]["id"] == "voer-html-regex-space-v1", "Normalization ID")
    profile = json.loads(resolve(mapping["profile_ref"]).read_text(encoding="utf-8"))
    check(profile["corpus_snapshot"] == mapping["corpus_snapshot"], "Profile snapshot")
    source_path = resolve(mapping["source_case_file"]["path"])
    check(sha(source_path.read_bytes()) == mapping["source_case_file"]["sha256"], "Source cases checksum")
    source_cases = {json.loads(line)["id"]: (n, json.loads(line)) for n, line in enumerate(source_path.read_text(encoding="utf-8").splitlines(), 1) if line.strip()}
    expected_ids = next(group["case_ids"] for group in profile["groups"] if group["id"] == "academic_answerable")
    check([case["id"] for case in mapping["cases"]] == expected_ids, "Selected answerable IDs")

    documents = {doc["document_id"]: doc for doc in mapping["documents"]}
    locators = {loc["id"]: loc for loc in mapping["locators"]}
    check(len(documents) == len(mapping["documents"]), "Unique document IDs")
    check(len(locators) == len(mapping["locators"]), "Unique locator IDs")
    texts = {}
    for doc_id, doc in documents.items():
        path = resolve(doc["source_path"])
        payload = path.read_bytes()
        source = json.loads(payload)["data"]
        text = normalize(source["text"])
        texts[doc_id] = text
        check(sha(payload) == doc["source_file_sha256"], doc_id + " file hash")
        check(doc_id == "voer-module-" + source["material_id"], doc_id + " identity")
        check(source["version"] == doc["source_version"] and source["modified"] == doc["source_modified"], doc_id + " version")
        check(source["title"] == doc["title_as_source"], doc_id + " source title")
        check([a["fullname"] for a in source.get("author", [])] == doc["authors_as_source"], doc_id + " attribution")
        check(sha(source["text"].encode("utf-8")) == doc["raw_html_sha256"], doc_id + " HTML hash")
        check(sha(text.encode("utf-8")) == doc["normalized_text_sha256"], doc_id + " normalized hash")
        check(len(text) == doc["normalized_text_codepoints"], doc_id + " normalized length")

    for loc_id, loc in locators.items():
        check(loc["document_id"] in texts, loc_id + " document reference")
        text = texts[loc["document_id"]]
        start, end = loc["start"], loc["end"]
        check(isinstance(start, int) and isinstance(end, int) and 0 <= start < end <= len(text), loc_id + " offset bounds")
        check(text[start:end] == loc["quote"], loc_id + " exact quote")
        check(text.count(loc["quote"]) == loc["occurrences_in_document"] == 1, loc_id + " unique occurrence")
        check(sha(loc["quote"].encode("utf-8")) == loc["quote_sha256"], loc_id + " quote hash")
        check(text[max(0, start-100):start] == loc["prefix"] and text[end:end+100] == loc["suffix"], loc_id + " context anchors")
        check(loc["kind"] == "normalized_text_span" and loc["json_pointer"] == "/data/text", loc_id + " coordinate space")

    used_locators: set[str] = set()
    claim_count = group_count = cross_document_count = 0
    for case in mapping["cases"]:
        source_line, source = source_cases[case["id"]]
        check(case["source_case_ref"] == {"path": mapping["source_case_file"]["path"], "line_1based": source_line}, case["id"] + " source line")
        check(case["query"] == source["query"], case["id"] + " unchanged query")
        check(case["answerability_as_source"] == source["answerability"] and case["mode_as_source"] == source["mode"], case["id"] + " unchanged labels")
        check([claim["text"] for claim in case["claims"]] == source["required_claims"], case["id"] + " unchanged required claims")
        check(not case["human_reviewed"], case["id"] + " review status")
        groups = {group["id"]: group for group in case["evidence_groups"]}
        check(len(groups) == len(case["evidence_groups"]) and bool(groups), case["id"] + " unique nonempty groups")
        local_locators = set()
        for group in groups.values():
            check(group["required"] and bool(group["alternatives"]), group["id"] + " required alternatives")
            for alt in group["alternatives"]:
                ids = alt["all_of_locators"]
                check(bool(ids) and len(ids) == len(set(ids)), group["id"] + " nonvacuous locator AND")
                check(all(loc_id in locators for loc_id in ids), group["id"] + " locator references")
                local_locators.update(ids)
        claimed_groups = set()
        for i, claim in enumerate(case["claims"]):
            check(claim["id"] == case["id"] + "-C" + str(i+1) and claim["source_required_claim_index_0based"] == i, claim["id"] + " claim identity")
            check(bool(claim["all_of_groups"]) and all(g in groups for g in claim["all_of_groups"]), claim["id"] + " group dependencies")
            claimed_groups.update(claim["all_of_groups"])
        check(claimed_groups == set(groups), case["id"] + " no orphan groups")
        used_locators.update(local_locators)
        cross_document_count += len({locators[loc_id]["document_id"] for loc_id in local_locators}) > 1
        claim_count += len(case["claims"])
        group_count += len(groups)
    check(used_locators == set(locators), "No unused locators")
    computed_counts = {"cases": len(mapping["cases"]), "claims": claim_count, "evidence_groups": group_count, "locators": len(locators), "source_documents": len(documents), "cross_document_cases": cross_document_count}
    check(mapping["counts"] == computed_counts, "Computed counts")
    check(issues["mapping_id"] == mapping["mapping_id"] and not issues["human_reviewed"], "Issue pack identity/status")
    issue_ids = {issue["id"] for issue in issues["issues"]}
    check(len(issue_ids) == len(issues["issues"]), "Unique review issue IDs")
    for case in mapping["cases"]:
        check(all(issue_id in issue_ids for issue_id in case["review_issue_ids"]), case["id"] + " issue references")

    # These are deliberate toy evidence removals, not retriever/model outputs.
    scenarios = [
        ("only-stack-rule", "001", ["stack-lifo"], 1, False),
        ("valid-alternative-rule", "001", ["stack-lifo-alt", "stack-push", "stack-pop"], 3, True),
        ("only-queue-rule", "002", ["queue-fifo"], 1, False),
        ("missing-node-link", "003", ["list-data"], 0, False),
        ("missing-node-data", "003", ["list-link-null"], 1, False),
        ("only-overflow-cause", "006", ["queue-overflow"], 1, False),
        ("only-stack-half", "007", ["stack-lifo"], 1, False),
        ("both-comparison-sides", "007", ["stack-lifo", "queue-fifo"], 2, True),
        ("missing-list-side", "008", ["array-fixed", "array-index"], 2, False),
        ("two-docs-but-missing-requirement", "009", ["problem-ipo", "algorithm-resources"], 2, False),
        ("all-problem-evidence", "009", ["problem-ipo", "problem-requirements", "algorithm-resources"], 3, True),
        ("only-null-side", "010", ["list-link-null"], 1, False),
    ]
    case_index = {case["id"]: case for case in mapping["cases"]}
    scenario_results = []
    if not errors:
        for name, suffix, ids, expected_count, expected_all in scenarios:
            result = coverage(case_index["VOER-ACA-" + suffix], set(ids))
            check(result["covered_groups"] == expected_count and result["all_evidence_present"] == expected_all, "Synthetic coverage: " + name)
            if suffix == "007" and name == "only-stack-half":
                check(result["claims_with_all_evidence"] == 1, "Comparison synthesis requires both groups")
            scenario_results.append({"id": name, "case_id": "VOER-ACA-" + suffix, "provided_locator_ids": ids, **result, "expected_all_evidence_present": expected_all})
        for case in mapping["cases"]:
            check(not coverage(case, set())["all_evidence_present"], case["id"] + " empty evidence rejected")
            check(coverage(case, set(locators))["all_evidence_present"], case["id"] + " all mapped evidence accepted")

    # Parse self without importing any runtime source or historical PDF helpers.
    ast.parse(Path(__file__).read_text(encoding="utf-8"))
    print(json.dumps({
        "status": "passed" if not errors else "failed", "mapping_id": mapping["mapping_id"],
        "mapping_sha256": sha((PACK / "evidence-map.json").read_bytes()),
        "verifier_sha256": sha(Path(__file__).read_bytes()),
        "integrity_checks_including_synthetic_assertions": checks, "failures": errors,
        "counts": computed_counts, "synthetic_coverage_scenarios": scenario_results,
        "interpretation": "Source integrity and toy Boolean coverage only; no retrieval, generation, human adjudication or accuracy measurement.",
    }, ensure_ascii=False, indent=2))
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
