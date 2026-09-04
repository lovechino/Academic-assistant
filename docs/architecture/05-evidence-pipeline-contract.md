# Evidence pipeline contract v0.1 — từ nguồn đến citation

Ngày: 2026-09-04. Trạng thái: **working draft + ví dụ đối chiếu nguồn**, chưa là schema/API đã freeze, chưa có parser/chunker/index/model chạy trong vòng này.

Cập nhật ở vòng tiếp nối cùng ngày: đã [parse cấu trúc HTML của 16 module CTDL](../data/08-voer-dsa-structural-representation.md) và nối 22 locator về nguồn. Các ví dụ/manual chunks dưới đây giữ nguyên như artifact thiết kế; không biến chúng thành kết quả chunker. Chưa chunk/index/model; code, công thức và ngữ cảnh hình/bảng còn cần review.

## 1. Quyết định của vòng này

Thiết kế dữ liệu phải giúp trả lời: “Một ý được trả lời dựa trên đoạn nào, thuộc phiên bản nào, đã đi qua chunk/context nào, và còn được phép sử dụng không?”. Không chỉ lưu một chuỗi text cùng document ID.

Luồng provenance đề xuất:

```text
Source snapshot + representation version
  -> structural elements + source locators
  -> child chunks + parent/neighbor relationships
  -> versioned index references
  -> retrieval candidates -> packed source fragments
  -> draft claims + citation links -> authorized public response

Evaluation sidecar: reference claims/qrels -> chấm các đầu ra trên
                   KHÔNG đi vào model input hoặc access filter
```

**Ba điều độc lập:** packet đúng cấu trúc; packet đủ evidence cho câu hỏi; người dùng được phép xem. Đạt một điều không suy ra hai điều còn lại. Contract không tự giải quyết semantic understanding hoặc authorization.

Người dùng đã xác nhận cần SIM-01/02/03 để kiểm tra đủ context, khôi phục context và không tự điền khi thiếu context. Số lần retry, ngân sách và cách hiển thị partial answer vẫn là quyết định mở; không tự chốt “một lần” thành policy sản phẩm.

## 2. Ownership và ranh giới

| Phần | Owner | Trách nhiệm |
|---|---|---|
| Source identity, rights/admission, policy hiện hành | Backend/data governance | Không lấy trạng thái trong vector payload làm quyền hiện hành duy nhất |
| Representation, elements, chunking, index revision, packing trace | AI core | Giữ provenance, không tự cấp quyền hoặc publish nguồn |
| Claim-citation links và assessment | AI core | Trả kết quả kiểm tra và giới hạn, không biến self-check thành gold |
| Public DTO/source reference, kiểm tra cuối và mở nguồn | Backend | Chỉ trả projection được phép; không trả path nội bộ |
| Hiển thị answer/partial/error và mở citation | Frontend | Không sửa version, tự cấp quyền hoặc dùng offset khác representation |
| Reference claims/qrels, expected coverage | Evaluation | Tách khỏi query-time input, scorer và corpus permissions |

Các lớp trung gian ingestion/chunk ở đây chủ yếu là nội bộ AI core. [Evidence packet boundary](../../contracts/evidence-packet.md) mô tả phần giao tiếp; không tạo shared runtime package hoặc API schema trong vòng này.

## 3. Document identity và các biểu diễn nguồn

Một nguồn cần phân biệt ít nhất ba loại version:

| Loại | Nội dung cần giữ | Khi thay đổi |
|---|---|---|
| Source snapshot | document ID, source version nếu có, raw checksum, thời điểm nguồn, corpus snapshot | Tạo source revision mới; nhãn “v1” của website không đủ nếu bytes đổi |
| Representation | parser/normalization profile, output checksum, mapping về raw source | Tạo representation mới; không áp offsets cũ vào text mới |
| Index | parser/chunker/contextualizer/embedding/sparse/filter-schema config và revision | Tạo index revision mới; không ghi đè rồi so benchmark như cùng cấu hình |

`document_ref` trong ví dụ gồm `document_id`, `source_version`, `source_file_sha256`, `representation_id`, `representation_sha256`. Đây là khóa ghép tham chiếu nguồn, không phải giấy phép truy cập.

Source registry giữ riêng: title/author đúng metadata, origin format, raw source location, rights và approval. Path filesystem chỉ thuộc artifact local/backend, không nằm trong model input hay public citation.

Raw source bất biến; normalized/retrieval text là dẫn xuất có version. Chuẩn hóa để tìm kiếm không được âm thầm thay nội dung dùng để cite. ID element/chunk production cần gắn source/representation/profile/range; các ID dễ đọc trong ví dụ hiện tại chỉ là aliases, chưa đóng thuật toán sinh ID.

