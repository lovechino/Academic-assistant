# Rà soát nguồn scan/OCR tiếng Việt

Ngày kiểm tra: 2026-09-04. **Chỉ rà metadata và điều kiện truy cập; chưa tải thêm dataset/scan trong vòng này.**

## 1. Đừng trộn ba loại thước đo

1. OCR recognition: đọc chữ, dấu, số, ký hiệu từ ảnh; cần transcription đã review để tính CER/WER.
2. Document structure: vùng bảng/hình/caption, reading order, cell/row continuation; cần annotations hình học và quan hệ.
3. Academic QA/retrieval: tìm đủ evidence và trả lời đúng trong môn học; cần qrels/đáp án theo chính corpus bài giảng.

Dataset chữ viết tay một dòng không đo khả năng nối bảng PDF; sách cổ không đại diện bài giảng hiện đại; annotation bbox không tự cung cấp đáp án QA.

## 2. Shortlist có kiểm tra nguồn gốc

### A. UIT-DODV / UIT-DODV-Ext: ưu tiên cho layout

Trang nhóm nghiên cứu mô tả DODV gồm 2.394 ảnh: 1.696 chuyển từ PDF, 247 scanner, 451 smartphone; bốn lớp Table/Figure/Caption/Formula. Bản Ext có 5.000 ảnh, ba lớp Table/Figure/Caption, gồm sách và bài báo với layout khác nhau. Phù hợp khảo sát detector hơn là gold QA. [Nguồn: UIT Together](https://uit-together.github.io/datasets/).

Hai liên kết dataset từ trang chính trả 404 tại thời điểm kiểm tra: [DODV](https://github.com/nguyenvd-uit/uit-together-dataset/blob/main/UIT-DODV.md), [DODV-Ext](https://github.com/nguyenvd-uit/uit-together-dataset/blob/main/UIT-DODV-Ext.md). Chưa xác nhận file, phiên bản annotation hoặc giấy phép dataset; không lấy giấy phép bài báo thay cho dữ liệu.

Trạng thái: `candidate_access_and_license_unverified`. Bước mở khóa: tìm đường phát hành chính thức còn hoạt động hoặc người dùng liên hệ tác giả; chưa gửi liên hệ thay người dùng. Sau khi tiếp cận hợp lệ, kiểm tra split, duplicate/source family và chất lượng annotation trước khi đưa vào eval.

### B. VieBookRead: ứng viên OCR sách, không mặc nhiên gold

Dataset card gắn với bài AAAI 2025 về hậu xử lý OCR tiếng Việt; nội dung sách xuất bản khoảng 1850-2003, dung lượng niêm yết 26,7 GB. Card gọi `final.zip` là **pseudo groundtruth**, không phải mọi trang đều được người chép và duyệt. [Nguồn: VieBookRead](https://huggingface.co/datasets/thaodd11/VieBookRead).

Trang yêu cầu đăng nhập, chấp nhận điều kiện và chia sẻ thông tin liên hệ. Metadata đầu trang ghi AFL-3.0 nhưng nội dung card ghi CC BY-NC 4.0 và hạn chế thương mại hóa. Chưa làm rõ sự không nhất quán này; không tự chấp nhận điều kiện hoặc tải qua đường khác.

Trạng thái: `gated_terms_and_license_clarification_needed`. Nếu sau này dùng, chỉ lấy mẫu nhỏ sau khi quyền rõ; tự review transcription để đo lỗi, phân slice thời kỳ/ngôn ngữ. Không dùng toàn bộ pseudo labels làm gold rồi công bố accuracy OCR.

### C. Viet-Handwriting-OCR-v2: slice chữ viết tay phụ trợ

Card mô tả 60.247 ảnh dòng/câu viết tay: 59.247 train, 1.000 test; nhãn thủ công theo công bố nhà cung cấp, ảnh gốc lấy từ Internet. Terms ghi CC BY-NC 4.0. Đây không phải ảnh nguyên trang của giáo trình. [Nguồn: 5CD-AI](https://huggingface.co/datasets/5CD-AI/Viet-Handwriting-OCR-v2/blob/main/README.md).

API metadata chính thức trả `gated: auto`, revision `eb9e4dd97511fd73f17a62bbc0605508369dace7`; card đọc công khai không có nghĩa các data files đã được cấp quyền. Chưa tải parquet, chưa dùng tài khoản/chấp nhận điều kiện. [API nguồn](https://huggingface.co/api/datasets/5CD-AI/Viet-Handwriting-OCR-v2).

Trạng thái: `gated_secondary_ocr_candidate`. Tuyên bố ẩn danh từ nhà cung cấp cần được kiểm tra độc lập; không mặc định không có thông tin cá nhân. Nếu dùng thì chấm CER/WER cho handwriting riêng, không nhập điểm này vào QA bài giảng.

### D. Đại Nam quấc âm tự vị, tập I: scan lịch sử phụ trợ

Bản ghi Wikisource/Commons nêu sách năm 1895, 621 trang, khoảng 32,4 MB; hiển thị Public Domain Mark 1.0. Đây là tuyên bố quyền tại bản ghi, không phải chứng nhận mọi mục đích/jurisdiction. Từ điển lịch sử khác xa môn pilot; chỉ cân nhắc stress test scan và chữ cũ. [Bản ghi tập tin](https://vi.wikisource.org/wiki/Tập_tin:Đại_Nam_quấc_âm_tự_vị_1.pdf).

Một lần gọi metadata Commons API bị 403 với thông báo yêu cầu tôn trọng robot policy. Đã dừng việc tải tự động, không thử né bằng CDN/proxy. Chưa có file PDF mới trong workspace. Bản chép cộng đồng cần kiểm tra trạng thái hiệu đính và revision từng trang, không mặc định gold. [Mục lục/hiệu đính](https://vi.wikisource.org/wiki/Mục_lục:Đại_Nam_quấc_âm_tự_vị_1.pdf).

Trạng thái: `public_domain_mark_reported_access_blocked`. Nếu người dùng cung cấp bản tải hợp lệ về sau, kiểm tra checksum/nguồn và chọn vài trang chữ in; không thay bộ bài giảng bằng 621 trang từ điển.

## 3. Quyết định thu thập

- **Chưa có nguồn mới nào được nhập corpus.** Không giả định vượt qua login/điều kiện truy cập chỉ vì metadata công khai.
- Ưu tiên UIT-DODV/Ext cho layout nếu tìm được bản phát hành và quyền rõ. VieBookRead cho scan sách; handwriting và từ điển cổ là slice phụ, không làm chậm pilot chính.
- Tận dụng nguồn đã có quyền phù hợp như VOER cho thử nghiệm text/retrieval; PDF trường học hiện vẫn cách ly. Không áp giấy phép VOER sang PDF trường.
- Synthetic scan/degradation chỉ tạo từ nguồn được phép, gắn nhãn `synthetic`, cùng split/source group với bản gốc. Không dùng nó để tuyên bố đã đánh giá scan thực.

## 4. Checklist trước khi nhập một nguồn

Ghi URL nguồn, thời điểm, file/revision/checksum, giấy phép và ngoại lệ, quyền audit/eval/publication, robots/terms, hình thức nhãn, đơn vị trang/dòng, split và nguồn gốc tài liệu. Kiểm tra PII, bản quyền bên thứ ba, near-duplicates, nhãn lỗi và mức lệch miền. Gating, quyền nghiên cứu, quyền chia sẻ lại và quyền gửi dữ liệu lên dịch vụ model là bốn câu hỏi riêng.

Khi chọn mẫu OCR: lưu transcript gốc được review và quy tắc Unicode NFC/whitespace công bố trước. Báo CER theo ký tự có dấu, WER theo quy tắc token cố định, lỗi số/dấu toán/đơn vị riêng. Không bỏ dấu tiếng Việt để làm đẹp điểm. So OCR-only với post-OCR riêng; hậu xử lý bằng LLM có thể tạo từ đúng nghĩa nhưng không có trên ảnh.

Kết quả nghiên cứu nguồn này bổ sung cho [parser diagnostic vòng 0](../evaluation/07-parser-diagnostic-round0.md), không thay việc kiểm chứng trên PDF bài giảng thật.
