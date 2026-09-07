# Authorization E0.1 — direct-action, dependency và cache expansion

Ngày chạy: 2026-09-05

Kết luận: **representative structural coverage pass; policy review pending; runtime not run**.

## 1. Vì sao có E0.1

[E0 ban đầu](19-authorization-e0-fixture-review.md) có đủ stage/metric representative coverage sau khi thêm query-planning/citation cases, nhưng còn 11 action chưa có case trực tiếp và dependency/cache quá mỏng. E0.1 bổ sung case để người dùng review policy cụ thể trước khi freeze hoặc viết evaluator.

Không đổi expected outcome DT-001..DT-052. E0.1 chỉ thêm DT-053..DT-084, một security-auditor principal và ba resource fixtures cần cho policy test.

## 2. Những case được thêm

| Nhóm | IDs | Nội dung |
|---|---|---|
| Metadata discovery | 053–054 | Public allow; cross-tenant metadata/enumeration deny |
| Upload/review/publish/archive | 055–062 | Positive và negative paths, separation of duties, epoch/cache/index obligations |
| External share | 063–064 | Exact recipient/version/action/expiry allow; lecturer không có grant bị deny |
| Grant administration | 065–066 | Org-admin control-plane allow; agent không được đổi membership |
| Audit content | 067–068 | Org admin deny; security auditor incident-scoped allow có redaction |
| Transform/OCR/index | 069–074 | Exact admitted version allow; draft/secret/cross-tenant deny |
| Dependency | 075–078 | Current table allow; confidential child/cross-tenant/stale parent deny |
| Cache | 079–084 | Exact compatible allow; stale epoch/version, mixed tenant và missing lineage deny |

## 3. Kết quả lint hiện hành

| Mục | E0 | E0.1 |
|---|---:|---:|
| Cases | 52 | 84 |
| Decision checkpoints | 56 | 90 |
| Expected ALLOW | 19 | 34 |
| Expected DENY | 37 | 56 |
| All-ALLOW cases | 15 | 28 |
| Families | 27 | 31 |
| Principal entities | 10 | 11 |
| Resource entities | 11 | 14 |
| Direct request actions | 12 | 23 |
| Enforcement stages represented | 12/12 | 12/12 |
| AUTH metric IDs routed | 14/14 | 14/14 |
| Duplicate/unknown/missing-oracle issues | 0 | 0 |

Machine-readable historical result: [validation-e01-84.json](../../data/evaluation/synthetic/authorization-v0.1/validation-e01-84.json). Working fixture sau báo cáo này đã được mở rộng cho upload/dedup; xem [E0.2 upload review](21-authorization-e02-upload-dedup-review.md).

### Stage distribution E0.1

| Stage | Checkpoints |
|---|---:|
| request admission | 14 |
| query planning | 2 |
| candidate retrieval | 9 |
| dependency expansion | 5 |
| model context serialization | 5 |
| tool execution | 7 |
| cache hydrate/write | 8 |
| pre-delivery | 2 |
| citation mint | 2 |
| source view/download | 8 |
| ingest/index publish | 13 |
| share/export/privileged action | 15 |

### Metric routing E0.1

| Metric | Cases tagged |
|---|---:|
| AUTH-01 | 15 |
| AUTH-02 | 52 |
| AUTH-03 | 57 |
| AUTH-04 | 8 |
| AUTH-05 | 12 |
| AUTH-06 | 8 |
| AUTH-07 | 11 |
| AUTH-08 | 10 |
| AUTH-09 | 21 |
| AUTH-10 | 6 |
| AUTH-11 | 1 |
| AUTH-12 | 30 |
| AUTH-13 | 7 |
| AUTH-14 | 15 |

Các con số trên là routing/fixture counts, không phải observed security metrics.

## 4. Các policy proposal cần người dùng review

