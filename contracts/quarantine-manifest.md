# Quarantine manifest và aligned-delta contract v0.1

Ngày: 2026-09-06 — clarification v0.1.1

Trạng thái: **logical contract để review; chưa có JSON Schema, API, persistence hoặc runtime implementation**.

## 1. Mục tiêu

Contract này nối Backend intake với sandbox scanner/parser và duplicate-review workflow mà không đưa raw upload vào content DB hoặc serving index. Nó tách rõ:

- **trusted envelope** do Backend tạo từ authenticated request/policy;
- **untrusted observations** lấy từ file, metadata, OCR, parser và detector;
- **review decision** do Backend ghi theo quyền hiện hành;
- **serving artifact** chỉ được tạo sau promotion gate riêng.

AI core, parser, OCR và duplicate model không được sửa trusted envelope, cấp quyền, kế thừa rights hoặc tự promote lifecycle.

## 2. Hai record khác nhau

### 2.1 Minimal quarantine receipt

Được lưu ngay sau intake, không chứa extracted content hoặc embedding:
```text
receipt_id
submission_id
tenant_id
uploader_principal_id
authorization_decision_id
server_object_key
raw_sha256
byte_size
detected_media_type
idempotency_digest
received_at
intake_state
policy_version
```

Receipt dùng cho idempotency, audit và trạng thái. Không được query xuyên tenant hoặc trả tín hiệu existence của tenant khác.

### 2.2 Quarantine analysis manifest

Được ghi trong analysis namespace tách serving data plane. Manifest có thể chứa dẫn chiếu tới extracted text/render/OCR/diff artifacts nhưng không nhúng chúng vào receipt/public API.

## 3. Logical shape

```json
{
  "manifest_version": "quarantine-manifest-v0.1",
  "trusted_envelope": {},
  "raw_artifact": {},
  "structure_inventory": {},
  "representations": [],
  "security_findings": [],
  "duplicate_candidates": [],
  "cross_representation_findings": [],
  "review_state": {},
  "lineage": {},
  "audit": {}
}
```

Đây là shape khái niệm, không phải schema đã freeze.

## 4. Trusted envelope

Chỉ Backend/PDP tạo:

| Field | Quy tắc |
|---|---|
| `receipt_id`, `submission_id` | Opaque, server-generated |
| `tenant_id` | Đúng một active tenant; immutable trong manifest version |
| `uploader_principal_id` | Từ authenticated identity, không lấy từ PDF author |
| `purpose` | Upload/review purpose đã policy-check |
| `sensitivity_ceiling` | Giới hạn được phép của sandbox job |
| `authorization_decision_id` | Trỏ decision/epoch hiện hành |
| `policy_version` | Bắt buộc cho reproducibility |
| `job_capability_id` | Capability hẹp cho exact submission; no network/tools mặc định |
| `created_at`, `expires_at` | Server clock |

File-derived author, course, institution, title và rights claim không được ghi đè các field này.

## 5. Raw artifact

| Field | Ý nghĩa |
|---|---|
| `object_ref` | Tenant quarantine object, không public URL |
| `raw_sha256`, `byte_size` | Exact bytes/idempotency |
| `declared_filename` | Untrusted display-only |
| `declared_media_type` | Untrusted request value |
| `detected_media_type` | Scanner observation |
| `magic_match` | Declared vs detected |
| `encrypted`, `password_required` | Giữ quarantine nếu true |
| `resource_limit_findings` | Page/object/decompressed-size/time/memory limits |

Object immutable; mọi transform tạo artifact ID/hash mới, không overwrite raw bytes.

## 6. Structure inventory

PDF pilot cần tối thiểu:

```text
page_count
object_count
annotation_count_by_subtype
action_types
external_uris
embedded_files
javascript_or_launch_actions
form_fields
image_count_by_page
text_object_count_by_page
off_page_or_tiny_text_findings
unicode_format_or_confusable_counts
parser_name/version/config_hash
```

Mọi string lấy từ PDF object/metadata là `untrusted_content`, kể cả tên action hoặc annotation contents.

## 7. Representation record

Mỗi raw/text/render/OCR/canonical representation có:

| Field | Bắt buộc |
|---|---|
| `representation_id` | Có |
| `kind` | `raw`, `text_layer`, `canonical_text`, `page_render`, `ocr`, `layout`, `structure_inventory` |
| `artifact_ref` | Quarantine-only reference |
| `sha256` | Có |
| `source_submission_id` | Có |
| `source_page_or_object_locator` | Khi áp dụng |
| `producer`, `producer_version`, `config_hash` | Có |
| `created_at` | Có |
| `trust_label` | Luôn `untrusted_content` cho file-derived output |
| `sensitivity`, `rights_state` | Kế thừa source; không tự hạ |
| `error_or_partial_reason` | Bắt buộc nếu output thiếu/partial |

