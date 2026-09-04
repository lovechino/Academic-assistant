# Chiến lược đánh giá v0.2 — working draft

Ngày cập nhật: 2026-09-04

V0.2 thống nhất pass/fail và mẫu số với [metric contract](08-metric-contract-v0.2.md); chưa có run mới hoặc chấm lại output lịch sử. Rule partial-score không được dùng thay các gate bắt buộc.

## 1. Nguyên tắc

Không đánh giá toàn bộ hệ thống bằng một con số duy nhất. Cần chạy ba cấp độ:

1. **Component evaluation:** OCR, retrieval, reranker, router và policy được chấm riêng.
2. **Oracle evaluation:** generator nhận đúng gold evidence để kiểm tra khả năng đọc và trả lời.
3. **End-to-end evaluation:** chạy toàn bộ pipeline từ câu hỏi tới câu trả lời và citation.

Nhờ đó có thể phân loại lỗi:

- Gold evidence không được retrieve: retrieval failure.
- Gold evidence đã có nhưng câu trả lời sai: generation/reasoning failure.
- Câu trả lời đúng nhưng citation sai/thiếu: attribution failure.
- Trả lời trực tiếp khi phải hướng dẫn hoặc từ chối: policy failure.
- Chọn sai agent: routing failure.
- Retrieve tài liệu ngoài quyền: access-control failure.

## 2. Sáu evaluation suites

### Suite A — Ingestion và OCR

Đo trên một tập trang nội bộ đại diện cho PDF text, PDF scan, slide, bảng, công thức và tài liệu nhiều cột.

Metrics:

- Page ingestion success rate.
- Character/word error rate cho OCR.
- Heading, table, formula và reading-order preservation.
- Provenance accuracy: đoạn trích có mở đúng trang/slide hay không.
- Metadata completeness và document-version correctness.

### Suite B — Retrieval và Knowledge Hub

Mỗi query có danh sách gold document/page/chunk.

Metrics:

- Recall@5 và Recall@10.
- Precision@5.
- Mean Reciprocal Rank (MRR).
- nDCG@10 nếu evidence có nhiều mức liên quan.
- Filter accuracy theo môn, học kỳ, loại tài liệu và quyền.
- Multi-document evidence recall.

### Suite C — Academic Assistant

Metrics chính:

- Grounded Answer Pass Rate.
- Required-claim recall và incorrect-claim rate.
- Faithfulness/groundedness.
- Citation precision và citation recall/coverage.
- Answer relevancy.
- Correct abstention khi không có đủ dữ liệu.

### Suite D — Learning Assistant

Rubric được điều chỉnh từ nghiên cứu về đánh giá AI tutor:

- Correctness: không dẫn người học tới kiến thức sai.
- Mistake identification: nhận ra hiểu lầm/lỗi của người học.
- Mistake location: chỉ đúng phần gây lỗi.
- Guidance quality: đưa gợi ý hoặc giải thích phù hợp.
- Actionability: người học biết bước tiếp theo cần làm.
- Coherence và tone.
- Cognitive load: không đổ quá nhiều thông tin cùng lúc.
- Answer leakage: không tiết lộ đáp án khi policy yêu cầu scaffolding.

Các tiêu chí `correctness`, `grounding` và `answer leakage` là gate; không được dùng điểm tone cao để bù cho lỗi này.

### Suite E — Router và orchestration

Mỗi case có `expected_route`, có thể là một route, multi-route hoặc `clarify`.

Metrics:

- Route accuracy và macro-F1.
- Critical misroute rate.
- Multi-intent coverage.
- Unnecessary-agent-call rate.
- Fallback/clarification correctness.
- End-to-end task success sau khi route.

### Suite F — Safety, integrity và RBAC

Bao gồm yêu cầu làm hộ bài, prompt injection, yêu cầu bỏ qua policy, truy cập chéo môn, role spoofing và tài liệu chưa publish.

Metrics:

- Policy compliance rate.
- Answer-leakage rate.
- False-refusal rate trên câu hỏi học tập hợp lệ.
- Prompt-injection resistance.
- Unauthorized retrieval rate; mục tiêu bắt buộc bằng 0.
- Citation-to-unauthorized-source rate; mục tiêu bắt buộc bằng 0.

## 3. Định nghĩa KPI 80%

Mỗi case Academic QA được chấm theo các điều kiện nhị phân:

1. Trả lời đúng và đủ các required claims.
2. Không chứa factual claim sai hoặc không được evidence hỗ trợ; suy luận/ví dụ được phép phải đúng và được phân biệt rõ với nội dung nguồn.
3. Citation hỗ trợ đúng từng claim cần dẫn nguồn, đủ coverage và trỏ đúng nguồn/version/locator.
4. Đúng response mode: answer, hint, clarify hoặc refuse.
5. Không vi phạm quyền truy cập.

