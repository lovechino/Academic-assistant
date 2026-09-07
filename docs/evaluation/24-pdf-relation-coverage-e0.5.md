# PDF relation coverage — E0.5

Ngày tạo/kiểm: 2026-09-05

Kết luận: **đã tạo thêm 24 PDF/28 trang và hiện thực hóa 12 relation còn thiếu; 28/28 trang qua visual QA, 8/8 structural assertions pass; chưa chạy OCR, BGE-M3 hoặc tune threshold**.

## 1. Phạm vi

E0.4 có 10 PDF cho exact, metadata-only, near/variant/unrelated và bốn modality poisoned. E0.5 bổ sung 12 matched relations:

- Unicode NFC/NFD;
- punctuation/whitespace;
- page reorder;
- repeated watermark/header;
- new revision thêm section;
- thay đổi academic claim trong span nhỏ;
- semester variant;
- shared-boilerplate false merge;
- hidden PDF annotation;
- instruction marker trong metadata;
- external URL/link annotation;
- invisible Unicode format character.

Artifacts:

- [E0.5 manifest và SHA-256](../../data/evaluation/synthetic/duplicate-detection-v0.1/pdf-fixtures-e05-manifest.json);
- [generator/inspector](../../ai-core/experiments/security-fixtures/README.md);
- [E0.4 report](23-synthetic-pdf-duplicate-fixtures-e0.4.md);
- [26-pair oracle](../../data/evaluation/synthetic/duplicate-detection-v0.1/pairs.jsonl).

Tất cả vẫn là synthetic quarantine fixtures local. Không file nào được đưa vào content DB, serving index, model context hoặc external OCR/VLM.

## 2. Kết quả relation diagnostics

| Pair | Relation | Text similarity | Các tín hiệu đã xác nhận |
|---|---|---:|---|
| DUP-006 | NFC ↔ NFD | 1.000000 sau NFC | Normalized text bằng nhau; raw/render bytes khác |
| DUP-007 | `:` ↔ `-` + double space | 0.995058 | Punctuation-aware canonical text bằng nhau |
| DUP-009 | Ba trang bị đổi thứ tự | 0.880315 | Page multiset bằng nhau, order khác |
| DUP-010 | Watermark/header delta | 0.973837 | Core content gần nhau, render khác |
| DUP-011 | Revision thêm section | 0.743802 | Substantive addition, cần immutable new version |
| DUP-012 | `O(n)` ↔ `O(log n)` | 0.870504 | Span nhỏ nhưng academic claim thay đổi |
| DUP-014 | HK1 ↔ HK2 | 0.989399 | Similarity rất cao nhưng là legitimate variant |
| DUP-016 | Shared boilerplate, khác core topic | 0.791069 | Negative false-merge case |
| DUP-019 | Hidden annotation | 1.000000 | Text/render bằng nhau; right có `/Text` annotation flag hidden |
| DUP-020 | Metadata instruction | 1.000000 | Text/render bằng nhau; PDF subject khác |
| DUP-021 | External URL delta | 0.952234 | Right có `/Link` URI tới inert `.invalid` fixture |
| DUP-022 | Hidden marker + U+200B | 0.947214 | Render bằng nhau; right có Unicode category `Cf` |

## 3. Visual và structural QA

| Check | Result |
|---|---:|
| PDF được tạo | 24/24 |
| Trang được render/xem | 28/28 |
| Layout/font/clipping issue | 0 |
| Matched relations có đủ hai phía | 12/12 |
| Automated structural assertions | 8/8 pass |
| Page-reorder page number | 6/6 trang đúng 1/3, 2/3, 3/3 |
| Hidden annotation/metadata/Unicode không lộ trong render | Pass |

E0.4 + E0.5 có 34 PDF/38 trang, ánh xạ relation-level tới đủ 26 pair IDs. Hai clean matched counterparts cho DUP-023/024 và deterministic baseline đã được bổ sung ở [E0.6](25-deterministic-dedup-baselines-e0.6.md); toàn bộ vẫn là development fixtures, không phải final test.

## 4. Các phản ví dụ đối với một similarity threshold

1. DUP-014 là legitimate semester variant nhưng similarity `0.989399`.
2. DUP-019 và DUP-020 đạt `1.0` ở extracted text và pixel render, dù candidate chứa security delta ở annotation/metadata.
3. DUP-021 poisoned URL chỉ đạt `0.952234`, thấp hơn legitimate variant.
4. DUP-012 chỉ sửa một academic claim nhưng phải là new revision, không phải cosmetic near duplicate.
5. DUP-006 có normalized text giống hệt nhưng raster bytes không giống, cho thấy exact visual hash cũng không phải canonical content identity.
6. DUP-009 cần giữ đồng thời page-set và page-order; một bag-of-pages score sẽ bỏ mất reorder.

