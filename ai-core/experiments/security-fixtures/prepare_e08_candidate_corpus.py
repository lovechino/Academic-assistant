"""Prepare the E0.8 corpus with 24 labeled hard negatives outside model input."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys

from generate_duplicate_pdf_fixtures import OUTPUT_DIR, ROOT
from generate_e08_hard_negative_pdf_fixtures import HARD_NEGATIVES
from run_duplicate_candidate_baselines import RELATIONS, document_features, score


OUTPUT_DEFAULT = ROOT / "tmp" / "e08-candidate-routing" / "corpus.json"


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def ranked_names(
    method: str,
    features: dict[str, dict[str, object]],
    query_name: str,
) -> list[dict[str, object]]:
    ranked = [
        (score(method, candidate, features[query_name]), name)
        for name, candidate in features.items()
        if name != query_name
    ]
    ranked.sort(key=lambda item: (-item[0], item[1]))
    return [{"filename": name, "score": round(value, 6)} for value, name in ranked]


def exact_candidates(
    method: str,
    features: dict[str, dict[str, object]],
    query_name: str,
) -> list[str]:
    return sorted(
        name
        for name, candidate in features.items()
        if name != query_name and score(method, candidate, features[query_name]) == 1.0
    )


def build() -> dict[str, object]:
    relation_names = {filename for relation in RELATIONS for filename in (relation[3], relation[4])}
    hard_negative_names = {str(item["filename"]) for item in HARD_NEGATIVES}
    filenames = sorted(relation_names | hard_negative_names)
    missing = [name for name in filenames if not (OUTPUT_DIR / name).is_file()]
    if missing:
        raise FileNotFoundError(f"Missing E0.8 PDF fixtures: {missing}")
    features = {filename: document_features(OUTPUT_DIR / filename) for filename in filenames}

    documents = [
        {
            "filename": filename,
            "embedding_text": features[filename]["normalized_text"],
            "source_sha256": features[filename]["raw_sha256"],
        }
        for filename in filenames
    ]
    document_eval_labels = {
        str(item["filename"]): {
            "role": "hard_negative",
            "category": item["category"],
            "target_family": item["target_family"],
        }
        for item in HARD_NEGATIVES
    }
    for filename in relation_names:
        document_eval_labels[filename] = {"role": "relation_fixture"}

    qrels = []
    for pair_id, duplicate_class, security_class, left_name, right_name, candidate_expected in RELATIONS:
        qrels.append(
            {
                "pair_id": pair_id,
                "duplicate_class": duplicate_class,
                "security_class": security_class,
                "candidate_expected": candidate_expected,
                "left": left_name,
                "right": right_name,
                "raw_exact_candidates": exact_candidates("raw_sha256", features, right_name),
                "canonical_exact_candidates": exact_candidates("canonical_text_exact", features, right_name),
                "minhash_ranking": ranked_names("minhash128_char5", features, right_name),
                "char5_ranking": ranked_names("char5_jaccard", features, right_name),
            }
        )

    return {
        "snapshot_id": "duplicate-hard-negative-routing-e0.8-2026-09-05",
        "scope": "synthetic_quarantine_development_only",
        "documents": documents,
        "document_eval_labels": document_eval_labels,
        "qrels": qrels,
        "counts": {
            "documents": len(documents),
            "pages": 64,
            "relation_documents": len(relation_names),
            "hard_negatives": len(hard_negative_names),
            "physical_relations": len(RELATIONS),
            "candidate_expected_relations": sum(relation[5] for relation in RELATIONS),
        },
        "embedding_input_fields": ["documents[].embedding_text"],
        "evaluation_labels_outside_embedding_input": ["document_eval_labels", "qrels"],
        "labels_excluded_from_embedding_text": True,
        "hidden_test": False,
        "serving_index_allowed": False,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=OUTPUT_DEFAULT)
    args = parser.parse_args()
    result = build()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    payload = json.dumps(result, ensure_ascii=False, indent=2).encode("utf-8") + b"\n"
    args.output.write_bytes(payload)
    sys.stdout.reconfigure(encoding="utf-8")
    print(json.dumps({
        "output": args.output.relative_to(ROOT).as_posix(),
        "sha256": digest(payload),
        **result["counts"],
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
