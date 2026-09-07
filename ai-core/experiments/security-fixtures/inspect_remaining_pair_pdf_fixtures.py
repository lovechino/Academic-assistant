"""Print E0.5 structural/text/render diagnostics for 12 matched PDF relations."""
from __future__ import annotations

from collections import Counter
from difflib import SequenceMatcher
import hashlib
import json
from pathlib import Path
import re
import sys
import unicodedata

from pypdf import PdfReader

from generate_duplicate_pdf_fixtures import OUTPUT_DIR, ROOT


RENDER_DIR = ROOT / "tmp" / "pdfs" / "academic-assistant-duplicate-fixtures-v0.1" / "rendered-e05"
PAIR_FILES = {
    "DUP-006": ("F11-dup006-unicode-nfc.pdf", "F12-dup006-unicode-nfd.pdf"),
    "DUP-007": ("F13-dup007-punctuation-clean.pdf", "F14-dup007-punctuation-spacing-delta.pdf"),
    "DUP-009": ("F15-dup009-page-order-original.pdf", "F16-dup009-page-order-reordered.pdf"),
    "DUP-010": ("F17-dup010-header-clean.pdf", "F18-dup010-watermark-header-delta.pdf"),
    "DUP-011": ("F19-dup011-revision-v1.pdf", "F20-dup011-revision-v2-added-section.pdf"),
    "DUP-012": ("F21-dup012-claim-on.pdf", "F22-dup012-claim-ologn.pdf"),
    "DUP-014": ("F23-dup014-semester-hk1.pdf", "F24-dup014-semester-hk2.pdf"),
    "DUP-016": ("F25-dup016-boilerplate-data-structures.pdf", "F26-dup016-boilerplate-databases.pdf"),
    "DUP-019": ("F27-dup019-annotation-clean.pdf", "F28-dup019-hidden-annotation-delta.pdf"),
    "DUP-020": ("F29-dup020-metadata-clean.pdf", "F30-dup020-metadata-instruction-delta.pdf"),
    "DUP-021": ("F31-dup021-url-clean.pdf", "F32-dup021-external-url-delta.pdf"),
    "DUP-022": ("F33-dup022-unicode-invisible-clean.pdf", "F34-dup022-unicode-invisible-delta.pdf"),
}


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def normalize_text(text: str) -> str:
    normalized = unicodedata.normalize("NFC", text).casefold()
    return re.sub(r"\s+", " ", normalized).strip()


def canonical_punctuation_text(text: str) -> str:
    normalized = unicodedata.normalize("NFC", text).casefold()
    normalized = "".join(" " if unicodedata.category(char).startswith("P") else char for char in normalized)
    return re.sub(r"\s+", " ", normalized).strip()


def without_page_number(text: str) -> str:
    return re.sub(r"\btrang\s+\d+\s*/\s*\d+\b", "", text, flags=re.IGNORECASE)


def annotation_inventory(reader: PdfReader) -> list[dict[str, object]]:
    inventory: list[dict[str, object]] = []
    for page_number, page in enumerate(reader.pages, start=1):
        annotations = page.get("/Annots") or []
        for reference in annotations:
            annotation = reference.get_object()
            action = annotation.get("/A")
            action = action.get_object() if action else None
            inventory.append(
                {
                    "page": page_number,
                    "subtype": str(annotation.get("/Subtype")),
                    "flags": int(annotation.get("/F", 0)),
                    "contents": str(annotation.get("/Contents", "")),
                    "uri": str(action.get("/URI", "")) if action else "",
                }
            )
    return inventory


def inspect_file(filename: str) -> dict[str, object]:
    path = OUTPUT_DIR / filename
    reader = PdfReader(path)
    page_texts = [page.extract_text() or "" for page in reader.pages]
    normalized_pages = [normalize_text(text) for text in page_texts]
    content_pages = [normalize_text(without_page_number(text)) for text in page_texts]
    text = "\n".join(page_texts)
    normalized = normalize_text(text)
    render_paths = sorted(RENDER_DIR.glob(f"{path.stem}-*.png"))
    format_chars = sorted({f"U+{ord(char):04X}" for char in text if unicodedata.category(char) == "Cf"})
    metadata = reader.metadata
    return {
        "filename": filename,
        "bytes": path.stat().st_size,
        "pages": len(reader.pages),
        "sha256": sha256(path),
        "render_sha256": [sha256(render_path) for render_path in render_paths],
        "normalized_text_sha256": hashlib.sha256(normalized.encode("utf-8")).hexdigest(),
        "canonical_punctuation_sha256": hashlib.sha256(canonical_punctuation_text(text).encode("utf-8")).hexdigest(),
        "normalized_text_characters": len(normalized),
        "normalized_page_hashes": [hashlib.sha256(page.encode("utf-8")).hexdigest() for page in normalized_pages],
        "content_page_hashes": [hashlib.sha256(page.encode("utf-8")).hexdigest() for page in content_pages],
        "annotations": annotation_inventory(reader),
        "metadata": {
            "author": metadata.author if metadata else None,
            "subject": metadata.subject if metadata else None,
        },
        "unicode_format_characters": format_chars,
        "_normalized_text": normalized,
    }


