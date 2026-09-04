# Contracts giữa ba thành phần

Đây là **đặc tả boundary nháp**, chưa phải API/schema đã triển khai hoặc cam kết tương thích v1.

- [Backend -> AI core](ai-core.md): input được cấp quyền, evidence/result và lỗi có cấu trúc.
- [Frontend -> Backend](http-api.md): request công khai, identity, streaming và truy cập citation.
- [Evidence packet và public citation](evidence-packet.md): boundary draft, tách input generation với evaluator sidecar; có ví dụ nguồn thật nhưng chưa đóng schema/API.

Owner producer chịu trách nhiệm format; consumer cùng review trước khi đóng phiên bản. Không chia sẻ domain/private modules giữa thành phần để thay thế contract. Không dựng `shared/utils` chỉ để né việc xác định owner.

Khi bắt đầu một use case thật, chốt schema + synthetic fixtures + contract tests cho đúng use case đó. OpenAPI/JSON Schema và generated client sẽ bổ sung khi có implementation; hiện chưa có file schema giả làm API hoạt động.
