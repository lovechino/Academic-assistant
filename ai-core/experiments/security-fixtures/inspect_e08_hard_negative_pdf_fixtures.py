"""Audit E0.8 hard-negative PDFs and write a local reproducibility manifest."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys

from PIL import Image
from pypdf import PdfReader

from generate_duplicate_pdf_fixtures import OUTPUT_DIR, ROOT
from generate_e08_hard_negative_pdf_fixtures import HARD_NEGATIVES


RENDER_DIR = ROOT / "tmp" / "pdfs" / "academic-assistant-duplicate-fixtures-v0.1" / "rendered-e08"
OUTPUT_DEFAULT = (
    ROOT
    / "data"
    / "evaluation"
    / "synthetic"
    / "duplicate-detection-v0.1"
    / "e08-hard-negative-pdf-manifest.json"
)


def sha256(path: Path) -> str:
    hasher = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            hasher.update(block)
    return hasher.hexdigest()


def inspect(visual_qa_passed: bool) -> dict[str, object]:
    expected_names = {str(item["filename"]) for item in HARD_NEGATIVES}
    observed_names = {path.name for path in OUTPUT_DIR.glob("H*.pdf")}
    if observed_names != expected_names:
        raise ValueError({
            "missing": sorted(expected_names - observed_names),
            "unexpected": sorted(observed_names - expected_names),
        })
    if not visual_qa_passed:
        raise ValueError("Pass --visual-qa-passed only after inspecting all rendered pages")

    documents = []
    for item in HARD_NEGATIVES:
        filename = str(item["filename"])
        pdf_path = OUTPUT_DIR / filename
        render_matches = sorted(RENDER_DIR.glob(f"{pdf_path.stem}-*.png"))
        if len(render_matches) != 1:
            raise ValueError(f"Expected one rendered page for {filename}, found {len(render_matches)}")
        reader = PdfReader(pdf_path)
        if len(reader.pages) != 1:
            raise ValueError(f"Expected one PDF page for {filename}")
        text = reader.pages[0].extract_text() or ""
        for required in (str(item["fixture_id"]), str(item["title"]), str(item["heading"])):
            if required not in text:
                raise ValueError(f"Missing extracted text {required!r} in {filename}")
        annotations = reader.pages[0].get("/Annots") or []
        if annotations:
            raise ValueError(f"Unexpected annotation in benign hard negative {filename}")
        with Image.open(render_matches[0]) as image:
            render_size = list(image.size)
        documents.append({
            "filename": filename,
            "fixture_id": item["fixture_id"],
            "category": item["category"],
            "target_family": item["target_family"],
            "pdf_sha256": sha256(pdf_path),
            "pdf_bytes": pdf_path.stat().st_size,
            "page_count": 1,
            "extracted_characters": len(text),
            "render_filename": render_matches[0].name,
            "render_sha256": sha256(render_matches[0]),
            "render_size": render_size,
            "annotation_count": 0,
        })

    return {
        "snapshot_id": "duplicate-hard-negatives-e0.8-2026-09-05",
        "classification": "synthetic_quarantine_development_fixture",
        "contains_real_documents": False,
        "pdf_count": len(documents),
        "page_count": sum(int(item["page_count"]) for item in documents),
        "category_distribution": {
            category: sum(item["category"] == category for item in documents)
            for category in sorted({str(item["category"]) for item in documents})
        },
        "visual_qa": {
            "status": "passed_manual_contact_sheet_review",
            "render_dpi": 120,
            "rendered_pages_checked": len(documents),
            "defects_observed": 0,
            "contact_sheets": [f"contact-{index:02d}.png" for index in range(1, 5)],
        },
        "generator_sha256": sha256(Path(__file__).with_name("generate_e08_hard_negative_pdf_fixtures.py")),
        "documents": documents,
        "restrictions": {
            "serving_index_allowed": False,
            "redistribution_approved": False,
            "real_document_claim": False,
            "hidden_test_claim": False,
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=OUTPUT_DEFAULT)
    parser.add_argument("--visual-qa-passed", action="store_true")
    args = parser.parse_args()
    result = inspect(args.visual_qa_passed)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    payload = json.dumps(result, ensure_ascii=False, indent=2).encode("utf-8") + b"\n"
    args.output.write_bytes(payload)
    sys.stdout.reconfigure(encoding="utf-8")
    print(json.dumps({
        "output": args.output.relative_to(ROOT).as_posix(),
        "sha256": hashlib.sha256(payload).hexdigest(),
        "pdf_count": result["pdf_count"],
        "page_count": result["page_count"],
        "visual_qa": result["visual_qa"],
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
