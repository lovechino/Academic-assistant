# Synthetic PDF duplicate/security fixtures — E0.4

Ngày tạo/kiểm: 2026-09-05

Kết luận: **10/10 PDF synthetic render được và qua visual QA; các quan hệ exact/metadata-only/hidden/image-only hoạt động như thiết kế; chưa chạy OCR, BGE-M3 hoặc detector threshold**.

## 1. Mục tiêu và phạm vi

Vòng E0.4 biến một phần mini-set E0.3 từ mô tả text/metadata thành PDF thật để kiểm tra các failure mode mà label thuần không thể đại diện:

- cùng byte;
- cùng nội dung nhìn thấy nhưng khác PDF metadata;
- thay đổi vài ký tự/từ;
- biến thể giảng viên hợp lệ;
- trùng tiêu đề nhưng khác môn;
- poisoned delta nhìn thấy;
- poisoned text layer không nhìn thấy;
- marker chỉ nằm trong ảnh;
- nội dung raster nhìn thấy và text layer ẩn mâu thuẫn.

Toàn bộ file là dữ liệu tổng hợp, được giữ trong quarantine fixture local. Không file nào được ghi vào content DB, serving index, model context hay dịch vụ OCR/VLM bên ngoài.

Artifacts:

- [generator và inspector](../../ai-core/experiments/security-fixtures/README.md);
- [PDF fixture manifest](../../data/evaluation/synthetic/duplicate-detection-v0.1/pdf-fixtures-manifest.json);
- [E0.3 labeled mini-set](22-duplicate-detection-labeled-mini-set-v0.1.md);
- [upload/quarantine/dedup policy](../governance/05-secure-upload-quarantine-deduplication-v0.1.md).

## 2. Bộ PDF

| ID | Quan hệ/rủi ro được mô phỏng | Expected use |
|---|---|---|
| F01 | Clean base | Mốc so sánh |
| F02 | Byte-identical copy của F01 | Exact raw-hash path |
| F03 | Render + normalized text giống F01, metadata khác | Canonical content path |
| F04 | Benign wording delta | Near-duplicate review |
| F05 | Legitimate lecturer variant | Không auto-merge |
| F06 | Cùng tiêu đề nhưng nội dung khác | False-merge negative |
| F07 | Near duplicate có visible synthetic instruction marker | Security quarantine |
| F08 | Pixel-identical với F01 nhưng có invisible text marker | Text-layer security scan |
| F09 | Synthetic instruction marker chỉ nằm trong raster image | OCR/vision security scan |
| F10 | Raster nhìn thấy an toàn nhưng text layer ẩn có marker | Layer-conflict quarantine |

### 2.1 Ánh xạ vào pair oracle

Ánh xạ này chỉ dùng PDF để hiện thực hóa **quan hệ vật lý**. Uploader, tenant, rights, purpose và expected resolution tiếp tục lấy từ `pairs.jsonl`; detector không được suy các thuộc tính đó từ file.

| PDF relation | Pair IDs có thể dùng | Mức coverage |
|---|---|---|
| F01 ↔ F02 | DUP-001, 002, 003, 026 | Exact bytes; workflow context quyết định retry/link/isolate/rights hold |
| F01 ↔ F03 | DUP-004, 005, 025 | Exact content + metadata delta; rights vẫn là policy input |
| F01 ↔ F04 | DUP-008 | Benign near duplicate |
| F01 ↔ F05 | DUP-013 | Legitimate lecturer variant |
| F01 ↔ F06 | DUP-015 | Same-title unrelated negative |
| F01 ↔ F07 | DUP-017 | Visible poisoned delta |
| F01 ↔ F08 | DUP-018 | Hidden text-layer delta, pixel-identical |
| F09 nội bộ | DUP-023 | Mới cover image-marker modality; clean matched pair còn thiếu |
| F10 nội bộ | DUP-024 | Mới cover layer conflict; clean matched pair còn thiếu |

12 pair từng chưa có PDF relation trong E0.4 (DUP-006/007, 009-012, 014, 016, 019-022) đã được hiện thực hóa ở [E0.5](24-pdf-relation-coverage-e0.5.md). Manifest E0.4 vẫn giữ nguyên danh sách backlog như một snapshot lịch sử.

## 3. Verification đã chạy

Mỗi PDF có một trang A4. Đã render toàn bộ 10 trang bằng Poppler ở 130 DPI và xem bằng ảnh, không thấy clipping, font lỗi hoặc marker ẩn bị lộ.

| Check | Kết quả |
|---|---|
| PDF được tạo | 10/10 |
| Page count | 10/10 là 1 trang |
| Visual QA | 10/10 pass |
| F01 ↔ F02 | raw bytes, normalized text và render đều bằng nhau |
| F01 ↔ F03 | raw bytes khác; normalized text và render bằng nhau |
| F01 ↔ F08 | render pixels bằng nhau; text layer khác và chứa hidden marker |
| F09 image marker | nhìn thấy trong render; không có trong PDF text extraction |
| F10 hidden marker | có trong text extraction; không nhìn thấy trong render |

