# Context review R0: nhãn probe và nhóm nội dung nguồn

Ngày: 2026-09-04. **Đã thực hiện annotation/source review; chưa chạy chunking.** Đây là kết quả tiếp nối [protocol](10-context-preservation-protocol.md), không phải bài nghiên cứu hoặc benchmark mới.

## 1. Kết quả bàn giao

| Hạng mục | Đã làm | Chưa được suy ra |
|---|---|---|
| Context probes | 30 probe / 31 biến thể, có source refs, quan sát, expected behavior và điểm còn mở | Chưa có 30 câu trả lời/model tests đạt |
| Nguồn probe | 21 nguồn thật, 6 fixture điều chỉnh điều kiện trên nguồn, 3 synthetic | Fixture thiếu context không chứng minh corpus thật thiếu context |
| Enrichment | 29 nhóm: 14 Stack, 6 Queue, 8 Mảng, 1 nhóm danh sách nối đơn | Không phải 29 chunk; chưa phủ toàn bộ 16 module |
| Dependency | 7 liên kết có loại/lý do/trạng thái, chưa tự động follow | Không phải dependency closure đã đầy đủ |
| Visual review | Xem trực tiếp 4 file ảnh local | Không phải OCR gold hoặc review 69/69 ảnh |
| Integrity audit | 2.384 checks đạt; phát hiện 12/12 lỗi cố ý | Không đo accuracy ngữ nghĩa, retrieval hoặc chống hallucination |

Tất cả annotations vẫn **assistant-silver/dev, human_reviewed=false**. Review cùng assistant không phải xác nhận độc lập. R0 theo protocol còn phần serializer/projection chưa thực hiện; chỉ phần annotation và source review đã được chuẩn bị trong vòng này.

Artifacts để cùng review:

- [Bảng 30 probe, mỗi dòng một quyết định](../../data/evaluation/silver/voer-dsa-context-probes-v0.1/review-matrix.md).
- [Probes JSON đầy đủ](../../data/evaluation/silver/voer-dsa-context-probes-v0.1/probes.json), [validation](../../data/evaluation/silver/voer-dsa-context-probes-v0.1/validation.json).
- [Enrichment nguồn](../../data/processed/voer-dsa-enrichment-v0.1/README.md), [29 nhóm và 7 dependency](../../data/processed/voer-dsa-enrichment-v0.1/enrichment.json).
- [Helper audit chỉ đọc](../../ai-core/experiments/context-review/README.md).

## 2. Những quyết định có căn cứ nguồn

### A. List, định nghĩa và hai ý cùng một đoạn

`list-node-components` giữ câu dẫn node có hai thành phần và hai đoạn mô tả dữ liệu/liên kết. `stack-main-operations` giữ câu dẫn và hai thao tác mặc dù nguồn dùng p, không dùng ul/li. `stack-operation-names` giữ push/pop chung một node nguồn.

CP-04 làm đối chứng: đoạn định nghĩa Stack tự nêu LIFO và đối tượng; không bắt buộc lấy cả chương cho một lookup giới hạn ở ý đó. Không mở rộng vô điều kiện chỉ để được gọi là “giữ context”.

### B. Pseudocode và listing C là hai nhóm khác nhau

Đã đọc và tách candidate:

- PUSH bằng mảng: 14 p; POP: 13 p, cùng phần khai báo được link riêng.
- Chương trình postfix C-like: 101 p từ các include tới cuối main; có candidate hàm `dinhtri` và phần dẫn giới hạn đầu vào.

Các bản gốc có `T +=T`, `T- = T`, biến hoa/thường chưa nhất quán và ký tự lỗi khác. Chỉ ghi ranh giới/issue, **không tự chữa, compile hoặc xác nhận thuật toán đúng**. Listing nhiều hàm chưa có đủ dependency inventory; chưa được gọi là oversized theo token khi chưa có tokenizer.

