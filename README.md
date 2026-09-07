# Academic Assistant

Dự án xây dựng bộ trợ lý học thuật dựa trên kho tài liệu được phê duyệt. Source được chia rõ thành **AI core, Backend, Frontend**. Giai đoạn hiện tại có khung tổ chức source, tài liệu và nghiên cứu dữ liệu; **chưa có ứng dụng/model/index chạy thật**.

Bắt đầu bằng [bài toán và phạm vi bản ngắn](docs/00-project-brief.md), đọc [charter đầy đủ](docs/01-project-charter.md) khi cần mục tiêu/tiêu chí/điều chưa chốt. Model bất kỳ có thể nhận [task packet](docs/harness/MODEL-NEUTRAL-TASK.md); không cần biết lịch sử chat, nhưng vẫn phải được cấp đủ input và công cụ cho task. Chưa có bảo đảm mọi model nhỏ đều đủ năng lực thực hiện.

## Cấu trúc dự án

```text
ai-core/     Xử lý học liệu, RAG, agents, prompts, evaluation và experiments
backend/     API, identity/permissions, courses/materials, review, jobs và persistence
frontend/    UI ba trợ lý, Knowledge Hub, review workspace và citation viewer
contracts/   Đặc tả boundary giữa các thành phần
docs/        Problem, metrics, workflow, kiến trúc và governance
data/        Nguồn, annotations và kết quả local có version
infra/       Dành cho cấu hình hạ tầng/deploy về sau
scripts/     Kiểm tra và bảo trì repo
tests/       Dành cho integration xuyên thành phần
tmp/         Scratch local, không phải source
```

- [AI core](ai-core/README.md), [Backend](backend/README.md), [Frontend](frontend/README.md).
- [Source layout, ownership và những điểm tham khảo từ P-122](docs/architecture/04-source-layout.md).
- [Toàn bộ tài liệu nghiên cứu](docs/README.md), [data policy](data/README.md), [boundary contracts](contracts/README.md).

Hai helper PDF đã chuyển vào `ai-core/experiments/pdf-pilot/`; `data/` và các snapshot giữ nguyên. Không copy source/secrets/dependencies từ P-122. Tách component không bắt buộc tách thành ba microservices.

## Kiểm tra scaffold

```powershell
python scripts/verify_structure.py --require-local-data
```

Cần Python 3.11+; không cài dependencies sản phẩm. Với checkout chưa có corpus, bỏ `--require-local-data`; các thiếu sót data sẽ được báo skip. Lệnh chỉ kiểm tra structure/syntax/links/checksum, không chạy lại parser hoặc sửa dữ liệu. Xem [chi tiết](scripts/README.md).

Chưa có lệnh chạy backend/frontend, package manifest, Docker service hay bộ runtime tests. Đang đi lại problem -> metrics -> workflow/contracts -> data -> parsing/chunking/indexing.

## Luồng đang làm

[Agent work harness](docs/harness/README.md) giúp các model dùng chung state/card, kiểm tra scope theo baseline và bàn giao bằng chứng. Đây là tooling phát hiện lệch quy trình, không phải agent runtime hoặc security sandbox. Bắt đầu bằng `py -3.11 -B scripts/agent_harness.py status`.

[Master Plan v0.2](docs/roadmap/03-master-plan-v0.2.md) là nguồn trạng thái hiện hành: [WP-01.1 review repair](docs/evaluation/29-review-regression-and-metric-clarifications-v0.1.md) đã sửa chín findings ở mức draft/contracts và bounded regression; còn human sign-off/runtime validation. Bước kế tiếp là WP-03 evaluation inventory/scorers, rồi WP-02 multimodal/OCR readiness. Trước khi sửa runtime `ai-core/src`, thêm product entrypoint/dependencies/index writer hoặc đóng orchestration state machine, dự án phải dừng tại **ASTRA-01** để người dùng review AI Core workflow bằng Astra và xác nhận GO.

[Technical pilot 01](docs/roadmap/02-technical-pilot-v0.1.md): tạm chọn CTDL & Giải thuật, hỏi kiến thức -> giải thích có citation -> mở đúng nguồn. Đã có [metric contract v0.2](docs/evaluation/08-metric-contract-v0.2.md), [workflow xuyên ba component](docs/workflows/01-grounded-qa-pilot.md) và profile tham chiếu 14 case silver có sẵn.

