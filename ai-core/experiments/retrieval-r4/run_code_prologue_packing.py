"""Evaluate a source-only backward code-prologue expansion without runtime labels."""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
import time
import unicodedata


ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
CONFIG = HERE / "code-prologue-config-v0.1.json"
R3_PACKER = ROOT / "ai-core/experiments/retrieval-r3/run_context_packing.py"
CORPUS_DEFAULT = ROOT / "data/processed/voer-dsa-dense-r2-v0.1/corpus.json"
RERANK_DEFAULT = ROOT / "data/processed/voer-dsa-retrieval-r3-v0.1/reranker-results.json"
ENRICHMENT_DEFAULT = ROOT / "data/processed/voer-dsa-enrichment-v0.1/enrichment.json"
R1_RUN_DEFAULT = ROOT / "data/processed/voer-dsa-chunking-r1-v0.1/run.json"
TOKENIZER_DEFAULT = ROOT / "tmp/tokenizers/bge-m3-5617a9f61b028005a4858fdac845db406aefb181/tokenizer.json"
OUTPUT_DEFAULT = ROOT / "data/processed/voer-dsa-retrieval-r4-v0.1/code-prologue-results.json"


def digest(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def require(ok: bool, code: str) -> None:
    if not ok:
        raise ValueError(code)


def load_r3_packer():
    spec = importlib.util.spec_from_file_location("retrieval_r4_r3_packer", R3_PACKER)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def normalized(text: str) -> str:
    return unicodedata.normalize("NFKC", text).casefold()


def contains_marker(text: str, markers: list[str]) -> bool:
    value = normalized(text)
    return any(normalized(marker) in value for marker in markers)


def expansion_ids(anchor: dict, previous: dict, by_id: dict, config: dict) -> list[tuple[str, str]]:
    if not contains_marker(anchor["embedding_text"], config["code_markers"]):
        return []
    result = []
    cursor = anchor["chunk_id"]
    for distance in range(1, config["policy"]["maximum_previous_chunks"] + 1):
        prior_id = previous.get(cursor)
        if prior_id is None:
            break
        prior = by_id[prior_id]
        result.append((prior_id, "code_previous_" + str(distance)))
        cursor = prior_id
        if contains_marker(prior["embedding_text"], config["prologue_markers"]):
            break
    return result


def pack(r3, ranking: list[dict], budget: int, tokenizer, separator: str,
         by_id: dict, previous: dict, config: dict) -> dict:
    retained = []
    retained_ids = set()
    trace = []

    def attempt(chunk_id: str, reason: str, anchor_rank: int) -> None:
        if chunk_id in retained_ids:
            trace.append({"chunk_id": chunk_id, "reason": reason, "anchor_rank": anchor_rank,
                          "decision": "deduplicated"})
            return
        chunk = by_id[chunk_id]
        if not chunk["embedding_eligible"]:
            trace.append({"chunk_id": chunk_id, "reason": reason, "anchor_rank": anchor_rank,
                          "decision": "unsupported_empty_text"})
            return
        proposed = retained + [chunk]
        proposed_tokens = r3.token_count(tokenizer, [row["embedding_text"] for row in proposed], separator)
        if proposed_tokens <= budget:
            retained.append(chunk)
            retained_ids.add(chunk_id)
            trace.append({"chunk_id": chunk_id, "reason": reason, "anchor_rank": anchor_rank,
                          "decision": "retained", "packet_tokens_after": proposed_tokens})
        else:
            trace.append({"chunk_id": chunk_id, "reason": reason, "anchor_rank": anchor_rank,
                          "decision": "skipped_budget", "would_be_tokens": proposed_tokens})

    for anchor in ranking:
        attempt(anchor["chunk_id"], "retrieved_anchor", anchor["rank"])
        for chunk_id, reason in expansion_ids(by_id[anchor["chunk_id"]], previous, by_id, config):
            attempt(chunk_id, reason, anchor["rank"])
    return {
        "chunk_ids": [row["chunk_id"] for row in retained],
        "tokens": r3.token_count(tokenizer, [row["embedding_text"] for row in retained], separator),
        "chunks": len(retained),
        "trace": trace,
    }


def dependency_diagnostics(enrichment: dict, r1_run: dict, chunks: list[dict],
                           previous: dict, config: dict) -> dict:
    structure = r1_run["variants"]["structure-512-o0"]["chunks_by_document"]
    docs = r1_run["input_documents"]
    refs = enrichment["refs"]
    groups_by_id = {group["id"]: group for group in enrichment["groups"]}
    group_chunks = {}
    for group in enrichment["groups"]:
        chunk_ids = []
        for ref_id in group["member_refs"]:
            ref = refs[ref_id]
            span = docs[ref["document_id"]]["node_ranges"][ref["node_id"]]
            matches = [row["chunk_id"] for row in structure[ref["document_id"]]
                       if row["eligible"] and max(row["projection_span"][0], span[0]) <
                       min(row["projection_span"][1], span[1])]
            require(bool(matches), "dependency_member_not_touching_chunk:" + ref_id)
            chunk_ids.extend(matches)
        group_chunks[group["id"]] = list(dict.fromkeys(chunk_ids))

    by_id = {chunk["chunk_id"]: chunk for chunk in chunks}
    rows = []
    for edge in enrichment["dependencies"]:
        anchors = group_chunks[edge["from_group"]]
        targets = set(group_chunks[edge["to_group"]])
        anchor_group = groups_by_id[edge["from_group"]]
        visual_unsupported = (
            "image" in anchor_group["type"]
            or anchor_group["review"]["status"] == "assistant_visual_checked"
            or any(not by_id[chunk_id]["embedding_eligible"] for chunk_id in set(anchors) | targets)
        )
        available = set(anchors)
        expansion_trace = []
        for anchor_id in anchors:
            if not by_id[anchor_id]["embedding_eligible"]:
                continue
            added = expansion_ids(by_id[anchor_id], previous, by_id, config)
            available.update(chunk_id for chunk_id, _ in added)
            expansion_trace.append({"anchor_chunk_id": anchor_id, "added": [
                {"chunk_id": chunk_id, "reason": reason} for chunk_id, reason in added
            ]})
        rows.append({
            "dependency_id": edge["id"],
            "status": edge["status"],
            "type": edge["type"],
            "anchor_chunk_ids": anchors,
            "target_chunk_ids": sorted(targets),
            "visual_text_path_unsupported": visual_unsupported,
            "policy_covers_target": targets.issubset(available) and not visual_unsupported,
            "runtime_expansion_trace": expansion_trace,
        })
    eligible = [row for row in rows if not row["visual_text_path_unsupported"]]
    return {
        "dependencies": rows,
        "summary": {
            "covered": sum(row["policy_covers_target"] for row in eligible),
            "eligible": len(eligible),
            "visual_unsupported": len(rows) - len(eligible),
        },
    }


def build(corpus_path: Path, rerank_path: Path, enrichment_path: Path, r1_path: Path,
          tokenizer_path: Path, output_path: Path) -> dict:
    from tokenizers import Tokenizer, __version__ as tokenizers_version

    started = time.perf_counter()
    config_bytes = CONFIG.read_bytes()
    config = json.loads(config_bytes)
    corpus_bytes = corpus_path.read_bytes()
    corpus = json.loads(corpus_bytes)
    rerank_bytes = rerank_path.read_bytes()
    rerank = json.loads(rerank_bytes)
    enrichment_bytes = enrichment_path.read_bytes()
    enrichment = json.loads(enrichment_bytes)
    r1_bytes = r1_path.read_bytes()
    r1_run = json.loads(r1_bytes)
    tokenizer_bytes = tokenizer_path.read_bytes()
    require(tokenizers_version == config["tokenizer"]["library_version"], "tokenizers_version_mismatch")
    require(digest(tokenizer_bytes) == config["tokenizer"]["file_sha256"], "tokenizer_hash_mismatch")
    require(rerank["inputs"]["corpus_sha256"] == digest(corpus_bytes), "reranker_corpus_hash_mismatch")
    require(enrichment["runtime_ready"] is False, "unexpected_runtime_ready_dependency_labels")
    require(all(edge["automatically_follow"] is False for edge in enrichment["dependencies"]),
            "dependency_labels_must_not_drive_runtime")

    r3 = load_r3_packer()
    tokenizer = Tokenizer.from_file(str(tokenizer_path))
    tokenizer.no_truncation()
    tokenizer.no_padding()
    chunks = corpus["chunks"]
    by_id, previous, _, _ = r3.indexes(chunks)
    stored_rankings = rerank["stages"][config["ranking"]["stage"]]["rankings"]
    rankings = {case_id: rows[:config["ranking"]["candidate_limit"]]
                for case_id, rows in stored_rankings.items()}
    evaluator = r3.load_r2_runner()
    stages = {}
    for budget in config["packet"]["budgets_tokens_including_special_tokens"]:
        packets = {
            case["case_id"]: pack(
                r3,
                rankings[case["case_id"]],
                budget,
                tokenizer,
                config["packet"]["separator"],
                by_id,
                previous,
                config,
            )
            for case in corpus["cases"]
        }
        stages[config["policy"]["id"] + "-b" + str(budget)] = r3.packet_metrics(
            evaluator, corpus["cases"], packets
        )
    dependencies = dependency_diagnostics(enrichment, r1_run, chunks, previous, config)
    triggered_chunks = [
        chunk["chunk_id"] for chunk in chunks
        if chunk["embedding_eligible"] and contains_marker(chunk["embedding_text"], config["code_markers"])
    ]
    result = {
        "run_id": config["experiment_id"] + "-run-001",
        "status": "completed_source_only_code_prologue_diagnostic",
        "config": config,
        "config_sha256": digest(config_bytes),
        "implementation_sha256": digest(Path(__file__).read_bytes()),
        "inputs": {
            "corpus_sha256": digest(corpus_bytes),
            "reranker_results_sha256": digest(rerank_bytes),
            "enrichment_sha256": digest(enrichment_bytes),
            "r1_run_sha256": digest(r1_bytes),
            "tokenizer_sha256": digest(tokenizer_bytes),
        },
        "runtime": {"seconds": round(time.perf_counter() - started, 3),
                    "source_chunks_matching_code_marker": len(triggered_chunks)},
        "triggered_chunk_ids": triggered_chunks,
        "stages": stages,
        "dependency_diagnostics": dependencies,
        "limitations": [
            "code/prologue markers are fixed source-only string heuristics and may over-trigger or miss other code styles",
            "dependency annotations and qrels are post-hoc evaluator inputs only",
            "image-only dependencies remain unsupported and are excluded from text-path coverage",
            "the BGE-M3 tokenizer is a provisional accounting tokenizer; no generation model is selected",
            "no generation, citation validation or hallucination evaluation is included",
        ],
    }
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--corpus", type=Path, default=CORPUS_DEFAULT)
    parser.add_argument("--reranker", type=Path, default=RERANK_DEFAULT)
    parser.add_argument("--enrichment", type=Path, default=ENRICHMENT_DEFAULT)
    parser.add_argument("--r1-run", type=Path, default=R1_RUN_DEFAULT)
    parser.add_argument("--tokenizer", type=Path, default=TOKENIZER_DEFAULT)
    parser.add_argument("--output", type=Path, default=OUTPUT_DEFAULT)
    args = parser.parse_args()
    result = build(
        args.corpus.resolve(), args.reranker.resolve(), args.enrichment.resolve(),
        args.r1_run.resolve(), args.tokenizer.resolve(), args.output.resolve()
    )
    print(json.dumps({
        "output": args.output.resolve().relative_to(ROOT).as_posix(),
        "runtime": result["runtime"],
        "metrics": {stage: value["summary"] for stage, value in result["stages"].items()},
        "dependency_diagnostics": result["dependency_diagnostics"]["summary"],
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
