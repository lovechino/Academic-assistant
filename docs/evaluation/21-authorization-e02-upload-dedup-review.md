# Authorization E0.2 — upload quarantine và duplicate review

Ngày chạy: 2026-09-05

Kết luận cập nhật: **upload/dedup specification và metric routing pass; U-01..U-12 được người dùng chấp thuận ngày 2026-09-05; runtime not run**.

## 1. Thay đổi quyết định

R-01 được làm chặt hơn:

```text
upload
  -> minimal receipt/hash/state in quarantine registry
  -> immutable raw blob in tenant quarantine storage
  -> static scan
  -> sandbox parse (no network/tools)
  -> duplicate fingerprint/diff
  -> security + rights + content review
  -> staging content DB/index
  -> backend publish gate
  -> serving DB/index
```

Không có đường `upload -> content DB/serving index`. Quarantine registry chỉ giữ metadata tối thiểu phục vụ audit, idempotency, hash/race và deletion; nó không phải knowledge/content database.

Policy đầy đủ: [secure upload, quarantine và duplicate resolution](../governance/05-secure-upload-quarantine-deduplication-v0.1.md).

## 2. Case DT-085..DT-102

| IDs | Case review |
|---|---|
| 085–086 | Upload chỉ tạo receipt/quarantine blob; submission không thấy ở retrieval/model/viewer |
| 087–088 | Visible và hidden/multimodal indirect prompt injection chặn promotion |
| 089 | Hai lecturer cùng tenant upload exact hash: hai provenance, tối đa một blob |
| 090 | Cùng hash khác tenant: xử lý độc lập, không lộ existence |
| 091–092 | Normalized duplicate và near duplicate vài ký tự: cluster + diff + human review |
| 093 | Vài ký tự khác chính là hidden/tool/exfiltration instruction: security quarantine |
| 094 | Concurrent exact upload: idempotent reservation và đủ hai receipts |
| 095–097 | Phân biệt new revision, legitimate lecturer variant và unrelated title collision |
| 098–099 | Agent không merge; duplicate không kế thừa rights/published state |
| 100 | Active PDF/embedded payload/resource bomb bị chặn trước parser/provider |
| 101 | Nếu detector bỏ sót, runtime tool PEP vẫn chặn instruction từ source |
| 102 | Upload response không lộ confidential duplicate/canonical material |

## 3. Kết quả fixture sau E0.2

| Mục | E0.1 | E0.2 |
|---|---:|---:|
| Cases | 84 | 102 |
| Decision checkpoints | 90 | 110 |
| Expected ALLOW | 34 | 45 |
| Expected DENY | 56 | 65 |
| All-ALLOW cases | 28 | 37 |
| Families | 31 | 47 |
| Principal entities | 11 | 15 |
| Resource entities | 14 | 20 |
| Direct request actions | 23 | 26 |
| AUTH metrics represented | 14/14 | 14/14 |
| UPL metrics represented | — | 12/12 |
| Reference/count/schema issues | 0 | 0 |

Machine-readable result: [validation.json](../../data/evaluation/synthetic/authorization-v0.1/validation.json).

## 4. Duplicate resolution oracle

| Input relation | Auto action | Human decision required | Serving outcome |
|---|---|---|---|
| Same tenant + same raw hash | Reuse/reserve tenant blob; create receipt | Link/canonical identity nếu cần | Không tạo serving duplicate |
| Same normalized content | Create exact-content cluster | Exact duplicate/new rights context | Chưa serve |
| Near duplicate/few-character delta | Create candidate + diff/risk report | New version/variant/unrelated/quarantine | Chưa serve |
| Same title only | Không merge | Owner confirms identity | Separate by default |
| Same hash cross tenant | Không expose/global-link | Tenant-local review | Separate security context |
| Poisoned/hidden delta | Security quarantine | Security reviewer | Không serve |

Không có similarity threshold tự động quyết định merge/publish ở v0.1.

