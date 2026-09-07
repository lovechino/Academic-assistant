# Policy decision table v0.1

> Historical oracle 2026-09-05: DT cases/fixtures giữ nguyên. Các case bổ sung về inspection lane, public/share binding và race/revision theo clarification 2026-09-06 nằm trong [review regression registry](../evaluation/29-review-regression-and-metric-clarifications-v0.1.md); chưa được tính là runtime pass hoặc ngầm cộng vào 102 cases.

Ngày cập nhật: 2026-09-05

Trạng thái: **expected-policy oracle để review, chưa phải kết quả runtime**. Bảng này cụ thể hóa [Zero Trust blueprint](03-multi-tenant-zero-trust-authorization.md) trên [synthetic pack](../../data/evaluation/synthetic/authorization-v0.1/README.md).

## 1. Mục tiêu

- tách expected behavior khỏi policy engine/vendor;
- buộc mỗi decision nêu subject, active tenant, action, purpose, resource và current state;
- bao phủ cả allow path để không tối ưu bằng cách “deny tất cả”;
- cung cấp oracle cho policy unit, integration, concurrency và agent red-team về sau.

## 2. Precedence của quyết định

PDP đánh giá theo thứ tự logic sau; một deny ở tầng cao không được tầng thấp override:

1. identity/session hợp lệ và đúng một active tenant;
2. tenant/resource lineage và trusted relation;
3. explicit deny, quarantine và `secret_forbidden`;
4. lifecycle/admission cho purpose;
5. role + resource relation cho action;
6. sensitivity clearance, separation of duties và environmental obligations;
7. agent profile/tool allowlist/budget;
8. capability audience/action/resource/version/epoch/expiry;
9. final current-state recheck ở checkpoint đang thực thi.

Không trả public error khác nhau giữa “resource không tồn tại” và “resource ngoài quyền” nếu khác biệt đó tạo existence oracle.

## 3. Subject và resource classes

Synthetic IDs đầy đủ nằm ở `entities.json`. Các alias dùng trong bảng:

| Alias | Mô tả |
|---|---|
| `FREE` | free user, personal tenant, không thuộc trường |
| `A-STUDENT` | sinh viên Course A/CTDL |
| `A-LECTURER` | contributor Course A/CTDL |
| `A-OWNER` | course owner/approver Course A/CTDL |
| `A-CURATOR` | curator được phân scope Course A |
| `A-ADMIN` | org admin Trường A, không có content-reader grant |
| `PLATFORM-ADMIN` | admin kỹ thuật platform, control plane only |
| `B-STUDENT` | thành viên Tổ chức B |
| `TUTOR-A` | agent run thay mặt A-STUDENT, read-only tool profile |
| `INDEXER-A` | workload chỉ transform/index version đã admission |

| Resource class | Ví dụ | Thuộc tính chính |
|---|---|---|
| Public catalog | `PUBLIC-CTDL` | public, published |
| Course material | `A-NOTES` | tenant A, CTDL, course_restricted, published |
| Draft | `A-DRAFT` | tenant A, draft |
| Staff note | `A-STAFF` | tenant A, staff_restricted, published |
| Assessment | `A-EXAM` | tenant A, assessment_confidential, in_review |
| Secret canary | `A-SECRET` | tenant A, secret_forbidden, quarantined |
| Visual dependency | `A-FIGURE` | child của A-NOTES, version-pinned |
| Other tenant | `B-NOTES` | tenant B, title gần giống A-NOTES |
| Personal resource | `FREE-OWN` | personal tenant của FREE |
| External share | `A-SHARED-V1` | version đích danh được share cho B-STUDENT |

## 4. Baseline action policy

Ký hiệu: `A` allow khi relation/current state hợp lệ; `D` deny mặc định; `O` cần obligation/step-up/approval bổ sung.

