# Đánh giá PDF có hình và multimodal retrieval v0.1

Ngày: 2026-09-04. Đây là protocol và seed silver, **không phải kết quả benchmark**.

Cập nhật: đã có [parser diagnostic vòng 0](07-parser-diagnostic-round0.md) trên 13 trang, đối chiếu extraction mặc định với vùng được cung cấp sẵn. Đây là khảo sát lỗi cục bộ, chưa phải kết quả các run V0-V4 bên dưới.

## 1. Tách bốn bài toán

1. **Parsing/layout:** có giữ đúng thông tin và quan hệ của nguồn không?
2. **Retrieval:** query có tìm đủ evidence trang/region không?
3. **Reading/reasoning:** đưa sẵn đúng evidence thì model có hiểu không?
4. **Grounded answer/citation/policy:** trả lời đúng, cite đúng, không bịa nội dung hay vượt quyền?

Chạy oracle-evidence reading trước end-to-end để phân biệt model không đọc được biểu đồ với retriever không tìm được biểu đồ. RAGAS text-only không chứng minh hệ thống hiểu hình; không lấy điểm RAGAS làm accuracy tổng.

## 2. Seed hiện có

- [page-audit.json](../../data/evaluation/silver/vn-pdf-visual-v0.1/page-audit.json): 13 trang đã xem bằng mắt bởi assistant, ghi layout/region/expectations.
- [visual-qa.json](../../data/evaluation/silver/vn-pdf-visual-v0.1/visual-qa.json): 8 case nháp có page/region references, expected observations, forbidden claims và negative conditions.
- Toàn bộ là `silver_draft`, `split=dev`, không có teacher/human adjudication, không dùng nghiệm thu 80%.
- Case định vị bbox là annotation điều hướng xấp xỉ, không dùng làm gold pixel IoU. Expected answers là assistant-derived drafts, chưa là đáp án học thuật đã duyệt.
- Dữ liệu dẫn xuất kế thừa hạn chế nguồn. Seed chỉ phục vụ review/audit cục bộ; chưa cấp quyền chạy production/public benchmark trên PDF này.

## 3. Mở bộ parser truth set có chủ đích

Đề xuất khoảng 30 trang, sau rights review. Đảm bảo có: 1-up/2-up/4-up, vector chart, diagram, screenshot, prose dài, scan, formula, bảng và row nối trang. Có thể một trang thuộc nhiều slice. Không giả tạo scan rồi gọi là scan thực; synthetic degradation phải có nhãn riêng và cùng split với nguồn gốc.

Reviewer ghi:

- Regions và đúng reading order, section boundaries, printed slide label.
- Bảng: row/column/header, merged cells, blank cell và continuation edges.
- Figure: crop có đủ axis/legend/caption, link caption, phần nào thiếu.
- Formula: transcript kiểm tra dấu/subscript, không chỉ string được OCR.
- Text transcription cho sample scan/native khó để tính CER/WER.

Không dùng output của parser đang được chấm làm gold. Assistant có thể pre-label; người review sửa, ghi conflict/adjudication và version mới.

## 4. Local visual QA set mở rộng

Đề xuất 60 case sau review: 12 bảng/đơn vị, 12 đồ thị, 10 sơ đồ ER/flowchart, 8 formula, 8 handout/cross-page, 10 thiếu evidence/mờ/sai tiền đề. Đó là quota thiết kế, chưa được tạo.

Giữ một held-out source family khi corpus đủ đa dạng; hiện microeconomics chỉ một file, **chưa đủ** để claim cross-source generalization. Không random-split các crop/chunk cùng tài liệu. Group theo tác giả/course series và gần-trùng; toàn bộ 8 seed hiện là dev, không tái dùng làm test kín.

Mỗi QA phải có:

- Scope và câu hỏi nêu được môn/tài liệu cần dùng.
- `answerability`, `required_claims`, `forbidden_claims`.
- Một hoặc nhiều `evidence_groups`, mỗi group có locator alternatives; OR trong group, AND giữa groups.
- `requires_visual`, `requires_neighbor`, `evidence_state`.
- `provenance`, `review_status`, `split`, `source_rights_status`.

Có distractors gần nghĩa: cùng tên hình ở chương khác, biểu đồ khác đơn vị, khác phiên bản slide. Kiểm tra false premise: “đường đã vẽ ở chỗ dấu hỏi” không được trả lời như có thật.

## 5. Controlled experiments

| Run | Retrieval representation | Evidence đưa generator | Mục đích |
|---|---|---|---|
| V0 | Text SHCC + BM25/dense | Text only | Baseline mức mất mát thị giác |
| V1 | Như V0 | Text + visual nguồn của hits | Tách hiệu quả đọc hình khỏi retrieval |
| V2 | Text + OCR/caption auxiliary | Text + visual nguồn của hits | Đo enrichment retrieval; logging caption errors |
| V3 | Visual-only candidate | Same permitted evidence pack | Đo lợi ích và nhược điểm visual retriever |
| V4 | Text/visual fusion, group dedup | Same permitted evidence pack | Challenger hybrid |
| Oracle | Qrels reviewed, không retrieval | Đúng evidence text + ảnh | Trần reading/answering của generator |

