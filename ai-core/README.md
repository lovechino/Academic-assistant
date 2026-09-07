# AI core

Owner của xử lý học liệu và ba trợ lý Academic Assistant, Learning Assistant, Knowledge Hub. Hiện có **khung source và các experiment local**; đã chạy một BGE-M3 exact-index baseline trong `experiments/`, nhưng chưa có agent, product index hoặc service runtime.

## Bố trí

| Thư mục | Trách nhiệm |
|---|---|
| `src/academic_ai/domain/` | Evidence, citation, source locator, retrieval scope và policy thuần |
| `src/academic_ai/application/` | Use case AI, ports và phối hợp các pipeline |
| `src/academic_ai/ingestion/` | Chính sách cấu trúc tài liệu, context-preserving chunking, provenance |
| `src/academic_ai/retrieval/` | Candidate grouping, fusion, reranking policy, parent/neighbor packing |
| `src/academic_ai/agents/` | Router, workflow và công cụ được cấp quyền của ba trợ lý |
| `src/academic_ai/infrastructure/` | Adapter parser/OCR/model/vector store, không chứa quyền nghiệp vụ |
| `prompts/` | Prompt/template có phiên bản, không chứa secrets hay dữ liệu thật |
| `evaluation/` | Harness và cấu hình đánh giá về sau; không copy gold/silver vào source |
| `tests/` | Unit/integration tests của AI core về sau |
| `experiments/` | Khảo sát có kiểm soát, không được import từ runtime |

Tên thư mục thành phần là `ai-core`; tên namespace Python dự kiến là `academic_ai`. Chưa khai báo package hay dependency manifest vì chưa chọn runtime qua thử nghiệm.

## Product-code review gate

[Master Plan v0.2 ASTRA-01](../docs/roadmap/03-master-plan-v0.2.md) là gate bắt buộc trước khi thêm runtime logic vào `src/academic_ai/`, product entrypoint/dependencies, index writer hoặc agent/application state machine. Khi tới gate, Codex phải dừng và báo người dùng để workflow được Astra review; chỉ triển khai sau explicit GO. Docs/contracts và scripts trong `experiments/` không tự động vượt qua gate này.

AI core không sở hữu đăng nhập, API công khai, quyền phê duyệt hoặc UI. Nhận scope đã được backend xác thực, giữ scope qua search, parent expansion và fetch ảnh. Trả lời qua [boundary contract](../contracts/ai-core.md), không trả provider payload/raw prompt cho frontend.

Tài liệu nền: [chunking](../docs/architecture/01-context-preserving-chunking.md), [indexing](../docs/architecture/02-indexing-retrieval-design.md), [Content Unit & Index Contract v0.1](../docs/architecture/07-content-unit-index-contract-v0.1.md), [PDF có hình](../docs/architecture/03-visual-pdf-retrieval.md), [parser diagnostic](../docs/evaluation/07-parser-diagnostic-round0.md).
