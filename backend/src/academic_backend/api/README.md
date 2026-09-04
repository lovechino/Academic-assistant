# API boundary

Nhận HTTP/SSE, validate dữ liệu, lấy principal đã xác thực và chuyển sang application command. Không chứa SQL, prompt, graph hoặc thuật toán retrieval.

Không nhận role/ACL từ câu chữ chat làm quyền thật. Response dùng public DTO đã lọc, không trả raw provider/tool payload. Endpoint/schema cụ thể chưa được triển khai.