| Action | Student | Lecturer | Course owner | Curator | Org/platform admin | Tutor agent |
|---|:---:|:---:|:---:|:---:|:---:|:---:|
| `discover_metadata` | A trong scope | A trong scope | A trong scope | A assignment | D nếu không content grant | A trong scope |
| `search` | A published scope | A published + own draft review path | A course | A assignment | D content | A capability scope |
| `read_excerpt` | A published scope | A scope | A course | A assignment | D content | A capability scope |
| `use_in_model_context` | A published/admitted | A admitted | A admitted | A admitted | D content | A capability scope |
| `view_source` | A nếu policy cho | A scope | A course | A assignment | D content | Không trực tiếp; viewer reauth user |
| `download` | Theo resource policy | A scope | A course | A assignment | D content | D |
| `upload/edit draft` | D | A own/assigned | A course | A assignment | D | D |
| `submit_review` | D | A own/assigned | A course | A assignment | D | D |
| `approve/publish` | D | D own version | A nếu không conflict | A assignment nếu không conflict | D | D |
| `share/export` | D mặc định | D mặc định | O | O | O control-specific | D |
| `manage_grants` | D | D | D | D | O control plane | D |

Action `read_excerpt`, `use_in_model_context`, `cite`, `view_source` và `download` độc lập; allow một action không suy ra action khác.

## 5. Decision oracle

### 5.1 Positive controls

| ID | Subject/context | Action → resource | Expected | Lý do/obligation |
|---|---|---|---|---|
| DT-001 | FREE / personal | search → PUBLIC-CTDL | ALLOW | Public snapshot current |
| DT-002 | FREE / personal | read_excerpt → FREE-OWN | ALLOW | Owner relation |
| DT-003 | A-STUDENT / tenant A / learn | search → A-NOTES | ALLOW | Active course relation + published |
| DT-004 | A-STUDENT / tenant A / learn | use_in_model_context → A-NOTES | ALLOW | Tutor corpus admission current |
| DT-005 | A-STUDENT / tenant A | view_source → A-NOTES | ALLOW | Viewer rechecks current relation |
| DT-006 | A-LECTURER / tenant A / review | read_excerpt → A-DRAFT | ALLOW | Contributor of exact material |
| DT-007 | A-OWNER / tenant A / review | approve → A-DRAFT | ALLOW | Không phải editor của version; step-up + audit |
| DT-008 | A-CURATOR / tenant A / curate | edit_metadata → A-DRAFT | ALLOW | Assignment includes course A |
| DT-009 | B-STUDENT / tenant B | view_source → A-SHARED-V1 | ALLOW | Share recipient/version/action còn hạn |
| DT-010 | TUTOR-A / tenant A / learn | read_excerpt → A-NOTES | ALLOW | User ∩ agent profile ∩ capability |
| DT-011 | INDEXER-A / tenant A / operate | embed → approved A-NOTES version | ALLOW | Workload/capability pin exact version |
| DT-012 | A-OWNER / tenant A | read_audit_metadata → course A | ALLOW | Không gồm raw content/prompt |

### 5.2 Tenant, identity và enumeration deny

| ID | Subject/context | Action → resource | Expected reason |
|---|---|---|---|
| DT-013 | unauthenticated | search → A-NOTES | `authentication_required` |
| DT-014 | A-STUDENT / missing tenant | search → A-NOTES | `tenant_context_required` |
| DT-015 | A-STUDENT / two active tenants | search → A-NOTES | `tenant_context_ambiguous` |
| DT-016 | A-STUDENT / tenant A | read_excerpt → B-NOTES | `access_denied`; không lộ existence |
| DT-017 | B-STUDENT / tenant B | exact-title search → A-NOTES | `access_denied`; 0 candidate A |
| DT-018 | FREE tự khai tenant A | search → A-NOTES | `access_denied`; client tenant không tạo membership |
| DT-019 | A-STUDENT sửa resource ID | view_source → B-NOTES | `access_denied`; generic response |

### 5.3 Lifecycle, sensitivity và separation of duties

| ID | Subject/context | Action → resource | Expected reason |
|---|---|---|---|
| DT-020 | A-STUDENT | search → A-DRAFT | `resource_not_servable` |
| DT-021 | A-STUDENT | read_excerpt → A-STAFF | `access_denied` |
| DT-022 | A-STUDENT | search/use_model → A-EXAM | `resource_not_servable` + sensitivity deny |
| DT-023 | A-LECTURER là editor version | approve → A-DRAFT | `separation_of_duties` |
| DT-024 | A-ADMIN không content grant | read_excerpt → A-NOTES | `access_denied` |
| DT-025 | PLATFORM-ADMIN | download → A-NOTES | `access_denied`; break-glass riêng |
| DT-026 | bất kỳ normal principal | OCR/embed → A-SECRET | `secret_forbidden` |
| DT-027 | INDEXER-A | embed → A-DRAFT chưa admission | `resource_not_servable` |

