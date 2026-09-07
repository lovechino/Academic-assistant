"""Print deterministic diagnostics for the synthetic quarantine PDF fixtures."""
from __future__ import annotations

from difflib import SequenceMatcher
import hashlib
import json
from pathlib import Path
import re
import unicodedata

from PIL import Image
from pypdf import PdfReader


ROOT = Path(__file__).resolve().parents[3]
PDF_DIR = ROOT / "output" / "pdf" / "academic-assistant-duplicate-fixtures-v0.1"
RENDER_DIR = ROOT / "tmp" / "pdfs" / "academic-assistant-duplicate-fixtures-v0.1" / "rendered"
MARKERS = (
    "[SYNTHETIC_TOOL_EXPORT_INSTRUCTION]",
    "[SYNTHETIC_HIDDEN_CROSS_TENANT_INSTRUCTION]",
    "[SYNTHETIC_IMAGE_ONLY_PROMPT]",
    "[SYNTHETIC_HIDDEN_TOOL_INSTRUCTION]",
)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def normalize_text(text: str) -> str:
    normalized = unicodedata.normalize("NFC", text).casefold()
    return re.sub(r"\s+", " ", normalized).strip()


def difference_hash(path: Path, size: int = 16) -> int:
    image = Image.open(path).convert("L").resize((size + 1, size))
    pixels = list(image.get_flattened_data())
    value = 0
    for row in range(size):
        offset = row * (size + 1)
        for column in range(size):
            value = (value << 1) | (pixels[offset + column] > pixels[offset + column + 1])
    return value


def hamming_distance(left: int, right: int) -> int:
    return (left ^ right).bit_count()


def inspect() -> dict[str, object]:
    files: list[dict[str, object]] = []
    extracted: dict[str, str] = {}
    render_hashes: dict[str, str] = {}
    perceptual_hashes: dict[str, int] = {}

    pdf_paths = [
        path
        for path in sorted(PDF_DIR.glob("F*.pdf"))
        if int(path.name.split("-", 1)[0][1:]) <= 10
    ]
    for pdf_path in pdf_paths:
        fixture_id = pdf_path.name.split("-", 1)[0]
        render_path = RENDER_DIR / f"{pdf_path.stem}.png"
        reader = PdfReader(pdf_path)
        text = "\n".join(page.extract_text() or "" for page in reader.pages)
        normalized = normalize_text(text)
        extracted[fixture_id] = normalized
        render_hashes[fixture_id] = sha256(render_path)
        perceptual_hashes[fixture_id] = difference_hash(render_path)
        files.append(
            {
                "fixture_id": fixture_id,
                "filename": pdf_path.name,
                "byte_size": pdf_path.stat().st_size,
                "page_count": len(reader.pages),
                "raw_sha256": sha256(pdf_path),
                "render_sha256": render_hashes[fixture_id],
                "normalized_text_sha256": hashlib.sha256(normalized.encode("utf-8")).hexdigest(),
                "normalized_text_characters": len(normalized),
                "markers_in_text_layer": [marker for marker in MARKERS if marker.casefold() in normalized],
                "metadata": {
                    "author": reader.metadata.author if reader.metadata else None,
                    "subject": reader.metadata.subject if reader.metadata else None,
                },
            }
        )

    base_text = extracted["F01"]
    base_render = perceptual_hashes["F01"]
    base_raw_hash = next(item["raw_sha256"] for item in files if item["fixture_id"] == "F01")
    comparisons = []
    for fixture_id in sorted(extracted):
        candidate_raw_hash = next(item["raw_sha256"] for item in files if item["fixture_id"] == fixture_id)
        comparisons.append(
            {
                "left": "F01",
                "right": fixture_id,
                "raw_bytes_equal": base_raw_hash == candidate_raw_hash,
                "render_pixels_equal": render_hashes["F01"] == render_hashes[fixture_id],
                "normalized_text_equal": base_text == extracted[fixture_id],
                "normalized_text_similarity": round(SequenceMatcher(None, base_text, extracted[fixture_id]).ratio(), 6),
                "render_dhash_hamming_256": hamming_distance(base_render, perceptual_hashes[fixture_id]),
            }
        )

    by_id = {item["fixture_id"]: item for item in files}
    checks = {
        "ten_pdf_fixtures_present": len(files) == 10,
        "all_single_page": all(item["page_count"] == 1 for item in files),
        "F02_is_byte_identical_to_F01": by_id["F02"]["raw_sha256"] == by_id["F01"]["raw_sha256"],
        "F03_changes_bytes_only_not_text_or_render": (
            by_id["F03"]["raw_sha256"] != by_id["F01"]["raw_sha256"]
            and by_id["F03"]["normalized_text_sha256"] == by_id["F01"]["normalized_text_sha256"]
            and by_id["F03"]["render_sha256"] == by_id["F01"]["render_sha256"]
        ),
        "F08_is_pixel_identical_but_has_hidden_text_marker": (
            by_id["F08"]["render_sha256"] == by_id["F01"]["render_sha256"]
            and MARKERS[1] in by_id["F08"]["markers_in_text_layer"]
        ),
        "F09_image_marker_absent_from_pdf_text_layer": MARKERS[2] not in by_id["F09"]["markers_in_text_layer"],
        "F10_hidden_marker_present_in_pdf_text_layer": MARKERS[3] in by_id["F10"]["markers_in_text_layer"],
    }

    return {
        "fixture_count": len(files),
        "status": "passed" if all(checks.values()) else "failed",
        "checks": checks,
        "files": files,
        "comparisons_against_F01": comparisons,
    }


if __name__ == "__main__":
    print(json.dumps(inspect(), ensure_ascii=False, indent=2))
