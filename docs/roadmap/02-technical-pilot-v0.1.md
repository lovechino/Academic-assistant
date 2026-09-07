# Pilot kỹ thuật 01: hỏi kiến thức và kiểm chứng nguồn

> Status note 2026-09-05: artifact này giữ scope của vertical slice. Phase status và thứ tự triển khai hiện hành nằm ở [Master Plan v0.2](03-master-plan-v0.2.md); chưa được hiểu là authorization cho product code.

Ngày: 2026-09-04. Trạng thái: **bản thiết kế đang làm việc**, chưa được stakeholder/chuyên gia phê duyệt, chưa triển khai hay chạy benchmark.

## 1. Problem trước, không bắt đầu bằng ba agents

Giả thuyết vấn đề: người học mất công tìm đoạn giải thích trong nhiều tài liệu và khó kiểm tra câu trả lời có thực sự dựa trên nguồn hay không. Chưa có phỏng vấn hoặc số đo thời gian của sinh viên; đây là giả thuyết sản phẩm, không phải kết quả user research.

Luồng đầu tiên: **chọn phạm vi môn -> hỏi một khái niệm/so sánh -> nhận giải thích có nguồn -> mở đúng đoạn nguồn để tự kiểm chứng**.

Ví dụ truy vết từ case đã có: so sánh cách lấy phần tử của stack và queue. Luồng phải tìm đủ evidence của cả hai, giữ chúng qua context packing, gắn citation đúng claim và mở lại đúng phiên bản. Chỉ trả lời nghe hợp lý là chưa đủ.

Mục đích vòng này là chứng minh một luồng có thể đo và truy nguyên lỗi xuyên AI core/Backend/Frontend. Chưa triển khai full multi-agent, lộ trình học cá nhân, upload hàng loạt, auto-publish, dashboard thống kê hoặc tối ưu semantic cache.

## 2. Tách hai mức pilot khi chưa có giảng viên

| Mức | Có thể chuẩn bị/làm gì? | Không được kết luận |
|---|---|---|
| Technical research pilot | Định nghĩa hợp đồng; kiểm tra provenance; tabletop workflow; về sau thử retrieval/answer trên nguồn có quyền nghiên cứu | Chưa chứng minh phù hợp học phần, hiệu quả học tập hoặc đạt KPI nghiệm thu |
| Academic acceptance pilot | Corpus authoritative, reviewer môn học, rubric đã hiệu chỉnh và frozen test | Chưa đủ điều kiện bắt đầu vì chưa có content owner/reviewer |

Không đổi nhãn `research_reference` thành `published` chỉ để demo. Các actor/permission fixtures về sau phải là synthetic và được ghi rõ; không giả mạo giáo viên phê duyệt. Người không phải giáo viên có thể review link/layout/transcription nếu đủ khả năng, nhưng review học thuật cần người có chuyên môn phù hợp và được chỉ định.

## 3. Phạm vi dữ liệu và giả định làm việc

Tạm ưu tiên CTDL & Giải thuật cho luồng kỹ thuật, chưa thay quyết định chọn 2-3 môn của MVP:

- Snapshot: `voer-2026-09-04-r1`, course `cau-truc-du-lieu-va-giai-thuat`.
- 16 module, 69/69 ảnh tải được theo manifest; việc tải được không chứng minh hiểu được hình hay chất lượng nội dung đã duyệt.
- Candidate retrieval corpus dự kiến là **toàn bộ 16 module**, không chỉ các module chứa đáp án. Không dùng `material_id` trong nhãn đáp án làm filter đầu vào.
- Dùng theo [source notice hiện có](../../data/raw/voer/SOURCE-NOTICE.md): research reference, không training/fine-tuning; chưa có quyền gọi dịch vụ model ngoài được suy ra từ tài liệu này.
- 17 PDF trường học vẫn ở quarantine. 13 trang audit, 8 visual QA và 12 structural probes là nhánh diagnostic riêng, không nhập vào corpus trả lời của luồng này.
- Chưa thu thập thêm nguồn, không thay snapshot hay nhãn cũ trong vòng lập kế hoạch.

## 4. Bộ case đầu tiên: dùng lại, không sinh thêm hàng loạt

[Profile tham chiếu](../../ai-core/evaluation/profiles/technical-pilot-v0.1.json) chỉ chọn ID từ pack `voer-silver-v0.1`, không sao chép đáp án hoặc đổi nhãn thành gold.

| Nhóm | IDs có sẵn | Cách dùng |
|---|---|---|
| Answerable Academic | `VOER-ACA-001` đến `VOER-ACA-010` | 10 case: 4 lookup, 2 explanation, 2 comparison, 2 multi-hop |
| Không đủ evidence | `VOER-ACA-012` | 1 case kiểm tra không bịa; cần review lại nhãn unanswerable trên corpus giới hạn |
| Bảo vệ secrets | `VOER-SAF-001` | Không tiết lộ hoặc gọi downstream để đáp ứng yêu cầu đó |
| Bài chấm điểm | `VOER-SAF-004` | Không cung cấp bài nộp hoàn chỉnh; cho phép hint theo policy dự thảo |
| Tự khai vai trò | `VOER-SAF-007` | Không cấp quyền hoặc retrieve dựa vào lời tự khai |

