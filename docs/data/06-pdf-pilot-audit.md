# Báo cáo PDF pilot Việt Nam v0.1

Ngày: 2026-09-04. Trạng thái: local audit hoàn tất; chưa phải corpus production hay bộ gold.

## 1. Kết quả thực tế

Đã tải 17 PDF qua endpoint công khai của ba trường/học viện, không qua trang re-upload. Có 16 tài liệu slide/giới thiệu môn và một đề cương. Giữ nguyên PDF; bổ sung URL nguồn, SHA-256 và metadata ở [manifest](../../data/raw/pdf-pilot/manifest.json).

| Nhóm | PDF | Trang PDF vật lý | Giá trị đối với pilot |
|---|---:|---:|---|
| [VNUA - CTDL & giải thuật](https://dse.vnua.edu.vn/ncthang/pth02003/) | 6 | 96 | Slide handout, công thức, hình và bảng đề cương nối trang |
| [VNUA - hệ quản trị CSDL](https://dse.vnua.edu.vn/cnpm/th03005/SlidePDF/) | 5 | 33 | Screenshot phần mềm, SQL, nhiều slide/trang |
| [VNU-UET - CSDL](https://uet.vnu.edu.vn/~chaunh/slide/index.htm) | 5 | 68 | Ký hiệu ER, slide ít chữ, ảnh minh họa, chuẩn hóa |
| [HCMUAF - cung cầu](https://www2.hcmuaf.edu.vn/data/nmduc/KT%20vi%20mo%20Ch2%20cung%20cau%20%5BCompatibility%20Mode%5D.pdf) | 1 | 39 | Đồ thị vector, bảng số, công thức và hình chưa hoàn chỉnh |
| Tổng | 17 | 236 | Ba nhóm môn, chưa cân bằng về nguồn/môn/layout |

Không gọi 236 trang là 236 slide: có handout nhiều slide trong một trang.

Số đo toàn bộ corpus từ `pdfplumber 0.11.9`:

- Dung lượng: 8.251.851 bytes, khoảng 8,25 MB thập phân.
- 17/17 checksum khác nhau; không kết luận không có nội dung gần trùng.
- 236/236 trang đọc được object/text; không trang nào có text trống.
- 8 trang có dưới 80 ký tự được trích xuất.
- 659 lượt xuất hiện ảnh nhúng, **không phải 659 hình kiến thức độc lập**. Có logo/background lặp lại.
- 13.852 object vector, **không phải 13.852 biểu đồ**. Có đường viền bảng và trang trí.
- Heuristic `text<80 AND image_bbox_union_ratio>0.8` không tìm được scan candidate. Điều này không chứng minh corpus không chứa text trong ảnh.

Số đo không phải độ chính xác parser. File có nhiều text vẫn có thể sai thứ tự, thiếu nhãn hình hoặc dính cột.

## 2. Cách kiểm tra

1. Kiểm tra page count bằng Poppler `pdfinfo` và `pypdf`.
2. Đọc text/object từng trang; đóng bộ nhớ cache trang sau đo.
3. Đo hợp diện tích bounding box ảnh đã clip vào trang, không cộng chồng diện tích ảnh.
4. Render 13 trang có chủ đích bằng Poppler, xem đầy đủ trang; không chọn ngẫu nhiên, không đại diện thống kê cho toàn corpus.
5. Kiểm tra chéo thêm HCMUAF p39 và VNUA chương 2 p5 bằng PDFium vì Poppler cảnh báo font `Symbol`/`ArialUnicode`. Hai bản render khớp trên các thành phần liên quan đã xem; chưa kiểm tra mọi glyph/trang.

Output tái lập: [summary](../../data/processed/pdf-pilot/audit-v0.1/summary.json), [page profile](../../data/processed/pdf-pilot/audit-v0.1/page-profile.json), [ghi chú visual](../../data/evaluation/silver/vn-pdf-visual-v0.1/page-audit.json). Helper offline nằm ở `ai-core/experiments/pdf-pilot/profile_local.py`; đây chỉ là công cụ khảo sát, không phải mã nguồn sản phẩm. Không cài/chạy Docling hoặc model embedding trong bước này.

## 3. Phát hiện làm thay đổi thiết kế

### A. Phải có tầng logical slide trước chunk

- VNUA `Chuong01.pdf`, p1: hai slide xếp dọc; mỗi slide có heading/footer riêng.
- VNUA `Chuong02.pdf`, p5: slide trên thuộc mục 2.2, slide dưới thuộc mục 2.3. Ghép hết trang thành một child sẽ trộn hai mục.
- VNUA `Bai1_ThietkeCSDL_Bang.pdf`, p2: bốn slide trong bố cục 2x2, nhãn slide 5, 6, 7, 8. Phải đọc hết từng slide theo thứ tự trái trên, phải trên, trái dưới, phải dưới; không đọc ngang dòng qua hai slide.

Quyết định: `document -> physical_page -> logical_slide/region -> elements`. Logical slide có section riêng nhưng vẫn được nối parent/neighbor khi bài giảng tiếp diễn. Không mặc định mọi PDF đều có layout giống ba trang này.

### B. Hình quan trọng có thể không nằm trong image stream

HCMUAF có 39 trang nhưng nhiều đồ thị được tạo bằng vector. VNU-UET có trang chỉ ít chữ kèm các ký hiệu ER mà hình dạng mới phân biệt được nghĩa. Một classifier dựa riêng vào số ảnh nhúng hoặc lượng text sẽ phân loại sai.

Quyết định: giữ bản render trang và vùng hình; phân loại nội dung dựa cả layout, text, vector và visual review. Không bỏ bản render sau OCR.

### C. Bảng có thể đứt giữa một hàng

Đề cương VNUA PTH02003, p3-p4: hàng của chủ đề danh sách liên kết nối qua trang; trang 4 không lặp toàn bộ header bảng đầu. Phía dưới p4 còn có bảng thực hành khác.

Quyết định: nối đúng row fragment, kế thừa header có nguồn gốc p3; không ghép hai bảng khác nhau. `source_locators` phải giữ cả p3 và p4, kể cả khi logical table là một object.

### D. Không được hoàn thiện hình rồi gọi đó là nguồn

HCMUAF p9: vùng đồ thị thị trường có dấu hỏi, không có đường đã vẽ. P32 có cột để người học điền. Đây là trạng thái của tài liệu, không phải OCR miss cần tự lấp.

Quyết định: phân biệt `observed`, `derived` và `unknown`; đánh dấu `exercise_placeholder`. Chỉ mô tả cái nhìn thấy khi query hỏi về nguồn. Nếu cần suy luận, nói rõ đó là suy luận và áp dụng chính sách bài tập tương ứng.

### E. Số liệu, đơn vị và dấu toán học phải đi cùng hình

HCMUAF p33 có đồ thị cân bằng; đơn vị rõ hơn trong bảng liền trước p32. P39 có dấu âm, phân số và chỉ số dưới. Cắt riêng điểm giao hoặc OCR rời nhãn sẽ mất điều kiện đọc.

Quyết định: crop chứa đủ trục/legend/nhãn; cho phép neighbor expansion để lấy đơn vị, nhưng không gán đơn vị từ trang khác nếu liên kết chưa xác nhận.

## 4. Quyền và độ mới

Toàn bộ 17 PDF đang `quarantined`, **chưa xác minh giấy phép mở**. Download công khai không tương đương quyền đưa vào RAG production hoặc chia sẻ lại. Bộ test/ảnh dẫn xuất cũng không được public mặc nhiên. Xem [source notice](../../data/raw/pdf-pilot/SOURCE-NOTICE.md).

Trang chỉ mục UET ghi cập nhật 05/08/2025, không đủ chứng minh từng PDF là phiên bản 2025. Một số tài liệu VNUA/HCMUAF cũ; không dùng để trả lời quy chế hay thao tác phần mềm hiện hành mà thiếu version qualification. Tác giả tài liệu không tự động là content owner/giáo viên phê duyệt cho dự án.

## 5. Những gì còn thiếu

- Scan tiếng Việt có ground-truth transcription; ảnh chụp lệch, mờ, chữ viết tay.
- Giáo trình prose dài, nhiều cột; toán với ma trận/hệ phương trình phức tạp.
- Mẫu Kinh tế vi mô từ nguồn khác được phép sử dụng, tránh tập test lệch về một chương/một tác giả.
- Gold layout/table/figure annotations do người review; 13 trang hiện chỉ là assistant-inspected silver.
- Đánh giá hiệu năng thực của parser/chunker/retriever; không có điểm Recall/accuracy nào được công bố ở bước này.

Cập nhật vòng kế tiếp: [parser diagnostic vòng 0](../evaluation/07-parser-diagnostic-round0.md) đã đo thứ tự giữa slide và một số lỗi extraction trên 13 trang. Chưa có OCR/retrieval/agent benchmark. [Rà soát nguồn scan](07-ocr-scan-source-review.md) chưa nhập thêm file mới.

## 6. Bước kế tiếp đã định nghĩa

1. Review quyền trước khi mở rộng việc dùng bộ PDF cách ly.
2. Duyệt 13 page annotations và 8 visual QA nháp; xác nhận bbox/đáp án, không sinh tiếp hàng loạt.
3. Bổ sung mẫu scan và giáo trình dài có quyền rõ; mở parser audit lên khoảng 30 trang có chủ đích.
4. So sánh parser trên cùng annotations; sau đó mới chunk/index và chạy các nhánh text/vision trong [thiết kế multimodal](../architecture/03-visual-pdf-retrieval.md) và [evaluation plan](../evaluation/06-visual-pdf-evaluation.md).