### 5.4 Agent, capability và dependency deny

| ID | Subject/context | Action → resource | Expected reason |
|---|---|---|---|
| DT-028 | TUTOR-A | export → A-NOTES | `agent_action_not_permitted` |
| DT-029 | TUTOR-A, source prompt yêu cầu | read_excerpt → B-NOTES | `access_denied`; prompt không đổi scope |
| DT-030 | TUTOR-A, model giả resource ID | download → A-NOTES | `agent_action_not_permitted` |
| DT-031 | TUTOR-A capability sai audience | read_excerpt → A-NOTES | `capability_invalid` |
| DT-032 | TUTOR-A capability hết hạn/replay | read_excerpt → A-NOTES | `capability_expired_or_replayed` |
| DT-033 | A-NOTES allow, A-FIGURE relation/version mismatch | expand image | `dependency_access_denied`; không serialize ảnh |
| DT-034 | peer agent gửi context không lineage | use_model_context | `untrusted_tool_result` |

### 5.5 Revocation, cache và time-of-check/time-of-use

| ID | Timeline | Expected sequence |
|---|---|---|
| DT-035 | A-STUDENT retrieve A-NOTES; membership revoke; pre-model check | ALLOW retrieval → DENY pre-model; no model input/cache write |
| DT-036 | Generation xong; material quarantine; pre-delivery check | Earlier ALLOW → DENY delivery; discard buffer/citation |
| DT-037 | Answer đã phát; material revoke; user mở citation | Earlier delivery unaffected → DENY viewer; không thể unsee answer cũ |
| DT-038 | Cache từ A-LECTURER; A-STUDENT query giống hệt | Reject incompatible cache; retrieve lại trong student scope |
| DT-039 | Cache tenant A; B-STUDENT query giống hệt | Reject before hydrate; 0 bytes/content from entry A |
| DT-040 | Vector point version cũ còn sau archive | Candidate prefilter/recheck deny; stale point không vào rank/model |
| DT-041 | Policy store timeout khi đọc protected resource | DENY `policy_unavailable`; không fallback broad cache/index |
| DT-042 | Grant/revoke commit nhưng replica policy cũ | Check yêu cầu minimum revision; không accept stale allow |

### 5.6 External share, privileged flow và audit

| ID | Subject/context | Action → resource | Expected |
|---|---|---|---|
| DT-043 | B-STUDENT có view share | download → A-SHARED-V1 | DENY nếu share chỉ có viewer action |
| DT-044 | người khác dùng forwarded link | view_source → A-SHARED-V1 | DENY recipient mismatch |
| DT-045 | B-STUDENT sau share expiry | view_source → A-SHARED-V1 | DENY expired/revoked |
| DT-046 | PLATFORM-ADMIN có approved break-glass | read_excerpt → exact A resource | ALLOW có step-up, ticket, expiry, alert, audit |
| DT-047 | PLATFORM-ADMIN break-glass wildcard tenant | search/export tenant A | DENY scope quá rộng |
| DT-048 | audit writer thử xóa/sửa audit | mutate audit record | DENY separation of duties/immutability |

### 5.7 Query planning và citation mint

| ID | Subject/context | Action → resource | Expected |
|---|---|---|---|
| DT-049 | TUTOR-A, tool profile/capability current | plan authorized retrieval → A-NOTES | ALLOW; plan chỉ chứa tool/action/scope hẹp |
| DT-050 | TUTOR-A yêu cầu arbitrary URL fetch | plan search → A-NOTES | DENY `agent_action_not_permitted` trước tool execution |
| DT-051 | TUTOR-A, exact evidence lineage/current policy | cite → A-NOTES v3 | ALLOW mint opaque handle; không mang capability |
| DT-052 | TUTOR-A sinh citation tới B-NOTES | cite → B-NOTES | DENY `access_denied`; không mint handle/metadata |

### 5.8 Direct action coverage: discovery và content lifecycle

