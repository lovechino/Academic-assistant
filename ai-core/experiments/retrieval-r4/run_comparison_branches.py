"""Decompose supported Vietnamese comparisons and retrieve candidates for each branch."""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import re
import sys
import time
import unicodedata

import numpy as np


ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
CONFIG = HERE / "comparison-config-v0.1.json"
R2_CONFIG = ROOT / "ai-core/experiments/dense-retrieval-r2/config-v0.1.json"
R2_RUNNER = ROOT / "ai-core/experiments/dense-retrieval-r2/run_dense_retrieval.py"
R3_HYBRID = ROOT / "ai-core/experiments/retrieval-r3/run_hybrid_retrieval.py"
CORPUS_DEFAULT = ROOT / "data/processed/voer-dsa-dense-r2-v0.1/corpus.json"
VECTORS_DEFAULT = ROOT / "data/processed/voer-dsa-dense-r2-v0.1/vectors.npz"
MODEL_DEFAULT = ROOT / "tmp/models/bge-m3-5617a9f61b028005a4858fdac845db406aefb181"
OUTPUT_DEFAULT = ROOT / "data/processed/voer-dsa-retrieval-r4-v0.1/comparison-branches.json"


def digest(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def require(ok: bool, code: str) -> None:
    if not ok:
        raise ValueError(code)


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def normalize_query(text: str) -> str:
    return " ".join(unicodedata.normalize("NFKC", text).casefold().strip().split())


def decompose(query: str, config: dict) -> dict:
    normalized = normalize_query(query).rstrip(" .?!;:")
    prefix = config["trigger_prefix"]
    if not normalized.startswith(prefix):
        return {"status": "not_comparison", "normalized_query": normalized, "branches": []}
    body = normalized[len(prefix):]
    for suffix in config["removable_suffixes"]:
        if body.endswith(suffix):
            body = body[:-len(suffix)].rstrip()
            break
    entity_separator = config["entity_separator"]
    relation_separator = config["relation_separator"]
    if entity_separator not in body:
        return {"status": "unsupported_missing_entity_separator", "normalized_query": normalized, "branches": []}
    left, right_entity = body.rsplit(entity_separator, 1)
    if relation_separator not in left:
        return {"status": "unsupported_missing_relation_separator", "normalized_query": normalized, "branches": []}
    relation, left_entity = left.rsplit(relation_separator, 1)
    values = [relation.strip(), left_entity.strip(), right_entity.strip()]
    if any(not value for value in values):
        return {"status": "unsupported_empty_component", "normalized_query": normalized, "branches": []}
    relation, left_entity, right_entity = values
    branches = [
        {"branch_id": "left", "entity": left_entity, "query": relation + relation_separator + left_entity},
        {"branch_id": "right", "entity": right_entity, "query": relation + relation_separator + right_entity},
    ]
    return {
        "status": "decomposed",
        "normalized_query": normalized,
        "relation": relation,
        "branches": branches,
    }


def build(corpus_path: Path, vector_path: Path, model_dir: Path, output_path: Path) -> dict:
    from tokenizers import Tokenizer

    config_bytes = CONFIG.read_bytes()
    config = json.loads(config_bytes)
    r2_config = json.loads(R2_CONFIG.read_text(encoding="utf-8"))
    corpus_bytes = corpus_path.read_bytes()
    corpus = json.loads(corpus_bytes)
    vector_bytes = vector_path.read_bytes()
    vectors = np.load(vector_path, allow_pickle=False)
    chunks = [row for row in corpus["chunks"] if row["embedding_eligible"]]
    require(vectors["chunk_ids"].tolist() == [row["chunk_id"] for row in chunks], "chunk_vector_order_mismatch")

    decompositions = {case["case_id"]: decompose(case["query"], config["decomposition"])
                      for case in corpus["cases"]}
    selected_cases = [case for case in corpus["cases"] if decompositions[case["case_id"]]["status"] == "decomposed"]
    branch_rows = [
        {"case_id": case["case_id"], **branch}
        for case in selected_cases
        for branch in decompositions[case["case_id"]]["branches"]
    ]
    require(branch_rows, "no_supported_comparisons")

    r2 = load_module("retrieval_r4_r2", R2_RUNNER)
    r3 = load_module("retrieval_r4_r3_hybrid", R3_HYBRID)
    tokenizer = Tokenizer.from_file(str(model_dir / r2_config["tokenizer"]["file"]))
    tokenizer.no_padding()
    tokenizer.no_truncation()
    session = r2.make_session(model_dir / r2_config["encoder"]["model_file"], 4)
    query_vectors, encoding_runtime = r2.encode_texts(
        session,
        tokenizer,
        [row["query"] for row in branch_rows],
        r2_config["encoder"]["batch_size"],
        r2_config["chunking"]["hard_cap_tokens_including_special_tokens"],
    )
    dense_scores = query_vectors @ vectors["chunk_vectors"].T
    bm25 = r3.BM25(
        [chunk["embedding_text"] for chunk in chunks],
        config["retrieval"]["bm25_k1"],
        config["retrieval"]["bm25_b"],
    )
    depth = config["retrieval"]["prefetch_depth_per_retriever"]
    take = config["retrieval"]["candidate_pool_per_branch"]
    results: dict[str, dict] = {}
    for branch_index, branch in enumerate(branch_rows):
        dense_order = np.argsort(-dense_scores[branch_index], kind="stable")
        sparse_scores = bm25.score(branch["query"])
        sparse_order = np.argsort(-sparse_scores, kind="stable")
        candidates = r3.rrf(
            dense_order,
            sparse_order,
            sparse_scores,
            chunks,
            depth,
            config["retrieval"]["rrf_k"],
        )[:take]
        results.setdefault(branch["case_id"], {})[branch["branch_id"]] = {
            "entity": branch["entity"],
            "query": branch["query"],
            "candidates": candidates,
        }

    result = {
        "run_id": config["experiment_id"] + "-branches-run-001",
        "status": "completed_qrel_free_comparison_branch_retrieval",
        "config": config,
        "config_sha256": digest(config_bytes),
        "implementation_sha256": digest(Path(__file__).read_bytes()),
        "inputs": {"corpus_sha256": digest(corpus_bytes), "vectors_sha256": digest(vector_bytes)},
        "decomposition_audit": decompositions,
        "selected_case_ids": [case["case_id"] for case in selected_cases],
        "branches": results,
        "runtime": {"branch_queries": len(branch_rows), "encoding": encoding_runtime},
        "limitations": [
            "the parser intentionally supports only the frozen 'relation of A and B' Vietnamese pattern",
            "branch retrieval and selection do not inspect qrels",
            "retrieval candidates do not by themselves establish evidence correctness or answer safety",
        ],
    }
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--corpus", type=Path, default=CORPUS_DEFAULT)
    parser.add_argument("--vectors", type=Path, default=VECTORS_DEFAULT)
    parser.add_argument("--model-dir", type=Path, default=MODEL_DEFAULT)
    parser.add_argument("--output", type=Path, default=OUTPUT_DEFAULT)
    args = parser.parse_args()
    result = build(args.corpus.resolve(), args.vectors.resolve(), args.model_dir.resolve(), args.output.resolve())
    print(json.dumps({
        "output": args.output.resolve().relative_to(ROOT).as_posix(),
        "selected_case_ids": result["selected_case_ids"],
        "decomposition": {case_id: result["decomposition_audit"][case_id]
                          for case_id in result["selected_case_ids"]},
        "runtime": result["runtime"],
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
