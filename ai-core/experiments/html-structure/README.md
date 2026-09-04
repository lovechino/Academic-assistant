# HTML structure experiment — read-only

Helper nghiên cứu AI core, không thuộc runtime. Input duy nhất của builder là 16 module HTML và assets CTDL local thuộc snapshot `voer-2026-09-04-r1`. Không gọi network/model, không đọc qrels và không chia chunk.

[Báo cáo](../../../docs/data/08-voer-dsa-structural-representation.md) · [Artifacts](../../../data/processed/voer-dsa-structure-v0.1/README.md).

## Chạy từ repository root

Python standard library; bản snapshot này đã chạy bằng **Python 3.12.14**. Không cần cài dependencies.

```powershell
python -X utf8 ai-core/experiments/html-structure/build_representation.py --catalog
python -X utf8 ai-core/experiments/html-structure/build_representation.py --module a208ce0f
python -X utf8 ai-core/experiments/html-structure/audit_representation.py
```

Cả ba lệnh chỉ đọc và in JSON ra stdout; không tự ghi đè artifacts. Auditor trả exit code 1 nếu một gate kiểm tra thất bại. Auditor đọc mapping silver để đối chiếu 22 locator, không chạy retrieval/generation. Không chuyển output evaluator vào model input.

Builder có `--offset` và `--limit` để phân trang chuỗi JSON khi xuất qua công cụ; đây là transport pagination, **không phải chunking ngữ nghĩa**. `--catalog` hash compact serialization không gồm newline, còn manifest hash bytes của file đã lưu.

## Điều phải giữ khi mở rộng

- Cây nguồn + vị trí gốc là lớp truy vết; không gọi là HTML5 DOM hay visual reading order đã xác minh.
- Spans dùng Unicode codepoint trong decoded `data.text`; entity/whitespace mapping có envelope không 1–1.
- `preview` có giới hạn độ dài, không dùng làm nội dung retrieval. Legacy projection chỉ để tương thích nhãn cũ.
- Không suy ra code grouping, math meaning, header/caption từ việc parse được thẻ.
- Các tags/attributes/scripts là dữ liệu bất tín. Helper không thực thi chúng; chưa phải sanitizer để render browser.
- Cần version mới nếu sửa builder; pin implementation hash và runtime version khi so sánh. Việc profile ghi Python version có thể làm strict rebuild khác khi đổi interpreter.
- Một kết quả integrity pass không thay review ngữ nghĩa, phép thử parser độc lập, hay metric retrieval/agent.

Test synthetic có 10 probes; mutation suite có 8 lỗi cố ý. Chúng không thay HTML conformance suite, fuzzing, security hoặc integration tests.