Tổng **14 case tham chiếu**, tất cả vẫn `silver_draft/dev/human_reviewed=false`. Ba case safety chỉ là thử hành vi, **không thay RBAC integration tests** trên private fixtures.

`VOER-ACA-011` tạm ngoài scorecard đầu tiên để review riêng việc câu hỏi cây biểu thức cần ảnh hay chỉ text; không suy ra `requires_visual` chỉ từ tag `table_figure_formula`. Giữ nguyên case đó trong pack gốc và báo việc loại khỏi profile trước khi chạy.

Ví dụ ambiguity cần sửa ở version nhãn kế tiếp: `VOER-ACA-008` mô tả mảng theo tài liệu; reviewer phải kiểm tra cách diễn đạt phạm vi, tránh nâng kết luận của ví dụ thành khẳng định cho mọi loại cấu trúc mảng. Không sửa ngầm reference answer hiện tại.

## 5. Metric và điều kiện để coi vòng thử có ích

Định nghĩa chi tiết tại [metric contract v0.2](../evaluation/08-metric-contract-v0.2.md):

- Grounded Answer Pass Rate: mẫu số đầu tiên là 10 case answerable, không gồm case abstention/safety. Mục tiêu kỹ thuật tham khảo >=80%, tức >=8/10; **không phải nghiệm thu**.
- Retrieval: Group Recall@5 >=90%, @10 >=95%; All-evidence Success@10 >=85% trên subset có qrels đủ điều kiện. Đây là mục tiêu thiết kế kế thừa protocol, chưa có kết quả.
- Tách điểm retrieval trước/sau packing và oracle/retrieved answer. Không dùng điểm tổng để che lỗi làm mất đơn vị/đoạn evidence.
- Case bất khả trả lời, safety và các tình huống quyền phải báo từng case. 0 lỗi quan sát trên tập nhỏ không chứng minh hệ thống không có lỗi.
- Thời gian/chi phí: trước hết ghi theo stage và success/failure; chưa đặt SLA hay ngân sách tiền tùy ý khi chưa chốt runtime. Không gọi model trả phí trong vòng này.

Đã có [mapping silver đầu tiên](../evaluation/09-evidence-mapping-voer-dsa.md): 30 required claims -> 25 evidence groups -> 22 source locators cho 10 answerable case. Còn review chuyên môn và controls; không tự coi mỗi `material_id` là một evidence group. Một module có thể chứa nhiều ý phải tìm đủ.

## 6. Phần việc của ba component

| Component | Đầu ra cần thiết của luồng pilot | Không sở hữu |
|---|---|---|
| AI core | Kết quả retrieval/packing có provenance; answer/hint/abstention có claim-citation mapping; trạng thái thiếu evidence | Auth, quyền approve, API công khai, UI |
| Backend | Trusted scope; kiểm tra admission nguồn; gọi use case; validate public response; kiểm tra lại quyền mở citation; audit/failure semantics | Prompt logic, chunking hoặc quyết định đáp án học thuật |
| Frontend | Course context rõ; hiển thị câu trả lời/trạng thái; mở citation đúng locator; thông báo thiếu evidence/thu hồi/lỗi | Tự quyết định quyền, truy cập vector DB hoặc giữ provider key |

Chưa cần smart router: người dùng chọn Academic mode. Safety/policy vẫn áp dụng; case graded work có thể trả hint giới hạn, không bắt buộc tạo Learning agent đầy đủ để thử policy. Learning diagnosis/path planning và Knowledge Hub quản trị đầy đủ vẫn ở các bước sau.

## 7. Thứ tự hành động và điểm dừng

| Bước | Artifact/gate | Hiện trạng |
|---|---|---|
| P01 Problem/scope | Luồng ở tài liệu này, non-goals và giả định rõ | Đã có bản nháp |
| P02 Metric contract | Mẫu số, pass/fail và cách phân loại lỗi thống nhất | Đã có bản nháp v0.2 |
| P03 Workflow | Happy path và lỗi xuyên ba component | Đã có [đặc tả](../workflows/01-grounded-qa-pilot.md) |
| P04 Evidence mapping | Review 14 case, qrels/locators cho 10 QA, log nhãn chưa chắc | Mapping 10 QA và issue log đã có ở mức assistant/silver; controls/expert review còn mở |
| P05 Tabletop review | Đi qua từng bước với nguồn cho phép và fixtures synthetic, không gọi model | Đã chạy [11 tình huống synthetic](../workflows/02-tabletop-simulation-v0.1.md), 9 guard mutations; chờ người dùng review quyết định, chưa đủ mọi WF-N |
| P06 Baseline kỹ thuật | Quyền/source scope + mapping + config/budget cho phép; chạy retrieval-only trước | Chưa chạy, chưa cài stack |
| P07 Academic acceptance | Content owner, reviewer, policy và frozen holdout | Chưa đủ điều kiện |

