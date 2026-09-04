# Project Charter v0.2 — working draft

Ngày cập nhật: 2026-09-04

Cập nhật v0.2: làm rõ pilot kỹ thuật khi chưa có giảng viên và mẫu số KPI; chưa thay scope MVP hoặc phê duyệt stakeholder. Luồng làm việc hiện tại ở [technical pilot 01](roadmap/02-technical-pilot-v0.1.md).

## 1. Bài toán

Kho giáo trình, slide, đề cương và tài liệu tham khảo của trung tâm có giá trị nhưng phân tán, khó tìm kiếm theo nội dung và khó tổng hợp. Sinh viên cần hỗ trợ học tập có nguồn kiểm chứng; giảng viên cần kiểm soát tài liệu, phiên bản và quyền truy cập.

## 2. Mục tiêu

Xây dựng nền tảng giúp sinh viên và giảng viên tìm kiếm, hiểu và tổng hợp kiến thức từ kho tài liệu đã được phê duyệt, với câu trả lời:

- Có bằng chứng từ tài liệu được phép truy cập.
- Có citation tới đúng tài liệu và trang/slide.
- Biết từ chối khi kho tài liệu không đủ thông tin.
- Tuân thủ liêm chính học thuật.
- Có thể đánh giá lặp lại trên một bộ test đóng băng.

## 3. Ba năng lực sản phẩm

### Academic Assistant

Hỏi đáp chuyên sâu theo môn, giải thích và tổng hợp nhiều nguồn. Kết quả phải grounded và có citation.

### Learning Assistant

Chẩn đoán chỗ người học chưa hiểu, giải thích, đưa gợi ý và hành động tiếp theo. Khi gặp bài tập tính điểm, hệ thống ưu tiên scaffolding/Socratic guidance thay vì tiết lộ đáp án cuối.

### Knowledge Hub

Tìm kiếm, lọc, xem, tóm tắt tài liệu và quản lý vòng đời `Draft -> Review -> Published -> Archived`.

## 4. Người dùng

- Sinh viên: hỏi kiến thức, tìm tài liệu, nhận giải thích và lộ trình học.
- Giảng viên: sử dụng trợ lý, upload/review/publish tài liệu, xem phản hồi.
- Quản trị viên, nếu được đưa vào phạm vi: quản lý tài khoản, môn học, quyền và audit.

## 5. In scope của MVP

- Web app với tối thiểu hai vai trò sinh viên và giảng viên.
- Kho tài liệu mẫu của 2-3 môn.
- Academic mode, Learning mode và Knowledge Hub.
- Citation có thể truy ngược tới phiên bản tài liệu và trang/slide.
- Phân quyền theo vai trò và môn học.
- Giảng viên phê duyệt trước khi tài liệu được dùng để trả lời.
- Bộ test nội bộ có nhãn và báo cáo lỗi theo từng lớp hệ thống.

## 6. Ngoài phạm vi MVP

- Trợ lý kiến thức Internet tổng quát.
- Tự động phê duyệt hoặc tự thay thế tài liệu chính thức.
- Làm hộ bài thi/bài tập tính điểm.
- Fine-tuning mô hình trước khi baseline RAG được đo.
- Multi-agent phức tạp trước khi từng chế độ đơn lẻ đạt yêu cầu.

## 7. North-star metric

`Grounded Answer Pass Rate >= 80%` trên bộ test đóng băng.

Một case chỉ pass khi đồng thời đúng nội dung, đủ ý bắt buộc, không có factual claim sai/không được hỗ trợ, citation đủ và hỗ trợ đúng claim, đúng quyền và đúng chính sách học thuật. Ví dụ/suy luận được phép phải ghi rõ không phải quan sát nguyên văn của nguồn và phải đúng. Các metric retrieval, RAGAS, citation và pedagogy là metric chẩn đoán, không thay thế north-star metric.

Mẫu số KPI gồm Academic answerable/partially-answerable có đủ nhãn để chấm; abstention, safety và RBAC báo riêng. Case thiếu required claim không pass bằng điểm completeness một phần. Định nghĩa thống nhất ở [metric contract v0.2](evaluation/08-metric-contract-v0.2.md).

## 8. Critical gates

- Không có trường hợp rò rỉ tài liệu trái quyền trong test suite.
- Không nghiệm thu nếu chỉ đạt điểm trung bình nhưng có lỗi permission nghiêm trọng.
- Mọi tài liệu trong test phải được cố định bằng `document_id`, `version` và checksum/snapshot.
- Test set cuối không được dùng để chỉnh prompt, chunking, retriever hoặc router.

## 9. Câu hỏi cần stakeholder chốt

- 2-3 môn nào được dùng trong pilot?
- Tài liệu nào là nguồn chuẩn khi hai phiên bản mâu thuẫn?
- Loại bài nào được coi là bài tập tính điểm?
- Giảng viên có được phép xem đáp án mẫu qua hệ thống không?
- Phạm vi quyền theo môn, lớp, học kỳ hay khoa?
- Ngân sách mục tiêu cho mỗi 1.000 câu hỏi và giới hạn latency chấp nhận được?

## 10. Phạm vi làm việc trước khi có reviewer

Cho phép chuẩn bị một technical research pilot: tạm chọn CTDL & Giải thuật, dùng snapshot tham chiếu có quyền phù hợp, thiết kế phép đo và review evidence trên giấy. Không coi nghiên cứu này là corpus published cho sinh viên; không gán tác giả nguồn thành người phê duyệt nội bộ và không dùng silver để tuyên bố đạt KPI. Chưa có baseline user research để khẳng định giảm thời gian học hay cải thiện kết quả học tập.
