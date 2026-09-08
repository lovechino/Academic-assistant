# Authorization context và agent capability boundary v0.1

Ngày cập nhật: 2026-09-06 — clarification v0.1.1; chưa có runtime enforcement.

Trạng thái: **logical contract draft, chưa phải token format, API schema hoặc behavior đã triển khai**. Threat model và policy đầy đủ ở [multi-tenant Zero Trust authorization](../docs/governance/03-multi-tenant-zero-trust-authorization.md).

## 1. Mục đích

Contract này định nghĩa thông tin đáng tin cậy Backend phải bind trước khi gọi AI core/tool và bằng chứng quyết định phải quay về. Nó ngăn AI tự suy quyền từ prompt, request body, metadata nguồn hoặc model output.

Frontend chỉ gửi selectors/intention. Backend xác thực identity, chọn đúng active tenant, hỏi Policy Decision Point và mint authorization context/capability hẹp. AI core/tool chỉ consume context, không tự thêm role/resource/action.

## 2. Invariants

1. Mỗi request/run có đúng một `active_tenant_id`.
2. Effective permission không lớn hơn giao của user authority, agent profile và tool policy.
3. Capability bind audience, purpose, action, resource/snapshot, policy version, epoch và expiry.
4. Không có wildcard cross-tenant cho user-facing run.
5. Resource ID từ user/model là untrusted selector cho tới khi PEP/PDP resolve và allow.
6. Authorization context không vào prompt, model-visible tool result, public DTO, citation hoặc log raw.
7. Mọi dependency thực dùng phải xuất hiện trong authorization trace; không chỉ root document.
8. Recheck current policy trước model input, side effect, delivery và source view.
9. Deny hoặc policy unavailable fail closed và không retry bằng resource khác ngoài policy.
10. Citation/source reference là lookup handle, không mang quyền.

## 3. Request security envelope

Logical fields; tên/type cụ thể sẽ đóng khi có use case implementation:

| Nhóm | Field logic | Owner/nguồn tin cậy | Ràng buộc |
|---|---|---|---|
| Correlation | request ID, agent-run ID, trace ID | Backend | Nonempty, không dùng làm credential |
| Subject | subject ID/type, auth session ID, assurance/step-up state | Backend/IdP validation | Không nhận từ prompt/client claim |
| Tenant | active tenant ID, membership revision | Backend/PDP | Chính xác một tenant |
| Delegation | workload/agent profile, on-behalf-of subject | Backend | Agent authority ≤ user ∩ profile ∩ tool |
| Intent | action, purpose, requested resource roots | Backend từ validated use case | Action cụ thể, không generic `read_all` |
| Policy | decision ID, policy version, authorization epoch | PDP | Current hoặc bị recheck |
| Data | serving snapshot, material versions, sensitivity ceiling, resource bindings | Backend/PDP/catalog | Version-pinned; mỗi owner tenant khác active tenant cần named share hoặc public-snapshot binding, không wildcard |
| Constraints | tool allowlist, max chunks/rows/calls/tokens/time, egress | Backend policy | Default minimum/read-only |
| Obligations | redact/no-download/watermark/step-up/retain rules | PDP | Consumer phải thi hành hoặc deny |
| Validity | audience, issued/expiry, nonce, replay/use limits | Issuer | Ngắn hạn, integrity protected |

Representation có thể là opaque reference tra server-side hoặc envelope có integrity protection. Không chốt JWT; self-contained token có nguy cơ mang stale relation và lộ metadata nếu thiết kế sai.

### Resource ownership và request tenant

Một request vẫn có đúng một `active_tenant_id`. Mỗi resource binding ghi server-side `resource_owner_tenant_id`, exact resource/version, action/purpose và một trong ba basis:

- `tenant_relation`: owner tenant trùng active tenant, relation hiện hành;
- `public_catalog`: exact public publication/snapshot còn hiệu lực; không suy public từ metadata nguồn;
- `named_share`: exact share ID/revision, authenticated recipient, recipient active tenant, source version, actions/purpose và expiry. Share view-only không cấp search hoặc use-model.

Backend/PDP tạo prefilter theo từng owner partition từ các binding hợp lệ. Broker chỉ hợp kết quả đã được phép; agent không được tự chuyển tenant hoặc thêm partition. Public và tenant evidence có thể cùng packet bằng các item riêng; không ghép thành một unit mất ownership. Copy blob sang tenant người nhận không được dùng để né share expiry/revoke. Quyền mở page/parent/image vẫn cần binding cho đúng resource; share excerpt không tự cấp toàn PDF.

Cache compatibility phải mang active tenant, subject/effective-scope digest, owner-partition set, public-publication revision và từng share/resource revision/dependency. Thu hồi share của B không phải thu hồi quyền owner A, nhưng phải chặn B tại các checkpoint tiếp theo.

### Quarantine inspection lane

`inspect_quarantine` và `inspect_quarantine_ocr` là action riêng: exact submission/snapshot, assigned reviewer hoặc isolated workload, purpose security/rights/content review, egress none mặc định. Agent học tập không được cấp action này. Local scanner có thể xử lý file chưa phân loại để phát hiện secret trong ảnh trong sandbox; output nằm trong restricted inspection namespace. File đã classified `secret_forbidden` không tự tiếp tục OCR; cần incident workflow riêng ngoài phạm vi hiện tại. Inspection không cho phép generic model context, external OCR/VLM, serving index hoặc publication.

