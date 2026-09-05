# R4: ổn định reranker, coverage câu so sánh và code-prologue context

Ngày chạy: 2026-09-05. **Đã chạy ba diagnostic local; chưa chạy generation, citation validation, agent workflow hoặc hallucination evaluation.** R4 giữ nguyên 16 tài liệu, 216 text chunks, 10 câu/25 evidence groups assistant-silver của R2 và các artifact R3.

## Câu hỏi của R4

1. Warning `0,03069` ở R3 là nhiễu lặp lại hay là batch-shape sensitivity thật, và F32 có cùng vấn đề không?
2. Với câu so sánh, có thể ép candidate packet đại diện cả hai vế mà không dùng qrels ở runtime không?
3. Có source-only rule nào nối thân hàm code về phần khai báo/giới hạn chương trình để cứu `dep-03` không?

Mỗi phép thử ghi artifact riêng. R4 không sửa config hoặc kết quả R3, không upload nguồn/model input ra ngoài, và không dùng manual dependency edge để điều khiển expansion.

## S1 — frozen stability probe

Probe lấy đúng 8 candidate RRF-depth-80 đầu tiên của mỗi query, tổng 80 query–passage pairs. Selection hoàn tất mà không đọc qrels. Cùng upstream `BAAI/bge-reranker-v2-m3` revision đã pin được chạy ở F32 và dynamic-int8, batch 1 và batch 4; không pair nào vượt 512 token.

| So sánh | Mean abs logit delta | Max abs logit delta | Top-1 giống nhau | Top-3 overlap | Pairwise inversions |
|---|---:|---:|---:|---:|---:|
| F32 batch 1 ↔ 4 | 0,0000023 | 0,0000153 | 10/10 | 100% | 0 |
| int8 batch 1 ↔ 4 | 0,2845 | 1,0836 | 10/10 | 86,7% | 19 |
| F32 ↔ int8, batch 1 | 0,4761 | 1,6740 | 10/10 | 80,0% | 20 |
| F32 ↔ int8, batch 4 | 0,4242 | 1,4448 | 10/10 | 90,0% | 21 |

Lặp lại cùng bốn pair, cùng batch 4 cho delta bằng 0 ở cả F32 và int8. Vì vậy finding R3 không phải nondeterminism ngẫu nhiên; nó chủ yếu xuất hiện khi padding/batch shape thay đổi trong dynamic-int8 backend này.

Thời gian 80 pair trên CPU pilot: F32 batch 1 `152,551s`, F32 batch 4 `225,527s`, int8 batch 1 `123,706s`, int8 batch 4 `88,250s`. Batch 4 không mặc định nhanh hơn với F32 trên các độ dài không đều của probe này.

Quyết định: chưa đặt relevance threshold/margin từ raw int8 score. R3 int8 chỉ còn phù hợp với diagnostic ranking khi candidate order và batch policy được cố định. Trước runtime cần benchmark lại F32 hoặc một quantization backend ổn định trên corpus lớn hơn; top-1 10/10 không đủ để xóa finding.

## C1 — comparison decomposition và coverage gate

Parser R4 cố ý hẹp: chỉ nhận mẫu `so sánh <quan hệ> của A và B`, NFKC/casefold, bỏ suffix `theo tài liệu`. Hai câu được tách mà không dùng labels:

| Case | Quan hệ | Nhánh trái | Nhánh phải |
|---|---|---|---|
| ACA-007 | thứ tự lấy phần tử | stack | queue |
| ACA-008 | cách tổ chức phần tử | mảng | danh sách nối đơn |

Mỗi nhánh chạy BGE-M3 dense + BM25/RRF depth 40, lấy 20 candidate, rồi BGE reranker int8 batch 4. Merge round-robin theo branch rank, deduplicate cùng chunk và giữ provenance của mọi branch. Query không parse được phải giữ ranking gốc và báo `unsupported`, không đoán entity.

Coverage gate đạt 2/2 branch ở top 2, 5, 10 và 20 cho cả hai case. Nhưng gate chỉ biết candidate đến từ query nhánh nào; nó **không biết candidate đó có phải evidence đúng không**.

| Diagnostic trên 2 case / 5 groups | R3 nguyên câu | R4 tách nhánh |
|---|---:|---:|
| Evidence groups @1 | 2/5 | 1/5 |
| Evidence groups @3 | 5/5 | 5/5 |
| All-evidence cases @3 | 2/2 | 2/2 |
| Mean binary nDCG@3 | 0,920 | 0,847 |

