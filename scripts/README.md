# Repository maintenance scripts

Script tại đây chỉ phục vụ vận hành repo, không chứa logic AI hoặc nghiệp vụ backend.

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