| Ref | Đề xuất mặc định | Lý do | Nếu đổi thì ảnh hưởng |
|---|---|---|---|
| R-01 | Upload luôn vào quarantine/draft; chưa vào serving index | File upload là untrusted input | Đổi thành serve ngay sẽ phá admission boundary |
| R-02 | Người sửa version không approve/publish chính version đó | Separation of duties | Cần reviewer thứ hai hoặc exception audited |
| R-03 | `publish` do Backend điều phối; indexer chỉ ghi staging index | Worker/agent không tự public hóa dữ liệu | Nếu indexer đổi alias thì authority quá rộng |
| R-04 | Archive cần step-up, audit, epoch bump và invalidate index/cache | Revoke phải có hiệu lực ở mọi derivative | Nếu chỉ đổi DB state, stale vectors/cache có thể rò |
| R-05 | External share cần named recipient + exact version + actions + expiry + approval | Link không trở thành bearer credential | Có thể giảm friction nhưng tăng nguy cơ forward/leak |
| R-06 | Org admin quản lý membership nhưng không tự cấp content-reader cho bản thân | Tách control plane/content plane | Cần workflow khác cho support/break-glass |
| R-07 | Raw audit content chỉ cho security auditor theo incident/ticket; org admin bị deny | Audit có thể chứa query/resource metadata nhạy cảm | Nếu org admin đọc, phải bổ sung redaction/scope rõ |
| R-08 | OCR bên ngoài chỉ khi provider route được policy cho phép | OCR có thể gửi toàn bộ PDF ra ngoài | Cần provider/data-residency matrix trước runtime |
| R-09 | Parent allow không override child sensitivity/version | Ảnh/bảng/đáp án có thể nhạy hơn tài liệu cha | Nếu inherit mù, hidden-answer có thể lọt context |
| R-10 | Mixed-scope cache entry bị reject toàn bộ rồi recompute | Không hydrate một packet chứa dependency trái quyền | Partial sanitize cache phức tạp và dễ sót lineage |
| R-11 | Cache thiếu complete dependency lineage bị deny | Không chứng minh được current authorization | Cache cũ không lineage phải bỏ, không migrate bằng đoán |
| R-12 | AUTH-11 chỉ đo sau runtime; không giả latency từ fixture | Fixture không thực thi PDP | E1/E2 phải ghi timestamps và batch complexity |

## 5. Review theo hướng tránh deny-all

Review 28 all-ALLOW cases trước. Mỗi ALLOW phải xác nhận:

- đúng principal/tenant/action/purpose;
- resource/version/lifecycle/sensitivity chính xác;
- obligations có đủ và thực thi được;
- allow không vô tình kéo thêm action như download/export/share;
- agent/workload authority không rộng hơn human/business authority.

Sau đó review 56 DENY checkpoints, đặc biệt reason precedence và public response. Internal reason có thể chi tiết để audit; response ra user phải tránh existence oracle.

## 6. Gap còn lại

- chưa có full principal × action × resource cross-product; đây là representative pack;
- `edit_metadata`, `read_audit_metadata`, `mutate_audit_record` và vài stage có ít case;
- chưa tách hidden adversarial set;
- chưa kiểm obligation semantics bằng code;
- AUTH-10/11 chưa có runtime timestamps;
- chưa có institutional owner/security reviewer ký expected policy.

## 7. Quyết định vòng

```text
JSON/reference/count lint: PASS
direct action representative coverage: PASS (23 actions)
dependency/cache expansion: PASS at specification level
policy proposal approval: PENDING USER REVIEW
hidden adversarial split: NOT CREATED
runtime evaluation: NOT RUN
E1 readiness: BLOCKED BY POLICY REVIEW/FREEZE, not by fixture syntax
```

## 8. Sau khi review

1. Áp feedback vào R-01..R-12 và expected DT outcomes.
2. Bổ sung one-sided action cases nếu reviewer thấy rủi ro.
3. Freeze decision table + entities/cases thành snapshot bất biến.
4. Tạo hidden adversarial split tách khỏi development specification.
5. Thiết kế pure policy evaluator E1; chưa nối model/vector database.
