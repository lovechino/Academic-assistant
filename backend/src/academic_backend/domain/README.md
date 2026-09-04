# Backend domain

Nơi đặt rule xác thực quyền truy cập theo môn/vai trò, lifecycle nguồn, approval/revocation và audit. Không chứa HTTP framework, ORM hay model SDK.

Người phê duyệt phải là actor được xác thực; output AI chỉ là draft, không có quyền tự nâng trạng thái. Theo [permission matrix](../../../../docs/governance/01-permission-matrix.md) và [document lifecycle](../../../../docs/governance/02-document-lifecycle.md).
