# Contracts giữa ba thành phần

Đây là **đặc tả boundary nháp**, chưa phải API/schema đã triển khai hoặc cam kết tương thích v1. [Clarification WP-01.1 ngày 2026-09-06](../docs/evaluation/29-review-regression-and-metric-clarifications-v0.1.md) là reference hiện hành cho inspection/promotion, public/share, model-input, conflict và serving-snapshot semantics; chưa có human sign-off/runtime verification.

- [Backend -> AI core](ai-core.md): input được cấp quyền, evidence/result và lỗi có cấu trúc.
- [Frontend -> Backend](http-api.md): request công khai, identity, streaming và truy cập citation.
- [Evidence packet và public citation](evidence-packet.md): boundary draft, tách input generation với evaluator sidecar; có ví dụ nguồn thật nhưng chưa đóng schema/API.
- [Authorization context và agent capability](authorization-context.md): trusted tenant/policy envelope, quyền dẫn xuất tối thiểu cho agent/tool, revocation và authorization trace.
- [Quarantine manifest và aligned delta](quarantine-manifest.md): tách trusted intake envelope khỏi file-derived observations, representation lineage, security findings và duplicate-review evidence.
- [Content unit và index boundary v0.1.1](content-unit-index.md): stage-aware submission/promotion lineage, similarity-conflict assessment, model-input projection, serving-snapshot activation và revoke ordering.

Owner producer chịu trách nhiệm format; consumer cùng review trước khi đóng phiên bản. Không chia sẻ domain/private modules giữa thành phần để thay thế contract. Không dựng `shared/utils` chỉ để né việc xác định owner.

Khi bắt đầu một use case thật, chốt schema + synthetic fixtures + contract tests cho đúng use case đó. OpenAPI/JSON Schema và generated client sẽ bổ sung khi có implementation; hiện chưa có file schema giả làm API hoạt động.
