# Review repair registry v0.1 — WP-01.1

Ngày: 2026-09-06. Scope: xử lý chín findings từ review; docs/contracts và bounded offline regression. User yêu cầu xử lý findings; không có product GO, academic sign-off hoặc quyền gửi nguồn ra external processor.

## 1. Disposition và bằng chứng

| ID | Finding | Sửa ở đâu / cách sửa | Trạng thái kiểm chứng |
|---|---|---|---|
| F-01 | Legacy projection làm x² và x₂ thành cùng text | Experiment mới dùng R0 typed event tape, source hash/alignment, giữ markup cấu trúc; unsupported layout block | Synthetic behavior pass; chưa chạy lại corpus hoặc embedding |
| F-02 | Anchor còn nhưng dependency bị budget loại; 6/6 chỉ pre-pack | Atomic required closure, optional sau required, post-pack assertion, anchor retention và N/A | Synthetic behavior pass; chưa chứng minh resolver tự tìm đúng context |
| F-03 | Quarantine reviewer/OCR bị cấm chung với serving | Exact inspection actions/principal/purpose/sinks; known-secret vs unknown inspection; UPL/AUTH profile clarification | Specification corrected; runtime NOT RUN |
| F-04 | Representation cần material version trước approval | Quarantine origin = submission/snapshot; immutable promotion binding sang material version | Specification corrected; persistence tests NOT RUN |
| F-05 | Missing conflict record bị coi là no conflict | Assessment state + assessed scope/revisions + known-conflict coverage; exact shortcut không thay conflict check | Specification corrected; adjudication/recall NOT RUN |
| F-06 | Public/share chưa rõ owner tenant và active tenant | Typed resource binding: tenant relation/public/named share; revision-aware scoped cache | Specification corrected; PDP/data-plane tests NOT RUN |
| F-07 | Internal packet bị mô tả như toàn model input | Allowlisted projection + internal item map/trace; exact serialized input hash/accounting | Projection boundary synthetic pass; provider integration NOT RUN |
| F-08 | Macro/micro, temporal citation và rebuild drift chưa rõ | Definitions ở mục 3–4; scorer profile mới, không sửa historical scores | Definition corrected; full WP-03 pack inventory/calibration còn mở |
| F-09 | Activation nhiều surface, unrelated epoch/race chưa rõ | One serving snapshot, guarded CAS, relevant revisions, delivery/revoke ordering | Specification corrected; concurrency/chaos NOT RUN |

Không dùng cột specification corrected như test đã pass. `contracts/content-unit-index.md` v0.1.1 và authorization/evidence clarification là boundary hiện hành. Các roadmap/report R1–R4/E0.* giữ lịch sử; quyết định tương lai theo clarification này.

## 2. Offline repair và giới hạn

[Experiment context-integrity-v0.1](../../ai-core/experiments/context-integrity-v0.1/README.md) có 23 unittest methods (kèm subcases), chạy bằng Python 3.11/std library, không đọc dataset thật hoặc ghi artifact. Kết quả: 23/23 pass ngày 2026-09-06.

Các case phủ sup/sub collision của hàm legacy; dấu/đơn vị/phủ định/case/code newline; entity vs literal tag; simple table header/blank/zero; noncitable structure marker/alignment; unsupported attributes/img/MathML/implicit root; required/transitive dependency; missing/ineligible/scope/version; cycle/hop/unit limits; required bundle quá budget; optional không chiếm chỗ required; omitted anchor không sinh expansion; dedup shared dependency; model-input allowlist/hash; empty denominator. Counterexample của packer R4 cũ vẫn tái hiện để chứng minh regression có ý nghĩa.

Accounting test là codepoint trên toàn serialized payload, legacy probe là whitespace count; KHÔNG phải số token BGE/generator. Phép đo này chỉ kiểm logic budget. Sau khi chọn generator phải đo bằng tokenizer/profile của model đó, bao gồm wrappers/history/tools/images và output reserve.

Dependency graph được truyền vào bằng synthetic fixture để kiểm thuật toán pack; không gọi graph đó là automatic discovery hoặc gold học thuật. `eligible` là offline availability, không phải PDP allow. `answerability=not_assessed`, `serving_authorized=false` luôn giữ. Một packet rỗng không được báo thành success bằng closure-rate 100%.

