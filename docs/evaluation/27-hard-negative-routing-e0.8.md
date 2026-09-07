# Hard-negative candidate routing — E0.8

Ngày chạy/kiểm: 2026-09-05

Kết luận: **sau khi thêm 24 hard negatives, MinHash vẫn giữ 19/19 matched counterpart ở rank 1; BGE-M3 giữ 18/19 ở rank 1 và 19/19 ở rank 2. Routing `raw exact → canonical exact candidate → retriever@3` giữ recall 1,0, giảm retriever queries 36,84% và candidate reviews từ 57 xuống 44. Union MinHash + BGE-M3 không tăng recall nhưng tạo 60 false candidate slots, nên không bật mặc định.**

## 1. Câu hỏi đo

E0.8 mở rộng E0.7 theo ba câu hỏi:

1. Khi có tài liệu cùng template, cùng tiêu đề hoặc chồng lấn thuật ngữ, matched counterpart còn đứng trong candidate budget không?
2. Bao nhiêu hard negatives lọt vào top K và tạo thêm review load?
3. Exact-first routing có giảm semantic/sparse work mà vẫn giữ candidate recall không?

Đây là candidate-generation diagnostic, không phải duplicate classifier, security detector hoặc production benchmark.

## 2. Corpus và QA

| Thành phần | Số lượng |
|---|---:|
| Relation PDFs từ E0.4–E0.6 | 36 |
| Hard-negative PDFs mới | 24 |
| Tổng PDF / trang | 60 / 64 |
| Physical relations | 21 |
| Expected candidate relations | 19 |
| Unrelated relation negatives | 2 |

24 PDF mới chia đều bốn nhóm:

- shared boilerplate;
- same title, different content;
- cross-course lexical overlap;
- template-dominated short documents.

Tất cả là dữ liệu synthetic, benign và quarantine-only. 24/24 trang đã render ở 120 DPI và visual QA; không thấy clipping, font lỗi, chồng lấn hoặc annotation ngoài dự kiến. Evaluation labels nằm ngoài `embedding_text`.

Artifacts:

- [E0.8 hard-negative PDF manifest](../../data/evaluation/synthetic/duplicate-detection-v0.1/e08-hard-negative-pdf-manifest.json);
- [E0.8 routing result](../../data/evaluation/synthetic/duplicate-detection-v0.1/e08-hard-negative-routing-results.json);
- [reproducible generators, runners và audits](../../ai-core/experiments/security-fixtures/README.md);
- [E0.7 BGE-M3 ablation](26-bge-m3-duplicate-ablation-e0.7.md).

## 3. Candidate ranking

| Retriever | Recall@1 | Full-recall rank | MRR | Hard negatives trong top 3 |
|---|---:|---:|---:|---:|
| Character 5-gram Jaccard | 1,000000 | 1 | 1,000000 | 0/57 |
| MinHash-128 char5 | 1,000000 | 1 | 1,000000 | 2/57 — 3,51% |
| BGE-M3 dense cosine | 0,947368 | 2 | 0,973684 | 5/57 — 8,77% |

Với đúng một judged relevant counterpart cho mỗi query, candidate precision/yield tại K=3 của cả ba method đạt 19/57 = 0,333333 khi recall bằng 1,0. Con số này chỉ mô tả workload của synthetic exhaustive labels, không phải precision trên upload thật.

BGE-M3 vẫn miss DUP-013 ở top 1 như E0.7: counterpart hợp lệ rank 2. Năm hard-negative intrusions ở top 3 của dense retrieval:

| Query relation | Rank | Hard negative | Score |
|---|---:|---|---:|
| DUP-023 | 2 | Same-title marketing | 0,919588 |
| DUP-023 | 3 | Same-title statistics | 0,903557 |
| DUP-012 | 2 | Lexical “độ phức tạp” của dự án | 0,862266 |
| DUP-014 | 3 | Short template về project | 0,826340 |
| DUP-020 | 2 | Lexical “heap” của bộ nhớ | 0,850231 |

Các score được lấy từ artifact máy đọc; bảng làm tròn sáu chữ số. DUP-023 đặc biệt dễ nhiễu vì text embedding không quan sát nội dung image-only khác biệt và phần text còn lại chủ yếu là shell/title.

## 4. Candidate load theo K

| Retriever | K | Recall | False candidate slots | Hard-negative intrusions |
|---|---:|---:|---:|---:|
| MinHash | 1 | 1,000000 | 0 | 0 |
| MinHash | 3 | 1,000000 | 38 | 2 |
| MinHash | 5 | 1,000000 | 76 | 6 |
| MinHash | 10 | 1,000000 | 171 | 31 |
| BGE-M3 | 1 | 0,947368 | 1 | 0 |
| BGE-M3 | 3 | 1,000000 | 38 | 5 |
| BGE-M3 | 5 | 1,000000 | 76 | 12 |
| BGE-M3 | 10 | 1,000000 | 171 | 48 |

