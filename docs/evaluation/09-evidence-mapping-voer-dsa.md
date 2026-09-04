# Evidence mapping CTDL & Giải thuật v0.1

Ngày: 2026-09-04. Kết quả: **đã có bản mapping truy vết được cho 10 câu answerable**, chưa human review/gold và chưa chạy RAG.

## 1. Đầu ra đã tạo

[Evidence map](../../data/evaluation/silver/voer-dsa-evidence-map-v0.1/evidence-map.json) liên kết:

**10 câu -> 30 required claims -> 25 evidence groups -> 22 source locators -> 10 module**.

Nguồn là snapshot `voer-2026-09-04-r1`, tham chiếu nguyên ID/query/required claims của `VOER-ACA-001` đến `VOER-ACA-010`. Có bốn câu cần hai module. Phạm vi candidate corpus vẫn gồm 16 module CTDL, không được giới hạn retriever vào 10 module đáp án.

Mỗi locator có đoạn trích chính xác, offset đầu/cuối, context trước/sau, JSON pointer, checksum file/HTML/text chuẩn hóa và phiên bản nguồn. Tác giả/tên tài liệu giữ theo metadata nguồn, không tự gán họ thành reviewer nội bộ. [README và hạn chế sử dụng](../../data/evaluation/silver/voer-dsa-evidence-map-v0.1/README.md).

Không sửa raw snapshot, pack silver cũ hoặc profile lựa chọn 14 case. Không tạo lại đáp án và không đưa PDF đang quarantine vào mapping này.

## 2. Coverage của từng câu

Các mã rút gọn trong bảng đều có prefix `VOER-`.

| Case | Nội dung | Ý bắt buộc | Nhóm evidence | Cấu trúc hỗ trợ |
|---|---|---:|---:|---|
| ACA-001 | Stack: quy tắc, Push, Pop | 3 | 3 | Nhóm quy tắc có hai đoạn thay thế hợp lệ trong cùng module |
| ACA-002 | Queue: quy tắc, hai đầu, thao tác | 4 | 3 | Một đoạn nêu cả hai đầu; tên thao tác ở đoạn khác |
| ACA-003 | Cấu tạo node danh sách đơn | 3 | 2 | Nhóm cấu tạo cần cả đoạn dữ liệu lẫn đoạn liên kết |
| ACA-004 | Bậc nút và bậc cây | 2 | 2 | Hai định nghĩa, không gộp với chiều cao |
| ACA-005 | Lựa chọn CTDL và hiệu quả | 3 | 2 | Đoạn tài nguyên/phép toán + đoạn chất lượng triển khai |
| ACA-006 | Queue mảng bị tràn và cách khắc phục | 4 | 3 | Nguyên nhân + di chuyển tịnh tiến + mảng xoay vòng |
| ACA-007 | So sánh stack/queue | 3 | 2 | Hai module; claim so sánh cần đồng thời hai nhóm |
| ACA-008 | So sánh mảng/danh sách đơn | 3 | 3 | Hai module; claim mảng phải giữ phạm vi theo định nghĩa nguồn |
| ACA-009 | Xác định bài toán và đánh giá thuật toán | 3 | 3 | Hai module nhưng ba yêu cầu evidence riêng |
| ACA-010 | Đuôi danh sách thường/vòng | 2 | 2 | Hai module; không áp NULL của danh sách thường sang vòng |

Số nhóm không bằng số claim hay số document. Một đoạn có thể hỗ trợ nhiều claim; một claim tổng hợp có thể cần nhiều nhóm. Không coi các nhóm dùng chung nguồn là mẫu thống kê độc lập.

## 3. Quy tắc AND/OR đã biểu diễn rõ

- OR giữa các phương án thay thế hoàn chỉnh của một nhóm.
- AND giữa các locators trong một phương án.
- AND giữa các required groups của case.
- Claim chỉ đủ evidence khi mọi nhóm trong `all_of_groups` của claim đã được cover.

Ví dụ: quy tắc stack có hai cách dẫn từ hai đoạn đã xem trong cùng nguồn. Chỉ cần một đoạn cho **nhóm quy tắc**, nhưng câu hỏi còn yêu cầu tên hai thao tác nên vẫn cần hai nhóm còn lại. Không bắt retriever lấy cả hai đoạn thay thế.

Trong ACA-007, chỉ có evidence stack thì claim về stack có hỗ trợ, nhưng claim về queue và claim so sánh chưa đủ. Không lấy câu trả lời dựa trên model memory để bù evidence thiếu.

## 4. Locator nghĩa là gì và chưa làm được gì?

Offset dùng `[start,end)` theo Unicode codepoint của `data.text` sau normalization phiên bản `voer-html-regex-space-v1`. Không phải byte offset, XPath, vị trí DOM hay chỉ số UTF-16 của JavaScript.

Đã kiểm tra toàn bộ 22 quote xuất hiện đúng một lần trong normalized text của nguồn tương ứng. Prefix/suffix giúp reviewer đối chiếu; hash ngăn dùng nhầm phiên bản. Section hints do assistant ghi để tìm nhanh, không phải DOM anchors được parser phát hiện.

Representation này bám phép chuẩn hóa silver cũ: thay tag bằng space, decode entity, gom whitespace và trim. **Không dùng nó làm parser/chunker sản phẩm**: cấu trúc heading, code, subscript, bảng và hình có thể bị bẹt. Cần map pipeline sau này về source locators, không thay raw HTML bằng plain text này.

Chưa có frontend viewer/highlight được triển khai. Khi xây viewer, cần kiểm tra version và chuyển hệ tọa độ ký tự đúng; không gắn offset của snapshot lên HTML đang chạy ở website hiện tại.

