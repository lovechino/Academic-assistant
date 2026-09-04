# Dữ liệu của Academic Assistant

Thư mục này chứa dữ liệu phục vụ nghiên cứu và đánh giá trong giai đoạn chuẩn bị. Dữ liệu ở đây chưa mặc nhiên thuộc production corpus.

## Corpus hiện có

- `raw/voer/`: snapshot học liệu công khai từ Thư viện Học liệu Mở Việt Nam (VOER), thu thập ngày 2026-09-04.
- Ba bộ môn: Cấu trúc dữ liệu và giải thuật, Cơ sở dữ liệu, Kinh tế học vi mô.
- 34 module tiếng Việt, khoảng 57.730 từ và 158 tài nguyên hình ảnh tải được.

Xem [báo cáo crawl](../docs/data/05-crawl-report-voer.md), [source notice](raw/voer/SOURCE-NOTICE.md) và [manifest](raw/voer/MANIFEST.md) trước khi sử dụng.

## Phân loại sử dụng

Corpus VOER hiện được gắn nhãn `research_reference`:

- Được dùng để thử ingestion, parsing, retrieval, citation và tạo evaluation case nháp.
- Không được dùng làm nguồn chính thức cho một học kỳ cụ thể khi chưa có content owner xác nhận.
- Không được dùng để train hoặc fine-tune mô hình.
- Khi hiển thị nội dung hoặc citation phải giữ tên tác giả, tên bộ sưu tập và URL nguồn.

Lý do áp dụng chính sách thận trọng này: VOER công bố giấy phép CC BY 3.0 trừ khi có ngoại lệ, đồng thời `robots.txt` tại thời điểm crawl ghi `ai-train=no,use=reference`. Bản sao `robots.txt` đã được lưu cùng snapshot để truy vết.

## Nguyên tắc dữ liệu

### PDF pilot bổ sung ngày 2026-09-04

`raw/pdf-pilot/quarantine/` có 17 PDF công khai từ VNUA, VNU-UET và HCMUAF, tổng cộng 236 trang vật lý. Chưa xác minh giấy phép mở: **không áp chính sách VOER sang bộ PDF này**. Chỉ đang giữ cho local reference audit, không production/index public, không redistribute, không training hoặc gửi lên dịch vụ OCR/VLM ngoài theo mặc định.

Xem [source notice](raw/pdf-pilot/SOURCE-NOTICE.md), [manifest](raw/pdf-pilot/manifest.json) và [báo cáo](../docs/data/06-pdf-pilot-audit.md). Số đo tự động ở `processed/pdf-pilot/audit-v0.1/`; 13 trang visual audit và 8 QA nháp ở `evaluation/silver/vn-pdf-visual-v0.1/`. Tất cả dẫn xuất kế thừa hạn chế nguồn.

Diagnostic extraction và 12 structural probes nằm ở `processed/pdf-pilot/layout-diagnostic-v0.1/`; chưa phải gold/test kín, không phải corpus đã index. Xem [kết quả vòng 0](../docs/evaluation/07-parser-diagnostic-round0.md). Giữ annotations v0.1; các vấn đề mới được ghi riêng trong `review-issues.json` để review trước khi tạo version tiếp theo.

### Quy tắc chung

1. `raw/` là dữ liệu nguồn bất biến; không sửa lỗi chính tả hoặc HTML tại đây.
2. Dữ liệu làm sạch/chunk về sau phải nằm ở thư mục khác và trỏ lại `material_id`.
3. Không tự gán tác giả nguồn thành content owner nội bộ.
4. Câu hỏi và đáp án sinh tự động chỉ là `silver`; chỉ thành `gold` sau review chuyên môn.
5. Mọi lần đánh giá phải ghi snapshot ID trong manifest.
