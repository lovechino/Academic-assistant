"""Offline corpus audit only. Does not build an application, OCR or an index.

Run with bundled Python: python ai-core/experiments/pdf-pilot/profile_local.py
Results are measurements, NOT validated semantic/visual ground truth.
"""
from pathlib import Path
from datetime import datetime, timezone
import hashlib
import json
import statistics
import re
import pdfplumber
from pypdf import PdfReader

ROOT = Path(__file__).resolve().parents[3]
RAW = ROOT / "data/raw/pdf-pilot"
OUT = ROOT / "data/processed/pdf-pilot/audit-v0.1"
OUT.mkdir(parents=True, exist_ok=True)

SOURCES = {
    "vnua-dsa": ("Học viện Nông nghiệp Việt Nam", "Cấu trúc dữ liệu và giải thuật", "https://dse.vnua.edu.vn/ncthang/pth02003/", "https://dse.vnua.edu.vn/ncthang/pth02003/SlidePDF/"),
    "vnua-dbms": ("Học viện Nông nghiệp Việt Nam", "Hệ quản trị cơ sở dữ liệu", "https://dse.vnua.edu.vn/cnpm/th03005/SlidePDF/", "https://dse.vnua.edu.vn/cnpm/th03005/SlidePDF/"),
    "uet-db": ("Trường Đại học Công nghệ, ĐHQGHN", "Cơ sở dữ liệu", "https://uet.vnu.edu.vn/~chaunh/slide/index.htm", "https://uet.vnu.edu.vn/~chaunh/slide/"),
    "hcmuaf-micro": ("Trường Đại học Nông Lâm TP.HCM", "Kinh tế vi mô", "https://www2.hcmuaf.edu.vn/data/nmduc/KT%20vi%20mo%20Ch2%20cung%20cau%20%5BCompatibility%20Mode%5D.pdf", ""),
}

def union_area(rects):
    """Exact union of clipped image bounding rectangles; not semantic coverage."""
    xs = sorted({v for r in rects for v in (r[0], r[2])})
    total = 0.0
    for x0, x1 in zip(xs, xs[1:]):
        intervals = sorted((r[1], r[3]) for r in rects if r[0] < x1 and r[2] > x0)
        covered, start, end = 0.0, None, None
        for a, b in intervals:
            if start is None:
                start, end = a, b
            elif a <= end:
                end = max(end, b)
            else:
                covered += end - start
                start, end = a, b
        if start is not None:
            covered += end - start
        total += (x1 - x0) * covered
    return total

