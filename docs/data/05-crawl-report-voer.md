# Báo cáo crawl VOER — pilot corpus v0.1

Ngày báo cáo: 2026-09-04

Snapshot: `voer-2026-09-04-r1`

Trạng thái: thu thập xong; chỉ dùng ở mức `research_reference`.

## 1. Mục tiêu

Tạo một corpus tiếng Việt đủ đa dạng để tiếp tục thiết kế ingestion, retrieval, citation và evaluation trong khi dự án chưa có giảng viên/content owner. Đây là corpus thay thế tạm thời cho nghiên cứu kỹ thuật, không phải giáo trình chính thức của trung tâm.

## 2. Nguồn và phạm vi

Nguồn được chọn là Thư viện Học liệu Mở Việt Nam (VOER). Trang nguồn ghi tài liệu dùng giấy phép Creative Commons Attribution 3.0 trừ khi có ngoại lệ. Snapshot `robots.txt` ghi `search=yes,ai-train=no,use=reference`; dự án vì vậy không dùng corpus này cho training/fine-tuning.

| Môn pilot | Tác giả/đơn vị trên nguồn | Module | Từ gần đúng | Bảng | Ảnh tải được / tham chiếu | Lý do chọn |
|---|---|---:|---:|---:|---:|---|
| Cấu trúc dữ liệu và giải thuật | Khoa CNTT ĐHSP KT Hưng Yên | 16 | 28.989 | 9 | 69/69 | Nội dung kỹ thuật, code, ký hiệu và nhiều hình |
| Cơ sở dữ liệu | Ths. Phạm Hoàng Nhung | 7 | 21.073 | 8 | 88/95 | Khái niệm, ER, chuẩn hóa, bảng và sơ đồ |
| Kinh tế học vi mô | PGS., TS. Lê Thế Giới | 11 | 7.668 | 0 | 1/1 | Miền phi CNTT để kiểm tra routing và thuật ngữ |
| **Tổng** |  | **34** | **57.730** | **17** | **158/165** |  |

## 3. Những gì đã lưu

- HTML của ba collection page.
- JSON gốc cho từng module, bao gồm `material_id`, title, HTML text, language, modified time và attribution.
- 158 ảnh được module tham chiếu.
- Bản sao `robots.txt`, source notice, manifest và module manifest.
- Checksum cho từng cây môn và toàn payload.

Không có nội dung đăng nhập, đề thi, đáp án hay dữ liệu cá nhân được chủ động thu thập.

## 4. Kiểm tra chất lượng

| Kiểm tra | Kết quả | Xử lý dự kiến |
|---|---|---|
| Module JSON | 34/34 lấy được | Có thể dùng cho parser baseline |
| Ngôn ngữ | 34/34 khai báo `vi` | Giữ metadata gốc |
| Ảnh | 158/165 tải được | 7 ảnh thiếu phải tạo cảnh báo khi ingest |
| Decode ảnh | 158/158 decode được | 5 JPEG mang đuôi `.png`; nhận diện theo magic bytes |
| Ký tự lỗi `U+FFFD` | 0 | Pass |
| Private Use Unicode | 7 ký tự | Đưa vào regression test normalization |
| Trùng nội dung | Không thấy hash trùng trong 34 module | Tiếp tục kiểm tra gần-trùng ở bước chunking |
| Tính thời sự | Nội dung/sửa đổi nguồn chủ yếu năm 2013 | Không dùng cho câu hỏi cần kiến thức cập nhật |

## 5. Rủi ro học thuật

1. Tác giả trên VOER là attribution nguồn, không phải content owner của dự án.
2. Chưa có giảng viên xác nhận độ đúng, độ đầy đủ hoặc mức phù hợp với chương trình hiện hành.
3. Có lỗi chính tả và cách ghi thuật ngữ cũ trong nguồn; raw snapshot không được sửa âm thầm.
4. Hai module thực hành cây chỉ có khoảng 24-28 từ, phụ thuộc mạnh vào hình hoặc nội dung thiếu.
5. Bảy hình bị mất đều ở module “Thiết kế cơ sở dữ liệu vật lý”, nên module này không phù hợp làm gold evidence về phần sơ đồ.
6. Giấy phép mở không đồng nghĩa với authoritative curriculum và không thay thế review chuyên môn.

## 6. Cách dùng cho evaluation khi chưa có giáo viên

Có thể làm ngay:

- Tạo câu hỏi `silver` từ heading và đoạn văn, rồi kiểm tra tự động rằng đáp án có evidence span.
- Tạo retrieval cases theo `material_id`: single-hop, cross-section và negative query.
- Tạo citation cases yêu cầu trả đúng collection/module và không viện dẫn ảnh bị thiếu.
- Tạo robustness cases từ lỗi chính tả, Unicode đặc biệt, bảng HTML và ảnh sai extension.
- Dùng câu hỏi có đáp án trích xuất trực tiếp để đo Recall@k, MRR, nDCG và citation entailment.

Chưa được làm:

- Gọi câu hỏi sinh tự động là `gold`.
- Báo “độ chính xác học thuật ≥80%” chỉ từ corpus này.
- Dùng tài liệu như phiên bản chính thức cho một học kỳ cụ thể.
- Train/fine-tune mô hình trên snapshot.

## 7. Quyết định gate

N1 mới đạt phần `corpus acquisition`, provenance và technical profiling. Gate N1 chưa qua vì cả ba môn chưa có content owner/reviewer nội bộ và chưa xác nhận mức phù hợp với chương trình đào tạo hiện hành.

Bước kế tiếp hợp lý là tạo một `silver evaluation pack` khoảng 60 case từ snapshot này, sau đó giữ riêng một hàng đợi 20-30 case cần chuyên gia review khi tìm được giảng viên.

