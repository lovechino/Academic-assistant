# Parser diagnostic vòng 0: lỗi trước khi chunking

Ngày: 2026-09-04. Trạng thái: **đã chạy khảo sát cục bộ, chưa phải benchmark nghiệm thu**.

## 1. Kết luận để quyết định

Chưa đưa text PDF vào chunker hàng loạt. Trên mẫu đã chọn, có lỗi thứ tự đọc, mất nội dung nằm trong ảnh, sai ký hiệu và đứt quan hệ bảng. Semantic chunking trên chuỗi text đã hỏng không khôi phục đáng tin cậy những thông tin này.

Giữ hướng thiết kế: parse cấu trúc -> kiểm tra evidence -> logical slide/table/figure -> chunk theo ngữ nghĩa -> index. Không có kết quả nào trong vòng này chứng minh một parser/model cụ thể là tốt nhất.

## 2. Đã chạy gì?

- Nguồn: snapshot `vn-pdf-pilot-2026-09-04-v0.1`, 17 PDF / 236 trang, vẫn cách ly vì quyền sử dụng chưa được xác minh.
- Tập khảo sát: 13 trang chọn có chủ đích, không lấy mẫu đại diện thống kê; annotations do assistant kiểm tra, chưa có người duyệt.
- Baseline: `pdfplumber 0.11.9`, `extract_text()`, `extract_words()` và `extract_tables()` mặc định. Không OCR, không model layout/VLM, không embedding/indexing.
- Diagnostic đối chứng: dùng bbox **được cung cấp sẵn** để crop từng vùng rồi trích text. Đây là oracle-region diagnostic, không phải khả năng tự phát hiện layout của parser.
- Đối chiếu trang render với extraction; p33 cung-cầu được xem thêm bằng PDFium để kiểm tra bất đồng text/ảnh. Bản PDF nguồn không bị thay đổi.

Helper tái lập: [audit_layout_order.py](../../ai-core/experiments/pdf-pilot/audit_layout_order.py). Output: [extractions.json](../../data/processed/pdf-pilot/layout-diagnostic-v0.1/extractions.json). Dẫn xuất giữ nguyên hạn chế nguồn, không public/upload sang dịch vụ ngoài.

[Kiểm tra nhất quán](../../data/processed/pdf-pilot/layout-diagnostic-v0.1/validation.json): 106/106 assertions về checksum, tham chiếu, số đo và liên kết cục bộ đạt. Đây là kiểm tra artifact/số liệu, **không phải 106 test chất lượng parser** hay 12 probes đã pass.

## 3. Kết quả đo thứ tự giữa các slide

Gán mỗi từ vào logical slide theo tâm bbox; giữ nguyên thứ tự từ mà `extract_words()` trả về. Một “run” là chuỗi từ liên tiếp thuộc cùng slide. Chỉ so các cặp từ thuộc hai slide khác nhau; không chấm thứ tự bên trong một slide.

`pair_order_accuracy = 1 - số cặp đảo thứ tự / số cặp khác slide`.

| Trang audit | Slide thật | Runs mặc định | Từ được gán / bị loại | Cặp đảo / cặp so sánh | Pair-order accuracy |
|---|---:|---:|---:|---:|---:|
| `dsa-ch1-p001` | 2 | 2 | 183 / 0 | 0 / 8.162 | 100% |
| `dsa-ch2-p005` | 2 | 2 | 160 / 0 | 0 / 6.204 | 100% |
| `db-table-p002` | 4 | 22 | 141 / 1 | 1.242 / 6.978 | 82,20% |

Trang 4-up đọc qua lại hai slide trên cùng hàng; crop theo bốn vùng có sẵn tách được slide 5/6/7/8. Nhưng không vì thế mà đã đọc đúng chữ trong screenshot, quan hệ mũi tên hay thứ tự callout trong slide.

**Không báo 82,20% như độ chính xác PDF/RAG.** Đây chỉ là một chỉ số diagnostic trên một trang và các cặp từ phụ thuộc nhau. Điểm oracle 100% là hệ quả sắp theo annotation, không phải kết quả học máy. Hai trang 2-up đúng thứ tự cũng không chứng minh công thức/text bên trong đúng.