Case chỉ pass khi đạt tất cả điều kiện áp dụng. KPI:

`Grounded Answer Pass Rate = passed_cases / eligible_cases`.

Eligible cases được xác định trước run: Academic answerable/partially-answerable có đủ required claims, reference evidence và response-mode labels để chấm. Unanswerable/false-premise, safety và RBAC có mẫu số riêng. Lỗi thực thi hoặc không tìm được evidence trên case answerable tính fail, không loại khỏi mẫu số. Silver score là provisional, không thay nghiệm thu trên reviewed frozen set. Mẫu số 0 là N/A.

## 4. Quy mô test theo giai đoạn

| Giai đoạn | QA grounded | Tutor/policy | Router | RBAC | OCR nội bộ |
|---|---:|---:|---:|---:|---:|
| Seed v0 | 30 | 20 | 30 | 12 | 10 trang |
| Pilot v1 | 120 | 60 | 100 | 40 | 30 trang |
| Frozen v2 | 200+ | 100 | 200 | 60+ | 50+ trang |

Với 24/30 câu pass, accuracy quan sát là 80% nhưng khoảng tin cậy Wilson 95% xấp xỉ 63%-91%. Với 80/100, khoảng này xấp xỉ 71%-87%. Vì vậy 30 câu phù hợp làm smoke test, không đủ mạnh cho kết luận nghiệm thu cuối.

## 5. Cấu trúc QA set đề xuất

- 25% single-hop fact lookup.
- 20% giải thích khái niệm.
- 20% tổng hợp nhiều đoạn hoặc nhiều tài liệu.
- 10% so sánh hai khái niệm/nguồn.
- 10% câu hỏi về bảng, hình, slide hoặc công thức.
- 10% unanswerable/out-of-scope.
- 5% nguồn mâu thuẫn hoặc khác phiên bản.

Các case safety, prompt injection và permission được giữ ở suite riêng để không bị che khuất bởi điểm QA trung bình.

## 6. RAGAS và automated judges

RAGAS có thể dùng cho context precision/recall, faithfulness, response relevancy và các metric agent/tool-use. Tuy nhiên:

- Không gọi RAGAS faithfulness là accuracy.
- Judge model và prompt judge phải được version hóa.
- Chạy judge nhiều lần trên một subset để đo độ ổn định.
- So sánh automated judge với nhãn của giảng viên trước khi dùng trên quy mô lớn.
- Audit thủ công toàn bộ failure nghiêm trọng và một mẫu ngẫu nhiên của case pass.

RAGChecker có thể dùng ở tầng claim để tách lỗi retriever và generator. ALCE cung cấp cách tư duy phù hợp cho citation correctness/completeness. GroUSE cho thấy evaluator tự động cũng có failure mode, vì vậy cần meta-evaluation trên nhãn người thật.

## 7. Quy trình chạy evaluation

1. Cố định corpus snapshot, quyền và phiên bản tài liệu.
2. Cố định model, embedding, reranker, prompt, top-k và seed/temperature.
3. Chạy retrieval-only.
4. Chạy generator với oracle evidence.
5. Chạy end-to-end.
6. Chạy policy, prompt-injection và RBAC suites.
7. Tính confidence interval và kết quả theo từng slice.
8. Human review các case bất đồng hoặc critical failure.
9. Xuất error taxonomy và regression list.

## 8. Báo cáo bắt buộc

- Điểm tổng và confidence interval.
- Điểm theo môn, ngôn ngữ, loại tài liệu, role, difficulty và question type.
- Retrieval/oracle/end-to-end side-by-side.
- Số lỗi citation, hallucination, refusal, routing và permission.
- P50/P95 latency, error rate và chi phí trên mỗi câu hỏi.
- Thay đổi so với baseline gần nhất.

## 9. Nguồn phương pháp chính

- [RAGAS: Automated Evaluation of Retrieval Augmented Generation](https://aclanthology.org/2024.eacl-demo.16/)
- [RAGAS metrics documentation](https://docs.ragas.io/en/latest/concepts/metrics/available_metrics/)
- [RAGChecker](https://arxiv.org/abs/2408.08067)
- [ALCE citation evaluation](https://aclanthology.org/2023.emnlp-main.398/)
- [GroUSE meta-evaluation benchmark](https://aclanthology.org/2025.coling-main.304/)
- [BEA 2025 Pedagogical Ability Assessment](https://sig-edu.org/sharedtask/2025)
- [MathTutorBench](https://aclanthology.org/2025.emnlp-main.11/)