Một nhóm có member_refs riêng lẻ. Ví dụ declaration của Stack có hình chen giữa nhưng không phải mọi byte trong envelope min/max đều tự động thuộc nhóm. Điều này tránh nhét nội dung không được review vào context dưới tên “cùng đoạn”.

### C. Công thức có thể là text, rich inline hoặc ảnh

CP-08 xác nhận một false-positive cụ thể của code heuristic: node `n-b4334d953bfd1507` có dấu `{` nhưng trình bày công thức địa chỉ. Đây là quan sát trên một mẫu, **không phải precision/recall của bộ nhận diện 697 candidate**.

CP-09 giữ ba p: điều kiện cận → công thức → giải thích số phần tử mỗi hàng. CP-10 yêu cầu bảo toàn sub/sup ở các vùng công thức/đa thức khác nhau, không ghép chúng thành một công thức mới. CP-11 giữ c là số từ máy và L0 là địa chỉ gốc; phạm vi chỉ số trong nguồn chưa chắc nên vẫn có cảnh báo. CP-12 giữ nguyên notation hỏng, không tự đoán dấu bất đẳng thức.

### D. Hai ảnh Mảng chứa những phần công thức phụ thuộc nhau

Đã xem [8663.png](../../data/raw/voer/cau-truc-du-lieu-va-giai-thuat/assets/9461a675/8663.png) và [8667.png](../../data/raw/voer/cau-truc-du-lieu-va-giai-thuat/assets/9461a675/8667.png): ảnh đầu trình bày công thức tổng địa chỉ có hệ số p_i; ảnh sau định nghĩa p_i bằng tích. Đoạn `p_n = 1` ở text phía sau; cận chỉ số ở text phía trước.

Vì vậy `array-multidim-images` gồm **hai ảnh + đoạn p_n**, link tới `array-multidim-lead`. P trống nằm giữa hai ảnh bị loại khỏi vai trò caption, nhưng không bị xóa khỏi nguồn. Không tạo LaTeX/OCR transcript giả. Quan hệ này là assistant visual/source review, tính đúng toán học vẫn chờ chuyên môn.

Hai ảnh còn lại đã xem: [mảng S của Stack](../../data/raw/voer/cau-truc-du-lieu-va-giai-thuat/assets/a208ce0f/16706.png), [danh sách Queue](../../data/raw/voer/cau-truc-du-lieu-va-giai-thuat/assets/387652b5/15023.png). Link được đối chiếu với nhãn/chỉ số nhìn thấy và phần giải thích; filename alt vẫn không phải semantic caption.

### E. Bảng diễn tiến: hàng trước chưa chắc chứa đủ trạng thái

Trong bảng Stack, hàng xử lý `/` mô tả lấy `*` ra rồi push `/`. Hàng ngay trước ghi toán hạng 2 nhưng ô Stack trống; trạng thái `+ *` được ghi ở hàng trước nữa. Do đó candidate context cần ít nhất xét cả hai hàng này, không mặc định neighbor=1 là đủ.

Tuy nhiên **không tự kết luận ô trống nghĩa là carry-forward**. CP-13 giữ blank đúng nguồn; CP-15 ghi dependency ở mức proposed và giữ cảnh báo. Hàng header được review là nhãn cột, nhưng vẫn lưu td trong HTML gốc.

Hai bảng Stack–Deque và Queue–Deque không được merge chỉ vì cùng có từ Deque. Cũng không nối định nghĩa biến N giữa hai document chỉ vì trùng tên.

### F. Các nhánh đủ, cứu được, không cứu được

CP-22/24 định nghĩa fixture với cùng đoạn thành phần dữ liệu: một fixture cung cấp lại câu dẫn, fixture kia không cung cấp. Validator chỉ kiểm tra expected và tập khả dụng nhất quán; **chưa có thuật toán expansion chạy để tự tìm câu dẫn**.

