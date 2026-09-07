# Chỉ mục chương trình phân quyền và bảo mật agent

Ngày cập nhật: 2026-09-05

Trạng thái tổng thể: **đang ở pha thiết kế + synthetic specification; chưa có authorization runtime, policy engine hoặc security certification**.

## 1. Cách đọc

Đọc theo thứ tự sau để không nhầm vai trò, policy và implementation:

1. [Permission matrix v0.1](01-permission-matrix.md) — các logical role/action ban đầu.
2. [Document lifecycle v0.1](02-document-lifecycle.md) — trạng thái admission/publish/revoke của học liệu.
3. [Multi-tenant Zero Trust authorization v0.1](03-multi-tenant-zero-trust-authorization.md) — threat model, trust boundary, tenant isolation và agent security.
4. [Authorization context contract v0.1](../../contracts/authorization-context.md) — boundary Backend → AI/tool và authorization trace.
5. [Policy decision table v0.1](04-authorization-policy-decision-table-v0.1.md) — oracle ALLOW/DENY độc lập implementation.
6. [Authorization security evaluation protocol v0.1](../evaluation/18-authorization-security-evaluation-protocol-v0.1.md) — cách chạy, metric, gate và báo cáo.
7. [Synthetic authorization pack v0.1](../../data/evaluation/synthetic/authorization-v0.1/README.md) — entities/cases local, không chứa dữ liệu thật.
8. [E0 fixture lint và coverage review](../evaluation/19-authorization-e0-fixture-review.md) — kết quả 52-case ban đầu và gap phát hiện.
9. [E0.1 action/dependency/cache expansion](../evaluation/20-authorization-e01-action-expansion-review.md) — 84 case/90 checkpoint hiện hành và 12 policy proposal cần review.
10. [Secure upload/quarantine/dedup](05-secure-upload-quarantine-deduplication-v0.1.md) — intake boundary, indirect injection và hai uploader trùng/gần trùng tài liệu.
11. [E0.2 upload/dedup review](../evaluation/21-authorization-e02-upload-dedup-review.md) — DT-085..102, UPL-01..12 và các quyết định U-01..U-12.
12. [Duplicate detection labeled mini-set E0.3](../evaluation/22-duplicate-detection-labeled-mini-set-v0.1.md) — 26 synthetic pairs để review class/security/resolution trước detector experiment.
13. [Synthetic PDF duplicate/security fixtures E0.4](../evaluation/23-synthetic-pdf-duplicate-fixtures-e0.4.md) — 10 PDF cho byte/content/visual/hidden/image/OCR-layer diagnostics; chưa chạy detector threshold.
14. [PDF relation coverage E0.5](../evaluation/24-pdf-relation-coverage-e0.5.md) — thêm 24 PDF/28 trang cho 12 relation còn thiếu, structural/visual diagnostics trước detector.
15. [Deterministic dedup baselines E0.6](../evaluation/25-deterministic-dedup-baselines-e0.6.md) — matched image/OCR relations, candidate recall và canonical auto-link security counterexample.
16. [BGE-M3 duplicate ablation E0.7](../evaluation/26-bge-m3-duplicate-ablation-e0.7.md) — dense candidate recall, MinHash union load và counterexample bác bỏ global dense threshold.
17. [Hard-negative routing E0.8](../evaluation/27-hard-negative-routing-e0.8.md) — 24 hard negatives, candidate review load và exact-first route không trao quyền merge/publish.
18. [Equivalence/conflict triplets E0.9](../evaluation/28-equivalence-conflict-triplets-e0.9.md) — similarity ưu tiên conflicting near-copy 12/12; giữ source/claim riêng và cấm collapse/auto-equivalence.

## 2. Artifact map

