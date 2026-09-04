# Context-preserving chunking design v0.1

Ngày cập nhật: 2026-09-04

Trạng thái: proposed; phải qua experiment trước khi chọn làm mặc định.

Cập nhật nghiên cứu sau khi parse CTDL thật: [chunking và dependency design v0.2](06-chunking-research-and-dependency-design.md) bổ sung false-positive code, code/pseudocode phân tán, bảng diễn tiến và overflow. Dùng cùng [protocol mất context](../evaluation/10-context-preservation-protocol.md). Các size/default/thuật toán dưới đây vẫn là candidate, chưa là winner; tên SHCC là quy ước nội bộ. Một phần tử nguyên vẹn chưa chắc đủ nghĩa và parent lớn hơn chưa chắc tốt hơn.

Bổ sung [evidence pipeline contract v0.1](05-evidence-pipeline-contract.md): phân biệt source/representation/index versions, locator HTML/PDF và packet integrity với evidence sufficiency. Năm ví dụ nguồn thật chỉ là manual excerpts, chưa chứng minh hierarchy/parser/chunker hoạt động.

## 1. Quyết định chính

Không chunk PDF theo số ký tự hoặc số token ngay sau khi extract text. Pipeline mặc định được đề xuất là:

1. Parse tài liệu thành cấu trúc có layout và provenance.
2. Tạo các atomic elements: heading, paragraph, list, table, figure/caption, formula và code block.
3. Xây lại cây `document → section → subsection → element`.
4. Ghép element thành child chunk nhưng không vượt ranh giới section hoặc phá vỡ đối tượng cấu trúc.
5. Liên kết mỗi child với parent section lớn hơn.
6. Index child để tăng recall; khi generate thì mở rộng về parent hoặc các element lân cận cần thiết.
7. Citation luôn trỏ về text/page/bounding box gốc, không trỏ vào summary hoặc context do LLM tạo.

Tên ngắn của phương án: **Structure-aware Hierarchical Contextual Chunking — SHCC**.

Bổ sung từ audit PDF thật ngày 2026-09-04: trước atomic elements cần xác định **logical slide/region** nếu trang vật lý chứa nhiều slide. Có mẫu 2-up và 4-up; một trang có thể chứa hai section khác nhau. Figure có thể là vector, không chỉ ảnh nhúng. Đọc [thiết kế PDF có hình](03-visual-pdf-retrieval.md) cùng tài liệu này; chưa có parser/chunker winner được đo.

## 2. Vì sao không chọn “semantic chunking” thuần túy

