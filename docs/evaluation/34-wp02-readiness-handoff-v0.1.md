# WP-02 readiness handoff v0.1

2026-09-06. User giao WP-03 và WP-02; WP-03 technical inputs đã bàn giao, M0/human/calibration pending. Status: verified_local cho docs/integrity, needs_review cho readiness decisions. Card [WP02-READINESS-01](../harness/tasks/WP02-READINESS-01.json); run `wp02-readiness-01-r1`, baseline 197 Git-visible paths trước output edits; card trước baseline. Five-file scope, không product code.

## Deliverables và quyết định

- [Readiness decision table](../architecture/09-multimodal-readiness-v0.1.md): per-region sufficiency + independent authority; prose/handout/scan/mixed/vector/table/formula/unsafe inputs.
- [Probe protocol](33-multimodal-probe-protocol-v0.1.md): SP01..12 hiện có và 6 coverage cases mới MM-P01..06, tất cả NOT RUN qua parser/OCR/model mới; preservation khác failure detection.
- [Inspection record](wp02-inspection-record-v0.1.json): 6 full physical pages trong 4 existing PDFs, source+render hashes, 120 DPI/Poppler 26.07.0, warnings và observations do assistant. Không source text dump hoặc ảnh public.
- Docs index cập nhật link. Historical audit/annotations/results/raw PDFs không sửa.

## Thực thi

Đã render exact six selected pages bằng `pdftoppm -f N -l N -singlefile -r 120 -png` vào ignored `tmp/pdfs/wp02-readiness-01`, tất cả exit 0; đã xem full từng PNG. Poppler báo thiếu display fonts Symbol/ArialUnicode ở micro và syllabus; không có new cross-renderer check hoặc glyph certification. Đây là local inspection kế thừa quarantine; không OCR/VLM, text extraction rerun, model/index/benchmark. Scratch không do harness theo dõi; giữ local có hạn chế nguồn, không publish.

Kết quả thật: `py -3.11 -B scripts/agent_harness.py verify --run wp02-readiness-01-r1 --require-local-data` all_checks_passed tại 2026-09-06T12:24:52 UTC; 31/31 harness tests, 658/658 structure checks, 50 Python files, 17 PDF source hashes, skips = []; đúng 5 output paths. Hash audit riêng: 6/6 source/render pairs khớp, source hashes khớp manifest lịch sử; 105/105 WP-03 pins vẫn khớp. `git diff --check` exit 0. Sau ghi kết quả handoff, final scope check trên cùng baseline. Không biến observed layout thành parser quality score, không nâng six pages này thành sáu mẫu độc lập mới ngoài 13-page audit cũ.

## Self-review và giới hạn

Same-assistant review, không independent/human sign-off. Decision table không có runtime states/DTO/retry algorithm hoặc product dependencies. Missing image/units/blank/formula/context giữ rõ; no silent fallback. OCR confidence/native text/source instruction không là quyền hoặc truth. ARCH-02 vẫn một vai trò suy luận chính, không thêm agents. PDF skill khiến dùng full-page visual inspection và ghi render warnings thay vì suy từ extraction text; không làm PDF authoring.

Technical readiness documents hoàn thành để review; actual parser/OCR comparison, scan corpus/reference, calibrated matching/thresholds, runtime security và source rights vẫn pending. Chưa tự chọn engine/provider/model/DB hoặc production budgets. OpenAI Docs dùng cho WP-03 evaluation methodology, không lựa chọn vendor sản phẩm.

## Điểm tiếp tục

Follow-up 2026-09-06: đã thực hiện bounded decision/gap review theo yêu cầu tiếp tục; đọc [review 35](35-wp02-decision-review-v0.1.md) và [handoff 36](36-wp02-review-handoff-v0.1.md) cho kết quả mới nhất. Không rerun readiness/OCR, không thay bằng chứng lịch sử bên trên; state vẫn WP-02, scope đề xuất chờ xác nhận.

State giữ WP-02 như current review checkpoint, không tự advance WP-04. Model tiếp theo đọc handoff này cùng WP-03 handoff và các deliverables; không chạy lại toàn bộ research hoặc tạo thêm dataset theo quán tính. Review phạm vi nguồn/modality/label gaps trước WP-04 packet; khi tới implementation-grade workflow phải báo `Đã tới ASTRA-01: cần review AI Core workflow`, chờ review + explicit GO trước product code. User chưa cấp broader PDF/OCR external authority trong request này.
