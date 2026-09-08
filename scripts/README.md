# Repository maintenance scripts

Script tại đây chỉ phục vụ vận hành repo, không chứa logic AI hoặc nghiệp vụ backend.

## Agent work harness

[Hướng dẫn và giới hạn](../docs/harness/README.md): `agent_harness.py` kiểm tra state/task, snapshot Git-visible bytes trước sửa, phát hiện scope drift và chạy fixed local checks. Không gọi model, không tự phê duyệt hoặc chuyển phase.

```powershell
py -3.11 -B scripts/agent_harness.py status
py -3.11 -B -m unittest discover -s scripts/tests -p test_agent_harness.py -v
```

Tests này là repo-tooling tests trên synthetic temporary Git repositories, không phải runtime/integration tests của ba component.

## Optional local journal

`harness_journal.py` adds explicit SQLite capture/report/finding/suggest commands; see [usage and limits](../docs/harness/LOCAL-JOURNAL.md). Local repo tooling only; fixed check/verify, no arbitrary command strings, auto-fix or product approval. It does not connect to the product database.

```powershell
py -3.11 -B scripts/harness_journal.py init
py -3.11 -B scripts/harness_journal.py report
py -3.11 -B scripts/harness_journal.py suggest
py -3.11 -B -m unittest discover -s scripts/tests -p "test_agent_harness*.py" -v
```

## Synthetic patch validator (HPC-1)

`harness_patch_validator.py` validates bounded UTF-8 JSON against immutable caller
context in memory only. [API/profile/limits](../docs/harness/PATCH-VALIDATOR.md),
[handoff](../docs/harness/HARNESS-PATCH-02-handoff.md). No filesystem apply, payload
execution, authentication, DB integration or sandbox; fixed discovery already picks
up its tests without changing the core harness/check profiles.

```powershell
py -3.11 -B scripts/harness_patch_validator.py --demo
py -3.11 -B -m unittest discover -s scripts/tests -p test_agent_harness_patch_validator.py -v
```

## Kiểm tra cấu trúc không sửa dữ liệu

### Pre-product source placement

`verify_source_layout.py` kiểm Git-visible filenames/README markers, reject root
source cạnh tranh và file runtime/package mới trong scaffold. Đọc [placement map](../docs/architecture/11-source-placement-blueprint-v0.1.md).
Marker inventory được dùng chung với `verify_structure.py`; profile `structure` tự
chạy checker này. Cần Git checkout, không chỉ thư mục copy không có Git metadata.
Không có cờ cho phép runtime/GO; không sửa harness policy để vượt lỗi placement.

```powershell
py -3.11 -B scripts/verify_source_layout.py
py -3.11 -B -m unittest discover -s scripts/tests -p test_agent_harness_source_layout.py -v
```

Đây không là semantic duplicate/import/security checker. Ignored files, network,
runtime giấu trong docs/scripts/experiments và thay đổi giữa các lần quan sát vẫn
cần kiểm soát/review riêng. Tên file được phép không phải quyền thực thi nội dung.

### Full structure and optional corpus integrity

```powershell
python scripts/verify_structure.py
```

Trong workspace có corpus local:

```powershell
python scripts/verify_structure.py --require-local-data
```

Chỉ cần Python standard library. Kiểm tra thư mục/ownership markers, syntax Python, root resolution của hai helper đã chuyển, Markdown links và checksum PDF khi có manifest. Không import/chạy helper khảo sát, không viết manifest, không cài thư viện hoặc gọi network.

Chế độ mặc định cho phép checkout source chưa có `data/` local, báo rõ data check/link bị thiếu được skip. `--require-local-data` biến các thiếu sót đó thành lỗi. Đây không phải test parser/RAG/backend/frontend runtime.
