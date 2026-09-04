# Chỉ mục tài liệu

Tài liệu ở đây là nguồn quyết định/phương pháp. Source triển khai được tách thành `ai-core/`, `backend/`, `frontend/`; dữ liệu có version vẫn ở `data/`.

## Bắt đầu và source ownership

- [Project Charter](01-project-charter.md)
- [Roadmap không viết code sản phẩm](roadmap/01-no-code-roadmap.md)
- [Luồng đang làm: technical pilot 01 và danh sách case](roadmap/02-technical-pilot-v0.1.md)
- [Workflow hỏi/giải thích/mở nguồn xuyên ba component](workflows/01-grounded-qa-pilot.md)
- [Kết quả mô phỏng workflow: 11 tình huống, từng bước và quyết định còn mở](workflows/02-tabletop-simulation-v0.1.md)
- [Cấu trúc source ba thành phần và điểm tiếp tục](architecture/04-source-layout.md)
- [Boundary contracts](../contracts/README.md)

## Kiến trúc AI

- [Context-preserving chunking](architecture/01-context-preserving-chunking.md)
- [Research bổ sung: chunking giáo trình và dependency design, đối chiếu nguồn CTDL thật](architecture/06-chunking-research-and-dependency-design.md)
- [Indexing và retrieval](architecture/02-indexing-retrieval-design.md)
- [PDF có hình và dual-path retrieval](architecture/03-visual-pdf-retrieval.md)
- [Evidence pipeline contract: nguồn → chunk → packet → citation, kèm năm ví dụ thật](architecture/05-evidence-pipeline-contract.md)

## Dữ liệu và quyền

- [Tiêu chí chọn môn pilot](data/01-pilot-selection.md)
- [Data catalog và phiếu kiểm kê](data/02-data-catalog.md)
- [Metadata dictionary](data/03-metadata-dictionary.md)
- [N1 readiness checklist](data/04-n1-readiness-checklist.md)
- [Báo cáo crawl VOER](data/05-crawl-report-voer.md)
- [PDF pilot Việt Nam: 17 PDF / 236 trang và visual audit](data/06-pdf-pilot-audit.md)
- [Nguồn scan/OCR tiếng Việt và điều kiện truy cập](data/07-ocr-scan-source-review.md)
- [CTDL source HTML structure: 16 module, truy vết evidence và các vùng cần review trước chunking](data/08-voer-dsa-structural-representation.md)
- [Permission matrix](governance/01-permission-matrix.md)
- [Vòng đời tài liệu](governance/02-document-lifecycle.md)
- [Hướng dẫn sử dụng dữ liệu local](../data/README.md)
- [VOER corpus manifest](../data/raw/voer/MANIFEST.md)
- [Nguồn và hạn chế PDF pilot](../data/raw/pdf-pilot/SOURCE-NOTICE.md)

## Evaluation

- [Chiến lược đánh giá](evaluation/01-evaluation-strategy.md)
- [Metric contract v0.2: mẫu số, pass/fail và phân loại lỗi](evaluation/08-metric-contract-v0.2.md)
- [Danh mục dataset và benchmark](evaluation/02-dataset-catalog.md)
- [Local gold set specification](evaluation/03-gold-set-specification.md)
- [VOER silver evaluation pack](evaluation/04-silver-pack-voer-v0.1.md)
- [Experiment plan chunking/indexing](evaluation/05-chunking-indexing-experiment.md)
- [Protocol mất/ghép sai context: kế hoạch 30 probe, budget-matched ablation và thước đo](evaluation/10-context-preservation-protocol.md)
- [Kết quả context review R0: 30 probe / 31 biến thể, 29 nhóm và 4 ảnh đã xem](evaluation/11-context-review-round0.md)
- [Serializer R0 đã chạy: bảo toàn 29 nhóm, alignment, bảng/hình và trace từng bước](evaluation/12-source-serialization-round0.md)
- [Layout và visual retrieval evaluation](evaluation/06-visual-pdf-evaluation.md)
- [Parser diagnostic vòng 0 và 12 structural probes](evaluation/07-parser-diagnostic-round0.md)
- [Evidence mapping CTDL: 10 câu, 30 claims, 22 locators](evaluation/09-evidence-mapping-voer-dsa.md)
- [Visual silver seed: 13 trang audit / 8 QA nháp](../data/evaluation/silver/vn-pdf-visual-v0.1/README.md)

Các link `data/` là artifact local, có thể không đi cùng source checkout. Không nhầm tài liệu kế hoạch, silver draft hoặc baseline diagnostic với kết quả nghiệm thu.
