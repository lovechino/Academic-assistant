# Roadmap giai đoạn không viết code

> Status note 2026-09-05: tài liệu này giữ lịch sử N0–N5. Trạng thái và thứ tự hiện hành nằm ở [Master Plan v0.2](03-master-plan-v0.2.md), bao gồm gate ASTRA-01 trước product code.

## Mục tiêu

Hoàn tất các quyết định có ảnh hưởng lớn trước khi chọn framework hoặc triển khai agent.

Luồng làm việc sau khi tách AI core/Backend/Frontend: [technical pilot 01](02-technical-pilot-v0.1.md). Đã có bản nháp problem/metric/workflow, [mapping silver cho 10 QA](../evaluation/09-evidence-mapping-voer-dsa.md) và [kết quả 11 mô phỏng workflow synthetic](../workflows/02-tabletop-simulation-v0.1.md); bước tiếp theo là review các quyết định/nhãn còn mở, chưa code sản phẩm.

## Milestone N0 — Foundation

Trạng thái: hoàn thành bản nháp v0.1.

- Project Charter.
- Evaluation strategy.
- Public dataset catalog.
- Local gold-set specification.

## Milestone N1 — Domain và data inventory

Trạng thái: đã có 3 pilot corpus công khai để nghiên cứu kỹ thuật; chưa có content owner hoặc corpus nội bộ được phê duyệt.

Đầu vào cần có:

- Danh sách 2-3 môn pilot.
- 10-20 tài liệu mẫu mỗi môn.
- Chủ sở hữu và quyền sử dụng từng tài liệu.
- Phiên bản chính thức và tài liệu đã lỗi thời.

Đầu ra:

- Data catalog.
- Metadata dictionary.
- Document lifecycle policy.
- Permission matrix theo role/course/term.
- Danh sách loại tài liệu khó: scan, nhiều cột, bảng, công thức, slide có hình.

Gate N1: mọi tài liệu mẫu có owner, version, scope và trạng thái publish rõ ràng.

Tiến độ ngày 2026-09-04:

- Đã crawl 34 module VOER thuộc Cấu trúc dữ liệu và giải thuật, Cơ sở dữ liệu và Kinh tế học vi mô.
- Đã lưu provenance, giấy phép/content signal, manifest, checksum và các lỗi dữ liệu.
- Corpus được giới hạn ở `research_reference`; chưa qua Gate N1 vì thiếu reviewer nội bộ và xác nhận tính thời sự.
- Đã bổ sung 17 PDF / 236 trang để audit cục bộ, vẫn quarantine do quyền chưa được xác minh. Không tự tính các PDF này vào tập được phép publish.

## Milestone N2 — Policy và annotation guideline

- Định nghĩa graded work và các mức hỗ trợ được phép.
- Viết ví dụ answer/hint/clarify/refuse.
- Chốt rubric Academic và Learning Assistant với giảng viên.
- Chốt taxonomy cho router.
- Viết hướng dẫn gắn gold evidence và citation.

Gate N2: hai annotator chấm thử cùng 10 case và thống nhất cách hiểu rubric.

## Milestone N3 — Seed evaluation pack

Trạng thái: đã có silver draft 60 case trên corpus VOER; chưa có human review và chưa freeze.

- 30 grounded QA cases.
- 20 Learning/integrity cases.
- 30 router cases.
- 12 RBAC cases.
- 10 trang/slide OCR đại diện.

Gate N3: toàn bộ case được review, có corpus snapshot và evidence truy ngược được.

Tiến độ ngày 2026-09-04: 30 Academic, 10 Learning, 12 Router và 8 Safety case đã được tạo ở split `dev`. N3 chưa đạt vì còn thiếu reviewer, 10 Learning case, 18 Router case, 12 RBAC case và OCR set trên PDF/slide.

Bổ sung sau đó: 13 trang visual audit, 8 visual QA silver và 12 structural probes; không phải transcript OCR gold hoặc RBAC integration suite. Profile pilot 01 chỉ tham chiếu 14 case VOER đã có, không tạo thêm 14 nhãn mới.

