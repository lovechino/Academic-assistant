# Authorization E0 — fixture lint và coverage review

Ngày chạy: 2026-09-05

Kết luận: **structural lint pass; policy review và runtime evaluation chưa chạy**.

## 1. Input

- policy oracle: [decision table v0.1](../governance/04-authorization-policy-decision-table-v0.1.md);
- fixture snapshot: `authorization-synthetic-v0.1-2026-09-05`;
- [manifest](../../data/evaluation/synthetic/authorization-v0.1/manifest.json), [entities](../../data/evaluation/synthetic/authorization-v0.1/entities.json), [cases](../../data/evaluation/synthetic/authorization-v0.1/cases.jsonl);
- protocol: [authorization security evaluation v0.1](18-authorization-security-evaluation-protocol-v0.1.md).

Không dùng model, policy engine, database, vector index, cache, PDF hoặc user/tenant thật.

## 2. Việc đã kiểm

- JSON parse được cho manifest/entities và từng JSONL case;
- case/decision IDs khớp tuần tự DT-001..DT-052;
- manifest counts khớp parsed counts;
- không trùng case ID;
- principal, agent/workload, tenant và resource references đều tồn tại trong fixture;
- stage thuộc registry 12 checkpoint;
- metric thuộc AUTH-01..AUTH-14;
- mỗi checkpoint có expected ALLOW/DENY, reason và unauthorized-exposure oracle;
- mọi expected unauthorized-exposure list rỗng.

## 3. Kết quả

| Mục | Kết quả |
|---|---:|
| Cases | 52 |
| Decision checkpoints | 56 |
| Expected ALLOW | 19 |
| Expected DENY | 37 |
| Threat/behavior families | 27 |
| Principal entities | 10 |
| Resource entities | 11 |
| Distinct request actions | 12 |
| Enforcement stages | 12/12 có ít nhất một case |
| AUTH metric IDs | 14/14 được gắn vào ít nhất một case |
| Duplicate/unknown/missing-oracle issues | 0 |

Machine-readable historical result: [validation-e0-52.json](../../data/evaluation/synthetic/authorization-v0.1/validation-e0-52.json). Working fixture sau báo cáo này đã được mở rộng; xem [E0.1 action-expansion review](20-authorization-e01-action-expansion-review.md) cho số liệu hiện hành.

### Stage distribution

| Stage | Checkpoints |
|---|---:|
| request admission | 12 |
| query planning | 2 |
| candidate retrieval | 7 |
| dependency expansion | 1 |
| model context serialization | 5 |
| tool execution | 6 |
| cache hydrate/write | 2 |
| pre-delivery | 2 |
| citation mint | 2 |
| source view/download | 8 |
| ingest/index publish | 3 |
| share/export/privileged action | 6 |

### Metric tagging distribution

| Metric | Cases tagged |
|---|---:|
| AUTH-01 cross-tenant | 10 |
| AUTH-02 unauthorized exposure | 35 |
| AUTH-03 checkpoint coverage | 30 |
| AUTH-04 retrieval prefilter | 5 |
| AUTH-05 stale authorization | 6 |
| AUTH-06 cache isolation | 2 |
| AUTH-07 agent/tool bypass | 8 |
| AUTH-08 secret admission | 3 |
| AUTH-09 audit completeness | 7 |
| AUTH-10 revocation latency | 5 |
| AUTH-11 policy latency | 1 |
| AUTH-12 false deny | 16 |
| AUTH-13 enumeration | 5 |
| AUTH-14 privileged workflow | 7 |

Đây là **metric routing coverage**, không phải metric values. Ví dụ AUTH-11 có một denominator candidate nhưng chưa có latency sample.

## 4. Gap đã tìm thấy và xử lý ngay

Audit đầu tiên có 48 case/52 checkpoint, nhưng thiếu hoàn toàn `query_planning`, `citation_mint` và không case nào route tới AUTH-11. Đã bổ sung:

- DT/AUTHZ-049: allowed query plan cho brokered retrieval;
- DT/AUTHZ-050: deny arbitrary URL-fetch plan;
- DT/AUTHZ-051: allowed citation mint với exact lineage/version;
- DT/AUTHZ-052: deny citation sang tenant khác;
- AUTH-11 route vào positive query-planning checkpoint.

Sau bổ sung, registry stage và metric đạt 12/12, 14/14 ở mức có đại diện.

## 5. Gap còn lại trước khi freeze

E0 chưa pass content/policy review vì:

1. Chưa có reviewer xác nhận 52 expected decisions, nhất là break-glass, external share và separation of duties.
2. Stage coverage không đồng nghĩa full cross-product. `dependency_expansion` mới có 1 case; cache mới 2 case.
3. Các action sau chưa có direct case riêng: `discover_metadata`, `transform`, `ocr`, `index`, `upload`, `submit_review`, `publish`, `archive`, `share`, `manage_grants`, `read_audit_content`.
4. Chưa có hidden adversarial split; toàn bộ hiện là development specification.
5. AUTH-10/11 chưa có timestamps/runtime nên không có p50/p95/p99.
6. Chưa kiểm semantic consistency bằng policy evaluator; lint chỉ biết references/schema và coverage tags.

## 6. Quyết định E0

```text
structure/reference lint: PASS
stage/metric representative coverage: PASS
human policy-oracle review: PENDING
full action/cross-product coverage: PENDING
runtime authorization/enforcement: NOT RUN
overall: CONTINUE E0, NOT READY FOR E1
```

## 7. Bước tiếp theo

- mở rộng direct action cases và parent/image/table/cache variants;
- review lần lượt 19 ALLOW trước, rồi 37 DENY để tránh “deny-all” và false deny;
- chốt conflict rules/obligations;
- tạo hidden adversarial split;
- freeze snapshot mới, sau đó mới viết pure policy evaluator spike E1.

Không chọn policy engine hoặc gọi đây là security pass trước các bước trên.
