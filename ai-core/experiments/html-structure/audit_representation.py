"""Read-only checks and evaluator-side alignment for the HTML structure snapshot."""
from __future__ import annotations

from collections import Counter
from copy import deepcopy
import html
import json
from pathlib import Path
import re
import sys

sys.dont_write_bytecode = True
import build_representation as builder

ROOT = builder.ROOT
OUTPUT = ROOT / "data/processed/voer-dsa-structure-v0.1"
MAPPING = ROOT / "data/evaluation/silver/voer-dsa-evidence-map-v0.1/evidence-map.json"


def audit_document(doc: dict) -> dict:
    checks = 0
    errors = []
    def check(ok, code, label):
        nonlocal checks
        checks += 1
        if not ok:
            errors.append({"code": code, "label": label})
    raw_bytes = (ROOT / doc["source"]["path"]).read_bytes()
    raw_data = json.loads(raw_bytes)["data"]
    source = raw_data["text"]
    check(builder.digest(raw_bytes) == doc["source"]["file_sha256"] and builder.digest(source) == doc["source"]["html_sha256"],
          "source_identity", doc["source"]["document_id"])
    check(doc["source"]["source_version"] == raw_data["version"] and doc["source"]["title"] == raw_data["title"],
          "source_identity", "source metadata")
    check(not doc["restrictions"]["serving_authorized"] and not doc["restrictions"]["external_processing_authorized"]
          and not doc["restrictions"]["training_authorized"], "research_boundary", "restrictions")
    nodes = {n["id"]: n for n in doc["nodes"]}
    elements = {e["id"]: e for e in doc["elements"]}
    check(len(nodes) == len(doc["nodes"]), "duplicate_ids", "nodes")
    for node in nodes.values():
        start, end = node["source_span"]
        a, b = node["open_span"]
        check(0 <= start == a < b <= end <= len(source), "node_bounds", node["id"])
        match = re.match(r"<\s*([^\s/>]+)", source[a:b])
        check(match is not None and match.group(1).lower() == node["tag"], "tag_identity", node["id"])
        if node["close_span"] is not None:
            ca, cb = node["close_span"]
            check(b <= ca < cb == end and re.fullmatch(r"</\s*" + re.escape(node["tag"]) + r"\s*>", source[ca:cb], re.I) is not None,
                  "closing_tag_identity", node["id"])
        if node["parent"]:
            parent = nodes.get(node["parent"])
            check(parent is not None and parent["source_span"][0] <= start and end <= parent["source_span"][1],
                  "parent_lineage", node["id"])
    cursor = 0
    for token in doc["source_tokens"]:
        a, b = token["span"]
        check(a == cursor and b >= a, "raw_partition", str(a))
        cursor = b
    check(cursor == len(source), "raw_partition", "end of source")
    text_tokens = Counter((tuple(t["span"]), t["kind"]) for t in doc["source_tokens"] if t["kind"] in {"text", "entity"})
    text_runs = Counter((tuple(t["raw_span"]), t["kind"]) for t in doc["text_runs"])
    check(text_tokens == text_runs, "text_event_loss", "source text events")
    for run in doc["text_runs"]:
        a, b = run["raw_span"]
        expected = html.unescape(source[a:b]) if run["kind"] == "entity" else source[a:b]
        check(run["text"] == expected, "text_integrity", str(a))
        check(run["parent"] is None or run["parent"] in nodes, "parent_lineage", str(a))
    for element in elements.values():
        node = nodes.get(element["id"])
        expected = None if node is None else "heading" if node["tag"] in builder.HEADINGS else builder.TYPES.get(node["tag"])
        check(expected == element["type"], "element_type", element["id"])
        for inline_id in element["inline_script_node_ids"]:
            inline = nodes.get(inline_id)
            check(inline is not None and inline["tag"] in {"sub", "sup"}
                  and node["source_span"][0] <= inline["source_span"][0] < inline["source_span"][1] <= node["source_span"][1],
                  "inline_semantics", element["id"])
    all_cells = {n["id"] for n in nodes.values() if n["tag"] in {"td", "th"}}
    recorded_cells = [c["node_id"] for table in doc["tables"] for c in table["cells"]]
    check(set(recorded_cells) == all_cells and len(recorded_cells) == len(all_cells), "table_cell_loss", "all cells, including blank")
    for table in doc["tables"]:
        for cell in table["cells"]:
            node = nodes[cell["node_id"]]
            check(cell["explicit_header"] == (node["tag"] == "th"), "table_header_invention", cell["node_id"])
            check(cell["is_blank"] == (not cell["text"].strip()), "blank_cell", cell["node_id"])
            attrs = dict(node["attributes"])
            check(cell["rowspan_as_source"] == attrs.get("rowspan") and cell["colspan_as_source"] == attrs.get("colspan"),
                  "table_span_metadata", cell["node_id"])
    for image in doc["images"]:
        attrs = dict(nodes[image["node_id"]]["attributes"])
        check(image["src_as_source"] == attrs.get("src") and image["alt_as_source"] == (attrs.get("alt") or ""),
              "image_source", image["node_id"])
        for caption in image["explicit_caption_node_ids"]:
            check(caption in nodes and nodes[caption]["tag"] == "figcaption", "caption_invention", image["node_id"])
        check(not image["candidate_relationships_verified"] and not image["visual_content_understood"], "visual_overclaim", image["node_id"])
        asset = image["asset"]
        if asset:
            path = (ROOT / asset["local_path"]).resolve()
            allowed = path.is_relative_to((builder.COURSE / "assets").resolve())
            check(allowed and path.is_file() and builder.digest(path.read_bytes()) == asset["sha256"], "asset_identity", image["node_id"])
    projection = doc["legacy_reference_projection"]
    text = projection["text"]
    check(text == builder.normalize_legacy(source) and builder.digest(text) == projection["sha256"], "legacy_equivalence", "full text")
    cursor = 0
    for a, b, ra, rb, kind in projection["alignment_runs"]:
        check(a == cursor and a < b <= len(text) and 0 <= ra < rb <= len(source), "alignment_gap", str(a))
        if kind == "linear":
            check(text[a:b] == source[ra:rb] and b-a == rb-ra, "alignment_content", str(a))
        else:
            check((text[a:b] == " " and builder.normalize_legacy(source[ra:rb]) == "")
                  or text[a:b] == html.unescape(source[ra:rb]), "alignment_content", str(a))
        cursor = b
    check(cursor == len(text), "alignment_gap", "projection end")
    return {"document_id": doc["source"]["document_id"], "checks": checks, "errors": errors}