def inspect() -> dict[str, object]:
    pairs: list[dict[str, object]] = []
    by_pair: dict[str, tuple[dict[str, object], dict[str, object]]] = {}
    for pair_id, (left_filename, right_filename) in PAIR_FILES.items():
        left = inspect_file(left_filename)
        right = inspect_file(right_filename)
        by_pair[pair_id] = (left, right)
        pairs.append(
            {
                "pair_id": pair_id,
                "left": {key: value for key, value in left.items() if not key.startswith("_")},
                "right": {key: value for key, value in right.items() if not key.startswith("_")},
                "comparison": {
                    "raw_bytes_equal": left["sha256"] == right["sha256"],
                    "render_pixels_equal": left["render_sha256"] == right["render_sha256"],
                    "normalized_text_equal": left["normalized_text_sha256"] == right["normalized_text_sha256"],
                    "canonical_punctuation_text_equal": left["canonical_punctuation_sha256"] == right["canonical_punctuation_sha256"],
                    "normalized_text_similarity": round(
                        SequenceMatcher(None, left["_normalized_text"], right["_normalized_text"]).ratio(), 6
                    ),
                    "content_page_multiset_equal": Counter(left["content_page_hashes"]) == Counter(right["content_page_hashes"]),
                    "content_page_order_equal": left["content_page_hashes"] == right["content_page_hashes"],
                },
            }
        )

    checks = {
        "twelve_matched_relations_present": len(pairs) == 12,
        "twenty_four_pdf_files_present": len({name for pair in PAIR_FILES.values() for name in pair}) == 24,
        "DUP_006_nfc_normalized_text_equal": by_pair["DUP-006"][0]["normalized_text_sha256"] == by_pair["DUP-006"][1]["normalized_text_sha256"],
        "DUP_007_punctuation_canonical_text_equal": by_pair["DUP-007"][0]["canonical_punctuation_sha256"] == by_pair["DUP-007"][1]["canonical_punctuation_sha256"],
        "DUP_009_same_page_set_different_order": (
            Counter(by_pair["DUP-009"][0]["content_page_hashes"]) == Counter(by_pair["DUP-009"][1]["content_page_hashes"])
            and by_pair["DUP-009"][0]["content_page_hashes"] != by_pair["DUP-009"][1]["content_page_hashes"]
        ),
        "DUP_019_render_equal_annotation_added": (
            by_pair["DUP-019"][0]["render_sha256"] == by_pair["DUP-019"][1]["render_sha256"]
            and len(by_pair["DUP-019"][0]["annotations"]) == 0
            and any("SYNTHETIC_AGENT_OVERRIDE_ANNOTATION" in item["contents"] for item in by_pair["DUP-019"][1]["annotations"])
        ),
        "DUP_020_render_and_text_equal_metadata_changed": (
            by_pair["DUP-020"][0]["render_sha256"] == by_pair["DUP-020"][1]["render_sha256"]
            and by_pair["DUP-020"][0]["normalized_text_sha256"] == by_pair["DUP-020"][1]["normalized_text_sha256"]
            and by_pair["DUP-020"][0]["metadata"]["subject"] != by_pair["DUP-020"][1]["metadata"]["subject"]
        ),
        "DUP_021_external_uri_annotation_added": (
            len(by_pair["DUP-021"][0]["annotations"]) == 0
            and any(item["uri"] == "https://example.invalid/synthetic-exfil-marker" for item in by_pair["DUP-021"][1]["annotations"])
        ),
        "DUP_022_render_equal_unicode_format_chars_added": (
            by_pair["DUP-022"][0]["render_sha256"] == by_pair["DUP-022"][1]["render_sha256"]
            and not by_pair["DUP-022"][0]["unicode_format_characters"]
            and "U+200B" in by_pair["DUP-022"][1]["unicode_format_characters"]
        ),
    }
    return {
        "evaluation_round": "E0.5-remaining-pdf-relations-2026-09-05",
        "status": "passed" if all(checks.values()) else "failed",
        "checks": checks,
        "pairs": pairs,
    }


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    print(json.dumps(inspect(), ensure_ascii=False, indent=2))