## 4. Những lỗi có bằng chứng

| Hiện tượng | Quan sát thực tế | Tác động tới chunk/index |
|---|---|---|
| Có text nhưng mất vùng kiến thức | `er-p004`: 105 ký tự toàn trang, nhưng text vùng chú giải bằng rỗng; hình và nhãn nằm trong raster | Không dùng `page_text_nonempty` để quyết định bỏ OCR/vision; kiểm tra ở cấp evidence region |
| Nhận khung trang trí là bảng | `micro-p005`, `micro-p032`: mỗi trang có 6 table candidates; bảng số cần dùng là candidate thứ 6, không phải đầu tiên | Cần định vị, lọc và ghép đúng bảng; không dùng `tables[0]` hoặc index mọi candidate |
| Bảng đúng nhưng thiếu ngữ cảnh | Bảng p5 có cột lượng kg; chu kỳ tháng ở heading bên ngoài bảng | Table child phải nối heading/units với locator riêng |
| Ô trống là trạng thái nguồn | Bảng p32 giữ được một dấu hỏi và bốn ô trống trong cột bài tập | Không đổi blank thành 0, không tự điền đáp án rồi coi là evidence |
| Crop không giải quyết bảng nối trang | Dòng đầu p4 là phần tiếp của hàng cuối p3; crop text vẫn trộn từ ở cột cuối vào cột mục tiêu | Nối theo cell/column; giữ hai trang nguồn; không nối bằng chuỗi text toàn hàng |
| Công thức bị bẹt | `micro-p039`: S/D và chỉ số 0 tách khỏi Q/P; quan hệ subscript không còn rõ trong plain text | Cần math structure hoặc visual evidence; không tự sửa bằng mẫu regex chưa kiểm chứng |
| Native text sai glyph | `dsa-ch2-p005`: render thể hiện `1 ≤ i ≤ m`, extraction có hai ký tự `£` tách riêng | Đánh dấu text/visual mismatch; native extraction cũng cần kiểm tra, không chỉ OCR |
| Biểu đồ thành danh sách nhãn | `micro-p033`: text có ticks/nhãn nhưng mất đường, giao điểm, quan hệ không gian | Text query match không chứng minh evidence đủ trả lời; cần ảnh gốc và nhóm evidence đơn vị ở p32 |

Các bảng số p5/p32 được đối chiếu các hàng và cột liên quan, nhưng chưa tính cell accuracy toàn bộ corpus. Sáu candidates không đồng nghĩa sáu bảng kiến thức, cũng không đủ để suy ra precision tổng.

### Bất đồng cần review: text có nhưng render không thấy

Ở p33, extraction có token `P` tại bbox PDF khoảng `[232.43, 61.69, 256.44, 97.69]` trên trang 842 x 595. Vùng đó nằm trong dải header. Cả bản render Poppler và PDFium đã xem đều không cho thấy token này. Crop chart hiện tại không chứa token đó, **nhưng chưa đủ cơ sở kết luận crop làm mất một nhãn đang nhìn thấy**. Nguyên nhân render/occlusion chưa được xác minh.

Ghi vấn đề vào [review-issues.json](../../data/processed/pdf-pilot/layout-diagnostic-v0.1/review-issues.json); giữ annotations v0.1, chưa tự nâng thành gold. Khi text và hình bất đồng, cần lưu cả hai trạng thái và flag review, không mặc định text là chân lý.

## 5. Bộ 12 structural probes cho vòng kế tiếp

Đặc tả máy đọc được: [structural-probes.json](../../data/processed/pdf-pilot/layout-diagnostic-v0.1/structural-probes.json). Đây là **silver dev probes**, chưa phải 12 test đã pass.

