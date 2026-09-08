# SOURCE-BASE-01 — bản đồ đặt source cho mọi coding agent

2026-09-07. **Scaffold hiện có + quy ước đặt code, chưa phải product implementation.**
User yêu cầu base source để các agent không tạo lại một chức năng ở nhiều folder.
Giữ nguyên ba component và source bytes hiện có; không tạo khung thứ hai, package,
entrypoint, fake service, ORM, dependency hoặc logic runtime. ASTRA-01 + explicit
scoped product GO vẫn bắt buộc; user đã đọc review không đồng nghĩa đã GO.

Đây là nguồn tra cứu placement hiện hành, bổ sung [source layout](04-source-layout.md)
và làm rõ các README scaffold cũ. Khi contract khác với ví dụ ở đây, giữ contract
và báo mismatch; không tự sửa contract hoặc state để phù hợp ví dụ. Kế hoạch/gate
vẫn ở [master plan](../roadmap/03-master-plan-v0.2.md), không được quyết định bởi folder.

## 1. Khung vật lý giữ nguyên

```text
ai-core/
  src/academic_ai/
    domain/           Kiểu và invariant thuần về evidence/context
    ingestion/        Quy tắc biến cấu trúc/giữ context, không SDK/I/O
    retrieval/        Chính sách chọn/gom/pack evidence, không client I/O
    application/      Use case AI + ports; một owner điều phối QA
    agents/           Dự trữ mode/router adapter về sau; không pipeline QA thứ hai
    infrastructure/   Implement ports bằng parser/model/search/source adapters
  prompts/            Prompt versioned, không trộn expected answers
  evaluation/         Đánh giá AI; không được import vào runtime
  experiments/        Lịch sử nghiên cứu riêng, không được import vào runtime
  tests/              Tests nội bộ AI Core, chưa có runtime tests
backend/
  src/academic_backend/
    domain/           Invariant quyền/lifecycle, không DB/HTTP
    application/      Use case + ports, điều phối quyền/jobs/delivery
    api/              HTTP adapter mỏng; không nhân bản rule
    workers/          Job adapter mỏng; không điều phối nghiệp vụ lần hai
    infrastructure/   Identity/DB/storage/queue/AI boundary adapters
  migrations/         Schema migration backend về sau
  tests/              Tests nội bộ Backend
frontend/
  src/
    app/              Route/layout/composition mỏng
    features/         UI/state/hook theo chức năng
    components/       Presentation dùng chung thật sự, không business state
    lib/              Backend transport + boundary DTO mapping
  public/             Chỉ assets đã được phép public
  tests/              UI/contract tests
contracts/            Đặc tả boundary; không Python/TS shared runtime package
tests/                Chỉ integration xuyên component, không copy unit tests
scripts/              Development tooling; không product use case
docs/                 Thiết kế, bằng chứng, kế hoạch/harness
data/                 Source/annotation/result snapshots theo quyền
infra/                Hạ tầng về sau, chưa deployment
```

Các folder runtime ở trên hiện được giữ bằng README, không có code sản phẩm.
Không tạo root `src/`, `app/`, `apps/`, `services/`, `packages/`, `shared/` hoặc
`utils/` để làm một cấu trúc cạnh tranh. Một chức năng có thể đi qua ba component,
nhưng mỗi **trách nhiệm** có một implementation owner; không ép tất cả vào một file.

## 2. Chức năng → owner → nơi đặt

Đường dẫn bên dưới là **địa chỉ dành trước cho task sau GO**, không khẳng định file
đã tồn tại hoặc cấp quyền tạo chúng ngay. Không scaffold tất cả các feature chưa làm.
Tên file cụ thể chỉ được đổi qua task có lý do và cập nhật map; không dùng alias
`service2`, `new`, `v2`, `utils` để lách quyết định owner.

