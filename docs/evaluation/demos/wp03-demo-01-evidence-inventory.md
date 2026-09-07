# WP03-DEMO-01 — kiểm kê bằng chứng một report

Ngày 2026-09-06. Đây là đầu ra thật của một task nhỏ trong WP-03, do assistant hiện tại thực hiện bằng local harness. Không gọi thêm model/provider; không phải benchmark model nhỏ hoặc independent review. Mục tiêu: phân loại bằng chứng mà không nâng historical/synthetic/specification thành product acceptance.

## 1. Inputs được cố định cho lượt kiểm kê

| Ref | File/version | SHA-256 bytes đọc trong lượt |
|---|---|---|
| S1 | [Repair registry](../29-review-regression-and-metric-clarifications-v0.1.md), report v0.1; measurement clarification v0.1.1 | `af825cf7f31d46775449c95ac513e83f4d7fc46eeb4bd26bcb9fe3e87382f9dc` |
| S2 | [Experiment README](../../../ai-core/experiments/context-integrity-v0.1/README.md), context-integrity-v0.1 | `d87fdc577aea2517df9c29b5388c310c58f487bae71ed45aa81480b7c485d8c8` |
| S3 | [Test source](../../../ai-core/experiments/context-integrity-v0.1/test_context_integrity.py), context-integrity-v0.1 | `9b3e0eb9e96f2840b44b44449343d9f502df1476cf79cddb1613d099c4a0838d` |

HEAD tại begin: `54b405da8f549f68835626b1f03d8c41cd233573`. Repo có uncommitted/untracked work nên **HEAD không đủ pin inputs**; SHA-256 ở trên và baseline giữ trạng thái local. Các số dòng dưới áp dụng cho hashes này. Không đọc raw pilot corpus để làm inventory, không thay files S1–S3. Corpus hashes chỉ được kiểm tra bởi structure verifier ở bước kiểm tra cuối.

## 2. Inventory — bốn loại bằng chứng không dùng chung mẫu số

| ID | Nguồn/locator | Nội dung/status | Authority và exposure | Eligible cho phép đo nào? | Được/không được kết luận |
|---|---|---|---|---|---|
| INV-01 | S1 §2, dòng 23–31; S2 Limits; S3 methods dòng 26–184 | Report ghi 23/23 regression methods pass ngày 2026-09-06; **reported historical run, không rerun trong demo** | Fixture/expected assertions synthetic, exposed dev; không human gold hoặc hidden split | Kiểm regression của projection/packing trên fixture profile; static count trong demo | Được nói report đã ghi PASS. Không nói automatic dependency discovery, OCR, generator accuracy, BGE token budget hoặc runtime authorization đã đạt |
| INV-02 | S1 §6, dòng 118 | Report ghi 554/554 structure checks, 46 Python files, 17 PDF hashes, không skip; **historical** | Local mechanical verification được tóm tắt trong report; không phải nhãn học thuật; train/dev/test split không áp dụng | Structure/syntax/links/checksum trong snapshot cũ | Không dùng 554 như số checks của lượt demo hoặc số câu QA đúng; checksum không chứng minh rights |
| INV-03 | S1 §5, dòng 86–114 | RC-01..RC-21: **NOT RUN integration specifications** | Expected behavior trong design draft; independent runtime observations/human acceptance chưa có; exposed specs, không hidden test | Chuẩn bị test matrix về sau; chưa đủ observed outputs để chấm behavior | Không gán pass/fail runtime hay dùng 0/21 làm failure rate; riêng RC-14 có basic allowlist check, không biến thành integration pass |
| INV-04 | S1 §3–4, dòng 33–84 | Definitions CU/IX/CR/CI/R/V và mappings; **definition corrected, không phải score mới** | Design/measurement draft, chưa đồng nghĩa reviewed scorer/calibration; dataset split không áp dụng cho văn bản định nghĩa | Đặc tả scorer/registry WP-03; cần thêm run-specific snapshots, labels và outputs | Ngưỡng trong bảng không là score đạt được. IX-07b tolerance còn TBD; RAGAS/judge chưa chạy ghi not_measured |

