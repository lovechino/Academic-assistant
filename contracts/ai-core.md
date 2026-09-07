# Backend -> AI core: boundary draft

Trạng thái: thiết kế, chưa triển khai. Backend là caller; AI core là producer. Có thể dùng Python facade in-process ban đầu, không bắt buộc tạo HTTP microservice. Facade/package public sẽ được định nghĩa khi làm use case đầu tiên; hiện chưa tồn tại.

Use case đầu tiên đang đặc tả: [grounded QA pilot](../docs/workflows/01-grounded-qa-pilot.md). Chưa đóng schema/field names; phân biệt response mode với lỗi vận hành và đưa claim-citation mapping vào bước review tiếp theo.

Đã có [evidence packet boundary draft](evidence-packet.md) với provenance, model-input/evaluator separation và public citation mock. [Content unit và index boundary v0.1](content-unit-index.md) chốt các identity từ material version đến retrieval unit/index projection và tách similarity khỏi equivalence/conflict. Packet integrity, evidence sufficiency và current access là ba kiểm tra độc lập; ví dụ hợp lệ không chứng minh source được serving hoặc model đã chạy.

## Query input

- Request/conversation identity và câu hỏi, mode mong muốn.
- Principal/scope được backend xác thực theo [authorization context draft](authorization-context.md): đúng một active tenant, action/purpose/resource, quyền hoạt động, policy version/epoch và capability ngắn hạn. Không lấy role, tenant hoặc resource authority từ prompt hay payload tự khai.
- Corpus/index snapshot, ngôn ngữ, context và time/token budget; chỉ truyền lịch sử cần thiết, đã được phép.

AI core vẫn phải áp scope trước retrieval và kiểm tra từng nguồn/parent/image/tool result, không chỉ ở generation. Mọi resource dùng trong model input phải có `use_in_model_context`; source viewer recheck action riêng. Thiếu/mismatch/stale scope thì fail closed. In-process boundary không tự tạo sandbox: cấu hình credentials/tools vẫn phải least privilege.

## Query result

- Public answer và trạng thái có/thiếu evidence, từ chối theo policy hoặc cần review.
- Citation/evidence references: document/source version và locator tương ứng HTML/PDF; physical page/bbox/logical slide nếu có, không mặc định tất cả tài liệu có số trang.
- Phân biệt quan sát nguồn với suy luận; không cite generated caption như nguồn gốc.
- Public warning/usage/latency/trace ID khi được phép; không trả raw prompt, hidden reasoning, credentials hoặc raw provider payload.

Backend chuyển result thành HTTP DTO và kiểm tra quyền mở source lần cuối. Frontend không biết private class hay vector-store record của AI core.

## Ingestion boundary

Backend sở hữu material lifecycle, review approval và job identity; AI core sở hữu parse/chunk/index algorithms và candidate index build. Mỗi derived object phải dùng định danh/lineage theo [content unit và index boundary](content-unit-index.md). Job chỉ được phép xử lý theo use scope đã duyệt, không biến research-only thành production-ready.

Result gồm trạng thái từng stage, provenance, quality issues và candidate index version. Publication phải kiểm tra lại material revision/approval hiện hành trước khi chuyển active alias; nguồn bị revoke giữa chừng không được publish từ một job cũ. Chunk/ảnh/parent cũng phải bị chặn truy cập khi revoke, dù việc xóa vật lý còn đang chạy.

## Failure contract

Phân biệt validation/scope denied, source not approved, insufficient evidence, parser incomplete, budget/dependency failure và cancellation. Quy định retryability/idempotency tại use case, không tự retry mọi lỗi model. Tên mã lỗi/field cụ thể sẽ đóng sau review; không có endpoint chạy thật trong tài liệu này.
