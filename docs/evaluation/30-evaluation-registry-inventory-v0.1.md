# WP-03 — Evaluation inventory v0.1

2026-09-06. Technical inventory, **pending human review/M0**, không là academic acceptance. User giao WP-03 rồi WP-02. Không tạo dataset mới, chấm lại historical model outputs hoặc chạy provider.

## 1. Phạm vi và snapshot

[Registry máy đọc](registry-v0.1.json) ghi 18 nhóm artifact, tổng 105 file references được kiểm kê từ local bytes, gồm các references chung. Mỗi file có path, SHA-256 và byte size. Hash chỉ xác định bản đang có, không là chữ ký lịch sử hoặc chứng minh nhãn đúng. Không đưa nội dung PDF/QA vào registry public. Các snapshots thực vẫn ở data local, giữ restrictions.

Corpus VOER: `voer-2026-09-04-r1`, local reference/evaluation theo source notice, không training. Corpus PDF: `vn-pdf-pilot-2026-09-04-v0.1`, chỉ local inspection, rights pending; không serving, OCR/VLM bên ngoài hoặc rộng hơn inspection mặc định. Synthetic không chứa người/trường thật nhưng vẫn không tự được đưa vào serving. Xem source notices được pin trong registry; không suy quyền mới từ license summary.

## 2. Inventory theo đơn vị đúng

Các số trong bảng là **reported inventory counts** từ README/report hiện hành, không là model scores chạy mới. Các nhóm dùng lại nguồn/nhãn nên không cộng tất cả thành N độc lập. Chi tiết từng file/byte snapshot và restriction trong JSON cùng ID.

| Registry ID | Đơn vị / nguồn | Authority và exposure | Có thể kết luận / chưa thể kết luận |
|---|---|---|---|
| VOER-SEED | 60 draft cases: 30 Academic, 10 Learning, 12 router, 8 safety | Assistant silver, dev | Kiểm schema/source refs; không GAP/gold; route cũ cần đối chiếu ARCH-02 |
| EVIDENCE-MAP | 10 QA, 30 claims, 25 groups, 22 locators | Assistant silver, dev | AND/OR locator diagnostics; không answer correctness; 10 modules có nhãn không là retrieval allowlist |
| CONTEXT-PROBES | 30 probes / 31 variants | Assistant silver, exposed | Review context; expected sidecar không vào model |
| CONTRACT-EXAMPLES | 5 examples, manually selected excerpts/packets | Source thật + mock output | EX-04 loss counterexample; draft answer không là LLM output |
| VISUAL-SEED | 13 pages / 8 QA từ 6 PDFs | Assistant silver, quarantine | Review targets; bbox approximate chưa đủ IoU/gold |
| TABLETOP | 11 scenarios, 132 baseline steps, 66 source actions | Synthetic, exposed | Stub/state expectations; không live auth/cache/retrieval |
| AUTH-FIXTURES | E0/E0.1/E0.2; current 102 cases/110 checkpoints | Synthetic policy draft | Lint/coverage; không runtime enforcement. 52/84 là mốc cũ, không ba tập độc lập |
| DUPLICATE-FIXTURES | 26 pairs; E0.4–E0.9 PDF manifests/results | Synthetic dev, tuned/exposed | Candidate/poison/conflict diagnostics; không semantic equivalence, OCR accuracy hoặc hidden threshold |
| PDF-AUDIT | 17 PDFs / 236 physical pages | Diagnostic, quarantine | Page/object audit; text nonempty không chứng minh hiểu hình |
| PDF-LAYOUT | 13 selected pages, 12 SP specifications | Silver/oracle regions | Extraction/read-order diagnostics; crop có sẵn không là auto-layout; SP không là 12 pass |
| HTML-STRUCTURE | 16 CTDL modules | Source-derived + silver sidecars | Traceability; semantic correctness pending |
| HTML-ENRICHMENT | Manual source enrichment | Assistant silver | Hypothesis/visual observations; không canonical source truth |
| SERIALIZATION-R0 | 29 groups chọn từ 4 modules | Selected dev groups | Event/alignment integrity, không full-corpus quality |
| CHUNKING-R1 | Fixed vs structure, cùng 4-module input | Silver boundary-only | Boundary/capacity diagnostics; không paired E2E |
| RETRIEVAL-R2 | Dense BGE-M3 results | Exposed silver | Retrieval-only; generation NOT RUN |
| RETRIEVAL-R3 | Hybrid/rerank/packing | Exposed silver | Historical micro recall; không gọi thành macro; generator NOT RUN |
| RETRIEVAL-R4 | Stability/comparison/dependency | Exposed silver | Pre-pack/prologue loss/false expansion limits theo repair report; generation NOT RUN |
| CONTEXT-REPAIR | 23 unittest methods với subcases | In-memory synthetic | Limited projection/packing behavior; không auto-discovery/PDP |

