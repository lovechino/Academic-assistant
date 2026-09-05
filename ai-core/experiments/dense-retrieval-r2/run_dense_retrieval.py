"""Run the local BGE-M3 dense baseline and evidence-completeness diagnostics."""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
import platform
import sys
import time

import numpy as np


ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
CONFIG = HERE / "config-v0.1.json"
CORPUS_DEFAULT = ROOT / "data/processed/voer-dsa-dense-r2-v0.1/corpus.json"
MODEL_DEFAULT = ROOT / "tmp/models/bge-m3-5617a9f61b028005a4858fdac845db406aefb181"
OUTPUT_DEFAULT = ROOT / "data/processed/voer-dsa-dense-r2-v0.1"


def digest(value: str | bytes) -> str:
    return hashlib.sha256(value.encode("utf-8") if isinstance(value, str) else value).hexdigest()


def file_digest(path: Path) -> str:
    hasher = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(8 * 1024 * 1024), b""):
            hasher.update(block)
    return hasher.hexdigest()


def require(ok: bool, code: str) -> None:
    if not ok:
        raise ValueError(code)


def file_identity(path: Path) -> dict:
    return {"path": path.as_posix(), "size": path.stat().st_size, "sha256": file_digest(path)}


def make_session(model_file: Path, intra_op_threads: int):
    import onnxruntime as ort

    options = ort.SessionOptions()
    options.graph_optimization_level = ort.GraphOptimizationLevel.ORT_ENABLE_ALL
    options.execution_mode = ort.ExecutionMode.ORT_SEQUENTIAL
    options.intra_op_num_threads = intra_op_threads
    options.inter_op_num_threads = 1
    options.enable_mem_pattern = True
    return ort.InferenceSession(str(model_file), sess_options=options, providers=["CPUExecutionProvider"])


def encode_texts(session, tokenizer, texts: list[str], batch_size: int, hard_cap: int,
                 pad_id: int = 1) -> tuple[np.ndarray, dict]:
    vectors = []
    lengths = []
    started = time.perf_counter()
    input_names = {item.name for item in session.get_inputs()}
    output_names = [item.name for item in session.get_outputs()]
    for offset in range(0, len(texts), batch_size):
        batch = texts[offset:offset + batch_size]
        encodings = tokenizer.encode_batch(batch, add_special_tokens=True)
        batch_lengths = [len(encoding.ids) for encoding in encodings]
        require(max(batch_lengths) <= hard_cap, "encoder_input_exceeds_hard_cap")
        lengths.extend(batch_lengths)
        width = max(batch_lengths)
        input_ids = np.full((len(batch), width), pad_id, dtype=np.int64)
        attention_mask = np.zeros((len(batch), width), dtype=np.int64)
        for row, encoding in enumerate(encodings):
            input_ids[row, :len(encoding.ids)] = encoding.ids
            attention_mask[row, :len(encoding.ids)] = 1
        feed = {}
        if "input_ids" in input_names:
            feed["input_ids"] = input_ids
        if "attention_mask" in input_names:
            feed["attention_mask"] = attention_mask
        if "token_type_ids" in input_names:
            feed["token_type_ids"] = np.zeros_like(input_ids)
        require(set(feed) == input_names, "unsupported_onnx_inputs:" + ",".join(sorted(input_names - set(feed))))
        raw_outputs = session.run(None, feed)
        named = list(zip(output_names, raw_outputs))
        sentence = next((array for _, array in named if array.ndim == 2 and array.shape[-1] == 1024), None)
        if sentence is None:
            token_output = next((array for _, array in named if array.ndim == 3 and array.shape[-1] == 1024), None)
            require(token_output is not None, "missing_1024d_onnx_output")
            sentence = token_output[:, 0, :]
        sentence = np.asarray(sentence, dtype=np.float32)
        norms = np.linalg.norm(sentence, axis=1, keepdims=True)
        require(bool(np.all(norms > 0)), "zero_embedding")
        vectors.append(sentence / norms)
    matrix = np.concatenate(vectors, axis=0) if vectors else np.empty((0, 1024), dtype=np.float32)
    return matrix, {
        "texts": len(texts),
        "seconds": round(time.perf_counter() - started, 3),
        "min_tokens": min(lengths) if lengths else 0,
        "max_tokens": max(lengths) if lengths else 0,
        "onnx_inputs": sorted(input_names),
        "onnx_outputs": output_names,
    }


def binary_ndcg(ranked_ids: list[str], relevant: set[str], cutoff: int) -> float:
    if not relevant:
        return 0.0
    dcg = sum(1.0 / math.log2(rank + 1) for rank, chunk_id in enumerate(ranked_ids[:cutoff], 1)
              if chunk_id in relevant)
    ideal = sum(1.0 / math.log2(rank + 1) for rank in range(1, min(len(relevant), cutoff) + 1))
    return dcg / ideal if ideal else 0.0


