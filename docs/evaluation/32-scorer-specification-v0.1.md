# WP-03 scorer specification v0.1

2026-09-06. Draft chuẩn hóa cho future runs; synthetic arithmetic implementation giới hạn ở experiment riêng. Không thay thresholds, current labels hoặc historical scores. Authority definitions: [metric contract v0.2](08-metric-contract-v0.2.md), [measurement map](17-measurement-architecture-v0.1.md), [clarification v0.1.1](29-review-regression-and-metric-clarifications-v0.1.md). Khi có mâu thuẫn với draft cũ, clarification mới có ưu tiên; vấn đề chưa quyết định giữ pending.

## 1. Common record và thiếu dữ liệu

Mọi score record cần metric ID/definition revision, source+case+policy+scorer snapshots, stage, unit, label authority, split/slice, selected/eligible/excluded/pending IDs, numerator/denominator hoặc distribution, direction, threshold authority, status, timestamp và owner. Log giới hạn truy cập, không raw private prompts trong docs public. Expected outputs nằm ngoài input model.

- `measured`: có observation hợp lệ và denominator > 0; công bố rõ synthetic/silver/human, không chỉ một số.
- `not_applicable`: universe hợp lệ nhưng denominator = 0; value null (N/A), không 1.0.
- `not_measured`: metric chưa chạy, value null; không giả numerator=0 như observed fail.
- `pending_review`: thiếu nhãn/oracle/rights cần thiết, value null; có số case pending.
- `invalid_run`: thiếu telemetry, duplicate/malformed IDs hoặc đánh giá không thể tái lập; không xuất selective aggregate. Lỗi hệ thống được đánh giá khác lỗi evaluator: timeout hệ thống trên case eligible là fail/zero hits, vẫn ở denominator.

Danh sách exclusion và các tiêu chí applicability chốt trước run. Unsupported visual phải xuất hiện trong intake coverage và missing-required evidence, không được bỏ để đẹp điểm. Review uncertainty không thành agreement/no-conflict. Tỷ lệ cùng giá trị nhưng khác unit/stage không được cộng/trung bình chung.

## 2. Core score contracts

Các rows dùng common rules trên cho version/exclusions/N/A. `expected` là tập nhãn độc lập đã chốt, không lấy predictions làm mẫu số. Source family là đơn vị phân cụm khi so sánh, không phải mọi group/cặp từ độc lập.

