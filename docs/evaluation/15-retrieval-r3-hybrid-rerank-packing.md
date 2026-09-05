# R3: BM25, RRF, BGE reranker và context packing

Ngày chạy: 2026-09-05. **Đã chạy retrieval/reranking/packing local; chưa chạy generation, agent, citation hoặc hallucination evaluation.** R3 dùng nguyên corpus, structure-aware chunks, vectors và evaluator của [R2 BGE-M3](14-dense-retrieval-r2-bge-m3.md).

## Phép thử và chống rò nhãn

R3 không đổi chunk boundary, embedding hoặc qrels. BM25/RRF tạo ranking mà không nhận evidence map. Reranker nhận query + passage của candidate pool, không nhận locator/claim/group. Ba packer chỉ nhận ranking, query, text và source section/adjacency.

Bảy manual dependencies có `runtime_ready=false` và `automatically_follow=false`; chúng chỉ được mở sau cùng để chấm liệu policy source-only có tình cờ lấy đủ target hay không. Không policy nào được phép lookup `from_group → to_group`.

## Stage I0/I2 — BM25 và RRF

BM25 baseline dùng Unicode NFKC + casefold + alphanumeric runs, không Vietnamese word segmentation, stemming hoặc stopwords; Okapi `k1=1,2`, `b=0,75`. RRF dùng `k=60`, không cộng raw cosine với BM25 score, và báo cả prefetch depth 20/40/80 thay vì chọn depth thắng trên 10 dev queries.

| Stage | Group recall @5 | All-evidence @5 | Group recall @10 | All-evidence @10 | All-evidence @20 |
|---|---:|---:|---:|---:|---:|
| Dense BGE-M3 R2 | 84% | 80% | 88% | 80% | 100% |
| BM25 | 88% | 80% | 92% | 90% | 90% |
| RRF depth 20 | 88% | 80% | 92% | 90% | 90% |
| RRF depth 40 | 88% | 80% | 92% | 90% | 90% |
| RRF depth 80 | 88% | 80% | 92% | 90% | 90% |

BM25 cứu một số exact terms ở @10 nhưng mất evidence Mảng của ACA-008 ngoài top 20. RRF không tự động thắng: definition chunk Mảng từ dense rank 17 thành RRF rank 29/38/27 ở depth 20/40/80. Dù vậy, candidate pool 40 và 80 vẫn chứa đủ 25/25 groups; failure nằm ở ordering, chưa phải candidate-generation ceiling. Pool 20 chỉ chứa 23/25 groups.

## Stage I3 — BGE reranker

