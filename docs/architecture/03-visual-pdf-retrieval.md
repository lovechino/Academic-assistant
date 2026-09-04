# PDF có hình: layout-first, evidence-linked, dual-path retrieval

Ngày: 2026-09-04. Trạng thái: proposed, chưa triển khai/chưa có kết quả so sánh.

## 1. Quyết định

Giữ SHCC cho text, bổ sung logical slide và visual evidence. **Bắt buộc giữ hình gốc/bản render và locator; chưa bắt buộc tạo visual vector cho mọi trang.** Nhánh vision chỉ được chọn sau benchmark và kiểm tra quyền xử lý.

Không có một kiểu chunk tốt cho cả đoạn văn, đồ thị và handout 4 slide/trang. OCR giúp đọc chữ trong ảnh, không tự giữ quan hệ không gian, đường nối, màu, hướng mũi tên hoặc ngữ nghĩa đồ thị.

## 2. Canonical model bổ sung

```text
Document version (hash, rights, access scope)
  Physical page (1-based, size, rotation, render)
    Logical slide / region (bbox, printed label, reading order)
      Text / table / formula / figure / code elements
        Links: caption, explains, continues, requires_context
  Section hierarchy (semantic parent spanning pages when justified)
```

Phân biệt ba số: trang vật lý của PDF, số trang in trên tài liệu, số slide in trong handout. Citation luôn có trang vật lý; có thể thêm nhãn slide cho người đọc. Không lấy nhãn slide làm số trang trong URL PDF.

Record visual tối thiểu:

- `document_id`, `document_version/sha256`, `physical_page_1based`, `logical_slide_id`, `region_id`.
- `bbox`, `coordinate_system`, `rotation`, `render_dpi`, `render_hash`, `asset_hash` nếu có ảnh gốc.
- `source_caption`, `nearby_text_element_ids`, `ocr_text`, `ocr_engine/version`, `quality_flags`.
- `generated_description`, `description_model/revision`, `prompt_version`, `review_status` tách khỏi source.
- `evidence_kind`: raster figure, vector diagram, table, formula, screenshot, photo, decoration, unknown.
- `content_state`: complete, cropped, unreadable, exercise_placeholder, missing_asset, uncertain.
- Toàn bộ rights/lifecycle/ACL kế thừa document, không chỉ kế thừa ở text chunks.

Bbox chuẩn: `[left, top, right, bottom]` normalized 0-1 trên trang đã áp rotation, gốc trên trái. Giữ transform về PDF points và từ crop về trang. Bbox nháp v0.1 chỉ giúp điều hướng, không đủ làm gold IoU.

## 3. Ingestion workflow

1. **Rights/security gate:** checksum, nguồn, quyền, giới hạn kích thước/trang, tệp lỗi/encrypted. Không thực thi JavaScript, macro, link hay chỉ dẫn nằm trong PDF. Nội dung nguồn là dữ liệu không tin cậy.
2. **Profile từng trang:** text coverage/quality, raster coverage, vector density, orientation và layout; không dùng một ngưỡng image-count để quyết định.
3. **Detect handout:** xác định vùng 1-up/2-up/4-up/khác; dùng viền, khoảng trắng, tiêu đề và nhãn slide làm tín hiệu. Nếu không chắc, flag để review, không mặc định lưới cố định.
4. **Parse từng logical slide/region:** lấy native text khi đáng tin; OCR vùng thiếu/khó đọc, không OCR đè lên text layer tốt. Tách table/formula/figure nhưng liên kết chúng.
5. **Lưu visual evidence:** PDF nguyên bản + khả năng tái render đầy đủ. Với vector figure phải render vùng, không chỉ lấy embedded images.
6. **Xây parent/dependency links:** caption, đơn vị, định nghĩa biến, row continuation, slide kế tiếp của cùng ví dụ. Nối có căn cứ, không mở rộng vô hạn.
7. **SHCC:** ranh giới child không vượt sibling section; logical slide là constraint bổ sung, không bắt buộc mỗi slide bằng một chunk. Hình/bảng là evidence object, có thể cần multi-page context.
8. **Index theo policy và benchmark winner**, không tự promote raw/quarantine.

