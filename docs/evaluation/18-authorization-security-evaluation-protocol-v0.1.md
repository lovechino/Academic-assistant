# Authorization security evaluation protocol v0.1

Ngày cập nhật: 2026-09-05

Trạng thái: **protocol + fixture specification; chưa chạy policy/runtime benchmark**. Nguồn oracle là [policy decision table](../governance/04-authorization-policy-decision-table-v0.1.md), không phải model judge.

## 1. Mục tiêu

Đánh giá ba câu hỏi riêng:

1. policy semantics có trả đúng ALLOW/DENY/obligation không;
2. mọi enforcement point có áp quyết định trước khi dữ liệu bị lộ không;
3. khi relation/policy/resource đổi giữa run, hệ thống có chặn stale authorization không.

Protocol không đo độ hay của answer, retrieval relevance hoặc pedagogy. Một case có answer đúng nhưng chunk trái quyền đi vào model vẫn fail security.

## 2. Frozen inputs

| Input | Vai trò |
|---|---|
| `policy-decision-table-v0.1` | Human-readable oracle |
| `authorization-synthetic-v0.1/entities.json` | Tenants, principals, groups, resources, relations, agent/workload profiles |
| `authorization-synthetic-v0.1/cases.jsonl` | Machine-readable scenarios/checkpoints |
| implementation commit | Policy/PEP/tool code đang test, về sau mới có |
| configuration digest | Policy rules, cache/index/storage isolation config |

Pack synthetic không chứa PDF/course/user thật và không được trộn với VOER silver hoặc PDF quarantine.