## Milestone N4 — Experiment design

Trạng thái: đã có thiết kế parser, context-preserving chunking, indexing và controlled experiment. Đã có PDF/slide và chạy diagnostic extraction trên 13 trang; chưa chạy so sánh parser/chunker/retriever cạnh tranh do còn thiếu reviewed annotations, điều kiện dùng nguồn và execution config. Không còn dùng lý do “chưa có PDF” để mô tả trạng thái hiện tại.

Chưa viết sản phẩm; chỉ chốt cách so sánh sau này:

- Baseline keyword search.
- Baseline vector search.
- Hybrid search.
- Hybrid + reranker.
- Generator với oracle context.
- Generator với retrieved context.
- Manual mode selection so với smart router.

Mỗi experiment phải cố định input, corpus snapshot và cấu hình; chỉ thay một biến chính để biết thay đổi nào tạo ra cải thiện.

Experiment matrix hiện gồm parser P0–P2, chunker C0–C8 và retrieval/index stack I0–I5. Candidate mặc định để thử trước là structure-aware child/parent chunking với deterministic context header; semantic chunking, LLM contextualization, late chunking và RAPTOR chỉ là challenger.

## Milestone N5 — Readiness review

Chỉ bắt đầu code khi:

- Phạm vi MVP và non-goals được duyệt.
- Có tài liệu mẫu hợp lệ.
- Permission và integrity policy được chốt.
- Seed evaluation pack chạy được trên giấy/manual.
- Metric, gate và cách báo cáo đã thống nhất.

## Thứ tự tiếp theo hiện tại

1. Review profile CTDL & Giải thuật cho technical research pilot; không thay điều kiện lựa chọn môn nghiệm thu.
2. Review mapping đã có cho 10 answerable case; làm rõ nhãn còn mở của 1 abstention và 3 policy cases. Không nâng mapping assistant thành gold.
3. Review kết quả tabletop đã chạy về packing, citation, revoke và cache; chốt D-01..D-06. Scope thiếu/role spoofing/admission/timeout và kiểm thử integration thật còn chưa chạy.
4. Review [evidence pipeline contract và năm ví dụ nguồn thật](../architecture/05-evidence-pipeline-contract.md). Đã có [representation nguồn HTML cho 16 module CTDL](../data/08-voer-dsa-structural-representation.md); tiếp theo review/gom code, công thức và ngữ cảnh bảng/hình trước thử chunking. Chốt quyền thực thi/config/ngân sách cho bước bị ảnh hưởng; không dùng manual chunks chọn từ nhãn làm kết quả chunking benchmark.
5. Khi có content owner/reviewer: hiệu chỉnh rubric, xác nhận policy và nâng nhãn có review; giữ một nguồn/cụm tài liệu khác cho holdout.
6. Freeze test để nghiệm thu theo N5; không biến tập dev đã tối ưu thành test kín.

Cập nhật bước 4: đã có [nghiên cứu bổ sung chunking](../architecture/06-chunking-research-and-dependency-design.md) và [protocol 30 probe dự kiến](../evaluation/10-context-preservation-protocol.md). Việc tiếp theo là annotation/review các quan hệ cần giữ và không được nối nhầm; 30 probe chưa được tạo/chạy. Giữ dữ liệu hiện tại ở dev, không gọi đó là holdout chưa từng thấy.

Cập nhật tiếp nối bước 4: [R0 annotation/source review](../evaluation/11-context-review-round0.md) đã tạo 30 probe / 31 biến thể và enrichment 29 nhóm. Vẫn chưa chạy probe qua chunker; tiếp theo hoàn thiện serializer/source alignment rồi thử boundary trên scope công bố trước. Nhãn và các vùng chưa chắc chưa được nâng thành gold.

N5 vẫn là gate cho MVP/academic acceptance. Việc chuẩn bị metric, schema, static checks và technical experiments được phép trong scope nghiên cứu không tự làm N1-N3 đạt hay biến nguồn cách ly thành nguồn sản phẩm.
