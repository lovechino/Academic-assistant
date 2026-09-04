"""Source-positioned HTML structure experiment. Read only; emits JSON to stdout.

Not an HTML5 browser DOM, layout engine, code/formula parser, chunker or indexer.
No evaluation labels are read by this builder.
"""
from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import html
from html.parser import HTMLParser
import json
from pathlib import Path
import re
import sys


ROOT = Path(__file__).resolve().parents[3]
COURSE = ROOT / "data/raw/voer/cau-truc-du-lieu-va-giai-thuat"
PROFILE = "voer-source-html-structure-v0.1"
VOID = {"area", "base", "br", "col", "embed", "hr", "img", "input", "link", "meta", "param", "source", "track", "wbr"}
HEADINGS = {f"h{i}" for i in range(1, 7)}
TYPES = {"p": "paragraph", "ul": "list", "ol": "list", "li": "list_item", "table": "table",
         "td": "table_cell", "th": "table_cell", "figure": "figure", "figcaption": "caption",
         "pre": "preformatted", "code": "code", "math": "math"}
CODE_HINT = re.compile(r"\btypedef\b|\b(?:void|int|char|float|double|struct)\s+[A-Za-z_]|\breturn\b|#include|->|[{}]")
# Candidate matches are passed to html.unescape; exact legacy equivalence is asserted.
ENTITY = re.compile(r"&(?:\#[0-9]+;?|\#[xX][0-9a-fA-F]+;?|[^\t\n\f <&#;]{1,32};?)")


def digest(value: str | bytes) -> str:
    return hashlib.sha256(value.encode("utf-8") if isinstance(value, str) else value).hexdigest()


def normalize_legacy(value: str) -> str:
    return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", value))).strip()


def legacy_projection(source: str) -> dict:
    """Compatibility projection with conservative source envelopes, not parser text."""
    chars = []
    last = 0
    for match in re.finditer(r"<[^>]+>", source):
        chars.extend((c, i, i + 1) for i, c in enumerate(source[last:match.start()], last))
        chars.append((" ", match.start(), match.end()))
        last = match.end()
    chars.extend((c, i, i + 1) for i, c in enumerate(source[last:], last))
    stripped = "".join(c[0] for c in chars)
    expanded = []
    last = 0
    for match in ENTITY.finditer(stripped):
        expanded.extend(chars[last:match.start()])
        decoded = html.unescape(match.group())
        if decoded == match.group():
            expanded.extend(chars[match.start():match.end()])
        else:
            expanded.extend((c, chars[match.start()][1], chars[match.end() - 1][2]) for c in decoded)
        last = match.end()
    expanded.extend(chars[last:])
    collapsed = []
    whitespace = []
    for item in expanded:
        if item[0].isspace():
            whitespace.append(item)
            continue
        if whitespace and collapsed:
            collapsed.append((" ", whitespace[0][1], whitespace[-1][2]))
        whitespace = []
        collapsed.append(item)
    text = "".join(c[0] for c in collapsed)
    if text != normalize_legacy(source):
        raise ValueError("Legacy compatibility projection is not exact")
    runs = []
    for index, (character, start, end) in enumerate(collapsed):
        linear = end == start + 1 and source[start:end] == character
        if runs and linear and runs[-1][4] == "linear" and runs[-1][3] == start:
            runs[-1][1] = index + 1
            runs[-1][3] = end
        elif runs and not linear and runs[-1][4] == "envelope" and runs[-1][2:4] == [start, end]:
            runs[-1][1] = index + 1
        else:
            runs.append([index, index + 1, start, end, "linear" if linear else "envelope"])
    return {"profile": "voer-html-regex-space-v1", "purpose": "evaluation_alignment_only_not_generation_text",
            "text": text, "sha256": digest(text), "alignment_columns": ["text_start", "text_end", "raw_start", "raw_end", "mapping_kind"],
            "alignment_runs": runs}