| Probe | Điều kiện phải kiểm tra |
|---|---|
| SP01 | Tách đúng bốn logical slides, giữ nhãn in và reading order |
| SP02 | Tách section 2.2/2.3 dù cùng trang vật lý |
| SP03 | Phát hiện vùng legend còn thiếu, không pass chỉ nhờ title/footer |
| SP04 | Chọn đúng table, loại candidate trang trí; đo cả precision và recall |
| SP05 | Giữ đơn vị/thời gian từ heading cùng với bảng |
| SP06 | Phân biệt blank, dấu hỏi, zero và giá trị suy luận |
| SP07 | Nối hàng p3-p4 theo cột, không trộn từ giữa cột |
| SP08 | Không ghép bảng thực hành p4 vào bảng tiếp diễn phía trên |
| SP09 | Giữ dấu và subscript công thức; uncertainty nếu không đọc được |
| SP10 | Không chấp nhận `£` như bản chép đúng của `≤` |
| SP11 | Giữ evidence đường/giao điểm/trục và liên kết đơn vị; flag bất đồng render |
| SP12 | Giữ dấu hỏi vùng thị trường; không tạo thêm đường chưa có trong nguồn |

Tách hai kết quả: `information_preserved` và `failure_detected`. Parser có thể được chấp nhận ở bước routing nếu nhận ra mình thiếu evidence và chuyển review/visual, nhưng không được tính như đã trích xuất đúng nội dung đó.

## 6. Hợp đồng output tối thiểu trước index

Mỗi element cần những trường khái niệm sau; chưa triển khai schema sản phẩm:

- Identity: source snapshot, document ID, file SHA-256, physical page, logical-slide ID/printed label, element ID, parent ID, section path.
- Locator: bbox và hệ tọa độ/rotation, trang render tương ứng; nhiều locator nếu bảng/định nghĩa nối trang.
- Representation: native text, OCR text, structured table/math, original visual; generated description đặt namespace riêng và không được làm citation evidence.
- Relations: reading order, table-cell/header, caption-of, continuation-of, unit-context, previous/next; cạnh suy đoán phải có review state.
- Quality: observed/derived/unknown/placeholder, extraction method/version, confidence nếu có, issue flags; confidence model không đồng nghĩa xác suất đúng đã hiệu chỉnh.
- Governance: rights/review/ACL/version trạng thái hiện tại; nguồn chưa được phép vẫn cách ly, kể cả khi parser đúng.

Chunk không được cắt ngang đơn vị nguyên tử đã xác định: một công thức cùng biến, một figure cùng nhãn/trục, một row group cùng header. Nếu vượt budget thì dùng parent expansion/locator có kiểm soát, không tăng overlap vô hạn.

Index về sau chỉ nhận elements đủ điều kiện theo modality: text mất ký hiệu phải bị flag; region chưa OCR nhưng còn ảnh không được im lặng biến thành text-only complete. Không dedup mất quan hệ giữa ảnh, chữ và parent. Context packing phải được chấm lại vì có thể làm rơi đơn vị dù retrieval đã tìm đúng trang.

## 7. Vòng làm việc tiếp theo và điểm dừng

1. Review 12 probes và vùng evidence, sửa bbox/reading order nếu cần, lưu version mới và reviewer. Phần layout có thể do người không phải giáo viên review; đúng kiến thức/chính sách sư phạm vẫn cần người có chuyên môn phù hợp.
2. Bổ sung scan với quyền rõ theo [source review](../data/07-ocr-scan-source-review.md). Chưa có sample scan mới được tải trong vòng này; không gọi corpus hiện tại là scan benchmark.
3. Khi quyền sử dụng cho phép: chạy parser layout-aware đầu tiên trên đúng tập này, ghi model/revision/OCR config và chi phí. So với baseline và oracle-region; không chọn winner chỉ bằng bản Markdown trông đẹp.
4. Chỉ bắt đầu thí nghiệm chunk/index trên phần nguồn được phép và đã qua QA. Giữ 12 probes là dev; cần source family mới cho test kín.

Chưa chạy benchmark parser cạnh tranh, CER/WER, Recall@k, RAGAS hay accuracy agents. Không cần cài model hoặc viết ứng dụng để sử dụng kết quả vòng 0 này.
