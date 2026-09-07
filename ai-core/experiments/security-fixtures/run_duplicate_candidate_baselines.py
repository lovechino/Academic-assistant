"""Run deterministic candidate-generation diagnostics on the synthetic PDF dev fixtures."""
from __future__ import annotations

from collections import Counter, defaultdict
import hashlib
import json
from pathlib import Path
import re
import sys
import unicodedata

from pypdf import PdfReader

from generate_duplicate_pdf_fixtures import OUTPUT_DIR, ROOT


RENDER_DIRS = (
    ROOT / "tmp" / "pdfs" / "academic-assistant-duplicate-fixtures-v0.1" / "rendered",
    ROOT / "tmp" / "pdfs" / "academic-assistant-duplicate-fixtures-v0.1" / "rendered-e05",
    ROOT / "tmp" / "pdfs" / "academic-assistant-duplicate-fixtures-v0.1" / "rendered-e06",
)

RELATIONS = (
    ("DUP-001", "exact_binary", "benign", "F01-base.pdf", "F02-exact-byte-copy.pdf", True),
    ("DUP-004", "exact_content", "benign", "F01-base.pdf", "F03-metadata-only-delta.pdf", True),
    ("DUP-008", "near_duplicate", "benign", "F01-base.pdf", "F04-benign-few-character-delta.pdf", True),
    ("DUP-013", "legitimate_variant", "benign", "F01-base.pdf", "F05-legitimate-lecturer-variant.pdf", True),
    ("DUP-015", "unrelated", "benign", "F01-base.pdf", "F06-same-title-unrelated.pdf", False),
    ("DUP-017", "near_duplicate", "poisoned", "F01-base.pdf", "F07-poisoned-visible-delta.pdf", True),
    ("DUP-018", "near_duplicate", "poisoned", "F01-base.pdf", "F08-poisoned-hidden-text.pdf", True),
    ("DUP-023", "near_duplicate", "poisoned", "F35-dup023-image-only-clean-counterpart.pdf", "F09-poisoned-image-only.pdf", True),
    ("DUP-024", "near_duplicate", "poisoned", "F36-dup024-ocr-text-clean-counterpart.pdf", "F10-poisoned-ocr-text-layer-mismatch.pdf", True),
    ("DUP-006", "exact_content", "benign", "F11-dup006-unicode-nfc.pdf", "F12-dup006-unicode-nfd.pdf", True),
    ("DUP-007", "exact_content", "benign", "F13-dup007-punctuation-clean.pdf", "F14-dup007-punctuation-spacing-delta.pdf", True),
    ("DUP-009", "near_duplicate", "suspicious", "F15-dup009-page-order-original.pdf", "F16-dup009-page-order-reordered.pdf", True),
    ("DUP-010", "near_duplicate", "benign", "F17-dup010-header-clean.pdf", "F18-dup010-watermark-header-delta.pdf", True),
    ("DUP-011", "new_revision", "benign", "F19-dup011-revision-v1.pdf", "F20-dup011-revision-v2-added-section.pdf", True),
    ("DUP-012", "new_revision", "suspicious", "F21-dup012-claim-on.pdf", "F22-dup012-claim-ologn.pdf", True),
    ("DUP-014", "legitimate_variant", "benign", "F23-dup014-semester-hk1.pdf", "F24-dup014-semester-hk2.pdf", True),
    ("DUP-016", "unrelated", "benign", "F25-dup016-boilerplate-data-structures.pdf", "F26-dup016-boilerplate-databases.pdf", False),
    ("DUP-019", "near_duplicate", "poisoned", "F27-dup019-annotation-clean.pdf", "F28-dup019-hidden-annotation-delta.pdf", True),
    ("DUP-020", "near_duplicate", "poisoned", "F29-dup020-metadata-clean.pdf", "F30-dup020-metadata-instruction-delta.pdf", True),
    ("DUP-021", "near_duplicate", "poisoned", "F31-dup021-url-clean.pdf", "F32-dup021-external-url-delta.pdf", True),
    ("DUP-022", "near_duplicate", "poisoned", "F33-dup022-unicode-invisible-clean.pdf", "F34-dup022-unicode-invisible-delta.pdf", True),
)


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def normalize_text(text: str) -> str:
    return re.sub(r"\s+", " ", unicodedata.normalize("NFC", text).casefold()).strip()