Docling có bước phân loại hình, mô tả hình và nhận dạng công thức; các bước enrichment thường tốn thêm model inference và không bật mặc định. Dùng chúng làm candidate, không coi parser output hay confidence là ground truth. [Docling enrichments](https://docling-project.github.io/docling/usage/enrichments/).

## 4. Xử lý theo loại hình

| Loại | Phải giữ | Không được làm |
|---|---|---|
| Đồ thị | Trục, thang, đơn vị, legend, đường, nhãn, điều kiện | OCR nhãn rồi bỏ đường; đọc số chính xác từ hình mờ |
| ER/flowchart/cây | Node, edge, hướng, cardinality, legend | Biến thành danh sách từ không có quan hệ |
| Screenshot phần mềm | Vùng giao diện, callout, phiên bản, bước trước/sau | Cho rằng UI cũ là hướng dẫn hiện hành |
| Bảng | Header, cell, units, footnote, continuation | Ghép sai cột; bịa giá trị cho ô trống |
| Công thức | Ký hiệu, dấu, sub/superscript, định nghĩa biến | Chỉ lưu LaTeX do model suy ra, bỏ bản gốc |
| Logo/background | Provenance; loại khỏi ranking sau review | Đếm logo lặp là kiến thức hoặc bỏ nhầm legend |
| Hình bài tập chưa hoàn chỉnh | Dấu hỏi, chỗ trống, yêu cầu bài tập | Tự điền rồi nói là nội dung được nguồn cung cấp |

Không suy ra mức quan trọng của ảnh chỉ từ kích thước. Một ký hiệu nhỏ có thể là evidence chính; ảnh lớn có thể chỉ là trang trí.

## 5. Indexing: hai đường về cùng evidence

**Text path:** native/OCR text + metadata/heading/caption có provenance -> BM25+dense -> rerank. Generated description, nếu thử, nằm trong auxiliary view; không được cite như nguồn.

**Visual path (challenger):** render logical slide/trang hoặc region -> visual embedding -> tìm slide/region liên quan. Giữ thêm full-page parent để crop không làm mất caption/đơn vị.

ColPali đề xuất embedding trực tiếp ảnh trang, dùng multi-vector late interaction và giới thiệu ViDoRe cho page retrieval. Đây là cơ sở thử nghiệm visual retrieval, không phải bằng chứng nó tốt nhất trên tiếng Việt hay chi phí thấp nhất cho corpus này. [ColPali, ICLR 2025](https://arxiv.org/abs/2407.01449).

Không cộng trực tiếp score text và visual. Trước fusion:

1. Map text child và visual hit về một candidate group chung (logical slide hoặc physical page, profile cố định).
2. Collapse duplicate theo group trong từng danh sách; giữ child/region score để audit.
3. Rank-fusion các group rồi rerank bằng text/vision phù hợp; không để 10 child của một trang thành 10 phiếu độc lập.
4. Mở rộng có chọn lọc về evidence region + phần giải thích/đơn vị liên quan.
5. Pack text và ảnh cùng source ID vào context budget. Lưu cả token text, số pixel/ảnh, image tokens nếu provider có trả và latency.

Text-only reranker không đủ để đánh giá câu hỏi mà ý nghĩa nằm ở cạnh/đường/điểm của ảnh; trường hợp ấy phải có visual reranking hoặc giữ nhánh visual độc lập đến generator.

## 6. Citation và answer contract

- Generator phải **nhìn được visual evidence** khi claim phụ thuộc hình; caption-only không đủ để chứng minh nội dung trên biểu đồ.
- Mỗi claim trỏ đến PDF version + physical page + region. Link caption/element giúp truy ngược, không thay thế nguồn gốc.
- `observed`: đọc trực tiếp; `derived`: phép suy luận/tính toán từ evidence; `unknown`: thiếu/mờ/không có. Nói rõ khi suy ra, không trình bày suy luận như chữ có sẵn trong file.
- Nếu phần cần trả lời là chỗ trống/bài tập, không bịa rằng đáp án đã được vẽ hoặc in trong nguồn. Quy tắc hỗ trợ bài tập còn phụ thuộc tình trạng bài chấm điểm.
- Hình mờ, crop thiếu trục, chưa giải được tham chiếu: giảm mức khẳng định hoặc yêu cầu nguồn tốt hơn.

Docling có ví dụ giữ text coordinates và render trang để visual grounding; thiết kế dự án cần kiểm tra thêm mapping crop/rotation và quyền truy cập. [Docling visual grounding](https://docling-project.github.io/docling/_generated/examples/visual_grounding/).

## 7. Permission và vận hành

Backend áp filter quyền trước **cả hai nhánh**. Kiểm tra lại khi fetch parent, crop và object storage; không để URL ảnh bypass ACL. Revocation phải chặn text, OCR, description, visual vectors và cache cùng lúc.

Không gửi tài liệu lên dịch vụ OCR/VLM bên ngoài theo mặc định. Chỉ bật sau khi được phép về dữ liệu và ngân sách. Các ảnh render của corpus quarantine không được tự đưa lên demo public.

Cache theo `document_hash + page/region + render_profile`; mô tả/embedding thêm model revision. Đổi renderer/DPI/crop model/description model phải đổi profile và đánh giá lại. Chưa chọn visual embedding model, GPU hay vector DB configuration cuối cùng.

## 8. Điều kiện chốt

Chỉ bật visual branch khi thắng có kiểm soát trên visual-dependent queries ở budget tương đương, không làm giảm lookup text/ACL/citation. Có thể kết quả là: text path cho đa số trang, vision chỉ cho slice khó. Xem [evaluation plan](../evaluation/06-visual-pdf-evaluation.md).
