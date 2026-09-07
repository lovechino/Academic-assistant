# Synthetic security PDF fixtures

Offline-only generator for upload quarantine, duplicate and indirect-prompt-injection evaluation. Runtime source must not import this folder.

`generate_duplicate_pdf_fixtures.py` creates ten synthetic PDFs under `output/pdf/academic-assistant-duplicate-fixtures-v0.1/`:

- base and byte-identical copy;
- metadata-only and benign few-character deltas;
- legitimate lecturer variant and same-title unrelated content;
- visible, hidden-text, image-only and OCR/text-layer-mismatch markers.

All markers are inert synthetic labels, not real credentials or operational instructions. Outputs remain local/ignored, are never added to serving content DB/index and must be treated as untrusted quarantine files.

`generate_remaining_pair_pdf_fixtures.py` adds 24 E0.5 PDFs, forming 12 matched relations for Unicode normalization, punctuation/spacing, page reorder, watermark/header, revision, academic claim change, semester variant, shared boilerplate, hidden annotation, metadata injection, external URL and Unicode-format-character injection.

`generate_multimodal_clean_counterparts.py` adds the two E0.6 clean counterparts required to turn the image-only and OCR/text-layer mismatch modalities into matched relations.

Use the bundled workspace Python because it contains ReportLab and Pillow:

```powershell
& '<bundled-python>' ai-core/experiments/security-fixtures/generate_duplicate_pdf_fixtures.py
& '<bundled-python>' ai-core/experiments/security-fixtures/generate_remaining_pair_pdf_fixtures.py
& '<bundled-python>' ai-core/experiments/security-fixtures/generate_multimodal_clean_counterparts.py
```

After generation, render every PDF with Poppler and inspect PNGs. Text extraction is a diagnostic only; it cannot replace visual review.

After rendering, print deterministic byte, text-layer and visual diagnostics with:

```powershell
& '<bundled-python>' ai-core/experiments/security-fixtures/inspect_duplicate_pdf_fixtures.py
& '<bundled-python>' ai-core/experiments/security-fixtures/inspect_remaining_pair_pdf_fixtures.py
& '<bundled-python>' ai-core/experiments/security-fixtures/run_duplicate_candidate_baselines.py
```

The E0.7 BGE-M3 ablation uses a two-runtime boundary: bundled Python extracts the local PDFs into an ignored `tmp` corpus, while the pinned R2 ONNX environment encodes only `embedding_text` and never receives labels in model input.

```powershell
& '<bundled-python>' ai-core/experiments/security-fixtures/prepare_bge_m3_duplicate_corpus.py
& 'tmp/r2-bge-m3-venv/Scripts/python.exe' -X utf8 ai-core/experiments/security-fixtures/run_bge_m3_duplicate_ablation.py
& '<bundled-python>' ai-core/experiments/security-fixtures/audit_bge_m3_duplicate_result.py
```

E0.8 adds 24 benign hard negatives across shared-boilerplate, same-title/different-content, cross-course lexical-overlap and template-dominated-short categories. Render and visually inspect every generated page before setting the explicit QA flag. The routing run compares direct MinHash/BGE-M3, their union, and exact-first candidate routing; canonical equality remains candidate evidence only.

```powershell
& '<bundled-python>' ai-core/experiments/security-fixtures/generate_e08_hard_negative_pdf_fixtures.py
& '<poppler>/pdftoppm' -png -r 120 '<each-Hxx.pdf>' '<render-prefix>'
& '<bundled-python>' ai-core/experiments/security-fixtures/inspect_e08_hard_negative_pdf_fixtures.py --visual-qa-passed
& '<bundled-python>' ai-core/experiments/security-fixtures/prepare_e08_candidate_corpus.py
& 'tmp/r2-bge-m3-venv/Scripts/python.exe' -X utf8 ai-core/experiments/security-fixtures/run_e08_bge_m3_candidate_routing.py
& '<bundled-python>' ai-core/experiments/security-fixtures/audit_e08_candidate_routing.py
```

E0.9 uses a separate three-layout generator family and creates 12 triplets. Each query has a paraphrased equivalent plus a lexically closer conflicting-claim document. The conflict remains a valid first-stage review candidate; the second-stage metric asks whether a method prefers the equivalent without treating the conflict as safe to merge. Filenames and evaluation roles are excluded from model text.

```powershell
& '<bundled-python>' ai-core/experiments/security-fixtures/generate_e09_equivalence_triplet_pdfs.py
& '<poppler>/pdftoppm' -png -r 120 '<each-E9xx.pdf>' '<render-prefix>'
& '<bundled-python>' ai-core/experiments/security-fixtures/inspect_e09_equivalence_triplet_pdfs.py --visual-qa-passed
& '<bundled-python>' ai-core/experiments/security-fixtures/prepare_e09_equivalence_corpus.py
& 'tmp/r2-bge-m3-venv/Scripts/python.exe' -X utf8 ai-core/experiments/security-fixtures/run_e09_equivalence_triplet_ablation.py
& '<bundled-python>' ai-core/experiments/security-fixtures/audit_e09_equivalence_triplets.py
```
