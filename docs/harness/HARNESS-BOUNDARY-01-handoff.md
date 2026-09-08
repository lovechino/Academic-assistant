# HARNESS-BOUNDARY-01 — HPC-2 boundary documentation

2026-09-08. Status: verified_local (documentation/tooling) / needs review.
User “Tiếp tục” sau review prototype: soạn boundary contract trước chọn môi trường,
không host provisioning/execution hoặc product GO. Card
[HARNESS-BOUNDARY-01](tasks/HARNESS-BOUNDARY-01.json), run `harness-boundary-01-r1`;
`check-task` pass, `begin` tạo baseline **241 Git-visible files** trước output edits.
Card được tạo trước baseline, không phải authority tự chứng thực. Giữ dirty edits
cũ, không rebaseline. Product state vẫn WP-04/pre_product_research và ASTRA pending
theo [control record](WP02-WP04-reconciliation.md); không đổi plan/state.

## Đầu ra và review disposition

- [Boundary contract](HPC2-BOUNDARY-CONTRACT.md): owner/resource/action matrix,
  separate read/write/base inputs, bounded channels, protected observation,
  materialization requirements, quotas và 8 host probes NOT RUN.
- [Design](PATCH-ONLY-DESIGN.md): forward pointer và điểm tiếp tục; giữ HPD pending.
- [Test map](PATCH-ONLY-TEST-MAP.md): map HB-01..08 sang cases cũ; không tăng executions.
- [Harness README](README.md): entrypoint mới để model tiếp theo phục hồi đúng bước.
- Handoff này: evidence/limits. Exact five outputs; không sửa code/tests/validator,
  core harness/journal/checkers, source/data, root instructions hoặc product contracts.

Đã tìm bằng `rg --files docs/harness` và các references HPC/PATCH/BOUNDARY: reuse
design/test-map làm nguồn, thêm đúng một docs owner cho host boundary, không runtime
module/source placement mới. Review trước chỉ không thấy defect trong subset thuần;
không là independent security certification, user sign-off hoặc HPC-2 acceptance.
36 tests + 6 probes + 3.000 mutations được ghi **historical**, không rerun probes
hoặc đăng ký incidents giả trong lượt soạn docs. Các four integration gaps được
chuyển thành requirements, không chuyển thành findings “đã sửa bằng tài liệu”.

## Checks

| Check | Actual | Limits |
|---|---|---|
| status/check-task/begin | Hợp lệ; baseline 241 files | Không approval |
| `harness_journal.py capture --run harness-boundary-01-r1 --event boundary-contract-verify-01 --phase verify --require-local-data` | passed; harness exit 0, 120 methods; structure exit 0, 878/878, 56 Python syntax files, 17 PDF hashes, 0 failures/skips | Fresh existing fixed checks; không thêm test hoặc chạy HB host probes |
| `agent_harness.py check --run harness-boundary-01-r1`, `git diff --check` | Exact five outputs; diff check exit 0 | Không scope/state/HEAD drift hoặc sửa preexisting files ngoài scope |

Capture finished `2026-09-07T23:13:49.190423+00:00` (ngày 2026-09-08 giờ Việt Nam),
baseline hash `70fa43ac72bd340e1a5be1a445b9a4dc7c2ad5a1e82efff6f5d49cf7e95ed47f`.
Observed tree `4b36b8d0f48354066005a9f18f65b4852bc767385633358f3953698755edc190`
là trước cập nhật evidence vào handoff này, không phải hash revision cuối sau sửa
handoff. Sau đó kiểm lại scope/structure/diff, không sửa code/tests. Capture chỉ ghi
local diagnostic journal, không protected audit/approval. Không coi full verify gồm
36 parser methods chạy lại là host review hoặc rerun six probes/mutation generator.

## Self-review và còn mở

Contract tách proposal khỏi quyền ghi/accept; không cho worker tự cấp context,
đọc toàn repo hoặc biến safe path string thành safe filesystem object. Required
packet khác synthetic notes baseline, candidate channel khác logs. Observer failure,
timeout/cancel/cleanup failure không được biến thành PASS hoặc tự retry. Quyền network
mặc định deny trong proposed host trial; chưa có gateway/provider được chọn.

HB-01..08 executed=0, NOT RUN=8. Cơ chế isolation/IPC/authentication/control store,
OS primitives chống link race, aggregate budgets/cleanup grace, positive-control
observer và evidence retention chưa chọn. Không claim enforce hay production-ready.
ARCH-02 và manual Academic giữ nguyên; task chỉ development tooling documentation.
HPC-3 receipt/currentness/replay/cancel/crash và HPC-4 backup/restore vẫn pending,
không triển khai rollback checkout. PDF chỉ có thể được checksum bởi fixed structure
profile; không OCR/parser/model/external processing hoặc historical generators.

## Handoff tiếp theo

Đọc boundary contract + design + API limits. Có thể lập comparison công nghệ và
khảo sát prerequisites read-only trong scope riêng; không tự install, enable OS
features, chỉnh ACL/network, chạy worker hoặc apply changeset. User/operator cần
chốt HB-D01..04 trước provisioning/test; HB-D05 thuộc phase sau. Maintainer/reviewer
cần đối chiếu requirements thực với khả năng môi trường, không lấy draft làm sign-off.
ASTRA-01/explicit scoped product GO chưa có; không đổi master plan từ task maintenance.