## 4. Structural element: không đánh đồng với một đoạn text bất kỳ

Mô hình đề xuất cho parser thật:

| Field/nhóm | Ý nghĩa |
|---|---|
| `element_id`, `document_ref` | Identity/version có thể truy ngược |
| `element_type` | heading, paragraph, list, table, figure, caption, formula, code, footnote; chưa biết phải ghi unknown |
| `source_locators` | Một hoặc nhiều vùng thật; không ép một paragraph nối trang thành một bbox giả |
| `section_path`, reading order | Cây mục và thứ tự đọc có provenance/trạng thái review |
| `relationships` | Caption của hình nào, bảng nối ở đâu, công thức dùng định nghĩa biến nào, footnote của đoạn nào |
| `source_text`, representations | Tách nguồn quan sát được, OCR, text tuyến tính hóa và mô tả sinh tự động |
| `quality_flags`, confidence provenance | Thiếu ảnh, sai thứ tự, OCR chưa chắc, formula chưa khôi phục; không tự điền confidence=1 |

### HTML và PDF dùng locator khác nhau

- **HTML:** DOM/block anchor nếu parser xác định được; text offsets phải nêu representation, checksum và hệ tọa độ. Ví dụ legacy hiện tại dùng Unicode codepoint `[start,end)` trong text chuẩn hóa từ `/data/text`, không phải offset raw HTML, byte hay JavaScript UTF-16. Không có số trang PDF.
- **PDF:** physical page index 0-based; page label là field hiển thị riêng, không thay physical index. Bbox cần page dimensions, units, origin, page box và rotation/transform profile. Đề xuất quy ước sau parse: top-left, đơn vị point, theo kích thước hiển thị đã áp rotation; phải giữ phép đổi từ hệ tọa độ parser và kiểm tra trước khi áp dụng.
- **Handout:** thêm logical slide/region ID trong physical page. Không coi cả trang 4-up là một semantic section.
- **Nhiều trang/vùng:** lưu danh sách locator, không bịa một hình chữ nhật phủ mọi trang.

Các nhánh PDF/DOM/bbox là **đặc tả đề xuất, chưa có fixture kiểm chứng trong vòng này**. Chưa bổ sung tool/parser SDK hoặc OCR.

### Hình, bảng, công thức

Giữ asset identity/checksum, vị trí, caption/đoạn giải thích gốc, chất lượng và availability. OCR/ảnh render/description phải có transformation provenance. Caption do model viết không thay evidence gốc. Nếu câu hỏi phụ thuộc hình mà asset thiếu hoặc chỉ có mô tả chưa kiểm chứng, không tuyên bố visual evidence đã đủ.

Với bảng nối trang: giữ logical table ID, từng phần, hàng/cột, header/đơn vị/chú thích và nơi lấy chúng. Lặp header phục vụ đọc phải trỏ lại header nguồn, không giả nó tồn tại nguyên văn tại mọi trang. Công thức phải gắn điều kiện và biến; code phải giữ các block có ý nghĩa khi ngân sách cho phép.

## 5. Chunk, parent và index record

### Chunk

Chunk giữ `chunk_id`, document ref, element IDs, **danh sách source fragments có vị trí**, profile tạo chunk, liên kết parent/neighbor và quality flags. Không chỉ ghép text rồi bỏ bản đồ về nguồn.

Tách hai vùng:

- `source_fragments`: nội dung nguồn có thể đối chiếu và cite.
- `retrieval_header`: title/mục/context xác định hoặc sinh ra, có origin, không phải evidence để cite trong profile này.

Không trộn document/version/access scope. Không tự xem null neighbor là đầu/cuối tài liệu nếu cấu trúc chưa được dựng. Fragment bị cắt phải cập nhật vùng source và lý do; không giữ full-span locator khi chỉ gửi nửa text.

### Parent/context window

Parent section đúng cần parser xác định hierarchy. Một window chỉ được tạo từ các vùng lân cận **không mặc nhiên là section đầy đủ**. Vì vậy ví dụ dùng `context_window_id` + `is_verified_section=false`, không giả làm parser output đã kiểm chứng.

Expansion phải truy nguyên cùng phiên bản, áp quyền hiện hành, ghi nguồn child dẫn tới expansion và lý do. Có thể tăng context nhưng cũng tăng phần dư; không coi parent càng dài càng tốt.

### Index record