| Trách nhiệm | Vị trí chuẩn dự kiến (tương đối repo root) | Không đặt bản thứ hai ở |
|---|---|---|
| Kiểu evidence/citation/locator + invariant thuần | `ai-core/src/academic_ai/domain/evidence.py` | Backend business domain, frontend DTO tự viết lại invariant |
| Required context/negation/units/dependency rules | `ai-core/src/academic_ai/domain/context.py` | Prompt, graph node, API handler |
| Ghép cấu trúc/chunk sau parse | `ai-core/src/academic_ai/ingestion/chunking.py` | Backend worker, parser SDK adapter |
| Chính sách chọn evidence/candidate groups | `ai-core/src/academic_ai/retrieval/selection.py` | Model prompt, API, `agents/` |
| Pure post-pack completeness và packing decisions | `ai-core/src/academic_ai/retrieval/packing.py` | Frontend, provider adapter, eval scorer dùng làm runtime oracle |
| Điều phối manual Academic QA và gọi các ports | `ai-core/src/academic_ai/application/academic_qa.py` | `agents/academic_qa.py`, backend QA thuật toán |
| Narrow AI I/O ports | `ai-core/src/academic_ai/application/ports/` | Concrete infrastructure hoặc root `contracts/` runtime package |
| Model/search/parser/source I/O adapters | `ai-core/src/academic_ai/infrastructure/` | `domain/`, `retrieval/`, `ingestion/` |
| Public AI boundary + composition nội bộ | `ai-core/src/academic_ai/public.py`, `ai-core/src/academic_ai/composition.py` | Backend import private AI graph/adapter |
| Pure authorization và material lifecycle invariants | `backend/src/academic_backend/domain/authorization.py`, `backend/src/academic_backend/domain/materials.py` | AI Core, route handler, client-side ACL |
| Current resource/action/purpose checks qua trusted ports | `backend/src/academic_backend/application/authorization.py` | UI role checks hoặc model confidence |
| Session/request admission + gọi AI + delivery checks | `backend/src/academic_backend/application/academic_qa.py` | API handler, worker; không copy AI evidence algorithm |
| Upload/quarantine/restore/publish use cases | `backend/src/academic_backend/application/materials.py` | AI tool, frontend, storage adapter tự duyệt |
| Job idempotency/fence/cancel use cases | `backend/src/academic_backend/application/jobs.py` | Worker handler nhân bản state transition |
| HTTP validation/response mapping | `backend/src/academic_backend/api/` | Domain, source parser |
| Queue message → application command | `backend/src/academic_backend/workers/` | AI `agents/`, route handler |
| Trusted identity/persistence + public AI adapter | `backend/src/academic_backend/infrastructure/` | Domain/application import concrete SDK |
| Backend dependency wiring | `backend/src/academic_backend/composition.py` | Module import gây kết nối DB/model |
| Academic QA UI và conversation/request state | `frontend/src/features/academic-qa/` | `app/` đầy logic, `lib/chat-service` |
| Citation fetch/open/revoke và view-generation state | `frontend/src/features/source-viewer/` | `components/` giữ global source cache/quyền |
| Citation card/visual viewer presentation | `frontend/src/components/` | Copy trong mỗi feature |
| Backend API transport/abort và public DTO mapping | `frontend/src/lib/api/` | `features/` tự tạo client, direct vector/model calls |

Backend và AI cùng có `academic_qa.py` **không phải duplicate** nếu một bên sở hữu
admission/delivery, bên kia evidence reasoning. DTO ở mỗi boundary cũng không phải
duplicate nghiệp vụ: mapping/generated types phải truy về contract/version, không
tự sáng tác policy. Runtime completeness và offline scorer có trách nhiệm khác nhau;
không import expected labels/scorer vào QA hoặc mặc định chúng phải chung implementation.

## 3. Giải quyết ba chỗ dễ trùng

### AI application, retrieval và agents

- `application/academic_qa.py` là owner điều phối end-to-end QA sau GO. Đây chỉ là
  placement, không bổ sung state machine/thuật toán triển khai trong lượt này.
- `retrieval/` giữ tính toán/chính sách thuần; cụm “reranking orchestration” trong
  README cũ không có nghĩa tự mở model/search client. Application gọi port I/O,
  rồi đưa kết quả vào policy; infrastructure chỉ thực hiện adapter.
- `ingestion/` cũng giữ transformation thuần; parser/OCR và index writes không nằm đây.
- `agents/` là chỗ dự trữ adapter mode/router ở giai đoạn sau, không owner một QA
  loop thứ hai. Không tạo ba agents từ ba tên năng lực. Giữ [ARCH-02](08-controlled-workflow-decision-v0.1.md):
  controlled multi-step, một vai trò reasoning, manual Academic trước.