Source projector nhỏ chỉ hỗ trợ một explicit HTML root không attributes; không có image/MathML/spanning-table support. Chặn cả unit khi ngoài profile. Nó tái sử dụng R0 serializer thay vì tạo parser product hoặc dùng legacy stripping. Không tạo index mới; R2–R4 inputs/vectors/metrics và script lịch sử không bị ghi đè.

## 3. Measurement clarification profile v0.1.1

Common fields bắt buộc trước run: metric ID + definition version, owner, dataset/corpus/config/scorer snapshot, expected unit set, label authority, split, eligibility, exclusions + reason, timestamp stage, numerator, denominator, direction, gate, assessment status. Denominator 0 → null + `not_applicable`; chưa chạy/thiếu labels → null + `not_measured`/`pending_review`, không phải pass. Timeout/missing output trên eligible case tính fail hoặc làm run invalid nếu telemetry hỏng; không xóa case khỏi mẫu số sau run.

| Metric | Numerator / denominator hoặc count | Gate và owner |
|---|---|---|
| CU-01 | Locator mở đúng immutable snapshot/version/region / locators trong predeclared audit | 100%; AI ingestion + Backend viewer; availability/authorization chấm riêng |
| CU-02 | Derived records có lineage hợp lệ cho stage / all audited derived records | 100%; quarantine dùng submission/snapshot, serving thêm promotion/material version; Backend + ingestion |
| CU-03 | Units ghép fragments ngoài một permitted source scope/version | 0 count; packet có nhiều riêng biệt authorized items không là violation; ingestion |
| CU-04 | Critical annotated atoms bị cắt trái rule hoặc mất / critical atoms của input được chọn trước | 0; không loại atom oversized sau khi thấy output; ingestion |
| CU-05 | Annotated representation conflicts được phát hiện và giữ các phía/locator / all annotated conflicts | 100% trên reviewed set; chưa review thì pending, không lấy detector positives làm denominator; ingestion |
| IX-01 | Unauthorized item/content/metadata crossing retrieval boundary | 0 count theo stage, kèm số attempts; Backend enforcement |
| IX-02 | Quarantine item crossing serving boundary hoặc unassigned inspection boundary | 0 count; authorized restricted inspection có positive controls riêng; Backend |
| IX-03 | Orphan/mismatched projection referenced by activated serving snapshot | 0 count trên all activated projections; AI index + Backend publish |
| IX-04 | Protected delivery operation ordered after effective revoke nhưng vẫn phát | 0 count; operation ordered trước revoke báo riêng, không dùng network arrival thay ordering point; Backend |
| IX-05 | Known annotated conflicting claim sets bị collapse mất phía/lineage | 0 count / report evaluated sets; AI retrieval/packing |
| IX-06 | Candidate similarity tự tạo same_as/merge/approval/access without authorized decision | 0 count / report candidate decisions; Backend lifecycle |
| IX-07a | Deterministic structural rebuild differences on same source/profile, keyed by derivation identity | 0 count; so text/fragment lineage/profile/hash, bỏ fresh opaque IDs, timestamps, run IDs khỏi comparison; AI index |
| IX-07b | Vector numeric deltas, rank inversions và overlap trên paired probes | Tolerance/profile TBD trước run; không yêu cầu mọi hardware bitwise giống nhau; không pass khi tolerance chưa freeze; AI evaluation |
| IX-08 | Eligible expected units có đủ required surface projections / predeclared eligible units | 100%; reject/partial/unsupported được báo riêng so toàn intake, không tự giảm expected set sau build; AI index |
| IX-09 | Dependency hydrate operations thiếu exact current binding/version/purpose | 0 count theo edge; explicit authorized cross-version/share target không tự là violation; Backend + AI |
| IX-10 | Cache hydrate/delivery với incompatible active/owner/share/policy/dependency revisions | 0 count / all hit attempts; Backend |
| CR-01 | Reviewed changed claim spans được detected/located đúng / all required changed spans | 100% critical synthetic reviewed subset; annotation phải pin số/đơn vị/toán tử/điều kiện và matching rule; AI eval |
| CR-02 | Expected relevant authorized unresolved sets có đủ các phía sau pack / expected relevant authorized unresolved sets cho case | 100%; set chưa vào top-K vẫn ở denominator; ngoài quyền không lộ existence trong model/public output; AI eval |
| CR-03 | Eligible cases phát disputed claim như fact đã thống nhất | 0 count / report all reviewed unresolved cases; human/reference adjudication, không chỉ keyword checking; AI generation |

