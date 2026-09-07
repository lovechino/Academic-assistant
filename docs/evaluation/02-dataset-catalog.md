# Danh mục dataset và benchmark v0.1

Ngày nghiên cứu: 2026-09-04

## 1. Kết luận lựa chọn

Không có một public dataset nào đại diện đầy đủ cho giáo trình, slide, quyền truy cập và chính sách học thuật của trung tâm. Chiến lược phù hợp là:

- **Local gold set:** nguồn KPI nghiệm thu chính.
- **Public benchmark:** kiểm tra năng lực chung, học cách thiết kế nhãn và regression test.
- **Public methodology:** dùng rubric/metric đã được nghiên cứu, sau đó điều chỉnh cho tiếng Việt và chính sách nội bộ.

## 2. Nhóm RAG và academic QA

| Dataset/benchmark | Nội dung | Giá trị cho dự án | Quyết định |
|---|---|---|---|
| QASPER | 5.049 câu hỏi trên 1.585 bài báo NLP; có evidence và câu unanswerable | Mô phỏng hỏi đáp trên tài liệu học thuật dài, evidence ở nhiều đoạn | Dùng subset để thử academic QA và evidence selection |
| MultiHop-RAG | 2.556 query; evidence phân bố trong 2-4 tài liệu và có metadata | Kiểm tra tổng hợp đa tài liệu và metadata-aware retrieval | Dùng subset làm stress test nâng cao |
| RAGBench | Khoảng 100.000 example trên 5 domain, có nhãn phục vụ đánh giá RAG | Kiểm tra evaluator và lỗi retrieval/generation trên quy mô lớn | Dùng để hiệu chuẩn evaluation pipeline, không dùng làm KPI nghiệp vụ |
| RAGTruth | Gần 18.000 response được gắn nhãn hallucination ở mức case và span | Xây detector/audit cho unsupported claim | Dùng taxonomy và một subset regression |
| ALCE | Benchmark và metric cho câu trả lời dài có citation | Thiết kế citation precision, completeness và correctness | Dùng methodology bắt buộc |
| GroUSE | 144 unit test cho evaluator grounded QA với 7 failure mode | Kiểm tra xem LLM judge có bỏ sót lỗi hay không | Dùng để meta-evaluate judge |
| RAGChecker | Framework và benchmark claim-level, tách retriever/generator | Error analysis chi tiết | Dùng sau khi đã có local reference answer |

Nguồn:

