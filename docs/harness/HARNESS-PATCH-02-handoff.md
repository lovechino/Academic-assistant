# HARNESS-PATCH-02 — HPC-1 prototype handoff

2026-09-08. Status: **verified_local / needs review**, không checkpoint acceptance.
User yêu cầu tiếp tục sau patch-only design: bounded pure validator + synthetic tests,
không launcher/applier/sandbox/model/product. [Card](tasks/HARNESS-PATCH-02.json), run
`harness-patch-02-r1`, baseline 236 Git-visible files được tạo trước sửa 8 outputs.
Card được tạo trước baseline, không là authority độc lập. Run đã phục hồi sau turn
interruptions, giữ baseline cũ; `check` lúc thiếu outputs báo missing đúng kỳ vọng,
không scope/state/HEAD drift hoặc rebaseline. Repo dirty từ các task trước được giữ.

Master plan vẫn WP-04 / pre_product_research; plan SHA-256
`062e9216632341880e66104b9a2955ddc5c965f86b7c75b1bf7bd37950e67b04`;
[current control record](WP02-WP04-reconciliation.md). Scope acceptance không là ASTRA
review completion hoặc explicit scoped product GO; cả gate vẫn pending.

## Placement packet và đầu ra

- USER_REQUEST: tiếp tục bước HPC-1 đã đề xuất, thử tooling trong bộ nhớ.
- RESPONSIBILITY / OWNER: development changeset parser/validator ở `scripts/`,
  không AI Core/Backend/Frontend runtime. Contract: [patch design §4/7](PATCH-ONLY-DESIGN.md),
  [source placement map](../architecture/11-source-placement-blueprint-v0.1.md).
- EXISTING_SEARCH: `rg` tìm `harness_patch`, `validate_changeset`, path helpers trong
  core harness, placement checker và `scripts/tests`; đã đọc owners/callers/tests.
  Existing helpers gắn filesystem/Git và task schema, không phải pure changeset API.
- DECISION: **new** canonical owner `scripts/harness_patch_validator.py`; **reuse**
  fixed unittest discovery + structure profiles nguyên trạng, không copy Git/I/O
  helpers hoặc sửa generic path policy thành profile notes mới.
- DEPENDENCIES: dataclasses/hashlib/json/re; argparse chỉ built-in demo entrypoint.
  Không third-party SDK, filesystem/Git/DB/network hoặc candidate execution.
- TEST_PLACEMENT: `scripts/tests/test_agent_harness_patch_validator.py`; không tạo
  competing source tree. Review độc lập pending; self-review không làm human sign-off.

8 outputs so với run baseline:

1. [Validator](../../scripts/harness_patch_validator.py): bounded parsing, exact scope,
   synthetic base/preconditions, immutable result và safe diagnostic.
2. [Tests](../../scripts/tests/test_agent_harness_patch_validator.py): 36 methods với
   positive controls/adversarial/limit boundaries, không host/model execution.
3. [API và limits](PATCH-VALIDATOR.md): cách thử, identity, unsupported và điểm dừng.
4. Handoff này: scope/evidence/risks cho model tiếp theo.
5. [Design](PATCH-ONLY-DESIGN.md): forward update parser subset, giữ pending decisions.
6. [Test map](PATCH-ONLY-TEST-MAP.md): 13 scoped parser pass, 1 partial, 26 NOT RUN
   trong inventory 40 specs; không đổi chúng thành 40 test executions.
7. [Harness README](README.md): entrypoint phục hồi prototype, không đổi state/gate.
8. [Scripts README](../../scripts/README.md): discovery và built-in demo usage.

## Evidence thực chạy