[Mapping evidence đầu tiên](docs/evaluation/09-evidence-mapping-voer-dsa.md) đã nối 10 answerable case với 30 claims, 25 nhóm và 22 đoạn nguồn định vị bằng hash/offset. Vẫn là silver, chưa chạy benchmark. Đã chạy [11 tình huống workflow synthetic](docs/workflows/02-tabletop-simulation-v0.1.md), ghi từng bước và thử 9 lần cố ý bỏ guard; tiếp theo cần người dùng review quy tắc xử lý và các nhãn còn mở, chưa code sản phẩm.

Đã bổ sung [evidence pipeline contract và năm ví dụ trên nguồn CTDL thật](docs/architecture/05-evidence-pipeline-contract.md): ba tài liệu, sáu excerpt/chunk mẫu, ba context windows; tách source, model input, answer draft và evaluator sidecar. Đây là manual contract examples, chưa phải parsing/chunking/indexing benchmark.

Vòng tiếp theo đã [parse cấu trúc nguồn thật của toàn bộ 16 module CTDL](docs/data/08-voer-dsa-structural-representation.md), giữ vị trí HTML, section, bảng, ảnh và sub/sup; 22/22 locator silver truy ngược được. Chưa chunk/index hoặc chạy model. Bước kế tiếp là review/gom code, công thức và ngữ cảnh bảng/hình trước khi chọn đơn vị chunk; integrity pass không đồng nghĩa đã hiểu ngữ nghĩa.

Đã bổ sung [nghiên cứu chunking và quan hệ ngữ cảnh](docs/architecture/06-chunking-research-and-dependency-design.md), cùng [protocol 30 probe dự kiến](docs/evaluation/10-context-preservation-protocol.md). Tách đơn vị tìm kiếm khỏi context cần để hiểu; kiểm tra cả mất context lẫn nối nhầm. Đây là kế hoạch, chưa tạo/chạy 30 probe hoặc chọn chunker thắng cuộc.

Vòng tiếp nối đã [tạo annotation cho 30 probe / 31 biến thể và review nguồn](docs/evaluation/11-context-review-round0.md): 29 nhóm, 7 dependency candidates, 4 ảnh xem trực tiếp. Vẫn là silver, chưa chạy chunking. Tiếp theo cần serializer giữ nguồn và thử boundary có giới hạn; không đưa expected fixture vào runtime.

Cập nhật mới nhất: đã [chạy serializer bảo toàn nguồn trên 29 nhóm / 188 roots](docs/evaluation/12-source-serialization-round0.md), có [trace và ví dụ đọc được](data/processed/voer-dsa-serialization-v0.1/review-examples.md), alignment giữ sub/sup/bảng/ảnh. Chưa đo token/chunking/retrieval; bước kế tiếp là freeze tokenizer/input/scope cho R1 boundary-only, giữ source issues và các case chưa đủ context.

Đã [chạy R1 fixed 512 so với structure-aware 512](docs/evaluation/13-chunking-boundary-r1.md) trên cùng 4 module/tokenizer/budget. Structure loại bỏ cut xuyên atom/rich node trong run này nhưng tạo nhiều chunks hơn, chỉ cải thiện 1/29 group và chưa cứu 3 dependency edges.

Đã [chạy R2 BGE-M3 dense retrieval local](docs/evaluation/14-dense-retrieval-r2-bge-m3.md) trên đủ 16 module: 216 text chunks, 10 câu/25 evidence groups silver. All-evidence success đạt 80%@5 và 80%@10; hai câu so sánh vẫn thiếu vế đến rank 14/17, nên chưa được phép coi any-hit/MRR là đủ bằng chứng. Đây là experiment index local, chưa phải product index hoặc answer/agent benchmark.

Đã [chạy R3 BM25 → RRF → BGE reranker → token-budget packing](docs/evaluation/15-retrieval-r3-hybrid-rerank-packing.md). Reranker int8 pool 40 đưa 25/25 groups vào top 5, nhưng packet 1.024 token chỉ giữ đủ 9/10 case; 2.048 giữ 10/10 trong dev run. Expansion heuristic không hơn child-only trên QA và còn thiếu `dep-03`; visual dependency vẫn unsupported. Audit 71/71 kèm warning batch-shape int8, nên chưa freeze production config.