## 4. Authorization decision API semantics

Các operation logic cần có:

- `check(subject, tenant, action, resource, context)` cho một action;
- `list_authorized_resources(...)` hoặc prefilter handle cho search;
- `batch_check(...)` cho candidate/dependency nhưng vẫn trả decision theo resource;
- `check_at_least_revision(...)` để không đọc policy cũ hơn revoke/grant vừa commit;
- `mint_run_capability(...)` sau allow;
- `revoke/increment_epoch(...)` khi membership/share/lifecycle/policy đổi.

Không quy định transport/service split. Dù in-process hay networked, semantics và audit không đổi.

## 5. Decision result

| Field logic | Ý nghĩa |
|---|---|
| allow/deny | Deny mặc định |
| reason code | Dùng control flow/audit; public response không lộ object |
| decision ID | Correlate các checkpoint |
| evaluated policy version/revision | Chứng minh freshness |
| authorization epoch | Cache/revocation validation |
| effective resource/action/purpose | Phát hiện selector bị thu hẹp hoặc mismatch |
| obligations | Redaction, no-download, watermark, step-up, limits |
| expires/recheck-before | Giới hạn thời gian quyết định |

## 6. Usage theo component

### Frontend

- không giữ capability nội bộ AI hoặc credential datastore;
- tenant/course/resource ID chỉ là selector;
- không suy role, ẩn UI hoặc opaque ID là enforcement;
- đổi tenant/conversation/logout/login phải invalidate client view/session generation và bỏ state/cached content trước; mọi callback/event kiểm request + conversation + generation trước khi render/ghi cache/history theo [HTTP request/view binding](http-api.md). Client fencing không cấp quyền và không thay current Backend checks.

### Backend

- owner của authentication, active-tenant binding, PDP call, grant/revoke và audit;
- mint capability hẹp; recheck trước delivery/view/download;
- không cấp content access ngầm cho platform/org admin;
- xử lý obligations và generic deny response.

### AI core

- reject missing/expired/audience-mismatched capability;
- áp authorized prefilter trước retrieval và recheck mọi parent/image/attachment;
- chỉ serialize resource có `use_in_model_context` allow;
- không tự grant, publish, share, export hoặc đổi tenant.

### Brokered tool

- xác minh caller/run/action/resource/current epoch độc lập;
- không tin tool arguments do model sinh;
- chỉ trả fields/data đã allow; result mang lineage để pre-delivery verify;
- policy unavailable thì fail closed.

## 7. Authorization trace

Mỗi run giữ trace server-side gồm:

- checkpoint/stage;
- principal/workload/agent-run references;
- tenant, action, purpose và resource/version references;
- decision/policy/epoch;
- allow/deny, obligations và enforcement outcome;
- dependency lineage: retrieved → expanded → model-input → cited → delivered/viewed.

Trace không chứa raw credential/capability và hạn chế raw source/prompt. Evaluation có thể tính exposure theo stage từ trace nhưng không được dùng trace như đường đọc nội dung ngoài quyền.

## 8. Cache compatibility

Một cache entry chỉ compatible nếu tất cả điều kiện sau khớp và còn current:

```text
tenant
AND subject-or-effective-policy-scope digest
AND action AND purpose
AND policy version AND authorization epoch
AND corpus/index snapshot
AND every dependency resource/version
AND tool/model/prompt version where applicable
```

Cache hit vẫn phải recheck trước hydrate/delivery. Semantic similarity không bao giờ thay compatibility check.

## 9. Contract tests bắt buộc

- missing/zero/multiple active tenant → deny;
- client/model spoof role, tenant, resource, policy version → deny;
- audience/action/purpose mismatch → deny;
- expired/replayed capability → deny;
- user allow nhưng agent profile/tool deny → deny;
- authorized root nhưng unauthorized dependency → dependency bị loại và answer không claim phần thiếu;
- revoke/epoch change giữa retrieval/model/delivery/viewer → các checkpoint sau deny;
- public query trong personal tenant → chỉ exact public binding current; public revoke → deny;
- named view share A→B → allow exact version; search/use-model/download nếu không được share → deny;
- tenant switch hoặc recipient/share mismatch → deny, không copy cached content;
- assigned inspector → đọc exact submission ở restricted review lane; learner/agent/khác assignment → deny;
- same query/cache key ở hai tenant/scope → không hydrate chéo;
- PDP timeout/unavailable → protected action deny;
- denial response không xác nhận resource ngoài quyền có tồn tại;
- decision và enforcement trace đủ 100% protected actions.

## 10. Chưa quyết định

Clarification 2026-09-07: accidental deletion recovery dùng các action riêng `inspect_trash_metadata`, `soft_delete`, `restore_to_review`, `purge` theo [material recovery contract](material-recovery.md). Upload/view/share hoặc platform-admin role không mặc định cấp chúng. Restore không khôi phục grants, approval hay epoch cũ; current lifecycle deny chi phối mọi serving checkpoint. Retained trash content chỉ được exact assigned restricted inspection, không cấp generic model-use qua restore.

- token/envelope encoding, signature/MAC/key rotation;
- policy engine/relation store/vendor và topology;
- TTL/revision consistency/batch-check protocol;
- exact error/schema/OpenAPI fields;
- revocation latency và PDP performance SLO.

Không implement các điểm trên chỉ dựa vào draft này; trước tiên phải freeze policy fixtures và expected decisions.