Registry còn pin technical-pilot profile: Q=10/U=1/S=3 là phân nhóm silver dự kiến, không human eligibility. Empty qrels của U không là Recall=100%. RC-01..21 là integration specifications NOT RUN, riêng RC-14 chỉ có basic projection regression. ARCH-C01..13 là routing/design specifications NOT RUN. HARNESS-B01..13 là development-model comprehension, **khác namespace** với product metrics B-01..03 về user study.

Public datasets trong [catalog](02-dataset-catalog.md) là candidates/methodology, không phải đã nhập hay đã chạy: QASPER/MultiHop-RAG/RAGBench/RAGTruth/ALCE/GroUSE/RAGChecker; ViQuAD/VN-MTEB; tutor benchmarks; OmniDocBench/SlideVQA/DocVQA/OCRBench. Không cập nhật claim license/count từ memory. Chỉ kiểm license/revision/terms lại khi chọn release cụ thể; không cần tải thêm để đóng inventory local.

## 3. Eligibility và split

1. Chọn case universe trước run, ghi từng disposition theo metric. Official Academic GAP hiện `pending_review`, không phải zero accuracy hoặc đã đủ gold.
2. Integrity checks có thể chạy trên data local; scoring semantics chỉ được công bố là silver/synthetic diagnostics trong phạm vi nhãn tương ứng. PDF quyền chỉ inspection: broader evaluation cần rights review riêng, dù labels đầy đủ.
3. Theo dõi riêng `selected`, `eligible`, `pending`, `excluded_with_reason`, `attempted`, `completed`, `failed`. Timeout/missing output trên eligible case không bị loại khỏi mẫu số.
4. Group theo source family/document + mọi crop/revision/paraphrase/duplicate/triplet trước split; không split ngẫu nhiên từng câu/pair/ảnh. Một group dùng chung source không là nhiều independent observations.
5. Dev hiện exposed/tuned; chưa có frozen test, judge calibration hoặc red-team holdout độc lập được thiết lập ở lượt này. Không chia lại dev đã xem rồi đổi tên thành hidden.
6. Qrels, answer drafts, expected permission và dependency truth là evaluator-only. Actual input cho model phải được ghi/hash riêng và loại các sidecars; tránh oracle leakage.

## 4. Chuẩn hóa scorer và gaps

[Scorer specification](32-scorer-specification-v0.1.md) là bản chuẩn hóa cho run mới; definitions chi tiết kế thừa metric contract v0.2 + clarification v0.1.1. Không rewrite số cũ. Experiment mới chỉ kiểm số học/AND-OR trên synthetic input; không implement RAGAS hay model grader.

| Gap | Cách xử lý / owner | Chặn việc gì? |
|---|---|---|
| Qrels/claims/visual boxes chưa chuyên gia duyệt | Content reviewer adjudicate từng case, version mới | Official GAP, OCR/layout accuracy, config winner |
| X3 precision thiếu negative labels | Review trigger/nontrigger và required dependency targets, kể cả omission | Bật resolver mặc định |
| Macro/micro/historical mismatches | Pin scorer definition, paired same outputs nếu được giao rescore | So scores khác definition |
| RAGAS thiếu version/judge/prompt/calibration | Thiết kế calibration tiếng Việt; pin sau review | Judge dùng như release gate |
| A-01 gộp mode và response behavior | Tách nhãn trong spec, không sửa route fixtures cũ | Freeze router taxonomy/F1 |
| Security events chưa có implementation trace | Backend integration suite sau gate | Tuyên bố auth/revoke/cache runtime pass |
| OCR/visual thiếu reviewed transcription/matching | WP-02 readiness + local inspection protocol | Chấm CER/IoU hoặc chọn parser |
| Numerics/resource thresholds TBD | Người dùng/reviewer duyệt trước run lựa chọn | Production thresholds, SLA, model budget |

## 5. Disposition

Inventory/specification và bounded arithmetic tests là chuẩn bị kỹ thuật. M0 user review, học thuật, rights, scorer coverage toàn bộ và runtime integration vẫn mở. **Đủ đầu vào để tiếp tục soạn WP-02 readiness**, không đủ mở model benchmark/M4 hay product implementation. Handoff ghi checks thực và scope closure; không nâng toàn bộ WP-03 thành nghiệm thu hoàn chỉnh.
