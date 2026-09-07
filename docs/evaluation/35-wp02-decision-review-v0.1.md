# WP-02 — Review quyết định và khoảng trống trước WP-04

2026-09-06. Review kỹ thuật của assistant theo yêu cầu tiếp tục; **không phải independent review, human acceptance hoặc product GO**. Đọc cùng [WP-02 handoff](34-wp02-readiness-handoff-v0.1.md), [readiness](../architecture/09-multimodal-readiness-v0.1.md) và [WP-03 scorer specification](32-scorer-specification-v0.1.md). Không thay các metric contracts, nhãn hoặc kết quả lịch sử.

## 1. Kết luận và phạm vi đề xuất

Đã đủ tài liệu để xác định đầu vào/gaps của WP-04; chưa đủ để gọi ingestion, semantic scorer hoặc agent là đã đạt chất lượng. Không cần crawl thêm hàng loạt để giải quyết các quyết định dưới đây.

Đề xuất lát cắt đầu: **Academic QA chọn mode thủ công, text có cấu trúc đủ bằng chứng; visual chưa đọc đủ thì giới hạn claim tương ứng**. Giữ [ARCH-02](../architecture/08-controlled-workflow-decision-v0.1.md): nhiều bước được kiểm soát, một vai trò suy luận chính, rules cho trường hợp rõ; chưa router đa mode hoặc multi-agent tự chủ.

Text-first là giới hạn năng lực, không phải xóa hình khỏi nguồn/expected evidence. Câu text-only độc lập có thể được hỗ trợ; câu cần biểu đồ/đơn vị/hình còn thiếu phải trả phần có nguồn hoặc nêu chưa đủ bằng chứng. Không gắn `ready` cho toàn PDF chỉ vì trích được chữ. Phạm vi này **đang chờ người dùng xác nhận**, chưa là lựa chọn nguồn cụ thể hoặc quyền đưa PDF vào sản phẩm.

## 2. Risk/decision register

Mức cao = có thể dẫn đến lộ dữ liệu, khẳng định sai hoặc đánh giá sai nếu bỏ qua; không có nghĩa đã quan sát lỗi sản phẩm đang chạy. Owner là vai trò cần chịu trách nhiệm, chưa có người được bổ nhiệm.

