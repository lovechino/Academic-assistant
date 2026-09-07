# WP03 → WP02: explicit governance reconciliation

2026-09-06. User giao cả WP-03 và WP-02. Research run `wp03-registry-01-r1` đã verify/final scope check xong trước transaction này. Technical inventory/specification đủ để soạn WP-02; human/M0/calibration/full semantic scorer/runtime acceptance chưa hoàn tất và không bị đổi thành approved.

Card: [WP03-WP02-RECONCILE-01](tasks/WP03-WP02-RECONCILE-01.json). Run `wp03-wp02-reconcile-01-r1`, baseline 195 Git-visible paths, card được tạo trước baseline. Scope duy nhất: master plan, project-state và record này. Không sửa checker/tests/ASTRA/sequence hoặc overwrite baseline.

Old plan SHA-256: `feadc8d4236aeea03f3cd54a46b4aa25b45da09cee07e6843f977da534ca0636`. New plan SHA được ghi trong state và kiểm tra trực tiếp bằng status; next WP-03 → WP-02, last handoff → evaluation/31. Không có API advance/GO.

## Verification contract

Harness v0.1 cố định `state_sha256` cho cả maintenance run. Vì thế `verify` của control transaction này dự kiến reject stale-state; **không được báo all_checks_passed cho run này**. Sau khi ghi state/plan nhất quán: chạy verify để ghi rejection thật, read-only compare toàn inventory với baseline cũ (exact three-file allowlist), kiểm HEAD/card không đổi, `status` xác nhận plan hash/ASTRA/sequence, structure và fixed harness tests. Không tự refresh baseline để làm verify xanh.

Kết quả thật: harness verify trả `BLOCKED: State changed during run; reconcile separately`, đúng giới hạn đã khai báo, không PASS. Read-only inventory compare với baseline cũ xác nhận đúng 3 allowed files; card SHA và HEAD không đổi. `status` pass với next WP-02, ASTRA pending, new plan SHA `3c118624f1053c5021b549ceb251d8ddc766d133db1a873edbaa4dc46db403e0`. Independent checks: 643/643 structure, 50 Python files, 17 PDF hashes, skips []; 31/31 harness unittest; git diff --check exit 0. Record này được cập nhật kết quả sau tests; không thay baseline.

Ngoại lệ verification này chỉ ghi giới hạn công cụ khi quản trị state theo user request, không cho phép research tasks đổi controls. WP-02 sẽ có card/run mới sau transaction, không tái sử dụng research baseline đã kết thúc. Các run cũ giữ nguyên bằng chứng tại thời điểm hoàn tất, không được resume như state vẫn cũ.

## Pending

ASTRA = pending_review_and_explicit_user_go. WP-02 chỉ readiness docs/local inspection; PDF rights vẫn quarantine, không broader eval/OCR/provider. WP-03 technical handoff không đồng nghĩa M0/academic acceptance. Không bắt đầu WP-04/product trong transaction này.
