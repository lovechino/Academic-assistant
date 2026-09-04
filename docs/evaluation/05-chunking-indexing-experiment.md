# Chunking và indexing experiment plan v0.1

Ngày cập nhật: 2026-09-04

Bổ sung sau audit CTDL thật: [protocol context preservation](10-context-preservation-protocol.md) tách review grouping → chunking-only → retrieval/packing → generation; có kế hoạch 30 probe, forbidden merges, token-budget matching và mẫu số rescue. Matrix dưới đây giữ vai trò thiết kế tổng; chưa chạy C0–C8/I0–I5, không coi 22 locator silver là bộ chunking gold.

## 1. Câu hỏi cần trả lời

1. Parser nào giữ reading order, bảng, công thức, hình và provenance tốt nhất trên giáo trình Việt Nam?
2. Chunk boundary nào cho recall cao mà không kéo quá nhiều context thừa?
3. Child–parent retrieval có cứu được câu hỏi phụ thuộc định nghĩa/antecedent không?
4. Context header deterministic hoặc LLM-generated có cải thiện retrieval không?
5. Dense, BM25, hybrid và reranking đóng góp bao nhiêu?
6. Cấu hình nào đạt chất lượng tốt nhất trong giới hạn latency, RAM và chi phí?

## 2. Nguyên tắc thí nghiệm

- Không đổi parser, chunker, embedding, fusion và reranker cùng lúc.
- Cố định corpus snapshot, query set, filters và tokenizer cho mỗi comparison.
- Ghi cả retrieval-only, oracle generation và end-to-end.
- Dùng test theo module/document split; không để evidence gần-trùng ở dev và frozen test.
- Không chọn cấu hình chỉ theo answer quality của một LLM judge.

## 3. Round P — parser benchmark

Cần bổ sung tối thiểu 10 PDF/slide đại diện: native text, scan, hai cột, bảng dài, công thức, code, figure/caption và trang nối bảng.

Cập nhật 2026-09-04: đã thu 17 PDF / 236 trang và audit bằng mắt 13 trang ([báo cáo](../data/06-pdf-pilot-audit.md)). Đã thấy handout 2-up/4-up, vector chart, ký hiệu ER và row nối trang; **chưa có mẫu scan được xác nhận**, chưa phủ hết profile trên. Audit object/text bằng pdfplumber không phải kết quả benchmark P0-P2. Bộ PDF đang quarantine pending rights review. Bổ sung metric/evidence visual theo [protocol multimodal](06-visual-pdf-evaluation.md).

| ID | Parser | Mục đích |
|---|---|---|
| P0 | PyMuPDF blocks/words | Baseline text-layer đơn giản |
| P1 | Docling structured parse | Candidate chính cho layout/table/OCR |
| P2 | Unstructured hi-res/by-title | Challenger/fallback |

Metrics:

- Page ingestion success.
- Text coverage và OCR CER/WER trên sample có transcription.
- Reading-order accuracy.
- Heading hierarchy F1.
- Table cell/header reconstruction.
- Figure-caption link accuracy.
- Page/bbox provenance accuracy.
- Latency và peak memory trên mỗi trang.

Hard gate đề xuất:

- Page count và document identity: 100%.
- Source locator mở đúng trang: 100%.
- Không có silent empty page.
- Bảng/công thức/hình không đạt phải có quality flag, không được âm thầm coi là plain text tốt.

## 4. Round C — chunking benchmark

Dùng cùng parser output và cùng dense model baseline.

| ID | Strategy | Child | Parent/context | Mục đích |
|---|---|---|---|---|
| C0 | Fixed token | 512 + overlap 64 | none | Baseline bắt buộc |
| C1 | Structure-aware small | target 256, hard 384 | section ID | Kiểm tra precision |
| C2 | Structure-aware medium | target 384, hard 512 | section ID | Candidate mặc định |
| C3 | Structure-aware large | target 600, hard 768 | section ID | Kiểm tra context tự thân |
| C4 | Hierarchical small-to-big | C2 child | parent 1.200–1.800 hoặc subsection | Kiểm tra parent rescue |
| C5 | C4 + deterministic header | C2 child | course/doc/section/page/type | Context an toàn |
| C6 | C4 + semantic boundary fallback | dynamic | same parent | Chỉ cho section dài/thiếu heading |
| C7 | C4 + LLM contextual sentence | C2 child | generated 50–100 token context | Challenger có rủi ro |
| C8 | Late chunking | structural boundaries | long-context embedding | Advanced challenger |

Round đầu chạy C0–C5. Chỉ chạy C6–C8 nếu C4/C5 vẫn có context-related misses hoặc khi có ngân sách thử nghiệm.

## 5. Round I — indexing/retrieval benchmark

Giữ chunker thắng Round C.

| ID | Candidate retrieval stack |
|---|---|
| I0 | BM25 only |
| I1a | Dense multilingual-e5 |
| I1b | Dense BGE-M3 |
| I1c | Dense Qwen3-Embedding |
| I2 | Best dense + BM25, RRF |
| I3 | I2 + cross-encoder reranker |
| I4 | I2 + ColBERT/late-interaction reranker |
| I5 | I3 + parent/neighbor expansion + context packing |

RRF là fusion mặc định đầu tiên. Weighted RRF/DBSF chỉ tune trên dev/validation; không tune raw weighted sum của cosine và BM25.

## 6. Tạo qrels từ silver pack