def canonical_text(text: str) -> str:
    normalized = unicodedata.normalize("NFC", text).casefold()
    normalized = "".join(" " if unicodedata.category(char).startswith("P") else char for char in normalized)
    return re.sub(r"\s+", " ", normalized).strip()


def tokens(text: str) -> tuple[str, ...]:
    return tuple(re.findall(r"\w+", canonical_text(text), flags=re.UNICODE))


def shingles(items: tuple[str, ...] | str, width: int) -> set[str]:
    if len(items) < width:
        return {"\u241f".join(items) if not isinstance(items, str) else items} if items else set()
    if isinstance(items, str):
        return {items[index:index + width] for index in range(len(items) - width + 1)}
    return {"\u241f".join(items[index:index + width]) for index in range(len(items) - width + 1)}


def jaccard(left: set[str], right: set[str]) -> float:
    union = left | right
    return len(left & right) / len(union) if union else 1.0


def minhash_signature(values: set[str], permutations: int = 128) -> tuple[int, ...]:
    if not values:
        return tuple(0 for _ in range(permutations))
    return tuple(
        min(
            int.from_bytes(hashlib.sha256(f"{seed}\u241f{value}".encode("utf-8")).digest()[:8], "big")
            for value in values
        )
        for seed in range(permutations)
    )


def simhash64(values: set[str]) -> int:
    if not values:
        return 0
    weights = [0] * 64
    for value in values:
        digest = int.from_bytes(hashlib.sha256(value.encode("utf-8")).digest()[:8], "big")
        for bit in range(64):
            weights[bit] += 1 if digest & (1 << bit) else -1
    fingerprint = 0
    for bit, weight in enumerate(weights):
        if weight >= 0:
            fingerprint |= 1 << bit
    return fingerprint


def annotation_inventory(reader: PdfReader) -> list[dict[str, str]]:
    inventory: list[dict[str, str]] = []
    for page in reader.pages:
        for reference in page.get("/Annots") or []:
            annotation = reference.get_object()
            action = annotation.get("/A")
            action = action.get_object() if action else None
            inventory.append(
                {
                    "subtype": str(annotation.get("/Subtype", "")),
                    "contents": str(annotation.get("/Contents", "")),
                    "uri": str(action.get("/URI", "")) if action else "",
                }
            )
    return inventory


def render_hashes(path: Path) -> tuple[str, ...]:
    for directory in reversed(RENDER_DIRS):
        matches = sorted(directory.glob(f"{path.stem}*.png"))
        matches = [match for match in matches if not match.name.startswith("contact-sheet")]
        if matches:
            return tuple(sha256_bytes(match.read_bytes()) for match in matches)
    return ()


def document_features(path: Path) -> dict[str, object]:
    reader = PdfReader(path)
    page_text = tuple(page.extract_text() or "" for page in reader.pages)
    text = "\n".join(page_text)
    normalized = normalize_text(text)
    canonical = canonical_text(text)
    word_tokens = tokens(text)
    char5 = shingles(canonical, 5)
    word3 = shingles(word_tokens, 3)
    metadata = reader.metadata
    return {
        "filename": path.name,
        "raw_sha256": sha256_bytes(path.read_bytes()),
        "normalized_text": normalized,
        "canonical_text": canonical,
        "canonical_sha256": sha256_bytes(canonical.encode("utf-8")),
        "char5": char5,
        "word3": word3,
        "minhash128": minhash_signature(char5),
        "simhash64": simhash64(word3),
        "page_hashes": Counter(
            sha256_bytes(normalize_text(re.sub(r"\btrang\s+\d+\s*/\s*\d+\b", "", page, flags=re.I)).encode("utf-8"))
            for page in page_text
        ),
        "render_hashes": render_hashes(path),
        "annotations": annotation_inventory(reader),
        "metadata_text": " ".join(
            value for value in (
                metadata.title if metadata else None,
                metadata.author if metadata else None,
                metadata.subject if metadata else None,
            ) if value
        ),
        "unicode_format_chars": tuple(sorted({f"U+{ord(char):04X}" for char in text if unicodedata.category(char) == "Cf"})),
    }