| ID / mức | Căn cứ và nguy cơ | Hướng xử lý / owner | Mốc phải giải quyết |
|---|---|---|---|
| DR-01 / cao | Readiness §2–4: đủ text không chứng minh đủ chart, glyph, units hoặc row continuation. Text-first có thể vô tình trở thành bỏ mọi visual khỏi mẫu số | Giữ required groups và dependencies theo câu hỏi; báo coverage/pending modality riêng. Người dùng xác nhận scope; AI eval xác định reference | Scope trước đóng packet; sufficiency phải kiểm trước claim liên quan |
| DR-02 / cao | Readiness §2,5: PDF pilot vẫn quarantine. Đọc local không cấp quyền serving; cũng không xác nhận inspector đã có sandbox | Tách local inspection, model processing và user serving theo authority hiện hành. Backend/data steward review exact source/version/purpose; không external fallback | Trước mỗi loại sử dụng cần quyền tương ứng; không chặn chuẩn bị tài liệu hoặc fixture tự tạo |
| DR-03 / cao | Scorer spec §2 và `gate_rate` trong [toy scorer](../../ai-core/experiments/evaluation-scoring-v0.1/scoring.py): chỉ AND các boolean được đưa vào, không kiểm rubric có đủ gates | Future scorer phải kiểm case ID, rubric revision, required/applicable gates, lý do N/A và completeness trước phép tính. AI eval owner; không dùng helper trực tiếp làm GAP chính thức | Trước run dùng GAP để quyết định chất lượng |
| DR-04 / cao | Scorer spec §1,5: silver/exposed dev và self-review chưa là human gold; oracle regions không đo auto-detection | Giữ nhãn/rights/split độc lập; reviewer nội dung adjudicate claim, dependency, transcript; evaluator pin matching trước run. Khi chưa có giáo viên chỉ công bố diagnostic đúng giới hạn | Trước semantic KPI chính thức hoặc chọn ngưỡng theo human calibration; không buộc hoàn tất trước mọi design draft |
| DR-05 / cao | Protocol §3–4: giữ ảnh khác đọc đúng ảnh; detect mất context khác preserve được context; oracle boxes làm điểm detector cao giả | Báo preservation và safe handling riêng; detector dùng full input, oracle-region có nhãn diagnostic. AI ingestion/eval owner | Trước parser/OCR comparison và báo downstream quality |
| DR-06 / cao | Readiness §6: renderer exit 0 nhưng có font warnings; chưa đối chứng glyph-critical regions | Kiểm fidelity vùng liên quan bằng tham chiếu phù hợp/đối chứng renderer trong task được giao; giữ uncertain trước đó. Không tự chữa dấu bằng suy luận. Ingestion reviewer | Trước dùng transcript/formula/chart liên quan làm reference hoặc kết luận ký hiệu |
| DR-07 / trung bình | Scorer spec §4: A-01 trộn capability với clarify/refuse; Academic cần clarify có thể bị chấm sai routing | Đề xuất tách capability, response behavior và reason; future taxonomy review + version/migration cho labels, không sửa đè 12 fixtures cũ. AI eval owner | Trước router evaluation/P7; manual Academic slice không cần triển khai router để vượt điểm này |
| DR-08 / cao | Scorer spec §3, protocol §4: BGE tokenizer/budget lịch sử không là generator context; chưa chọn provider, output reserve hoặc image accounting | Packet ghi budget dimensions và các quyết định còn mở; chọn generator/tokenizer chính xác, full payload accounting, hardware/cost ceiling trong task riêng trước run. Người dùng chốt giới hạn tài nguyên; AI owner đo | Trước model run thật hoặc đóng cấu hình triển khai phụ thuộc model; không cần API trả phí cho review này |
| DR-09 / cao | Handoff WP-03/WP-02: runtime security, citation recheck và integration RC chưa chạy. Synthetic pass dễ bị dùng như enforcement | WP-04 ánh xạ yêu cầu tới owner và test dự kiến; sau Astra review + GO mới implement/test adapters. Tests thực chưa chạy phải NOT RUN; không bắt chúng PASS khi chưa cho viết runtime. Backend + AI + reviewer | Thiết kế test trước code; enforcement tests trước nối dữ liệu thật/serving |
| DR-10 / trung bình | [Reconciliation record](../harness/WP02-handoff-reconciliation.md): đổi state làm frozen-state verify BLOCKED; transaction trước dùng audit riêng | Giữ kết quả BLOCKED và audit như record, không gọi toàn bộ là verify PASS. Maintenance transition cần task riêng nếu được giao. Lượt này không đổi state/plan hoặc rebaseline. Harness maintainer | Trước lần chuyển control tiếp theo; không thay bằng sửa checker/baseline ngầm |

Ví dụ DR-03 (suy từ đọc code, **không phải regression mới đã chạy**): truyền chỉ một gate `claims=true` vẫn có thể cho tỷ lệ 1/1. Kết quả đó chỉ nghĩa toàn bộ boolean đã cung cấp đều true; không chứng minh citation, mode, policy và evidence được chấm đầy đủ. Đây là giới hạn đã được docstring nói rõ, không báo thành một exploit sản phẩm. Sửa đúng là bổ sung validation/rubric ở task scorer tương lai, không đổi công thức AND hoặc yêu cầu mọi gate N/A phải true.

## 3. Các case phải đi cùng review tiếp theo

Các rows sau là **acceptance specifications, NOT RUN**, không cộng thành executable tests hoặc mẫu độc lập mới. Tái sử dụng SP/MM-P/ARCH-C/RC hiện có khi phù hợp, tránh nhân bản score.

