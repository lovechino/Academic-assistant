# Deterministic duplicate candidate baselines — E0.6

Ngày tạo/kiểm: 2026-09-05

Kết luận: **đã hoàn thiện matched relations cho DUP-023/024 và chạy 7 baseline trên 21 physical relations; Jaccard/MinHash đạt candidate recall@1 = 1.0 trên dev fixture nhỏ, nhưng canonical-text auto-link promote nhầm 3/8 poisoned relations. Không chốt threshold và không có production claim.**

## 1. Artifact và phạm vi

- Corpus: 36 PDF/40 trang synthetic, quarantine-only.
- Relation-level evaluation: 21 physical relations.
- Expected candidate: 19 relations.
- Unrelated negatives: 2 relations.
- Poisoned modalities: 8 relations.
- Hidden test: chưa tạo.
- OCR/BGE-M3: chưa chạy.

Artifacts:

- [E0.6 two-counterpart manifest](../../data/evaluation/synthetic/duplicate-detection-v0.1/pdf-fixtures-e06-manifest.json);
- [E0.6 baseline result](../../data/evaluation/synthetic/duplicate-detection-v0.1/e06-candidate-baseline-results.json);
- [reproducible experiment helpers](../../ai-core/experiments/security-fixtures/README.md);
- [E0.5 relation coverage](24-pdf-relation-coverage-e0.5.md).

## 2. Hai matched relations vừa hoàn thiện

| Pair | Clean ↔ poisoned relation | Verification |
|---|---|---|
| DUP-023 | Image sạch ↔ image có synthetic marker | PDF text bằng nhau, render khác; marker không có trong text layer |
| DUP-024 | Raster an toàn ↔ cùng raster + hidden text marker | Render pixels bằng nhau, extracted text khác |

Hai file đều qua visual QA, không clipping/font/layout issue. DUP-023 chứng minh text-only pipeline không quan sát được image payload; DUP-024 chứng minh render-only pipeline không quan sát được hidden text layer.

## 3. Baseline config

| Method | Cấu hình |
|---|---|
| Raw exact | SHA-256 toàn file |
| Canonical exact | NFC + casefold + Unicode punctuation thành space + collapse whitespace |
| Character Jaccard | Character 5-grams |
| Word Jaccard | Word 3-grams |
| MinHash | 128 permutations trên character 5-grams |
| SimHash | 64-bit trên word 3-grams |
| Page set | Jaccard của normalized exact page hashes, bỏ page number |

Candidate ranking dùng full extracted text, bao gồm synthetic template chung; tie-break theo filename. Đây là development diagnostic, không phải config production.

## 4. Candidate recall

| Method | Recall@1 | Recall@3 | Recall@5 |
|---|---:|---:|---:|
| Raw SHA-256 | 0.052632 | 0.052632 | 0.052632 |
| Canonical text exact | 0.368421 | 0.368421 | 0.368421 |
| Character 5-gram Jaccard | 1.000000 | 1.000000 | 1.000000 |
| Word 3-gram Jaccard | 1.000000 | 1.000000 | 1.000000 |
| MinHash-128 char5 | 1.000000 | 1.000000 | 1.000000 |
| SimHash-64 word3 | 0.736842 | 0.789474 | 0.894737 |
| Exact page-set Jaccard | 0.368421 | 0.368421 | 0.368421 |

SimHash miss ở top-5:

- DUP-013 legitimate lecturer variant: rank 6;
- DUP-011 substantive new revision: rank 20.

Không được đọc `1.0` của Jaccard/MinHash như accuracy đã đạt. Mỗi matched pair dùng template/topic khá riêng nên left thường là candidate gần nhất; chưa có corpus nhiễu lớn, cross-course hard negatives hoặc hidden templates.

## 5. Auto-link diagnostic

Chỉ có bốn physical relations được coi là safe exact ở mức nội dung: DUP-001, 004, 006 và 007. Đây vẫn chưa bao gồm rights/tenant workflow context.

| Rule giả định | TP | FP | Precision | Recall | Poisoned promoted |
|---|---:|---:|---:|---:|---:|
| Raw SHA-256 equal | 1 | 0 | 1.000000 | 0.250000 | 0 |
| Canonical text equal | 4 | 3 | 0.571429 | 1.000000 | 3 |

Ba false positives của canonical text:

- DUP-019: hidden annotation;
- DUP-020: instruction-like PDF metadata;
- DUP-023: image-only marker.

Điều này bác bỏ đường `canonical hash equal → auto-link/promote`. Canonical equality chỉ tạo duplicate evidence. Raw equality chỉ được reuse tenant blob/idempotent receipt; vẫn giữ submission, uploader, rights và approval riêng.

## 6. Security inventory

| Metric | Result |
|---|---:|
| Poisoned physical relations | 8 |
| Observable bằng text/metadata/annotation/URI/Unicode/render-text deterministic checks | 7 |
| Pending OCR/vision | 1 — DUP-023 |

Nếu chỉ block finding đã quan sát, DUP-023 vẫn lọt canonical auto-link. Khi áp dụng `required modality pending → fail closed`, false positive còn lại giảm về 0 trên fixture này. Đây chỉ là invariant demonstration; synthetic marker matching không phải prompt-injection detector thực tế.

Tesseract không có trong workspace, nên không cài thêm OCR stack và không giả lập kết quả OCR trong vòng này.

## 7. Stop/go decision

| Hạng mục | Decision | Lý do |
|---|---|---|
| Raw SHA-256 cho same-tenant blob reuse | GO có điều kiện | Deterministic; không kế thừa rights/publish |
| Canonical text hash cho candidate cluster | GO cho quarantine candidate | Bắt exact-content nhưng bỏ modality |
| Char5/word3/MinHash cho candidate generation | GO tới ablation tiếp theo | Recall tốt trên dev; chưa có precision/hidden evidence |
| SimHash làm primary candidate method | NO-GO hiện tại | Miss new revision/variant ở top-5 |
| Bất kỳ similarity/hash nào auto-merge/publish | NO-GO | Poisoned/variant/unrelated overlap |
| Promotion khi OCR/vision pending | HARD BLOCK | DUP-023 là concrete counterexample |
| Production threshold | BLOCKED BY EVIDENCE | Chưa có hidden family hoặc reviewer |

## 8. E0.7 đề xuất

Trạng thái: đã thực hiện trong [BGE-M3 duplicate candidate ablation E0.7](26-bge-m3-duplicate-ablation-e0.7.md); danh sách dưới đây được giữ làm trace của quyết định tại thời điểm E0.6.

1. Chạy BGE-M3 trong quarantine-only dev ablation với cùng 21 relations và recall@1/3/5.
2. So union candidate sets: MinHash ∪ BGE-M3; đo candidate expansion và latency/cost.
3. Bổ sung nhiều unrelated/shared-template hard negatives để đo candidate precision/load, không chỉ recall.
4. Chọn local OCR path sau dependency/security review; không gửi fixture lên external provider mặc định.
5. Tạo hidden-family pack bởi reviewer/process độc lập; generator hiện tại không được xem là hidden.
6. Chỉ sau đó mới freeze candidate budget và threshold.

## 9. Không được claim

- Không có detector precision/recall trên dữ liệu thật.
- Không có OCR, multimodal model, BGE-M3 hoặc RAGAS result trong E0.6.
- Không có auto-link/publish runtime.
- 36 synthetic PDF không chứng minh security against prompt injection.
- 100% dev candidate recall không phải final benchmark.