- [QASPER paper](https://aclanthology.org/2021.naacl-main.365/) và [dataset card, CC BY 4.0](https://huggingface.co/datasets/allenai/qasper)
- [MultiHop-RAG dataset card, ODC-BY](https://huggingface.co/datasets/yixuantt/MultiHopRAG)
- [RAGBench paper](https://arxiv.org/abs/2407.11005) và [dataset card, CC BY 4.0](https://huggingface.co/datasets/galileo-ai/ragbench)
- [RAGTruth paper](https://aclanthology.org/2024.acl-long.585/)
- [ALCE](https://aclanthology.org/2023.emnlp-main.398/)
- [GroUSE](https://aclanthology.org/2025.coling-main.304/)
- [RAGChecker](https://arxiv.org/abs/2408.08067)

## 3. Nhóm tiếng Việt và embedding

| Dataset/benchmark | Nội dung | Giá trị | Giới hạn |
|---|---|---|---|
| UIT-ViQuAD | Hơn 23.000 QA do con người tạo trên 5.109 đoạn từ 174 bài Wikipedia tiếng Việt | Kiểm tra đọc hiểu tiếng Việt và format QA | Không phải dữ liệu giáo trình và không kiểm tra RAG end-to-end |
| VN-MTEB | Benchmark embedding tiếng Việt đa nhiệm, mở rộng đáng kể độ phủ task | Shortlist embedding trước khi test trên local retrieval set | Kết quả public không thay thế retrieval test nội bộ |

Nguồn:

- [UIT-ViQuAD paper](https://aclanthology.org/2020.coling-main.233/)
- [VN-MTEB paper](https://aclanthology.org/2026.findings-eacl.86/)
- [MTEB benchmark registry](https://docs.mteb.org/overview/available_benchmarks/)

Không nên dịch tự động toàn bộ benchmark tiếng Anh rồi xem đó là benchmark tiếng Việt. Chỉ nên dịch một subset, sau đó để người Việt có chuyên môn sửa và gắn nhãn lại.

Đối với upload dedup/data-poisoning, dự án có [synthetic duplicate mini-set v0.1](22-duplicate-detection-labeled-mini-set-v0.1.md) gồm 26 pairs exact/near/revision/variant/unrelated và 8 poisoned deltas. E0.4–[E0.6](25-deterministic-dedup-baselines-e0.6.md) hiện thực hóa 36 relation PDFs; [E0.7](26-bge-m3-duplicate-ablation-e0.7.md) thêm BGE-M3; [E0.8](27-hard-negative-routing-e0.8.md) thêm 24 hard negatives; [E0.9](28-equivalence-conflict-triplets-e0.9.md) thêm 12 triplet/36 PDF để tách candidate coverage khỏi semantic equivalence. Pool hiện có 96 PDF/100 trang. Đây là development seed cho metric UPL-04..07 và claim-conflict gates, không phải public benchmark, production detector result hoặc hidden test.

## 4. Nhóm Learning Assistant và pedagogy

| Dataset/benchmark | Nội dung | Giá trị cho dự án | Quyết định |
|---|---|---|---|
| MRBench | 192 hội thoại và 1.596 phản hồi trong bản công bố; nhãn theo 8 chiều pedagogy | Rubric cho nhận diện lỗi, guidance, actionability và answer revealing | Nguồn rubric chính cho Learning Assistant |
| BEA 2025 Shared Task | Đánh giá Mistake Identification, Mistake Location, Providing Guidance và Actionability | Có task, nhãn 3 mức và macro-F1 rõ ràng | Dùng schema nhãn để tạo tutor set nội bộ |
| MathTutorBench | Benchmark open-ended cho tutoring; nhấn mạnh correctness, scaffolding, self-correction và cognitive load | Phân biệt “giải được bài” với “dạy tốt” | Dùng methodology; chỉ dùng math subset nếu pilot có môn phù hợp |
| TutorEval | 370 câu hỏi về chương sách khoa học, viết từ góc nhìn người học | Gần với hỏi đáp dựa trên giáo trình | Candidate cho smoke test Learning Assistant |
| TutorMoments | Các thời điểm dạy học được chuyên gia gắn nhãn về scaffolding và rigor | Đánh giá nhiều lượt và mức hỗ trợ phù hợp | Candidate nâng cao, sau MVP |
| Answer Leakage Robustness | Sáu nhóm kỹ thuật thuyết phục/adversarial nhằm lấy đáp án cuối từ tutor | Thiết kế red-team academic-integrity suite | Dùng taxonomy để tạo prompt tiếng Việt nội bộ |

Nguồn:

- [MRBench paper](https://arxiv.org/abs/2412.09416) và [repository](https://github.com/kaushal0494/UnifyingAITutorEvaluation)
- [BEA 2025 Shared Task](https://sig-edu.org/sharedtask/2025)
- [MathTutorBench](https://aclanthology.org/2025.emnlp-main.11/)
- [TutorEval repository](https://github.com/princeton-nlp/LM-Science-Tutor)
- [TutorMoments](https://github.com/allenai/tutormoments)
- [Answer Leakage Robustness paper](https://arxiv.org/abs/2604.18660)

## 5. Nhóm PDF, slide và OCR

| Dataset/benchmark | Nội dung | Giá trị | Quyết định |
|---|---|---|---|
| OmniDocBench | PDF đa dạng gồm academic paper, textbook, slide, công thức, bảng và handwritten note | So sánh parser/OCR và taxonomy lỗi tài liệu | Dùng methodology và một public subset |
| SlideVQA | Hơn 2.600 slide deck, 52.000 slide image và 14.500 câu hỏi | Kiểm tra retrieval/evidence trên nhiều slide | Candidate phù hợp trực tiếp với kho slide |
| DocVQA | 50.000 câu hỏi trên hơn 12.000 ảnh tài liệu | Kiểm tra document understanding và layout | Dùng cho OCR/document-QA smoke test |
| OCRBench | Text recognition, document VQA, key information extraction và công thức viết tay | Kiểm tra năng lực OCR/VLM chung | Chỉ dùng khi pipeline có OCR hoặc VLM |

Nguồn:

- [OmniDocBench paper](https://openaccess.thecvf.com/content/CVPR2025/html/Ouyang_OmniDocBench_Benchmarking_Diverse_PDF_Document_Parsing_with_Comprehensive_Annotations_CVPR_2025_paper.html)
- [SlideVQA paper](https://ojs.aaai.org/index.php/AAAI/article/view/26598)
- [DocVQA paper](https://openaccess.thecvf.com/content/WACV2021/html/Mathew_DocVQA_A_Dataset_for_VQA_on_Document_Images_WACV_2021_paper.html)
- [OCRBench paper](https://arxiv.org/abs/2305.07895)

## 6. Dataset không nên dùng làm KPI chính

- MMLU, GSM8K hoặc các exam benchmark chỉ đo kiến thức/giải bài của model, không đo việc grounded trên kho tài liệu.
- SQuAD/ViQuAD đơn thuần không đo retrieval trên corpus lớn, citation, quyền hay từ chối.
- Dữ liệu tổng hợp hoàn toàn bằng LLM có thể mở rộng coverage nhưng không được thay nhãn của giảng viên.
- Benchmark công khai có nguy cơ xuất hiện trong dữ liệu huấn luyện của model; chỉ nên dùng làm external sanity check.

Security authorization không dùng public QA benchmark làm oracle. Dự án có [synthetic authorization pack v0.1](../../data/evaluation/synthetic/authorization-v0.1/README.md) với hai tenant giả, free user, roles, agent/workload và expected checkpoint decisions. Pack này đo policy/enforcement theo [protocol riêng](18-authorization-security-evaluation-protocol-v0.1.md); không chứa tài liệu/người dùng thật và không được gộp với RAG quality score.

## 7. Ma trận áp dụng đề xuất

| Năng lực | Public reference | Local evaluation bắt buộc |
|---|---|---|
| Academic QA | QASPER, RAGBench | Câu hỏi từ giáo trình/slide thật |
| Multi-document synthesis | MultiHop-RAG | Gold evidence từ nhiều tài liệu nội bộ |
| Citation | ALCE | Claim-to-page/slide labels |
| Hallucination | RAGTruth, RAGChecker | Unsupported-claim annotations |
| Vietnamese retrieval | VN-MTEB, UIT-ViQuAD | Query thật bằng tiếng Việt theo môn |
| Tutor quality | MRBench, BEA, MathTutorBench | Hội thoại và policy của trung tâm |
| Academic integrity | Answer-leakage benchmark | Prompt tấn công tiếng Việt, bài tập thật đã ẩn đáp án |
| PDF/slide parsing | OmniDocBench, SlideVQA, DocVQA | 30-50 trang/slide đại diện của kho thật |

## 8. Kiểm tra pháp lý trước khi tải dữ liệu

Trước khi đưa dataset vào repository hoặc pipeline CI cần xác nhận lại license tại phiên bản cụ thể, yêu cầu attribution, điều kiện non-commercial và quyền phân phối lại. Với tài liệu nội bộ, chỉ lưu metadata/evidence theo chính sách dữ liệu của trung tâm; không đưa nội dung riêng tư vào public repository.