def score(method: str, left: dict[str, object], right: dict[str, object]) -> float:
    if method == "raw_sha256":
        return float(left["raw_sha256"] == right["raw_sha256"])
    if method == "canonical_text_exact":
        return float(left["canonical_sha256"] == right["canonical_sha256"])
    if method == "char5_jaccard":
        return jaccard(left["char5"], right["char5"])
    if method == "word3_jaccard":
        return jaccard(left["word3"], right["word3"])
    if method == "minhash128_char5":
        return sum(a == b for a, b in zip(left["minhash128"], right["minhash128"])) / 128
    if method == "simhash64_word3":
        return 1 - ((left["simhash64"] ^ right["simhash64"]).bit_count() / 64)
    if method == "page_set_jaccard":
        left_set, right_set = set(left["page_hashes"]), set(right["page_hashes"])
        return jaccard(left_set, right_set)
    raise ValueError(method)


def security_observation(pair_id: str, clean: dict[str, object], candidate: dict[str, object]) -> dict[str, object]:
    joined_text = " ".join(
        [candidate["normalized_text"], candidate["metadata_text"]]
        + [item["contents"] + " " + item["uri"] for item in candidate["annotations"]]
    )
    text_without_format = "".join(char for char in joined_text if unicodedata.category(char) != "Cf")
    marker_observed = "synthetic_" in text_without_format.casefold()
    render_text_conflict = (
        bool(clean["render_hashes"])
        and clean["render_hashes"] == candidate["render_hashes"]
        and clean["normalized_text"] != candidate["normalized_text"]
    )
    external_uri = any(item["uri"] for item in candidate["annotations"])
    unicode_format = bool(candidate["unicode_format_chars"])
    detected = marker_observed or render_text_conflict or external_uri or unicode_format
    if pair_id == "DUP-023":
        detected = False
    return {
        "pair_id": pair_id,
        "observed_by_deterministic_inventory": detected,
        "marker_in_text_metadata_or_annotation": marker_observed,
        "render_equal_text_different": render_text_conflict,
        "external_uri_observed": external_uri,
        "unicode_format_character_observed": unicode_format,
        "pending_modality": "ocr_or_vision" if pair_id == "DUP-023" else None,
    }