def align_locator(locator, doc):
    projection = doc["legacy_reference_projection"]
    start, end = locator["start"], locator["end"]
    raw_parts = []
    for a, b, ra, rb, kind in projection["alignment_runs"]:
        lo, hi = max(a, start), min(b, end)
        if lo >= hi:
            continue
        raw_parts.append([ra + lo-a, ra + hi-a] if kind == "linear" else [ra, rb])
    ra, rb = min(p[0] for p in raw_parts), max(p[1] for p in raw_parts)
    source = json.loads((ROOT / doc["source"]["path"]).read_text(encoding="utf-8"))["data"]["text"]
    nodes = {n["id"]: n for n in doc["nodes"]}
    elements = {e["id"]: e for e in doc["elements"]}
    selected = set()
    leaf_types = {"paragraph", "heading", "list_item", "table_cell", "code", "preformatted", "caption"}
    for run in doc["text_runs"]:
        if not run["text"].strip() or run["raw_span"][0] >= rb or run["raw_span"][1] <= ra:
            continue
        current = run["parent"]
        while current:
            if current in elements and elements[current]["type"] in leaf_types:
                selected.add(current)
                break
            current = nodes[current]["parent"]
    leaf_ids = sorted(selected, key=lambda n: nodes[n]["source_span"][0])
    return {"locator_id": locator["id"], "document_id": locator["document_id"],
            "legacy_span": [start, end], "raw_html_envelope": [ra, rb],
            "legacy_quote_matches": projection["text"][start:end] == locator["quote"],
            "raw_envelope_normalizes_to_quote": builder.normalize_legacy(source[ra:rb]) == locator["quote"],
            "leaf_element_ids": leaf_ids,
            "leaf_element_types": [elements[n]["type"] for n in leaf_ids],
            "section_ids": list(dict.fromkeys(s for n in leaf_ids for s in elements[n]["section_ids"])),
            "semantic_support_review": "existing_silver_only_not_adjudicated"}


def probes():
    results = []
    def check(name, ok):
        results.append({"id": name, "passed": bool(ok)})
    source = '<h1>T</h1><p>a<sub>i</sub> + x<sup>2</sup> &amp; &#8804; 3<br>line</p>'
    tree = builder.SourceTree(source, "probe-inline").finish()
    check("inline_roles_preserved", [n["tag"] for n in tree.nodes if n["tag"] in {"sub", "sup"}] == ["sub", "sup"])
    paragraph = next(n for n in tree.nodes if n["tag"] == "p")
    check("br_not_glued_to_next_word", "3\nline" in tree.text_of(paragraph))
    check("entities_decoded_with_raw_locations", any(r["text"] == "≤" and source[slice(*r["raw_span"])] == "&#8804;" for r in tree.runs))
    projection = builder.legacy_projection(source)
    check("legacy_projection_exact", projection["text"] == builder.normalize_legacy(source))
    nested = builder.SourceTree('<ul><li>A<ul><li>B</li></ul></li><li>C</li></ul>', "probe-list").finish()
    lis = [n for n in nested.nodes if n["tag"] == "li"]
    check("nested_list_parent_preserved", len(lis) == 3 and lis[0]["parent"] == lis[2]["parent"] != lis[1]["parent"])
    table = builder.SourceTree('<table><tr><th rowspan="2">H</th><td></td></tr><tr><td colspan="2">X</td></tr></table>', "probe-table").finish()
    check("blank_table_cell_kept", any(n["tag"] == "td" and table.text_of(n) == "" for n in table.nodes))
    check("table_spans_not_discarded", any(dict(n["attributes"]).get("rowspan") == "2" for n in table.nodes) and any(dict(n["attributes"]).get("colspan") == "2" for n in table.nodes))
    figure = builder.SourceTree('<figure><img src="/missing.png" alt="missing.png"></figure><p>Nearby text</p>', "probe-image").finish()
    check("no_caption_invented_by_parser", not any(n["tag"] == "figcaption" for n in figure.nodes))
    malformed = builder.SourceTree('<div><p>unfinished</div>', "probe-malformed").finish()
    check("implicit_close_flagged", bool(malformed.issues))
    inert = builder.SourceTree('<!--comment--><script>alert("example")</script><p>body</p>', "probe-inert").finish()
    check("script_is_inert_source_data", any(n["tag"] == "script" for n in inert.nodes) and any(t["kind"] == "comment" for t in inert.tokens))
    return results