| IDs / stage | Công thức, denominator | Eligibility / owner / implementation |
|---|---|---|
| R-01a, R-01b / retrieval | Group hit nếu ANY alternative có ALL locators; macro = mean(hit_q/required_q); micro = sum(hit_q)/sum(required_q) | Nonempty qrels ở snapshot đúng; AI eval. Toy AND/OR scorer có, không tự map source spans |
| R-02, K-02 | Queries có đủ mọi required group / queries có qrels | Pre-pack hoặc exact post-pack input ghi riêng; toy scorer có |
| K-01 | R-01a/b trên evidence thật trong serialized model input | Không dùng retrieved-but-omitted IDs; actual payload projection còn cần integration |
| K-03 | Required groups hit trước nhưng mất sau / required groups hit trước | So cùng query/group ID; không lấy net count khi nhóm khác được bù; toy scorer có |
| CI-02a | Retained anchors có đủ declared required closure / retained anchors | Báo attempted/retained/omitted; graph declaration chưa là truth; bounded repair tests có |
| CI-02b, C-04 | Reference required dependencies được giữ / reference dependencies của selected anchors | Omitted anchor/undeclared edge vẫn có denominator; visual availability không xóa requirement; full resolver scorer pending |
| G-01/G-02 GAP | Eligible Academic Q pass tất cả applicable claim/evidence/citation/mode/policy gates / toàn Q đã chốt | U/S/security riêng; partial Q phải nêu giới hạn; no output fail. Boolean conjunction toy có, semantic adjudication pending |
| G-03/G-04/G-05 | Correct required claims / required; incorrect issued / issued; unsupported issued / issued | Claim segmentation/matching phải được review; no issued claims không cứu G-03/GAP. Scorer semantic pending |
| G-09/G-10/G-11, S-04 | Correct abstentions/U; false refusals/eligible Q hoặc benign S; correct partial/partial Q | Báo refusal riêng timeout/no-hit; toy false-refusal denominator có; semantic labels pending |
| V-01/V-02/V-04/V-05 | Supported issued links/issued links; supported source-needing issued claims/all such claims; cited required claims/required claims; unhandled contradictory links/issued links | V-02 không thay V-04 nếu model bỏ hẳn claim; multi-evidence AND; human matching pending |
| V-03a/V-03b/V-06 | Exact locators at delivery/issued citations; current auth decisions đúng/view attempts; successful exact opens/authorized attempts | Revoke sau delivery không làm locator cũ sai; false allow/deny riêng; Backend integration NOT RUN |
| P-03 OCR | CER = character Levenshtein/ref characters; WER = token Levenshtein/ref tokens | Reviewed transcription, Unicode NFC, giữ dấu/case/số/ký hiệu; WER whitespace-tokenized không gọi Vietnamese word segmentation. Toy distance có |
| P-04/P-05 | Correct ordered annotated pairs/all annotated comparable pairs; matched relations/predicted (P) và matched/reference (R) | Order partial được phép, không ép arbitrary total order; matching rule/version trước run; no predictions với reference >0: recall 0, precision N/A; full scorer pending |
| P-07/K-08 | Available required visual assets/annotated required visuals; visuals present pre nhưng absent post/eligible pre visuals | Crop/source/version và model modality đều cần xác nhận; OCR text không thay visual preservation |
| E-01 | Cases đủ nhãn theo metric/selected cases | Tách label readiness và rights readiness; không có selected cases: N/A |
| E-02..06 | Human/judge confusion matrix, kappa, false-pass/critical human fails, repeated-score variance/flips, claim segmentation agreement | Dual-reviewed labels, pinned judge/protocol; NOT RUN, không gọi self-review là human agreement |

CER/WER có thể >1 do insertions; không clamp như tỷ lệ hit. Reference rỗng: CER/WER N/A nhưng vẫn báo insertion/edit count và empty-reference samples. Empty OCR trên reference không rỗng là deletion errors, không bỏ sample. CER aggregate dùng sum edits/sum ref length; report macro riêng nếu thêm. Bbox IoU/TEDS/math-equivalence chỉ chấm khi có reviewed region/grid/semantic matching; exact string không chứng minh công thức tương đương.

## 3. Các family còn lại: giữ definition và nêu rõ chưa có scorer

| Family | Definition source / unit | Disposition cho run mới |
|---|---|---|
| D-01/02; P-01/02/06; C-01/02/03/05/06/07 | Measurement map §§3.1–3.2; source/object/atom/group/expansion/token | Pin expected universe; fidelity/false expansion labels pending. Size distributions không là quality score |
| I-01..03; R-03..10 | Map §3.3; index projection, filter actions, relevance-ranked query, paired rank/resource probes | R-03 ranking precision definition cần chọn explicit metric; R-04 graded gain/log-discount phải pin; R-05 chỉ single-hit; numerical tolerance chưa chốt |
| K-04..07; G-06..08 | Map §§3.4–3.5; capacity/noise/claim/reference | Tokenizer phải của generator, gồm wrappers/history/tools/images/output reserve; BGE budget cũ không thay. RAGAS scorer/version chưa chọn |
| CU-01..05; IX-01..10 (IX-07a/b); CR-01..03; CI-01 | Clarification §§3–4; lineage/atom/projection/claim-set/unit/operation | Deterministic structural hashes khác vector tolerance; preserve conflict sides; không tạo metric trùng để cộng incident |
| AUTH-01..14; UPL-01..12; S-01..03 | Governance security/upload registries; scoped action/checkpoint/case | Expected policy không observed enforcement. Ghi false allow/deny, attempts và unique incident IDs; runtime NOT RUN |
| A-04..09; L-01..04 | Map §3.7; tool/goal/learning cases | Không yêu cầu exact call order nếu nhiều thứ tự hợp lệ; annotate accepted outcomes; chưa chạy agents/tutoring |
| O-01..04 | Map §3.8; all requests/hits | End-to-end/per-stage distributions với N; ghi mọi retry/routing/check cost, failures và missing telemetry. Chưa SLA hoặc pricing version |
| Product B-01..03 | Map §3.8; user-study tasks/participants | NOT RUN; không suy learning gain từ retrieval hoặc harness. Không lẫn HARNESS-B probes |
| H-01..07 | Harness README §6; development-model runs | Ngoài academic scorecard; mechanical tests không đo model success |