## 5. Upload metrics UPL-01..12

| Metric | Case tags | Gate/trạng thái |
|---|---:|---|
| UPL-01 upload-to-serving bypass | 4 | Gate 0; chưa chạy runtime |
| UPL-02 quarantine visibility | 2 | Gate 0; chưa chạy runtime |
| UPL-03 forbidden file reaches parser/provider/index | 4 | Gate 0; chưa chạy runtime |
| UPL-04 exact duplicate recall | 2 | Target 100% exact hash fixture |
| UPL-05 near-duplicate recall/precision | 2 | Threshold TBD sau labeled set |
| UPL-06 false merge | 4 | Gate 0 critical variants/title collision |
| UPL-07 poisoned-delta promotion | 4 | Gate 0 |
| UPL-08 provenance completeness | 7 | Target 100% |
| UPL-09 concurrent duplicate blob writes | 1 | ≤1 tenant blob/hash, đủ receipts |
| UPL-10 cross-tenant existence leakage | 2 | Gate 0 |
| UPL-11 review queue/time | 1 | Runtime operational metric, chưa có value |
| UPL-12 post-approval injection tool success | 1 | Gate 0 |

Các số “case tags” chỉ là metric routing, không phải measured scores.

## 6. Những điểm cần người dùng review

Review outcome: **12/12 proposal accepted**. Bảng dưới được giữ như decision record; chưa chứng minh control đã được triển khai.

| Ref | Proposal hiện tại | Review question |
|---|---|---|
| U-01 | Raw blob chỉ ở tenant quarantine storage | Có đồng ý tách hẳn khỏi content DB/serving index? |
| U-02 | Quarantine registry chỉ giữ receipt/hash/state/audit | Có cần thêm metadata nào trước parse không? |
| U-03 | Dedup mặc định chỉ trong tenant | Có chấp nhận tốn storage để tránh cross-tenant leakage? |
| U-04 | Blob reuse nhưng giữ submission của từng giáo viên | Có cần hiển thị mọi uploader cho Course Owner? |
| U-05 | Near duplicate không auto merge/publish | Có đồng ý luôn yêu cầu human review? |
| U-06 | Hai lecturer variants có thể cùng tồn tại | Có cần một bản được gắn `course_authoritative`? |
| U-07 | Duplicate không kế thừa rights/review/published state | Có đồng ý reviewer kiểm rights riêng từng submission? |
| U-08 | Parser/dedup worker no network/no agent tools | Có use case nào thật sự cần network ở bước này? |
| U-09 | BGE-M3 near-duplicate experiment dùng quarantine-only index | Có đồng ý chưa dùng serving vector store? |
| U-10 | Instruction-like/hidden delta mặc định security quarantine | Có cần allow reviewer override với reason/dual approval? |
| U-11 | Scan clean vẫn là untrusted source | Runtime agent/tool PEP luôn còn hiệu lực |
| U-12 | Upload response không báo confidential duplicate | Có đồng ý chỉ trả generic receipt/status? |

Quyết định hiện hành: giữ U-01..U-12. Nếu cần giảm công review, tối ưu bằng priority/risk queue chứ không auto-publish near duplicate.

## 7. Giới hạn và bước sau

- chưa có labeled Vietnamese duplicate/non-duplicate set để chốt MinHash/SimHash/semantic thresholds;
- chưa đo false merge/near-duplicate precision/recall;
- chưa chọn quarantine object store, sandbox/parser hoặc CDR/antimalware product;
- chưa chạy concurrent upload hoặc hidden-text detector;
- chưa có reviewer thật xác nhận legitimate variants/new revisions.

Bước này đã được thực hiện bằng [labeled duplicate mini-set v0.1](22-duplicate-detection-labeled-mini-set-v0.1.md): 26 pairs exact/near/revision/variant/unrelated, gồm 8 poisoned deltas. Labels còn chờ review; chưa chạy detector hoặc ghi bất kỳ upload nào vào serving index.
