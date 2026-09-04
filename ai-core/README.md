# AI core

Owner của xử lý học liệu và ba trợ lý Academic Assistant, Learning Assistant, Knowledge Hub. Hiện chỉ có **khung source**, hai script khảo sát đã có và tài liệu; chưa có agent/model/index chạy thật.

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

AI core không sở hữu đăng nhập, API công khai, quyền phê duyệt hoặc UI. Nhận scope đã được backend xác thực, giữ scope qua search, parent expansion và fetch ảnh. Trả lời qua [boundary contract](../contracts/ai-core.md), không trả provider payload/raw prompt cho frontend.

Tài liệu nền: [chunking](../docs/architecture/01-context-preserving-chunking.md), [indexing](../docs/architecture/02-indexing-retrieval-design.md), [PDF có hình](../docs/architecture/03-visual-pdf-retrieval.md), [parser diagnostic](../docs/evaluation/07-parser-diagnostic-round0.md).
