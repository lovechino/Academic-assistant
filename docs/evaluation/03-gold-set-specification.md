# Đặc tả local gold set v0.2 — working draft

Ngày cập nhật: 2026-09-04

V0.2 làm rõ completeness/citation gates và provenance; không sửa hoặc nâng hạng các pack silver v0.1. Tham chiếu [metric contract](08-metric-contract-v0.2.md).

## 1. Mục đích

Local gold set là bộ dữ liệu chuẩn để:

- So sánh các phiên bản retriever, reranker, LLM và prompt.
- Đo KPI >=80%.
- Phát hiện regression.
- Chứng minh citation, permission và academic-integrity behavior.

Gold set là evaluation asset, không phải training data.

## 2. Đơn vị dữ liệu

Mỗi case cần các trường logic sau:

| Trường | Ý nghĩa |
|---|---|
| case_id | ID bất biến |
| suite | ingestion, retrieval, academic, learning, router, safety hoặc rbac |
| split | dev, validation hoặc frozen_test |
| language | vi, en hoặc mixed |
| role | student, lecturer, admin |
| course_id / term | Phạm vi học phần |
| corpus_snapshot | Phiên bản kho tài liệu dùng khi chấm |
| query | Câu hỏi đầu vào |
| conversation_history | Ngữ cảnh nhiều lượt nếu có |
| expected_route | academic, learning, hub, multi hoặc clarify |
| answerability | answerable, partially_answerable, unanswerable |
| allowed_response_mode | answer, hint, clarify hoặc refuse |
| reference_answer | Đáp án tham chiếu được giảng viên duyệt |
| required_claims | Các ý bắt buộc |
| forbidden_or_incorrect_claims | Các ý sai/nguy hiểm không được xuất hiện |
| gold_evidence | document_id, version, page/slide và evidence span |
| difficulty | easy, medium, hard |
| reasoning_type | lookup, explanation, comparison, multi-hop, table/figure... |
| policy_tags | graded_work, prompt_injection, permission, privacy... |
| annotators | Người gắn nhãn và người phân xử |
| status | draft, reviewed, frozen, retired |

Đây là schema logic mục tiêu, không phải tên field vật lý của mọi pack hiện có. VOER silver v0.1 dùng `id`, `course`, `route`, `mode`, `evidence`; cần mapping rõ khi làm adapter, không tự coi field theo schema mới bị thiếu là dữ liệu nguồn hỏng. Giữ pack schema/version bất biến cho đến lần migration có review.

## 3. Citation ground truth

Không chỉ lưu tên tài liệu. Mỗi gold evidence phải gắn:

- `document_id` ổn định.
- `document_version`.
- PDF: `physical_page_1based` và bbox/region khi cần; `printed_slide_label` riêng nếu một trang chứa nhiều slide. Không dùng nhãn in làm số trang vật lý.
- HTML: section/span locator theo phiên bản normalization, không tạo số trang PDF giả.
- Evidence text/span.
- Mức độ `required` hoặc `acceptable_support`.
- Quyền tối thiểu để truy cập.

Một claim có thể có nhiều nguồn chấp nhận được. Khi tài liệu được cập nhật, case cũ vẫn chạy trên corpus snapshot cũ hoặc phải được review lại trước khi chuyển snapshot.

Group evidence theo yêu cầu nội dung, không mặc định mỗi chunk/module là một group. Một group có các phương án hỗ trợ (OR); một phương án có thể cần nhiều locator đồng thời (AND). Mọi required group phải được cover. Generated descriptions không được làm gold evidence thay nguồn.

## 4. Rubric cho Academic Assistant

Mỗi tiêu chí chấm `0 = fail`, `1 = partial`, `2 = pass`:

- Correctness.
- Completeness.
- Faithfulness.
- Citation correctness.
- Citation completeness.
- Relevance và clarity.

Các gate nhị phân bổ sung:

- Permission respected.
- Correct response mode.
- Không có critical unsupported claim.

