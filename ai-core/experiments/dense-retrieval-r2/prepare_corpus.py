"""Build the local R2 retrieval corpus and evaluator qrels; never loads a model.

The builder reads the frozen source/structure snapshot and assistant-silver qrels.
It writes only the explicitly requested derived artifact under data/processed.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import statistics
import sys


ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
CONFIG = HERE / "config-v0.1.json"
R1_CHUNKER = ROOT / "ai-core/experiments/chunking-r1/run_boundary_comparison.py"
HTML_BUILDER = ROOT / "ai-core/experiments/html-structure/build_representation.py"
STRUCTURE_MANIFEST = ROOT / "data/processed/voer-dsa-structure-v0.1/manifest.json"
EVIDENCE_MAP = ROOT / "data/evaluation/silver/voer-dsa-evidence-map-v0.1/evidence-map.json"
TOKENIZER_DEFAULT = ROOT / "tmp/tokenizers/bge-m3-5617a9f61b028005a4858fdac845db406aefb181/tokenizer.json"
OUTPUT_DEFAULT = ROOT / "data/processed/voer-dsa-dense-r2-v0.1/corpus.json"
LEAF_TYPES = {"paragraph", "heading", "list_item", "table_cell", "code", "preformatted", "caption"}


def digest(value: str | bytes) -> str:
    return hashlib.sha256(value.encode("utf-8") if isinstance(value, str) else value).hexdigest()


def require(ok: bool, code: str) -> None:
    if not ok:
        raise ValueError(code)


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def containing_chunk_ids(span: list[int], chunks: list[dict]) -> list[str]:
    start, end = span
    return [c["chunk_id"] for c in chunks
            if c["eligible"] and c["projection_span"][0] <= start and end <= c["projection_span"][1]]


def raw_envelope(locator: dict, representation: dict) -> list[int]:
    start, end = locator["start"], locator["end"]
    raw_parts = []
    for a, b, raw_start, raw_end, kind in representation["legacy_reference_projection"]["alignment_runs"]:
        lo, hi = max(a, start), min(b, end)
        if lo >= hi:
            continue
        raw_parts.append([raw_start + lo - a, raw_start + hi - a] if kind == "linear" else [raw_start, raw_end])
    require(bool(raw_parts), "locator_has_no_raw_alignment:" + locator["id"])
    return [min(part[0] for part in raw_parts), max(part[1] for part in raw_parts)]


def locator_leaf_ids(locator: dict, representation: dict) -> tuple[list[str], list[int]]:
    projection = representation["legacy_reference_projection"]
    require(projection["text"][locator["start"]:locator["end"]] == locator["quote"],
            "locator_quote_mismatch:" + locator["id"])
    raw_start, raw_end = raw_envelope(locator, representation)
    nodes = {node["id"]: node for node in representation["nodes"]}
    elements = {element["id"]: element for element in representation["elements"]}
    selected = set()
    for run in representation["text_runs"]:
        if not run["text"].strip() or run["raw_span"][0] >= raw_end or run["raw_span"][1] <= raw_start:
            continue
        current = run["parent"]
        while current:
            if current in elements and elements[current]["type"] in LEAF_TYPES:
                selected.add(current)
                break
            current = nodes[current]["parent"]
    leaf_ids = sorted(selected, key=lambda node_id: nodes[node_id]["source_span"][0])
    require(bool(leaf_ids), "locator_has_no_leaf_elements:" + locator["id"])
    return leaf_ids, [raw_start, raw_end]


def build(tokenizer_path: Path) -> dict:
    from tokenizers import Tokenizer, __version__ as tokenizers_version

    config_bytes = CONFIG.read_bytes()
    config = json.loads(config_bytes)
    require(tokenizers_version == config["tokenizer"]["library_version"], "tokenizers_version_mismatch")
    require(digest(tokenizer_path.read_bytes()) == config["tokenizer"]["file_sha256"], "tokenizer_hash_mismatch")
    tokenizer = Tokenizer.from_file(str(tokenizer_path))
    tokenizer.no_truncation()
    tokenizer.no_padding()

    r1 = load_module("dense_r2_r1_chunker", R1_CHUNKER)
    html_builder = load_module("dense_r2_html_builder", HTML_BUILDER)
    manifest_bytes = STRUCTURE_MANIFEST.read_bytes()
    manifest = json.loads(manifest_bytes)
    manifest_ids = [row["document_id"] for row in manifest["documents"]]
    require(config["scope"]["document_ids"] == manifest_ids, "scope_not_exact_structure_manifest_order")
    manifest_by_id = {row["document_id"]: row for row in manifest["documents"]}

    records = r1.source_catalog(config)
    serializer = r1.load_serializer()
    documents = {}
    chunks = []
    excluded = []
    cap = config["chunking"]["hard_cap_tokens_including_special_tokens"]
    for record in records:
        doc = r1.projection_document(record, serializer)
        for atom in doc["atoms"]:
            atom["document_id"] = doc["document_id"]
        doc_chunks = r1.decorate_chunks(doc, r1.structure_chunks(doc, tokenizer, cap), config["chunking"]["variant"])
        for chunk in doc_chunks:
            start, end = chunk["projection_span"]
            embedding_text = html_builder.normalize_legacy(doc["text"][start:end])
            embedding_tokens = r1.token_count(tokenizer, embedding_text)
            embedding_eligible = bool(embedding_text.strip()) and embedding_tokens <= cap
            row = {
                "chunk_id": chunk["chunk_id"],
                "document_id": doc["document_id"],
                "projection_span": chunk["projection_span"],
                "boundary_tokens": chunk["tokens"],
                "embedding_tokens": embedding_tokens,
                "boundary_reason": chunk["boundary_reason"],
                "section_id": chunk.get("section_id"),
                "atom_node_ids": chunk.get("atom_node_ids", []),
                "source_projection_sha256": chunk["input_sha256"],
                "embedding_text_sha256": digest(embedding_text),
                "embedding_eligible": embedding_eligible,
                "embedding_text": embedding_text,
            }
            chunks.append(row)
            if not embedding_eligible:
                excluded.append({"chunk_id": row["chunk_id"], "document_id": row["document_id"],
                                 "reason": "empty_after_text_projection" if not embedding_text.strip() else "over_cap"})
        documents[doc["document_id"]] = {
            "projection": doc,
            "representation": record["rep"],
            "chunks": doc_chunks,
            "source_path": record["source_path"],
            "source_file_sha256": record["source_file_sha256"],
            "representation_path": record["representation_path"],
            "representation_file_sha256": record["representation_file_sha256"],
            "title_as_source": manifest_by_id[doc["document_id"]].get("title_as_source"),
        }

    evidence_bytes = EVIDENCE_MAP.read_bytes()
    evidence = json.loads(evidence_bytes)
    locator_rows = {}
    for locator in evidence["locators"]:
        doc = documents[locator["document_id"]]
        leaf_ids, envelope = locator_leaf_ids(locator, doc["representation"])
        required_chunks = []
        for leaf_id in leaf_ids:
            ids = containing_chunk_ids(doc["projection"]["node_ranges"][leaf_id], doc["chunks"])
            require(len(ids) == 1, "leaf_not_in_exactly_one_chunk:" + locator["id"] + ":" + leaf_id)
            required_chunks.extend(ids)
        required_chunks = list(dict.fromkeys(required_chunks))
        locator_rows[locator["id"]] = {
            "locator_id": locator["id"],
            "document_id": locator["document_id"],
            "legacy_span": [locator["start"], locator["end"]],
            "quote_sha256": locator["quote_sha256"],
            "raw_html_envelope": envelope,
            "leaf_element_ids": leaf_ids,
            "required_chunk_ids": required_chunks,
        }

    cases = []
    required_group_count = 0
    for case in evidence["cases"]:
        groups = []
        for group in case["evidence_groups"]:
            if not group["required"]:
                continue
            alternatives = []
            for alternative in group["alternatives"]:
                locator_ids = alternative["all_of_locators"]
                chunk_ids = list(dict.fromkeys(
                    chunk_id for locator_id in locator_ids for chunk_id in locator_rows[locator_id]["required_chunk_ids"]
                ))
                alternatives.append({"all_of_locator_ids": locator_ids, "all_of_chunk_ids": chunk_ids})
            require(bool(alternatives) and all(a["all_of_chunk_ids"] for a in alternatives),
                    "unattainable_group:" + group["id"])
            groups.append({"group_id": group["id"], "alternatives": alternatives})
            required_group_count += 1
        cases.append({"case_id": case["id"], "query": case["query"], "required_groups": groups})

    public_documents = []
    for document_id, doc in documents.items():
        public_documents.append({
            "document_id": document_id,
            "title_as_source": doc["title_as_source"],
            "source_path": doc["source_path"],
            "source_file_sha256": doc["source_file_sha256"],
            "representation_path": doc["representation_path"],
            "representation_file_sha256": doc["representation_file_sha256"],
            "projection_sha256": doc["projection"]["input_sha256"],
        })
    eligible_tokens = [row["embedding_tokens"] for row in chunks if row["embedding_eligible"]]
    return {
        "artifact_id": config["experiment_id"] + "-corpus-001",
        "status": "prepared_local_text_only",
        "config": config,
        "config_sha256": digest(config_bytes),
        "implementation_sha256": digest(Path(__file__).read_bytes()),
        "r1_chunker_sha256": digest(R1_CHUNKER.read_bytes()),
        "html_builder_sha256": digest(HTML_BUILDER.read_bytes()),
        "structure_manifest_sha256": digest(manifest_bytes),
        "evidence_map_sha256": digest(evidence_bytes),
        "tokenizer_file_sha256": digest(tokenizer_path.read_bytes()),
        "summary": {
            "documents": len(public_documents),
            "qrel_bearing_documents": len(evidence["documents"]),
            "distractor_documents": len(public_documents) - len(evidence["documents"]),
            "source_chunks": len(chunks),
            "dense_eligible_chunks": sum(row["embedding_eligible"] for row in chunks),
            "dense_excluded_chunks": len(excluded),
            "min_embedding_tokens": min(eligible_tokens),
            "median_embedding_tokens": statistics.median(eligible_tokens),
            "mean_embedding_tokens": round(statistics.mean(eligible_tokens), 2),
            "max_embedding_tokens": max(eligible_tokens),
            "evaluation_cases": len(cases),
            "required_evidence_groups": required_group_count,
            "locators": len(locator_rows),
        },
        "documents": public_documents,
        "chunks": chunks,
        "excluded_chunks": excluded,
        "locators": list(locator_rows.values()),
        "cases": cases,
        "limitations": [
            "qrels are assistant-silver and have not been adjudicated by a teacher",
            "HTML image-only chunks have no text embedding and are excluded from this dense baseline",
            "no generated contextual header, parent expansion, lexical retrieval, reranker or answer model is used",
        ],
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--tokenizer", type=Path, default=TOKENIZER_DEFAULT)
    parser.add_argument("--output", type=Path, default=OUTPUT_DEFAULT)
    parser.add_argument("--summary", action="store_true")
    args = parser.parse_args()
    result = build(args.tokenizer.resolve())
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result["summary"] if args.summary else {
        "output": args.output.relative_to(ROOT).as_posix(),
        "artifact_id": result["artifact_id"],
        "summary": result["summary"],
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