Các family trên đã có inventory/mapping, **chưa đồng nghĩa tất cả scorer đã implement hoặc calibrated**. Nếu definition còn tự do (matching, ranking precision, threshold), run tương ứng phải pending, không lấy default SDK làm quyết định.

## 4. ARCH-02 routing clarification (draft, không freeze API)

A-01 draft cũ trộn Academic/Learning/Hub với clarify/refuse. Tách trục nhãn để đo: (a) task capability/intent, (b) response behavior, (c) reason như no evidence/policy/operational. Một câu Academic có thể cần clarify; không gán chúng thành hai class loại trừ nhau. Không sửa 12 route fixtures lịch sử trong lượt này.

- Single-label capability slice đã review: macro-F1 theo taxonomy đã pin, báo support/confusion. Với absent class (không truth lẫn prediction) báo N/A/excluded theo policy trước run; không cộng F1=1.
- Mixed intent: A-03 = satisfied required subgoals / required subgoals, dùng cả workflow đơn; không cần multi-agent mới đo được. Accepted route sets/partial orders nếu có phải annotated.
- `A-01/false_out_of_scope` diagnostic slice = in-scope cases wrongly labelled out-of-scope / all labelled in-scope cases. No-hit/timeouts không tự là out-of-scope. Chưa cấp ID registry chính thức mới.
- A-02 critical misroute: critical cases đi sai boundary / all labelled critical cases; giữ unauthorized action incidents riêng. Confidence không là PDP.
- ARCH-C01..13 là exposed dev design cases, không tự thành executable fixtures/gold; B-11..13 kiểm model phát triển repo, không gộp với router sản phẩm.

## 5. Calibration, so sánh và exit

Pin SDK/scorer/model/prompt/rubric khi thật sự chọn run. Với judge, chọn calibration độc lập theo source family và lỗi, gồm positive controls/unsupported/partial/citation errors; human labels và resolution trước threshold. Báo false-pass trên human critical failures, disagreement và repeatability; không average để bù security. Task-specific evals và human calibration phù hợp hướng dẫn [OpenAI evaluation best practices](https://developers.openai.com/api/docs/guides/evaluation-best-practices), đọc 2026-09-06; nguồn không quyết threshold dự án.

Paired runs dùng cùng inputs/scope/evidence and budget, đổi một yếu tố; mọi retry/check/router cost đều tính. Report counts và uncertainty có giả định rõ: Wilson chỉ mô tả tỷ lệ trong set, không giả các synthetic derivatives độc lập; bootstrap theo family khi có đủ clusters. Không tuyên bố tổng quát từ 10 silver QA.

Technical exit của lượt: registry pins verified, formulas có counterexamples, gaps gắn owner/disposition, đủ chuyển sang WP-02 **readiness documentation**. M0 approval/calibration, official KPI, broader PDF use và all runtime tests vẫn pending. Experiment hỗ trợ số học không đọc corpus hoặc quyết định quyền, và không là phần AI Core runtime.