Để tính Grounded Answer Pass Rate, case phải đạt `2` ở correctness, completeness, faithfulness, citation correctness và citation completeness đối với các phần áp dụng; đạt tối thiểu `1` ở relevance/clarity; đồng thời pass toàn bộ gate áp dụng. Required claim/citation bị thiếu luôn làm case fail; điểm partial chỉ dùng chẩn đoán. Tiêu chí N/A phải được xác định hợp lệ, không tự gán để tránh lỗi.

## 5. Rubric cho Learning Assistant

Chấm ba mức `No / To some extent / Yes`:

- Nhận diện lỗi hoặc chỗ chưa hiểu.
- Xác định đúng vị trí lỗi.
- Hướng dẫn đúng và liên quan.
- Có hành động tiếp theo rõ ràng.
- Khuyến khích tự sửa và suy nghĩ.
- Kiểm soát cognitive load.
- Tone phù hợp.
- Không tiết lộ đáp án khi policy cấm.

`Correctness`, `grounding` và `no answer leakage` là gate.

## 6. Rubric cho router

- Một intent rõ ràng: expected route duy nhất.
- Multi-intent: danh sách route bắt buộc và thứ tự nếu có dependency.
- Thiếu thông tin quan trọng: expected route là `clarify`.
- Yêu cầu bị cấm: safety policy được gọi trước downstream agent.

Cần chủ động tạo hard negatives: hai câu có từ khóa gần giống nhưng route khác nhau, câu hỏi đổi intent giữa nhiều lượt, và prompt chứa cả tìm tài liệu lẫn yêu cầu giải thích.

## 7. Annotation workflow

1. Chọn corpus snapshot đã được giảng viên phê duyệt.
2. Người A viết câu hỏi; người B độc lập tìm evidence và đáp án.
3. Hai annotator chấm thử cùng một subset.
4. Phân xử bất đồng bằng giảng viên phụ trách môn.
5. Đo agreement cho label phân loại; sửa guideline nếu agreement thấp.
6. Tách theo tài liệu/chủ đề trước khi chia dev/validation/test để giảm leakage.
7. Freeze test set và giới hạn người được xem.
8. Mọi sửa đổi sau freeze phải có lý do và changelog.

## 8. Phân chia dữ liệu

- Dev: dùng để sửa prompt, chunking, retrieval và policy.
- Validation: dùng để chọn cấu hình, không sửa case theo output hệ thống.
- Frozen test: chỉ chạy ở milestone/release; không dùng để tối ưu hằng ngày.
- Red-team holdout: giữ riêng các prompt tấn công chưa từng thấy.

Không để các câu hỏi khác nhau nhưng dùng cùng một đoạn evidence xuất hiện ở cả dev và test nếu mục tiêu là đo khả năng khái quát.

## 9. Seed set 30 câu đầu tiên

- 8 câu fact lookup.
- 6 câu giải thích khái niệm.
- 5 câu tổng hợp nhiều đoạn/tài liệu.
- 3 câu so sánh.
- 3 câu dựa trên bảng/hình/slide.
- 3 câu unanswerable.
- 2 câu có nguồn mâu thuẫn hoặc khác phiên bản.

Tạo thêm, không trộn vào 30 câu QA:

- 20 case Learning/academic integrity.
- 30 case router.
- 12 case RBAC tối thiểu.

## 10. Quality checklist trước khi freeze

- Câu hỏi tự nhiên, không chứa nguyên văn đáp án một cách vô tình.
- Reference answer có đủ required claims.
- Evidence thực sự hỗ trợ từng claim.
- Page/slide mở đúng ở bản người dùng nhìn thấy.
- Có cả answerable và unanswerable.
- Có phân bố theo môn, loại tài liệu, ngôn ngữ và difficulty.
- Hai annotator hiểu rubric giống nhau.
- Không có dữ liệu nhạy cảm hoặc đáp án bài thi đang sử dụng.