def group_hit(group: dict, retrieved: set[str]) -> bool:
    return any(set(alternative["all_of_chunk_ids"]).issubset(retrieved)
               for alternative in group["alternatives"])


def evaluate(cases: list[dict], rankings: dict[str, list[dict]], cutoffs: list[int]) -> tuple[dict, list[dict]]:
    per_case = []
    for case in cases:
        ranking = rankings[case["case_id"]]
        ranked_ids = [row["chunk_id"] for row in ranking]
        relevant = {
            chunk_id
            for group in case["required_groups"]
            for alternative in group["alternatives"]
            for chunk_id in alternative["all_of_chunk_ids"]
        }
        first_rank = next((rank for rank, chunk_id in enumerate(ranked_ids, 1) if chunk_id in relevant), None)
        by_cutoff = {}
        for cutoff in cutoffs:
            retrieved = set(ranked_ids[:cutoff])
            hits = [group_hit(group, retrieved) for group in case["required_groups"]]
            by_cutoff[str(cutoff)] = {
                "required_groups_hit": sum(hits),
                "required_groups_total": len(hits),
                "all_evidence_success": bool(hits) and all(hits),
                "any_evidence_hit": bool(relevant & retrieved),
                "qrel_chunk_recall": len(relevant & retrieved) / len(relevant) if relevant else 0.0,
                "binary_ndcg": binary_ndcg(ranked_ids, relevant, cutoff),
            }
        per_case.append({
            "case_id": case["case_id"],
            "query": case["query"],
            "qrel_chunk_ids": sorted(relevant),
            "first_qrel_chunk_rank": first_rank,
            "reciprocal_rank_first_qrel_chunk": 1.0 / first_rank if first_rank else 0.0,
            "by_cutoff": by_cutoff,
            "top_results": ranking[:max(cutoffs)],
        })

    aggregate = {}
    total_groups = sum(len(case["required_groups"]) for case in cases)
    for cutoff in cutoffs:
        rows = [case["by_cutoff"][str(cutoff)] for case in per_case]
        aggregate[str(cutoff)] = {
            "evidence_groups_hit": sum(row["required_groups_hit"] for row in rows),
            "evidence_groups_total": total_groups,
            "evidence_group_recall": sum(row["required_groups_hit"] for row in rows) / total_groups,
            "all_evidence_cases": sum(row["all_evidence_success"] for row in rows),
            "cases_total": len(rows),
            "all_evidence_success": sum(row["all_evidence_success"] for row in rows) / len(rows),
            "any_evidence_hit_rate": sum(row["any_evidence_hit"] for row in rows) / len(rows),
            "macro_qrel_chunk_recall": sum(row["qrel_chunk_recall"] for row in rows) / len(rows),
            "mean_binary_ndcg": sum(row["binary_ndcg"] for row in rows) / len(rows),
        }
    aggregate["mean_reciprocal_rank_first_qrel_chunk"] = (
        sum(case["reciprocal_rank_first_qrel_chunk"] for case in per_case) / len(per_case)
    )
    return aggregate, per_case