| Case | Kết quả cần phân biệt |
|---|---|
| Text độc lập và câu cần hình trong cùng PDF | Cho phép phần đủ evidence theo quyền; câu cần hình vẫn missing/pending, không toàn file pass hoặc toàn file fail |
| So sánh A/B đủ context; mất B sau packing; B bị deny | Đủ thì so sánh; mất thì repair trong quyền hoặc partial; deny thì không hydrate/lộ existence. Không blanket refusal cho mọi câu so sánh |
| Bảng có ô trống, dấu hỏi, 0 và row kéo sang trang khác | Giữ khác biệt, đúng column/header/units và hai locators; không tự điền/ghép nhầm bảng |
| Hình còn nguyên nhưng caption/model reading sai | Visual availability có thể đạt, semantic claim không đạt; không lấy presence thay correctness |
| Source representation mất một dấu nhưng detector báo uncertain | Extraction preservation fail; safe handling có thể đạt nếu không khẳng định phần sai |
| Thiếu gate citation so với rubric; gate thật sự N/A | Thiếu gate phải invalid/incomplete trước aggregate; N/A chỉ theo applicability đã chốt, không tự bỏ sau nhìn kết quả |
| Timeout hệ thống; telemetry evaluator bị mất; chưa có nhãn | Lần lượt failure trong eligible denominator; invalid run; pending review. Không cùng ghi là điểm 0 hoặc bỏ mẫu |
| Lookup/cache có dữ liệu nhưng quyền đã revoke | Scope hiện tại chi phối trả lời/mở nguồn; không dùng cached text hoặc history làm đường vòng quyền |

## 4. Đầu vào cho WP-04 và điều kiện chuyển bước

Đây là danh sách đầu vào, **chưa phải workflow/state machine triển khai được**.

| Đầu vào | Tài liệu gốc | Sẵn có / còn thiếu |
|---|---|---|
| Scope và component ownership | [Brief](../00-project-brief.md), ARCH-02, AGENTS | Direction đã chọn; text-first/visual-limited cần xác nhận |
| Readiness và lineage/context preservation | Readiness 09, [content-unit contract](../architecture/07-content-unit-index-contract-v0.1.md), protocol 33 | Draft có; parser/scorer/matching và fidelity validation chưa hoàn thành |
| Authority, upload và revoke | [Authorization contract](../../contracts/authorization-context.md), [secure upload](../governance/05-secure-upload-quarantine-deduplication-v0.1.md) | Draft inputs, không xác nhận runtime enforcement hoặc quyền dùng nguồn |
| Metrics và acceptance cases | Scorer spec 32, [review clarifications](29-review-regression-and-metric-clarifications-v0.1.md), protocol 33 | Có definitions/gaps; semantic scoring, human calibration và integration còn mở |
| Implementation review requirements | [Master plan](../roadmap/03-master-plan-v0.2.md), WP-04/ASTRA-01 | Cần packet về boundary/authority, failures/retry/cancel, provenance, budgets, telemetry, tests và dependencies; chưa soạn implementation-grade ở lượt này |

Trình tự tiếp tục có giới hạn:

1. Người dùng xác nhận scope đề xuất hoặc yêu cầu vision là năng lực bắt buộc ngay lát cắt đầu. Chọn vision sẽ cần kế hoạch source/rights/reference/budget tương ứng; không chỉ thêm một OCR tool.
2. Reconcile work-package control rõ ràng theo quy tắc harness khi được giao chuẩn bị WP-04; không sửa state chỉ để một card mới pass. Đem các gap trên vào packet dưới dạng quyết định pending và điều kiện không được vượt.
3. Khi tới implementation-grade workflow, báo `Đã tới ASTRA-01: cần review AI Core workflow` và chuẩn bị packet theo master plan. Chưa code sản phẩm cho tới Astra review và explicit user GO.

Chưa có giáo viên không buộc dừng mọi thiết kế. Có thể chuẩn bị packet và, sau đúng GO, kiểm boundary với fake/in-memory adapters cùng nguồn synthetic có quyền rõ. Nhưng không được gọi chúng là gold hoặc thay thế review nội dung/quyền trước dùng học liệu thật. Quyết định scope không đồng thời là source approval, chọn model trả phí hoặc product GO.
