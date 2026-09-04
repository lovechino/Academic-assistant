# R0 tiếp nối: serializer giữ nguồn đã chạy

Ngày: 2026-09-04. **Đã triển khai/chạy helper nghiên cứu bảo toàn nguồn; chưa chunking, index hoặc gọi model.** Tiếp nối [annotation R0](11-context-review-round0.md), theo [protocol context preservation](10-context-preservation-protocol.md).

## 1. Kết quả để quyết định

Đã kiểm tra việc chuyển 29 nhóm thủ công sang dạng có thể truy ngược về nguồn, không dùng preview bị cắt hoặc legacy text đã làm phẳng sub/sup. Có thể chuyển sang chuẩn bị một thử nghiệm boundary giới hạn; chưa thể kết luận thiết kế chunking đúng hoặc đủ ngữ cảnh để trả lời.

| Phần kiểm tra | Kết quả thật | Giới hạn |
|---|---|---|
| Nhóm / source roots | 29/29 nhóm, 188/188 selected roots serialize được | 4 module, lựa chọn thủ công/dev; không phải 16-module full coverage |
| Nội dung text | 545 text runs, 10.493 decoded codepoints unique giữ và ánh xạ lại | Không có token count hoặc semantic equivalence score |
| Inline | 32 sub và 5 sup giữ đúng kiểu | Không chứng minh công thức đúng toán học |
| Bảng | 3 bảng, 24 hàng, 86 ô, 7 ô blank | Không suy carry-forward, không expand merged-cell grid |
| Ảnh | 2 ảnh công thức thuộc selected members, hash local đúng | Chưa tạo transcription, chưa xác nhận agent hiểu hình |
| Code listing | 101 p của chương trình postfix được giữ riêng | Không coi p là dòng code logic hoặc AST boundary |
| Integrity | 13.062 checks, 5 checks bổ sung, 12 synthetic tests, 14 mutations phát hiện | Không phải 30 context probes hay điểm agents |

Đọc trực tiếp [kết quả từng bước và ví dụ](../../data/processed/voer-dsa-serialization-v0.1/review-examples.md), [trace JSON đủ 29 nhóm](../../data/processed/voer-dsa-serialization-v0.1/group-traces.json), [validation](../../data/processed/voer-dsa-serialization-v0.1/validation.json). [Helper](../../ai-core/experiments/source-serialization/README.md) chỉ xuất stdout, không tự tái ghi snapshot.

## 2. Những điều serializer đã làm thực sự

Mỗi nhóm đi qua năm bước: kiểm tra source/version/hash → chọn từng member → serialize typed events + aligned review view → giữ riêng dependency/overlap → báo trạng thái kỹ thuật và cảnh báo. Source và representation đầu vào được pin; 7 dependency edges không tự mở rộng.

**Nguồn chuẩn và bản xem tách biệt.** Canonical units giữ source nodes, attributes, text/entity events, raw spans và table/image metadata. Bản xem dùng escaped markup để hiển thị vai trò sub/sup/paragraph/row/cell. Dấu thẻ và newline thêm từ cấu trúc là generated markers, không được cite như lời tác giả. Chuỗi `<sub>` thật trong nội dung nếu được mã hóa ở nguồn vẫn là literal, không bị hiểu thành chỉ số dưới.

**Không kéo khoảng chen giữa.** Nhóm khai báo Stack có 6 p không liền nhau; ảnh chen giữa không thuộc member_refs nên không xuất hiện trong body nhóm. Nó vẫn nằm nguyên trong raw/representation/visual review cũ. Tổng 190 refs của enrichment có 188 selected roots và 2 refs chỉ dùng để review ảnh; không tự thêm 2 refs đó vào nội dung nhóm.

**Không ngầm biến nhóm thành chunk.** Có 207 lượt tham chiếu tới 188 roots duy nhất. Listing đầy đủ/hàm con và bảng đầy đủ/hàng con có overlap được khai báo. Nếu index tất cả nhóm như các chunks độc lập sẽ gây trùng; serializer chưa thực hiện quyết định chọn hierarchy hay dedup khi packing.

**Không chữa nguồn.** Pseudocode `T +=T`, `T- = T`, notation/cận chưa chắc và câu dẫn Queue không nhất quán vẫn được giữ. Không compile hay thực thi code bài giảng. Formula false-positive của code heuristic vẫn có source flag nhưng không bị tự đổi loại nội dung.

**Không phát minh dữ liệu hình/bảng.** 7 ô blank giữ nguyên; td vẫn là td. Hai ảnh Mảng có locator và checksum, phần p_n = 1 giữ sub; không thay ảnh bằng filename alt, OCR đoán hoặc LaTeX sinh thêm. Việc đã xem ảnh ở vòng trước vẫn là assistant review, không thành academic gold.

## 3. Alignment và failure policy

Input offsets là Unicode codepoints trong chuỗi HTML đã decode JSON `/data/text`; output offsets là codepoints trong bản xem của từng unit. Không phải UTF-8 bytes, UTF-16 indices, PDF pages hay token offsets.

