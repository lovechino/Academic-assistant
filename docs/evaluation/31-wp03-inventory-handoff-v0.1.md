# WP-03 technical handoff v0.1

2026-09-06. User giao WP-03 và WP-02; đã làm WP-03 trước. Status: verified_local cho technical scope, pending human review/calibration. Task [WP03-REGISTRY-01](../harness/tasks/WP03-REGISTRY-01.json), run `wp03-registry-01-r1`, baseline 187 Git-visible paths trước output edits. Card tạo trước baseline; prepared WP03-01 cũ không chạy, không sửa để giả execution.

## Deliverables

- [Inventory](30-evaluation-registry-inventory-v0.1.md) và [105 file pins / 18 nhóm](registry-v0.1.json): provenance/authority/exposure/rights/eligibility/permitted claims, không sao chép source contents.
- [Scorer specification](32-scorer-specification-v0.1.md): formulas, N/A/pending/error, mapping family/ownership và ARCH-02 taxonomy gap.
- [Offline scoring experiment](../../ai-core/experiments/evaluation-scoring-v0.1/README.md): synthetic arithmetic only, không product logic/model calls.

## Verification

Kết quả thật 2026-09-06: 19/19 tests bằng `py -3.11 -B -m unittest discover -s ai-core/experiments/evaluation-scoring-v0.1 -p test_scoring.py -v`; harness `verify --run wp03-registry-01-r1 --require-local-data` đạt 31/31 harness tests, 23/23 context-integrity regression, 641/641 structure checks, 50 Python files và 17 PDF hashes, skips = []. Scope đúng 8 output paths; all_checks_passed tại 12:16:44 UTC. Hash audit registry: 105 checked, 0 mismatch. `git diff --check` exit 0. Sau ghi kết quả handoff, final scope check dùng cùng baseline.

Registry hashes đọc từ files hiện tại, không xác nhận independently historical snapshot hoặc nhãn học thuật. Không rerun helpers/generators ghi artifact lịch sử; 23 context tests read-only được chạy lại theo card. New synthetic tests không là 21 RC integration cases, không là model/agent scores.

## Review/disposition

Same-assistant self-review, không independent sign-off: AND/OR locator semantics, macro/micro, packing loss theo identity, timeout denominator, OCR signs/accents và gate conjunction được tách rõ. Pending labels không encode như observed false. Registry split/rights không nâng silver/quarantine; public benchmark chỉ là catalog candidate. Các family chưa có scorer semantic đều marked pending; không nói full calibration complete.

Technical inventory/specification đủ làm đầu vào WP-02 readiness documentation. WP-03 **chưa được M0/human acceptance hoặc full scorer calibration**: reviewed labels, negative expansion oracle, citation/claim matching, thresholds, RAGAS và integration còn mở. Runtime behavior không thể nghiệm thu bằng fixture tests. Không chọn production winner hoặc token budget.

Master plan/state chưa đổi trong run này. Nếu chuyển next WP để làm WP-02 theo request hiện hành, reconcile bằng thay đổi quản trị riêng sau khi kết thúc/verify run, giữ rõ các pending trên. Không sửa state giữa run hoặc tự bật approval.

## Next

WP-02: dùng PDF audit/SP01..12/visual seed, phân biệt preservation và failure detection; chốt local inspection-only/readiness protocol, không chạy OCR/provider trên corpus chưa có rights. Sau các technical docs mới chuẩn bị WP-04; ASTRA-01 và explicit user GO vẫn mandatory. Không triển khai AI Core hoặc router đa mode ở lượt này.
