# Silver evaluation pack VOER v0.1

Ngày tạo: 2026-09-04

## Kết quả

Đã tạo 60 case phát triển dựa trên snapshot `voer-2026-09-04-r1`:

| Suite | Số case | Trọng tâm |
|---|---:|---|
| Academic | 30 | QA grounded, retrieval, citation, abstention |
| Learning | 10 | Misconception, scaffolding, academic integrity |
| Router | 12 | Academic, Learning, Hub, multi-route, clarify |
| Safety | 8 | Injection, training restriction, graded work, RBAC giả lập |

Tất cả case đang ở `silver_draft`, split `dev`, chưa có human review.

## Kiểm tra cấu trúc đã chạy

| Kiểm tra | Kết quả |
|---|---:|
| JSONL parse thành công | 60/60 |
| ID duy nhất | 60/60 |
| Trường bắt buộc theo suite | 60/60 |
| Evidence span tồn tại chính xác trong nguồn đã chuẩn hóa | 66/66 |
| Phân bố Academic khớp đặc tả | 30/30 |

Kiểm tra trên chỉ xác nhận tính toàn vẹn dữ liệu và provenance, không xác nhận correctness học thuật.

## Coverage Academic

Phân bố 30 case bám seed specification:

- 8 lookup.
- 6 explanation.
- 5 multi-hop.
- 3 comparison.
- 3 table/figure/formula.
- 3 unanswerable.
- 2 staleness/version.

Các case answerable có candidate evidence theo `material_id`. Case unanswerable kiểm tra ba failure mode thực tế: chủ đề không có trong corpus, ảnh nguồn bị mất và câu hỏi đòi dữ liệu pháp luật hiện hành.

## Những gì pack đo được ngay

- Retrieval Recall@5/10 và MRR trên các case có evidence.
- Grounded answer/citation pass rate ở chế độ oracle và end-to-end.
- Correct abstention cho dữ liệu thiếu hoặc lỗi thời.
- Learning behavior ở các hiểu lầm phổ biến.
- Route accuracy cho single-intent, multi-intent và thiếu ngữ cảnh.
- Compliance với academic integrity và chống prompt injection.

## Những gì chưa thể kết luận

- Độ chính xác học thuật cuối cùng.
- Mức phù hợp với chương trình đào tạo hiện hành.
- RBAC thực trên corpus nội bộ.
- Chất lượng OCR PDF/slide vì VOER snapshot chủ yếu là HTML.
- KPI nghiệm thu ≥80% vì chưa có nhãn chuyên gia và frozen test.

## Gate để nâng cấp

1. Chạy kiểm tra tự động về JSON schema, ID, evidence substring và distribution.
2. Review thủ công mọi reference answer để loại lỗi sinh tự động.
3. Khi có chuyên gia, ưu tiên review 30 Academic case trước.
4. Mở rộng Learning từ 10 lên 20, Router từ 12 lên 30 và tạo 12 RBAC case trên tài liệu có phân quyền thật.
5. Tách module giữa dev/validation/test trước khi freeze.

Chi tiết sử dụng nằm trong `data/evaluation/silver/voer-v0.1/README.md`.
