# Chunking R1 — fixed với structure-aware

Experiment chỉ đọc: tạo cùng input từ source-preserving serializer cho 4 module, rồi so fixed và structure-aware trong cùng budget. Boundary builders không đọc enrichment; annotations chỉ được dùng post-hoc để diagnostic group/dependency.

## Runtime local đã pin

- Python 3.12.14 virtual environment nằm ở `tmp/r1-tokenizer-venv` (gitignored).
- `tokenizers==0.23.2`; dependency lock đầy đủ ở [config](config-v0.1.json).
- `BAAI/bge-m3/tokenizer.json`, revision `5617a9f61b028005a4858fdac845db406aefb181`, SHA-256 `21106b6d7dab2952c1d496fb21d5dc9db75c28ed361a05f5020bbba27810dd08`, nằm ở `tmp/tokenizers/...` (gitignored).
- Không tải model weights, không upload corpus. Truncation/padding bị tắt; cap 512 gồm 2 special tokens, body 510, overlap/header 0.

```powershell
./tmp/r1-tokenizer-venv/Scripts/python.exe -X utf8 ai-core/experiments/chunking-r1/run_boundary_comparison.py --summary
./tmp/r1-tokenizer-venv/Scripts/python.exe -X utf8 ai-core/experiments/chunking-r1/audit_boundary_comparison.py
```

Hai script chỉ xuất JSON ra stdout. `--offset/--limit` phân trang JSON transport, không phải chunk semantic. Muốn tái hiện cần tải đúng tokenizer file/hash từ revision đã pin; không tự fallback sang `main` mới hơn.

Fixed dùng tokenizer offsets liên tiếp. Structure dùng outermost heading/p/li/tr/figure và fallback atom cho source text mồ côi, greedy trong section; atom vượt cap giữ nguyên nhưng ineligible. Các container tags có thể đi qua chunks trong review projection; gate bảo vệ áp dụng cho semantic atoms/rich nodes và source spans, không tuyên bố mỗi chunk là HTML cân bằng.

[Run/report local](../../../data/processed/voer-dsa-chunking-r1-v0.1/README.md). 1.728 audit checks, 3 additional guards, 9 mutations. Không phải retrieval, generation hoặc human gold evaluation.