| ID | Subject/context | Action → resource | Expected |
|---|---|---|---|
| DT-053 | FREE / personal | discover_metadata → PUBLIC-CTDL | ALLOW public metadata đã duyệt |
| DT-054 | B-STUDENT / tenant B | discover_metadata → A-NOTES | DENY generic; không lộ title/existence |
| DT-055 | A-LECTURER / assigned course | upload → A-DRAFT | ALLOW vào quarantine/draft only; scan + provenance obligations |
| DT-056 | A-STUDENT | upload → A-DRAFT | DENY `access_denied` |
| DT-057 | A-LECTURER, own assigned draft | submit_review → A-DRAFT | ALLOW; version immutable khi vào review |
| DT-058 | A-STUDENT | submit_review → A-DRAFT | DENY `access_denied` |
| DT-059 | A-OWNER, approved review, không sửa version | publish → A-DRAFT | ALLOW step-up/audit; backend đổi state/index alias |
| DT-060 | A-LECTURER là editor | publish → A-DRAFT | DENY separation of duties |
| DT-061 | A-OWNER, exact active version | archive → A-NOTES | ALLOW step-up/audit + epoch/index/cache invalidation |
| DT-062 | A-STUDENT | archive → A-NOTES | DENY `access_denied` |

### 5.9 Direct action coverage: share, grant và audit

| ID | Subject/context | Action → resource | Expected |
|---|---|---|---|
| DT-063 | A-OWNER, named B recipient/exact v3/view-only/expiry | share → A-NOTES | ALLOW sau step-up + external-share approval/audit |
| DT-064 | A-LECTURER không share grant | share → A-NOTES | DENY `access_denied` |
| DT-065 | A-ADMIN, exact membership change | manage_grants → A-MEMBERSHIP-POLICY | ALLOW control plane, step-up/audit; không cấp content access cho admin |
| DT-066 | TUTOR-A/model request | manage_grants → A-MEMBERSHIP-POLICY | DENY `agent_action_not_permitted` |
| DT-067 | A-ADMIN | read_audit_content → A-AUDIT | DENY; org admin không mặc định là security auditor |
| DT-068 | A-SECURITY-AUDITOR, exact incident/ticket | read_audit_content → A-AUDIT | ALLOW step-up, redaction, no-export và audit-of-audit |

### 5.10 Direct action coverage: transform, OCR và index

| ID | Subject/context | Action → resource | Expected |
|---|---|---|---|
| DT-069 | INDEXER-A, exact admitted v3 | transform → A-NOTES | ALLOW single-tenant/version-pinned |
| DT-070 | INDEXER-A, exact admitted v3 | ocr → A-NOTES | ALLOW approved local/provider route theo sensitivity |
| DT-071 | INDEXER-A, exact admitted v3 | index → A-NOTES | ALLOW staging index; publish alias vẫn là action khác |
| DT-072 | INDEXER-A | index → A-DRAFT | DENY `resource_not_servable` |
| DT-073 | INDEXER-A | ocr → A-SECRET | DENY `secret_forbidden`; 0 OCR/provider sink |
| DT-074 | INDEXER-A capability tenant A | transform → B-NOTES | DENY tenant/capability mismatch |

### 5.11 Dependency expansion variants

| ID | Timeline/dependency | Expected |
|---|---|---|
| DT-075 | A-STUDENT expands A-TABLE bound to current A-NOTES v3 | ALLOW dependency with lineage |
| DT-076 | A-STUDENT expands A-HIDDEN-ANSWER under allowed parent | DENY child sensitivity; parent allow không truyền qua |
| DT-077 | TUTOR-A attempts B-NOTES as comparison dependency | DENY tenant mismatch; no partial serialization of B |
| DT-078 | A-TABLE allow at retrieval; parent A-NOTES quarantined before expansion | ALLOW earlier → DENY expansion at current epoch |

### 5.12 Cache variants

| ID | Cache condition | Expected |
|---|---|---|
| DT-079 | Same subject/tenant/action/purpose/policy/epoch/snapshot/dependencies | ALLOW hydrate, rồi vẫn pre-delivery recheck |
| DT-080 | Same user/query nhưng cache policy epoch cũ | DENY hydrate `cache_stale_authorization` |
| DT-081 | Scope current nhưng một dependency version stale | DENY toàn entry; retrieve/repack lại |
| DT-082 | Cache packet trộn PUBLIC-CTDL + A-NOTES, FREE query public | DENY hydrate packet; recompute public-only |
| DT-083 | Semantic-similar FREE query va vào cache tenant A | DENY trước deserialize/hydrate |
| DT-084 | Cache entry thiếu dependency lineage | DENY `cache_lineage_missing`; không đoán compatibility |

