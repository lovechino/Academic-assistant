# BGE-M3 duplicate candidate ablation — E0.7

Ngày chạy/kiểm: 2026-09-05

Kết luận: **BGE-M3 local đạt candidate recall@1 = 18/19 và recall@3/@5 = 19/19 trên dev fixture, nhưng một unrelated shared-boilerplate pair đạt cosine 0,997499 và rank 1. Vì vậy dense similarity chỉ được dùng để sinh candidate trong quarantine; không được dùng làm ngưỡng auto-merge, kế thừa quyền hoặc publish.**

## 1. Câu hỏi đo

E0.7 trả lời ba câu hỏi hẹp:

1. BGE-M3 có tìm lại matched counterpart của 19/21 physical relations cần sinh candidate ở top 1/3/5 không?
2. Union `MinHash ∪ BGE-M3` có tăng recall đủ để bù candidate load không?
3. Dense score có tách được duplicate hợp lệ khỏi unrelated/poisoned relation để dùng làm quyết định merge không?

E0.7 không đo answer quality, RAGAS, OCR/vision, quyền truy cập, prompt-injection detection hoặc production precision.

## 2. Phạm vi và tính tái lập

- Corpus: 36 PDF synthetic/40 trang, quarantine-only.
- Relations: 21; trong đó 19 expected candidate và 2 unrelated negatives.
- Hidden test: không; đây là development ablation trên fixture đã biết.
- Model: `BAAI/bge-m3`, revision `5617a9f61b028005a4858fdac845db406aefb181`.
- Runtime: ONNX Runtime 1.29.0 CPU, 4 intra-op threads.
- Vector: CLS 1.024 chiều, L2 normalize, exact cosine in-memory.
- Input: extracted text; label và expected relation không nằm trong `embedding_text`.
- Token length quan sát: 40–171; không có truncation ở hard cap 512 trong run này.
- Không gọi mạng, không gửi file ra external OCR/VLM, không ghi serving index và không persist vector.
- Determinism probe trên cùng input: max absolute delta = 0,0.

Artifacts:

- [E0.7 compact result](../../data/evaluation/synthetic/duplicate-detection-v0.1/e07-bge-m3-duplicate-results.json);
- [local corpus preparation và runner](../../ai-core/experiments/security-fixtures/README.md);
- [E0.6 deterministic baselines](25-deterministic-dedup-baselines-e0.6.md).

## 3. So sánh candidate recall trên cùng relations

| Method | Recall@1 | Recall@3 | Recall@5 |
|---|---:|---:|---:|
| Raw SHA-256 | 0,052632 | 0,052632 | 0,052632 |
| Canonical text exact | 0,368421 | 0,368421 | 0,368421 |
| Character 5-gram Jaccard | 1,000000 | 1,000000 | 1,000000 |
| Word 3-gram Jaccard | 1,000000 | 1,000000 | 1,000000 |
| MinHash-128 char5 | 1,000000 | 1,000000 | 1,000000 |
| SimHash-64 word3 | 0,736842 | 0,789474 | 0,894737 |
| BGE-M3 dense cosine | **0,947368** | **1,000000** | **1,000000** |

Kết quả 1,0 của sparse methods không chứng minh chúng tốt hơn semantic retrieval trên production. Fixture hiện còn nhỏ, topic/template của các matched pair khá riêng, chưa có đủ cross-course hard negatives và không phải hidden set.

Miss duy nhất của BGE-M3 tại top 1 là DUP-013, một legitimate lecturer variant:

- expected counterpart: rank 2, score 0,927072;
- candidate rank 1: `F04-benign-few-character-delta.pdf`, score 0,931670.

Nếu candidate budget là 3 thì BGE-M3 không miss relation nào trong dev set hiện tại. Con số này chưa được freeze thành production budget.

## 4. MinHash union

| K mỗi retriever | Union recall | Mean union candidates | Mean overlap | Max candidates |
|---:|---:|---:|---:|---:|
| 1 | 1,000000 | 1,052632 | 0,947368 | 2 |
| 3 | 1,000000 | 4,105263 | 1,894737 | 5 |
| 5 | 1,000000 | 7,210526 | 2,789474 | 9 |