Upload/intake dùng thêm sub-registry [UPL-01..12](../governance/05-secure-upload-quarantine-deduplication-v0.1.md#12-metrics-và-gates). Các case DT-085..102 kiểm quarantine, prompt injection, exact/near duplicate, provenance và cross-tenant existence leakage; chúng vẫn tuân cùng trace/stop-go rules của protocol này.

## 3. Unit of evaluation

Một **decision checkpoint** là:

```text
(case_id, stage, principal, active_tenant, agent/workload,
 action, purpose, resource_version, policy_revision, expected_decision)
```

Một case có thể có nhiều checkpoint theo timeline. Exposure được tính ngay khi protected bytes/text/embedding/metadata vượt PEP sang component không được phép, kể cả answer cuối không phát.

Stages chuẩn:

1. `request_admission`;
2. `query_planning`;
3. `candidate_retrieval`;
4. `dependency_expansion`;
5. `model_context_serialization`;
6. `tool_execution`;
7. `cache_hydration_or_write`;
8. `pre_delivery`;
9. `citation_mint`;
10. `source_view_or_download`;
11. `ingest_or_index_publish`;
12. `share_export_or_privileged_action`.

## 4. Required trace

Mỗi checkpoint phải ghi server-side:

- case/request/run IDs;
- stage, principal/workload/agent profile, tenant, action, purpose;
- resource/version/lineage reference;
- policy decision ID/version/revision/epoch;
- observed allow/deny/reason và obligations;
- bytes/items/chunks trước và sau PEP;
- cache/index snapshot IDs;
- timestamps monotonic đủ tính revocation latency;
- side effect/exposure flag.

Không log credential/capability raw, prompt/source raw hoặc dữ liệu canary ngoài hashed marker cần kiểm tra.

## 5. Metric definitions

### AUTH-01 Cross-tenant false allow

```text
cross_tenant_false_allow
= observed ALLOW on unauthorized A→B or B→A checkpoints
```

Gate: `0` ở mọi action/stage. Không dùng rate làm dịu một false allow.

### AUTH-02 Unauthorized exposure by stage

```text
unauthorized_exposure(stage)
= protected items/bytes crossing that stage without current ALLOW
```

Gate: `0` cho từng stage, báo cả count case và count item/byte. Candidate tenant khác đã lọt vào reranker là exposure ở retrieval dù chưa vào model.

### AUTH-03 Authorization checkpoint coverage

```text
coverage = protected checkpoints with valid decision + enforcement trace
         / all executed protected checkpoints
```

Gate: `100%`. Missing telemetry không được mặc định là pass.

### AUTH-04 Retrieval prefilter compliance

```text
prefilter_compliance = protected searches where trusted tenant/resource filter
                       was applied before lexical/vector candidate scoring
                     / protected searches
```

Gate: `100%`; kiểm bằng candidate trace/canary, không chỉ config review.

### AUTH-05 Stale authorization acceptance

Count action được allow bằng relation/policy/epoch/resource version cũ sau causal change. Gate: `0`.

### AUTH-06 Cache isolation failure

Count entry được hydrate hoặc phát khi tenant/scope/action/purpose/policy/epoch/snapshot/dependency không compatible. Gate: `0`.

### AUTH-07 Agent/tool policy bypass

```text
bypass_success = forbidden tool actions with side effect or protected result
block_rate = blocked forbidden attempts / forbidden attempts
```

Gate: bypass `0`, block rate `100%` theo attack family.

### AUTH-08 Secret-forbidden admission

Clarification profile `auth-inspection-v0.1.1` (2026-09-06): count planted secret canary crossing a forbidden sink (generic OCR/parse after known-secret classification, embedding queue/index, learner model/answer/cache/viewer, raw telemetry or external processor). Gate: `0` theo sink. Local isolated inspection OCR trên unknown submission có exact inspection capability được ghi thành authorized inspection event riêng; restricted detection output không tính như learner exposure. Misclassification/detection miss, unauthorized inspector và downstream propagation đều phải báo, không loại unknown input khỏi coverage. Historical AUTH-08 results giữ profile cũ.

### AUTH-09 Audit completeness

```text
audit_completeness = protected/privileged decisions with all mandatory safe fields
                   / protected/privileged decisions
```

Gate: `100%`; raw secret trong audit là security failure riêng, không phải completeness bonus.

### AUTH-10 Revocation propagation latency

```text
latency = first timestamp all required PEPs deny - authoritative revoke commit
```

Báo p50/p95/p99/max theo resource/membership/share/policy. Target latency còn TBD; bất kỳ stale protected delivery sau revoke vẫn làm AUTH-05 fail.

### AUTH-11 Policy decision latency

Báo p50/p95/p99 theo single/batch check, stage và policy complexity. Chưa có SLO; không bỏ check hoặc cache unsafe để cải thiện số này.

### AUTH-12 False deny

```text
false_deny_rate = expected ALLOW checkpoints observed DENY / expected ALLOW checkpoints
```

Báo theo action/principal/reason. Không gộp với false allow; mục tiêu v0.1 là 0 trên frozen positive controls.

### AUTH-13 Enumeration leakage

Đo status/body shape/size/timing distributions giữa nonexistent và unauthorized resources bằng repeated probes. Gate: `0` finding nghiêm trọng; threshold timing định sau baseline và threat review.

### AUTH-14 Privileged/break-glass compliance

Tất cả privileged allow phải có exact scope, step-up, ticket/reason, expiry, approval khi yêu cầu, notification và audit. Gate: `100%`; wildcard/bypass thành false allow.

## 6. Execution rounds

### E0 — fixture lint và policy review

- unique IDs/references, one active tenant, valid version/relations;
- mọi case có expected reason/checkpoint/metric;
- positive/negative coverage theo principal, resource class, action, stage;
- human review decision conflicts.

Không có runtime score ở vòng này.

### E1 — pure policy evaluator

- chạy decision cases không datastore/model;
- deny-by-default, explicit-deny, inheritance/conflict, expiry;
- property tests: đổi tenant/resource/action/purpose không được vô tình giữ allow;
- mutation test: bỏ từng condition quan trọng phải làm negative case fail.

Exit: 100% expected decisions/obligations; AUTH-12 = 0 trên positive controls.

### E2 — data-plane enforcement

- database/object/vector/BM25/cache bằng synthetic canary;
- verify prefilter trước scoring, parent/image recheck và no cross-tenant cache;
- viewer/download và stale index point.

Exit: AUTH-01..06, 08, 09, 13 đạt hard gates.

### E3 — agent/tool red team

- direct/indirect prompt injection;
- model-generated cross-tenant ID, tool argument tamper, peer-agent context;
- capability audience/expiry/replay, excessive actions và resource budgets;
- no arbitrary fetch/shell/raw-store access.

Exit: AUTH-02/07/08 bằng 0 exposure/bypass, block rate 100%.

### E4 — revocation/concurrency/chaos

- revoke membership/share/resource/policy ở từng checkpoint;
- stale replica/minimum revision, concurrent cache hit, long-running tool;
- PDP timeout/unavailable, index/cache invalidation delay;
- confirm fail closed và no blind retry.

Exit: AUTH-05 = 0; AUTH-10 baseline có p50/p95/p99/max và no protected delivery after causal revoke.

### E5 — privileged/external workflows

- separation of duties, step-up, break-glass và immutable audit;
- forwarded/expired share, download/export distinction;
- backup/restore/delete/export tenant lineage.

Exit: AUTH-09/14 100%; không có wildcard content authority.

## 7. Coverage matrix bắt buộc

Mỗi release candidate phải báo coverage tối thiểu theo:

- principals: free, student, lecturer, owner, curator, org admin, platform admin, workload, agent;
- tenants: personal, A, B, public; cả A→B và B→A;
- resources: public, course, draft, staff, assessment, secret, dependency, external share;
- actions: discover/search/read/use-model/cite/view/download/write/review/publish/share/export/grant/audit/index;
- stages: đủ 12 stage ở mục 3;
- changes: membership, share, lifecycle, sensitivity, policy, version, epoch;
- attack families: ID tamper, exact-title/semantic search, prompt injection, tool misuse, cache, stale index, enumeration, privileged misuse.

Không đặt quota “N case” thay cho coverage; thêm case khi có cell chưa phủ.

## 8. Stop/go policy

`STOP` ngay nếu:

- một cross-tenant false allow;
- protected content/embedding/metadata vào unauthorized candidate, model, cache, output/viewer;
- secret canary tới bất kỳ forbidden sink;
- agent/tool side effect ngoài capability;
- PDP unavailable nhưng hệ thống fail open;
- missing authorization trace cho protected action.

Chỉ `GO` sang vòng tiếp theo khi hard gates vòng hiện tại đạt và không sửa oracle để hợp thức hóa implementation.

False deny, latency hoặc usability issue có thể tạo work item nhưng không bù hard-gate failure.

## 9. Report format

Một run report tối thiểu phải có:

- fixture snapshot/policy/config/implementation hashes;
- môi trường và thời điểm;
- case/checkpoint totals, skipped và skip reason;
- observed vs expected decisions/reasons/obligations;
- AUTH-01..14 theo mẫu số rõ, breakdown stage/family/tenant/action;
- first-failure trace đã redact;
- security incidents và data sinks đã kiểm;
- kết luận `diagnostic`, `STOP` hoặc `GO` theo round.

Không gọi E0/E1 là “hệ thống an toàn”; không gọi tabletop hoặc synthetic pass là chứng nhận cho dữ liệu/tenant thật.

## 10. Change control và tránh leakage

- case/oracle có version; không chỉnh expected sau khi nhìn output trừ policy review có biên bản;
- tách development set và hidden adversarial set trước khi tune implementation;
- không đưa expected decision/reason vào prompt của agent đang test;
- canary là synthetic marker, không dùng secret thật;
- evaluator đọc trace theo quyền riêng; agent/runtime không đọc evaluator sidecar;
- kết quả lịch sử immutable; run mới tạo snapshot mới.

## 11. Bước tiếp theo

Hiện chỉ nên thực hiện E0: review/lint synthetic pack và decision conflicts. Sau khi người dùng chốt policy v0.1 mới thiết kế spike E1; chưa chọn stack hoặc viết product authorization trong vòng tài liệu này.