class SourceTree(HTMLParser):
    def __init__(self, source: str, source_key: str):
        super().__init__(convert_charrefs=False)
        self.source = source
        self.key = source_key
        self.lines = [0] + [m.end() for m in re.finditer("\n", source)]
        self.nodes = []
        self.by_id = {}
        self.stack = []
        self.runs = []
        self.tokens = []
        self.issues = []

    def absolute_offset(self):
        line, column = self.getpos()
        return self.lines[line - 1] + column

    def node_id(self, tag, start):
        return "n-" + digest(f"{PROFILE}:{self.key}:{tag}:{start}")[:16]

    def token(self, start, end, kind):
        self.tokens.append({"span": [start, end], "kind": kind})

    def open_node(self, tag, attrs, self_closed=False):
        start = self.absolute_offset()
        end = start + len(self.get_starttag_text())
        closed = self_closed or tag in VOID
        node = {"id": self.node_id(tag, start), "tag": tag,
                "parent": self.stack[-1] if self.stack else None,
                "attributes": attrs, "open_span": [start, end],
                "close_span": None, "source_span": [start, end if closed else None],
                "closure": "self_closed" if self_closed else "void" if closed else "pending"}
        self.nodes.append(node)
        self.by_id[node["id"]] = node
        self.token(start, end, "start_tag")
        if not closed:
            self.stack.append(node["id"])

    def handle_starttag(self, tag, attrs):
        self.open_node(tag, attrs)

    def handle_startendtag(self, tag, attrs):
        self.open_node(tag, attrs, True)

    def handle_endtag(self, tag):
        start = self.absolute_offset()
        end = self.source.find(">", start) + 1
        self.token(start, end, "end_tag")
        positions = [i for i, node_id in enumerate(self.stack) if self.by_id[node_id]["tag"] == tag]
        if not positions:
            self.issues.append({"code": "unmatched_end_tag", "tag": tag, "raw_span": [start, end]})
            return
        position = positions[-1]
        for node_id in self.stack[position + 1:]:
            node = self.by_id[node_id]
            node.update(closure="inferred_outer_close")
            node["source_span"][1] = start
            self.issues.append({"code": "inferred_close", "node_id": node_id, "raw_offset": start})
        node = self.by_id[self.stack[position]]
        node.update(close_span=[start, end], closure="explicit")
        node["source_span"][1] = end
        del self.stack[position:]

    def add_text(self, start, end, text, kind):
        self.runs.append({"parent": self.stack[-1] if self.stack else None,
                          "raw_span": [start, end], "text": text, "kind": kind})
        self.token(start, end, kind)

    def handle_data(self, data):
        start = self.absolute_offset()
        if self.source[start:start + len(data)] != data:
            raise ValueError("HTMLParser changed a data callback unexpectedly")
        self.add_text(start, start + len(data), data, "text")

    def handle_entityref(self, name):
        start = self.absolute_offset()
        end = start + len(name) + 1
        end += int(self.source[end:end + 1] == ";")
        self.add_text(start, end, html.unescape(self.source[start:end]), "entity")

    def handle_charref(self, name):
        start = self.absolute_offset()
        end = start + len(name) + 2
        end += int(self.source[end:end + 1] == ";")
        self.add_text(start, end, html.unescape(self.source[start:end]), "entity")

    def handle_comment(self, data):
        start = self.absolute_offset()
        end = self.source.find("-->", start) + 3
        self.token(start, end, "comment")

    def handle_decl(self, decl):
        start = self.absolute_offset()
        self.token(start, self.source.find(">", start) + 1, "declaration")

    def handle_pi(self, data):
        start = self.absolute_offset()
        self.token(start, self.source.find(">", start) + 1, "processing_instruction")

    def finish(self):
        self.feed(self.source)
        self.close()
        for node_id in self.stack:
            node = self.by_id[node_id]
            node.update(closure="inferred_eof")
            node["source_span"][1] = len(self.source)
            self.issues.append({"code": "unclosed_at_eof", "node_id": node_id})
        return self

    def ancestors(self, node):
        result = []
        current = node["parent"]
        while current:
            result.append(self.by_id[current])
            current = self.by_id[current]["parent"]
        return list(reversed(result))

    def descendants(self, node):
        start, end = node["source_span"]
        return [n for n in self.nodes if start <= n["source_span"][0] < end and n["id"] != node["id"]]

    def text_of(self, node):
        start, end = node["source_span"]
        events = [(r["raw_span"][0], 1, r["text"]) for r in self.runs
                  if start <= r["raw_span"][0] and r["raw_span"][1] <= end]
        blocks = {"p", "li", "ul", "ol", "tr", "td", "th", "pre", "br"} | HEADINGS
        for child in self.descendants(node):
            if child["tag"] in blocks:
                events.append((child["open_span"][0], 0, "\n"))
                if child["tag"] != "br":
                    events.append((child["source_span"][1], 0, "\n"))
        return "".join(event[2] for event in sorted(events))


def is_section(node):
    return node["tag"] == "div" and "section" in dict(node["attributes"]).get("class", "").split()


