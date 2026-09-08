# Chỉ mục tài liệu

Tài liệu ở đây là nguồn quyết định/phương pháp. Source triển khai được tách thành `ai-core/`, `backend/`, `frontend/`; dữ liệu có version vẫn ở `data/`.

## Bắt đầu và source ownership

- [Đọc trước: bài toán, mục tiêu, scope và non-goals cho model bất kỳ](00-project-brief.md)
- [Task packet độc lập model: đầu vào vừa scope, output/checks và comprehension probes](harness/MODEL-NEUTRAL-TASK.md)
- [Agent work harness: giữ scope/kế hoạch, baseline, checks và handoff khi đổi model](harness/README.md)
- [Project Charter](01-project-charter.md)
- [Roadmap không viết code sản phẩm](roadmap/01-no-code-roadmap.md)
- [Luồng đang làm: technical pilot 01 và danh sách case](roadmap/02-technical-pilot-v0.1.md)
- [Master Plan v0.2: phase map, work packages và mandatory ASTRA-01 review gate](roadmap/03-master-plan-v0.2.md)
- [Workflow hỏi/giải thích/mở nguồn xuyên ba component](workflows/01-grounded-qa-pilot.md)
- [Kết quả mô phỏng workflow: 11 tình huống, từng bước và quyết định còn mở](workflows/02-tabletop-simulation-v0.1.md)
- [Cấu trúc source ba thành phần và điểm tiếp tục](architecture/04-source-layout.md)
- [Boundary contracts](../contracts/README.md)
- [WP-01.1 review repair: chín findings, metric clarification, regression và contract cases chưa chạy](evaluation/29-review-regression-and-metric-clarifications-v0.1.md)

## Kiến trúc AI

- [WP-04 AI Core workflow review packet: states, quyền, failures, budgets và quyết định còn mở](architecture/10-ai-core-workflow-review-packet-v0.1.md)
- [ASTRA-01 review guide: đầu vào, prompt read-only và findings template; chưa product GO](roadmap/04-astra-review-guide-v0.1.md)

- [WP-02 multimodal readiness: PDF/hình/OCR, phạm vi và điều kiện trước chunk/index](architecture/09-multimodal-readiness-v0.1.md)
- [ARCH-02: phương án 2 đã chọn — workflow có kiểm soát, một vai trò suy luận chính, rules và các ca review chưa chạy](architecture/08-controlled-workflow-decision-v0.1.md)
- [Context-preserving chunking](architecture/01-context-preserving-chunking.md)
- [Research bổ sung: chunking giáo trình và dependency design, đối chiếu nguồn CTDL thật](architecture/06-chunking-research-and-dependency-design.md)
- [Indexing và retrieval](architecture/02-indexing-retrieval-design.md)
- [PDF có hình và dual-path retrieval](architecture/03-visual-pdf-retrieval.md)
- [Evidence pipeline contract: nguồn → chunk → packet → citation, kèm năm ví dụ thật](architecture/05-evidence-pipeline-contract.md)
- [Content Unit & Index Contract v0.1: identity, lineage, projection, conflict và revoke](architecture/07-content-unit-index-contract-v0.1.md)

## Dữ liệu và quyền

- [Đề xuất xóa nhầm/khôi phục: restricted trash, restore-to-review, purge/backup và quyết định còn mở](governance/06-material-deletion-recovery-v0.1.md)

- [Chỉ mục chương trình phân quyền và bảo mật agent](governance/00-authorization-program-index.md)
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
- [Kiến trúc phân quyền Zero Trust đa tổ chức: tenant isolation, agent capability, checkpoints và security gates](governance/03-multi-tenant-zero-trust-authorization.md)
- [Policy decision table v0.1: oracle ALLOW/DENY cho free user, hai tenant, admin, workload và agent](governance/04-authorization-policy-decision-table-v0.1.md)
- [Secure upload/quarantine/dedup: không vào thẳng content DB/index, xử lý exact/near duplicate và poisoned delta](governance/05-secure-upload-quarantine-deduplication-v0.1.md)
- [Authorization context và agent capability contract](../contracts/authorization-context.md)
- [Hướng dẫn sử dụng dữ liệu local](../data/README.md)
- [VOER corpus manifest](../data/raw/voer/MANIFEST.md)
- [Nguồn và hạn chế PDF pilot](../data/raw/pdf-pilot/SOURCE-NOTICE.md)

## Evaluation

- [WP-04 repair/handoff: ba findings, affected-scope re-review và recovery tests NOT RUN](evaluation/39-wp04-repair-recovery-handoff-v0.1.md)

- [WP-04 behavior/security map: 26 future case specifications NOT RUN](evaluation/37-wp04-behavior-security-review-v0.1.md)
- [WP-04 handoff: packet để Astra review, kiểm chứng và điểm dừng](evaluation/38-wp04-review-packet-handoff-v0.1.md)

- [WP-02 decision review: rủi ro, hướng xử lý, mốc cần chốt và đầu vào WP-04](evaluation/35-wp02-decision-review-v0.1.md)
- [WP-02 review handoff: kiểm chứng và điểm cần người dùng quyết định](evaluation/36-wp02-review-handoff-v0.1.md)