### 5.13 Upload quarantine và indirect injection

| ID | Scenario | Expected |
|---|---|---|
| DT-085 | A-LECTURER upload submission mới | ALLOW receipt + tenant quarantine blob; DENY direct content DB/serving index |
| DT-086 | Student/agent search submission đang quarantine | DENY; 0 candidate/model/viewer visibility |
| DT-087 | Uploaded file chứa visible indirect tool/export instruction | DENY promotion; security quarantine |
| DT-088 | Render/OCR khác text layer, hidden/tiny/off-page instruction | DENY promotion; manual security review |
| DT-100 | PDF có active content/JS/embedded launch/bomb signal | DENY transform/parser/provider; giữ/reject quarantine |
| DT-101 | Injection không bị detector bắt nhưng source đã publish | Tool action ngoài capability vẫn DENY; source không thành instruction |

### 5.14 Exact/near duplicate và hai uploader

| ID | Scenario | Expected |
|---|---|---|
| DT-089 | Hai lecturer cùng tenant upload exact raw hash | Hai receipts/provenance, tối đa một raw blob; không tạo serving duplicate |
| DT-090 | Tenant B upload cùng raw hash tenant A | ALLOW quarantine độc lập; không báo tồn tại/canonical ID tenant A |
| DT-091 | Khác container/metadata nhưng normalized content hash bằng nhau | Tạo exact-content cluster, chờ reviewer; không auto publish |
| DT-092 | Khác vài ký tự | Near-duplicate flag + character/token/section diff; không auto merge |
| DT-093 | Near-duplicate delta thêm hidden/tool/exfiltration instruction | DENY promotion; poisoned-delta quarantine |
| DT-094 | Hai upload exact đồng thời | Idempotent reservation: 2 receipts, ≤1 tenant blob write |
| DT-095 | Near duplicate là bản sửa hợp lệ | Reviewer tạo immutable new version + `supersedes` |
| DT-096 | Hai giáo viên có biến thể học thuật hợp lệ | Giữ separate variants theo lecturer/course/term sau owner approval |
| DT-097 | Cùng title nhưng nội dung khác | Không merge; tạo material riêng sau review |
| DT-098 | Agent/uploader tự chọn canonical hoặc merge | DENY `resolve_duplicate` |
| DT-099 | Exact duplicate nhưng uploader thiếu rights | Không kế thừa rights/review/published state; DENY promotion |
| DT-102 | Upload response gặp confidential duplicate | Trả generic receipt/status; không lộ material/title/uploader tồn tại |

## 6. Required obligations

ALLOW không phải lúc nào cũng đồng nghĩa trả raw content:

| Condition | Obligation |
|---|---|
| privileged action | step-up + reason/ticket + detailed audit |
| assessment/staff/PII | no-cache hoặc tenant-encrypted short cache; no external provider nếu policy cấm |
| external share | watermark, recipient/version/expiry binding, viewer reauth |
| no-download resource | source viewer only; không phát raw storage URL |
| model-context allowed with redaction | redact trước serialization; trace cả source và derived representation |
| bulk export | separate approval, manifest, max-volume/rate and destination restriction |

Consumer không thực hiện được obligation thì phải deny.

## 7. Conflict rules cần review

1. User vừa là lecturer/editor vừa là course owner: deny approve exact version mình đã sửa; có thể approve version khác nếu policy cho.
2. Public material bị quarantine: quarantine thắng public/published.
3. Explicit user deny và group allow đồng thời: deny thắng.
4. Share allow nhưng tenant data-residency/export policy deny: deny thắng.
5. User allow nhưng agent/tool profile deny: deny thắng.
6. Capability allow nhưng relation/epoch đã đổi: current policy deny thắng.
7. Parent allow nhưng child sensitivity cao hơn: child được kiểm riêng.
8. Multiple tenant memberships: chỉ relation của active tenant được xét; không union.

## 8. Freeze/change control

V0.1 chỉ được freeze sau human review. Mọi thay đổi expected outcome phải:

- ghi reason và threat/usability impact;
- cập nhật đồng thời decision table, entities/cases và protocol nếu mẫu số đổi;
- tăng `policy_version` và `fixture_snapshot_id`;
- không sửa expected output chỉ để làm implementation đang test pass.