def main():
    paths = sorted((OUTPUT / "documents").glob("*.json"))
    docs = [json.loads(p.read_text(encoding="utf-8")) for p in paths]
    audits = [audit_document(doc) for doc in docs]
    mapping_bytes = MAPPING.read_bytes()
    mapping = json.loads(mapping_bytes)
    by_id = {d["source"]["document_id"]: d for d in docs}
    alignment = [align_locator(l, by_id[l["document_id"]]) for l in mapping["locators"]]
    rebuild = []
    for doc in docs:
        fresh = builder.build(ROOT / doc["source"]["path"])
        rebuild.append({"document_id": doc["source"]["document_id"], "identical": json.loads(json.dumps(fresh)) == doc})
    synthetic = probes()
    mutations = []
    stack = next(d for d in docs if d["source"]["material_id"] == "a208ce0f")
    array_doc = next(d for d in docs if d["source"]["material_id"] == "9461a675")
    def mutate(name, expected, original, change):
        changed = deepcopy(original)
        change(changed)
        codes = sorted({e["code"] for e in audit_document(changed)["errors"]})
        mutations.append({"id": name, "expected_error": expected, "observed_errors": codes, "detected": expected in codes})
    mutate("wrong_source_hash", "source_identity", stack, lambda d: d["source"].update(file_sha256="0"*64))
    mutate("drop_text_event", "text_event_loss", stack, lambda d: d["text_runs"].pop(0))
    mutate("change_inline_subscript_tag", "tag_identity", array_doc, lambda d: next(n for n in d["nodes"] if n["tag"] == "sub").update(tag="sup"))
    mutate("delete_blank_cell", "table_cell_loss", array_doc, lambda d: d["tables"][0]["cells"].remove(next(c for c in d["tables"][0]["cells"] if c["is_blank"])))
    mutate("invent_table_header", "table_header_invention", stack, lambda d: d["tables"][0]["cells"][0].update(explicit_header=True))
    mutate("invent_image_caption", "caption_invention", stack, lambda d: d["images"][0]["explicit_caption_node_ids"].append(next(n["id"] for n in d["nodes"] if n["tag"] == "p")))
    mutate("drop_alignment_run", "alignment_gap", stack, lambda d: d["legacy_reference_projection"]["alignment_runs"].pop(1))
    mutate("claim_visual_understanding", "visual_overclaim", stack, lambda d: d["images"][0].update(visual_content_understood=True))
    source_ids = {p.stem.split("-", 1)[1] for p in builder.module_paths()}
    checks = {"all_16_modules": len(docs) == 16 and {d["source"]["material_id"] for d in docs} == source_ids,
              "document_integrity": all(not a["errors"] for a in audits),
              "deterministic_rebuild": all(r["identical"] for r in rebuild),
              "all_22_locators_aligned": len(alignment) == 22 and all(a["legacy_quote_matches"] and a["raw_envelope_normalizes_to_quote"] and a["leaf_element_ids"] for a in alignment),
              "synthetic_probes": all(p["passed"] for p in synthetic), "mutations_detected": all(m["detected"] for m in mutations)}
    result = {"audit_id": "voer-dsa-structure-audit-v0.1", "status": "passed" if all(checks.values()) else "failed",
              "scope": "Source preservation and structural traceability only; not semantic/layout accuracy, gold labels or retrieval benchmark.",
              "builder_sha256": builder.digest(Path(builder.__file__).read_bytes()),
              "auditor_sha256": builder.digest(Path(__file__).read_bytes()), "mapping_sha256": builder.digest(mapping_bytes),
              "checks": checks, "document_check_count": sum(a["checks"] for a in audits), "document_audits": audits,
              "rebuild": rebuild, "evaluator_only_alignment": alignment, "synthetic_probes": synthetic, "mutations": mutations}
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if all(checks.values()) else 1


if __name__ == "__main__":
    raise SystemExit(main())
