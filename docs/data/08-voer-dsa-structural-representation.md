# Biểu diễn cấu trúc CTDL: kiểm chứng nguồn trước khi chunking

Ngày thực hiện: 2026-09-04. Snapshot: `voer-2026-09-04-r1`. Artifact: `voer-dsa-structure-v0.1`.

## 1. Kết luận vòng này

Đã chạy parser nghiên cứu cục bộ trên **toàn bộ 16 module HTML CTDL**, lưu cây thẻ nguồn, vị trí ký tự, quan hệ section, bảng và tham chiếu ảnh. **Đạt kiểm tra bảo toàn/truy vết nguồn; chưa đạt kiểm chứng ngữ nghĩa để chunk/index toàn bộ corpus.**

Đây là bước tiếp nối [evidence pipeline contract](../architecture/05-evidence-pipeline-contract.md), không phải parser PDF hay runtime sản phẩm. Không gọi model, embedding, OCR/VLM, không crawl thêm, không tạo chunk/index.

Artifacts: [README dữ liệu](../../data/processed/voer-dsa-structure-v0.1/README.md), [manifest](../../data/processed/voer-dsa-structure-v0.1/manifest.json), [validation](../../data/processed/voer-dsa-structure-v0.1/validation.json), [review issues](../../data/processed/voer-dsa-structure-v0.1/review-issues.json). Helper nằm riêng trong [AI core experiments](../../ai-core/experiments/html-structure/README.md).

## 2. Từng bước và kết quả

| Bước đã chạy | Kết quả quan sát | Giới hạn |
|---|---|---|
| Đọc snapshot và định danh | 16 module; lưu hash file, hash HTML, version, title, author | Không xác nhận tài liệu đúng học thuật hoặc còn thời sự |
| Parse cây thẻ nguồn | 3.554 nodes, 7.379 text runs, 2.734 structural elements; toàn bộ HTML được phủ bởi chuỗi token liên tục | Thứ tự nguồn, chưa kiểm tra thứ tự hiển thị |
| Giữ cấu trúc nội dung | 120 heading, 120 section, 2.166 đoạn p, 69 list / 113 list item | Heading/section là dấu hiệu có trong HTML, chưa review logic chương mục |
| Giữ bảng | 9 bảng, 47 hàng, 188 ô, gồm 11 ô trống | Không có th; chưa suy luận header hay mở rộng grid |
| Giữ tham chiếu ảnh | 69 tham chiếu / 69 file local; lưu hash và chữ ký định dạng | Chưa hiểu nội dung hình, chưa OCR, không có figcaption |
| Giữ ký hiệu inline | 170 sub và 77 sup | Giữ vai trò thẻ, chưa hiểu công thức |
| Nối evidence cũ | 22/22 locator khớp quote và truy về HTML + element | Chỉ silver alignment, không phải chấm câu trả lời |
| Kiểm tra lỗi có chủ đích | 10/10 synthetic probes; phát hiện 8/8 mutations | Tập thử hữu hạn, chưa kiểm thử bảo mật/runtime |

Không có cảnh báo đóng thẻ suy đoán hoặc đóng thẻ không khớp trên 16 module theo bộ kiểm tra hiện tại. Điều này **không** chứng minh HTML hợp chuẩn hay mọi cấu trúc đều đúng.

## 3. Representation giữ gì, không giữ gì?

Mỗi file lưu các lớp riêng:

- `source`: file/version/hash, JSON pointer `/data/text`, tiêu đề và tác giả từ nguồn.
- `nodes`, `source_tokens`, `text_runs`: cây thẻ, thuộc tính đã parse, quan hệ cha-con và vị trí về HTML gốc.
- `sections`, `elements`: section theo container trong nguồn, loại phần tử, thứ tự và cờ cần review.
- `tables`: danh sách hàng/ô, nội dung đã decode, ô trống, thuộc tính rowspan/colspan nguyên trạng; chưa dựng ma trận chuẩn hóa.
- `images`: đường dẫn nguồn/local, checksum, alt nguyên trạng, liên kết đoạn lân cận ở trạng thái candidate.
- `legacy_reference_projection`: chỉ tương thích với offset nhãn cũ; không dùng làm văn bản chuẩn cho chunker/generator.

Tất cả raw span dùng **Unicode codepoint [start, end) trong chuỗi HTML sau khi decode JSON**. Không phải byte offset, JavaScript UTF-16, vị trí PDF hay offset trên text đã bỏ thẻ. Khi mở citation phải kiểm tra đúng source hash/version và đúng hệ tọa độ.