manifest, page_rows = [], []
for path in sorted((RAW / "quarantine").rglob("*.pdf")):
    group = path.parent.name
    institution, course, landing, base = SOURCES[group]
    url = base + path.name if base else landing
    if path.name == "PTH02003_CauTrucDuLieuVaGiaiThuat.pdf":
        url = landing + path.name
    doc_id = group + "--" + path.stem
    with path.open("rb") as stream:
        sha = hashlib.file_digest(stream, "sha256").hexdigest()
    reader = PdfReader(path)
    meta = reader.metadata or {}
    own_pages = []
    flags = []
    with pdfplumber.open(path) as pdf:
        for page in pdf.pages:
            row = {"document_id": doc_id, "physical_page_1based": page.page_number}
            try:
                text = page.extract_text() or ""
                boxes = []
                for im in page.images:
                    r = (max(0.0, float(im["x0"])), max(0.0, float(im["top"])), min(float(page.width), float(im["x1"])), min(float(page.height), float(im["bottom"])))
                    if r[2] > r[0] and r[3] > r[1]:
                        boxes.append(r)
                image_ratio = union_area(boxes) / float(page.width * page.height)
                vector_count = len(page.lines) + len(page.rects) + len(page.curves)
                row.update({"status": "measured", "width_pt": float(page.width), "height_pt": float(page.height), "chars": len(text), "embedded_image_occurrences": len(page.images), "image_bbox_union_ratio": round(image_ratio, 5), "vector_object_count": vector_count, "scan_candidate_unverified": len(text) < 80 and image_ratio > 0.8, "text_present": bool(text.strip()), "visual_review_status": "not_reviewed"})
                # No source text exported into the manifest; short matching snippets for rights triage only.
                for match in re.finditer(r".{0,35}(?:nghiêm cấm|nội bộ|all rights reserved|creative commons|copyright).{0,110}", text, re.I):
                    flags.append({"page": page.page_number, "snippet": match.group(0)})
            except Exception as exc:
                row.update({"status": "error", "error": str(exc)})
            own_pages.append(row)
            page.close()
    ok = [r for r in own_pages if r["status"] == "measured"]
    record = {"document_id": doc_id, "local_path": path.relative_to(ROOT).as_posix(), "source_url": url, "landing_url": landing, "institution": institution, "course": course, "download_date": "2026-09-04", "sha256": sha, "bytes": path.stat().st_size, "pages": len(reader.pages), "measured_pages": len(ok), "pdf_metadata_unverified": {str(k): str(v) for k, v in meta.items()}, "text_chars": sum(r["chars"] for r in ok), "median_chars_per_page": statistics.median(r["chars"] for r in ok) if ok else None, "low_text_pages_lt80": sum(r["chars"] < 80 for r in ok), "empty_text_pages": sum(not r["text_present"] for r in ok), "embedded_image_occurrences": sum(r["embedded_image_occurrences"] for r in ok), "pages_with_embedded_images": sum(r["embedded_image_occurrences"] > 0 for r in ok), "vector_object_count": sum(r["vector_object_count"] for r in ok), "scan_candidates_unverified": sum(r["scan_candidate_unverified"] for r in ok), "rights_notice_candidates": flags, "rights_status": "unknown_no_open_license_verified", "lifecycle_status": "quarantined", "usage_policy": "local_reference_audit_only_pending_rights_review", "production_index_allowed": False, "redistribution_allowed": False, "training_allowed": False, "subject_review_status": "not_reviewed"}
    manifest.append(record)
    page_rows.extend(own_pages)
    print(json.dumps({k: record[k] for k in ("document_id", "pages", "measured_pages", "text_chars", "embedded_image_occurrences", "vector_object_count")}, ensure_ascii=False), flush=True)

summary = {"snapshot_id": "vn-pdf-pilot-2026-09-04-v0.1", "audit_timestamp_utc": datetime.now(timezone.utc).isoformat(), "method": "pdfplumber-programmatic-text-and-object-audit-v0.1", "pdfplumber_version": pdfplumber.__version__, "documents": len(manifest), "bytes": sum(r["bytes"] for r in manifest), "pages": sum(r["pages"] for r in manifest), "measured_pages": sum(r["measured_pages"] for r in manifest), "empty_text_pages": sum(r["empty_text_pages"] for r in manifest), "low_text_pages_lt80": sum(r["low_text_pages_lt80"] for r in manifest), "embedded_image_occurrences": sum(r["embedded_image_occurrences"] for r in manifest), "vector_object_count": sum(r["vector_object_count"] for r in manifest), "scan_candidates_unverified": sum(r["scan_candidates_unverified"] for r in manifest), "distinct_sha256": len({r["sha256"] for r in manifest}), "limitations": ["Image occurrences include repeated logos/backgrounds, not unique figures.", "Vector counts include decoration, table borders and charts.", "No OCR or layout model run; scan flags are heuristic only.", "Nonempty text does not prove correct reading order or complete evidence.", "All documents remain quarantined pending rights and subject review."]}
for name, obj, dest in (("manifest.json", manifest, RAW), ("page-profile.json", page_rows, OUT), ("summary.json", summary, OUT)):
    (dest / name).write_text(json.dumps(obj, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print(json.dumps(summary, ensure_ascii=False, indent=2), flush=True)
