"""Prepare a local text-only corpus for the BGE-M3 duplicate-candidate ablation."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys

from generate_duplicate_pdf_fixtures import OUTPUT_DIR, ROOT
from run_duplicate_candidate_baselines import RELATIONS, document_features, score


OUTPUT_DEFAULT = ROOT / "tmp" / "e07-bge-m3-duplicate" / "corpus.json"


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def build() -> dict[str, object]:
    filenames = sorted({filename for relation in RELATIONS for filename in (relation[3], relation[4])})
    features = {filename: document_features(OUTPUT_DIR / filename) for filename in filenames}
    documents = [
        {
            "filename": filename,
            "embedding_text": features[filename]["normalized_text"],
            "source_sha256": features[filename]["raw_sha256"],
        }
        for filename in filenames
    ]
    qrels = []
    for pair_id, duplicate_class, security_class, left_name, right_name, candidate_expected in RELATIONS:
        ranked = []
        for candidate_name in filenames:
            if candidate_name == right_name:
                continue
            candidate_score = score("minhash128_char5", features[candidate_name], features[right_name])
            ranked.append((candidate_score, candidate_name))
        ranked.sort(key=lambda item: (-item[0], item[1]))
        qrels.append(
            {
                "pair_id": pair_id,
                "duplicate_class": duplicate_class,
                "security_class": security_class,
                "candidate_expected": candidate_expected,
                "left": left_name,
                "right": right_name,
                "minhash_ranking": [
                    {"filename": filename, "score": round(value, 6)} for value, filename in ranked
                ],
            }
        )
    return {
        "snapshot_id": "duplicate-bge-m3-dev-e0.7-2026-09-05",
        "scope": "synthetic_quarantine_development_only",
        "documents": documents,
        "qrels": qrels,
        "embedding_input_fields": ["documents[].embedding_text"],
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
        "documents": len(result["documents"]),
        "relations": len(result["qrels"]),
    }, ensure_ascii=False))


if __name__ == "__main__":
    main()
