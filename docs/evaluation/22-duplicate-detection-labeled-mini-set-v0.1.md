# Duplicate detection labeled mini-set v0.1 — E0.3 review

Ngày tạo/kiểm: 2026-09-05

Kết luận: **26 synthetic pair labels structurally valid; human label review pending; detector not run**.

## 1. Mục tiêu

Tạo denominator đầu tiên cho exact/near-duplicate và poisoned-delta evaluation sau khi upload policy U-01..U-12 được chấp thuận. Pack không dùng tài liệu thật và không tạo embedding/index.

Files:

- [manifest](../../data/evaluation/synthetic/duplicate-detection-v0.1/manifest.json);
- [26 labeled pairs](../../data/evaluation/synthetic/duplicate-detection-v0.1/pairs.jsonl);
- [validation](../../data/evaluation/synthetic/duplicate-detection-v0.1/validation.json);
- policy nguồn: [secure upload/quarantine/dedup](../governance/05-secure-upload-quarantine-deduplication-v0.1.md).

## 2. Ba trục nhãn độc lập

| Trục | Giá trị | Ý nghĩa |
|---|---|---|
| Duplicate | exact binary/content, near duplicate, new revision, legitimate variant, unrelated | Quan hệ nội dung |
| Security | benign, suspicious, poisoned | Rủi ro của delta/file/context |
| Resolution | reuse/link/review/version/variant/separate/quarantine/rights hold | Workflow expected |

Không suy security từ similarity. Một thay đổi rất nhỏ có thể là poisoned prompt; một thay đổi lớn hơn có thể là biến thể giảng dạy hợp lệ.

## 3. Phân bố

### Duplicate class

| Label | Pairs |
|---|---:|
| exact binary | 4 |
| exact content | 5 |
| near duplicate | 11 |
| new revision | 2 |
| legitimate variant | 2 |
| unrelated | 2 |

### Security class

| Label | Pairs |
|---|---:|
| benign | 14 |
| suspicious | 4 |
| poisoned | 8 |

### Expected resolution

| Resolution | Pairs |
|---|---:|
| idempotent receipt reuse | 1 |
| link tenant blob, preserve submissions | 1 |
| tenant-isolated intake | 1 |
| exact-content human review | 4 |
| near-duplicate diff/review | 3 |
| immutable new-version review | 2 |
| separate lecturer variant | 2 |
| separate material/do not merge | 2 |
| security quarantine | 8 |
| rights hold/no inheritance | 2 |

## 4. Các nhóm pair để review

| IDs | Proposed label | Điểm cần xác nhận |
|---|---|---|
| DUP-001 | exact binary/benign/reuse receipt | Retry cùng upload context không tạo submission mới |
| DUP-002 | exact binary/benign/link tenant blob | Hai lecturers vẫn giữ hai submissions/provenance |
| DUP-003 | exact binary/benign/tenant isolated | Không báo trùng xuyên tenant |
| DUP-004..007 | exact content/benign/review | Container, PDF timestamp, Unicode và whitespace không tạo new content |
| DUP-008 | near/benign/review | Một vài từ sửa cách diễn đạt, chưa đủ auto-version |
| DUP-009 | near/suspicious/review | Reorder section cần owner xác nhận |
| DUP-010 | near/benign/review | Header/watermark khác không auto merge |
| DUP-011..012 | new revision | Bổ sung section hoặc đổi academic claim phải version hóa |
| DUP-013..014 | legitimate variant | Hai giảng viên/học kỳ có thể giữ hai variants |
| DUP-015..016 | unrelated | Same title/boilerplate không được false merge |
| DUP-017..024 | near/poisoned/quarantine | Visible, hidden, annotation, metadata, URL, Unicode, image và OCR-layer injection |
| DUP-025..026 | exact/suspicious/rights hold | Hash trùng không kế thừa rights/approval |

## 5. Kết quả E0.3 lint

```text
pairs parsed: 26
unique pair IDs: 26/26
duplicate labels: 6/6 expected classes
security labels: 3/3 expected classes
expected resolutions: 10
missing label/resolution/signal: 0
distribution vs manifest: PASS
runtime detector: NOT RUN
```

## 6. Mapping tới metric

- UPL-04 exact duplicate recall: deterministic raw-hash subset trước, normalized-content subset riêng.
- UPL-05 near-duplicate recall/precision: DUP-008..010 + DUP-017..024; chưa chốt threshold.
- UPL-06 false merge: critical denominator DUP-013..016.
- UPL-07 poisoned-delta promotion: DUP-017..024, gate 0 promoted.
- UPL-08 provenance: DUP-002/003/011..014/025/026.
- UPL-10 cross-tenant existence leakage: DUP-003.

## 7. Không được kết luận

- 26 text/metadata pairs không đại diện đủ PDF/slide thực tế;
- label pass không phải detector pass;
- không có precision/recall/F1 hoặc threshold;
- mới có 10 PDF synthetic E0.4 cho một subset; chưa có đủ 26 pair hoặc PDF/slide phức tạp;
- chưa có hidden final test split;
- chưa có human reviewer xác nhận class boundary.

## 8. Sau khi review labels

1. Freeze pair labels hoặc ghi disagreement.
2. Mở rộng subset 10 PDF E0.4 sau review; mọi artifact vẫn ở quarantine fixture.
3. Định nghĩa train/dev/hidden split trước khi tune.
4. So exact hash → normalized hash → shingle/MinHash/SimHash → visual hash; semantic embedding chỉ là ablation sau.
5. Đo precision/recall theo duplicate class và security class; không chọn một similarity score chung làm publish decision.
