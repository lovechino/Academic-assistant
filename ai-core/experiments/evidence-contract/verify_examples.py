"""Read-only integrity checks for hand-authored evidence contract examples.

Not a general JSON Schema validator, parser, retriever, semantic judge or API test.
"""
from __future__ import annotations

from copy import deepcopy
import hashlib
import html
import json
from pathlib import Path
import re


ROOT = Path(__file__).resolve().parents[3]
PACK = ROOT / "data/evaluation/silver/voer-dsa-contract-examples-v0.1"
MAP_PATH = ROOT / "data/evaluation/silver/voer-dsa-evidence-map-v0.1/evidence-map.json"


def sha(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def canonical_ref(doc: dict) -> dict:
    return {"document_id": doc["document_id"], "source_version": doc["source_version"],
            "source_file_sha256": doc["source_file_sha256"],
            "representation_id": "voer-html-regex-space-v1",
            "representation_sha256": doc["normalized_text_sha256"]}


def covered_locators(fragments: list[dict], mapping: dict) -> set[str]:
    documents = {d["document_id"]: d for d in mapping["documents"]}
    covered = set()
    for locator in mapping["locators"]:
        intervals = []
        expected_ref = canonical_ref(documents[locator["document_id"]])
        for fragment in fragments:
            if fragment["document_ref"] == expected_ref:
                span = fragment["span"]
                intervals.append((span["start"], span["end"]))
        cursor = locator["start"]
        for start, end in sorted(intervals):
            if end <= cursor:
                continue
            if start > cursor:
                break
            cursor = max(cursor, end)
        if cursor >= locator["end"]:
            covered.add(locator["id"])
    return covered


def covered_groups(case: dict, locators: set[str]) -> set[str]:
    return {group["id"] for group in case["evidence_groups"]
            if any(set(option["all_of_locators"]) <= locators for option in group["alternatives"])}


def validate(bundle: dict, sidecar: dict, mapping: dict, texts: dict) -> dict:
    errors = []
    checks = 0

    def check(ok: bool, code: str, label: str):
        nonlocal checks
        checks += 1
        if not ok:
            errors.append({"code": code, "label": label})

    expected_docs = {d["document_id"]: d for d in mapping["documents"]}
    docs = {d["document_ref"]["document_id"]: d for d in bundle["documents"]}
    elements = {e["element_id"]: e for e in bundle["elements"]}
    chunks = {c["chunk_id"]: c for c in bundle["chunks"]}
    windows = {w["context_window_id"]: w for w in bundle["context_windows"]}
    for field, records in [("documents", docs), ("elements", elements), ("chunks", chunks), ("context_windows", windows)]:
        check(len(records) == len(bundle[field]), "duplicate_id", field)
    check(bundle["restrictions"] == {"usage": "local_research_reference", "serving_authorized": False,
                                    "external_processing_authorized": False, "training_authorized": False},
          "research_boundary", "bundle restrictions")
    check(bundle["index_plan"]["status"] == "not_built" and bundle["index_plan"]["examples_are_not_corpus_allowlist"]
          and bundle["index_plan"]["candidate_corpus_module_count"] == 16,
          "index_not_run", "index plan not a source allowlist")

    def ref_ok(ref: dict, label: str):
        check(ref["document_id"] in expected_docs and ref == canonical_ref(expected_docs[ref["document_id"]]),
              "source_identity", label)

    def span_ok(ref: dict, span: dict, label: str):
        ref_ok(ref, label)
        text = texts[ref["document_id"]]
        check(set(span) == {"coordinate_system", "json_pointer", "start", "end", "text", "text_sha256"},
              "locator_shape", label)
        check(span["coordinate_system"] == "unicode_codepoint_half_open" and span["json_pointer"] == "/data/text",
              "locator_coordinates", label)
        check(0 <= span["start"] < span["end"] <= len(text), "locator_bounds", label)
        check(text[span["start"]:span["end"]] == span["text"] and sha(span["text"]) == span["text_sha256"],
              "source_text_integrity", label)

    def contains(outer: dict, inner: dict) -> bool:
        return outer["start"] <= inner["start"] and outer["end"] >= inner["end"]

    for doc_id, doc in docs.items():
        ref_ok(doc["document_ref"], doc_id)
        original = expected_docs[doc_id]
        check(doc["title"] == original["title_as_source"] and doc["authors"] == original["authors_as_source"],
              "attribution", doc_id)
        check(doc["raw_source"]["path"] == original["source_path"] and doc["raw_source"]["raw_html_sha256"] == original["raw_html_sha256"],
              "raw_provenance", doc_id)
        check(doc["rights_state"] == original["rights_state"] and not doc["serving_authorized"]
              and doc["academic_approval"] == "not_reviewed", "research_boundary", doc_id)
        check(doc["origin_kind"] == "html_in_json" and not doc["representation"]["full_document_parsed"]
              and not doc["representation"]["dom_mapping_available"], "not_a_parser", doc_id)
    for element_id, element in elements.items():
        span_ok(element["document_ref"], element["span"], element_id)
        check(element["element_type"] == "text_excerpt" and element["boundary_origin"] == "manual_reference_span_not_parser"
              and element["section_hint"]["verified_anchor"] is None, "not_a_parser", element_id)
    for window_id, window in windows.items():
        span_ok(window["document_ref"], window["span"], window_id)
        check(not window["is_verified_section"], "not_a_parser", window_id)
        for element_id in window["element_ids"]:
            element = elements.get(element_id)
            check(element is not None and element["document_ref"] == window["document_ref"]
                  and contains(window["span"], element["span"]), "element_lineage", window_id + ":" + element_id)
    for chunk_id, chunk in chunks.items():
        window = windows.get(chunk["context_window_id"])
        check(window is not None and window["document_ref"] == chunk["document_ref"], "parent_lineage", chunk_id)
        check(not chunk["retrieval_header"]["citable"] and not chunk["production_index_eligible"], "research_boundary", chunk_id)
        for span in chunk["source_fragments"]:
            span_ok(chunk["document_ref"], span, chunk_id)
            check(window is not None and contains(window["span"], span), "parent_lineage", chunk_id)
            check(any(elements.get(eid) is not None and elements[eid]["document_ref"] == chunk["document_ref"]
                      and contains(elements[eid]["span"], span) for eid in chunk["element_ids"]), "element_lineage", chunk_id)

    eval_by_id = {e["example_id"]: e for e in sidecar["cases"]}
    cases = {c["id"]: c for c in mapping["cases"]}
    diagnostics = []
    for example in bundle["examples"]:
        example_id = example["example_id"]
        evaluation = eval_by_id[example_id]
        case = cases[evaluation["reference_case_id"]]
        model_input = example["model_input"]
        check(set(model_input) == {"request_id", "question", "execution_scope", "evidence_packet"},
              "oracle_input_leak", example_id)
        forbidden = {"reference_answer", "required_claims", "evidence_groups", "qrels", "expected", "gold_answer"}
        def has_forbidden(value):
            if isinstance(value, dict):
                return bool(set(value) & forbidden) or any(has_forbidden(v) for v in value.values())
            return isinstance(value, list) and any(has_forbidden(v) for v in value)
        check(not has_forbidden(model_input), "oracle_input_leak", example_id)
        check(model_input["question"] == case["query"], "query_identity", example_id)
        check(model_input["execution_scope"] == {"mode": "local_reference_example", "serving_authorized": False,
                                                "external_processing_authorized": False}, "research_boundary", example_id)
        packet = model_input["evidence_packet"]
        check(packet["answerability_assessment"] == {"status": "not_assessed", "method": None},
              "oracle_input_leak", example_id)
        items = {item["item_id"]: item for item in packet["items"]}
        check(len(items) == len(packet["items"]), "duplicate_id", example_id)
        for item_id, item in items.items():
            span_ok(item["document_ref"], item["span"], item_id)
            kind = item["origin_ref"]["kind"]
            origin = (chunks if kind == "chunk" else windows).get(item["origin_ref"]["id"])
            spans = [] if origin is None else origin.get("source_fragments", [origin.get("span")])
            check(kind in {"chunk", "context_window"} and origin is not None and origin["document_ref"] == item["document_ref"]
                  and any(s and contains(s, item["span"]) for s in spans), "packet_lineage", item_id)
            check(item["kind"] == "source_evidence" and not item["context_header"]["citable"], "header_not_evidence", item_id)
        budget = packet["budget"]
        check(budget["source_codepoints"] == sum(len(i["span"]["text"]) for i in items.values()), "budget_accounting", example_id)
        check(budget["measurement_state"] == "not_configured" and budget["tokenizer_id"] is None
              and budget["context_limit_tokens"] is None and budget["serialized_input_tokens"] is None
              and not budget["token_fit_claimed"], "token_budget_unmeasured", example_id)
        trace = example["retrieval_trace"]
        check(trace["origin"] == "hand_authored_candidates_not_search" and trace["scores"] is None
              and trace["index_revision"] is None, "retrieval_not_run", example_id)
        retrieved = [{"document_ref": chunks[cid]["document_ref"], "span": span}
                     for cid in trace["candidate_chunk_ids"] for span in chunks[cid]["source_fragments"]]
        before = covered_groups(case, covered_locators(retrieved, mapping))
        after = covered_groups(case, covered_locators(list(items.values()), mapping))
        supported = {c["id"] for c in case["claims"] if set(c["all_of_groups"]) <= after}
        actual = {"retrieved_groups": len(before), "packed_groups": len(after),
                  "required_groups": len(case["evidence_groups"]), "claims_with_evidence": len(supported),
                  "required_claims": len(case["claims"])}
        check(actual == evaluation["expected"], "coverage_expectation", example_id)
        draft = example["answer_draft"]
        check(draft["origin"] == "assistant_written_example_not_model_output" and draft["delivery_state"] == "not_authorized_for_serving",
              "research_boundary", example_id)
        citation_items = set()
        for citation in draft["citations"]:
            item = items.get(citation["item_ref"])
            check(item is not None, "citation_not_in_packet", example_id)
            check(set(citation) == {"citation_id", "item_ref", "source_ref", "title", "source_version", "locator", "viewer_state", "url"},
                  "public_projection", example_id)
            if item is None:
                continue
            citation_items.add(item["item_id"])
            check(citation["source_version"] == item["document_ref"]["source_version"]
                  and citation["locator"] == {"kind": "normalized_text_span", "representation_id": item["document_ref"]["representation_id"],
                                             "start": item["span"]["start"], "end": item["span"]["end"],
                                             "coordinate_system": "unicode_codepoint_half_open"}, "citation_locator", example_id)
            check(citation["viewer_state"] == "not_implemented" and citation["url"] is None, "viewer_not_run", example_id)
        reference_claims = {c["id"]: c for c in case["claims"]}
        claim_refs = {c["draft_claim_id"]: c["reference_claim_id"] for c in evaluation["draft_to_reference_claims"]}
        for claim in draft["claims"]:
            linked = claim["citation_item_ids"]
            check(bool(linked) and set(linked) <= citation_items, "citation_not_in_packet", claim["claim_id"])
            linked_groups = covered_groups(case, covered_locators([items[i] for i in linked if i in items], mapping))
            needed = reference_claims[claim_refs[claim["claim_id"]]]["all_of_groups"]
            check(set(needed) <= linked_groups, "claim_citation_coverage", claim["claim_id"])
        lost = sorted(before - after)
        check(("packing_loss" if lost else None) == evaluation["expected_failure"], "failure_classification", example_id)
        diagnostics.append({"example_id": example_id, **actual, "lost_group_ids_evaluator_only": lost,
                            "source_codepoints": budget["source_codepoints"], "tokens_measured": False,
                            "draft_claims": len(draft["claims"]), "semantic_correctness": "not_evaluated"})
    return {"status": "passed" if not errors else "failed", "checks": checks, "errors": errors, "diagnostics": diagnostics}


def main() -> int:
    bundle = json.loads((PACK / "examples.json").read_text(encoding="utf-8"))
    sidecar = json.loads((PACK / "evaluation-sidecar.json").read_text(encoding="utf-8"))
    mapping = json.loads(MAP_PATH.read_text(encoding="utf-8"))
    texts = {}
    preflight = []
    expected_documents = {d["document_id"]: d for d in mapping["documents"]}
    for record in bundle["documents"]:
        doc_id = record["document_ref"]["document_id"]
        expected = expected_documents[doc_id]
        raw = (ROOT / expected["source_path"]).read_bytes()
        source = json.loads(raw)["data"]
        text = re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", source["text"]))).strip()
        texts[doc_id] = text
        if (hashlib.sha256(raw).hexdigest() != expected["source_file_sha256"]
                or sha(source["text"]) != expected["raw_html_sha256"] or sha(text) != expected["normalized_text_sha256"]):
            preflight.append("source_checksum:" + doc_id)
    if hashlib.sha256(MAP_PATH.read_bytes()).hexdigest() != sidecar["mapping_ref"]["sha256"]:
        preflight.append("mapping_checksum")
    baseline = validate(bundle, sidecar, mapping, texts)
    mutations = []
    def mutate(name: str, expected_code: str, change):
        modified = deepcopy(bundle)
        change(modified)
        result = validate(modified, sidecar, mapping, texts)
        codes = sorted({error["code"] for error in result["errors"]})
        mutations.append({"id": name, "expected_error": expected_code, "observed_errors": codes,
                          "detected": expected_code in codes})
    mutate("stale_source_hash", "source_identity", lambda b: b["examples"][0]["model_input"]["evidence_packet"]["items"][0]["document_ref"].update(source_file_sha256="0" * 64))
    mutate("changed_source_text", "source_text_integrity", lambda b: b["elements"][0]["span"].update(text="invented"))
    mutate("fake_pdf_page_on_html", "locator_shape", lambda b: b["elements"][0]["span"].update(physical_page_index=0))
    mutate("wrong_document_parent", "parent_lineage", lambda b: b["chunks"][0].update(context_window_id="window-voer-module-387652b5"))
    mutate("oracle_claims_in_model_input", "oracle_input_leak", lambda b: b["examples"][0]["model_input"].update(required_claims=["gold hint"]))
    mutate("citation_to_omitted_evidence", "citation_not_in_packet", lambda b: b["examples"][3]["answer_draft"]["citations"].append(deepcopy(bundle["examples"][2]["answer_draft"]["citations"][1])))
    mutate("fake_token_fit", "token_budget_unmeasured", lambda b: b["examples"][0]["model_input"]["evidence_packet"]["budget"].update(token_fit_claimed=True))
    mutate("research_promoted_to_serving", "research_boundary", lambda b: b["examples"][0]["model_input"]["execution_scope"].update(serving_authorized=True))
    mutate("header_made_citable", "header_not_evidence", lambda b: b["examples"][0]["model_input"]["evidence_packet"]["items"][0]["context_header"].update(citable=True))
    passed = not preflight and baseline["status"] == "passed" and all(m["detected"] for m in mutations)
    result = {"status": "passed" if passed else "failed", "scope": "Source/lineage/coverage integrity of contract examples only; no general schema or runtime validation.",
              "checksums": {"examples": hashlib.sha256((PACK / "examples.json").read_bytes()).hexdigest(),
                            "evaluation_sidecar": hashlib.sha256((PACK / "evaluation-sidecar.json").read_bytes()).hexdigest(),
                            "mapping": hashlib.sha256(MAP_PATH.read_bytes()).hexdigest(),
                            "verifier": hashlib.sha256(Path(__file__).read_bytes()).hexdigest()},
              "preflight_errors": preflight, "baseline": baseline, "mutations": mutations,
              "limitations": ["Manually selected source excerpts are not chunker/retrieval outputs or independent gold.",
                              "Coverage is conservative source-span coverage, not semantic entailment or answerability detection.",
                              "No source admitted for production; no live rights enforcement or viewer is tested.",
                              "No tokenizer/model was selected and no context-fit or cost claim is made."]}
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