Tăng K sau khi đã đạt full recall chỉ làm tăng review load trên fixture này. Tuy nhiên không được freeze K=1 cho MinHash hoặc K=2 cho BGE-M3 vì corpus còn exposed, nhỏ và có nhiều matched pair với lexical overlap rõ.

## 5. Union không có incremental value

| Union cutoff | Recall | Mean candidates/query | False slots | Hard-negative intrusions |
|---:|---:|---:|---:|---:|
| 1 | 1,000000 | 1,052632 | 1 | 0 |
| 3 | 1,000000 | 4,157895 | 60 | 6 |
| 5 | 1,000000 | 7,210526 | 118 | 16 |
| 10 | 1,000000 | 15,473684 | 275 | 71 |

Tại K=3, union tăng workload từ 57 lên 79 candidate slots nhưng không tăng recall. Đây là bằng chứng chống lại việc luôn union hai retriever trên mọi upload.

## 6. Exact-first candidate routing

| Strategy | Recall | Retriever queries | Candidate reviews | False reviews | Hard-negative intrusions |
|---|---:|---:|---:|---:|---:|
| BGE-M3@3 trực tiếp | 1,000000 | 19 | 57 | 38 | 5 |
| Raw exact → BGE-M3@3 | 1,000000 | 18 | 55 | 36 | 5 |
| Raw → canonical candidate → BGE-M3@3 | **1,000000** | **12** | **44** | **25** | **2** |
| Raw → canonical candidate → MinHash@3 | **1,000000** | **12** | **44** | **25** | **2** |

Exact-first routing tránh 7/19 retriever queries, tương đương 36,84%, và giảm candidate reviews 22,81% so với direct top-3. Raw stage xử lý 1 query; canonical candidate stage xử lý 6; retriever xử lý 12.

`Canonical exact candidate` chỉ là routing/candidate evidence. E0.6 đã chứng minh canonical equality có thể che annotation, metadata hoặc image-only poisoned delta. Vì vậy stage này không được auto-merge, bỏ security scans, kế thừa rights hoặc publish.

## 7. Latency quan sát

| Stage | Local single run |
|---|---:|
| ONNX session load | 7,067 giây |
| Encode 60 documents | 20,609 giây |
| Mean encode | 343,491 ms/document |
| Repeat probe | 0,384 giây |
| 60×60 similarity matrix | 0,006076 giây |

Repeat probe trong cùng session có max absolute delta = 0,0. Một lần khởi tạo process/session độc lập trên cùng corpus cũng giữ nguyên toàn bộ relevant score, top-5 score và thứ tự (max delta = 0,0), nhưng encode time thay đổi từ 20,609 xuống 18,155 giây. Đây không phải SLA: chưa đo batching, concurrency, warm/cold distribution hoặc tài liệu dài.

## 8. Stop/go decision

| Hạng mục | Decision | Lý do |
|---|---|---|
| Exact-first candidate routing | GO cho dev design | Cùng recall, giảm retriever calls/review load |
| MinHash làm sparse primary candidate path | PROVISIONAL GO | Rank 1 đủ 19/19 trên corpus hiện tại |
| BGE-M3 fallback/secondary path | PROVISIONAL GO | Full recall ở rank 2; bắt quan hệ semantic nhưng nhiễu hơn ở top 3 |
| Always-union MinHash + BGE-M3 | NO-GO | Không thêm recall, tăng false slots |
| K=1/K=2 làm production budget | NO-GO | Chưa có hidden family hoặc realistic noise |
| Canonical equality auto-merge/publish | HARD BLOCK | Modality/security counterexamples từ E0.6/E0.7 vẫn còn nguyên |

## 9. E0.9 đề xuất

Trạng thái: đã thực hiện trong [Equivalence versus conflicting-claim triplets E0.9](28-equivalence-conflict-triplets-e0.9.md); danh sách dưới đây được giữ làm trace của quyết định tại thời điểm E0.8.

1. Tạo matched triplets `query / relevant / adversarial non-relevant` với cùng course shell và lexical overlap cao hơn; label semantic conflict, revision và legitimate variant tách riêng.
2. Tách generator family khi đánh giá để giảm template leakage; hiện tại chưa được gọi là hidden test nếu cùng quy trình tạo.
3. Đo route theo từng class và document-length bucket, không chỉ aggregate 19 relations.
4. Đánh giá local OCR candidate path riêng cho image-only scans; không trộn OCR quality với duplicate/security decision.
5. Chỉ sau independent review mới thử threshold/candidate budget trên validation rồi khóa một test family chưa thấy.

## 10. Không được claim

- Không có precision/recall trên tài liệu thật.
- Không có teacher-reviewed gold hoặc hidden test.
- Không có OCR/vision, authorization runtime hoặc prompt-injection detector result.
- Không có production latency, serving index hay persisted vectors.
- 19/19 MinHash rank 1 không chứng minh MinHash là final winner.
