# Vòng đời tài liệu v0.1

Ngày cập nhật: 2026-09-04

## 1. Trạng thái

| Trạng thái | Ý nghĩa | Có được retrieval không? |
|---|---|:---:|
| draft | Đang nhập metadata/chỉnh nội dung | Không |
| in_review | Đã gửi content owner/curator kiểm tra | Không với Student; chỉ reviewer |
| changes_requested | Cần sửa trước khi duyệt | Không |
| published | Đã duyệt, đang có hiệu lực | Có trong access scope |
| archived | Hết hiệu lực hoặc bị thay thế | Không theo mặc định |
| rejected | Không được chấp nhận | Không |
| quarantined | Có nghi vấn quyền, bảo mật hoặc chất lượng | Không với mọi retrieval thông thường |

## 2. Luồng chính

`Draft -> In review -> Published -> Archived`

Nhánh xử lý:

- `In review -> Changes requested -> Draft`.
- `In review -> Rejected`.
- Bất kỳ trạng thái nào có sự cố nghiêm trọng `-> Quarantined`.
- `Archived -> Draft` khi tạo phiên bản mới; không sửa trực tiếp bản đã archive.

## 3. Checklist review trước publish

- Owner và nguồn gốc rõ ràng.
- Quyền ingest, trích dẫn và hiển thị rõ ràng.
- Course, term, version và audience đúng.
- Không chứa PII hoặc assessment confidential ngoài dự kiến.
- Nội dung đọc được; OCR/reading order đạt mức chấp nhận.
- Page/slide numbering khớp file người dùng mở.
- Không trùng phiên bản đang active hoặc quan hệ supersedes đã khai báo.
- Access scope đã được reviewer kiểm tra.
- Ngày review tiếp theo được xác định.

## 4. Versioning

- `document_id` giữ nguyên cho cùng một logical document.
- Mỗi thay đổi nội dung tạo `document_version` mới.
- Không ghi đè file đã dùng trong một corpus snapshot.
- Phiên bản mới chỉ thay phiên bản cũ sau khi publish thành công.
- Gold case phải trỏ tới version cụ thể; nếu source đổi, case cần review lại.
- Khi rollback, khôi phục một version đã duyệt thay vì tái sử dụng index không rõ nguồn.

## 5. Tài liệu mâu thuẫn

Khi hai nguồn khác nhau:

1. Đánh dấu loại mâu thuẫn: khác term, khác version, lỗi nội dung hoặc quan điểm học thuật hợp lệ.
2. Course Owner xác định nguồn authoritative hoặc cho phép trình bày cả hai.
3. Ghi effective term và provenance note.
4. Assistant phải nêu sự khác biệt và citation riêng nếu cả hai đều hợp lệ.
5. Không để reranker tự quyết định tài liệu chính thức chỉ dựa vào similarity score.

## 6. Archive và xóa

- Archive khi tài liệu hết kỳ, bị thay thế hoặc không còn được phép phục vụ.
- Archive phải loại khỏi active retrieval và invalidate cache liên quan.
- Xóa vật lý chỉ khi có policy retention và người có thẩm quyền phê duyệt.
- Audit metadata về quyết định archive/delete được giữ theo chính sách của trung tâm.

## 7. Service levels đề xuất

- Tài liệu mới không xuất hiện với sinh viên trước khi review hoàn tất.
- Thay đổi quyền hoặc quarantine phải có hiệu lực ngay ở retrieval và cache.
- Tài liệu published được review lại theo học kỳ hoặc khi có phiên bản mới.
- Báo cáo định kỳ liệt kê tài liệu sắp hết hiệu lực, thiếu owner hoặc thiếu rights evidence.

