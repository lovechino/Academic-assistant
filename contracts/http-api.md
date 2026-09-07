# Frontend -> Backend: boundary draft

Trạng thái: thiết kế, chưa triển khai endpoint/OpenAPI. Backend sở hữu API contract; frontend là consumer.

Luồng ưu tiên hiện tại: [grounded QA pilot](../docs/workflows/01-grounded-qa-pilot.md). Chưa đóng routes/DTO/SSE schema; phải thể hiện riêng thiếu evidence, access denied và dependency failure.

Xem [evidence packet/public citation draft](evidence-packet.md) cho projection/locator invariants và [authorization context draft](authorization-context.md) cho active tenant, action/purpose, capability và revocation. HTML text spans không có số trang PDF; frontend không áp offsets lên representation/version khác. Source reference không tự cấp quyền mở tài liệu.

## Nhóm use case dự kiến

- Chat/học tập: gửi câu hỏi, nhận response hoặc public stream events, hủy/retry theo request identity.
- Knowledge Hub: tìm tài liệu được phép, xem metadata và mở citation/text/image/PDF theo quyền.
- Review workspace: người được phân quyền duyệt/từ chối/thu hồi học liệu; có audit actor và material version.
- Job status: hiển thị đang parse, cần review, thất bại hoặc sẵn sàng; không gọi “ready” chỉ vì upload xong.

## Ranh giới bắt buộc

- Session/auth backend là nguồn identity; client-provided role/course ID chỉ là yêu cầu cần kiểm tra, không phải quyền thật.
- Response/citation dùng public DTO và source locator ổn định; không lộ filesystem path nội bộ, raw model trace hoặc storage secrets.
- File/image access kiểm tra ACL tại thời điểm truy cập, kể cả link được cấp trước khi tài liệu bị thu hồi. Không public hóa kho dữ liệu để tiện làm viewer.
- Frontend render nội dung không đáng tin cậy an toàn; không chạy HTML/script hoặc instructions lấy từ tài liệu.
- Stream events có thứ tự và trạng thái kết thúc/lỗi rõ. Không coi stream protocol của provider là API frontend.

Chưa định nghĩa route names, SSE event schema hay auth provider. Chốt chúng theo use case đầu tiên rồi thêm contract tests, không dựng cả API giả trước khi đi lại problem/metric/workflow.
