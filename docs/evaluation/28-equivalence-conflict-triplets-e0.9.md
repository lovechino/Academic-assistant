# Equivalence versus conflicting-claim triplets — E0.9

Ngày chạy/kiểm: 2026-09-05

Kết luận: **cả Character Jaccard, MinHash và BGE-M3 đều xếp bản sai claim nhưng gần chữ hơn ở rank 1 cho 12/12 triplet; bản diễn đạt tương đương đúng nằm rank 2. Vì vậy các phương pháp này phù hợp để gom candidate review ở K=2 trên fixture hiện tại, nhưng không đủ để quyết định semantic equivalence, collapse index record hoặc auto-merge.**

## 1. Sửa định nghĩa bài toán

Một tài liệu chỉ đổi một claim học thuật không phải “irrelevant” đối với duplicate candidate generation. Nó cần được tìm thấy để diff, kiểm tra revision/poisoning và review. E0.9 vì vậy dùng hai mục tiêu tách biệt:

1. **First-stage candidate goal:** lấy được cả bản equivalent và bản conflicting-review-required.
2. **Second-stage equivalence goal:** ưu tiên bản equivalent, không coi bản conflict là cùng nghĩa hoặc an toàn để merge.

Nếu gộp hai mục tiêu thành một recall score, hệ thống có thể đạt retrieval recall cao nhưng vẫn chọn bằng chứng sai claim.

## 2. Corpus

| Thành phần | Số lượng |
|---|---:|
| Corpus E0.8 giữ lại | 60 PDF / 64 trang |
| Triplet family mới | 36 PDF / 36 trang |
| Tổng candidate pool | 96 PDF / 100 trang |
| Triplets | 12 |
| Layout families mới | 3 |

Mỗi triplet gồm:

- query note;
- semantic-equivalent paraphrase;
- lexically closer document có claim/mechanism/policy conflict và bắt buộc review.

Các chủ đề phủ thuật toán, cấu trúc dữ liệu, database, hệ điều hành, mạng, thống kê, giải tích, ML metric, operator semantics và tenant authorization. Family E0.9 dùng generator/layout riêng; role, filename và triplet label không nằm trong `embedding_text`. Đây vẫn là exposed synthetic dev set, không phải hidden hoặc teacher-reviewed gold.

Artifacts:

- [E0.9 PDF manifest](../../data/evaluation/synthetic/duplicate-detection-v0.1/e09-equivalence-triplet-pdf-manifest.json);
- [E0.9 triplet result](../../data/evaluation/synthetic/duplicate-detection-v0.1/e09-equivalence-triplet-results.json);
- [reproducible generator/runner/audit](../../ai-core/experiments/security-fixtures/README.md);
- [E0.8 hard-negative routing](27-hard-negative-routing-e0.8.md).

## 3. Pairwise equivalence result

| Method | Equivalent preferred | Conflict preferred | Accuracy | Mean equivalent margin |
|---|---:|---:|---:|---:|
| Character 5-gram Jaccard | 0/12 | 12/12 | 0,000000 | -0,425069 |
| MinHash-128 char5 | 0/12 | 12/12 | 0,000000 | -0,403646 |
| BGE-M3 dense cosine | 0/12 | 12/12 | 0,000000 | -0,050567 |

`Equivalent margin = score(query, equivalent) - score(query, conflict)`. Giá trị âm nghĩa là conflict được ưu tiên. Không method nào phân biệt đúng một triplet, kể cả authorization policy và các thay đổi số/công thức.

Đây không phải kết luận rằng BGE-M3 không hữu ích. Bi-encoder đang làm đúng vai trò similarity candidate retrieval: bản conflict dùng gần như cùng câu chữ nên rất gần query. Sai lầm sẽ xuất hiện nếu hệ thống diễn giải similarity thành equivalence hoặc truth.

## 4. Candidate coverage

| Method | Equivalent recall@1 | Conflict recall@1 | Dual coverage@2 | Mean ranks equivalent/conflict |
|---|---:|---:|---:|---:|
| Character Jaccard | 0,000000 | 1,000000 | 1,000000 | 2 / 1 |
| MinHash | 0,000000 | 1,000000 | 1,000000 | 2 / 1 |
| BGE-M3 | 0,000000 | 1,000000 | 1,000000 | 2 / 1 |

First-stage K=2 lấy đủ 12/12 equivalent và 12/12 conflict trong pool 96 tài liệu. Đây là kết quả tốt cho **review candidate coverage**, nhưng K=2 chưa được freeze vì triplets được tạo có chủ đích và chưa có family ẩn.

## 5. BGE-M3 score inversion

| Nhóm | Min score | Max score |
|---|---:|---:|
| Equivalent paraphrase | 0,892320 | 0,965793 |
| Conflicting near-copy | 0,977747 | 0,999859 |