Index record tham chiếu chunk/document ref, manifest revision và access/quality metadata; không chứa reference answer hoặc qrels. Corpus cho thử retrieval dự kiến vẫn là toàn bộ 16 module hợp lệ, không dùng 3 tài liệu/6 chunk của ví dụ này làm allowlist đáp án.

Metadata trong index hỗ trợ prefilter, nhưng có thể cũ; Backend vẫn là authority cho revoke/admission ở những bước nhạy cảm. Đổi index không sửa raw source. Cache cũng phải giữ dependency versions/policy context, không chỉ question hash và TTL.

## 6. Evidence packet và ba loại kiểm tra

Chi tiết field ở [boundary draft](../../contracts/evidence-packet.md). Packet chỉ mô tả các fragments **thực sự được chuyển tới generation**, kể cả nội dung do expansion đưa thêm.

| Kiểm tra | Có thể xác định từ gì? | Không được suy ra |
|---|---|---|
| Integrity | Hash, offsets, text match, references, assets, serialization | Không tự chứng minh câu trả lời đúng/đủ |
| Evidence sufficiency | Câu hỏi + evidence + assessment có phương pháp; qrels chỉ ở evaluator | Không mặc định thiếu vì câu hỏi là so sánh |
| Permission/currentness | Trusted identity, admission và policy/version hiện hành | Không lấy boolean trong artifact nghiên cứu làm quyền serving |

Query-time không có sẵn required claims của bộ test. Nó có thể phân rã yêu cầu từ câu hỏi (ví dụ hai đối tượng và tiêu chí thứ tự lấy), kiểm tra các dấu hiệu thiếu context và tìm thêm. Chất lượng của cơ chế assessment đó phải được thử riêng, gồm đủ/thiếu evidence và false refusal. Trong ví dụ, `answerability_assessment.status=not_assessed` vì chưa chạy cơ chế này.

`packing_trace` ghi phần giữ/bỏ/thay bằng parent và lý do. Runtime có thể biết một fragment bị bỏ, nhưng chưa tự biết đó là evidence bắt buộc. Evaluator dùng mapping riêng để xác nhận `packing_loss`; không đưa tên nhóm đáp án vào prompt để giúp hệ thống vượt test.

### Ngân sách phải đo trên input thực

Không dùng số ký tự hoặc tổng token của child làm token count của request. Khi cấu hình model thật, phải tính input đã serialize gồm system/query/history, wrappers/evidence, tools và hình theo accounting phù hợp, cộng phần dự trữ output và margin so với context limit. Ghi tokenizer/model/profile, method measured/estimated, số token và cách tính.

Hiện chưa chọn tokenizer/model: `measurement_state=not_configured`, các trường token là null, `token_fit_claimed=false`. `source_codepoints` chỉ là độ dài text nguồn để kiểm tra nội bộ, không gồm headers/wrappers và không chứng minh packet vừa ngân sách.

## 7. Claim/citation và trạng thái trả lời

Một claim tổng hợp có thể cần nhiều citation cùng lúc. Không đòi nguồn phải chứa nguyên văn câu so sánh; có thể tổng hợp từ hai phía nếu lập luận được hỗ trợ. Ngược lại, citation về stack không đủ cho claim khác biệt stack/queue.

Claim-citation mapping cần trỏ tới **packet item đã sử dụng** và locator nguồn tương ứng. Không cite item từng retrieved nhưng đã bị packing loại. Không cite header/summary sinh ra. Mở nguồn phải kiểm tra lại identity/version/quyền; thiếu bản cũ thì báo đúng trạng thái, không mở bản mới bằng offset cũ.

Kết quả cần tách: câu trả lời đầy đủ, một phần, cần làm rõ/thiếu evidence, bị policy/quyền chặn và lỗi vận hành. Timeout không phải bằng chứng rằng corpus không có đáp án. Đầu ra học thuật đang ở bản nháp cần qua kiểm tra trước delivery; streaming/quy tắc retry chưa chốt trong vòng này.

## 8. Năm ví dụ trên nguồn CTDL thật

[Bộ ví dụ](../../data/evaluation/silver/voer-dsa-contract-examples-v0.1/README.md) dùng ba module của snapshot `voer-2026-09-04-r1`: stack, queue và danh sách nối đơn. Tác giả theo nguồn: Khoa CNTT ĐHSP KT Hưng Yên. Giữ policy research reference, chưa phục vụ sinh viên hoặc được reviewer phê duyệt.

Các element/chunk được **chọn bằng tay từ mapping**, chỉ minh họa contract; không phải parser/chunker/retriever output hay corpus benchmark. Không dùng chúng để chọn chunk size. Heading chỉ là hint chưa có DOM anchor. `text_excerpt` không tự xưng là paragraph/list đã parse.

