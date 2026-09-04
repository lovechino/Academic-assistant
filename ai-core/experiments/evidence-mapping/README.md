# Evidence mapping audit

Verifier offline cho [VOER DSA mapping v0.1](../../../data/evaluation/silver/voer-dsa-evidence-map-v0.1/README.md). Chỉ dùng Python 3.11+ standard library, không model/parser SDK hay network.

```powershell
python -X utf8 ai-core/experiments/evidence-mapping/verify_mapping.py
```

Lệnh chỉ đọc nguồn/mapping và in kết quả: kiểm tra checksum/version, quote/offset, quan hệ claim/group/locator và 12 tình huống toy cố ý bỏ evidence. Không ghi lại pack, không chạy retrieval/generation, không đụng PDF helper. Logic coverage chỉ làm việc với locator IDs đã biết, chưa phải matching retrieved chunks.

Normalization là legacy tương thích silver để định vị text, không bảo toàn layout/DOM/math. Chưa được dùng để chọn chunking/indexing hoặc làm parser sản phẩm. Offset là Unicode codepoint, không trực tiếp dùng làm chỉ số JavaScript UTF-16.
