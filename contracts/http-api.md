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
- Public answer là exact validated canonical candidate theo [evidence §4.1](evidence-packet.md), không sanitize làm đổi nghĩa sau validation. Renderer chỉ dùng profile đã kiểm fidelity; unsupported math/table không được flatten âm thầm.
- Stream events có thứ tự và trạng thái kết thúc/lỗi rõ. Không coi stream protocol của provider là API frontend.

Chưa định nghĩa route names, SSE event schema hay auth provider. Chốt chúng theo use case đầu tiên rồi thêm contract tests, không dựng cả API giả trước khi đi lại problem/metric/workflow.

## Request/view binding — clarification 2026-09-07, WP04-F03

Mỗi pending UI operation giữ tuple opaque request/operation identity + conversation binding + client view/session generation tại lúc gửi. Backend xác thực và bind conversation/persistence target với subject, active tenant và request gốc; không dùng tenant/conversation đang được chọn trên UI lúc callback về làm đích ghi history. Retry với cùng key nhưng conversation khác là payload conflict, không replay vào hội thoại mới.

Frontend đổi tenant, conversation, logout/login hoặc thay session phải invalidate generation cũ **trước khi** nhận callback tiếp và clear state/cache của view trước. Kiểm tuple hiện hành trước mọi render, cache/store update, history append, viewer completion hoặc progress/terminal event; stale callback bị drop không copy body vào log/cache. Abort network là best effort, không thay check. Generation không được tái dùng kiểu A→B→A; kiểm tenant ID đơn thuần không đủ. Correlation này không là credential và không cần lộ tenant ID/capability nội bộ.

Response đã được Backend release hợp lệ trước switch có thể đến muộn: không mặc định đó là auth violation phía Backend, nhưng không được xuất hiện trong view mới. Server có thể hoàn tất/ghi kết quả vào đúng conversation gốc nếu policy/currentness cho phép; việc mở lại history vẫn cần current authorization/influence-set checks. Fetch mới cho view hiện hành có binding mới, không tái sử dụng callback cũ. Streaming nếu bổ sung vẫn phải kiểm binding và sequence/terminal state trên từng event; không mở prevalidated answer streaming ở first slice.

Tests: WPT-18/21/26; cả stale negative và still-current positive. Đây là draft contract, chưa có UI enforcement.

## Future material recovery boundary

Delete/restore UI phải phân biệt thùng rác, restore cần review và purge không phục hồi; không dùng tên file làm target. Theo [material recovery contract](material-recovery.md). Không đưa use case này vào first manual QA slice.