| Ví dụ | Evidence trước → sau packing | Ý có evidence theo silver | Text nguồn trong packet | Ý nghĩa |
|---|---|---|---:|---|
| EX-01: LIFO, Push, Pop | 3/3 → 3/3 nhóm | 3/3 | 334 codepoint | Ba yêu cầu trong cùng module vẫn cần đủ từng đoạn |
| EX-02: cấu tạo node | 2/2 → 2/2 nhóm | 3/3 | 265 | Một nhóm AND cần cả đoạn dữ liệu và liên kết |
| EX-03: so sánh đầy đủ | 2/2 → 2/2 nhóm | 3/3 | 452 | Hai nguồn đủ hỗ trợ một claim so sánh |
| EX-04: bỏ queue | 2/2 → 1/2 nhóm | 1/3 | 220 | Packet có thể hợp lệ về cấu trúc nhưng thiếu evidence; không chốt câu hỏi unanswerable |
| EX-05: parent-window repair minh họa | 2/2 → 2/2 nhóm cuối | 3/3 | 698 | Khôi phục evidence và thêm context; chưa chứng minh hiệu quả hoặc fit token budget |

EX-05 là một trace minh họa độc lập, không phải chương trình recovery đã chạy fetch thật sau EX-04. Parent stack kéo thêm đoạn Push/Pop so với EX-03; các thông tin thêm đó không bắt buộc cho phép so sánh. Đây là đánh đổi cần đo, không phải lý do mặc định lấy toàn parent.

Trong EX-04, phía queue bị bỏ hoàn toàn để minh họa thiếu evidence rõ ràng. Không lấy việc một quote bị thiếu một ký tự làm bằng chứng chắc chắn nó đã mất nghĩa. Rule coverage theo source spans vẫn bảo thủ và qrels silver chưa exhaustive.

`examples.json` có candidate traces, model-input mock và answer drafts ở các vùng riêng. Chỉ object `model_input` mô tả input generation; không gửi cả bundle hoặc answer draft vào model. `evaluation-sidecar.json` mới chứa case ID, expected coverage và liên kết reference claims. Draft answer là assistant viết, không phải output LLM.

## 9. Đã kiểm tra và giới hạn

[Verifier read-only](../../ai-core/experiments/evidence-contract/README.md) đã kiểm tra hashes/raw source, text offsets, element/chunk/window/packet lineage, tách evaluator và citation coverage. Bản chạy đầu đạt 331 checks; chín mutation đều bị phát hiện: hash sai, text thay đổi, page PDF giả trên HTML, parent sai tài liệu, qrels lọt vào input, citation tới item đã bỏ, token-fit giả, nâng research thành serving và cho cite header.

Đây là focused validation cho fixture, **không phải JSON Schema validator tổng quát**, runtime contract suite, semantic judge hoặc security audit. Helper chỉ dùng standard library, không ghi file hoặc chạy model.

Raw corpus, mapping, nhãn silver và kết quả SIM trước giữ nguyên. 17 PDF vẫn quarantine. Chưa chốt parser/chunker/index/model, chưa đo accuracy/latency và chưa xây DOM/PDF viewer.

Kiểm tra bàn giao: chạy lại verifier khớp toàn bộ bản `validation.json` đã lưu, gồm checksums. Structural verifier đạt 229/229 checks, sáu file Python qua kiểm tra cú pháp, 17 PDF giữ đúng hash, không skip. Toàn bộ 247 file `data/` có trước vòng này giữ nguyên SHA-256; chỉ thêm bốn file của bộ contract examples mới. Không sửa runtime source của ba component.

## 10. Bước tiếp theo, chưa thực thi trong vòng này

1. Review contract và các field còn mở: ID/version scheme, authority handle, tokenizer/budget, retry/partial UX, streaming, historical-source retention.
2. Chuyển từ manual excerpts sang structural representation của toàn bộ corpus được phép, kiểm tra parser alignment/quality trước khi chunk.
3. Dùng cùng representation để thử chunking/retrieval có kiểm soát; evaluator đọc mapping riêng. Báo before/after packing và từng nhóm lỗi.
4. Nhánh PDF/hình cần parser/locator/asset fixtures riêng và điều kiện quyền tương ứng; không tự nhập kho cách ly vào serving.

Chưa bắt đầu baseline chỉ vì đã có contract. Khi chọn công cụ/model thực, kiểm tra lại phiên bản, điều kiện sử dụng, môi trường và ngân sách trước khi chạy.