`IX-07` giữ vai trò family/alias; run mới phải tách IX-07a/07b. Gate cấu trúc không suy bitwise vector determinism. Activation snapshot consistency là gate riêng, không được dùng numerical tolerance để bỏ version mismatch.

### Retrieval, packing và citation

- `R-01a`: mean theo eligible query của (required groups hit / required groups). `R-01b`: sum groups hit / sum required groups. AND trong locator alternative, OR giữa alternatives. Query qrels rỗng là N/A theo predeclared disposition; missing output của query có qrels là zero hits. Báo cả hai; target lựa chọn cấu hình vẫn provisional tới M0.
- `CI-01 projection fidelity`: preserved reviewed semantic distinctions / reviewed distinctions sau serialization. Source/locator coverage không thay metric này; unsupported phải báo riêng, không đo generation.
- `CI-02a post-pack structural closure`: retained anchors có đủ declared required closure / retained anchors. Báo đồng thời attempted/retained/omitted anchor counts và retention rate để tránh “drop everything” đạt điểm đẹp.
- `CI-02b post-pack reference dependency recall`: required reference dependencies của selected evaluation anchors được giữ trong packet / all required reference dependencies của các anchors đó. Nếu resolver không khai báo edge hoặc pack bỏ cả anchor, không được biến thành N/A. `CI-02a` không thay `CI-02b` hay C-05 false expansion.
- `V-03a locator integrity at delivery`: issued citations có exact source/version/region mapping đúng tại delivery / issued citations. Không có citation → N/A với citation coverage gate riêng.
- `V-03b current viewer authorization`: viewer operations enforce đúng current expected decision / all tested viewer attempts; report false allow/deny riêng. Revoke sau delivery và deny viewer đúng không làm V-03a cũ fail. Artifact mất khi vẫn authorized là viewer availability failure V-06, không tự thành permission denial.

Historical `V-03` vẫn mang definition của scorer cũ. RAGAS/judge chưa chạy hoặc calibration chưa có thì `not_measured`; không dùng thay quyền, lineage, exact serialization hoặc conflict completeness.

## 4. Mapping các metric trùng tầng

| WP-01 family | Registry trước đó | Quan hệ |
|---|---|---|
| CU-01/CU-02 | D-02, P-06, V-03a | Cùng integrity nhưng khác unit/stage; không cộng các tỷ lệ |
| CU-04 / CI-01 | C-01, P-02, P-05 | Boundary vs serialized semantic fidelity vs silent-loss phải báo riêng |
| IX-01/02/09/10 | I-03, S-01, AUTH-02/04/06, UPL-02 | Cùng exposure event có một event ID và nhiều tags; không double-count incident |
| IX-04 | AUTH-05/10 | Stale delivery correctness vs propagation latency; không lấy p95 tốt bù false allow |
| IX-08 | I-01 | Coverage theo immutable expected unit set/surface |
| CI-02a/02b | C-04, C-05, K-01/02/03 | Resolver reachability, packing dependency và QA evidence là các denominator khác nhau |
| CR-02/03 | K-07, V-05, G-02 | Conflict coverage vs answer handling; explicit unknown không là no-conflict |

Full dataset registry gồm split, label authority, licensing/eligibility và reviewed scorer implementation vẫn là WP-03; tài liệu này chỉ sửa measurement defects phát hiện trong review.

## 5. Contract acceptance cases bổ sung — NOT RUN

Các case sau là review specifications, không cộng vào 23 unittest hoặc 102 DT fixtures lịch sử. Owner phải viết behavior/integration tests khi qua product gate.

