# Source layout và ranh giới ba thành phần

Ngày: 2026-09-04. Trạng thái: **đã tổ chức thư mục, chưa triển khai runtime sản phẩm**.

## 1. Tham khảo P-122 như thế nào?

Đã đọc `E:\P-122\ARCHITECTURE.md`, các phần ownership/dependency của `docs/CODEBASE.md`, quy tắc repo và cấu trúc `src/`, `frontend/src/`. P-122 có frontend riêng nhưng API/application/domain/agents/infrastructure chung trong root `src/`.

Áp dụng cách phân lớp và contract boundary, nhưng tách source Academic Assistant thành ba component ngang hàng. Không sao chép logic thương mại, source implementation, credentials, env, caches, dependencies hoặc deployment config từ P-122. P-122 chỉ là nguồn tham khảo, không bị sửa.

## 2. Cấu trúc hiện tại

```text
Academic-assistant/
├── ai-core/
│   ├── src/academic_ai/
│   │   ├── domain/
│   │   ├── application/
│   │   ├── ingestion/
│   │   ├── retrieval/
│   │   ├── agents/
│   │   └── infrastructure/
│   ├── prompts/
│   ├── evaluation/
│   ├── experiments/pdf-pilot/   # Hai helper đã có được chuyển về đây
│   └── tests/
├── backend/
│   ├── src/academic_backend/
│   │   ├── api/
│   │   ├── application/
│   │   ├── domain/
│   │   ├── infrastructure/
│   │   └── workers/
│   ├── migrations/
│   └── tests/
├── frontend/
│   ├── src/{app,features,components,lib}/
│   ├── public/
│   └── tests/
├── contracts/                  # Đặc tả nháp giữa các component
├── docs/                       # Problem, roadmap, kiến trúc, governance, eval
├── data/                       # Giữ nguyên nguồn, annotations và kết quả local
├── infra/                      # Chưa có deployment manifests
├── scripts/                    # Kiểm tra/bảo trì repo
├── tests/                      # Dành cho integration xuyên component
└── tmp/                        # Scratch local đã có, không phải source
```

Thư mục runtime được giữ bằng README ownership, **chưa có class/API/page giả**. Chưa tạo package/dependency lock, app entrypoint, model runtime, Docker service, database hoặc Git repository. Các `.gitignore`/`.gitattributes` là chuẩn bị cho source control, không phải đã commit/publish.

## 3. Ai sở hữu việc gì?

| Việc | Owner chính | Ranh giới |
|---|---|---|
| PDF layout/OCR/chunking | AI core | Backend chỉ điều phối job và quyền nguồn |
| Hybrid/visual retrieval, indexing, rerank | AI core | Scope bắt nguồn từ backend, được áp lại trong mọi bước truy xuất |
| Agent routing, grounding, pedagogical guidance | AI core | Không tự cấp quyền, không tự duyệt học liệu |
| Đăng nhập, vai trò, course/material access | Backend | Frontend/LLM không tự quyết định quyền |
| Review, approve/revoke, jobs, audit | Backend | AI có thể đề xuất draft, người được phép mới phê duyệt |
| Chat/Hub/review UI, citation viewer | Frontend | Gọi backend; không truy cập thẳng kho/vector/model |
| Protocol và quyết định nghiệm thu | Docs + người review | Harness AI core không tự đổi KPI/gold để pass |
| Nguồn/nhãn/result snapshots | Data tại root | Giữ một bản có version/provenance, không copy vào ba component |

## 4. Quy tắc dependency

Luồng sản phẩm dự kiến: **Frontend -> Backend -> AI core**. Đây là luồng gọi, không yêu cầu ba microservices.

Trong Python component: entrypoint/adapters -> application -> domain; infrastructure implement ports của application/domain. Backend AI adapter chỉ gọi public facade/contract, không import graph/chunker/private adapter. AI core không import backend. Frontend không import source Python hoặc truy cập private state.

Root `contracts/` chứa đặc tả dùng chung, không gom mọi tiện ích vào `shared`. Chưa tạo framework/abstraction nếu chưa có use case cần nó. Có thể compose AI core trong process backend lúc đầu; chưa tạo internal HTTP API chỉ để làm rõ source ownership.

