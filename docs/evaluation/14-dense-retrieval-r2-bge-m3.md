# R2 dense retrieval: BGE-M3 trên structure-aware chunks

Ngày chạy: 2026-09-05. **Đã chạy embedding/index/retrieval local; chưa chạy BM25, reranker, context packing, generation hoặc agent.** Baseline tiếp nối [R1 boundary comparison](13-chunking-boundary-r1.md).

## Bài toán đo

R1 chỉ trả lời “boundary có cắt cấu trúc hay không”. R2 hỏi câu khác: với một query tiếng Việt, dense retriever có lấy đủ các mảnh evidence cần thiết trước khi agent được phép trả lời hay không?

Không index riêng 4 module của R1 vì bộ qrels trải trên 10 tài liệu. Corpus R2 dùng đủ 16 module cùng snapshot: 10 tài liệu chứa qrel và 6 tài liệu in-snapshot làm distractor. Nếu bỏ các tài liệu qrel khỏi index thì Recall sai ngay từ mẫu số; nếu bỏ distractor thì bài toán lại dễ giả tạo.

Qrels vẫn là assistant-silver, chưa có giáo viên adjudicate. Vì vậy mọi điểm bên dưới là retrieval diagnostic trên dev, không phải độ chính xác học thuật hay KPI nghiệm thu.

## Pipeline đã chạy

1. Kiểm tra checksum source và structural representation của 16/16 module.
2. Áp dụng nguyên thuật toán `structure-512-o0`: source-order atoms, flush khi đổi section, cap 512 token gồm special tokens, overlap=0.
3. Tạo 217 chunks. Trước embedding, loại markup bằng projection `voer-html-regex-space-v1` trong từng boundary; 216 chunks có text, tối đa 469 token. Một chunk của tài liệu Mảng chỉ chứa hình nên text rỗng và bị loại có ghi nhận.
4. Căn 22 locator legacy → raw HTML envelope → leaf elements → chunk IDs. 22/22 locator và 25/25 required groups đều ánh xạ được; annotations không tham gia tạo boundary hoặc embedding.
5. Encode local bằng upstream ONNX float32 của `BAAI/bge-m3`, revision `5617a9f61b028005a4858fdac845db406aefb181`: 1.024 chiều, upstream sentence embedding/CLS pooling, L2 normalize, không instruction, không fine-tune.
6. Exact cosine search bằng dot product; không ANN/vector database. Đánh giá ở K = 1, 3, 5, 10, 20.
7. Lưu vectors rồi audit đọc lại, tự tính ranking và metrics từ đầu.

Config đầy đủ và model checksums nằm tại [config v0.1](../../ai-core/experiments/dense-retrieval-r2/config-v0.1.json). Model/corpus không được upload ra dịch vụ ngoài.

## Định nghĩa metric

- **Evidence-group recall@K**: tỷ lệ required groups có ít nhất một alternative được lấy đủ trong top K. Đây là primary retrieval diagnostic.
- **All-evidence success@K**: tỷ lệ câu có đủ mọi required group trong top K. Metric này bắt lỗi câu so sánh lấy được một vế nhưng thiếu vế còn lại.
- **Macro qrel-chunk recall@K**: trung bình mỗi câu về tỷ lệ direct qrel chunks xuất hiện trong top K. Với alternatives, relevance nhị phân dùng hợp của qrel chunks nên chỉ là secondary diagnostic.
- **Any-evidence hit@K/MRR/nDCG**: đo việc tìm thấy ít nhất một evidence sớm, nhưng không thay thế completeness. MRR có thể cao dù câu so sánh vẫn thiếu một vế.

## Kết quả aggregate

| K | Groups hit | Evidence-group recall | Cases đủ evidence | All-evidence success | Any hit | Macro chunk recall | Mean binary nDCG |
|---:|---:|---:|---:|---:|---:|---:|---:|
| 1 | 19/25 | 76% | 6/10 | 60% | 90% | 75% | 0,9000 |
| 3 | 20/25 | 80% | 7/10 | 70% | 90% | 80% | 0,8226 |
| 5 | 21/25 | 84% | 8/10 | 80% | 90% | 85% | 0,8463 |
| 10 | 22/25 | 88% | 8/10 | 80% | 100% | 90% | 0,8682 |
| 20 | 25/25 | 100% | 10/10 | 100% | 100% | 100% | 0,8986 |

MRR của direct qrel chunk đầu tiên là 0,9167. Con số này cao vì 9/10 câu có ít nhất một evidence ở rank 1; nó che khuất việc hai câu comparison vẫn thiếu evidence còn lại đến rank 14 hoặc 17.