| Artifact | Câu hỏi nó trả lời | Trạng thái | Không được hiểu là |
|---|---|---|---|
| Permission matrix | Role logic nào có action nào? | Draft | Runtime RBAC |
| Lifecycle | Version nào có thể phục vụ? | Draft | Workflow đã chạy |
| Zero Trust blueprint | Kiểm quyền ở đâu và chống threat nào? | Draft để review | Security certification |
| Authorization contract | Component trao trusted context thế nào? | Logical contract | Token/API schema đã đóng |
| Decision table | Với fixture cụ thể phải allow/deny ra sao? | Frozen candidate v0.1 | Kết quả test |
| Evaluation protocol | Đo AUTH-01..14 và stop/go thế nào? | Ready cho review | Test runner |
| Synthetic pack | Input/oracle không có dữ liệu thật | 102 case/110 checkpoint; E0.2 lint pass | Gold được chuyên gia duyệt |
| E0/E0.1/E0.2/E0.3/E0.4 reports | Referential/stage/action/upload/dedup metric coverage và gap | Structural/fixture diagnostics pass; detector chưa chạy | Runtime security result |
| Tabletop cũ | Mô phỏng state/permission tuần tự | Đã chạy synthetic | Concurrency/runtime proof |

## 3. Những invariant đã chốt

- Một request/agent run có đúng một active tenant.
- Không có implicit trust; thiếu policy input là deny.
- Effective allow = RBAC ∩ ReBAC ∩ ABAC ∩ current capability, sau đó explicit deny thắng.
- Admin control plane không mặc định đọc content plane.
- Agent không phải Policy Decision Point và không có datastore credential rộng.
- Search filter quyền trước ranking; recheck dependency trước model/delivery/viewer.
- Citation, cache key, opaque ID và prompt không phải authorization mechanism.
- Embedding/OCR/image/cache/memory kế thừa sensitivity và lineage của source.
- `secret_forbidden` không được OCR/embed/index/model-context.
- False allow hoặc unauthorized exposure có gate bằng 0 ở từng stage.

## 4. Quyết định đang provisional

- taxonomy role/sensitivity/action/purpose v0.1;
- uploader không approve chính version mình sửa;
- external share đích danh, có expiry, viewer reauth và không tự cho download;
- answer học thuật được buffer đến final authorization gate;
- policy/cache dùng authorization epoch và resource version;
- free user có personal tenant, public catalog và own resources.

Các điểm này có thể đổi sau tabletop/review nhưng phải đổi decision table và tăng fixture version cùng lúc.

## 5. Chưa chọn

- policy engine/relation store;
- database/vector/object-store product;
- capability encoding hoặc token format;
- exact API/OpenAPI schema;
- shared/dedicated data-plane threshold;
- revocation/authorization latency SLO;
- IdP/vendor/federation topology;
- streaming protocol cho content đã authorize.

Không được chọn stack trước khi decision table và negative test coverage được review, vì như vậy dễ khóa policy theo giới hạn của một sản phẩm.

## 6. Roadmap thực hiện

| Phase | Artifact/việc làm | Exit gate |
|---|---|---|
| G0 — hiện tại | Blueprint, contract, decision table, synthetic pack, protocol | Link/integrity pass; policy conflict đã ghi |
| G1 | Human review policy + threat coverage | Expected ALLOW/DENY được owner ký; version frozen |
| G2 | Pure policy evaluator spike, chưa AI | 100% decision cases pass; deny-by-default/property tests |
| G3 | Datastore/index/cache PEP integration | AUTH-01..06, 09, 13 đạt gate |
| G4 | Agent capability + brokered tools | AUTH-02/07/08 đạt; prompt injection không vượt PEP |
| G5 | Revocation/concurrency/chaos + viewer/export | AUTH-05/10 và fault cases đạt |
| G6 | Một tổ chức pilot, dữ liệu đã duyệt | Security review + incident drill; vẫn chưa suy rộng đa trường |

## 7. Bước kế tiếp sau tài liệu này

1. Review các case ALLOW trước để tránh policy quá chặt gây false deny.
2. Review toàn bộ case DENY theo từng stage và bổ sung threat bị thiếu.
3. Chốt conflict rules và sensitivity vocabulary.
4. Freeze `authorization-v0.1` thành input cho spike G2.
5. Chỉ sau đó mới so sánh các hướng policy engine bằng cùng một oracle.

Mọi kết quả về sau phải trỏ `policy_version`, `fixture_snapshot_id` và implementation commit; không ghi chung chung “phân quyền đã pass”.
