# Backend infrastructure

Adapter database/repositories, identity provider, object storage, queue và AI core. Thực hiện ports của application/domain.

Adapter gọi AI chỉ dùng public boundary đã công bố, không import `academic_ai.agents`, `ingestion` hoặc private infrastructure. ORM/migration nghiệp vụ thuộc backend; cấu trúc chunk/index thuộc AI core và được version riêng.

Chưa có database/provider configuration; secrets không nằm trong source hay frontend.
