# Academic Assistant

Dự án xây dựng bộ trợ lý học thuật dựa trên kho tài liệu được phê duyệt. Source được chia rõ thành **AI core, Backend, Frontend**. Giai đoạn hiện tại có khung tổ chức source, tài liệu và nghiên cứu dữ liệu; **chưa có ứng dụng/model/index chạy thật**.

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

[Technical pilot 01](docs/roadmap/02-technical-pilot-v0.1.md): tạm chọn CTDL & Giải thuật, hỏi kiến thức -> giải thích có citation -> mở đúng nguồn. Đã có [metric contract v0.2](docs/evaluation/08-metric-contract-v0.2.md), [workflow xuyên ba component](docs/workflows/01-grounded-qa-pilot.md) và profile tham chiếu 14 case silver có sẵn.

[Mapping evidence đầu tiên](docs/evaluation/09-evidence-mapping-voer-dsa.md) đã nối 10 answerable case với 30 claims, 25 nhóm và 22 đoạn nguồn định vị bằng hash/offset. Vẫn là silver, chưa chạy benchmark. Đã chạy [11 tình huống workflow synthetic](docs/workflows/02-tabletop-simulation-v0.1.md), ghi từng bước và thử 9 lần cố ý bỏ guard; tiếp theo cần người dùng review quy tắc xử lý và các nhãn còn mở, chưa code sản phẩm.

Đã bổ sung [evidence pipeline contract và năm ví dụ trên nguồn CTDL thật](docs/architecture/05-evidence-pipeline-contract.md): ba tài liệu, sáu excerpt/chunk mẫu, ba context windows; tách source, model input, answer draft và evaluator sidecar. Đây là manual contract examples, chưa phải parsing/chunking/indexing benchmark.

Vòng tiếp theo đã [parse cấu trúc nguồn thật của toàn bộ 16 module CTDL](docs/data/08-voer-dsa-structural-representation.md), giữ vị trí HTML, section, bảng, ảnh và sub/sup; 22/22 locator silver truy ngược được. Chưa chunk/index hoặc chạy model. Bước kế tiếp là review/gom code, công thức và ngữ cảnh bảng/hình trước khi chọn đơn vị chunk; integrity pass không đồng nghĩa đã hiểu ngữ nghĩa.

Đã bổ sung [nghiên cứu chunking và quan hệ ngữ cảnh](docs/architecture/06-chunking-research-and-dependency-design.md), cùng [protocol 30 probe dự kiến](docs/evaluation/10-context-preservation-protocol.md). Tách đơn vị tìm kiếm khỏi context cần để hiểu; kiểm tra cả mất context lẫn nối nhầm. Đây là kế hoạch, chưa tạo/chạy 30 probe hoặc chọn chunker thắng cuộc.

Vòng tiếp nối đã [tạo annotation cho 30 probe / 31 biến thể và review nguồn](docs/evaluation/11-context-review-round0.md): 29 nhóm, 7 dependency candidates, 4 ảnh xem trực tiếp. Vẫn là silver, chưa chạy chunking. Tiếp theo cần serializer giữ nguồn và thử boundary có giới hạn; không đưa expected fixture vào runtime.

Cập nhật mới nhất: đã [chạy serializer bảo toàn nguồn trên 29 nhóm / 188 roots](docs/evaluation/12-source-serialization-round0.md), có [trace và ví dụ đọc được](data/processed/voer-dsa-serialization-v0.1/review-examples.md), alignment giữ sub/sup/bảng/ảnh. Chưa đo token/chunking/retrieval; bước kế tiếp là freeze tokenizer/input/scope cho R1 boundary-only, giữ source issues và các case chưa đủ context.

Đã [chạy R1 fixed 512 so với structure-aware 512](docs/evaluation/13-chunking-boundary-r1.md) trên cùng 4 module/tokenizer/budget. Structure loại bỏ cut xuyên atom/rich node trong run này nhưng tạo nhiều chunks hơn, chỉ cải thiện 1/29 group và chưa cứu 3 dependency edges; chưa phải retrieval hoặc answer benchmark.

## Nguyên tắc quyết định

1. KPI nghiệm thu được đo trên tài liệu nội bộ và bộ test đóng băng.
2. Benchmark công khai dùng để tham khảo phương pháp và kiểm tra năng lực chung, không thay thế local gold set.
3. Đánh giá retrieval, generation, citation, pedagogy, routing và safety riêng trước khi tổng hợp kết quả end-to-end.
4. Không tối ưu theo test set cuối và không dùng điểm RAGAS như một cách gọi khác của accuracy.
