# WP-02 decision review handoff v0.1

2026-09-06. Request: “Tiếp tục cho tôi”, resolved to current WP-02 review checkpoint. Status: verified_local cho checks cơ học, needs_review cho quyết định scope. Không đổi work package hoặc tự tiến phase.

Card [WP02-DECISION-REVIEW-01](../harness/tasks/WP02-DECISION-REVIEW-01.json); run `wp02-decision-review-01-r1`; baseline 204 Git-visible paths, tạo sau card và trước bốn output edits. Plan SHA `9fa131e61c237b3471978c27213561c81009ae673a0c60cd57b4cfd50f1d95c2`; state giữ WP-02, ASTRA pending. Không rebaseline; giữ nguyên preexisting changes.

## Đã thay đổi

- [Decision review](35-wp02-decision-review-v0.1.md): 10 risks/decisions có căn cứ, owner và mốc giải quyết; future acceptance cases NOT RUN; input checklist WP-04, chưa orchestration triển khai được.
- Handoff hiện tại ghi scope/evidence/giới hạn cho model tiếp theo.
- Handoff 34 thêm follow-up link; docs index thêm hai tài liệu. State tiếp tục trỏ handoff 34 và có đường dẫn tới review mới, không phải stale recovery hoặc lần rerun WP-02 readiness.

## Bằng chứng thực thi

`py -3.11 -B scripts/agent_harness.py verify --run wp02-decision-review-01-r1 --require-local-data`: all_checks_passed tại 2026-09-06T12:49:50 UTC. 31/31 harness tests; 682/682 structure checks, 50 Python syntax files, 17 PDF source hashes; skipped = [], failures = []. Scope đúng bốn output paths. `git diff --check`: exit 0. Đây là checks cơ học, không là product test hoặc semantic acceptance; sau cập nhật handoff kiểm tra scope lại trên cùng baseline, không tạo baseline mới.

Không chạy model, PDF processing, OCR/parser comparison, lịch sử audit/generation hoặc scorer semantic. Không sửa code/scorer, nguồn dữ liệu, registry, plan, state hoặc approval.

## Self-review và còn mở

ARCH-02 được giữ nguyên: manual Academic slice, controlled steps/một vai trò suy luận, backend quyết quyền, no-hit/timeout không là ngoài phạm vi, missing B không được bịa thành comparison đủ. Text-first không xóa required visual hoặc quyền nguồn. DR-03 là documented helper limitation, không tuyên bố phát hiện product failure hoặc đã sửa semantic scoring.

Same-assistant technical review, không independent/human sign-off. Các case trong review là specifications NOT RUN, không nhập vào test counts. Rights, label owner/human gold, matching/calibration, parser/generator choice, resource ceilings và runtime integration vẫn pending theo mốc riêng. Không yêu cầu runtime tests pass trước khi được viết runtime, cũng không miễn tests trước phục vụ người dùng.

## Handoff cho model tiếp theo

**Follow-up 2026-09-07:** người dùng đã đồng ý scope và giao chuẩn bị WP-04/Astra. [Control record](../harness/WP02-WP04-reconciliation.md) chuyển next WP-04, giữ ASTRA pending; đọc [WP-04 handoff 38](38-wp04-review-packet-handoff-v0.1.md) để tiếp nhận packet mới nhất. Các yêu cầu xác nhận scope bên dưới là lịch sử, không xin lại hoặc suy ra product GO.

- Đọc review 35, readiness 09 và scorer spec 32; dùng master plan/harness hiện hành. Không cần đọc lại toàn bộ nghiên cứu hoặc tạo thêm dataset.
- Cần người dùng quyết định: scope text-first/visual-limited cho lát cắt đầu, chưa phải GO sản phẩm. Nếu được xác nhận và giao chuẩn bị WP-04, reconcile control công khai rồi soạn packet theo master plan, đưa gaps vào acceptance/stop conditions.
- Không tự dùng PDF quarantine cho QA/ngoại dịch vụ hoặc chọn provider/budget; không đổi sang multi-agent.
- ASTRA-01 vẫn pending review + explicit user GO. Trước implementation-grade workflow báo đúng gate; không coi review này đã vượt ASTRA-01.