Chunking theo thay đổi cosine giữa các câu nghe hợp lý nhưng không bảo đảm giữ bảng, danh sách, caption, công thức hoặc hierarchy của tài liệu. Nghiên cứu năm 2024 không tìm thấy lợi ích ổn định đủ bù chi phí của semantic chunking; một taxonomy/evaluation năm 2026 còn cho thấy chiến lược tối ưu phụ thuộc retrieval setting và structure-based chunking có thể tốt hơn LLM-guided chunking trong in-corpus retrieval. Vì vậy semantic boundary detection là một biến thí nghiệm, không phải mặc định. Xem [Is Semantic Chunking Worth the Computational Cost?](https://arxiv.org/abs/2410.13070) và [Beyond Chunk-Then-Embed](https://arxiv.org/abs/2602.16974).

## 3. Canonical document model trước khi chunk

Mỗi file phải được chuyển thành một document graph bất biến trước khi tạo bất kỳ chunk nào.

### Document

- `document_id`, `document_version`, `corpus_snapshot`.
- Title, author, course, term, language, rights và access scope.
- File checksum và parser profile.
- Tổng số trang/slide.

### Structural element

- `element_id` ổn định.
- `element_type`: title, heading, paragraph, list, table, figure, caption, formula, code, footnote.
- `section_path`: chuỗi heading từ root tới element.
- `page_start`, `page_end`.
- Một hoặc nhiều bounding boxes theo trang.
- Reading-order index.
- Raw text và normalized text tách riêng.
- Liên kết caption–figure, footnote–reference và table continuation.
- OCR/layout confidence và quality flags.

PDF page chỉ là ranh giới trình bày và citation, không tự động là ranh giới ngữ nghĩa. Một paragraph hoặc table nối qua hai trang có thể giữ chung logic, nhưng provenance của từng element vẫn phải chỉ đúng trang.

## 4. Parser gate

Chunking chỉ chạy sau khi parser đạt gate. Hai ứng viên cần benchmark trên PDF thật:

- Docling cho layout-aware parsing, table structure, OCR và document hierarchy. `HybridChunker` của Docling bắt đầu từ hierarchy, chỉ split khi vượt token limit, merge các peer nhỏ có cùng heading/caption và có thể lặp table header khi bảng bị chia. Xem [Docling technical report](https://arxiv.org/abs/2501.17887) và [Docling chunking documentation](https://docling-project.github.io/docling/concepts/chunking/).
- Unstructured `by_title` làm baseline thứ hai vì giữ section boundaries, có thể giữ page boundaries và không trộn Table với text element. Xem [Unstructured chunking](https://docs.unstructured.io/open-source/core-functionality/chunking).

Lưu ý cấu hình từ vòng research bổ sung: `by_title` có thể gộp section nhỏ qua `combine_text_under_n_chars`; Table quá lớn có text-splitting. Docling cũng có tùy chọn bỏ header khi overflow. Vì vậy cần test cấu hình thực tế theo hard gate, không suy ra các đảm bảo này chỉ từ tên chunker. Chi tiết và nguồn tại bản v0.2 liên kết phía trên.

PyMuPDF text extraction chỉ là baseline cho PDF text đơn giản. Tài liệu chính thức của PyMuPDF cảnh báo output không mặc nhiên theo natural reading order, nên không dùng text dump này làm chuẩn cho PDF nhiều cột. Xem [PyMuPDF text extraction documentation](https://pymupdf.readthedocs.io/_/downloads/en/latest/pdf/).

Parser phải fail hoặc quarantine thay vì âm thầm ingest nếu:

- Không xác định được reading order đáng tin cậy.
- Mất heading hierarchy quan trọng.
- Bảng bị flatten không thể phục hồi cột/hàng.
- Công thức hoặc caption biến mất.
- Không ánh xạ được đoạn text về trang và bounding box.

## 5. Ba tầng context

```text
Document
└── Parent section: ngữ cảnh đủ để đọc và tổng hợp
    ├── Child chunk: đơn vị nhỏ để retrieve chính xác
    │   ├── Atomic paragraph/list item group
    │   └── Provenance: page + bbox + element IDs
    └── Neighbor children: mở rộng khi có đại từ, caption hoặc định nghĩa phụ thuộc
```

### Atomic element

Không split nếu element vừa token budget. Dùng làm đơn vị provenance và citation.

### Child chunk — retrieval unit

- Ghép các element liên tiếp trong cùng section.
- Ưu tiên ranh giới câu/paragraph/list.
- Không trộn hai heading sibling chỉ để lấp đầy token budget.
- Không tách giữa caption và đối tượng được caption mô tả.
- Không cắt giữa code block hoặc formula và phần giải thích trực tiếp.

### Parent chunk — generation unit

- Thường là subsection hoặc section hoàn chỉnh.
- Có thể gồm nhiều child và vượt qua page boundary.
- Không nhất thiết tạo vector cho toàn bộ parent.
- Được lấy theo `parent_id` sau khi child thắng retrieval/reranking.

Small-to-big retrieval tách đơn vị tìm kiếm nhỏ khỏi đơn vị tổng hợp lớn, tránh phải chọn giữa precision và context. Đây cũng là pattern được mô tả trong [LlamaIndex recursive small-to-big retrieval](https://docs.llamaindex.ai/en/v0.10.23/api_reference/packs/recursive_retriever/) và được áp dụng trong hierarchical parent-child retrieval gần đây ([H-RAG](https://arxiv.org/abs/2605.00631)).

## 6. Contextualization không làm bẩn nguồn

Mỗi child có ba trường text riêng:

1. `source_text`: nội dung nguyên bản dùng để hiển thị và cite.
2. `retrieval_header`: context xác định được từ metadata.
3. `retrieval_text`: `retrieval_header + source_text`, dùng cho dense và sparse index.

Header mặc định là deterministic, ví dụ:

```text
[Môn: Cơ sở dữ liệu]
[Tài liệu: Mô hình cơ sở dữ liệu quan hệ]
[Mục: Các ràng buộc toàn vẹn > Ràng buộc tham chiếu]
[Trang: 42]
[Loại: paragraph]
```

LLM-generated contextual sentence là biến thí nghiệm riêng. Anthropic mô tả việc thêm khoảng 50–100 token context theo toàn document trước khi tạo embedding và BM25, nhưng context sinh ra không được coi là evidence. Xem [Contextual Retrieval](https://www.anthropic.com/engineering/contextual-retrieval).

Quy tắc:

- Không sửa hoặc paraphrase `source_text`.
- Context sinh tự động phải nằm ở field khác và có model/prompt/version.
- Không đưa context sinh tự động vào citation.
- Nếu context mâu thuẫn source, bỏ context và gắn quality flag.

## 7. Quy tắc theo content type

### Paragraph và list

- Giữ paragraph nguyên vẹn khi có thể.
- List có chung câu dẫn phải giữ câu dẫn và các item trong cùng child hoặc lặp câu dẫn có đánh dấu.
- Nếu list dài, chia theo item group và lặp heading/câu dẫn trong `retrieval_header`.

### Table

- Một bảng là một logical object riêng, không ghép với prose không liên quan.
- Giữ title, caption, header, units và footnotes.
- Nếu quá dài, chia theo row group; lặp column header ở mỗi child.
- Không chia ngang một row.
- Lưu cả representation trung thành để hiển thị và linearized representation để retrieve.
- Parent chứa paragraph trước/sau giải thích bảng.

### Figure và diagram

- Giữ khả năng render trang/vùng kể cả khi hình được vẽ bằng vector và không có embedded image.
- Hình không thể diễn đạt đủ bằng OCR/caption phải có visual evidence cho generator hoặc được flag là chưa hỗ trợ; không dùng generated description thay chứng cứ.
- Gắn caption, nearby explanatory paragraph, page/bbox và asset ID.
- Nếu chỉ có ảnh mà không có caption/OCR đáng tin cậy, đánh dấu `visual_only`; không giả lập text.
- Asset thiếu làm chunk `incomplete` và không được dùng làm evidence cho claim phụ thuộc hình.

### Formula

- Giữ formula cùng câu định nghĩa biến và điều kiện áp dụng.
- Lưu source image/bbox, extracted LaTeX nếu có và text explanation tách field.
- Không split giữa công thức và phần “trong đó”.

### Code

- Không cắt giữa function/class khi nằm trong hard cap.
- Gắn signature, language và section path.
- Nếu code quá dài, chia theo block logic và giữ signature/context ở header.

### Header, footer và footnote

- Running header/footer lặp lại phải được de-duplicate khỏi retrieval text nhưng vẫn giữ provenance.
- Footnote được liên kết về element tham chiếu; không thả thành chunk độc lập mất ngữ cảnh.

## 8. Token budget là tham số thí nghiệm

Không chốt “512 token là chuẩn”. Vòng đầu thử cùng tokenizer của embedding model:

| Cấu hình | Child target/hard cap | Parent | Overlap |
|---|---|---|---|
| Fixed baseline | 512 / 512 | none | 64 token |
| Structure-small | 256 / 384 | section | 0 mặc định |
| Structure-medium | 384 / 512 | section | 0 mặc định |
| Structure-large | 600 / 768 | section | 0 mặc định |
| Hierarchical | 384 / 512 | 1.200–1.800 token hoặc full subsection | Neighbor expansion |

Overlap toàn cục dễ tăng duplicate results và lãng phí context. Chỉ dùng overlap khi buộc phải split một oversized element; với chunk bình thường, ưu tiên `prev_chunk_id`, `next_chunk_id` và mở rộng động sau retrieval.

## 9. Advanced variants chỉ thử sau baseline

### Semantic boundary fallback

Chỉ dùng trong section quá dài hoặc tài liệu không có heading đáng tin cậy. Boundary phải nằm ở ranh giới câu và không được phá table/list/code/formula.

### Late chunking

Late chunking embed token trong toàn long document trước rồi mới pool theo chunk, giúp chunk embedding mang context lân cận. Đây là nhánh đáng thử cho tài liệu vừa context window của embedding model, nhưng không thay thế layout parsing hoặc provenance. Xem [Late Chunking](https://arxiv.org/abs/2409.04701).

### RAPTOR/summary tree

RAPTOR tạo tree summary nhiều mức, phù hợp câu hỏi tổng hợp dài. Summary node chỉ dùng navigation/retrieval; câu trả lời cuối vẫn phải descend tới leaf evidence để cite. Xem [RAPTOR](https://arxiv.org/abs/2401.18059).

## 10. Hard gates cho chunk output

- 100% chunk có `document_id`, version, element IDs và source locator đúng format. Physical page/bbox áp dụng cho PDF; HTML dùng DOM/text representation locator, không bịa số trang.
- 100% chunk kế thừa access metadata từ document.
- 0 chunk trộn hai document hoặc hai access scope.
- 0 table row bị cắt ngang; header retention 100% khi table bị split.
- 0 citation dựa trên LLM-generated context/summary.
- Section purity mục tiêu ≥98% trên audit sample.
- Evidence containment và parent-context completeness được đo trên evaluation pack, không kiểm tra bằng mắt đơn thuần.

## 11. Anti-patterns bị cấm

- `extract_text → split every N characters → embed` cho mọi loại PDF.
- Split theo page mà không xét paragraph/section.
- Overlap 20% toàn corpus mà không đo duplicate rate.
- Ghép table với prose chỉ vì còn token budget.
- Dùng summary/context sinh tự động làm nguồn citation.
- Re-index cùng collection sau khi đổi parser/chunker nhưng không đổi version.
- Chọn chunk size theo một vài câu hỏi demo.