| ID | Tình huống | Expected outcome | Owner |
|---|---|---|---|
| RC-01 | Assigned reviewer đọc exact quarantine submission | Allow restricted inert preview, no serving access | Backend |
| RC-02 | Student/agent hoặc reviewer khác assignment đọc cùng submission | Deny, không lộ content/existence | Backend |
| RC-03 | Unknown scan có canary, inspector local được cấp đúng quyền | Restricted detection output; quarantine downstream, không external/model/index | Backend + ingestion |
| RC-04 | File đã classified secret, job OCR cũ retry | Deny tại current revision; không kế thừa allow cũ | Backend |
| RC-05 | Parse trước approval, material version chưa có | Valid submission/snapshot lineage; reject serving | Ingestion + Backend |
| RC-06 | Promote representation từ submission được duyệt | New immutable promotion binding; hash/source lineage cũ không đổi | Backend |
| RC-07 | Missing conflict record hoặc top-K chỉ có một phía | Assessment not_assessed/partial; không kết luận source agreement | AI Core |
| RC-08 | Known authorized conflict; exact candidate route short-circuits | Conflict check vẫn chạy; missing required side blocks settled claim | AI Core |
| RC-09 | Conflict target bị deny | Không hydrate; không lộ ID/title/count/existence; safe limitation | Backend + AI |
| RC-10 | Personal user tìm public catalog | Only current approved public snapshot binding | Backend |
| RC-11 | B dùng view-only share từ A | Exact version view allow; search/use-model/download deny | Backend |
| RC-12 | Share expiry/revoke hoặc đổi active tenant | Cache incompatible, subsequent protected operations deny; quyền owner A độc lập | Backend |
| RC-13 | User/model sửa owner tenant/grant selector | Resolve/recheck server-side; no wildcard partition | Backend |
| RC-14 | Internal envelope chứa auth decision/capability/gold sidecar | Model projection không có các fields đó; exact payload hash/profile ghi internal | AI + Backend |
| RC-15 | Citation hợp lệ tại delivery, revoke trước viewer | V-03a giữ integrity cũ; V-03b pass correct deny, không phát bytes mới | Backend/viewer |
| RC-16 | Lexical build mới, dense/graph chưa xong | Serving pointer không activate; query không mix generations | Index + Backend |
| RC-17 | Membership của user không liên quan đổi giữa build | Không rebuild content vô ích; current user checks vẫn enforce | Backend |
| RC-18 | Approval/resource revision/workload revoked giữa verify và CAS | Publish fails atomically; stale worker không reactivate | Backend |
| RC-19 | Revoke commit cạnh tranh với protected delivery | Operation order/fence rõ; no later authorized release, audit đúng ordering point | Backend |
| RC-20 | Rebuild tạo opaque IDs/timestamps mới, content giống | IX-07a compares derivation-keyed content, không false fail do metadata run | AI index |
| RC-21 | Vector backend/precision thay đổi | IX-07b paired probe + declared tolerance, không dùng claim bitwise determinism | AI evaluation |

RC-14 có kiểm tra allowlist cơ bản trong experiment; matrix integration với provider/Backend vẫn NOT RUN. Không biến policy expected decision thành observed implementation result.

## 6. Điểm tiếp tục

Verification ngày 2026-09-06: `py -3.11 -B scripts/verify_structure.py --require-local-data` đạt 554/554 checks, 46 Python files syntax-valid, 17 PDF source hashes đúng, không skip. `git diff --check` pass; runtime AI Core/Backend/Frontend và historical experiment Python/config không có diff. Đây là structure/integrity verification, không phải product test. Không chạy lại historical audit/generator, không ghi lại source/processed/evaluation snapshots.

WP-01.1 hoàn tất bản sửa và bounded regressions, trạng thái corrected draft; còn cần human/workflow review và runtime validation. Tiếp theo hoàn thiện WP-03 inventory/scorers trước vòng model mới, rồi WP-02 multimodal readiness với các representation/inspection semantics đã thống nhất. Sau đó WP-04 packet và ASTRA-01 + explicit user GO mới tới product code. Không freeze threshold, hardware tolerance, generator budget hoặc model winner trong lượt repair này.
