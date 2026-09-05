"""Pack a frozen reranker ranking with source-only expansion policies."""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import re
import sys
import time


ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
CONFIG = HERE / "packing-config-v0.1.json"
R2_RUNNER = ROOT / "ai-core/experiments/dense-retrieval-r2/run_dense_retrieval.py"
CORPUS_DEFAULT = ROOT / "data/processed/voer-dsa-dense-r2-v0.1/corpus.json"
RERANK_DEFAULT = ROOT / "data/processed/voer-dsa-retrieval-r3-v0.1/reranker-results.json"
ENRICHMENT_DEFAULT = ROOT / "data/processed/voer-dsa-enrichment-v0.1/enrichment.json"
R1_RUN_DEFAULT = ROOT / "data/processed/voer-dsa-chunking-r1-v0.1/run.json"
TOKENIZER_DEFAULT = ROOT / "tmp/tokenizers/bge-m3-5617a9f61b028005a4858fdac845db406aefb181/tokenizer.json"
OUTPUT_DEFAULT = ROOT / "data/processed/voer-dsa-retrieval-r3-v0.1/packing-results.json"
COMPARE = re.compile(r"\b(so sánh|khác nhau|giống nhau|điểm khác)\b", re.IGNORECASE)
EXPLAIN = re.compile(r"\b(tại sao|vì sao|như thế nào|giải thích)\b", re.IGNORECASE)
BACK = re.compile(r"\b(trong đó|điều này|như trên|ở trên|nêu trên|hình trên|bảng trên|công thức trên)\b", re.IGNORECASE)
FORWARD = re.compile(r"\b(sau đây|như sau|ở dưới|hình sau|bảng sau|công thức sau)\b", re.IGNORECASE)
VISUAL_REF = re.compile(r"\b(hình|bảng|công thức)\b", re.IGNORECASE)