Trên fixture này, conflict score thấp nhất vẫn cao hơn equivalent score cao nhất. Một global threshold không những không tách được hai nhóm mà còn ưu tiên sai theo hướng nhất quán. Những thay đổi nhỏ như `queue → stack`, `O(log n) → O(n²)`, dấu âm, mẫu số precision/recall hoặc `deny → allow` không thể được bảo vệ bằng cosine threshold.

## 6. Tác động trực tiếp tới chunking và indexing

E0.9 chốt các invariant thiết kế sau:

1. Similarity edge chỉ mang nghĩa `candidate_similar`, không phải `same_as`.
2. Không collapse các document/chunk có score cao thành một canonical record duy nhất.
3. Giữ immutable source version, checksum, tenant, page locator và claim-bearing span riêng cho từng bản.
4. Chunking không được tách toán tử, phủ định, số, công thức hoặc chủ thể khỏi câu/heading tạo nghĩa cho chúng.
5. Context packing cho câu hỏi có nhiều version phải giữ conflicting evidence, không chỉ lấy top 1 rồi che mất bản còn lại.
6. Khi chưa phân giải conflict, answer/agent phải abstain hoặc trình bày khác biệt kèm nguồn; không tự chọn bản có embedding score cao hơn.

Điều này liên kết trực tiếp với rủi ro mất context: một chunk giữ hầu hết từ khóa nhưng mất `không`, dấu âm, mẫu số hoặc tenant qualifier có thể nhìn rất gần trong embedding trong khi ý nghĩa bị đảo.

## 7. Metric cần thêm cho adjudication stage

| Metric | Ý nghĩa | Gate đề xuất ban đầu |
|---|---|---|
| Claim-delta span recall | Có phát hiện đúng vùng số/toán tử/phủ định/entity thay đổi không | 1,0 trên critical synthetic cases |
| Conflict candidate coverage@K | Cả hai bản có vào packet review không | 1,0 trên reviewed critical set |
| Equivalence pairwise accuracy | Equivalent có được ưu tiên hơn conflict không | Chưa freeze trước calibration |
| False-equivalence rate | Conflict bị gắn `same_as` | 0 trên authorization/security-critical cases |
| Conflict-aware abstention recall | Hệ thống có dừng khi chưa phân giải không | 1,0 trên critical unresolved cases |
| Citation dual-coverage | Câu trả lời so sánh có cite đủ hai phía không | 1,0 cho query yêu cầu đối chiếu |

RAGAS answer metrics không thay thế các gate trên. Các gate claim/conflict cần oracle span và deterministic trace; LLM judge chỉ có thể là diagnostic sau calibration.

## 8. Runtime quan sát

| Stage | Local run |
|---|---:|
| ONNX session load | 5,104 giây |
| Encode 96 documents | 35,207 giây |
| Mean encode | 366,744 ms/document |
| Repeat probe | 0,409 giây |
| 96×96 similarity matrix | 0,005088 giây |

Within-session repeat có max absolute delta = 0,0. Đây không phải production SLA.

## 9. Stop/go decision

| Hạng mục | Decision | Lý do |
|---|---|---|
| Char5/MinHash/BGE-M3 cho broad candidate generation | GO cho dev | Dual review coverage@2 = 12/12 |
| BGE-M3 cosine làm semantic-equivalence judge | NO-GO | Conflict preferred 12/12 |
| Similarity threshold để collapse index/auto-merge | HARD BLOCK | Score ranges đảo ngược hoàn toàn |
| Giữ cả equivalent và conflict trong review packet | GO | Tránh top-1 che mất claim khác biệt |
| K=2 production budget | NO-GO | Chưa có hidden family/realistic scale |
| Answer khi conflict chưa resolve | ABSTAIN/HITL | Không có teacher-reviewed authority |

## 10. E0.10 đề xuất

1. Thiết kế claim-sensitive diff trước: số, đơn vị, toán tử, phủ định, formula, entity, authorization qualifier và provenance.
2. Định nghĩa evidence packet chứa `candidate_similar`, `claim_delta`, `conflict_status` và hai source locators riêng.
3. So deterministic delta rules với một cross-encoder/NLI candidate local; chưa chọn model trước khi xác định license, tiếng Việt và metric.
4. Thêm mutation tests cho việc chunk boundary làm rơi từ phủ định, dấu âm, mẫu số hoặc heading.
5. Chạy adjudication chỉ trên 12 triplets hiện tại để debug; sau đó mới tạo validation/hidden family bằng quy trình độc lập.

## 11. Không được claim

- Không có teacher-reviewed correctness hoặc gold equivalence labels.
- Không có hidden test hoặc dữ liệu trường thật.
- Không có cross-encoder, NLI, LLM judge hoặc RAGAS result.
- Không có OCR/vision, serving index, auto-merge hay authorization runtime.
- Dual coverage@2 trên synthetic triplets không phải production recall.