Kết luận: embedding/shingle/visual score chỉ được dùng để tạo candidate hoặc cung cấp evidence. Nó không quyết định `safe`, `merge`, `publish`, rights hoặc tenant visibility.

## 5. Representation inventory bắt buộc

Trước khi similarity, mỗi upload phải tạo một quarantine manifest có ít nhất:

| Representation | Dùng để đo | Không được tin như |
|---|---|---|
| Raw bytes + SHA-256 | Idempotency/exact binary | Content equivalence đầy đủ |
| PDF object/annotation/action inventory | Annotation, URI, attachment, script/action surface | Trusted instructions |
| Metadata fields | Delta/provenance diagnostic | Owner/rights/authorization |
| Text layer nguyên bản | Hidden/control/instruction-like delta | Ground truth duy nhất |
| NFC + whitespace canonical text | Exact-content candidate | Auto-merge decision |
| Page fingerprints + ordered sequence | Reorder/add/delete alignment | Academic semantics |
| Rendered page image | Layout/image delta | Text safety |
| OCR/VLM output | Image-only observability | Trusted tool command |
| Cross-representation diff | OCR/text/render conflict | Automatic publication |

## 6. Metric registry cho E0.6

| ID | Metric | Denominator | Báo cáo bắt buộc |
|---|---|---|---|
| DUP-M01 | Exact binary recall | Exact-byte pair contexts | 100% |
| DUP-M02 | Exact content candidate recall | Metadata/NFC/punctuation/container equivalence | Theo normalization family |
| DUP-M03 | Near/revision candidate recall@k | Near + new revision | k, family, modality |
| DUP-M04 | Legitimate-variant false merge | DUP-013/014 và mở rộng | Hard error count |
| DUP-M05 | Unrelated false merge | DUP-015/016 và hard negatives | Hard error count |
| SEC-M01 | Security-surface inventory recall | Hidden/annotation/metadata/URL/image/OCR/Unicode | Theo modality |
| SEC-M02 | Poisoned promotion rate | Mọi poisoned case | Hard gate = 0 |
| SEC-M03 | Cross-representation conflict recall | Render/text/OCR mismatches | Reason code + locator |
| GOV-M01 | Provenance/rights preservation | Multi-uploader/tenant/rights cases | Không kế thừa ngầm |
| GOV-M02 | Cross-tenant leakage | Cross-tenant exact/near cases | Hard gate = 0 |

Không gộp các hard gates vào một micro-F1 hoặc RAGAS score.

## 7. Split policy trước benchmark

Bộ 26 pair hiện đã lộ trong docs/generator nên chỉ được dùng làm **calibration/development set**. Không được lấy ngẫu nhiên vài pair từ cùng template làm “hidden test”; như vậy sẽ rò rỉ layout, marker và mutation family.

Hidden set phải:

1. dùng source-family/template mới;
2. giữ kín marker strings và mutation implementation;
3. group split theo document family, không theo individual page/file;
4. có matched benign hard negatives cho từng attack modality;
5. khóa manifest/hash trước khi tune;
6. chỉ chạy sau khi detector config/threshold đã đóng.

## 8. Bước tiếp theo E0.6

1. Review và freeze [quarantine manifest/aligned-delta logical contract](../../contracts/quarantine-manifest.md), sau đó mới viết JSON Schema.
2. Tạo clean matched counterparts cho image-only và OCR/text mismatch.
3. Sinh hidden-family pack tách khỏi generator/dev fixtures hiện tại.
4. Chạy raw/canonical/page-structure baseline trên dev.
5. So shingle/MinHash/SimHash và BGE-M3 ở nhiệm vụ candidate recall@k.
6. Chạy security inventory độc lập, sau đó mới kết hợp evidence vào review workflow.
7. Chốt threshold trên dev; chạy hidden đúng một lần cho milestone.

## 9. Không được claim

- 34 synthetic PDF không đại diện corpus giáo trình Việt Nam thực tế.
- Structural/visual pass không phải detector accuracy hoặc security certification.
- Chưa có OCR accuracy, BGE-M3 result, precision/recall/F1 hay frozen threshold.
- Chưa có teacher/security reviewer; labels vẫn provisional.
- Không có runtime upload pipeline, policy enforcement hoặc serving-index integration.
