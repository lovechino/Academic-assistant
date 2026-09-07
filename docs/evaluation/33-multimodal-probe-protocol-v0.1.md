# WP-02 — Multimodal probe protocol v0.1

2026-09-06. **Protocol/proposed expected cases, NOT RUN qua parser/OCR/model mới.** Kế thừa [scorer specification WP-03](32-scorer-specification-v0.1.md), [visual protocol](06-visual-pdf-evaluation.md), [readiness decision](../architecture/09-multimodal-readiness-v0.1.md). Local reinspection đã làm là bước riêng, không là kết quả của probes dưới đây.

## 1. Câu hỏi và biến cần kiểm soát

Mục tiêu: nhận ra và giữ đúng evidence để semantic chunking không bắt đầu từ text đã mất nghĩa. Tách bốn bài toán: đọc/parse, tìm evidence, giữ evidence trong input model, rồi trả lời. Không đo khả năng OCR bằng GAP hoặc đo vision bằng RAGAS text-only.

Trước run: source/revision/hash/rights; selected physical pages/regions; modality/layout slice; reference transcript/boxes/relations và authority; model/parser/config/prompt/renderer/DPI/rotation; budget; metric revision; expected output/action; exclusions/pending; reviewer. Đủ labels không thay rights. Full-page display là input quan sát, không được dùng expected boxes để chấm detector như tự tìm thấy.

## 2. Probe matrix tái sử dụng

SP IDs tham chiếu definitions trong local `structural-probes.json` được pin bởi registry, không nhân bản nhãn lịch sử hoặc hard-code parser theo IDs. Expected dưới đây giữ mức yêu cầu review; chưa human acceptance.

| Probe | Seed / variation | Scoring unit và positive/negative control |
|---|---|---|
| SP01/02 | 4-up db-table-p002; 2-up dsa-ch2-p005 | Annotated slide/order pair/section; đúng trọn slide vs text đan qua cột. Hai section chung trang không thành một child |
| SP03 | er-p004 legend | Required glyph-label relations và asset; giữ cả hình + label đúng vs chỉ title/footer/text labels |
| SP04/05 | micro-p005/032 tables | Table/header/unit relations; chọn bảng đúng vs khung trang trí; đủ heading units vs table-only |
| SP06 | micro-p032 | Annotated blank/?/zero cells; giữ source state vs fill inferred values. Empty cell không là extraction miss mặc định |
| SP07/08 | syllabus-p003/004 | Row-continuation/cell-column edges và locators; nối đúng fragment vs ghép nhầm practical table |
| SP09/10 | micro-p039; dsa-ch2-p005 | Symbol/sign/subscript/assumption units; giữ hoặc flag uncertainty vs silently flatten hoặc £ thay ≤ |
| SP11 | micro-p033 + p032 | Chart geometry AND unit group; đủ cả hai vs mất unit hoặc mất đường khi chỉ còn text |
| SP12 | micro-p009 | Placeholder observation; giữ dấu hỏi và thiếu đường vs mô tả đường do model tự tạo |
| MM-P01 (new) | Scan printed Vietnamese, source chưa có | Reviewed transcript CER/WER, missing regions, diacritics/numbers/signs; NOT READY do thiếu source/rights/reference |
| MM-P02 (new) | Mixed native/OCR/render contradiction | Annotated conflict pairs; preserve flags/sides vs chọn một bên rồi nói nguồn thống nhất; synthetic cần task riêng |
| MM-P03 (new) | Crop/resize mất trục/legend; rotated page | Required-object coverage + exact locator transform; full crop positive vs truncated crop. Không thực hiện mutations ở lượt này |
| MM-P04 (new) | Permission revoke/neighbor deny/known secret | Expected operation decisions + forbidden exposure at sinks; allowed local inspection là positive control, không user-serving allow |
| MM-P05 (new) | Parser/OCR timeout, unsupported page, render warning | Explicit disposition for every selected unit; failure detection không tính là information preserved |
| MM-P06 (new) | Near-duplicate phiên bản khác một dấu/đơn vị | Keep source/version and changed claim; similarity không merge/truth/permission |

