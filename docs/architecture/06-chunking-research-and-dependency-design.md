# Chunking giáo trình: giữ cấu trúc và quan hệ ngữ cảnh

Ngày nghiên cứu: 2026-09-04. Trạng thái: **đề xuất v0.2, chưa triển khai chunker/index, chưa đo hiệu quả**. Tiếp nối [representation CTDL thật](../data/08-voer-dsa-structural-representation.md) và [thiết kế chunking v0.1](01-context-preserving-chunking.md).

Cập nhật tiếp nối: đã [gắn nhãn/source review R0](../evaluation/11-context-review-round0.md) cho 30 probe / 31 biến thể, tạo 29 nhóm nội dung và xem 4 ảnh. Đây là enrichment thủ công/silver, chưa chứng minh grouping tự động hoặc chunking hoạt động.

## 1. Kết luận để quyết định

Không nên tìm một thuật toán “semantic chunking chuẩn cho mọi giáo trình”. Với corpus hiện tại, cần tách bốn việc: **bảo toàn nguồn → phục hồi nhóm nội dung → tạo đơn vị tìm kiếm → đóng gói đủ ngữ cảnh để trả lời**.

Candidate ưu tiên là structure-aware child chunks + các liên kết phụ thuộc được kiểm chứng. Đây là thiết kế riêng của dự án, không phải tên một thuật toán đã được chứng minh. “SHCC” trong v0.1 cũng là tên quy ước nội bộ, không phải bằng chứng benchmark.

Điểm bổ sung so với kế hoạch cũ:

- Một thẻ p, một hàm hoặc một hàng bảng chưa chắc là đơn vị đủ nghĩa.
- Không chỉ giữ parent/neighbor; phải ghi **phụ thuộc vào phần nào, vì sao, đã xác minh chưa**.
- Mở rộng về parent không mặc định là lấy cả section. Cần so với cách lấy đúng các phần phụ thuộc trong cùng ngân sách.
- Đo cả bỏ sót ngữ cảnh, ghép nhầm ngữ cảnh và từ chối quá mức. Giữ hết tài liệu hoặc từ chối hết không được tính là giải pháp tốt.

## 2. Nghiên cứu nói gì — và không nói gì?

Chỉ dùng bài báo gốc và tài liệu chính thức; các kết quả dưới đây thuộc thiết lập của tác giả, không phải điểm của bộ CTDL Việt Nam.