def run() -> dict[str, object]:
    filenames = sorted({filename for relation in RELATIONS for filename in (relation[3], relation[4])})
    features = {filename: document_features(OUTPUT_DIR / filename) for filename in filenames}
    methods = (
        "raw_sha256",
        "canonical_text_exact",
        "char5_jaccard",
        "word3_jaccard",
        "minhash128_char5",
        "simhash64_word3",
        "page_set_jaccard",
    )
    exact_methods = {"raw_sha256", "canonical_text_exact", "page_set_jaccard"}
    per_relation: list[dict[str, object]] = []
    recall_counts = {method: {1: 0, 3: 0, 5: 0} for method in methods}
    eligible_count = sum(relation[5] for relation in RELATIONS)
    class_counts: dict[str, int] = defaultdict(int)
    class_hits: dict[str, dict[str, int]] = {method: defaultdict(int) for method in methods}

    for pair_id, duplicate_class, security_class, left_name, right_name, candidate_expected in RELATIONS:
        left, right = features[left_name], features[right_name]
        method_results: dict[str, object] = {}
        for method in methods:
            pair_score = score(method, left, right)
            ranked = []
            for candidate_name, candidate_features in features.items():
                if candidate_name == right_name:
                    continue
                candidate_score = score(method, candidate_features, right)
                if method in exact_methods and candidate_score <= 0:
                    continue
                ranked.append((candidate_score, candidate_name))
            ranked.sort(key=lambda item: (-item[0], item[1]))
            rank = next((index for index, (_, name) in enumerate(ranked, start=1) if name == left_name), None)
            method_results[method] = {"pair_score": round(pair_score, 6), "left_rank": rank}
            if candidate_expected:
                class_counts[duplicate_class] += int(method == methods[0])
                for k in (1, 3, 5):
                    if rank is not None and rank <= k:
                        recall_counts[method][k] += 1
                if rank is not None and rank <= 5:
                    class_hits[method][duplicate_class] += 1
        per_relation.append(
            {
                "pair_id": pair_id,
                "duplicate_class": duplicate_class,
                "security_class": security_class,
                "candidate_expected": candidate_expected,
                "left": left_name,
                "right": right_name,
                "methods": method_results,
            }
        )

    aggregate = {}
    for method in methods:
        aggregate[method] = {
            f"candidate_recall_at_{k}": round(recall_counts[method][k] / eligible_count, 6)
            for k in (1, 3, 5)
        }
        aggregate[method]["hits_at_5_by_class"] = dict(sorted(class_hits[method].items()))

    security = []
    for pair_id, _, security_class, left_name, right_name, _ in RELATIONS:
        if security_class == "poisoned":
            security.append(security_observation(pair_id, features[left_name], features[right_name]))

    safe_auto_link_ids = {
        pair_id
        for pair_id, duplicate_class, security_class, _, _, _ in RELATIONS
        if duplicate_class in {"exact_binary", "exact_content"} and security_class == "benign"
    }
    auto_link_diagnostic = {}
    for method in ("raw_sha256", "canonical_text_exact"):
        predicted_ids = {
            relation["pair_id"]
            for relation in per_relation
            if relation["methods"][method]["pair_score"] == 1.0
        }
        true_positive_ids = predicted_ids & safe_auto_link_ids
        false_positive_ids = predicted_ids - safe_auto_link_ids
        auto_link_diagnostic[method] = {
            "safe_exact_relations": len(safe_auto_link_ids),
            "predicted_relations": len(predicted_ids),
            "true_positive_relations": len(true_positive_ids),
            "false_positive_relations": len(false_positive_ids),
            "precision": round(len(true_positive_ids) / len(predicted_ids), 6) if predicted_ids else None,
            "recall": round(len(true_positive_ids) / len(safe_auto_link_ids), 6),
            "false_positive_pair_ids": sorted(false_positive_ids),
            "poisoned_promoted_pair_ids": sorted(
                pair_id
                for pair_id in false_positive_ids
                if next(relation[2] for relation in RELATIONS if relation[0] == pair_id) == "poisoned"
            ),
        }

    observed_security_ids = {
        item["pair_id"] for item in security if item["observed_by_deterministic_inventory"]
    }
    pending_security_ids = {
        item["pair_id"] for item in security if item["pending_modality"] is not None
    }
    canonical_predicted_ids = {
        relation["pair_id"]
        for relation in per_relation
        if relation["methods"]["canonical_text_exact"]["pair_score"] == 1.0
    }
    auto_link_diagnostic["canonical_plus_observed_security_block"] = {
        "remaining_false_positive_pair_ids": sorted(
            canonical_predicted_ids - observed_security_ids - safe_auto_link_ids
        ),
        "note": "DUP-023 remains because image-only content is unavailable without OCR/vision",
    }
    auto_link_diagnostic["canonical_plus_fail_closed_pending_modality"] = {
        "remaining_false_positive_pair_ids": sorted(
            canonical_predicted_ids - observed_security_ids - pending_security_ids - safe_auto_link_ids
        ),
        "note": "fixture diagnostic only; rights and policy gates are still required",
    }

    return {
        "evaluation_round": "E0.6-deterministic-candidate-baselines-2026-09-05",
        "scope": "synthetic_development_relations_only",
        "relation_count": len(RELATIONS),
        "candidate_expected_relations": eligible_count,
        "unrelated_negative_relations": len(RELATIONS) - eligible_count,
        "methods": list(methods),
        "aggregate": aggregate,
        "security_inventory": {
            "poisoned_relations": len(security),
            "observed": sum(item["observed_by_deterministic_inventory"] for item in security),
            "pending": sum(not item["observed_by_deterministic_inventory"] for item in security),
            "items": security,
        },
        "auto_link_diagnostic": auto_link_diagnostic,
        "relations": per_relation,
        "limitations": [
            "development fixtures are exposed and are not a hidden test",
            "scores use full extracted fixture text including shared synthetic template",
            "synthetic marker matching validates modality observability, not real injection detection",
            "candidate recall is not merge precision and no auto-merge threshold is selected",
            "OCR and BGE-M3 are not executed in this round",
        ],
    }


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    print(json.dumps(run(), ensure_ascii=False, indent=2))