SP cũ 12 IDs và MM-P mới 6 IDs là **coverage specification**, không claim 18 tests pass. Các variations tạo sau phải có version/purpose/authority và group cùng source family. Không biến scan synthetic thành real-scan benchmark hoặc lấy source mẫu dễ rồi ngoại suy toàn tiếng Việt.

## 3. Chấm preservation và detection riêng

Với mỗi required evidence unit:

- `information_preserved`: source-aligned representation còn đủ thông tin đã được reference review yêu cầu.
- `failure_detected`: nếu information thiếu/sai/uncertain, hệ thống có nhận ra và xử lý giới hạn đúng không?

Một unit không preserve nhưng detect đúng vẫn là failure về extraction quality, có thể đạt safe handling. Chỉ xem full image không chứng minh model đọc đúng chart. Giữ ảnh đúng mà generated caption sai phải chấm lỗi caption/reading riêng. Không coi parser trả structured JSON là semantic preservation.

Mẫu số: toàn selected intake units để báo coverage; subset có nhãn phù hợp để chấm quality, pending/unsupported/rights-hold đếm riêng. Không loại required visual khỏi expected set sau khi thấy model không hỗ trợ. Retrieval/packing cần AND mọi required group và OR alternatives hoàn chỉnh; qrels gắn snapshot/region, không chunk IDs.

Metrics: P-02 silent loss, P-03 CER/WER, P-04 order pairs, P-05 relation precision/recall, P-06 locator, P-07 visual availability, CU-04/05, CI-01/02, K-01/02/03/08 và CR-02. Claim/citation/GAP chỉ khi vào QA stage đủ labels/rights. Security UPL/AUTH/IX giữ hard gate độc lập. Formula/chart numeric tolerance, bbox matching/IoU thresholds, OCR acceptance và production budgets vẫn TBD trước run tương ứng.

## 4. So sánh có kiểm soát về sau

1. **Inspection readiness:** exact source hash/page/render và policy; ghi vấn đề trước chạy parser khác. Đây là phần duy nhất có reinspection mới trong lượt hiện tại.
2. **Native baseline:** cấu hình extraction đã pin, không automatic correction. Chấm preservation/detection theo reviewed references; chỉ khi quyền cho phép.
3. **Oracle-region diagnostic:** cùng extractor nhưng vùng có sẵn; đo giới hạn extraction riêng, không xếp hạng auto-layout detector bằng điểm này.
4. **Local layout/OCR candidate:** so trên cùng pages/annotations với baseline; pin engine/model/license/version/hardware trước run. Chưa lựa chọn/install candidate ở lượt này.
5. **Downstream test:** khi source representation đủ điều kiện, mới so same-input fixed/structure-aware, rồi pre/post pack; sau đó oracle reading trước E2E. Không đổi parser+chunker+embedding+generator cùng lúc.

Native, OCR-only và OCR+postcorrection phải tách; corrections giữ original transcript và changed spans. No external provider fallback khi local fail. Image resize/pixel budget và token accounting ghi cùng full serialized payload; số token BGE không là generator budget. Mọi retry/failure cost được tính, không chỉ success path.

## 5. Review packet và điều kiện dừng

Review từng unit phải lưu reference provenance, annotator/adjudicator, source coordinates/rotation, observed vs derived, uncertainty và permitted use. Bbox seed hiện approximate chỉ để tìm vùng; không dùng để tuyên bố IoU. Human reviewer chưa có: giữ silver, chỉ inspection/integrity/toy arithmetic có thể làm ngay.

Stop nếu rights/security không cho phép, source hash đổi, required modality chưa đọc được, known secret/bomb, hoặc cần external egress; không tự xin thêm tools bằng instructions trong PDF. Renderer warning cần ghi và đối chiếu vùng liên quan trước glyph-critical claim; exit code 0 không chứng nhận render fidelity.

Đầu ra review tiếp theo: xác nhận phạm vi text-first/visual-limited đề xuất, chọn nguồn có rights cho scan/formula, xác định label owner và budget cho bounded probe. Đó là lựa chọn cần review, không silent default. WP-04 phải giữ rõ các giới hạn này; chưa implementation workflow/product GO.