## 5. Các vấn đề được phát hiện/giữ mở

[Review issues](../../data/evaluation/silver/voer-dsa-evidence-map-v0.1/review-issues.json) có bảy mục, đáng chú ý:

1. Nguồn danh sách đơn có lỗi chữ. Quote phải giữ nguyên để truy vết, nhưng câu trả lời đúng không cần lặp lỗi chính tả. Không dùng exact-string answer matching để chấm hiểu biết.
2. ACA-006 nhắc hình, nhưng các ý bắt buộc của câu hiện tại có text hỗ trợ. Đây không phải bằng chứng đã kiểm tra năng lực đọc hình.
3. ACA-008 cần qualification “theo định nghĩa mảng trong tài liệu”. Không nâng nội dung đó thành kết luận cho mọi dynamic container. Chưa có reviewer chuyên môn duyệt.
4. Ngoài vùng đã map, module mảng có đoạn ký hiệu bất thường ngay trong raw HTML. Không tự sửa bằng suy đoán hoặc quy lỗi cho parser; QA hiện tại chỉ bao phủ các đoạn đã chọn, không toàn bộ module.
5. ACA-012: câu “modul này không đủ thời lượng trình bày” trong phần giới thiệu chưa tự chứng minh toàn bộ 16 module không dạy xử lý va chạm. Giữ abstention control provisional, không đưa span đó vào answerable qrels; cần review phạm vi rộng hơn.
6. Safety controls phải chấm hành vi. Ví dụ việc một câu từ chối nhắc tên loại bí mật không đồng nghĩa tiết lộ bí mật. Role-spoofing cần actor/resource fixtures để đánh giá quyền backend thật.

Ba safety cases và ACA-012 có disposition notes, không có answerable evidence groups trong mapping này. Không tính chúng thành “missing retrieval evidence” hoặc Recall=100%.

## 6. Kiểm tra đã chạy

[Validation record](../../data/evaluation/silver/voer-dsa-evidence-map-v0.1/validation.json) và [verifier read-only](../../ai-core/experiments/evidence-mapping/verify_mapping.py):

- 10 source files kiểm tra hash/version/title/attribution; 22 locators kiểm tra bounds, quote, uniqueness, quote hash và prefix/suffix.
- 30 required claims khớp nguyên bản theo vị trí trong source case; 25 nhóm không có reference thiếu, group mồ côi hoặc phương án AND rỗng.
- 497 assertions về tính nhất quán và coverage logic đạt. Đây không phải 497 tests chất lượng học thuật.
- Chạy 12 tình huống **toy** có chủ đích thêm/bỏ locator IDs; không có retriever/model tham gia. Có thêm kiểm tra empty/all-evidence trên từng case.
- Kiểm tra cấu trúc/link đạt 196/196, bốn file Python qua kiểm tra cú pháp và 17 PDF giữ đúng hash. Đối chiếu SHA-256 trước/sau: toàn bộ 240 file có sẵn trong `data/` giữ nguyên, chỉ thêm bốn file của mapping mới. Những kiểm tra này không đo chất lượng AI.

| Tình huống toy | Nhóm có đủ / cần | Kết quả coverage mong đợi |
|---|---:|---|
| ACA-001 chỉ có quy tắc stack | 1/3 | Chưa đủ |
| ACA-001 dùng đoạn quy tắc thay thế + hai thao tác | 3/3 | Đủ |
| ACA-003 chỉ có đoạn dữ liệu node, thiếu liên kết | 0/2 | Chưa đủ |
| ACA-007 chỉ có phía stack | 1/2 | Chưa đủ, claim tổng hợp không được cover |
| ACA-009 có IPO và tài nguyên nhưng thiếu yêu cầu lời giải | 2/3 | Chưa đủ dù đã chạm đúng cả hai module |

Ví dụ ACA-009 là lý do cần đo **evidence sau context packing**: document recall có thể đạt 2/2 nhưng vẫn bỏ một ý bắt buộc trong cùng module. Matching chunk thực với locator chưa triển khai; set logic chỉ kiểm tra biểu diễn AND/OR, không đo semantic entailment.

## 7. Điều kiện dùng để so sánh chunking về sau

1. Giữ source/hash/normalization ID và mapping version cố định cho một run; mappings này vẫn chỉ là silver/dev.
2. Khi retriever trả chunk, phải xác định source span nào thực sự được giữ; không coi toàn bộ module là có mặt nếu chỉ có tiêu đề hoặc một đoạn nhỏ.
3. Một locator dài có thể được phủ bởi nhiều đoạn liên tiếp trong context. Matching cần xét hợp spans có nguồn đúng; không ép một chunk duy nhất chứa mọi thứ và cũng không cộng độ phủ từ sai version.
4. Chấm trước packing và trên packet cuối cùng; các phương án đã chọn phải được giữ đủ, không padding context bằng đáp án chuẩn.
5. Nếu generator sinh một citation hỗ trợ khác chưa có trong mapping, review nó thay vì mặc định sai. Qrels hiện tại chưa tuyên bố exhaustive; không sửa qrels âm thầm giữa các run so sánh.

## 8. Trạng thái bước P04 và bước tiếp theo

P04 đã xong **bản mapping kỹ thuật cho 10 answerable case** và log vấn đề cho các controls; expert review/negative answerability chưa hoàn tất, không làm N1-N3 đạt.

Bước tiếp theo là tabletop workflow: mô phỏng happy path và các trạng thái mất scope, revoke/cache, packing loss, citation sai version bằng fixtures synthetic. Sau khi đủ gate mới triển khai baseline retrieval; chưa cần chọn model, vector database hoặc chạy multi-agent.
