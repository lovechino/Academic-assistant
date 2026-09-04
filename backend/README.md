# Backend

Owner của API và nghiệp vụ ứng dụng. Hiện chỉ có khung source; chưa có server, database, login hoặc job worker hoạt động.

| Thư mục | Trách nhiệm |
|---|---|
| `src/academic_backend/api/` | HTTP/SSE, request validation, response/error mapping |
| `src/academic_backend/application/` | Use case phiên hội thoại, course/material, review và jobs |
| `src/academic_backend/domain/` | Quyền, lifecycle tài liệu, audit/review policy độc lập framework |
| `src/academic_backend/infrastructure/` | Persistence, auth/storage/queue adapters và adapter gọi AI core |
| `src/academic_backend/workers/` | Job entrypoints, retry/idempotency/cancellation |
| `migrations/` | Migration nghiệp vụ backend về sau |
| `tests/` | Unit/integration/auth/contract tests về sau |

Backend xác định user/course scope từ session đáng tin cậy, kiểm tra quyền và gọi AI qua [AI contract](../contracts/ai-core.md). Frontend dùng [HTTP contract](../contracts/http-api.md). Không chuyển thẳng request tự khai quyền của user vào AI.

Backend sở hữu quyết định approve/revoke nguồn. AI core sở hữu cách tạo chunks/index; quyền publish đến từ backend, adapter AI không tự thay review state. File/image citation được backend kiểm tra lại quyền khi mở, kể cả sau khi nguồn bị thu hồi.

FastAPI là hướng dự kiến trong đề bài, chưa có dependency/package hoặc endpoint được triển khai. Không gọi đây là một service deploy được.
