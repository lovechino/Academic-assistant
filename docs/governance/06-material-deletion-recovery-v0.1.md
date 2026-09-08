# Xóa nhầm học liệu: thùng rác và khôi phục — đề xuất v0.1

2026-09-07. Theo yêu cầu bổ sung của người dùng; **thiết kế để review, chưa tính năng hoạt động**, chưa GO. Không áp dụng cho Git/source file của repo. Backend sở hữu lifecycle/quyền; AI không có tool tự xóa/restore. Chi tiết ở [recovery contract](../../contracts/material-recovery.md), scenarios ở [REC test map](../evaluation/37-wp04-behavior-security-review-v0.1.md).

## 1. Phân biệt thao tác

| Ý định | Cơ chế đề xuất | Không được hiểu thành |
|---|---|---|
| Bỏ khỏi danh sách cá nhân | Xóa shortcut/bookmark, use case riêng | Xóa nguồn của trường/người khác |
| Xóa nhầm upload/version/material | Soft-delete → restricted trash → restore-to-review trong hạn | Xóa bytes ngay hoặc restore mọi quyền cũ |
| Ngừng dùng tài liệu hết kỳ | Archive/revoke, giữ provenance | Thùng rác hoặc xóa vật lý |
| Quay về nội dung version trước | Tạo version/promotion mới tham chiếu nguồn cũ, kiểm current review/rights | Đổi active index về bản cũ vô điều kiện |
| Xóa vĩnh viễn / sự cố lưu trữ | Purge được phê duyệt / backup disaster recovery riêng | Nút undo luôn cứu được file |

## 2. Luồng cho xóa nhầm

`Xác nhận đúng target → soft-delete + deny serving → thùng rác hạn chế → restore có quyền → nonserving review → publish riêng khi đủ điều kiện`.

Xóa có hiệu lực ở quyền theo thứ tự authoritative; không đợi vector/cache cleanup. Query đang chạy, lịch sử answer có influence từ tài liệu, link viewer cũ và share/public binding đều phải kiểm lại. Bytes đã gửi hợp lệ trước xóa không thu hồi được.

Khôi phục giữ original bytes/checksum/snapshot/locator nếu còn, nhưng tạo recovery revision mới; không rewind epoch, ACL, membership, shares hay approval. Tài liệu có PII/secret/nghi injection vẫn restricted; không đưa thẳng vào DB/index phục vụ hoặc gọi model để “kiểm tra giúp”. Không có reviewer thì nằm pending. UI nói rõ **“đã khôi phục để chờ duyệt”**, không “đã sẵn sàng cho Assistant”.

Submission, version và material-wide delete khác nhau. Material parent bị xóa chặn mọi child; restore parent không tự hồi child đã xóa độc lập. Không auto restore dependency, không ghi đè newer active version. Chỉ nội dung có đầy đủ context và quyền sau review mới được tái phục vụ.

## 3. Quyền và dữ liệu trùng

Tách quyền xem metadata thùng rác, xóa mềm, restore-to-review và purge. Role mapping chi tiết **chưa duyệt**; mặc định deny nếu không có current explicit assignment. Người upload không tự có quyền xóa mọi bản cùng bytes; system admin không tự được đọc học liệu. Recipient của share không được sửa lifecycle nguồn owner.

Hai giảng viên upload cùng bytes vẫn là hai submissions/rights. Xóa một bản chỉ hủy binding của bản đó. Storage chỉ purge bytes khi authoritative references/holds/restore reservations đều cho phép; không dựa vào filename, similarity hoặc refcount đọc trước một race. Không lộ “bản trùng nằm ở trường khác”.

## 4. Race, retry và backup

- Delete → old publish job/cached answer/late restore callback: lifecycle generation mới chặn resurrection.
- Restore đua purge: chỉ một thao tác thắng tại fenced reservation/claim; purge đã thắng thì không hứa restore, dù còn vài file vật lý. Restore lỗi không để lộ bản nửa hoàn chỉnh.
- Double-click/retry: cùng operation không xóa hai lần, không gia hạn trash deadline; replay cũ không undo lần xóa mới.
- Backup cũ phải restore vào isolation và đối chiếu current delete/revoke/purge journal trước serving. Thiếu journal → block. Không khôi phục active ACL/index từ backup như sự thật hiện tại.
- Purge/crypto-erasure xong không bảo đảm phục hồi. Hold giữ bytes không cấp quyền đọc hoặc tự gia hạn quyền restore; nghĩa vụ retention/erasure cần policy owner chốt.

## 5. Quyết định còn mở, không dùng default ngầm

| Quyết định | Cần chốt trước | Trạng thái |
|---|---|---|
| Trash duration, expiry clock, quota/cost theo sensitivity/tenant | Lifecycle adapter dùng dữ liệu thật | TBD; chưa chốt 7/30/90 ngày |
| Ai được delete/restore/purge; step-up, dual approval, hold override | Policy fixtures/schema lifecycle | TBD; default deny, không cấp role mới trong lượt này |
| Material/version/submission UX, batch scope, independently deleted children | Lifecycle implementation | Invariants có; UI/schema chưa chọn |
| Purge reservation/lease/CAS, reachability và keys | Storage integration | TBD; chưa storage vendor/backup policy |
| Backup retention, journal durability/replay, RPO/RTO | Data onboarding/operations | TBD; chưa cam kết khôi phục sau sự cố |

Đo tương lai: unauthorized restore/purge/resurrection và false deny; cleanup propagation latency; successful eligible restore attempts / eligible attempts, báo riêng expired/hold/unavailable/pending; restore-to-review latency khác republish latency; backup drill completeness và RPO/RTO chỉ khi chạy thật. Đây là proposed diagnostics, không KPI đã freeze hoặc kết quả PASS. Không dùng recoverability tốt bù data leak.

Không mở rộng first slice manual QA sang upload/delete. Trước mắt review contract/test schedules; chỉ triển khai lane này trong một scope/GO riêng sau đó.