OCR/VLM output không thay thế text layer. Cả hai được giữ để tạo conflict finding.

Representation ở quarantine gắn `submission_id` + immutable `source_snapshot_id`, chưa bắt buộc material version. Sau review, Backend tạo immutable promotion binding sang material version, tham chiếu lại representation/artifact/hash gốc; không sửa manifest lịch sử. Quarantine origin không đủ điều kiện serving. Namespace này chỉ cho assigned reviewer/isolated inspector đọc bằng action/purpose riêng theo [authorization contract](authorization-context.md); không cấp generic learner model/viewer access.

## 8. Security finding

```text
finding_id
detector_id/version/config_hash
modality
finding_type
severity
confidence_or_deterministic
source_locator
evidence_artifact_ref
matched_span_hash
reason_code
review_status
```

`finding_type` tối thiểu gồm active content, hidden text, annotation instruction, metadata instruction, external URI, Unicode control/confusable, secret/credential pattern, OCR/text conflict, image-only instruction-like span và resource bomb.

Finding là signal, không phải instruction cho agent và không tự kết luận nội dung học thuật sai.

## 9. Duplicate candidate

Candidate search mặc định tenant-scoped và authorization-filtered trước similarity:

```text
candidate_ref_opaque
candidate_scope = same_tenant
signals[] = {kind, score_or_match, detector_version, artifact_ref}
aligned_delta_ref
duplicate_class_proposal
security_class_proposal
abstention_reason
```

Không trả canonical/material ID, uploader, title hoặc existence signal nếu caller không được phép biết candidate. `duplicate_class_proposal` không kế thừa owner, rights, approval hoặc publish state.

## 10. Aligned delta report

Một report so hai submissions phải có:

| Nhóm | Nội dung |
|---|---|
| Identity | Hai opaque submission refs, tenant scope, manifest versions |
| Exact | Raw/canonical hash equal/different |
| Page alignment | Added/removed/moved pages; order-preserving và set-based view |
| Text delta | Added/removed/changed spans với physical page/object locators |
| Unicode delta | Code point/category, normalized form, invisible/confusable positions |
| Structure delta | Annotation/action/URI/attachment/metadata changes |
| Visual delta | Render/layout/image hashes và changed regions |
| OCR conflict | Text layer ↔ OCR/render disagreement |
| Security delta | Finding refs, không copy thành executable prompt |
| Provenance | Uploader/course/term/version/rights từ trusted records, không từ PDF |

Reviewer UI phải hiển thị security delta tách khỏi academic-content delta.

## 11. Review state và transition

Allowed analysis outcomes:

- `needs_owner_review`;
- `exact_duplicate`;
- `new_version`;
- `legitimate_variant`;
- `unrelated_title_collision`;
- `rights_hold`;
- `security_quarantine`;
- `rejected_file`.

Mỗi transition ghi `actor`, `authorization_decision_id`, `policy_version`, `from`, `to`, `reason_code`, `time` và manifest hash. Uploader/model/agent không tự ghi quyết định owner/curator. `approved_for_staging` là Backend lifecycle action riêng và không nằm trong detector output.

## 12. Invariants và contract tests về sau

1. Thiếu tenant/policy/capability → deny/fail closed.
2. Raw upload không xuất hiện trong content DB/serving index.
3. File-derived metadata không ghi đè trusted identity/rights.
4. Mọi representation truy ngược được raw SHA-256 và producer config.
5. OCR/text/render conflict không bị silently collapsed.
6. Duplicate candidate không làm lộ existence xuyên tenant.
7. Exact duplicate không kế thừa approval/rights.
8. Poisoned finding không được serialize thành system/tool instruction.
9. Review transition append-only và có authorization trace.
10. Revoked/rejected/quarantined submission không thể được promote bằng stale result.

## 13. Chưa chốt

- JSON Schema/OpenAPI và field encoding;
- object store/database/vector product;
- scanner/OCR/VLM vendor;
- canonicalization algorithm/version;
- duplicate threshold;
- finding severity taxonomy cuối cùng;
- retention/encryption key schedule;
- reviewer UI payload shape.

Các mục này chưa được chốt bởi E0.9 hoặc WP-01; chúng cần policy review và experiment/review package tương ứng, không suy từ fixture generator. Khi một submission được duyệt để staging, mapping sang `source_snapshot_id`, `material_id` và immutable `material_version_id` phải tuân theo [Content Unit & Index Boundary v0.1](content-unit-index.md); similarity không tự tạo mapping hoặc merge.