Nguồn hiện tại có 25 Academic case answerable, 1 partially answerable, 4 unanswerable và thêm các evidence-bearing Learning/Safety cases.

Với mỗi chunker version:

1. Tìm mọi chunk chứa từng candidate evidence span.
2. Gắn relevance level:
   - `3`: chứa trực tiếp required evidence.
   - `2`: parent/neighbor cần thiết để giải nghĩa evidence.
   - `1`: cùng section và hữu ích nhưng không đủ trả lời.
   - `0`: không liên quan.
3. Case multi-hop có qrels theo từng evidence group; phải đo `all-evidence hit`, không chỉ có một chunk đúng.
4. Case unanswerable phải có empty gold result hoặc only-insufficient result tùy case.
5. Sau human review mới đổi candidate qrels thành gold qrels.

## 7. Metrics chunk quality

### Structural integrity

- `section_purity`: tỷ lệ chunk không trộn sibling sections ngoài rule cho phép.
- `atomic_integrity`: tỷ lệ table row/list/code/formula không bị cắt sai.
- `orphan_rate`: chunk bắt đầu bằng tham chiếu/đại từ nhưng không có resolvable parent/neighbor.
- `header_footer_noise_rate`.
- `duplicate_context_ratio` do overlap.

### Evidence preservation

- `evidence_containment_rate`: candidate evidence nằm trọn trong ít nhất một child.
- `evidence_group_coverage`: tỷ lệ evidence groups có chunk tương ứng.
- `parent_rescue_rate`: child hit nhưng chỉ parent expansion mới chứa đủ ngữ cảnh.
- `locator_accuracy`: chunk/evidence mở đúng page/bbox.
- `context_expansion_precision`: phần parent/neighbor thêm vào thực sự cần cho query.

## 8. Metrics retrieval và end-to-end

### Retrieval

- Recall@5 và Recall@10.
- MRR.
- nDCG@10 với relevance 0–3.
- All-evidence Recall@10 cho multi-hop.
- Context precision/recall ở claim level theo tư duy của [RAGChecker](https://arxiv.org/abs/2408.08067).
- Zero-result correctness cho unanswerable query.

### End-to-end

- Grounded Answer Pass Rate.
- Required-claim recall và unsupported-claim rate.
- Citation precision, coverage và locator accuracy.
- Correct abstention cho missing/current data.
- Unauthorized retrieval/citation rate.

### Operational

- Index build time và size.
- Embedding throughput và cost.
- Query P50/P95 latency theo từng stage.
- Peak RAM/VRAM.
- Số token context sau expansion/dedup.

## 9. Gate và cách chọn winner

Các ngưỡng dưới đây là target kỹ thuật ban đầu, không phải cam kết học thuật:

| Gate | Target ban đầu |
|---|---:|
| Metadata/provenance completeness | 100% |
| Unauthorized retrieval | 0 |
| Table header retention khi split | 100% |
| Section purity trên audit sample | ≥98% |
| Evidence containment | ≥95% |
| Recall@5 trên answerable reviewed subset | ≥90% |
| Recall@10 | ≥95% |
| Multi-hop all-evidence Recall@10 | ≥85% |
| Citation locator accuracy | 100% |
| Correct abstention ở missing/stale cases | 100% |

Selection rule:

1. Loại mọi config fail hard gate về permission, provenance, missing asset hoặc citation.
2. Trong số còn lại, ưu tiên Recall@5/10 và multi-hop all-evidence recall.
3. Nếu chênh lệch retrieval nằm trong uncertainty, chọn config có context precision cao hơn và latency/index size thấp hơn.
4. Chỉ chọn advanced contextualization/late interaction nếu cải thiện lặp lại trên nhiều slice, không chỉ điểm tổng.

## 10. Slice bắt buộc

- Course: CTDL, CSDL, Kinh tế vi mô.
- Query: lookup, explanation, comparison, multi-hop, table/figure/formula, unanswerable, stale.
- Content: paragraph, list, table, figure, formula, code.
- Context dependency: self-contained, needs heading, needs previous/next, needs parent, cross-document.
- PDF profile: native, scan, multi-column, complex table.
- Language: Vietnamese only và Vietnamese query → English source khi có corpus song ngữ.

## 11. Error analysis form

Mỗi failure phải chọn stage đầu tiên gây lỗi:

1. Source không có/không còn hiệu lực.
2. Parser mất nội dung hoặc sai reading order.
3. Chunker cắt mất evidence/context.
4. Sparse/dense candidate generation miss.
5. Fusion hạ đúng chunk.
6. Reranker hạ đúng chunk.
7. Parent expansion/context packing sai.
8. Generator đọc sai evidence.
9. Citation sai.
10. Policy/router/RBAC sai.

Không sửa prompt generator khi root cause là parser, chunker hoặc retriever.

## 12. Thứ tự thực hiện

1. Thu thập 10–20 PDF/slide đại diện và tạo parser truth set 10 trang đầu.
2. Chạy P0–P2; chốt canonical document graph.
3. Chạy C0–C5 trên cùng embedding baseline.
4. Sinh qrels theo từng chunker và review evidence mismatch.
5. Chọn 1–2 chunker rồi chạy I0–I5.
6. Chạy oracle và end-to-end trên silver pack.
7. Human review các failure và một mẫu pass.
8. Freeze `chunker_profile v1` và `index_profile v1` chỉ sau khi đạt gate.