- [WP-02 probe protocol: preservation khác failure detection, cases chưa chạy](evaluation/33-multimodal-probe-protocol-v0.1.md)
- [WP-02 readiness handoff và local visual reinspection](evaluation/34-wp02-readiness-handoff-v0.1.md)
- [WP-03 inventory: snapshot, nhãn, eligibility và giới hạn từng pack](evaluation/30-evaluation-registry-inventory-v0.1.md)
- [WP-03 scorer specification: phép tính, N/A, routing và gaps còn mở](evaluation/32-scorer-specification-v0.1.md)
- [WP-03 technical handoff, không phải human/calibration acceptance](evaluation/31-wp03-inventory-handoff-v0.1.md)
- [Chiến lược đánh giá](evaluation/01-evaluation-strategy.md)
- [Metric contract v0.2: mẫu số, pass/fail và phân loại lỗi](evaluation/08-metric-contract-v0.2.md)
- [Danh mục dataset và benchmark](evaluation/02-dataset-catalog.md)
- [Local gold set specification](evaluation/03-gold-set-specification.md)
- [VOER silver evaluation pack](evaluation/04-silver-pack-voer-v0.1.md)
- [Experiment plan chunking/indexing](evaluation/05-chunking-indexing-experiment.md)
- [Protocol mất/ghép sai context: kế hoạch 30 probe, budget-matched ablation và thước đo](evaluation/10-context-preservation-protocol.md)
- [Kết quả context review R0: 30 probe / 31 biến thể, 29 nhóm và 4 ảnh đã xem](evaluation/11-context-review-round0.md)
- [Serializer R0 đã chạy: bảo toàn 29 nhóm, alignment, bảng/hình và trace từng bước](evaluation/12-source-serialization-round0.md)
- [Chunking R1 boundary-only: fixed 512 so với structure-aware 512 trên cùng input](evaluation/13-chunking-boundary-r1.md)
- [Dense retrieval R2: BGE-M3 local trên 16 module/216 text chunks](evaluation/14-dense-retrieval-r2-bge-m3.md)
- [Retrieval R3: BM25, RRF, BGE reranker và context packing](evaluation/15-retrieval-r3-hybrid-rerank-packing.md)
- [Retrieval R4: stability, comparison coverage gate và code-prologue dependency](evaluation/16-retrieval-r4-stability-coverage-dependency.md)
- [Measurement architecture v0.1: toàn bộ điểm đo, RAGAS mapping và stop/go gates](evaluation/17-measurement-architecture-v0.1.md)
- [Authorization security evaluation protocol v0.1: AUTH-01..14, execution rounds và hard gates](evaluation/18-authorization-security-evaluation-protocol-v0.1.md)
- [Authorization E0: 52 synthetic case / 56 checkpoint, lint pass và coverage gaps](evaluation/19-authorization-e0-fixture-review.md)
- [Authorization E0.1: mở rộng 84 case / 90 checkpoint, 23 action và 12 policy proposal cần review](evaluation/20-authorization-e01-action-expansion-review.md)
- [Authorization E0.2: upload quarantine, indirect injection, duplicate/near-duplicate; 102 case / 110 checkpoint](evaluation/21-authorization-e02-upload-dedup-review.md)
- [Duplicate detection mini-set E0.3: 26 synthetic labeled pairs, gồm 8 poisoned deltas](evaluation/22-duplicate-detection-labeled-mini-set-v0.1.md)
- [Synthetic PDF fixtures E0.4: 10 PDF, visual QA và byte/text/render diagnostics](evaluation/23-synthetic-pdf-duplicate-fixtures-e0.4.md)
- [PDF relation coverage E0.5: thêm 24 PDF/28 trang, đủ 26 pair IDs ở relation level](evaluation/24-pdf-relation-coverage-e0.5.md)
- [Deterministic dedup baselines E0.6: 36 PDF/21 relations, MinHash/SimHash và auto-link counterexamples](evaluation/25-deterministic-dedup-baselines-e0.6.md)
- [BGE-M3 duplicate ablation E0.7: dense recall, union load và global-threshold counterexample](evaluation/26-bge-m3-duplicate-ablation-e0.7.md)
- [Hard-negative routing E0.8: 60 PDF, candidate precision/load và exact-first routing](evaluation/27-hard-negative-routing-e0.8.md)
- [Equivalence/conflict triplets E0.9: claim inversion, dual candidate coverage và indexing invariants](evaluation/28-equivalence-conflict-triplets-e0.9.md)
- [Layout và visual retrieval evaluation](evaluation/06-visual-pdf-evaluation.md)
- [Parser diagnostic vòng 0 và 12 structural probes](evaluation/07-parser-diagnostic-round0.md)
- [Evidence mapping CTDL: 10 câu, 30 claims, 22 locators](evaluation/09-evidence-mapping-voer-dsa.md)
- [Visual silver seed: 13 trang audit / 8 QA nháp](../data/evaluation/silver/vn-pdf-visual-v0.1/README.md)

Các link `data/` là artifact local, có thể không đi cùng source checkout. Không nhầm tài liệu kế hoạch, silver draft hoặc baseline diagnostic với kết quả nghiệm thu.
