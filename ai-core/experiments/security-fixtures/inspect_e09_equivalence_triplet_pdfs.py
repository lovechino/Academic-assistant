"""Audit E0.9 triplet PDFs and write a local reproducibility manifest."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys

from PIL import Image
from pypdf import PdfReader

from generate_e09_equivalence_triplet_pdfs import OUTPUT_DIR, ROOT, TRIPLETS


RENDER_DIR = ROOT / "tmp" / "pdfs" / "academic-assistant-equivalence-triplets-v0.1" / "rendered-e09"
OUTPUT_DEFAULT = (
    ROOT
    / "data"
    / "evaluation"
    / "synthetic"
    / "duplicate-detection-v0.1"
    / "e09-equivalence-triplet-pdf-manifest.json"
)


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def inspect(visual_qa_passed: bool) -> dict[str, object]:
    if not visual_qa_passed:
        raise ValueError("Pass --visual-qa-passed only after inspecting all rendered pages")
    expected = {str(name) for triplet in TRIPLETS for name in triplet["filenames"].values()}
    observed = {path.name for path in OUTPUT_DIR.glob("E9*.pdf")}
    if observed != expected:
        raise ValueError({"missing": sorted(expected - observed), "unexpected": sorted(observed - expected)})

    documents: list[dict[str, object]] = []
    for triplet in TRIPLETS:
        for role in ("query", "equivalent", "conflict"):
            filename = str(triplet["filenames"][role])
            pdf_path = OUTPUT_DIR / filename
            render_matches = sorted(RENDER_DIR.glob(f"{pdf_path.stem}-*.png"))
            if len(render_matches) != 1:
                raise ValueError(f"Expected one render for {filename}, found {len(render_matches)}")
            reader = PdfReader(pdf_path)
            if len(reader.pages) != 1:
                raise ValueError(f"Expected one page for {filename}")
            text = reader.pages[0].extract_text() or ""
            normalized_text = " ".join(text.split())
            if " ".join(str(triplet["topic"]).split()) not in normalized_text:
                raise ValueError(f"Missing topic in {filename}")
            if any(" ".join(str(line).split()) not in normalized_text for line in triplet[role]):
                raise ValueError(f"Extracted text mismatch in {filename}")
            lowered = text.casefold()
            if any(token in lowered for token in ("equivalent", "conflict", "query_role", "triplet_id")):
                raise ValueError(f"Evaluation role leaked into rendered text for {filename}")
            if reader.pages[0].get("/Annots"):
                raise ValueError(f"Unexpected annotation in {filename}")
            with Image.open(render_matches[0]) as image:
                render_size = list(image.size)
            documents.append({
                "filename": filename,
                "triplet_id": triplet["triplet_id"],
                "role": role,
                "category": triplet["category"],
                "layout_family": triplet["layout_family"],
                "pdf_sha256": digest(pdf_path),
                "pdf_bytes": pdf_path.stat().st_size,
                "page_count": 1,
                "extracted_characters": len(text),
                "render_filename": render_matches[0].name,
                "render_sha256": digest(render_matches[0]),
                "render_size": render_size,
                "annotation_count": 0,
                "role_present_in_model_text": False,
            })

    return {
        "snapshot_id": "equivalence-triplets-e0.9-2026-09-05",
        "classification": "synthetic_quarantine_development_fixture",
        "contains_real_documents": False,
        "triplet_count": len(TRIPLETS),
        "pdf_count": len(documents),
        "page_count": len(documents),
        "layout_family_distribution": {
            family: sum(item["layout_family"] == family for item in documents)
            for family in sorted({str(item["layout_family"]) for item in documents})
        },
        "visual_qa": {
            "status": "passed_manual_contact_sheet_review",
            "render_dpi": 120,
            "rendered_pages_checked": len(documents),
            "defects_observed": 0,
            "contact_sheets": [f"contact-{index:02d}.png" for index in range(1, 7)],
        },
        "generator_sha256": digest(Path(__file__).with_name("generate_e09_equivalence_triplet_pdfs.py")),
        "documents": documents,
        "restrictions": {
            "serving_index_allowed": False,
            "redistribution_approved": False,
            "gold_label_claim": False,
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
        "triplets": result["triplet_count"],
        "pdf_count": result["pdf_count"],
        "visual_qa": result["visual_qa"],
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