def build(path: Path) -> dict:
    raw = path.read_bytes()
    data = json.loads(raw)["data"]
    source = data["text"]
    material_id = data["material_id"]
    tree = SourceTree(source, digest(raw)).finish()
    sections = []
    for node in tree.nodes:
        if not is_section(node):
            continue
        headings = [n for n in tree.nodes if n["parent"] == node["id"] and n["tag"] in HEADINGS]
        parents = [n["id"] for n in tree.ancestors(node) if is_section(n)]
        sections.append({"id": node["id"], "parent_section_id": parents[-1] if parents else None,
                         "heading_node_ids": [n["id"] for n in headings],
                         "title": " / ".join(re.sub(r"\s+", " ", tree.text_of(h)).strip() for h in headings),
                         "basis": "explicit_source_div_section", "semantic_review": "not_reviewed"})
    elements = []
    for order, node in enumerate(tree.nodes):
        kind = "heading" if node["tag"] in HEADINGS else TYPES.get(node["tag"])
        if kind is None:
            continue
        text = tree.text_of(node)
        inline_nodes = [n["id"] for n in tree.descendants(node) if n["tag"] in {"sub", "sup"}]
        flags = []
        if node["closure"].startswith("inferred"):
            flags.append("malformed_or_implicit_structure")
        if inline_nodes:
            flags.append("inline_subscript_superscript_requires_rich_representation")
        if kind == "paragraph" and CODE_HINT.search(text):
            flags.append("code_like_paragraph_grouping_not_resolved")
        if any(0xE000 <= ord(c) <= 0xF8FF for c in text):
            flags.append("private_use_character_requires_review")
        elements.append({"id": node["id"], "type": kind, "source_order_index": order,
                         "section_ids": [n["id"] for n in tree.ancestors(node) if is_section(n)],
                         "preview": re.sub(r"\s+", " ", text).strip()[:140],
                         "inline_script_node_ids": inline_nodes, "quality_flags": flags})
    tables = []
    for table in [n for n in tree.nodes if n["tag"] == "table"]:
        rows = [n for n in tree.descendants(table) if n["tag"] == "tr"
                and next((a["id"] for a in reversed(tree.ancestors(n)) if a["tag"] == "table"), None) == table["id"]]
        cells = []
        for row_index, row in enumerate(rows):
            row_cells = [n for n in tree.descendants(row) if n["tag"] in {"td", "th"}
                         and next((a["id"] for a in reversed(tree.ancestors(n)) if a["tag"] == "tr"), None) == row["id"]]
            for cell_index, cell in enumerate(row_cells):
                attrs = dict(cell["attributes"])
                cells.append({"node_id": cell["id"], "row_node_id": row["id"], "source_row_index": row_index,
                              "source_cell_index": cell_index, "rowspan_as_source": attrs.get("rowspan"),
                              "colspan_as_source": attrs.get("colspan"), "explicit_header": cell["tag"] == "th",
                              "text": tree.text_of(cell), "is_blank": not tree.text_of(cell).strip()})
        tables.append({"node_id": table["id"], "row_node_ids": [n["id"] for n in rows], "cells": cells,
                       "header_semantics": "explicit_th_only_other_headers_unreviewed",
                       "grid_expansion": "not_computed_source_row_cell_order_only",
                       "cell_text_basis": "decoded_descendant_text_with_synthetic_block_breaks_not_raw_html"})
    images = []
    for node in [n for n in tree.nodes if n["tag"] == "img"]:
        attrs = dict(node["attributes"])
        src = attrs.get("src", "")
        match = re.fullmatch(r"/post-file/([a-f0-9]{8})/([A-Za-z0-9._-]+)", src)
        asset = None
        if match:
            candidate = (COURSE / "assets" / match.group(1) / match.group(2)).resolve()
            if candidate.is_relative_to((COURSE / "assets").resolve()) and candidate.is_file():
                content = candidate.read_bytes()
                actual_type = "png" if content.startswith(b"\x89PNG\r\n\x1a\n") else "jpeg" if content.startswith(b"\xff\xd8\xff") else "unknown"
                asset = {"local_path": candidate.relative_to(ROOT).as_posix(), "sha256": digest(content),
                         "bytes": len(content), "detected_signature": actual_type,
                         "declared_extension": candidate.suffix.lower(), "decode_tested_this_run": False}
        figures = [a for a in tree.ancestors(node) if a["tag"] == "figure"]
        figure = figures[-1] if figures else None
        captions = [] if figure is None else [n["id"] for n in tree.descendants(figure) if n["tag"] == "figcaption"]
        near = []
        if figure is not None:
            siblings = [n for n in tree.nodes if n["parent"] == figure["parent"]]
            position = siblings.index(figure)
            near = [siblings[i]["id"] for i in (position - 1, position + 1)
                    if 0 <= i < len(siblings) and siblings[i]["tag"] == "p"]
        alt = attrs.get("alt", "") or ""
        images.append({"node_id": node["id"], "figure_node_id": figure["id"] if figure else None,
                       "src_as_source": src, "alt_as_source": alt,
                       "alt_is_filename": bool(re.fullmatch(r"[^/]+\.(?:png|jpe?g|gif|svg)", alt, re.I)),
                       "asset": asset, "availability": "local_file_present" if asset else "missing_or_unresolved",
                       "explicit_caption_node_ids": captions, "nearby_paragraph_candidates": near,
                       "candidate_relationships_verified": False, "visual_content_understood": False})
    projection = legacy_projection(source)
    covered = 0
    token_partition = True
    for token in tree.tokens:
        if token["span"][0] != covered or token["span"][1] < covered:
            token_partition = False
        covered = token["span"][1]
    token_partition &= covered == len(source)
    counts = Counter(n["tag"] for n in tree.nodes)
    flags = Counter(f for e in elements for f in e["quality_flags"])
    summary = {"nodes": len(tree.nodes), "text_runs": len(tree.runs), "structural_elements": len(elements),
               "sections": len(sections), "headings": sum(counts[tag] for tag in HEADINGS),
               "paragraphs": counts["p"], "lists": counts["ul"] + counts["ol"], "list_items": counts["li"],
               "tables": len(tables), "table_rows": sum(len(t["row_node_ids"]) for t in tables),
               "table_cells": sum(len(t["cells"]) for t in tables), "blank_cells": sum(c["is_blank"] for t in tables for c in t["cells"]),
               "explicit_th_cells": counts["th"], "image_references": len(images),
               "local_images": sum(i["asset"] is not None for i in images),
               "explicit_figcaptions": counts["figcaption"], "filename_alts": sum(i["alt_is_filename"] for i in images),
               "subscript_nodes": counts["sub"], "superscript_nodes": counts["sup"],
               "explicit_code_nodes": counts["code"] + counts["pre"], "parser_issues": len(tree.issues),
               "raw_token_partition_complete": token_partition, "quality_flags": dict(flags)}
    return {"representation_id": PROFILE, "corpus_snapshot": "voer-2026-09-04-r1",
            "source": {"document_id": "voer-module-" + material_id, "material_id": material_id,
                       "path": path.relative_to(ROOT).as_posix(), "file_sha256": digest(raw),
                       "source_version": data.get("version"), "modified": data.get("modified"),
                       "title": data.get("title"), "authors": [a.get("fullname") for a in data.get("author", [])],
                       "json_pointer": "/data/text", "html_sha256": digest(source), "html_codepoints": len(source)},
            "profile": {"implementation_sha256": digest(Path(__file__).read_bytes()), "python_version": sys.version.split()[0],
                        "tree_kind": "source_tag_tree_not_browser_dom", "reading_order": "source_order_not_visual_verified",
                        "coordinate_system": "unicode_codepoint_half_open_in_decoded_json_data_text",
                        "code_grouping": "not_implemented", "math_semantics": "not_interpreted", "chunking": "not_run"},
            "restrictions": {"usage": "local_research_reference", "serving_authorized": False,
                             "external_processing_authorized": False, "training_authorized": False},
            "nodes": tree.nodes, "text_runs": tree.runs, "source_tokens": tree.tokens,
            "sections": sections, "elements": elements, "tables": tables, "images": images,
            "legacy_reference_projection": projection, "parser_issues": tree.issues, "summary": summary}