### Backend application và workers

API/worker là hai entry adapters của use case, không hai bản xử lý lifecycle.
Worker mapping/ack/transport retry thuộc adapter; policy retry/fence/idempotency
thuộc application/domain theo contract, atomic persistence thuộc infrastructure port
implementation. Tên folder không chứng minh atomicity/current authorization đã có.

### Frontend features và components

Feature source-viewer sở hữu fetching và trạng thái view/request; shared components
chỉ nhận props biểu diễn. Việc ẩn nút hoặc abort UI không thay backend authorization.
Feature Academic dùng source-viewer qua boundary được khai báo, không copy state
machine và không truy cập private hook của feature khác. Chỉ extract shared code khi
có ít nhất hai consumer thực và cùng semantics; không dựng “shared everything”.

## 4. Dependency và test placement

- AI application → domain + ingestion/retrieval policies; ingestion/retrieval → domain.
  Domain/policies không import application, SDK, HTTP, DB hoặc component khác.
- Infrastructure → các ports/types của application/domain. Application không import
  concrete infrastructure. Composition/public facade chịu trách nhiệm wiring.
- Backend API/workers → application → domain. Infrastructure implement ports;
  chỉ backend AI adapter được dùng public AI boundary đã chốt, không private import.
- Frontend app → feature public boundary/components; features → components/lib;
  lib/components không import ngược feature/app. Không runtime-import từ root contracts,
  experiments, data, evaluation hoặc scripts.
- Python file dùng `snake_case.py`; type/module names rõ trách nhiệm. Frontend feature
  folders dùng `kebab-case`. Chưa chốt framework/component naming hoặc generated schema
  tooling; không cài linter/package chỉ để điền skeleton.

Sau GO, unit tests đặt dưới `<component>/tests/unit/<layer>/`, adapter/contract tests
dưới `<component>/tests/integration/`, cross-component tests dưới root `tests/`.
Đây là chỗ dành trước, chưa tạo tests giả. Tests harness vẫn ở `scripts/tests/`.
Fake adapters/fixtures chỉ trong tests của task slice; nếu cần runtime demo adapter
phải có scope review riêng, không copy fake auth rồi gọi là bảo mật thật.

## 5. Quy trình trước khi thêm chức năng

1. Xác định trách nhiệm + contract, tìm owner trong map này.
2. Dùng `rg --files` và `rg` trong component/contract liên quan để tìm symbol,
   synonyms và implementation tương tự; đọc caller/tests. Không scan source secrets.
3. Ghi vào [placement packet](../harness/SOURCE-TASK-TEMPLATE.md): tìm gì, thấy gì,
   reuse/extend/new, exact paths, dependencies, tests và gate.
4. Nếu chức năng đã có: mở rộng owner hiện hành khi đúng scope; không copy. Nếu
   chưa có mapping hoặc cần chuyển owner: báo design delta, scope lại trước sửa;
   không sửa card/state/baseline đang chạy để che drift.
5. Sau sửa: reviewer đối chiếu responsibility/contract, diff và checks. Một tên file
   đúng folder chưa chứng minh code đúng trách nhiệm hoặc hết duplicate.

## 6. Kiểm tra hiện có và giới hạn

`py -3.11 -B scripts/verify_source_layout.py` kiểm Git-visible layout của **pre-product
scaffold**: giữ README markers, reject source roots cạnh tranh, file lạc chỗ và code
runtime/package mới trong component. `verify_structure.py` gọi cùng checker, nên
profile `structure` của harness cũng chạy. Không có flag GO/allow-runtime.

Pass không chứng minh semantic duplicate detection, import/dependency correctness,
runtime behavior, auth, sandbox hoặc source truth. Ignored files/network/bytes đổi rồi
khôi phục không được quan sát; docs/scripts/experiments vẫn cần review để không giấu
runtime trong bề mặt được phép. Git-visible filenames là dữ liệu, không commands.

Để bắt đầu exact fake-adapter product slice: user explicit GO sau review, rồi thay
profile/checker theo scope được duyệt với behavior/import-boundary tests thực. Không
tắt checker để chạy mẫu này. Model nhỏ/bất kỳ chưa được benchmark theo packet.
