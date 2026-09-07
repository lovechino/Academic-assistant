# WP02 → WP04: scope confirmation và review-packet preparation

Ghi nhận 2026-09-07. Người dùng trả lời “Tôi đồng ý” với đề xuất Academic QA manual, text có cấu trúc, giữ hình/dependency và chỉ trả phần có evidence khi visual chưa đọc đủ; đồng thời đồng ý chuẩn bị WP-04 và bộ tài liệu Astra. Sau đó yêu cầu “Tiếp tục”. Không phải source rights approval, human label acceptance hoặc product GO.

Card [WP02-WP04-RECONCILE-01](tasks/WP02-WP04-RECONCILE-01.json), run `wp02-wp04-reconcile-01-r1`, baseline 207 Git-visible paths trước output edits; card tạo trước baseline. Exact five-file scope: brief, master plan, state, harness README, record này. Giữ preexisting edits, không sửa checker hoặc baseline.

Plan/state chuyển WP-02 decision checkpoint → WP-04 review-packet preparation; stage vẫn pre_product_research, ASTRA pending_review_and_explicit_user_go. Đã thông báo gate trong hội thoại trước thiết kế workflow. Chỉ DR-01 scope decision được xác nhận; rights/labels/parser/matching/budgets/integration và DR-10 tooling debt còn mở theo [review 35](../evaluation/35-wp02-decision-review-v0.1.md).

Old plan SHA `9fa131e61c237b3471978c27213561c81009ae673a0c60cd57b4cfd50f1d95c2`; new SHA `062e9216632341880e66104b9a2955ddc5c965f86b7c75b1bf7bd37950e67b04`. Kết quả thật: `verify --run wp02-wp04-reconcile-01-r1 --require-local-data` exit 1, BLOCKED: State changed during run; không phải all_checks_passed. Independent inventory/hash compare trên baseline gốc đúng 5 output paths, task SHA và HEAD không đổi. `status` xác nhận plan hash/WP-04/ASTRA pending; `verify_structure.py --require-local-data` đạt 689/689 checks, 50 Python files, 17 PDF hashes, skips/failures = []; `git diff --check` exit 0. Không rerun harness unittest riêng ở transaction này. Giữ nguyên checker/baseline; sau cập nhật record kiểm lại exact scope.

## Điểm tiếp tục

Chuẩn bị WP-04 packet theo master plan trong bounded research documentation card mới; giữ workflow là review draft, không runtime/dependencies/index writer. Đọc [handoff nối tiếp](../evaluation/36-wp02-review-handoff-v0.1.md), nơi sẽ thêm link tới WP-04 deliverables trong scope documentation; research không sửa record dưới harness này. Sau packet, chờ user đưa Astra review findings; không tự tạo thread, gọi Astra hoặc suy câu “tiếp tục” là GO.