def build(corpus_path: Path, model_dir: Path, output_dir: Path, intra_op_threads: int) -> dict:
    import onnxruntime as ort
    from tokenizers import Tokenizer, __version__ as tokenizers_version

    config_bytes = CONFIG.read_bytes()
    config = json.loads(config_bytes)
    corpus_bytes = corpus_path.read_bytes()
    corpus = json.loads(corpus_bytes)
    require(corpus["config_sha256"] == digest(config_bytes), "corpus_config_hash_mismatch")
    require(tokenizers_version == config["tokenizer"]["library_version"], "tokenizers_version_mismatch")
    require(ort.__version__ == config["encoder"]["runtime_version"], "onnxruntime_version_mismatch")

    model_file = model_dir / config["encoder"]["model_file"]
    model_data_file = model_dir / config["encoder"]["model_data_file"]
    tokenizer_file = model_dir / config["tokenizer"]["file"]
    require(model_file.stat().st_size == config["encoder"]["model_file_size"], "model_file_size_mismatch")
    require(model_data_file.stat().st_size == config["encoder"]["model_data_file_size"], "model_data_size_mismatch")
    require(digest(tokenizer_file.read_bytes()) == config["tokenizer"]["file_sha256"], "model_tokenizer_hash_mismatch")
    model_identity = file_identity(model_file)
    model_data_identity = file_identity(model_data_file)
    for key, identity in (("model_file_sha256", model_identity), ("model_data_file_sha256", model_data_identity)):
        if config["encoder"].get(key):
            require(identity["sha256"] == config["encoder"][key], key + "_mismatch")

    chunks = [row for row in corpus["chunks"] if row["embedding_eligible"]]
    tokenizer = Tokenizer.from_file(str(tokenizer_file))
    tokenizer.no_truncation()
    tokenizer.no_padding()
    session_started = time.perf_counter()
    session = make_session(model_file, intra_op_threads)
    session_seconds = round(time.perf_counter() - session_started, 3)
    batch_size = config["encoder"]["batch_size"]
    cap = config["chunking"]["hard_cap_tokens_including_special_tokens"]

    chunk_vectors, chunk_timing = encode_texts(
        session, tokenizer, [row["embedding_text"] for row in chunks], batch_size, cap
    )
    query_vectors, query_timing = encode_texts(
        session, tokenizer, [case["query"] for case in corpus["cases"]], batch_size, cap
    )
    repeat_vector, _ = encode_texts(session, tokenizer, [corpus["cases"][0]["query"]], 1, cap)
    deterministic_probe_max_abs_delta = float(np.max(np.abs(repeat_vector[0] - query_vectors[0])))

    scores = query_vectors @ chunk_vectors.T
    rankings = {}
    max_cutoff = max(config["evaluation"]["cutoffs"])
    for query_index, case in enumerate(corpus["cases"]):
        order = np.argsort(-scores[query_index], kind="stable")[:max_cutoff]
        rankings[case["case_id"]] = [
            {
                "rank": rank,
                "chunk_id": chunks[index]["chunk_id"],
                "document_id": chunks[index]["document_id"],
                "score": float(scores[query_index, index]),
                "embedding_tokens": chunks[index]["embedding_tokens"],
                "preview": chunks[index]["embedding_text"][:240],
            }
            for rank, index in enumerate(order, 1)
        ]
    aggregate, per_case = evaluate(corpus["cases"], rankings, config["evaluation"]["cutoffs"])

    output_dir.mkdir(parents=True, exist_ok=True)
    vector_path = output_dir / "vectors.npz"
    np.savez_compressed(
        vector_path,
        chunk_ids=np.asarray([row["chunk_id"] for row in chunks]),
        chunk_vectors=chunk_vectors,
        case_ids=np.asarray([case["case_id"] for case in corpus["cases"]]),
        query_vectors=query_vectors,
    )
    result = {
        "run_id": config["experiment_id"] + "-run-001",
        "status": "completed_dense_retrieval_only",
        "config": config,
        "config_sha256": digest(config_bytes),
        "implementation_sha256": digest(Path(__file__).read_bytes()),
        "corpus_path": corpus_path.relative_to(ROOT).as_posix(),
        "corpus_sha256": digest(corpus_bytes),
        "vector_path": vector_path.relative_to(ROOT).as_posix(),
        "vector_file_sha256": digest(vector_path.read_bytes()),
        "model": {
            "model_file": {**model_identity, "path": model_file.relative_to(ROOT).as_posix()},
            "external_data_file": {**model_data_identity, "path": model_data_file.relative_to(ROOT).as_posix()},
            "tokenizer_file_sha256": digest(tokenizer_file.read_bytes()),
            "embedding_dimensions": int(chunk_vectors.shape[1]),
            "pooling": config["encoder"]["pooling"],
            "normalization": config["encoder"]["normalization"],
        },
        "runtime": {
            "python": platform.python_version(),
            "platform": platform.platform(),
            "numpy": np.__version__,
            "onnxruntime": ort.__version__,
            "tokenizers": tokenizers_version,
            "providers": session.get_providers(),
            "intra_op_threads": intra_op_threads,
            "batch_size": batch_size,
            "session_load_seconds": session_seconds,
            "chunk_encoding": chunk_timing,
            "query_encoding": query_timing,
            "deterministic_probe_max_abs_delta": deterministic_probe_max_abs_delta,
        },
        "corpus_summary": corpus["summary"],
        "metrics": aggregate,
        "cases": per_case,
        "limitations": corpus["limitations"] + [
            "metrics are retrieval-only diagnostics and are not agent or answer accuracy",
            "binary chunk relevance is derived from locator alignment rather than human-graded chunk judgments",
            "the exact-search index is appropriate only for this small pilot corpus",
        ],
    }
    result_path = output_dir / "results.json"
    result_path.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return {"result_path": result_path, "vector_path": vector_path, "result": result}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--corpus", type=Path, default=CORPUS_DEFAULT)
    parser.add_argument("--model-dir", type=Path, default=MODEL_DEFAULT)
    parser.add_argument("--output-dir", type=Path, default=OUTPUT_DEFAULT)
    parser.add_argument("--intra-op-threads", type=int, default=4)
    args = parser.parse_args()
    built = build(args.corpus.resolve(), args.model_dir.resolve(), args.output_dir.resolve(), args.intra_op_threads)
    result = built["result"]
    print(json.dumps({
        "result": built["result_path"].relative_to(ROOT).as_posix(),
        "vectors": built["vector_path"].relative_to(ROOT).as_posix(),
        "runtime": result["runtime"],
        "metrics": result["metrics"],
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