Chi tiết cho thấy trade-off thay vì một winner tuyệt đối:

- ACA-007: qrels từ ranks `1,3` thành `1,2`, nDCG@3 tăng `0,920 → 1,000`.
- ACA-008: qrels từ ranks `1,3` thành `2,3`; top 1 của nhánh Mảng là passage cùng chủ đề nhưng không phải qrel, nDCG@3 giảm `0,920 → 0,693`.

Quyết định: giữ comparison route như một **coverage guard/fallback có điều kiện**, không thay ranking mặc định và không gọi nó là relevance improvement. Gate về sau phải kết hợp branch entailment/evidence validation; chỉ có hai dev case nên chưa chọn threshold.

## X3 — backward code-prologue resolver

X3 chỉ đọc text và adjacency của source: nếu retrieved anchor chứa một marker code đã khai báo, đi lùi trong cùng section tối đa hai chunks và dừng khi thấy prologue marker như `#include`, `#define`, `khai báo`, `prototype`, `chương trình` hoặc `cài đặt stack`. Không có lookup `dep-id → target`.

Hai failure được nối bằng rule chung:

- `dep-02`: chunk POP `...:004` thêm previous chunk `...:003` chứa khai báo `S`, `T`, `N`.
- `dep-03`: `dinhtri` chunk `...:012` thêm `...:011`; chunk continuation `...:013` thêm `...:012` rồi dừng ở `...:011`. Prologue nói rõ mỗi toán hạng là một ký số và liệt kê năm toán tử.

| Policy | Text dependency covered | Visual unsupported | 1.024 groups/cases | 2.048 groups/cases | 4.096 groups/cases |
|---|---:|---:|---:|---:|---:|
| R3 X0 child-only | 4/6 | 1 | 24/25 · 9/10 | 25/25 · 10/10 | 25/25 · 10/10 |
| R3 X1 section-lead | 5/6 | 1 | 24/25 · 9/10 | 25/25 · 10/10 | 25/25 · 10/10 |
| R4 X3 code-prologue | 6/6 | 1 | 24/25 · 9/10 | 25/25 · 10/10 | 25/25 · 10/10 |

X3 giải đúng hai dependency đã biết nhưng không cải thiện QA completeness và match 62/216 chunks. Con số match rộng là cảnh báo precision: R4 chưa có nhãn `wrong-context/should-not-expand` đủ mạnh để đo nối nhầm. Do đó X3 là resolver candidate, chưa bật runtime. Visual `dep-07` tiếp tục bị đánh dấu unsupported thay vì tính ngầm là pass.

Budget 1.024 vẫn thiếu ACA-009; resolver dependency không thay thế token-budget policy. Mức 2.048 tiếp tục là lower bound quan sát được trên dev run, không phải production SLA hay generation context window đã chốt.

## Audit và quyết định

Audit đạt 60/60 checks, 3 guards, không failure; status `passed_with_findings`. Checks phủ config/implementation/input hashes, frozen probe, score/rank recomputation, parser, branch pool, reranker order, merge/dedup/provenance gate, metric recomputation, packet token budget, dependency/visual separation và ba guard cases.

Output local: [stability](../../data/processed/voer-dsa-retrieval-r4-v0.1/stability-results.json), [comparison branches](../../data/processed/voer-dsa-retrieval-r4-v0.1/comparison-branches.json), [comparison results](../../data/processed/voer-dsa-retrieval-r4-v0.1/comparison-results.json), [code prologue](../../data/processed/voer-dsa-retrieval-r4-v0.1/code-prologue-results.json), [validation](../../data/processed/voer-dsa-retrieval-r4-v0.1/validation.json). [Cách tái hiện](../../ai-core/experiments/retrieval-r4/README.md).

R4 chốt bốn hướng cho vòng kế tiếp:

1. bổ sung human-reviewed negative context labels để đo precision/over-expansion của X3;
2. mở visual path riêng cho `dep-07`, giữ OCR/text và region/image evidence tách biệt;
3. mở rộng comparison cases và thêm branch-evidence validation trước khi dùng coverage gate để quyết định `answer/insufficient evidence`;
4. chỉ sau các bước trên mới freeze reranker backend/batching và mở generation + citation/faithfulness evaluation.

Không dùng 6/6 dependency, 5/5 comparison groups hoặc 10/10 packet ở 2.048 để gọi agent accuracy hay chống hallucination. Tất cả vẫn là diagnostic trên một course snapshot và assistant-silver labels.