Đã [chạy R4 stability + comparison coverage + code-prologue](docs/evaluation/16-retrieval-r4-stability-coverage-dependency.md). F32 giữ nguyên ranking giữa batch 1/4 trên frozen probe, còn dynamic-int8 tạo 19 đảo cặp nên không dùng raw score làm threshold. Comparison route giữ đủ hai nhánh ở top 2 nhưng không cải thiện relevance tổng thể. X3 cứu `dep-03` và đạt 6/6 text dependencies; do match 62/216 chunks và chưa có negative-context gold, nó vẫn chỉ là candidate resolver. Visual path và generation chưa chạy.

Theo quyết định tạm dừng đi sâu vào code, dự án đã chuyển sang [measurement architecture v0.1](docs/evaluation/17-measurement-architecture-v0.1.md): vẽ toàn pipeline, định nghĩa metric/mẫu số/gate cho source → parser → chunking → retrieval → packing → generation → citation → agents → delivery, và đặt RAGAS ở vai trò automated diagnostic cần calibration. Chưa cài RAGAS hoặc mở generation run.

Để chuẩn bị mở rộng đa trường/tổ chức và free user, đã thiết kế [phân quyền Zero Trust đa tổ chức v0.1](docs/governance/03-multi-tenant-zero-trust-authorization.md) cùng [authorization context/agent capability](contracts/authorization-context.md). Blueprint kết hợp RBAC + quan hệ tài nguyên + thuộc tính/purpose; kiểm tra quyền trước retrieval, từng dependency/tool, model input, cache, delivery và source viewer. [Chỉ mục authorization](docs/governance/00-authorization-program-index.md) hiện nối blueprint với [policy decision table 102 case/110 checkpoint](docs/governance/04-authorization-policy-decision-table-v0.1.md), [secure upload/quarantine/dedup](docs/governance/05-secure-upload-quarantine-deduplication-v0.1.md), AUTH-01..14 và UPL-01..12. Đây là thiết kế/fixtures, chưa phải runtime authorization đã triển khai hay chứng nhận an toàn.

Upload policy U-01..U-12 đã được người dùng chấp thuận và freeze làm candidate v0.1: raw file chỉ vào tenant quarantine, không vào content DB/serving index; exact/near duplicate giữ provenance và cần resolution riêng. [Mini-set duplicate E0.3](docs/evaluation/22-duplicate-detection-labeled-mini-set-v0.1.md) có 26 synthetic pairs để review labels. E0.4–E0.8 xây 60 PDF/64 trang và chốt exact-first candidate routing; [E0.9 equivalence/conflict triplets](docs/evaluation/28-equivalence-conflict-triplets-e0.9.md) thêm 36 PDF, đưa pool lên 96 PDF/100 trang. Char5, MinHash và BGE-M3 đều lấy đủ equivalent+conflict ở K=2 nhưng xếp bản sai claim ở rank 1 cho 12/12 triplet. Vì vậy similarity chỉ sinh candidate; không được collapse index, auto-merge hoặc chọn truth.

[Content Unit & Index Contract v0.1.1](docs/architecture/07-content-unit-index-contract-v0.1.md) chuẩn hóa blob → submission/snapshot → quarantine representation → approved promotion binding → material/version → serving units/projections. Internal evidence envelope có model-input projection riêng. Contract giữ content truth, similarity/conflict và authorization truth độc lập; serving snapshot được activate qua guarded publish boundary, revoke chặn bằng current policy trước khi purge index hoàn tất. Đây là corrected draft, chưa có runtime enforcement.

## Nguyên tắc quyết định

1. KPI nghiệm thu được đo trên tài liệu nội bộ và bộ test đóng băng.
2. Benchmark công khai dùng để tham khảo phương pháp và kiểm tra năng lực chung, không thay thế local gold set.
3. Đánh giá retrieval, generation, citation, pedagogy, routing và safety riêng trước khi tổng hợp kết quả end-to-end.
4. Không tối ưu theo test set cuối và không dùng điểm RAGAS như một cách gọi khác của accuracy.
