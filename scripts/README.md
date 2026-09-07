# Repository maintenance scripts

Script tại đây chỉ phục vụ vận hành repo, không chứa logic AI hoặc nghiệp vụ backend.

## Agent work harness

[Hướng dẫn và giới hạn](../docs/harness/README.md): `agent_harness.py` kiểm tra state/task, snapshot Git-visible bytes trước sửa, phát hiện scope drift và chạy fixed local checks. Không gọi model, không tự phê duyệt hoặc chuyển phase.

```powershell
py -3.11 -B scripts/agent_harness.py status
py -3.11 -B -m unittest discover -s scripts/tests -p test_agent_harness.py -v
```

Tests này là repo-tooling tests trên synthetic temporary Git repositories, không phải runtime/integration tests của ba component.

## Kiểm tra cấu trúc không sửa dữ liệu

```powershell
python scripts/verify_structure.py
```

Trong workspace có corpus local:

```powershell
python scripts/verify_structure.py --require-local-data
```

Chỉ cần Python standard library. Kiểm tra thư mục/ownership markers, syntax Python, root resolution của hai helper đã chuyển, Markdown links và checksum PDF khi có manifest. Không import/chạy helper khảo sát, không viết manifest, không cài thư viện hoặc gọi network.

Chế độ mặc định cho phép checkout source chưa có `data/` local, báo rõ data check/link bị thiếu được skip. `--require-local-data` biến các thiếu sót đó thành lỗi. Đây không phải test parser/RAG/backend/frontend runtime.
