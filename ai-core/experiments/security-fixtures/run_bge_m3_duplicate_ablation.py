"""Run local BGE-M3 exact-cosine duplicate candidate retrieval on the E0.7 dev corpus."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import platform
import sys
import time

import numpy as np


ROOT = Path(__file__).resolve().parents[3]
CORPUS_DEFAULT = ROOT / "tmp" / "e07-bge-m3-duplicate" / "corpus.json"
MODEL_DEFAULT = ROOT / "tmp" / "models" / "bge-m3-5617a9f61b028005a4858fdac845db406aefb181"
MODEL_REVISION = "5617a9f61b028005a4858fdac845db406aefb181"
MODEL_FILE_SIZE = 724923
MODEL_DATA_SIZE = 2266820608
MODEL_FILE_SHA256 = "f84251230831afb359ab26d9fd37d5936d4d9bb5d1d5410e66442f630f24435b"
MODEL_DATA_SHA256 = "1eebfb28493f67bba03ce0ef64bfdc7fc5a3bd9d7493f818bb1d78cd798416b4"
TOKENIZER_SHA256 = "21106b6d7dab2952c1d496fb21d5dc9db75c28ed361a05f5020bbba27810dd08"


def file_digest(path: Path) -> str:
    hasher = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(8 * 1024 * 1024), b""):
            hasher.update(block)
    return hasher.hexdigest()


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def make_session(model_file: Path, intra_op_threads: int):
    import onnxruntime as ort

    options = ort.SessionOptions()
    options.graph_optimization_level = ort.GraphOptimizationLevel.ORT_ENABLE_ALL
    options.execution_mode = ort.ExecutionMode.ORT_SEQUENTIAL
    options.intra_op_num_threads = intra_op_threads
    options.inter_op_num_threads = 1
    options.enable_mem_pattern = True
    return ort.InferenceSession(str(model_file), sess_options=options, providers=["CPUExecutionProvider"])


def encode_texts(session, tokenizer, texts: list[str], hard_cap: int = 512) -> tuple[np.ndarray, dict[str, object]]:
    vectors: list[np.ndarray] = []
    lengths: list[int] = []
    started = time.perf_counter()
    input_names = {item.name for item in session.get_inputs()}
    output_names = [item.name for item in session.get_outputs()]
    for text in texts:
        encoding = tokenizer.encode(text, add_special_tokens=True)
        require(len(encoding.ids) <= hard_cap, "encoder_input_exceeds_512_tokens")
        lengths.append(len(encoding.ids))
        input_ids = np.asarray([encoding.ids], dtype=np.int64)
        attention_mask = np.ones_like(input_ids)
        feed = {}
        if "input_ids" in input_names:
            feed["input_ids"] = input_ids
        if "attention_mask" in input_names:
            feed["attention_mask"] = attention_mask
        if "token_type_ids" in input_names:
            feed["token_type_ids"] = np.zeros_like(input_ids)
        require(set(feed) == input_names, "unsupported_onnx_inputs")
        outputs = session.run(None, feed)
        named = list(zip(output_names, outputs))
        sentence = next((array for _, array in named if array.ndim == 2 and array.shape[-1] == 1024), None)
        if sentence is None:
            token_output = next((array for _, array in named if array.ndim == 3 and array.shape[-1] == 1024), None)
            require(token_output is not None, "missing_1024d_output")
            sentence = token_output[:, 0, :]
        sentence = np.asarray(sentence, dtype=np.float32)
        norm = np.linalg.norm(sentence, axis=1, keepdims=True)
        require(bool(np.all(norm > 0)), "zero_embedding")
        vectors.append(sentence / norm)
    matrix = np.concatenate(vectors, axis=0)
    seconds = time.perf_counter() - started
    return matrix, {
        "texts": len(texts),
        "seconds": round(seconds, 3),
        "milliseconds_per_text": round(seconds * 1000 / len(texts), 3),
        "min_tokens": min(lengths),
        "max_tokens": max(lengths),
    }


def run(corpus_path: Path, model_dir: Path, intra_op_threads: int) -> dict[str, object]:
    import onnxruntime as ort
    from tokenizers import Tokenizer, __version__ as tokenizers_version

    corpus_bytes = corpus_path.read_bytes()
    corpus = json.loads(corpus_bytes)
    require(corpus["serving_index_allowed"] is False, "corpus_must_be_quarantine_only")
    require(corpus["labels_excluded_from_embedding_text"] is True, "label_leakage_guard_missing")
    require(corpus["hidden_test"] is False, "unexpected_hidden_test_claim")

    model_file = model_dir / "onnx" / "model.onnx"
    model_data = model_dir / "onnx" / "model.onnx_data"
    tokenizer_file = model_dir / "tokenizer.json"
    require(model_file.stat().st_size == MODEL_FILE_SIZE, "model_file_size_mismatch")
    require(model_data.stat().st_size == MODEL_DATA_SIZE, "model_data_size_mismatch")
    require(file_digest(model_file) == MODEL_FILE_SHA256, "model_file_hash_mismatch")
    require(file_digest(model_data) == MODEL_DATA_SHA256, "model_data_hash_mismatch")
    require(file_digest(tokenizer_file) == TOKENIZER_SHA256, "tokenizer_hash_mismatch")

    tokenizer = Tokenizer.from_file(str(tokenizer_file))
    tokenizer.no_truncation()
    tokenizer.no_padding()
    session_started = time.perf_counter()
    session = make_session(model_file, intra_op_threads)
    session_seconds = time.perf_counter() - session_started

    documents = corpus["documents"]
    names = [item["filename"] for item in documents]
    vectors, encode_timing = encode_texts(session, tokenizer, [item["embedding_text"] for item in documents])
    repeat_vector, repeat_timing = encode_texts(session, tokenizer, [documents[0]["embedding_text"]])
    deterministic_delta = float(np.max(np.abs(repeat_vector[0] - vectors[0])))

    name_to_index = {name: index for index, name in enumerate(names)}
    score_matrix_started = time.perf_counter()
    similarity = vectors @ vectors.T
    matrix_seconds = time.perf_counter() - score_matrix_started
    expected = [qrel for qrel in corpus["qrels"] if qrel["candidate_expected"]]
    dense_hits = {1: 0, 3: 0, 5: 0}
    union_hits = {1: 0, 3: 0, 5: 0}
    union_sizes = {1: [], 3: [], 5: []}
    overlaps = {1: [], 3: [], 5: []}
    class_hits = {cutoff: {} for cutoff in (1, 3, 5)}
    per_relation = []

    for qrel in corpus["qrels"]:
        query_index = name_to_index[qrel["right"]]
        ranked_dense = sorted(
            (
                (float(similarity[query_index, candidate_index]), candidate_name)
                for candidate_index, candidate_name in enumerate(names)
                if candidate_name != qrel["right"]
            ),
            key=lambda item: (-item[0], item[1]),
        )
        dense_rank = next(
            (rank for rank, (_, candidate_name) in enumerate(ranked_dense, start=1) if candidate_name == qrel["left"]),
            None,
        )
        minhash_names = [row["filename"] for row in qrel["minhash_ranking"]]
        relation_union = {}
        if qrel["candidate_expected"]:
            for cutoff in (1, 3, 5):
                dense_set = {name for _, name in ranked_dense[:cutoff]}
                minhash_set = set(minhash_names[:cutoff])
                union = dense_set | minhash_set
                overlap = dense_set & minhash_set
                dense_hits[cutoff] += int(qrel["left"] in dense_set)
                union_hits[cutoff] += int(qrel["left"] in union)
                union_sizes[cutoff].append(len(union))
                overlaps[cutoff].append(len(overlap))
                class_hits[cutoff].setdefault(qrel["duplicate_class"], 0)
                class_hits[cutoff][qrel["duplicate_class"]] += int(qrel["left"] in dense_set)
                relation_union[str(cutoff)] = {
                    "hit": qrel["left"] in union,
                    "candidate_count": len(union),
                    "overlap_count": len(overlap),
                }
        per_relation.append(
            {
                "pair_id": qrel["pair_id"],
                "duplicate_class": qrel["duplicate_class"],
                "security_class": qrel["security_class"],
                "candidate_expected": qrel["candidate_expected"],
                "left": qrel["left"],
                "right": qrel["right"],
                "dense_pair_score": round(float(similarity[query_index, name_to_index[qrel["left"]]]), 6),
                "dense_left_rank": dense_rank,
                "dense_top_5": [
                    {"filename": name, "score": round(value, 6)} for value, name in ranked_dense[:5]
                ],
                "minhash_union": relation_union,
            }
        )

    denominator = len(expected)
    dense_aggregate = {
        f"recall_at_{cutoff}": round(dense_hits[cutoff] / denominator, 6) for cutoff in (1, 3, 5)
    }
    dense_aggregate["hits_at_5_by_class"] = dict(sorted(class_hits[5].items()))
    union_aggregate = {
        str(cutoff): {
            "recall": round(union_hits[cutoff] / denominator, 6),
            "mean_candidate_count": round(sum(union_sizes[cutoff]) / denominator, 6),
            "mean_overlap_count": round(sum(overlaps[cutoff]) / denominator, 6),
            "max_candidate_count": max(union_sizes[cutoff]),
        }
        for cutoff in (1, 3, 5)
    }

    return {
        "evaluation_round": "E0.7-bge-m3-duplicate-dev-ablation-2026-09-05",
        "status": "completed_local_dense_candidate_ablation_only",
        "corpus": {
            "path": corpus_path.relative_to(ROOT).as_posix(),
            "sha256": hashlib.sha256(corpus_bytes).hexdigest(),
            "documents": len(documents),
            "relations": len(corpus["qrels"]),
            "candidate_expected_relations": denominator,
            "hidden_test": False,
        },
        "model": {
            "model_id": "BAAI/bge-m3",
            "revision": MODEL_REVISION,
            "format": "upstream_onnx_external_data_float32",
            "dimensions": int(vectors.shape[1]),
            "pooling": "cls_token",
            "normalization": "l2",
            "query_instruction": None,
            "runtime": f"onnxruntime-{ort.__version__}-cpu",
            "tokenizers_version": tokenizers_version,
            "intra_op_threads": intra_op_threads,
        },
        "timing": {
            "platform": platform.platform(),
            "session_load_seconds": round(session_seconds, 3),
            "encode": encode_timing,
            "repeat_probe": repeat_timing,
            "similarity_matrix_seconds": round(matrix_seconds, 6),
        },
        "deterministic_probe_max_abs_delta": deterministic_delta,
        "dense_candidate_recall": dense_aggregate,
        "minhash_union": union_aggregate,
        "relations": per_relation,
        "restrictions": {
            "serving_index_written": False,
            "vectors_persisted": False,
            "external_processing": False,
            "auto_merge_or_publish": False,
            "threshold_selected": False,
        },
        "claims_not_tested": [
            "hidden-test generalization",
            "candidate precision on real documents",
            "security or prompt-injection detection",
            "OCR or image understanding",
            "auto-merge correctness",
            "production latency",
        ],
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--corpus", type=Path, default=CORPUS_DEFAULT)
    parser.add_argument("--model-dir", type=Path, default=MODEL_DEFAULT)
    parser.add_argument("--intra-op-threads", type=int, default=4)
    args = parser.parse_args()
    result = run(args.corpus.resolve(), args.model_dir.resolve(), args.intra_op_threads)
    sys.stdout.reconfigure(encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