## Kết quả từng tình huống

`Qrel ranks` là thứ hạng của các direct chunks cần cho câu. Một tài liệu có thể chứa nhiều evidence groups trong cùng chunk, nên số qrel chunks không bằng số groups.

| Case | Qrel ranks | Groups @5 | Đủ evidence @5 | Đủ evidence @10 | Đủ evidence @20 |
|---|---|---:|:---:|:---:|:---:|
| ACA-001 Stack/LIFO/Push/Pop | 1 | 3/3 | ✓ | ✓ | ✓ |
| ACA-002 Queue/FIFO/front/rear | 1 | 3/3 | ✓ | ✓ | ✓ |
| ACA-003 phần tử DSLK đơn | 1 | 2/2 | ✓ | ✓ | ✓ |
| ACA-004 bậc nút/cây | 1 | 2/2 | ✓ | ✓ | ✓ |
| ACA-005 cấu trúc dữ liệu và hiệu quả | 1 | 2/2 | ✓ | ✓ | ✓ |
| ACA-006 queue mảng bị tràn/cách sửa | 1 | 3/3 | ✓ | ✓ | ✓ |
| ACA-007 so sánh Stack–Queue | 6, 14 | 0/2 | ✗ | ✗ | ✓ |
| ACA-008 so sánh Mảng–DSLK | 1, 17 | 1/3 | ✗ | ✗ | ✓ |
| ACA-009 bắt đầu bài toán/đánh giá thuật toán | 1, 5 | 3/3 | ✓ | ✓ | ✓ |
| ACA-010 DSLK đơn–vòng | 1, 2 | 2/2 | ✓ | ✓ | ✓ |

Hai failure quan trọng:

- **ACA-007:** dense xếp các chunk cùng chủ đề Stack/Queue ở top đầu, nhưng definition chunks thật nằm rank 6 và 14. Nếu context cap dừng ở 5 hoặc 10, router phải trả `insufficient_evidence`; lấy một vế rồi tự suy ra vế kia sẽ vi phạm guard của SIM-03.
- **ACA-008:** evidence DSLK ở rank 1 nhưng evidence định nghĩa Mảng ở rank 17; nhiều bài thực hành/mô tả mảng khác chen vào trước. Đây là lỗi evidence completeness, không phải “không biết chủ đề”.

ACA-009 và ACA-010 cho thấy multi-source không luôn thất bại: hai vế ở rank 1/5 và 1/2. Vì vậy không nên gắn rule cứng “comparison luôn lấy top 20”; cần cải thiện retrieval/reranking và kiểm chứng đủ group trước answer.

## Hiệu năng và tính hợp lệ

Trên máy CPU 4 threads, batch 1: load session 5,137 giây; encode 216 chunks 192,932 giây; 10 queries 1,392 giây. Vectors 1.024 chiều được L2-normalize; deterministic probe delta 0.

Audit đạt 18/18 checks và 3 guards: config/corpus/vector hashes, ID order, shapes, finite/unit norm, exact rank/score recomputation, metric/per-case recomputation và guard qrel completeness. [Cách tái hiện](../../ai-core/experiments/dense-retrieval-r2/README.md).

Output local theo data policy: [corpus](../../data/processed/voer-dsa-dense-r2-v0.1/corpus.json), [results + top 20 từng query](../../data/processed/voer-dsa-dense-r2-v0.1/results.json), [vectors](../../data/processed/voer-dsa-dense-r2-v0.1/vectors.npz), [validation](../../data/processed/voer-dsa-dense-r2-v0.1/validation.json). Chúng không được push lên public remote.

## Quyết định và bước kế

BGE-M3 dense được giữ làm baseline đầu tiên, không gọi là winner. `K=20` đạt đủ evidence trên 216 chunks nhưng quá rộng để xem là context policy hợp lý; nó tăng chi phí và nguy cơ đưa nhiễu vào generation.

Vòng tiếp theo nên giữ nguyên corpus/chunks/qrels rồi thêm **BM25 → RRF với dense → evidence/dependency-aware expansion → reranker**, báo ablation sau từng lớp. Success criterion gần nhất là kéo cả hai qrel chunks của ACA-007/008 vào top 5 hoặc top 10 mà không làm giảm các case hiện đã đúng. Chưa đưa ảnh vào dense text index: chunk hình rỗng là một tín hiệu rõ để mở visual retrieval track riêng, không OCR/VLM ngầm.

Không dùng 80%@5 làm “độ chính xác agent”, không tuyên bố chống hallucination và không tune trực tiếp theo 10 câu silver này đến khi có dev/test tách biệt và review người dạy.