- `linear`: text không đổi, ánh xạ 1:1 về nguồn.
- `escaped_character`: ký tự như `<` thành `&lt;`, toàn output escape trỏ về một ký tự nguồn.
- `entity_envelope`: entity nguồn có thể giải mã thành một hoặc nhiều codepoints, tất cả trỏ về cả raw entity. Không tự chuyển envelope thành mapping tuyến tính.
- `generated_not_evidence`: marker cấu trúc có raw tag anchor để truy vết, nhưng không phải source text được trích.

Unsupported tag hoặc closure suy đoán làm unit bị block toàn bộ, có reason và projection rỗng. Không rơi về cắt text một phần mà gọi là đầy đủ. MathML/script là hai nhánh synthetic hiện bị block; không suy ra serializer đã hỗ trợ mọi dạng math/HTML. Asset missing/hash mismatch được báo riêng; nguồn có img tag vẫn serialize được, nhưng không đủ để trả lời phần nội dung hình.

Không phải HTML5 layout renderer hoặc HTML sanitizer. Attributes gốc là dữ liệu bất tín, không được phát lại vào projection; script không được thực thi. Việc giữ chỉ dẫn độc hại thành data không phải chứng minh model chống prompt injection — chưa có model trong vòng này.

## 4. Kiểm thử đã thực thi, không cộng nhầm mẫu số

Baseline audit đối chiếu source refs, node structures, partition của source events, output alignment, kiểu markers, exact decoded text, source rows/cells/images, annotation/dependency boundaries và source restrictions. Hai rebuild cho JSON giống nhau và khớp artifact đã lưu. Đây là source-preservation assertions; nhiều checks thuộc cùng một node, không phải mẫu độc lập.

12 synthetic tests gọi code thực trên input riêng: Unicode/emoji/sub/sup; entity nhiều ký tự và literal markup; code/pre/br; comment/attribute/chỉ dẫn bất tín; unsupported script; unsupported math; malformed closure; token bị thiếu; image URL không resolve; partial table row/rowspan/blank/zero; missing local asset/hash mismatch; asset ngoài scope. Missing/hash-mismatch dùng mock filesystem trong bộ nhớ, không sửa asset thật.

14 output mutations: locator drift, text replacement, missing event, truncation, sub→sup, marker giả thành evidence, alignment drift, blank→0, td→th, caption/transcription giả, auto-follow dependency, chèn ảnh ngoài selection, tự nâng academic review, tự cấp serving. Validator bắt đúng error code yêu cầu. Không vì vậy mà khẳng định bắt được mọi loại lỗi.

Additional check không có đường dẫn evaluator trong builder là static regression guard, không phải security sandbox. Builder/auditor cùng assistant, source groups đã dùng cho dev, chưa independent review. Không sửa execution_status của 30 probes / 31 variants cũ; các probes đó chưa đi qua chunker/retriever/generator. Audit annotation R0 cũ và audit serializer này có mục đích/mẫu số khác nhau.

## 5. Còn thiếu trước thử chunking

Đề xuất vòng tới là **R1 boundary-only nhỏ**, chưa vector index:

1. Chọn/pin tokenizer và exact input format; đo cả separators/markers/header nếu có. Chưa chọn embedding/generator hoặc tự đổi ký tự thành token.
2. Freeze scope và eligibility trước run. Không chỉ lấy các nhóm dễ có nhãn tốt; giữ code/formula/table/image và source_uncertain trong báo cáo, phân biệt technical preservation với academic eligibility.
3. So fixed baseline với structure-aware tại cùng hard cap/overlap trước; manual-group variant chỉ là nhánh có annotation hỗ trợ, không gọi là grouping tự động đã thắng. Mọi variant phải nhìn cùng source.
4. In boundary trace: source refs giữ lại, thứ gì bị tách, dependency chưa lấy, actual token count và lý do overflow/block. Nếu không có boundary an toàn thì báo needs_review/oversize, không silent truncate.
5. Đo locator fidelity, mandatory-unit break, forbidden merge, duplication/overhead và eligibility coverage. R1 không có retrieval recall hoặc answer accuracy. Sau đó mới R2 retrieval/packing và R3 generation.

SIM-03 vẫn là yêu cầu về phản hồi khi không khôi phục đủ context. Serializer giúp không làm mất nguồn trước khi chia nhưng **chưa tự tìm dependency còn thiếu, chưa xác định sufficiency và chưa kiểm tra hành vi không hallucinate**. Cần giữ nguyên ba nhánh đủ / cứu được / không cứu được ở các vòng sau.

Không triển khai runtime AI core/Backend/Frontend, không cài package/model, không gọi mạng hay thêm corpus trong vòng này. Tất cả nguồn giữ research restrictions; 17 PDF vẫn quarantine.

## 6. Kiểm tra bàn giao

305/305 scaffold/syntax/link/source checks đạt; 11 file Python được kiểm tra cú pháp, 17 hash PDF đúng, không skip. Rerun audit serializer cho kết quả JSON giống validation đã lưu. Audit context-review cũ vẫn đạt 2.384 checks; audit HTML cũ vẫn đạt 61.755 checks, 16 deterministic rebuilds và 22 locator alignments.

277 file dữ liệu có trước vòng này giữ nguyên checksum; chỉ thêm 5 artifacts trong thư mục serialization v0.1. Kiểm tra riêng trace/member/gap/Unicode counts, bản xem đầy đủ 8 nhóm và local links trong hai Markdown data artifacts đều đạt. Không gộp các số integrity này vào benchmark chất lượng học thuật.