Source separation không phải security sandbox. Khi implement vẫn phải least-privilege credentials, deny-by-default scope và kiểm tra quyền ở retrieval, parent/image fetch, source download và publication. Backend sở hữu quyết định quyền; AI adapters không được bỏ qua nó.

## 5. Di chuyển và tương thích dữ liệu

| Trước | Sau | Thay đổi |
|---|---|---|
| `research/pdf-pilot/profile_local.py` | `ai-core/experiments/pdf-pilot/profile_local.py` | Root resolver `parents[2]` -> `parents[3]`, cập nhật dòng hướng dẫn chạy |
| `research/pdf-pilot/audit_layout_order.py` | `ai-core/experiments/pdf-pilot/audit_layout_order.py` | Root resolver `parents[2]` -> `parents[3]` |
| `data/` | Không đổi | Không tái tạo corpus, manifest, annotations hay eval results |
| `docs/` | Không đổi vị trí tài liệu | Cập nhật links helper và thêm chỉ mục/kiến trúc source |

Không để lại bản script trùng ở đường dẫn cũ. Helper vẫn là experiment có side effects khi chạy; không tự rerun vì thao tác sắp xếp source. `.gitignore` loại raw/processed/evaluation local khỏi source control mặc định; đây không phải cấp phép sử dụng hoặc cơ chế ngăn một lệnh force-add.

Khi chia sẻ repo source về sau, data links có thể chưa có file trên máy nhận; cấp dataset qua workflow có quyền và snapshot riêng. Không gỡ ignore hàng loạt để làm các link xanh.

## 6. Quay lại các bước nghiên cứu sau khi tổ chức source

Ở lần sắp xếp source, chỉ ghi điểm tiếp tục, chưa chạy phase mới. Sau yêu cầu tiếp tục của người dùng, đã có [bản nháp technical pilot 01](../roadmap/02-technical-pilot-v0.1.md) cho problem/metric/workflow; vẫn chưa triển khai runtime:

1. Problem/use cases: đối chiếu [charter](../01-project-charter.md) và quyền mỗi vai trò.
2. Metrics/evaluation: chốt rubric, silver/gold và các case lỗi tại [evaluation strategy](../evaluation/01-evaluation-strategy.md).
3. Workflow/contracts: chốt một vertical slice qua ba component, schema cụ thể và failure states.
4. Data/rights: review snapshot/nguồn; scan/OCR chưa tự nhập thêm.
5. Parsing/context/chunking: dùng [12 structural probes](../evaluation/07-parser-diagnostic-round0.md), rồi mới thử indexing/retrieval.
6. Implementation: chọn/pin dependency, thêm package/entrypoint/tests cho use case đã thống nhất; không coi skeleton này là MVP.

## 7. Kiểm tra cấu trúc

`python scripts/verify_structure.py --require-local-data` tại repo root: kiểm tra markers, Python syntax, root resolver, links và hash nguồn PDF. Không chạy parser, không tạo lại eval data và không gọi model. Xem [hướng dẫn verifier](../../scripts/README.md).

Kết quả kiểm tra sau tổ chức ngày 2026-09-04:

- 158/158 kiểm tra structure/syntax/links/checksum đạt, không skip khi có corpus local; 3 file Python được kiểm tra syntax, 17 hash PDF khớp manifest.
- So sánh trước/sau: toàn bộ 240 file trong `data/` giữ nguyên checksum. Hai helper chỉ đổi root resolver và dòng hướng dẫn đường dẫn, không đổi thuật toán.
- Mô phỏng checkout chỉ có source: chế độ mặc định pass và báo 20 data/link checks bị skip; chế độ `--require-local-data` trả lỗi đúng khi thiếu corpus.
- Không chạy lại helper để tránh ghi đè snapshot lịch sử. Không chạy runtime tests vì chưa có sản phẩm; không cài thêm dependency.

Bản sao kiểm tra source-only nằm trong `tmp/` local, đã được ignore. Thư mục `research/pdf-pilot/` cũ không còn script; thư mục rỗng có thể còn trên filesystem nhưng không phải source component.