| Command/profile | Kết quả | Phạm vi |
|---|---|---|
| `agent_harness.py status` / `check-task`, `begin` và resume `check` | status hợp lệ; baseline cũ giữ nguyên; missing-output check trong tiến trình được khai báo | Không bypass check hoặc tạo lại run |
| `py -3.11 -B -m unittest discover -s scripts/tests -p test_agent_harness_patch_validator.py -v` | exit 0; 36/36 methods pass, 0 fail/skip; runner reported 0.708s | Exposed synthetic developer tests, không OS/model/human metric |
| `py -3.11 -B scripts/harness_patch_validator.py --demo` | exit 0; valid 1 file/38 bytes, sau đó `OUT_OF_SCOPE`, applied false | Candidate digest `54a53e0b1c245a5a9b3ed7a2bfe03a150d892abcacf0279105be185ef411928e`; không repo writes |
| `py -3.11 -B scripts/harness_journal.py capture --run harness-patch-02-r1 --event patch-validator-verify-01 --phase verify --require-local-data` | outcome passed; harness exit 0 / 120 methods; structure exit 0 / 862 of 862, 0 failures/skips, 56 Python syntax files, 17 PDF hashes | Fresh fixed verify: 84 existing + 36 new methods; không product behavior hoặc model benchmark |
| `py -3.11 -B scripts/agent_harness.py check --run harness-patch-02-r1` và `git diff --check` | Exact 8 outputs, không scope/state/HEAD drift; diff check exit 0 | Repo preexisting dirty changes giữ nguyên |

Capture hoàn tất `2026-09-07T23:02:15.867664+00:00` (2026-09-08 giờ Việt Nam).
Baseline digest `4592ab7958450d9d1af0f1d0a5b2fd135cb336c3b404810b9aad1bacfc2f57ef`;
observed tree `f6032c3f725919d1bfc6790bf4ba35bfd2384d67cae6e9d3be67afe2f77f054d` là
tree **trước** cập nhật kết quả vào handoff này. Sau đó chỉ cập nhật handoff/docs,
không code/tests; final scope/structure check đọc trạng thái cuối. Không gọi event
cũ như fresh verification của hash tree sau sửa handoff.

Core harness SHA-256 vẫn
`466421b7bddc5d8c3baa8220dae96bc18605f8fba8d353003f3db87dbecdbe6c`; journal vẫn
`fe3956ebe5caf4b74d4cb24990dda7d2e3a3fbde9e58608efc8adae92e9c5b77`.
Capture ghi observation vào ignored local journal theo workflow hiện có, không tích
hợp validator vào DB hoặc biến row thành authority; không thay checker/discovery.

## Self-review, residual risks và NOT RUN

- Schema/key/type checks, baseline/grant/action/bytes binding và lexical collisions
  được đối chiếu code/tests; không phát hiện contradiction cần sửa trong subset này.
  Kết luận chỉ self-review bounded, không independent security review.
- Context là giả định của caller, frozen objects không authenticated hoặc tamper-proof.
  Bytes baseline không xác thực filesystem loại regular/no-link; không sealed tree.
  Chặn claimed enforcement/host integration cho tới HPC-2 controls được kiểm chứng.
- 10s hard deadline, packet/token admission, queue/attempt/process quotas chưa có.
  Byte/depth/structure caps không chứng minh worst-case timing hay tổng memory.
- Source HTML/URL/shell/ANSI vẫn có thể hợp content: không execute trong validator,
  không tự render/log content; downstream safe rendering và semantic review chưa có.
- Không live policy/revoke/expiry, protected interpreter/checker, receipt/reviewer,
  CAS/idempotency/cancel/late callback hoặc recovery. HP-T03/04, host/acceptance/model
  probes và toàn HPC-2/3/4 chưa chạy; H-01..07/model success NOT_MEASURED.
- ARCH-02 giữ nguyên, task không sửa academic routing/metrics. Không model, paid calls,
  install, external processing, PDF parsing/generation, deployment, commit hoặc push.
  Kiểm PDF checksum nếu profile chạy là read-only integrity, không xử lý nội dung.
- Prototype không backup/rollback files. Recovery design vẫn yêu cầu new authorized
  change/current-base/review; không reset checkout dirty hoặc coi hash/SQLite là backup.

## Tiếp tục có giới hạn

Đọc [API](PATCH-VALIDATOR.md), code/tests, design và execution map cho một review
read-only trước HPC-2. Không tạo card/run cho riêng review. Chỉ sau khi chốt host
isolation, ownership của controls/quota và quyền người dùng mới cân nhắc task môi
trường thật; không tự cài VM/container/ACL, launcher/promoter từ generic continue.
Không đổi WP-04/state hoặc bypass ASTRA-01 + explicit scoped product GO.