def digest(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def require(ok: bool, code: str) -> None:
    if not ok:
        raise ValueError(code)


def load_r2_runner():
    spec = importlib.util.spec_from_file_location("retrieval_r3_r2_runner_for_packing", R2_RUNNER)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def token_count(tokenizer, texts: list[str], separator: str) -> int:
    if not texts:
        return 0
    return len(tokenizer.encode(separator.join(texts), add_special_tokens=True).ids)


def indexes(chunks: list[dict]) -> tuple[dict, dict, dict, dict]:
    by_id = {chunk["chunk_id"]: chunk for chunk in chunks}
    by_document = {}
    for chunk in chunks:
        by_document.setdefault(chunk["document_id"], []).append(chunk)
    previous, following, section_lead = {}, {}, {}
    for rows in by_document.values():
        rows.sort(key=lambda row: row["projection_span"])
        for index, row in enumerate(rows):
            key = (row["document_id"], row.get("section_id"))
            if row["embedding_eligible"]:
                section_lead.setdefault(key, row["chunk_id"])
            if index and rows[index - 1].get("section_id") == row.get("section_id"):
                previous[row["chunk_id"]] = rows[index - 1]["chunk_id"]
            if index + 1 < len(rows) and rows[index + 1].get("section_id") == row.get("section_id"):
                following[row["chunk_id"]] = rows[index + 1]["chunk_id"]
    return by_id, previous, following, section_lead


def expansion_ids(policy: str, query: str, anchor: dict, previous: dict, following: dict,
                  section_lead: dict) -> list[tuple[str, str]]:
    if policy == "x0-child-only":
        return []
    lead = section_lead.get((anchor["document_id"], anchor.get("section_id")))
    if policy == "x1-section-lead":
        return [(lead, "section_lead")] if lead and lead != anchor["chunk_id"] else []
    require(policy == "x2-cue-neighbors", "unknown_policy")
    rows = []
    query_requests_context = bool(COMPARE.search(query) or EXPLAIN.search(query))
    if query_requests_context and lead and lead != anchor["chunk_id"]:
        rows.append((lead, "query_cue_section_lead"))
    text = anchor["embedding_text"]
    if BACK.search(text) or VISUAL_REF.search(text):
        if anchor["chunk_id"] in previous:
            rows.append((previous[anchor["chunk_id"]], "source_back_reference"))
    if FORWARD.search(text):
        if anchor["chunk_id"] in following:
            rows.append((following[anchor["chunk_id"]], "source_forward_reference"))
    unique = []
    seen = set()
    for row in rows:
        if row[0] not in seen and row[0] != anchor["chunk_id"]:
            seen.add(row[0])
            unique.append(row)
    return unique


def pack(ranking: list[dict], query: str, policy: str, budget: int, tokenizer, separator: str,
         by_id: dict, previous: dict, following: dict, section_lead: dict) -> dict:
    retained = []
    retained_ids = set()
    trace = []

    def attempt(chunk_id: str, reason: str, anchor_rank: int) -> None:
        if chunk_id in retained_ids:
            trace.append({"chunk_id": chunk_id, "reason": reason, "anchor_rank": anchor_rank, "decision": "deduplicated"})
            return
        chunk = by_id[chunk_id]
        if not chunk["embedding_eligible"]:
            trace.append({"chunk_id": chunk_id, "reason": reason, "anchor_rank": anchor_rank,
                          "decision": "unsupported_empty_text"})
            return
        proposed = retained + [chunk]
        proposed_tokens = token_count(tokenizer, [row["embedding_text"] for row in proposed], separator)
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
        for chunk_id, reason in expansion_ids(policy, query, by_id[anchor["chunk_id"]], previous, following, section_lead):
            attempt(chunk_id, reason, anchor["rank"])
    return {
        "chunk_ids": [row["chunk_id"] for row in retained],
        "tokens": token_count(tokenizer, [row["embedding_text"] for row in retained], separator),
        "chunks": len(retained),
        "trace": trace,
    }


def packet_metrics(runner, cases: list[dict], packets: dict) -> dict:
    total_groups = sum(len(case["required_groups"]) for case in cases)
    groups_hit = 0
    all_cases = 0
    macro_chunk_recall = 0.0
    case_rows = []
    for case in cases:
        ids = set(packets[case["case_id"]]["chunk_ids"])
        hits = [runner.group_hit(group, ids) for group in case["required_groups"]]
        relevant = {chunk_id for group in case["required_groups"] for alternative in group["alternatives"]
                    for chunk_id in alternative["all_of_chunk_ids"]}
        groups_hit += sum(hits)
        all_cases += bool(hits) and all(hits)
        recall = len(relevant & ids) / len(relevant) if relevant else 0.0
        macro_chunk_recall += recall
        case_rows.append({"case_id": case["case_id"], "groups_hit": sum(hits), "groups_total": len(hits),
                          "all_evidence_success": bool(hits) and all(hits), "qrel_chunk_recall": recall,
                          "qrel_chunks_missing": sorted(relevant - ids), "packet": packets[case["case_id"]]})
    return {
        "summary": {
            "evidence_groups_hit": groups_hit,
            "evidence_groups_total": total_groups,
            "evidence_group_recall": groups_hit / total_groups,
            "all_evidence_cases": all_cases,
            "cases_total": len(cases),
            "all_evidence_success": all_cases / len(cases),
            "macro_qrel_chunk_recall": macro_chunk_recall / len(cases),
            "mean_packet_tokens": sum(packet["tokens"] for packet in packets.values()) / len(packets),
            "mean_packet_chunks": sum(packet["chunks"] for packet in packets.values()) / len(packets),
        },
        "cases": case_rows,
    }


def dependency_diagnostics(enrichment: dict, r1_run: dict, chunks: list[dict], policies: list[str],
                           previous: dict, following: dict, section_lead: dict) -> dict:
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
        visual_unsupported = ("image" in anchor_group["type"] or
                              anchor_group["review"]["status"] == "assistant_visual_checked" or
                              any(not by_id[chunk_id]["embedding_eligible"] for chunk_id in set(anchors) | targets))
        policy_hits = {}
        for policy in policies:
            available = set(anchors)
            for anchor_id in anchors:
                if by_id[anchor_id]["embedding_eligible"]:
                    available.update(chunk_id for chunk_id, _ in expansion_ids(
                        policy, "", by_id[anchor_id], previous, following, section_lead
                    ))
            policy_hits[policy] = targets.issubset(available) and not visual_unsupported
        rows.append({"dependency_id": edge["id"], "status": edge["status"], "type": edge["type"],
                     "anchor_chunk_ids": anchors, "target_chunk_ids": sorted(targets),
                     "visual_text_path_unsupported": visual_unsupported, "policy_covers_target": policy_hits})
    eligible = [row for row in rows if not row["visual_text_path_unsupported"]]
    return {"dependencies": rows, "summary": {policy: {
        "covered": sum(row["policy_covers_target"][policy] for row in eligible),
        "eligible": len(eligible),
        "visual_unsupported": len(rows) - len(eligible),
    } for policy in policies}}


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
    require(tokenizers_version == config["tokenizer"]["library_version"], "tokenizers_version_mismatch")
    require(digest(tokenizer_path.read_bytes()) == config["tokenizer"]["file_sha256"], "tokenizer_hash_mismatch")
    require(rerank["inputs"]["corpus_sha256"] == digest(corpus_bytes), "reranker_corpus_hash_mismatch")
    require(enrichment["runtime_ready"] is False, "unexpected_runtime_ready_dependency_labels")
    require(all(edge["automatically_follow"] is False for edge in enrichment["dependencies"]),
            "dependency_labels_must_not_drive_runtime")
    tokenizer = Tokenizer.from_file(str(tokenizer_path))
    tokenizer.no_truncation()
    tokenizer.no_padding()
    chunks = corpus["chunks"]
    by_id, previous, following, section_lead = indexes(chunks)
    policies = [row["id"] for row in config["policies"]]
    stored_rankings = rerank["stages"][config["ranking"]["stage"]]["rankings"]
    rankings = {case_id: rows[:config["ranking"]["candidate_limit"]]
                for case_id, rows in stored_rankings.items()}
    runner = load_r2_runner()
    stages = {}
    for policy in policies:
        for budget in config["packet"]["budgets_tokens_including_special_tokens"]:
            packets = {case["case_id"]: pack(
                rankings[case["case_id"]], case["query"], policy, budget, tokenizer,
                config["packet"]["separator"], by_id, previous, following, section_lead
            ) for case in corpus["cases"]}
            stages[policy + "-b" + str(budget)] = packet_metrics(runner, corpus["cases"], packets)
    dependencies = dependency_diagnostics(enrichment, r1_run, chunks, policies, previous, following, section_lead)
    result = {
        "run_id": config["experiment_id"] + "-run-001",
        "status": "completed_source_only_context_packing_diagnostic",
        "config": config,
        "config_sha256": digest(config_bytes),
        "implementation_sha256": digest(Path(__file__).read_bytes()),
        "inputs": {"corpus_sha256": digest(corpus_bytes), "reranker_results_sha256": digest(rerank_bytes),
                   "enrichment_sha256": digest(enrichment_bytes), "r1_run_sha256": digest(r1_bytes),
                   "tokenizer_sha256": digest(tokenizer_path.read_bytes())},
        "runtime": {"seconds": round(time.perf_counter() - started, 3)},
        "stages": stages,
        "dependency_diagnostics": dependencies,
        "limitations": [
            "manual dependency annotations are evaluator-only, runtime_ready=false and automatically_follow=false",
            "x1/x2 are source-only structural heuristics, not a learned dependency resolver",
            "packet budget uses the BGE-M3 tokenizer because no generation model has been selected",
            "image-only dependencies are unsupported on this text path and are not counted as covered",
            "no generation, citation or hallucination evaluation is included",
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
    result = build(args.corpus.resolve(), args.reranker.resolve(), args.enrichment.resolve(),
                   args.r1_run.resolve(), args.tokenizer.resolve(), args.output.resolve())
    print(json.dumps({"output": args.output.resolve().relative_to(ROOT).as_posix(),
                      "runtime": result["runtime"],
                      "metrics": {stage: value["summary"] for stage, value in result["stages"].items()},
                      "dependency_diagnostics": result["dependency_diagnostics"]["summary"]},
                     ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
