# Vòng đời tài liệu v0.1

Ngày cập nhật: 2026-09-06 — clarification v0.1.1

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

### Intake trước lifecycle

File vừa upload chưa được coi là `draft` trong content repository. Nó đi qua intake riêng:

`received -> static_scanning -> isolated_parsing -> duplicate_analysis -> awaiting_security_rights_content_review -> approved_for_staging`.

Chỉ sau `approved_for_staging` mới tạo một immutable material version hoặc đề xuất liên kết với material hiện có. Representation trước đó gắn submission + immutable source snapshot; promotion tạo binding mới, không sửa lineage cũ. Raw/extracted content trong intake không vào serving database/index và không được learner retrieval/model/viewer đọc. Assigned reviewer/isolated inspector được đọc exact submission trong restricted inspection lane bằng action riêng; quyền này không phải quyền publish. Similarity/exact-byte match chỉ tạo duplicate candidate; quyết định liên kết, tạo version hay giữ material riêng là lifecycle action có thẩm quyền. Xem [secure upload, quarantine và duplicate resolution](05-secure-upload-quarantine-deduplication-v0.1.md) và [Content Unit & Index Contract](../architecture/07-content-unit-index-contract-v0.1.md).

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

- `material_id` giữ nguyên cho cùng một logical material trong tenant; ID phải opaque và không suy ra từ content hash.
- Mỗi thay đổi nội dung hoặc publication metadata có nghĩa tạo immutable `material_version_id` mới.
- Không ghi đè file đã dùng trong một corpus snapshot.
- Phiên bản mới chỉ thay phiên bản cũ sau khi publish thành công.
- Gold case phải trỏ tới version cụ thể; nếu source đổi, case cần review lại.
- Khi rollback, khôi phục một version đã duyệt thay vì tái sử dụng index không rõ nguồn.
- Hai tenant hoặc hai owner có cùng bytes vẫn có submission, material, approval và quyền riêng; storage dedup nội bộ nếu có không được merge lifecycle.

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

### Serving index activation và revoke

- Một material version được duyệt chỉ đi vào isolated staging build trước; build manifest phải xác nhận version, representation/chunk profile, projection coverage, approval và policy epoch.
- Chỉ build đã verify và còn current mới được chuyển active bằng alias/snapshot switch nguyên tử hoặc cơ chế tương đương.
- Job cũ không được promote sau khi material, approval, publishing-workload authority hoặc relevant resource/publication revision thay đổi. Unrelated user membership change không buộc rebuild vector; current query policy vẫn được kiểm tra riêng.
- Khi revoke/ACL đổi, Backend/PDP phải từ chối protected read ngay; không chờ vector/lexical index xóa vật lý xong mới chặn.
- Cache phải mang policy epoch/effective scope; projection cũ được tombstone và purge bất đồng bộ, đồng thời đo propagation latency.
- Mỗi query pin một `serving_snapshot_id` cho lexical/dense/graph/representation; activation dùng catalog compare-and-set được serialize với revoke/update. Không mix các surface từ hai build. Chi tiết và ordering point revoke/delivery nằm tại [boundary contract](../../contracts/content-unit-index.md).

## 7. Service levels đề xuất

- Tài liệu mới không xuất hiện với sinh viên trước khi review hoàn tất.
- Thay đổi quyền hoặc quarantine phải có hiệu lực ngay ở retrieval và cache.
- Tài liệu published được review lại theo học kỳ hoặc khi có phiên bản mới.
- Báo cáo định kỳ liệt kê tài liệu sắp hết hiệu lực, thiếu owner hoặc thiếu rights evidence.
