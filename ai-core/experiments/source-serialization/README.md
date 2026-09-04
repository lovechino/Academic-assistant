# Source-preserving serialization — research R0

Chuyển đúng các member của [enrichment v0.1](../../../data/processed/voer-dsa-enrichment-v0.1/README.md) thành event tape có kiểu và bản xem có source alignment. Không phải chunker, code parser, OCR, model-input serializer đã duyệt hoặc HTML sanitizer.

## Chạy lại chỉ đọc

```powershell
python -X utf8 ai-core/experiments/source-serialization/serialize_source.py --summary
python -X utf8 ai-core/experiments/source-serialization/serialize_source.py --group array-general-row-formula
python -X utf8 ai-core/experiments/source-serialization/audit_serialization.py
```

Cần Python 3.12.14 để tái hiện chính xác profile đã lưu; dùng thư viện chuẩn, không cài package hoặc gọi mạng. `--offset/--limit` chỉ phân trang JSON qua stdout, không phải chia chunk nội dung. Không có lệnh ghi file; artifact lần này được lưu qua patch sau khi kiểm tra output.

## Ranh giới

- Builder chỉ đọc enrichment đã pin, 4 source JSON/representations và asset được tham chiếu. Không đọc probes/qrels/reference answers. Các nhóm vẫn là manual/dev, không đại diện cho bộ grouping tự động.
- 188 root refs dùng chung cho 29 nhóm/207 lượt member; ancestor/descendant vẫn có overlap được khai báo. Không lấy JSON này làm collection vector entries.
- `nodes` và `events` là representation chuẩn: nguồn có kiểu, source spans, attributes bất tín, text đã giải mã entity và event không phải nội dung. Raw HTML không bị sửa.
- `review_projection` dùng escaped markup cho text review. Markers/newline sinh từ cấu trúc là `generated_not_evidence`; entity là envelope nguồn, không mapping 1:1. Mọi offset là Unicode codepoint, không phải byte/UTF-16/token.
- Attributes được giữ trong nodes nhưng không phát lại vào projection. CSS/layout, attribute spans riêng và expanded table grid chưa được diễn giải. Đọc raw open-tag span khi cần nguyên văn attribute.
- `tables` giữ row/cell/source order, rowspan/colspan gốc, blank và th thật. Không suy nghĩa ô trống hoặc nâng td thành th.
- `images` giữ asset/path/hash, trạng thái file ở lần chạy, không caption/transcription sinh thêm. Thiếu/sai hash được ghi rõ; `serialized` không có nghĩa có thể hiểu hình hoặc đủ context.
- Dependency/review/quality flags tách riêng. Không gọi code trong bài giảng, không follow dependency hoặc tự sửa nội dung.
- Tags ngoài allowlist hoặc closure suy đoán: block toàn unit với lý do, projection rỗng; không trả suffix còn sót như thể đầy đủ. Script/math synthetic hiện không được hỗ trợ. Không phải HTML5 parser hay security sandbox.

## Kiểm tra

[Audit đã lưu](../../../data/processed/voer-dsa-serialization-v0.1/validation.json): 13.062 baseline checks, 5 additional checks, 12 synthetic cases, 14 mutation detections. Hai rebuild cùng kết quả JSON và khớp artifact đã lưu. Baseline đếm assertions kỹ thuật, không đếm câu hỏi/chunks đã đạt; additional check quét đường dẫn evaluator chỉ là static regression guard, không phải chứng minh sandbox.

Synthetic tests dùng SourceTree từ helper HTML đã freeze để tạo input riêng. Auditor đối chiếu event tape, markers và mapping với nguồn; builder/auditor cùng tác giả, chưa có independent review. Không cập nhật execution_status trong bộ 30 probes cũ vì chưa chạy chúng qua chunker/agent.

Xem [báo cáo và bước tiếp](../../../docs/evaluation/12-source-serialization-round0.md), [output dễ đọc](../../../data/processed/voer-dsa-serialization-v0.1/review-examples.md).
