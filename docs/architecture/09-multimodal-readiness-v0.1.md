# WP-02 — Multimodal ingestion/OCR readiness v0.1

2026-09-06. **Technical decision draft, không phải parser đã được chọn hoặc pipeline đã chạy.** Đầu vào là WP-03 inventory/scorer specification và PDF audit hiện có. Chỉ local reinspection; không nhập nguồn mới, chạy OCR/VLM hoặc production index.

## 1. Kết luận cho phiên bản đầu

Chưa đưa PDF pilot vào chunker/index hàng loạt. Readiness phải kiểm **theo vùng và bằng chứng câu hỏi cần**, không chỉ theo trang/file. Text đầy trang vẫn có thể thiếu screenshot, vector chart, glyph, đơn vị hoặc một nửa bảng.

Giữ đường text có cấu trúc cho nguồn đã đủ quyền và kiểm tra fidelity; vùng visual/scan/formula chưa đáp ứng phải có trạng thái thiếu/uncertain. Có thể trả phần kiến thức được hỗ trợ, nhưng không kết luận claim phụ thuộc vùng chưa hiểu. Đề xuất giữ phạm vi đầu hẹp là cách triển khai về sau, **không là source promotion hoặc product GO**.

Quyết định phương án 2 ở [ARCH-02](08-controlled-workflow-decision-v0.1.md) vẫn giữ: OCR, layout và evidence checks không đòi hỏi thêm các agents tự chủ. Workflow sản phẩm triển khai chi tiết chờ ASTRA-01; tài liệu này chỉ là readiness/measurement design.

## 2. Hai điều kiện độc lập: được dùng và đọc đủ

- **Authority:** backend kiểm source/version/principal/action/purpose/revision. Assigned local quarantine inspection khác learner retrieval/model use; inspection không cho publish hoặc training.
- **Technical sufficiency:** source text/render/OCR/structure có giữ evidence bắt buộc và locator không? Parse thành công không nghĩa đủ bằng chứng trả lời.

Nguồn hiện tại: 17 PDF / 236 physical pages theo audit cũ, tất cả quarantine/rights pending. Không có verified scan/handwriting corpus hoặc reviewed OCR transcripts. Six-page reinspection mới không đổi quyền hoặc silver labels. VOER text cũng giữ riêng restrictions của snapshot, không áp license sang PDF trường.

## 3. Decision table theo loại nội dung

Đây là hướng xử lý dự kiến và điều kiện probe, không phải kết quả parser comparison. Actual adapters/models/thresholds chưa chọn.

| Loại / dấu hiệu để kiểm tra | Evidence cần giữ | Khi chưa đủ | Điều cần đo trước chấp nhận |
|---|---|---|---|
| Born-digital prose đơn giản | Heading path, paragraph order, list/code/negation/units, exact locators | Flag các vùng glyph/layout lỗi; không sửa source bằng đoán | P-02/P-04/P-05, CI-01, CU-04 |
| Handout 2-up/4-up | Physical page + logical slide regions/printed labels; từng slide đọc trọn | Chưa tách layout đúng thì không ghép cả trang thành semantic child hoàn chỉnh | SP01/02, order pairs và cross-section cut |
| Mixed text + screenshot/raster legend | Text và image gốc, glyph-label/callout relations | Native text nonempty không miễn OCR/visual review vùng ảnh | SP03, P-07, required-region availability |
| Vector chart | Full axes/ticks/curves/legend/units, không chỉ embedded images | Không trả numeric/spatial claim từ danh sách tokens nếu geometry thiếu | SP11, P-05/P-07/K-08, chart+unit groups |
| Table / cross-page row | Cell/header identity, blank/?/zero, continuation theo cột, đủ hai locators | Không nối hai bảng khác nhau; không điền ô bài tập | SP04..08, cell/edge precision-recall, false fill count |
| Formula/math | Dấu, chỉ số, phân số, điều kiện và formula↔figure binding | OCR/LaTeX chưa reviewed giữ uncertain; exact text không đảm bảo math-equivalence | SP09/10, symbol errors + semantic critical errors |
| Scan/mixed scan | Render gốc + local OCR transcript aligned theo region khi được cấp phép | Không có text không là trang trắng; chưa OCR là chưa đọc | CER/WER trên reviewed transcript, missing region count |
| Handwriting/blur/rotation/occlusion | Image provenance, legibility annotation và unresolved portions | Unsupported/pending review, không hallucinate chỗ mờ | Slice riêng, không suy từ printed-text score |
| Text layer khác hình / hidden/off-page text | Giữ riêng representations và mismatch flags/locators | Không tự chọn native/OCR/description làm chân lý; giữ restricted inspection | CU-05/CR-02, mismatch detection và false positives |
| Active content/encrypted/known secret/bomb | Minimal quarantine/security record, không generic parse | Stop hoặc workflow chuyên biệt có authority; không cố decode bằng provider | UPL-02/03, resource and sink boundary checks |

