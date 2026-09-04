# Tiêu chí chọn môn pilot v0.1

Ngày cập nhật: 2026-09-04

## 1. Mục tiêu

Chọn 2-3 môn đủ đại diện để kiểm tra RAG, citation, OCR, pedagogy và phân quyền nhưng vẫn có phạm vi đủ nhỏ để giảng viên tạo gold set chất lượng.

Không chọn môn chỉ vì tài liệu nhiều. Một môn pilot tốt phải có người chịu trách nhiệm nội dung, tài liệu hợp pháp và khả năng tạo câu hỏi kiểm chứng.

## 2. Cấu hình pilot đề xuất

- **Môn A — theory-heavy:** nhiều khái niệm, định nghĩa và quan hệ giữa các phần; phù hợp kiểm tra explanation và multi-document synthesis.
- **Môn B — structure-heavy:** có bảng, công thức, hình hoặc PDF scan; phù hợp kiểm tra parsing/OCR và citation theo trang.
- **Môn C — slide/bilingual-heavy, nếu đủ nguồn lực:** nhiều slide hoặc tài liệu Việt-Anh; phù hợp kiểm tra retrieval tiếng Việt, thuật ngữ và evidence trên slide.

Nếu nguồn lực hạn chế, chỉ chọn A và B.

## 3. Scorecard chọn môn

Chấm mỗi tiêu chí từ 1 đến 5.

| Tiêu chí | Trọng số | Câu hỏi chấm |
|---|---:|---|
| Giảng viên phụ trách sẵn sàng tham gia | 20% | Có người review tài liệu, reference answer và dispute không? |
| Chất lượng/quyền sử dụng tài liệu | 20% | Tài liệu có nguồn gốc, phiên bản và quyền dùng rõ ràng không? |
| Khả năng tạo gold questions | 15% | Có thể tạo ít nhất 40-60 câu hỏi có evidence rõ không? |
| Tính đại diện | 15% | Môn có phản ánh use case thật của trung tâm không? |
| Độ đa dạng tài liệu | 10% | Có giáo trình, slide, đề cương, bảng/hình hoặc scan không? |
| Mức độ sử dụng dự kiến | 10% | Có đủ sinh viên/giảng viên để pilot không? |
| Rủi ro dữ liệu | 5% | Có dữ liệu cá nhân, đáp án thi hoặc bản quyền hạn chế không? Điểm cao nghĩa là rủi ro thấp. |
| Khối lượng vừa sức | 5% | Có thể hoàn thành inventory và annotation trong thời gian dự án không? |

`Pilot score = tổng (điểm 1-5 × trọng số)`.

## 4. Điều kiện loại trực tiếp

Không chọn ở vòng đầu nếu có một trong các điều kiện:

Các điều kiện này áp dụng cho **academic acceptance/published pilot**. Khảo sát kỹ thuật trên nguồn có quyền nghiên cứu có thể chuẩn bị riêng khi chưa có giảng viên, nhưng không đạt score/gate này. CTDL & Giải thuật hiện chỉ được tạm chọn cho [technical pilot 01](../roadmap/02-technical-pilot-v0.1.md).

- Không có giảng viên/content owner xác nhận đáp án.
- Không rõ quyền sử dụng tài liệu.
- Phần lớn tài liệu là đề thi hoặc đáp án đang được sử dụng.
- Không xác định được phiên bản tài liệu chính thức.
- Corpus quá nhỏ để có ít nhất 30 câu hỏi đa dạng.
- Corpus chứa dữ liệu cá nhân nhạy cảm chưa có phương án xử lý.

## 5. Phiếu chấm ứng viên

| Candidate | Owner | Readiness | Rights | Gold-set ability | Representativeness | Diversity | Usage | Low risk | Feasible | Tổng |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Môn ứng viên 1 | Chưa điền |  |  |  |  |  |  |  |  |  |
| Môn ứng viên 2 | Chưa điền |  |  |  |  |  |  |  |  |  |
| Môn ứng viên 3 | Chưa điền |  |  |  |  |  |  |  |  |  |
| Môn ứng viên 4 | Chưa điền |  |  |  |  |  |  |  |  |  |

## 6. Quy tắc ra quyết định

- Chọn hai môn có score cao nhất nhưng không cùng một profile tài liệu.
- Mỗi môn phải có ít nhất một content owner và một người backup.
- Không dùng môn pilot để đại diện cho toàn bộ trung tâm nếu chỉ có một loại tài liệu.
- Ghi lại lý do chọn và không chọn để tránh thay đổi phạm vi tùy tiện về sau.
