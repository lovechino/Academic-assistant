"""Local extraction diagnostics; annotated regions are ORACLE hints, not predictions.

Does not run OCR, train models, index corpus or publish source content.
"""
from pathlib import Path
import json
import time
import hashlib
from itertools import groupby
import pdfplumber

ROOT = Path(__file__).resolve().parents[3]
PACK = ROOT / "data/evaluation/silver/vn-pdf-visual-v0.1/page-audit.json"
OUT = ROOT / "data/processed/pdf-pilot/layout-diagnostic-v0.1"
OUT.mkdir(parents=True, exist_ok=True)
audit = json.loads(PACK.read_text(encoding="utf-8"))
docs = {d["document_id"]: d for d in json.loads((ROOT / "data/raw/pdf-pilot/manifest.json").read_text(encoding="utf-8"))}
results = []
for note in audit["pages"]:
    meta = docs[note["document_id"]]
    path = ROOT / meta["local_path"]
    with path.open("rb") as f:
        assert hashlib.file_digest(f, "sha256").hexdigest() == meta["sha256"]
    start = time.perf_counter()
    with pdfplumber.open(path) as doc:
        page = doc.pages[note["physical_page_1based"] - 1]
        def absolute(b):
            return (b[0]*page.width, b[1]*page.height, b[2]*page.width, b[3]*page.height)
        row = {"page_audit_id": note["id"], "document_id": note["document_id"], "sha256": meta["sha256"], "physical_page_1based": note["physical_page_1based"], "whole_page_text": page.extract_text() or "", "regions": []}
        for region in note["regions"]:
            row["regions"].append({"id": region["id"], "oracle_bbox_normalized": region["bbox"], "text": page.crop(absolute(region["bbox"])).extract_text() or ""})
        logical = sorted((r for r in note["regions"] if r["type"] == "logical_slide"), key=lambda r: r["reading_order"])
        if logical:
            boxes = [(r["id"], r["reading_order"], absolute(r["bbox"])) for r in logical]
            word_labels = []
            excluded_words = 0
            for word in page.extract_words():
                cx = (word["x0"] + word["x1"])/2
                cy = (word["top"] + word["bottom"])/2
                matches = [(i, order) for i, order, b in boxes if b[0] <= cx < b[2] and b[1] <= cy < b[3]]
                if len(matches) == 1:
                    word_labels.append({"text": word["text"], "region_id": matches[0][0], "order": matches[0][1]})
                else:
                    excluded_words += 1
            sequence = [w["order"] for w in word_labels]
            runs = [k for k, _ in groupby(sequence)]
            # Compare only cross-region pairs; this says nothing about within-slide order.
            denominator = sum(sequence[i] != sequence[j] for i in range(len(sequence)) for j in range(i+1, len(sequence)))
            inversions = sum(sequence[i] > sequence[j] for i in range(len(sequence)) for j in range(i+1, len(sequence)))
            row["handout_diagnostic"] = {"expected_region_order": [r["id"] for r in logical], "whole_page_word_region_runs": runs, "run_count": len(runs), "expected_run_count": len(logical), "labeled_words": len(sequence), "excluded_words": excluded_words, "cross_region_pairs": denominator, "inverted_cross_region_pairs": inversions, "cross_region_pair_order_accuracy": 1-inversions/denominator if denominator else None, "oracle_region_order_accuracy": 1.0 if denominator else None, "oracle_score_warning": "1.0 is by construction using supplied annotations, not a learned-parser result", "whole_page_word_labels": word_labels}
        if any(r["type"] in ("table", "row_fragment") for r in note["regions"]):
            row["default_table_extraction"] = page.extract_tables()
        row["elapsed_seconds_single_uncontrolled_run"] = round(time.perf_counter()-start, 4)
        page.close()
    results.append(row)
    print(note["id"], "chars", len(row["whole_page_text"]), "runs", row.get("handout_diagnostic",{}).get("run_count"), flush=True)

(OUT / "extractions.json").write_text(json.dumps({"method": "pdfplumber-default-versus-assistant-region-oracle", "pdfplumber_version": pdfplumber.__version__, "source_snapshot": audit["source_snapshot"], "rights": audit["rights"], "pages": results}, ensure_ascii=False, indent=2)+"\n", encoding="utf-8")
summary = [{"page_id": r["page_audit_id"], **{k:v for k,v in r["handout_diagnostic"].items() if k != "whole_page_word_labels"}} for r in results if "handout_diagnostic" in r]
print(json.dumps(summary, ensure_ascii=False, indent=2), flush=True)