Heuristics (ít chữ, nhiều images/vectors, OCR confidence) chỉ chọn vùng cần kiểm tra. Không là calibrated correctness, permission hoặc declaration toàn file sạch. Repeated logo không là critical figure; ít embedded images không nghĩa không có biểu đồ.

## 4. Những gì phải đi cùng chunk và index về sau

Giữ immutable source bytes/hash/version; physical page khác printed label; region geometry phải có coordinate origin/units/page box/rotation. OCR/render/transcript/model description là representations khác nhau có method/version/lineage. Generated description có thể là auxiliary retrieval hint nhưng không thay nguồn citation hoặc tự là observed fact.

Text/figure/table/formula child phải nối đến context bắt buộc bằng evidence-backed relations: heading/units, caption, row continuation, assumptions. Không suy adjacency hoặc semantic similarity là dependency đã chắc. Giữ uncertain links và scope từng target; không hydrate target bị deny để “cứu context”.

Readiness không là một cờ `pdf_ready` chung: có thể đủ text nhưng thiếu critical image, đủ hình nhưng chưa đọc semantics, đủ kỹ thuật nhưng thiếu quyền. Required evidence bị thiếu ở bất kỳ bước nào phải được phản ánh trong post-pack score/giới hạn đáp án. Các schema chi tiết theo [content-unit contract](07-content-unit-index-contract-v0.1.md), không freeze runtime fields ở đây.

## 5. Local-only và ranh giới inspection

Theo [upload clarification](../governance/05-secure-upload-quarantine-deduplication-v0.1.md), future inspector phải có exact assignment, no network/tools/egress, restricted output sink, time/memory/page/pixel limits và current classification check. Một unknown scan có thể cần OCR local trong inspection lane khi được cấp đúng quyền; known secret/active exploit/resource bomb không được generic OCR. Đây là yêu cầu thiết kế, **sandbox thực thi chưa được cài/chứng nhận trong repo**.

Không gửi quarantine PDF/crop/transcript tới external OCR/VLM mặc định. Muốn dùng external processor phải có quyết định riêng về rights, dữ liệu được phép, retention, region và egress; việc mua API hoặc detector báo clean không thay quyền đó. Không tải/chấp nhận terms của gated scan datasets trong lượt này.

## 6. Reinspection mới và giới hạn

[Inspection record](../evaluation/wp02-inspection-record-v0.1.json) pin source/render SHA, exact physical pages, Poppler 26.07.0, 120 DPI. Đã xem full page: db-table-p002, er-p004, micro-p032/033, syllabus-p003/004 (6 trang, 4 PDFs). Quan sát trực quan phục vụ design: handout 4-up, glyph-label legend, chart/unit linkage, blank/question-mark cells và row continuation cùng separate table. Không chấm lại QA answers hoặc boxes.

Poppler báo thiếu display font Symbol/ArialUnicode ở các lượt HCMUAF và syllabus nhưng exit 0. Các vùng được xem đọc được cho mục đích bố cục; **không chứng nhận mọi glyph hoặc renderer fidelity**. Không chạy đối chứng renderer mới; ghi warning vào record, giữ mismatch review mở. Counts lịch sử 13 pages inspected không được tăng thành 19 unique pages vì sáu trang này nằm trong mẫu đã có.

## 7. Đủ để làm gì tiếp?

Đã có decision table, source restrictions, local counterexamples và [probe protocol](../evaluation/33-multimodal-probe-protocol-v0.1.md). Đủ technical draft để người dùng review và chuẩn bị các phần được phép của WP-04; **chưa parser/OCR winner, reviewed labels hoặc production readiness**.

Trước model/OCR evaluation rộng hơn phải có rights và corpus/labels đủ điều kiện; trước implementation-grade workflow/product code vẫn phải báo ASTRA-01 và chờ review + explicit GO. Không có lý do mở thêm hàng trăm PDF để thay việc xử lý các gaps đã xác định.