Dùng `BAAI/bge-reranker-v2-m3` revision `953dc6f6f85a1b2dbfca4c34a2796e7dde08d41e`, model card mô tả reranker multilingual nhận trực tiếp query–passage và xuất relevance score. [Upstream model card](https://huggingface.co/BAAI/bge-reranker-v2-m3).

Máy pilot 8 GB/no GPU khiến F32 800-pair run ước tính khoảng 30 phút. Run hợp lệ dùng dynamic int8 cho Linear weights từ đúng upstream F32 checksum; không lưu derived weights, batch 4, max pair 512. 800 pairs mất 593,579 giây; pair dài nhất 501 token, không truncation.

| Candidate pool | Group recall @3 | All-evidence @3 | Group recall @5 | All-evidence @5 |
|---:|---:|---:|---:|---:|
| 20 | 88% | 80% | 92% | 90% |
| 40 | 96% | 90% | 100% | 100% |
| 80 | 96% | 90% | 100% | 100% |

Pool 20 không thể cứu ACA-008 vì chunk Mảng đứng ngoài pool. Pool 40/80 đưa:

- ACA-007 Stack–Queue: qrel ranks từ dense `6,14` thành reranker `1,3`.
- ACA-008 Mảng–DSLK: qrel ranks từ dense `17,1` thành reranker `3,1`.

Đây là tín hiệu tốt cho cross-encoder, chưa phải chọn winner. Dynamic-int8 có batch-shape sensitivity: cùng pair khi nằm trong batch 4 và khi chạy riêng lệch raw logit 0,03069. Candidate order/batching đã freeze và audit tái tính metrics từ scores đã lưu, nhưng cần chạy F32 hoặc quantization backend ổn định trước khi dùng threshold/margin production.

## Stage X — đóng packet theo token budget

Giữ cố định `reranker_pool_40`. Packer không split chunk; token budget đếm lại trên text đã join bằng tokenizer BGE-M3. Nếu chunk tiếp theo vượt cap, nó bị skip và packer thử candidate sau, nên đây là budget thật chứ không phải top-K đổi tên.

| Policy | 1.024: groups/cases | 2.048: groups/cases | 4.096: groups/cases |
|---|---:|---:|---:|
| X0 child-only | 24/25 · 9/10 | 25/25 · 10/10 | 25/25 · 10/10 |
| X1 section-lead | 24/25 · 9/10 | 25/25 · 10/10 | 25/25 · 10/10 |
| X2 cue-neighbors | 24/25 · 9/10 | 25/25 · 10/10 | 25/25 · 10/10 |

Ở budget 1.024, ACA-009 thiếu qrel chunk “đánh giá thuật toán” dù nó ở reranker rank 5: bốn chunk trước đã gần đầy packet. Đây là minh họa trực tiếp rằng `top-5 đủ` không đồng nghĩa `context budget đủ`. Với run này, 2.048 là mức nhỏ nhất trong grid giữ đủ 10/10, nhưng chưa phải SLA vì evaluator chỉ có 10 dev queries.

Expansion không tăng QA completeness so với child-only ở cùng budget. Nó còn thay thế một số ranked children bằng context bổ sung, nên không thể mặc định “thêm parent luôn tốt”.

## Dependency diagnostic

Một trong bảy dependencies dựa vào ảnh và không eligible cho text-path; không được tính như đã hiểu ảnh. Trên sáu dependency text-path:

| Policy | Covered | Thay đổi so với X0 |
|---|---:|---|
| X0 child-only | 4/6 | baseline; bốn quan hệ đã cùng chunk |
| X1 section-lead | 5/6 | cứu `dep-02` POP → khai báo |
| X2 cue-neighbors | 4/6 | không cứu thêm |

`dep-03` (dinhtri → giới hạn chương trình) vẫn thiếu với cả X1/X2. Visual `dep-07` vẫn unsupported. Vì vậy chưa được gọi X1/X2 là dependency resolver và chưa bật chúng trong runtime.

## Audit và quyết định

Audit đạt 71/71 checks, 2 guards, không failure; có một warning batch-shape int8 như trên. Các checks phủ hash chain corpus → hybrid → reranker → packet, implementation/config hashes, candidate conservation, reranker score order, metric recomputation, packet token budget, duplicate/empty-text guards và visual/dependency restrictions.

Output local: [hybrid](../../data/processed/voer-dsa-retrieval-r3-v0.1/hybrid-results.json), [reranker](../../data/processed/voer-dsa-retrieval-r3-v0.1/reranker-results.json), [packing](../../data/processed/voer-dsa-retrieval-r3-v0.1/packing-results.json), [validation](../../data/processed/voer-dsa-retrieval-r3-v0.1/validation.json). [Cách tái hiện](../../ai-core/experiments/retrieval-r3/README.md).

Giữ BGE-M3 dense + BM25/RRF + BGE reranker làm **candidate stack để tiếp tục**, không production winner. Bước kế tiếp nên:

1. kiểm tra F32 hoặc quantization ổn định trên frozen subset, rồi mới tin score margin;
2. thêm group-aware diversity/coverage gate để comparison không phụ thuộc may mắn của top-K;
3. thiết kế runtime dependency resolver từ source cues/structure thay vì manual edge lookup, tập trung `dep-03`;
4. mở visual path riêng cho `dep-07`;
5. mở rộng và human-review dev/test trước khi tune pool 40 hoặc packet 2.048.

Không dùng 100%@5 để gọi agent accuracy, chống hallucination hoặc đạt KPI ≥80%; đây vẫn là 10 câu assistant-silver trên một course snapshot.