Các SHA-256 cụ thể nằm trong manifest. Generator dùng chế độ deterministic để quan hệ byte/render có thể tái kiểm.

## 4. Diagnostic signal đầu tiên

So với F01:

| Candidate | Normalized text similarity | Render dHash distance / 256 | Điều rút ra |
|---|---:|---:|---|
| F02 exact copy | 1.000000 | 0 | Raw hash đủ cho retry cùng byte |
| F03 metadata-only | 1.000000 | 0 | Raw hash đơn lẻ bỏ sót exact content |
| F04 benign near duplicate | 0.833914 | 8 | Cần candidate + diff/review |
| F05 legitimate variant | 0.637019 | 6 | Layout gần không có nghĩa được merge |
| F06 same-title unrelated | 0.567633 | 7 | Visual hash đơn giản dễ bị boilerplate/layout chi phối |
| F07 visible poisoned delta | 0.845622 | 11 | Poisoned file có thể giống base hơn benign delta |
| F08 hidden-text poisoned delta | 0.948113 | 0 | Pixel-identical vẫn có thể chứa text-layer injection |
| F09 image-only marker | 0.555556 | 35 | Text extraction không quan sát marker trong ảnh |
| F10 OCR/text mismatch | 0.523810 | 32 | Phải so các representation, không chọn một layer làm chân lý |

Đây là diagnostics, không phải accuracy benchmark. Chưa có threshold và không được diễn giải các số trên thành quyết định publish.

## 5. Quyết định kiến trúc được củng cố

Một similarity score không thể quyết định cả duplicate và security:

1. F07 poisoned có text similarity cao hơn F04 benign.
2. F05/F06 có dHash gần base hơn F04 vì cùng template/layout.
3. F08 có render hoàn toàn giống base nhưng text layer mang delta độc hại.
4. F09 không thể được bảo vệ bởi text-only parser.
5. Exact/near duplicate không tự kế thừa owner, rights, approval hoặc tenant visibility.

Vì vậy intake cần hai nhánh song song sau safe parse:

- **duplicate evidence**: raw hash → canonical text/page hash → candidate generation → aligned diff;
- **security evidence**: metadata/annotation/URL/text-layer scan + OCR/vision scan + cross-representation conflict checks.

Hai nhánh chỉ hợp nhất ở resolution workflow. `reuse`, `link`, `version`, `keep separate`, `rights hold` hoặc `security quarantine` là quyết định có provenance và policy context, không phải output trực tiếp của embedding.

## 6. Metric cho detector round kế tiếp

| Metric | Denominator | Gate/ý nghĩa |
|---|---|---|
| Exact binary recall | Các pair byte-identical | 100%; deterministic |
| Exact content recall | Container/metadata/Unicode/whitespace equivalent | Đo riêng raw hash |
| Candidate recall@k | Near/new revision/poisoned delta | Detector không được bỏ ứng viên trước diff |
| False merge rate | Legitimate variant + unrelated | Critical; không auto-merge |
| Poisoned-delta quarantine recall | Visible/hidden/image/annotation/metadata/URL/OCR cases | Đo theo modality |
| Poisoned promotion rate | Mọi poisoned fixture | Hard gate = 0 |
| Layer conflict detection | Render/OCR/text mismatch cases | Phải tạo review reason có trace |
| Review/abstention coverage | Ambiguous near duplicate | Không ép classifier đoán |
| Provenance preservation | Hai uploader/version/tenant cases | Không mất submission lineage |
| Cross-tenant leakage | Cross-tenant duplicate cases | Hard gate = 0 existence/content leak |

Metric phải báo riêng theo `duplicate_class`, `security_class`, modality và expected resolution. Một micro-F1 chung sẽ che mất lỗi false merge hoặc poisoned promotion.

## 7. Round E0.5 đề xuất

1. Human-review 26 pair labels và freeze dev subset; giữ hidden final split trước khi tune.
2. Ánh xạ F01..F10 vào pair IDs, thêm annotation/URL/Unicode/whitespace/container fixtures còn thiếu.
3. Chạy deterministic baselines: raw SHA-256, canonical page/text hash và structural inventory.
4. So shingle/MinHash hoặc SimHash cho candidate generation; không dùng score này làm auto-publish.
5. Chạy BGE-M3 chỉ như một ablation cho candidate recall, trong quarantine và không nối serving index.
6. Tạo aligned delta report giữa text layer, OCR output, rendered image và metadata.
7. Tune threshold trên dev, khóa threshold, rồi mới đo hidden split.

## 8. Giới hạn

- Chỉ có 10 PDF một trang, template đơn giản; chưa đại diện slide nhiều cột, scan nhiễu, bảng/công thức hoặc PDF hỏng.
- Marker là synthetic token để đo observability, không phải corpus prompt-injection thực tế.
- Chưa chạy OCR nên F09/F10 mới chứng minh coverage gap, chưa chứng minh OCR detector xử lý đúng.
- SequenceMatcher/dHash là baseline chẩn đoán; chưa đo precision/recall/F1.
- Visual QA một người không biến labels thành gold.
- Không có runtime ingestion, authorization enforcement hoặc security certification trong vòng này.