def module_paths():
    return sorted((COURSE / "modules").glob("*.json"))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--module", help="Known material ID from the frozen course snapshot")
    parser.add_argument("--catalog", action="store_true")
    parser.add_argument("--offset", type=int)
    parser.add_argument("--limit", type=int, default=20000)
    args = parser.parse_args()
    paths = module_paths()
    if args.catalog:
        records = []
        for path in paths:
            result = build(path)
            serialized = json.dumps(result, ensure_ascii=False, separators=(",", ":"))
            records.append({"material_id": result["source"]["material_id"], "title": result["source"]["title"],
                            "summary": result["summary"], "serialization_characters": len(serialized),
                            "serialization_sha256": digest(serialized)})
        print(json.dumps(records, ensure_ascii=False, separators=(",", ":")))
        return
    matches = [p for p in paths if p.stem.endswith("-" + (args.module or ""))]
    if len(matches) != 1:
        parser.error("Select one known module or --catalog")
    result = build(matches[0])
    serialized = json.dumps(result, ensure_ascii=False, separators=(",", ":"))
    if args.offset is not None:
        if args.offset < 0 or args.limit <= 0:
            parser.error("Invalid serialization page")
        print(json.dumps({"offset": args.offset, "total": len(serialized), "sha256": digest(serialized),
                          "chunk": serialized[args.offset:args.offset + args.limit]}, ensure_ascii=False))
    else:
        print(serialized)


if __name__ == "__main__":
    main()
