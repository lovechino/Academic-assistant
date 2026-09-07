# Handoff ARCH-02 / arch-02-r1

- Request: ngày 2026-09-06, người dùng đồng ý phương án 2 và yêu cầu cập nhật files, cả harness. Chỉ ghi định hướng/docs, không product implementation.
- Status: `verified_local` cho docs và checks cơ học; không là independent semantic acceptance hoặc product readiness.
- Work package: maintenance trong namespace HARNESS-01; research next vẫn WP-03.
- Card: [ARCH-02.json](tasks/ARCH-02.json), được tạo trước baseline; bản thân card không là output nằm trong 11-file scope.
- Baseline: `tmp/agent-harness/arch-02-r1.json`, tạo trước mọi output edit; 184 Git-visible paths, gồm sửa đổi/untracked đã có. Không rebaseline hoặc revert sửa đổi của người dùng.
- Plan: [master plan v0.2](../roadmap/03-master-plan-v0.2.md), SHA-256 `feadc8d4236aeea03f3cd54a46b4aa25b45da09cee07e6843f977da534ca0636`; state/hash/next WP không thay đổi.

## Đã thay đổi

- [Quyết định ARCH-02](../architecture/08-controlled-workflow-decision-v0.1.md): phương án đã chọn, trách nhiệm, 13 exposed review cases NOT RUN, nhu cầu đo và điều kiện cân nhắc multi-agent về sau. Không có implementation state machine.
- AGENTS, brief, charter, workflow pilot và docs index: cùng trỏ tới quyết định, giữ manual Academic slice/authority/gate; không sửa kết quả SIM lịch sử.
- [Harness README](README.md), [model-neutral packet](MODEL-NEUTRAL-TASK.md), [handoff template](HANDOFF-TEMPLATE.md): checklist kiến trúc và probes B-11..13; không tuyên bố semantic enforcement bằng máy.
- [WP03-01 card](tasks/WP03-01.json): thêm decision input và acceptance về các nhu cầu đo. Vẫn prepared/not executed; không tăng allowed_files hoặc chạy WP-03 trong lượt này.
- Handoff này ghi bằng chứng và giới hạn; không sửa checker/tests, runtime, dependencies, nguồn hoặc artifacts nghiên cứu cũ.

## Bằng chứng thực thi

| Command/profile | Kết quả thực | Giới hạn |
|---|---|---|
| `py -3.11 -B scripts/agent_harness.py status` | pre_product_research, WP-03, ASTRA pending | Snapshot tiến độ, không approval |
| `check-task --task docs/harness/tasks/ARCH-02.json` | declared_task_valid_NOT_authorization | Card khớp schema; request là căn cứ riêng |
| `begin --task docs/harness/tasks/ARCH-02.json --run arch-02-r1` | baseline_created, 184 paths | Local mutable/unsigned, không sandbox |

| `check-task --task docs/harness/tasks/WP03-01.json` | declared_task_valid_NOT_authorization | Prepared card sau cập nhật hợp schema, chưa begin WP-03 |
| `py -3.11 -B scripts/agent_harness.py verify --run arch-02-r1 --require-local-data` | all_checks_passed; 31/31 harness tests; 624/624 structure checks; 48 Python files, 17 PDF hashes; skips = [] | Kết thúc 2026-09-06T12:03:18Z; đúng 11 output paths, ASTRA pending; không là product/model tests |
| `git diff --check` | Exit 0, không output | Whitespace của tracked diff, không chấm ngữ nghĩa/untracked content |

Đã ghi kết quả sau run thật. Chỉ chỉnh đoạn handoff kết quả này sau verification; thực hiện final scope check trên cùng baseline, không rebaseline. Các con số trên thuộc lượt ARCH-02, không thay số lịch sử ở report/handoff cũ.

## Chưa chạy / còn mở

- ARCH-C01..13 và B-11..13: NOT RUN qua model/router, chưa independent review; đây là expected cases công khai, không gold/hidden labels.
- Không gọi model/provider, không spawn subagent, không chạy A/B/C, RAGAS hay đo GAP/cost/latency. Không chạy lại 23 context regression methods hoặc historical generators trong task docs này.
- Chưa chọn generator, router implementation, SDK/topology, confidence threshold, budget hoặc ngưỡng nâng multi-agent. Quyết định hướng đi không phải kết quả tốt hơn baseline khác.
- Harness checker vẫn chỉ kiểm cơ học/path/hash/profile; model có thể không hiểu hoặc bỏ qua instructions. Cập nhật docs không biến nó thành sandbox/semantic validator.
- Human academic labels/rights, WP-03 scorer closure, WP-02 readiness và ASTRA-01 vẫn mở.

## Self-review nội dung

ARCH-02 được giữ nhất quán qua entry points và future card: controlled multi-step không tự thành multi-agent; backend giữ quyền; rules không bỏ mixed/follow-up intent; no-hit/timeout khác out-of-scope; không lấy agreement thay evidence. So sánh đủ hai phía có positive control, thiếu một phía có giới hạn; không luôn từ chối để lấy điểm đẹp. A/B/C tương lai đều phải giữ security gates. Đây là self-review của cùng assistant, chưa là independent acceptance.

Đã dùng OpenAI Docs để đối chiếu phân biệt workflow/agent và nguyên tắc eval-driven complexity; citation nằm trong ARCH-02. Những ca và quyết định cụ thể của repo là đề xuất/định hướng của dự án, không phải kết quả do nguồn web chứng minh.

## Handoff cho model tiếp theo

- Đọc brief, harness README, ARCH-02, state/master plan và card phù hợp request hiện hành. Với kiến trúc/routing/eval, cung cấp decision content cho model không có file tools.
- Tiếp theo: WP-03 inventory/scorer specification, đưa ARCH-C01..13 vào nhóm exposed NOT RUN và ghi gaps/scorer needs; không gọi WP-03 hoàn tất chỉ vì kiểm kê xong.
- Không làm: tự đổi sang multi-agent, external processing, model run, publish/index hoặc triển khai product orchestration.
- ASTRA-01 vẫn pending review và explicit user GO. Không thiếu quyết định để hoàn tất task docs này; các lựa chọn triển khai/budget để review đúng bước sau.