| Nguồn | Điều rút ra | Cách áp dụng / giới hạn |
|---|---|---|
| [Is Semantic Chunking Worth the Computational Cost? — 2024](https://arxiv.org/html/2410.13070v1) | Lợi ích semantic splitting không nhất quán; một số lợi ích xuất hiện ở tài liệu được ghép nhân tạo có chủ đề rất khác nhau | Giữ fixed/sentence baseline. Không suy ra semantic luôn vô ích; nguồn benchmark không tái hiện đầy đủ giáo trình của ta |
| [Beyond Chunk-Then-Embed — preprint 02/2026](https://arxiv.org/html/2602.16974v1) | Thứ hạng phương pháp thay đổi giữa tìm trong một tài liệu và tìm trong corpus; contextualized embedding cũng không thắng cả hai | Đo tìm trong toàn bộ môn riêng với tìm trong một tài liệu đã biết. “Structure-based” ở bài gồm cả fixed/sentence/paragraph, không chứng minh document graph đề xuất ở đây tốt hơn |
| [cAST — Findings EMNLP 2025](https://aclanthology.org/2025.findings-emnlp.430/) | Chia/ghép theo syntax tree cho kết quả tốt trên các tác vụ code được thử | Candidate cho vùng code parse được; không áp dụng thẳng cho pseudocode lẫn văn xuôi |
| [Controlled code-completion study — preprint 05/2026](https://arxiv.org/html/2605.04763v1) | Qua 864 cấu hình, function chunking kém các phương án còn lại trong thiết lập thử; sliding window và cAST có đánh đổi chi phí/chất lượng tốt | Không coi “nguyên hàm” là winner. Đây là code completion chủ yếu trên Python, không phải giải thích thuật toán tiếng Việt; không mâu thuẫn đơn giản với cAST vì khác thiết lập |
| [Late Chunking — bản sửa 07/2025](https://arxiv.org/abs/2409.04701) | Encode token với context dài trước, pool theo boundary sau | Có thể giúp vector biết ngữ cảnh; không khôi phục nội dung đã mất trước embedding và không tự thêm bằng chứng vào prompt |
| [Contextual Retrieval — Anthropic, 09/2024](https://www.anthropic.com/engineering/contextual-retrieval) | Thêm lời dẫn riêng cho chunk trước embedding/BM25 | Là nhánh thí nghiệm khác với chọn boundary. Mức giảm lỗi retrieval do tác giả báo cáo không phải mức tăng answer accuracy của ta; nội dung sinh thêm không được thay nguồn |
| [Lost in the Middle — TACL 2024](https://aclanthology.org/2024.tacl-1.9/) | Vị trí evidence trong context dài ảnh hưởng kết quả trên các model/tác vụ được thử | Có lý do kiểm tra nhiễu/vị trí khi mở parent. Không suy ra mọi model hiện nay đều có cùng mức suy giảm |

### Hai chi tiết thư viện cần kiểm tra, không chỉ đọc tên tính năng

Docling HybridChunker kết hợp hierarchy với tokenizer, có bước split/merge và lặp table header. Nhưng tùy chọn `omit_header_on_overflow` cho phép bỏ header ở hàng không vừa budget; LineBasedTokenChunker vẫn có thể tách dòng quá dài. **Suy luận cho dự án:** tên “hybrid” hay “line-based” chưa đảm bảo các hard gate của ta. Phải giữ header bắt buộc, kiểm tra serialization sau cùng và ghi overflow rõ ràng. Nó cũng không tự xác nhận header khi nguồn CTDL chỉ có td. [Docling chunking](https://docling-project.github.io/docling/concepts/chunking/).

Unstructured `by_title` có thêm tùy chọn gộp section nhỏ; tài liệu hướng dẫn đặt `combine_text_under_n_chars=0` để tắt. `Table` quá lớn có thể bị text-splitting; giữ `orig_elements` để không mất provenance. **Suy luận cho dự án:** phải cấu hình và test, không xem by_title là cam kết tuyệt đối không gộp nhầm section hoặc giữ trọn hàng bảng. Tham số character của thư viện cũng không tương đương token budget. [Unstructured chunking](https://docs.unstructured.io/open-source/core-functionality/chunking).

## 3. Đối chiếu với nguồn thật: lỗi khó nằm trước boundary

Các quan sát sau được đọc lại từ HTML local, không chạy model hoặc sửa representation v0.1. Node IDs và raw spans có thể kiểm chứng trong các file đã lưu.

| Ví dụ nguồn | Rủi ro nếu chia máy móc | Điều cần giữ |
|---|---|---|
| Stack: `Data S [N];`, `int t;`, phần dẫn và `Void PUSH ( S, T, X )` ở nhiều p | Lấy thân thao tác nhưng mất kiểu dữ liệu, biến quản lý đỉnh hoặc điều kiện tràn | Nhóm thuật toán + khai báo/giải thích được liên kết, không chỉ dấu ngoặc |
| Mảng: node `n-b4334d953bfd1507`, HTML [4060,4176), chứa công thức địa chỉ và dấu `{` | Heuristic code hiện tại gắn cờ cho một đoạn thực ra trình bày công thức: một false-positive quan sát được | Phân loại candidate phải được review; số 697 không phải tổng code đã nhận diện đúng |
| Mảng: [4420,4879), ba p liên tiếp | Công thức bị tách khỏi cận chỉ số và giải thích số phần tử mỗi hàng | Nhóm formula + điều kiện + giải thích; vẫn cần review tính đúng của nguồn |
| Stack: bảng `n-261e330b0dbfad08`, 14 hàng | Một hàng có thể mô tả trạng thái sau thao tác, cần trạng thái trước; chỉ lặp tên cột chưa đủ | Câu hỏi “giá trị là gì” và “vì sao thay đổi” cần context khác nhau |
| Queue: heading cài đặt bằng danh sách, sau đó có câu dẫn dùng từ array-queue | Header và câu dẫn trong chính nguồn có dấu hiệu không nhất quán | Gắn `source_uncertain`, không tự đổi thành mô tả có vẻ hợp lý |
| `list-data` / `problem-ipo` đi qua hai p; push/pop chung một p | Boundary nhãn, boundary HTML và boundary nghĩa không trùng nhau | Duy trì nhiều locator cho một yêu cầu evidence |

Nguồn ví dụ: [Stack](../../data/processed/voer-dsa-structure-v0.1/documents/a208ce0f.json), [Queue](../../data/processed/voer-dsa-structure-v0.1/documents/387652b5.json), [Mảng](../../data/processed/voer-dsa-structure-v0.1/documents/9461a675.json). Không xác nhận code trong giáo trình có thể biên dịch hoặc đúng thuật toán.

## 4. Thiết kế đề xuất: nhóm có phụ thuộc, không gom hết vào một chunk

### Lớp A — Nguồn bất biến

Giữ HTML/text runs, sub/sup, cells, ảnh, hash/version và locator. PDF về sau giữ page/region/bbox riêng; không chuyển HTML offset thành page giả. Không dùng preview bị cắt hoặc legacy regex projection làm văn bản chuẩn của chunker.

### Lớp B — Nhóm nội dung và quan hệ

Tạo một enrichment sidecar mới, không ghi đè cây nguồn. Một nhóm có thể gồm nhiều element, thậm chí không liền nhau; **không lấy min/max offset rồi xem cả phần xen giữa là cùng evidence**.

Thông tin cần có: group ID, loại nội dung, member element IDs/spans, dependency targets, lý do/rule version, trạng thái review, người/công cụ đề xuất. Các quan hệ dự kiến:

- `requires_definition`: thuật toán/công thức cần phần định nghĩa biến hoặc điều kiện.
- `requires_lead_in`: item cần câu dẫn.
- `requires_header`: hàng bảng cần header/đơn vị đã xác minh.
- `continues_from`: chuỗi thuật toán, lập luận hoặc trạng thái tiếp nối.
- `explained_by`: hình/công thức có đoạn giải thích đã đối chiếu.
- `candidate_neighbor`: gần nhau trong nguồn nhưng **chưa đủ để coi là quan hệ ngữ nghĩa**.

Đây là metadata quan hệ nội dung, chưa cần graph database hay GraphRAG. Quan hệ có hướng, cho phép unresolved; cần phát hiện vòng lặp và chặn mở rộng vô hạn. Scope/version/access luôn được kiểm tra trước khi đi theo cạnh. Quan hệ suy ra từ qrels chỉ ở evaluator, không được lén đưa vào builder.

### Lớp C — Đơn vị retrieval

Tạo child theo nhóm/ranh giới đã review và cap của embedding model. `body` chứa source fragments; `retrieval_header` tách riêng course/document/section/type. Nội dung sinh bởi model, nếu thử về sau, ở field khác và không được cite như nguyên văn.

Nhóm quá lớn không thể luôn giữ nguyên trong một embedding. Khi đó:

1. Chia ở ranh giới logic đã xác minh; gắn fragment index, group ID và phần phụ thuộc cần lấy lại.
2. Nếu chưa có ranh giới an toàn: giữ object đầy đủ trong source store, tạo trạng thái overflow/needs_review; không âm thầm truncate.
3. Tiêu đề/summary chỉ giúp tìm đến object, không chứng minh object đủ để trả lời.

Không trộn body từ hai module/access scope. Query so sánh Stack–Queue lấy hai nhóm riêng vào packet sau bước kiểm tra quyền, không cần tạo một chunk ghép trước từ đáp án.

### Lớp D — Context packet theo câu hỏi

Sau retrieval, mở rộng theo các phụ thuộc phù hợp với phần đang được hỏi; dedup theo source position và đóng packet trong budget. So sánh ba cách trên cùng tập child: không mở rộng, mở parent có cap, mở phụ thuộc có cap.

Không đưa evaluator “required evidence” vào runtime để chỉ đường. Runtime có thể dùng query intent, metadata và quan hệ nội dung; độ đầy đủ thực tế phải được chấm bằng sidecar độc lập.

Các trường hợp không đủ cần tách rõ: chưa retrieve được; nguồn có nhưng vượt budget; visual chưa đọc được; nguồn mâu thuẫn; thật sự thiếu bằng chứng. Câu hỏi so sánh **không tự động dẫn đến từ chối**: nếu tìm đủ cả hai phía, trả lời có citation; nếu chỉ một phía đủ, theo policy partial/abstention đã chốt, không tự điền phần còn lại.

## 5. Quy tắc riêng cho giáo trình hỗn hợp

**Code:** gom p theo tín hiệu khai báo, tên thao tác, indentation/dấu câu và phần giải thích, nhưng không lấy regex làm nhãn chắc chắn. Chỉ thử syntax-tree chunking khi xác định được ngôn ngữ và mức parse đáng tin; pseudocode giữ nguyên. Tree-sitter có ERROR/MISSING nodes nên “trả về tree” không đồng nghĩa code hợp lệ. Không thêm dấu ngoặc/kiểu dữ liệu cho parse thành công rồi coi đó là nguồn. [Tree-sitter syntax queries](https://tree-sitter.github.io/tree-sitter/using-parsers/queries/1-syntax.html).

**Công thức:** giữ hình thức sub/sup và quan hệ với biến, đơn vị, cận, giả định. Phân biệt “bảo toàn ký hiệu” với “công thức đúng”. Không suy ra điều kiện thiếu từ kiến thức model; ghi issue để reviewer xử lý.

**Bảng:** phân biệt bảng dữ liệu độc lập, bảng so sánh và bảng mô phỏng từng bước. Khi split, cần lặp header đã xác minh; trường hợp diễn tiến còn có dependency trước/sau. Hàng và ô trống là đối tượng nguồn, không thay trống bằng 0 hoặc tự điền trạng thái.

**Hình:** giữ asset + đoạn liên quan ở trạng thái được xác minh hoặc unresolved. Có thể thử visual retrieval song song: ColPali cho thấy hướng truy hồi từ biểu diễn hình trang và giới thiệu benchmark ViDoRe. Nhưng tìm đúng trang không chứng minh hiểu sơ đồ hoặc chọn đúng crop; đây là nhánh riêng, không thay kiểm chứng text–figure. [ColPali](https://arxiv.org/abs/2407.01449).

**Tiếng Việt trộn code/Anh:** không coi dấu chấm trong ký hiệu, số mục, viết tắt và số thập phân là boundary câu mặc định. Đo bằng tokenizer đã pin, không đổi 512 ký tự thành 512 token. Chuẩn hóa Unicode để search nếu cần phải có mapping; giữ code identifiers, dấu so sánh, chỉ số và nguyên văn citation.

## 6. Thứ tự thử và điểm dừng

1. Tạo bộ review khó **30 probe dự kiến**, có cả ví dụ cần nối và ví dụ tuyệt đối không nối; chưa tạo nhãn hay chạy 30 probe trong vòng nghiên cứu này.
2. Review enrichment cho Stack/Queue/Mảng, có negative controls để đo false merge và false split; không chỉ tối ưu 22 locator đã biết.
3. Chạy chunking-only trên cùng representation/eligibility; so baseline và candidate, giữ tất cả lỗi/oversize trong báo cáo.
4. Sau khi cấu trúc đủ điều kiện mới retrieval-only; so cùng token budget trước/sau packing.
5. Cuối cùng mới oracle/retrieved generation và ba SIM đủ / cứu được / không cứu được.

Chi tiết mẫu số, probe và ablation tại [protocol kiểm tra mất context](../evaluation/10-context-preservation-protocol.md). Semantic fallback, cAST, late chunking, LLM contextualization là các challenger riêng, không chạy tất cả cùng lúc rồi không biết cải thiện đến từ đâu.

Vòng này chỉ nghiên cứu, đọc mẫu nguồn và cập nhật tài liệu; không cài thư viện, không tải benchmark/model, không chạy chunk/index hoặc sửa corpus. Bản học liệu vẫn research reference; PDF giữ quarantine, chưa gửi nguồn lên dịch vụ ngoài.

Kiểm tra bàn giao: 266/266 scaffold/syntax/link/source checks đạt, không skip; 13 lượt tham chiếu tới 11 node nguồn đều tồn tại, formula flag/span đã đối chiếu. 271/271 file dữ liệu giữ nguyên checksum trước/sau, không thêm file dữ liệu. Đây là integrity checks, không phải 266 kết quả chunking hay điểm agents.
