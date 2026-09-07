"""Prepare the 96-document E0.9 triplet corpus without embedding evaluation labels."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys

from generate_duplicate_pdf_fixtures import OUTPUT_DIR as E08_OUTPUT_DIR, ROOT
from generate_e08_hard_negative_pdf_fixtures import HARD_NEGATIVES
from generate_e09_equivalence_triplet_pdfs import OUTPUT_DIR as E09_OUTPUT_DIR, TRIPLETS
from run_duplicate_candidate_baselines import RELATIONS, document_features, score


OUTPUT_DEFAULT = ROOT / "tmp" / "e09-equivalence-triplets" / "corpus.json"


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def ranked(
    method: str,
    features: dict[str, dict[str, object]],
    query_name: str,
) -> list[dict[str, object]]:
    values = [
        (score(method, candidate, features[query_name]), name)
        for name, candidate in features.items()
        if name != query_name
    ]
    values.sort(key=lambda item: (-item[0], item[1]))
    return [{"filename": name, "score": round(value, 6)} for value, name in values]


def build() -> dict[str, object]:
    relation_names = {filename for relation in RELATIONS for filename in (relation[3], relation[4])}
    e08_hard_names = {str(item["filename"]) for item in HARD_NEGATIVES}
    triplet_names = {str(name) for triplet in TRIPLETS for name in triplet["filenames"].values()}
    paths = {
        **{name: E08_OUTPUT_DIR / name for name in relation_names | e08_hard_names},
        **{name: E09_OUTPUT_DIR / name for name in triplet_names},
    }
    missing = sorted(name for name, path in paths.items() if not path.is_file())
    if missing:
        raise FileNotFoundError(f"Missing E0.9 corpus PDFs: {missing}")
    features = {name: document_features(path) for name, path in sorted(paths.items())}

    documents = [
        {
            "filename": name,
            "embedding_text": features[name]["normalized_text"],
            "source_sha256": features[name]["raw_sha256"],
        }
        for name in sorted(features)
    ]
    labels: dict[str, dict[str, object]] = {
        name: {"role": "prior_relation_fixture"} for name in relation_names
    }
    labels.update({
        str(item["filename"]): {
            "role": "prior_hard_negative",
            "category": item["category"],
        }
        for item in HARD_NEGATIVES
    })
    triplet_rows: list[dict[str, object]] = []
    for triplet in TRIPLETS:
        filenames = triplet["filenames"]
        for role in ("query", "equivalent", "conflict"):
            labels[str(filenames[role])] = {
                "role": f"triplet_{role}",
                "triplet_id": triplet["triplet_id"],
                "category": triplet["category"],
                "layout_family": triplet["layout_family"],
            }
        query_name = str(filenames["query"])
        triplet_rows.append({
            "triplet_id": triplet["triplet_id"],
            "category": triplet["category"],
            "layout_family": triplet["layout_family"],
            "query": query_name,
            "equivalent": str(filenames["equivalent"]),
            "conflict_review_required": str(filenames["conflict"]),
            "char5_ranking": ranked("char5_jaccard", features, query_name),
            "minhash_ranking": ranked("minhash128_char5", features, query_name),
        })

    return {
        "snapshot_id": "equivalence-triplet-candidate-corpus-e0.9-2026-09-05",
        "scope": "synthetic_quarantine_development_only",
        "documents": documents,
        "document_eval_labels": labels,
        "triplets": triplet_rows,
        "counts": {
            "documents": len(documents),
            "pages": 100,
            "prior_relation_documents": len(relation_names),
            "prior_hard_negatives": len(e08_hard_names),
            "triplet_documents": len(triplet_names),
            "triplets": len(triplet_rows),
        },
        "evaluation_semantics": {
            "equivalent": "preferred for semantic equivalence ranking",
            "conflict_review_required": "must remain candidate-visible but cannot be auto-equated",
            "first_stage_goal": "retrieve both for review",
            "second_stage_goal": "prefer equivalent over conflicting claim",
        },
        "embedding_input_fields": ["documents[].embedding_text"],
        "evaluation_labels_outside_embedding_input": ["document_eval_labels", "triplets"],
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
