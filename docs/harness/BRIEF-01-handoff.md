# BRIEF-01 — problem/scope clarification

Ngày 2026-09-06. Status: **verified_local**; nội dung còn cần người dùng review, chưa stakeholder acceptance. Request: làm rõ bài toán/mục tiêu/phạm vi để nhiều model nhỏ có thể đọc và làm theo. Không phải request chạy benchmark hoặc code sản phẩm.

Card: [BRIEF-01](tasks/BRIEF-01.json). Run: `brief-01-r1`, local baseline `tmp/agent-harness/brief-01-r1.json`, 177 Git-visible paths. Card mới được soạn trước baseline theo quy trình; mọi output edit bắt đầu sau baseline. HARNESS-01 là namespace maintenance của checker v0.1, không phải lặp lại installation task. Không sửa checker/state/master plan hoặc tự chuyển WP.

## Thay đổi và lý do

- [Charter v0.3](../01-project-charter.md): problem hypotheses, năm objectives, users, input/output, scope theo mức, non-goals, GAP/hard gates, open decisions, ownership và ví dụ hành vi.
- [Brief v0.1](../00-project-brief.md): đầu vào ngắn không phụ thuộc tên model; không cần đọc lịch sử chat để hiểu bài toán.
- [Task packet](MODEL-NEUTRAL-TASK.md): mẫu giao một việc, đọc theo lớp, repo/chat capability boundary và 10 comprehension scenarios chưa chạy.
- AGENTS/harness/index/README và prepared WP03 card nối brief vào đường đọc. Giữ task-specific contracts bắt buộc; không cắt guardrails để vừa context.

Hai ambiguity đã làm rõ: MVP đích có ba năng lực không có nghĩa code cả ba ngay; giảng viên/upload không tự có authority publish hoặc bypass quarantine. Tách model phát triển repo với model trong sản phẩm; không freeze model/provider/threshold mới.

## Verification

Chạy thật `py -3.11 -B scripts/agent_harness.py verify --run brief-01-r1 --require-local-data`, exit 0 ngày 2026-09-06:

| Check | Kết quả | Giới hạn |
|---|---|---|
| `check-task --task docs/harness/tasks/WP03-01.json` | Valid declaration sau thêm brief vào read_first | Không thực thi WP-03 |
| `check --run brief-01-r1` | 9/9 changed paths trong allowlist | Card được tạo trước baseline; không theo dõi ignored/remote actions |
| Harness unittest profile | 31/31 PASS | Checker behavior trên synthetic repos, không model behavior |
| Structure với `--require-local-data` | 598/598 PASS; 48 Python files; 17 PDF checksums; không skip | Structure/syntax/links/source integrity, không nghiệm thu nội dung |
| `git diff --check` | PASS | Whitespace, không semantic correctness |

Self-review đối chiếu charter/brief với master plan và metric clarification: không đổi scope product, metric threshold, quyền hoặc trạng thái nhãn; giữ so sánh đủ evidence khác so sánh thiếu evidence. Đã bổ sung từ vựng ngắn và tách goal IDs OBJ-* khỏi metric IDs. Không rerun context regression vì không sửa experiment/code; không lấy 23/23 lịch sử làm kết quả lượt này. Không thay state/checker/master plan, không commit/push.

## Còn mở

Chưa phỏng vấn người học/giảng viên; chưa chốt môn/nguồn chuẩn/rights/rubric chuyên môn/production budget. B-01..10 và model-level H metrics NOT RUN. Brief ngắn giúp giảm context phải nạp nhưng chưa chứng minh model nhỏ sẽ tuân thủ; không có token estimate chung cho mọi tokenizer. Checker không kiểm semantic truth của brief hoặc quyền do user cấp.

## Tiếp tục

Người dùng review bài toán và các OPEN decisions trong charter; chỉ hỏi lựa chọn nào thực sự chặn task kế tiếp. Nếu tiếp tục nghiên cứu, dùng WP03-01 inventory/scorer specification theo master plan hiện hành; không nhảy product. State vẫn WP-03 tiếp theo và ASTRA pending. Khi thử model khác, cấp packet read-only/synthetic trước, chấm comprehension và bằng chứng; không gửi pilot PDF/derivatives ra hosted provider mặc định.