Đây là **source tag tree**, không phải DOM mà trình duyệt đã sửa lỗi hay một layout engine. Python HTMLParser cung cấp callback và vị trí nhưng không tự xác thực sự khớp nhau của các thẻ đóng; helper bổ sung stack và cờ đóng thẻ suy đoán. [Tài liệu Python 3.12](https://docs.python.org/3.12/library/html.parser.html).

`preview` chỉ để duyệt nhanh và có thể bị cắt ngắn; không phải canonical text. Ví dụ `a<sub>i</sub>` vẫn còn thẻ sub trong cây, nhưng bản preview phẳng có thể nhìn thành `ai`. Không dùng riêng preview để trả lời về công thức. Không render trực tiếp HTML chưa sanitize; script/comment là dữ liệu nguồn bất tín, không phải chỉ dẫn thực thi.

## 4. Phát hiện quan trọng cho chunking

### Một evidence có thể đi qua hai đoạn thật

| Locator silver cũ | Span trên legacy text | Envelope trên HTML gốc | Cấu trúc thật |
|---|---|---|---|
| list-data | [28, 158) | [106, 281) | Hai p cùng section |
| problem-ipo | [39, 116) | [116, 220) | Hai p cùng section |
| stack-push | [362, 424) | [492, 554) | Một phần của một p |
| stack-pop | [425, 477) | [555, 607) | Một phần khác của chính p đó |

Ví dụ `list-data` gồm đoạn dẫn giải “chứa 2 thông tin” và đoạn tiếp theo về thành phần dữ liệu. Cắt theo một p có thể tách lời dẫn khỏi ý giải thích. Ngược lại, hai nhãn push/pop không có nghĩa phải tạo hai paragraph/chunk mới.

**Hệ quả thiết kế:** không lấy ranh giới manual evidence làm ranh giới chunk sản phẩm; cũng không mặc định mỗi p là đơn vị ngữ nghĩa độc lập. Chunking cần giữ lineage và có cơ chế mang theo ngữ cảnh cha/lân cận; mức mở rộng phải được đo, không mặc định lấy cả chương.

Builder không đọc reference answers/qrels. Chỉ auditor đọc mapping để kiểm tra khả năng định vị. 22 phép đối chiếu không đưa nhãn vào parser và không được gọi là Recall@k.

### Nguồn vẫn có những vùng chưa hiểu được

| Vùng cần xử lý | Quan sát thật | Quyết định trước khi chunk |
|---|---|---|
| Code/pseudocode | Không có pre/code; 697 p bị heuristic gắn cờ giống code | Review và gom chuỗi code cùng phần khai báo/giải thích; 697 là số candidate, không phải số dòng code chính xác |
| Bảng | 9/9 không có th; bảng Stack có hàng đầu “Ký tự / Thao tác / Stack / Chuỗi hậu tố” nhưng vẫn là td | Có thể tạo header candidate; chưa gắn nhãn header đã xác nhận. Giữ 11 ô trống, không đổi thành 0 |
| Hình | 69/69 alt là tên file; không có figcaption | Phân loại hình minh họa/nội dung bắt buộc/trang trí bằng review; đoạn gần ảnh chưa phải caption |
| Công thức | 247 node sub/sup; 101 element có cờ rich representation | Bảo toàn notation và kiểm tra cách render/serialize; không dùng plain-text preview để thay công thức |
| Ký tự lạ | 4 element chứa ký tự private-use | Review font/ký hiệu nguồn, không đoán và thay tự động |
| Nguồn lỗi hoặc thiếu | Có notation chỉ số mảng đáng ngờ đã tồn tại trong nguồn; module mở đầu không có heading | Giữ nguyên nguồn; ghi issue, không tự sửa nội dung hay tạo heading giả |

697 candidate có thể có false positive và false negative; đoạn không có cờ **không mặc nhiên được duyệt**. Chưa đo precision/recall của nhận diện code.

Có 5 file đuôi .png nhưng chữ ký là JPEG (2 ở Stack, 3 ở Queue), trùng hiện tượng đã ghi ở corpus trước đó. Giữ nguyên tên và bytes; ghi định dạng thực vào metadata. Đây là kiểm tra chữ ký, chưa decode lại hay kiểm chứng thị giác trong vòng này.

## 5. Kiểm kê theo module

Tiêu đề bên dưới giữ nguyên từ metadata, kể cả lỗi gõ và dấu ~. Cột ảnh là số tham chiếu, không phải số hình mang nội dung học thuật.

| Module | Heading | Đoạn p | Bảng / ô | Ảnh |
|---|---:|---:|---:|---:|
| 1. Mục lục - Cấu trúc dữ liệu và giải thuật~ | 0 | 6 | 0 / 0 | 6 |
| 2. Giải thuật và cấu trúc dữ liệu~ | 8 | 58 | 2 / 40 | 1 |
| 3. Phân tích và thiết kế bài toán | 3 | 152 | 0 / 0 | 7 |
| 4. Phân tích thời gian thực hiện thuật toán | 5 | 96 | 0 / 0 | 3 |
| 5. Mảng và dánh sách | 10 | 157 | 1 / 8 | 9 |
| 6. Danh sách nối đơn (Singlely Linked List)~ | 6 | 279 | 0 / 0 | 6 |
| 7. Thực hành cài đặt danh sách nối đơn~ | 6 | 15 | 0 / 0 | 0 |
| 8. Danh sách tuyến tính ngăn xếp (Stack) | 5 | 296 | 1 / 56 | 6 |
| 9. Danh sách tuyến tính kiểu hàng đợi | 12 | 353 | 2 / 30 | 6 |
| 10. Thực hành cái đặt danh sách kiểu hàng đợi | 19 | 24 | 0 / 0 | 5 |
| 11. Danh sách nối vòng và nối kép~ | 19 | 347 | 0 / 0 | 6 |
| 12. Thực hành cài đặt danh sách liên kết kép~ | 1 | 13 | 0 / 0 | 0 |
| 13. Kiểu dữ liệu cây | 9 | 153 | 2 / 51 | 14 |
| 14. Thực hành cài đặt cây nhị phân~ | 6 | 4 | 0 / 0 | 0 |
| 15. Cây nhị phân và ứng dụng~ | 6 | 208 | 1 / 3 | 0 |
| 16. Thực hành cài đặt cây nhị phân tìm kiếm~ | 5 | 5 | 0 / 0 | 0 |

## 6. Kiểm chứng và giới hạn kết luận

- **61.755 kiểm tra nội bộ** về hash, vị trí, lineage, token/text, bảng/ảnh và alignment đều đạt.
- **16/16 rebuild** cho object JSON giống artifact đã lưu, với implementation hash và Python 3.12.14 đã ghi trong profile.
- **22/22 locator** khớp cả quote legacy và HTML envelope; vẫn thuộc mapping assistant/silver, chưa adjudication.
- **10 synthetic probes** về sub/sup, br, entities, nested lists, blank cells, spans, captions, malformed HTML và dữ liệu script bất hoạt.
- **8 mutation tests** phát hiện sai hash, mất text event, đổi sub thành sup, xóa ô trống, tạo header/caption giả, mất alignment và tự nhận đã hiểu hình.

Trong quá trình phát triển, audit phát hiện một số khoảng trắng Unicode đã bị chuẩn hóa nhưng còn gắn ánh xạ 1–1; đã sửa thành envelope và rebuild trước khi chốt kết quả. Không sửa nguồn để làm test đạt.

Rebuild dùng cùng builder nên chủ yếu chứng minh tính lặp lại; các đối chiếu raw spans và mutations bổ sung kiểm tra, nhưng **chưa phải so sánh với parser độc lập hoặc human transcript**. “Passed” không có nghĩa AI đạt 100%, giải quyết xong SIM-03 hay đạt KPI 80%.

Kiểm tra bàn giao: structural verifier đạt **245/245**, kiểm tra cú pháp 8 helper Python và hash 17 PDF, không skip. So sánh checksum trước/sau cho **251 file dữ liệu có sẵn: không file nào thay đổi hoặc bị mất**; chỉ thêm 20 file vào thư mục representation mới. Nhãn silver, contract examples và kết quả các vòng trước giữ nguyên.

## 7. Bước tiếp theo đề xuất

1. **Review/gom cấu trúc khó**, ưu tiên Stack, Queue và mảng: nhóm code, notation, header bảng, liên kết hình với phần giải thích. Lưu decision + nguồn dẫn, không ghi đè representation này.
2. Tạo một version representation bổ sung các nhóm ngữ nghĩa đã kiểm chứng. Với vùng chưa chắc: ghi rõ cần thêm ngữ cảnh, cần visual review hoặc tạm chưa đủ điều kiện thử.
3. Chốt **đơn vị không được tách** và context bắt buộc; sau đó mới chạy baseline chunking có version trên phạm vi đã review. Nếu chỉ thử prose, công bố subset và coverage bị loại trước khi chấm.
4. Đo evidence coverage và context loss trước/sau chunking/packing; chạy lại ba tình huống đủ / khôi phục / không khôi phục. Chỉ sau đó mới thử indexing/retrieval và so sánh cấu hình.

Đây là thứ tự tiếp theo, **chưa được thực thi trong vòng này**. Toàn bộ corpus vẫn local research reference, không training, không publish/serving và không tự cấp quyền xử lý ngoài. 17 PDF vẫn quarantine. Thiếu giảng viên không chặn kiểm tra kỹ thuật, nhưng vẫn chặn nghiệm thu học thuật.