N1/N2/N3 của roadmap gốc **không được đánh dấu đạt** vì có thêm tài liệu. Có thể tiếp tục phần chuẩn bị kỹ thuật độc lập nhưng không bỏ qua gate sử dụng nguồn/nhãn/chuyên môn.

## 8. Các quyết định còn mở

- Người dùng có muốn đổi môn kỹ thuật ưu tiên từ CTDL & Giải thuật không? Hiện chỉ là giả định có thể đảo ngược.
- Ai có thể review nội dung và những loại bài chấm điểm nào thuộc policy chính thức?
- Có triển khai ở môi trường local-only hay cho phép dịch vụ ngoài? Ngân sách/latency chấp nhận được?
- Course/term/cohort thực và điều kiện download bản gốc là gì?

Không cần chờ các câu trả lời này để hoàn thiện evidence mapping trên giấy. Chúng phải được chốt trước những bước thực thi bị ảnh hưởng; không tự suy ra quyền/ngân sách từ yêu cầu “tiếp tục”.

## 9. Kiểm tra artifact của vòng lập kế hoạch

Đã kiểm tra ngày 2026-09-04: 180/180 checks của structural verifier đạt; 51/51 checks về pack/snapshot/ID/phân nhóm của profile đạt. Không có case trùng; case deferred không lọt vào danh sách chấm. Toàn bộ 240 file trong `data/` giữ nguyên checksum trước/sau.

Các checks này chỉ xác nhận đường dẫn và tính nhất quán của artifact; **không xác nhận đáp án đúng, qrels đã đủ, workflow đã chạy hoặc agents đạt điểm**. Chưa chạy parser/model/retrieval và chưa sửa code sản phẩm trong vòng này.

Cập nhật P04: [báo cáo evidence mapping](../evaluation/09-evidence-mapping-voer-dsa.md) có validation riêng và 12 tình huống coverage toy. Toy locator checks không thay tabletop quyền/end-to-end của P05.

Cập nhật P05: đã chạy state machine offline trên hai tài liệu/actor synthetic, không dùng quyền giả để publish nguồn VOER/PDF. Baseline có 132 bước; 11/11 khớp expected fixture không đồng nghĩa 11 câu trả lời đủ. Quy tắc partial/retry, buffer, cache và version chưa được người dùng chốt; runtime/concurrency/RBAC thật chưa được kiểm thử.

Cập nhật chuẩn bị P06: [evidence pipeline contract](../architecture/05-evidence-pipeline-contract.md) và [packet boundary](../../contracts/evidence-packet.md) đã có bản nháp cùng năm ví dụ chọn bằng tay từ nguồn thật. Chưa đóng runtime schema, chưa xây index hoặc chạy parser/chunker/model. User đã xác nhận cần cả ba tình huống context đủ/khôi phục/không khôi phục; không suy ra số retry hoặc mọi D-01..D-06 đã được duyệt.

Cập nhật tiếp nối chuẩn bị P06: đã [parse HTML thật của toàn bộ 16 module CTDL](../data/08-voer-dsa-structural-representation.md), giữ 120 heading, 9 bảng / 188 ô, 69 ảnh tham chiếu và 247 sub/sup nodes. 22/22 locator silver truy về đúng HTML; source integrity audit đạt, chưa review ngữ nghĩa. Tiếp theo xử lý code phân tán, công thức và context bảng/hình trước chunking. P06 retrieval baseline vẫn chưa chạy; P07 và các gate học thuật không đổi.

Cập nhật research chunking: [dependency design](../architecture/06-chunking-research-and-dependency-design.md) và [protocol context preservation](../evaluation/10-context-preservation-protocol.md) đã đối chiếu nguồn chính thức với mẫu Stack/Queue/Mảng. Có một formula bị code heuristic gắn cờ và một dấu hiệu không nhất quán trong câu dẫn Queue. Bước kế tiếp: annotation 30 probe dự kiến và enrichment có version, rồi mới chunking-only. Chưa sửa nhãn/corpus, chưa chạy retrieval/model hoặc nâng readiness học thuật.

Cập nhật R0: [annotation/source review](../evaluation/11-context-review-round0.md) đã tạo 30 probe / 31 biến thể silver, 29 nhóm và 7 dependency candidates. Đã xem 4 ảnh, giữ nguyên các source issues. Chưa có rich serializer/tokenizer/chunking run; bước kế tiếp hoàn thiện serializer trước boundary experiment. P06 retrieval và P07 chưa thay đổi.

Cập nhật R0 serializer: [bảo toàn nguồn đã chạy](../evaluation/12-source-serialization-round0.md) cho 29 nhóm / 188 roots, 13.062 checks, 12 synthetic cases và 14 mutation detections. Có source alignment và trace từng bước; chưa tokenizer/chunking/index/model. Tiếp theo chuẩn bị R1 boundary-only với scope/input/tokenizer cố định; P06 retrieval và P07 vẫn chưa đạt.
