# Workflow tabletop: mô phỏng offline

Chạy state machine trên fixtures hoàn toàn synthetic để quan sát packing loss, citation version, revoke và cache scope. Đây là experiment ngoài runtime; không phải Backend/Frontend/agent đã triển khai.

## Chạy lại

Từ root, Python 3.11+ standard library, không cài thêm package:

```powershell
python -X utf8 ai-core/experiments/workflow-tabletop/simulate.py
```

Chỉ đọc fixture, in JSON và trả exit code 0 khi baseline khớp kỳ vọng, các mutation dự kiến được phát hiện, span probes đạt. Không ghi file, gọi network/model hoặc import code sản phẩm. Lệnh không tự cập nhật kết quả lịch sử.

Đọc kết quả gọn/từng bước trong PowerShell:

```powershell
$tabletopResult = python -X utf8 ai-core/experiments/workflow-tabletop/simulate.py | ConvertFrom-Json
$tabletopResult.counts
$tabletopResult.baseline_runs | Select-Object id, actual
($tabletopResult.baseline_runs | Where-Object id -eq 'SIM-03').trace | Format-List step, stage, status, result, observed
```

## Artifacts

- [Fixtures và kết quả local](../../../data/evaluation/simulations/grounded-qa-tabletop-v0.1/README.md).
- [Báo cáo từng bước và quyết định còn mở](../../../docs/workflows/02-tabletop-simulation-v0.1.md).

11 baseline scenarios, 9 guard mutations, 7 span probes. Hai nguồn, hai actor và ba claim được viết mới; chỉ mượn hình dạng so sánh stack/queue, không dùng source/nhãn/approval thật. Claims chọn từ template: không kiểm tra semantic entailment hoặc khả năng phát hiện thiếu kiến thức của LLM. `generator_stub_calls` là số gọi hàm giả lập, không phải số gọi model.

State chuyển tuần tự tại ranh giới stage, observer dùng quyền/revision hiện hành để ghi nhận exposures. Không mô phỏng atomic check/send, mạng phân tán hoặc thu hồi dữ liệu đã tải xuống. Fixture policy (một repair, partial allowed, buffer trước delivery) là giả định cần người dùng duyệt, không phải cấu hình sản phẩm đã chốt.

Kết quả JSON lưu fixture/runner hashes; so sánh hash trước khi dùng lại. Khi đổi fixture/runner phải ghi rõ phiên bản và chạy lại có chủ đích; không ghi đè lịch sử rồi coi cùng một run. Không dùng số pass của simulator làm điểm RAG hoặc RBAC production.