CP-23 gồm `both_present` và `queue_missing`. Hai phía đủ thì bộ evidence phù hợp cho so sánh thứ tự; thiếu Queue thì chưa đủ để so sánh đầy đủ. Câu hỏi so sánh không tự động bị từ chối. Đây là hợp đồng evidence, chưa phải kết quả generation/partial-answer policy.

## 3. Trạng thái review và các phần chưa chốt

29 nhóm gồm 18 `assistant_source_checked`, 1 `assistant_visual_checked`, 4 `proposed`, 6 `source_uncertain`. Các status chỉ phân biệt quan sát nguồn, đề xuất và nghi vấn; academic review đều pending.

30 probe gồm 22 nhãn nháp, 6 có cảnh báo nguồn, CP-06 chờ execution config, CP-20 cần review học thuật/transcription. 22 nhãn nháp cũng chưa có human review, không phải 22 case đạt nghiệm thu.

Điểm còn mở cần đưa vào kế hoạch tiếp:

1. Rich serializer/source alignment để giữ sub/sup, ranh giới code, rows và image references trong output thực sự; chưa dùng preview hoặc legacy projection làm model input.
2. Chọn và pin tokenizer trước khi tuyên bố chunk/token budget, không đánh đồng 8 fixture units với 8 token.
3. Review rộng hơn dependency của listing C; đọc được một hàm không đồng nghĩa có đủ khai báo/hàm được gọi.
4. Xử lý source uncertainty và thiếu transcription ở nhánh học thuật; không dùng chúng để khẳng định answer accuracy.
5. Chưa có classifier/grouping tự động để đo precision/recall; các nhóm hiện tại do assistant chọn bằng tay, có thiên lệch dev.

Những điều này không chặn các thử nghiệm bảo toàn kỹ thuật cục bộ trên mẫu đã công bố, nhưng phải tách khỏi nghiệm thu học thuật hoặc phục vụ người học.

## 4. Audit đã chạy thực sự

Helper kiểm tra hash/version nguồn và representation, 190 refs enrichment/194 refs evaluator (có trùng nhau), member/target tồn tại, group không trộn document, dependency không có vòng lặp, giữ research/evaluator boundaries. Các checks đặc thù kiểm tra blank, td/header, sub/sup, code flag và self-consistency của fixture availability/budget/Unicode.

12 mutations đã bị phát hiện: sai source hash, sai span, member không tồn tại, gộp khác document, dependency mất target, cycle, caption giả, tự cấp serving, tự nhận gold, gọi fixture units là token, đổi synthetic thành nguồn thật và tự nhận đã chạy probe.

Đây là kiểm tra tính nhất quán của annotations và validator, **không kiểm tra trực tiếp mọi phán đoán ngữ nghĩa của assistant**. Các cờ visual review ghi lại việc assistant đã xem ảnh; script không tự “hiểu hình”. Không gọi API model, không thực thi code nguồn hoặc chỉ dẫn trong fixture.

Kiểm tra bàn giao bổ sung: 288/288 scaffold/syntax/link checks đạt, 9 helper Python được kiểm tra cú pháp, 17 hash PDF đúng, không skip. Rerun auditor cho JSON giống validation đã lưu; các link trong ba Markdown data artifacts đều tồn tại. 271 file dữ liệu có trước vòng này giữ nguyên checksum; chỉ thêm 6 file trong hai thư mục enrichment/probes mới.

## 5. Bước tiếp theo

Xây và kiểm tra **serializer giữ nguồn**, sau đó chạy chunking-only giới hạn trên cùng input/config, in trace cho mỗi boundary: phần giữ lại, dependency bị tách, lý do split và disposition nếu quá cap. Giữ các trường hợp nguồn chưa chắc trong báo cáo, không lặng lẽ bỏ chúng để tăng score.

Chưa chọn chunker thắng cuộc, chưa xây vector index, chưa thay source/nhãn/simulation cũ. Metadata enrichment không mang CP IDs/expected answers; evaluator pack không được cấp cho chunker hoặc model. Toàn bộ corpus vẫn local research reference, PDF giữ quarantine.