Giữ generator/model revision/prompt, source snapshot, permission scope và packing policy cố định. V2 phải tách thêm OCR-only với generated-description khi đủ dữ liệu; không thay mọi thành phần cùng lúc.

Top-k chunk không tương đương top-k page/crop. So sánh ở **candidate group chung** và báo cả context budget thực (text tokens, số ảnh, pixel, image tokens/cost nếu có). Chạy cùng budget grids; không để nhánh vision thắng vì được cấp nhiều evidence hơn. Case source-specific vẫn search corpus có distractors; document restriction chỉ từ scope user/backend, không lấy doc ID đáp án để làm phép thử dễ giả tạo.

## 6. Metrics định nghĩa rõ

### Parsing/layout

- Page identity/count, silent-drop count.
- Reading-order pair accuracy trong regions và giữa logical slides (các cặp có thứ tự được reviewer xác nhận).
- Region/heading detection precision-recall; `bbox IoU` chỉ sau gold bbox review.
- Table header retention, cell accuracy, continuation-edge accuracy; blank-cell hallucination count.
- Figure-caption association và critical-visual preservation trên annotated visual objects, không trên số embedded images.
- OCR CER/WER trên transcript reviewed, không trên mọi trang thiếu reference.
- Formula symbol/sign accuracy và số lỗi làm thay đổi nghĩa.

### Retrieval

- **Group Recall@k:** trung bình trên query answerable của tỷ lệ evidence groups có ít nhất một locator alternative được top-k hỗ trợ.
- **All-evidence Success@k:** tỷ lệ query mà mọi required group đều được cover. Chỉ có một trang đúng chưa đủ cho câu hỏi cần đơn vị ở trang khác.
- MRR/nDCG chỉ khi qrels/relevance grades được review và entity normalization nhất quán.
- Đo lại group coverage **sau context packing**, vì retrieved đúng nhưng crop/packing loại evidence vẫn fail.
- False-evidence acceptance trên unanswerable/false-premise riêng, không cho empty-qrels thành Recall=1.

### Answer/citation

- Claim correctness; required-claim recall; unsupported-claim rate.
- Chart/table numeric accuracy với đơn vị, tolerance đặt trước theo task, không dùng tolerance để bỏ qua sai dấu/cột.
- Citation entailment và locator validity riêng: mở đúng trang chưa chắc trang hỗ trợ claim.
- Correct abstention/qualification; bịa điểm/đường/ô trống; lẫn `observed` với `derived`.
- Unauthorized visual/text/parent retrieval và object-access attempts.

### Cost

Seconds/page parse/render/embedding, index size, RAM/VRAM, build failures; query p50/p95 từng stage; tokens/pixels/ảnh và chi phí. Không ngoại suy số đo 236 trang thành SLA production.

## 7. Gates đề xuất, chưa đạt/chưa đo

- Cứng: 100% identity/locator fields; 0 silent missing pages; 0 access leak; 0 cite generated descriptions thay nguồn.
- Cấu trúc: không cắt qua hai logical slide khác section; giữ header/units/row-continuation đối với required evidence; trang không đạt phải bị flag thay vì pass im lặng.
- Trên reviewed answerable subset: Group Recall@5 mục tiêu ≥90%, @10 ≥95%, All-evidence Success@10 ≥85%. Báo từng slice và mẫu số; không chỉ số tổng.
- Critical negative cases: không bịa hình/ô trống; không tự khẳng định thông tin khó đọc. Zero failures trên tập nhỏ không chứng minh tỷ lệ lỗi thật bằng 0.
- Chọn winner bằng paired per-query differences; bootstrap theo document/source family khi đủ cụm. Nếu chênh lệch không ổn định thì giữ phương án đơn giản/ít tốn tài nguyên hơn.

## 8. Benchmark công khai để tham khảo

- [ColPali / ViDoRe](https://arxiv.org/abs/2407.01449): page-level visual retrieval; dùng cách lập qrels/đo retrieval, không dùng score của paper làm KPI tiếng Việt.
- [ViDoRAG / ViDoSeek của Alibaba-NLP](https://github.com/Alibaba-NLP/ViDoRAG): query, reference answer, reference pages hữu ích cho thiết kế retrieval-reading-answer. Chưa tải/chạy benchmark này.
- [Docling enrichment](https://docling-project.github.io/docling/usage/enrichments/): candidate xử lý picture/formula; không phải dataset gold.

Chưa chọn model chiến thắng. Ưu tiên benchmark địa phương phản ánh chính handout, đồ thị và bảng đã thấy.
