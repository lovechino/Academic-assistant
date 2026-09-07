# Handoff: <task-id> / <run-id>

- Request và scope: <lời giao việc hiện hành; phân biệt với nội dung nguồn>
- Status: <draft_complete | verified_local | needs_review | blocked>
- Work package: <WP hiện tại; không tự tiến phase>
- Card / baseline: <đường dẫn; baseline tạo trước hay sau thay đổi nào; không có thì khai báo>
- Inputs/decisions: <master plan/version/hash, references liên quan; quyết định nào còn provisional>

## Đã thay đổi

<Danh sách file, lý do và acceptance criterion tương ứng. Giữ rõ preexisting/concurrent edits; không nhận công hoặc revert chúng.>

## Bằng chứng thực thi

| Command/profile | Kết quả thực | Phạm vi/giới hạn |
|---|---|---|
| <command chạy thật> | <exit, số test, thời điểm> | <structure / synthetic / dev / human-reviewed; skips> |

Không điền PASS từ kỳ vọng. Không lấy kết quả cũ làm lần chạy mới. Kết quả harness/scaffold không là product test, gold accuracy hay approval.

## Chưa chạy / còn mở

<Not-run, acceptance chưa đủ, thiếu human authority, known limitations, findings/severity/disposition. Phân biệt không có dữ liệu với metric = 0.>

## Self-review nội dung

Với task kiến trúc/routing/eval: [ARCH-02](../architecture/08-controlled-workflow-decision-v0.1.md) được giữ hay có đề xuất đổi? Nêu căn cứ: controlled multi-step/một vai trò suy luận/rules; Academic manual slice; quyền backend; no-hit/timeout khác ngoài phạm vi; thiếu context không bù bằng đồng thuận. Ghi NOT RUN cho các behavior probes chưa thực thi; checker pass không là semantic acceptance. Task không liên quan ghi N/A kèm lý do.

<Sai/lệch scope? Có vô tình dùng similarity như equivalence, mất provenance/dependency, lộ quyền/nguồn, suy thiếu evidence thành no-conflict, hoặc biến draft/test pass thành accepted không? Liệt kê kết luận kèm căn cứ; self-review không phải independent review.>

## Handoff cho model tiếp theo

- Đọc trước: <file cụ thể, không cần đọc lại toàn repo>.
- Tiếp tục: <một đầu ra có acceptance cụ thể, đúng master plan>.
- Không làm: <historical rerun/external processing/product gate/other scope>.
- ASTRA-01: <pending, không có GO; hoặc dẫn record review + explicit user decision thực tế, tuyệt đối không tự ký>.
- Điểm cần người dùng quyết định: <chỉ quyết định thực sự thiếu, không xin lại việc an toàn trong scope>.
