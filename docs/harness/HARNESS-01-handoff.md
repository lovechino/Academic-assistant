# HARNESS-01 — installation handoff

Ngày: 2026-09-06. Status: **verified_local**, chưa đánh giá hành vi model hoặc có independent acceptance. Work package nghiên cứu vẫn là WP-03 tiếp theo; HARNESS-01 là maintenance theo yêu cầu tạo harness của người dùng.

## Scope và baseline

[Card HARNESS-01](tasks/HARNESS-01.json); run `harness-01-install`, baseline local `tmp/agent-harness/harness-01-install.json`.

Bootstrap exception được ghi rõ: script checker, project-state và HARNESS-01 card phải được tạo trước khi có thể chạy `begin`; baseline này không chứng minh thời điểm tạo ba file đó. Chúng được kiểm tra lại bằng tests/static review. Baseline chứa 171 Git-visible paths, bao gồm các sửa đổi/untracked từ những lượt trước. Các chỉnh sửa tiếp theo phải nằm trong 10 exact files của card; không sửa master plan, runtime, corpus hay historical experiment scripts/config/results.

## Đầu ra

- AGENTS entry point và hướng dẫn vận hành: orient → card → baseline → execute → verify → handoff.
- Machine snapshot bám master plan qua checksum; stage pre-product, WP-03 tiếp theo, ASTRA pending.
- Checker stdlib và synthetic repository tests; không provider, DB, index writer hoặc product dependency.
- Handoff template; WP03-01 card cho inventory/scorer specification, chưa thực thi.
- H-01..07 và dev scenario proposal để đo chất lượng harness theo từng model về sau.

## Verification

Chạy thật ngày 2026-09-06, qua `py -3.11 -B scripts/agent_harness.py verify --run harness-01-install --require-local-data`; exit 0. Các subprocess/profile và scope được in cùng kết quả, không chạy model hoặc historical generator.

| Check | Kết quả | Phạm vi |
|---|---|---|
| `check-task --task docs/harness/tasks/WP03-01.json` | Valid declaration | Không phải authorization để bắt đầu WP-03 |
| `check --run harness-01-install` | 10 changed paths đúng allowlist | So với baseline sau ba bootstrap files; không có out-of-scope Git-visible delta |
| Harness unittest profile | 31/31 methods PASS, không skip | Synthetic temp repos; product actions, stale state/card/HEAD/plan, dirty/untracked files, path guards, output/check failures |
| `scripts/verify_structure.py --require-local-data` | 569/569 checks; 48 Python files; 17 PDF hashes; không skip | Structure/syntax/links/integrity, không AI quality |
| Context-integrity unittest profile | 23/23 methods PASS | Existing bounded in-memory regression; không rerun R2–R4 pipelines |
| `git diff --check` | PASS | Whitespace check, không semantic acceptance |

31 harness methods không phải 31 lần chạy Sol/Terra, và không được cộng vào 23 context methods để báo agent accuracy. H-01..07 model-level metrics, 12 behavioral scenario runs và 21 RC integration cases vẫn **NOT RUN**. Không có model API cost, product runtime change, deployment hoặc Git push trong lượt này.

## Self-review và giới hạn

Đây là drift detector tự nguyện, không sandbox; full-shell agent có thể bỏ qua hoặc sửa checker/baseline. Chỉ theo dõi Git-visible bytes; không chặn tool/network trước thực thi, không xác thực user approval từ JSON, không tự kiểm nghĩa của tài liệu. Task output tồn tại và tests pass chưa chứng minh acceptance. Reviewer phải đối chiếu request, diff và evidence; mọi lỗi semantic/safety chưa có oracle phải được nêu ra.

OpenAI Docs ảnh hưởng ở cách đặt entry point tại AGENTS root và đọc chi tiết theo task; không áp dụng model-specific prompting/config hay cài hook tự động. State không được phép tự unlock ASTRA. Không chạy thử Sol/Terra nên chưa có H-01..07 thực nghiệm hoặc tuyên bố “gần như không sai”.

## Tiếp nối

Đọc AGENTS → [harness guide](README.md) → state/master plan → [WP-01.1 repair report](../evaluation/29-review-regression-and-metric-clarifications-v0.1.md). Khi có request tiếp tục nghiên cứu, dùng [WP03-01](tasks/WP03-01.json): inventory packs + scorer specs + gaps. Chưa đóng toàn WP-03; không nhảy WP-02/WP-04/product. Không nâng silver thành gold, không mở E0.10 vô cớ, không rerun generator lịch sử.

ASTRA-01 vẫn **pending review và explicit user GO**. Chưa tới product runtime; chưa cần người dùng duyệt workflow sản phẩm ở lượt cài harness này.
