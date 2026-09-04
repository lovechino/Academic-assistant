# N1 readiness checklist

## 1. Trạng thái hiện tại

- [x] Có tiêu chí chọn môn pilot.
- [x] Có course/document inventory template.
- [x] Có metadata dictionary.
- [x] Có permission matrix bản nháp.
- [x] Có document lifecycle bản nháp.
- [x] Có danh sách môn ứng viên thật.
- [x] Chọn được 3 môn pilot cho nghiên cứu kỹ thuật.
- [ ] Có content owner cho từng môn.
- [ ] Có 10-20 tài liệu mẫu mỗi môn.
- [x] Ghi nhận provenance, giấy phép nguồn, content signal và sensitivity sơ bộ.
- [ ] Có người phụ trách nội bộ xác nhận quyền sử dụng và tính phù hợp học thuật.
- [x] Điền inventory và đánh dấu tài liệu khó cho corpus VOER.

Corpus hiện có: 34 module công khai thuộc Cấu trúc dữ liệu và giải thuật, Cơ sở dữ liệu và Kinh tế học vi mô. Đây là `research_reference`, chưa phải authoritative corpus.

## 2. Gói thông tin cần thu thập cho mỗi môn

- Mã và tên môn.
- Giảng viên/content owner.
- Học kỳ áp dụng.
- Ngôn ngữ chính.
- Danh sách file hoặc vị trí lưu.
- Loại tài liệu và số trang/slide gần đúng.
- Tài liệu scan, bảng, công thức hoặc hình phức tạp.
- Phiên bản chính thức.
- Quyền cho Student/Lecturer.
- Có hay không đề thi, đáp án hoặc dữ liệu cá nhân.
- 5-10 câu hỏi thật mà sinh viên thường hỏi.

## 3. Điều kiện hoàn thành N1

N1 hoàn thành khi:

- Có tối thiểu hai môn khác profile dữ liệu.
- Mỗi môn có owner và reviewer.
- Mỗi file mẫu có `document_id`, version, rights, access và lifecycle status.
- Có ít nhất 30 trang/slide đại diện cho các trường hợp parsing quan trọng.
- Không còn tài liệu `rights_status = unknown` trong tập dự kiến publish.
- Permission matrix được stakeholder chấp thuận hoặc ghi rõ exception.

Trạng thái gate ngày 2026-09-04: **chưa đạt**. Đã hoàn thành acquisition và technical profiling, nhưng thiếu content owner/reviewer và xác nhận chương trình hiện hành.

## 4. Handoff sang N2

Sau N1, chọn 3-5 tài liệu authoritative mỗi môn để tạo 10 annotation cases đầu tiên. Các case này được dùng để hiệu chỉnh rubric Academic, Learning, Router và citation trước khi mở rộng gold set.
