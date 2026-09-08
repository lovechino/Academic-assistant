# Placement packet — trước khi tạo hoặc sửa source

2026-09-07. Mẫu dùng chung cho mọi model, không phải task card đã được cấp quyền.
Đọc [source placement map](../architecture/11-source-placement-blueprint-v0.1.md)
và [model-neutral task](MODEL-NEUTRAL-TASK.md). Không tự chọn task từ mẫu này.

## Mẫu điền vào task/handoff

```text
USER_REQUEST: Yêu cầu thật đang thực hiện
RESPONSIBILITY: Một trách nhiệm cụ thể, không chỉ tên feature
OWNER_AND_LAYER: Component + layer theo source placement map
CONTRACTS: Contract/path/section liên quan; thiếu gì ghi unknown
EXISTING_SEARCH:
  - Lệnh rg thực chạy, phạm vi, symbol/synonyms đã tìm
  - File/caller/test đọc được; có gì tương tự, không chỉ tên trùng
DECISION: reuse | extend | new | placement_change_proposed
RATIONALE: Vì sao không tạo implementation cạnh tranh
EXACT_OUTPUTS: Các file đúng scope; tên trong map là dự kiến, không tự cấp quyền
DEPENDENCIES: Được import/gọi gì; forbidden back-edges/private imports
TEST_PLACEMENT: Unit / adapter / cross-component; negative cases cần kiểm
OPEN_DECISIONS_AND_GATE: Chưa chọn gì; user GO nào thực có hoặc vẫn pending
CHECKS: Lệnh thực chạy + result; không có tools ghi NOT RUN
REVIEW: Ai thực review; chưa review ghi pending, không giả reviewer identity
```

Với repo writes, dùng JSON card hiện hành: ghi responsibility/placement trong
`objective` và `acceptance`, map/inputs trong `read_first`, exact files trong
`allowed_files`/`required_outputs`. Không thêm keys mới vào schema card để rồi sửa
checker cho qua. File handoff cần nằm trong allowlist từ trước `begin`.

## Ví dụ đã điền — minh họa sau GO, KHÔNG phải lệnh triển khai

```text
RESPONSIBILITY: Pure context-packing policy
OWNER_AND_LAYER: AI Core / retrieval
CONTRACTS: evidence-packet + required-context contracts cần đọc đầy đủ cho task
EXISTING_SEARCH: NOT RUN trong ví dụ; worker phải tìm packing/context và callers
DECISION: Chưa chốt trước khi tìm implementation có sẵn
EXACT_OUTPUTS: Dự kiến ai-core/src/academic_ai/retrieval/packing.py
DEPENDENCIES: AI domain types; không backend, provider SDK, eval labels hoặc DB
TEST_PLACEMENT: AI unit tests cho policy + integration caller khi được giao
OPEN_DECISIONS_AND_GATE: Product GO vẫn chưa có; không được begin task runtime
CHECKS: NOT RUN — đây là template, không execution evidence
REVIEW: pending
```

Feature đi qua nhiều component phải chia trách nhiệm, không copy thuật toán sang
Backend/Frontend. Reviewer read-only không tạo card/run/journal finding chỉ để điền
template. Một writer mỗi checkout; khi đổi model, phục hồi card/run/baseline cũ.

## Reviewer kiểm gì ngoài tests?

- Search thực đã tìm implementation/caller gần nghĩa chưa? Nếu không có tools,
  “không tìm thấy” không được biến thành “không tồn tại”.
- Public DTO mapping có truy về contract hay tự nhân bản authorization policy?
- Có QA loop trong cả application và agents, lifecycle trong cả use case và worker,
  hoặc source-fetch state trong cả feature và shared component không?
- Có import runtime từ experiments/evaluation, copy expected labels hoặc fake auth
  thành security thật không?
- Phạm vi/checks đúng revision? Kết quả layout không được gọi import/semantic PASS.

Checklist này là yêu cầu review, không semantic detector hoặc approval tự động.