MinHash đã đạt recall 1,0 trên fixture nên union không tăng recall. So với chỉ lấy K candidate, union tăng mean candidate load khoảng 5,26% ở K=1, 36,84% ở K=3 và 44,21% ở K=5. Vì vậy chưa có bằng chứng để bật union mặc định; E0.8 phải đo incremental recall và review load trên hard-negative corpus lớn hơn.

## 5. Counterexample bác bỏ global dense threshold

| Pair | Nhãn | Dense score | Rank |
|---|---|---:|---:|
| DUP-013 | Legitimate variant, expected candidate | 0,927072 | 2 |
| DUP-015 | Unrelated same title | 0,802439 | 5 |
| DUP-016 | Unrelated shared boilerplate | **0,997499** | **1** |

Một threshold đủ thấp để giữ DUP-013 cũng nhận DUP-016. Một threshold cao để loại DUP-016 sẽ loại nhiều duplicate/variant hợp lệ. Kết quả này bác bỏ rule `dense score cao → merge` và cho thấy phải tách:

1. candidate generation;
2. evidence/classification;
3. rights, tenant và reviewer decision.

## 6. Dense similarity không phải security detector

Các poisoned relation vẫn có score rất cao: DUP-018 = 0,990255; DUP-019/020/023 = 1,0; DUP-021 = 0,986789; DUP-022 = 0,977294. Image-only delta DUP-023 có extracted text giống hệt nên dense text embedding không thể quan sát payload khác biệt.

Do đó:

- không dùng BGE-M3 để tuyên bố file an toàn;
- similarity không được bỏ qua annotation, metadata, URI, hidden text, OCR/vision hoặc malware/policy scans;
- modality bắt buộc chưa xử lý phải fail closed;
- duplicate evidence không kế thừa approval, visibility, rights hoặc tenant scope.

## 7. Latency quan sát

| Stage | Local measurement |
|---|---:|
| ONNX session load | 5,765 giây |
| Encode 36 documents | 13,601 giây |
| Mean encode | 377,798 ms/document |
| Repeat probe | 0,358 giây |
| 36×36 similarity matrix | 0,005942 giây |

Đây là single-run development timing trên máy hiện tại, không phải SLA. Chưa có warm/cold distribution, concurrency, batching study hoặc document-length stress test.

## 8. Stop/go decision

| Hạng mục | Decision | Lý do |
|---|---|---|
| BGE-M3 làm secondary candidate generator trong quarantine | GO cho ablation | Recall@3 = 1,0 trên fixture hiện tại |
| Candidate budget K=3 | PROVISIONAL | Đủ cho dev set nhưng chưa có hidden/hard-negative evidence |
| Luôn union MinHash + BGE-M3 | NO-GO hiện tại | Không tăng recall, tăng candidate load |
| Dense global threshold | NO-GO | DUP-016 score 0,997499 nhưng unrelated |
| Dense score để auto-merge/publish | HARD BLOCK | Trộn duplicate evidence với authorization/security |
| Production threshold hoặc SLA | BLOCKED BY EVIDENCE | Thiếu hidden family, corpus nhiễu và latency distribution |

## 9. E0.8 đề xuất

Trạng thái: đã thực hiện trong [Hard-negative candidate routing E0.8](27-hard-negative-routing-e0.8.md); danh sách dưới đây được giữ làm trace của quyết định tại thời điểm E0.7.

1. Mở rộng unrelated/shared-template/cross-course hard negatives và đo candidate precision, recall, cluster size, review load.
2. So chiến lược route: raw/canonical exact trước, sparse và dense chỉ chạy cho phần còn lại; đo incremental value thay vì luôn union.
3. Chọn OCR local sau dependency/security review; giữ image-only case ở trạng thái fail closed cho đến khi modality được xử lý.
4. Tạo hidden-family pack bằng reviewer hoặc quy trình độc lập với generator hiện tại.
5. Chỉ sau các bước trên mới thử candidate budget/threshold; vẫn không gộp bước similarity với rights/security approval.

## 10. Không được claim

- Không có production duplicate precision/recall.
- Không có kết quả trên dữ liệu trường thật hoặc user upload thật.
- Không có OCR/vision hoặc prompt-injection detection result.
- Không có hidden test, threshold đã freeze hoặc vector index production.
- Recall@3 = 1,0 trên 19 relation không phải agent/RAG accuracy.