Rights/eligibility: S1–S3 là tài liệu/source phục vụ kiểm kê local trong scope được giao; lượt này không xác nhận license để phân phối hoặc xử lý ngoài. Không suy quyền external OCR/VLM, train, publish của PDF/derivatives từ việc report có thể đọc được. Dataset/corpus snapshot của một academic evaluation run mới: **không có**, vì demo không tạo/chạy run đó.

Không có raw execution log của run lịch sử trong input packet này. Report và source code là bằng chứng cho **nội dung được báo cáo và cấu trúc tests**, không thay independent rerun hoặc chữ ký reviewer.

## 3. Disposition chín findings

Mỗi dòng lấy từ S1 §1, dòng 9–17; đây là trạng thái report, không là review lại toàn bộ implementation/contracts.

| Finding | Bằng chứng report có | Còn thiếu trước kết luận rộng hơn |
|---|---|---|
| F-01 | Synthetic projection regression | Corpus/embedding rerun; modalities ngoài profile |
| F-02 | Synthetic atomic packing regression | Resolver tự tìm đúng dependency trên nguồn thật |
| F-03 | Quarantine/inspection specification sửa | Runtime enforcement |
| F-04 | Quarantine/promotion lineage specification sửa | Persistence/integration tests |
| F-05 | Conflict-assessment specification sửa | Adjudication và conflict recall |
| F-06 | Public/share binding specification sửa | PDP và data-plane behavior |
| F-07 | Projection boundary synthetic pass | Provider/Backend integration, đặc biệt RC-14 |
| F-08 | Metric definitions sửa | Full inventory, scorer validation/calibration |
| F-09 | Serving snapshot/revoke ordering specification sửa | Concurrency/chaos tests |

F-01/F-02/F-07 có liên quan đến cùng regression suite; không nhân 23 tests ba lần. Chín disposition records không là chín integration cases pass.

## 4. Kiểm kê tĩnh đã chạy trong demo

Đọc S1–S3; dùng `Get-FileHash -Algorithm SHA256` để pin input và `rg` để kiểm đếm:

```powershell
rg -n '^    def test_' ai-core/experiments/context-integrity-v0.1/test_context_integrity.py
rg -n '^\| F-0[1-9] \|' docs/evaluation/29-review-regression-and-metric-clarifications-v0.1.md
rg -o '^\| RC-[0-9]{2}' docs/evaluation/29-review-regression-and-metric-clarifications-v0.1.md
```

Kết quả quan sát: **23 test method declarations, 9 finding IDs, 21 unique RC IDs**. So với expected inventory 23/9/21: PASS. Đây là ba checks đếm cấu trúc, không phải đã chạy 23 methods hoặc 21 RC cases. Có subcases trong methods; không gọi 23 là tổng số assertions.

## 5. Self-review theo acceptance

- Input pin: có ba paths/hashes, report/profile version và section/line locators; không lấy HEAD thay snapshot dirty files.
- Evidence honesty: tách reported historical, observed static và NOT RUN integration; không cộng các mẫu số.
- Context: giữ caveat codepoint/whitespace **không phải tokenizer**, dependency graph truyền sẵn **không phải discovery**, `eligible` offline **không phải quyền PDP**.
- RC-14: basic projection assertion chỉ là một phần; vẫn thiếu full integration.
- Scope: chỉ inventory một report và liên kết trực tiếp; không đóng WP-03, không sửa state/gate/nguồn lịch sử.

Đây là self-review của cùng assistant, không có reviewer độc lập; chưa báo H-04 accepted-task rate hay model accuracy. [Handoff và kết quả checker mới](wp03-demo-01-handoff.md) tách biệt khỏi các số historical ở INV-01/02.

## 6. Bước tiếp theo có ích

Khi người dùng yêu cầu tiếp tục WP-03, đưa các nhóm trên vào registry chung, đối chiếu packs còn lại theo cùng fields và thiết kế scorer tests cho unknown/N/A/missing outputs. Chưa cần model run để chuẩn hóa inventory. Independent review, human labels, OCR readiness và ASTRA-01 vẫn chưa được thay thế bởi demo này.
