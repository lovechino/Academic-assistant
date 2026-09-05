# R1 boundary-only: fixed 512 với structure-aware 512

Ngày chạy: 2026-09-05. **Đã chạy chunking boundary-only local trên cùng input; chưa index, retrieval hoặc generation.** Tiếp nối [serializer R0](12-source-serialization-round0.md) và [protocol](10-context-preservation-protocol.md).

## Cấu hình freeze trước run

Chọn tokenizer XLM-R đi cùng `BAAI/bge-m3`, revision `5617a9f61b028005a4858fdac845db406aefb181`; file tokenizer có SHA-256 `21106b6d7dab2952c1d496fb21d5dc9db75c28ed361a05f5020bbba27810dd08`. BGE-M3 được tác giả mô tả là multilingual và dùng tokenizer XLM-R; đây là lý do tương thích cho corpus tiếng Việt, **không phải kết luận BGE-M3 đã thắng retrieval của dự án**. [BGE-M3 model card](https://huggingface.co/BAAI/bge-m3), [tokenizer config tại revision được pin](https://huggingface.co/BAAI/bge-m3/blob/5617a9f61b028005a4858fdac845db406aefb181/tokenizer_config.json).

Runtime local dùng `tokenizers==0.23.2`, truncation/padding tắt. Hugging Face mô tả pipeline tokenizer gồm normalizer → pre-tokenizer → model → post-processor và API có character offsets; run vẫn tự kiểm tra hash/count/partition, không chỉ tin tên API. [Tokenizer API](https://huggingface.co/docs/tokenizers/api/tokenizer), [PyPI 0.23.2](https://pypi.org/project/tokenizers/0.23.2/).

Budget giống nhau: hard cap 512 token gồm `<s>`/`</s>`, overhead thực tế 2, body 510, overlap=0, header=0. Input là toàn bộ source-preserving projection của 4 module Stack/Queue/Mảng/DSLK, không chỉ 29 manual groups.

- `fixed-512-o0`: cắt ở tokenizer offset khi đầy.
- `structure-512-o0`: outermost heading/p/li/tr/figure, greedy trong source section; không split atom. Atom vượt cap phải giữ và báo ineligible; run này không có atom vượt cap.

Config đầy đủ: [config v0.1](../../ai-core/experiments/chunking-r1/config-v0.1.json). Không tải model weights hoặc gửi corpus ra ngoài.

## Kết quả

| Metric | Fixed | Structure |
|---|---:|---:|
| Chunks | 57 | 78 |
| Mean / median token | 485,47 / 512 | 356,15 / 467,5 |
| Boundary cắt semantic atom | 52 | 0 |
| Boundary cắt rich node | 7 | 0 |
| Chunk qua source section | 19 | 0 |
| Manual groups trọn trong một eligible chunk | 23/29 | 24/29 |
| Dependency group-pairs cùng một chunk | 4/7 | 4/7 |

Structure loại bỏ cut xuyên p/list item/row/figure/heading và không trộn source section trong run này, nhưng tạo thêm 21 chunks (+36,8%) và giảm mức lấp đầy. Nó cải thiện containment đúng một nhóm; không được gọi là winner retrieval/end-to-end.

Hai case được structure cứu: `stack-list-introduction` (fixed cắt giữa paragraph dẫn) và `queue-queue-deque-table` (fixed cắt bảng/hàng). Một regression: `stack-postfix-dinhtri` nằm trọn một fixed chunk nhưng structure tách qua hai chunks, vì source listing là 19 p và strategy chưa nhận diện function boundary. Fixed ở đây là trùng hợp placement, không phải semantic guarantee; structure failure là bằng chứng cần code grouping riêng.

Năm nhóm structure vẫn tách:

- Oversized theo members-only diagnostic: `stack-postfix-program` 1.529 token, `stack-trace-table` 792 token. Hard cap 512 không thể giữ cả logical group trong một child.
- Nhỏ hơn cap nhưng bị placement/boundary: `stack-postfix-dinhtri` 319, `queue-array-declaration` 298, `array-multidim-lead` 129 token.

Cả hai chỉ đặt đủ hai đầu của 4/7 dependency candidates trong cùng một chunk. `dep-02` (POP → khai báo), `dep-03` (dinhtri → giới hạn chương trình), `dep-07` (hai ảnh công thức → phần dẫn/cận) chưa được cứu. Không edge nào auto-follow; R2 dependency expansion vẫn cần thiết. SIM-03 chưa được kiểm tra bằng agent: thiếu dependency phải được phát hiện ở packing/generation sau này, không thể suy từ boundary integrity.

## Tính hợp lệ của run

[Helper và cách tái hiện](../../ai-core/experiments/chunking-r1/README.md) tách boundary construction khỏi evaluator. Audit monkeypatch chặn đọc enrichment trong lúc tạo chunks và xác nhận output không đổi; annotations chỉ mapping hậu kiểm. 1.728 checks, 3 additional guards và 9 mutations đạt. Hai rebuild khớp artifact đã lưu.

Source/representation hashes của 4 module và tokenizer hash đều được kiểm tra. 319/319 scaffold/syntax/link/source checks đạt, 13 Python files syntax-valid, 17 PDF hashes đúng, không skip. PDF không tham gia run và vẫn quarantine.

Output local không push vì `data/processed/` bị data policy ignore: [báo cáo mọi boundary](../../data/processed/voer-dsa-chunking-r1-v0.1/boundary-report.md), [run JSON](../../data/processed/voer-dsa-chunking-r1-v0.1/run.json), [validation](../../data/processed/voer-dsa-chunking-r1-v0.1/validation.json).

## Quyết định cho vòng kế

Giữ structure-aware làm baseline **bảo toàn kỹ thuật**, chưa freeze làm chunker thắng. R1 tiếp theo nên ablate ba điểm, vẫn cùng tokenizer/cap/input: (1) nhận diện code/function group và disposition oversized; (2) packing-aware grouping để group nhỏ không bị placement split; (3) row-table parent/reference thay vì ép bảng 792 token vào một child. Sau đó chấm lại boundary metrics trước khi chuyển sang R2 retrieval/dependency packing.

Không dùng 52/0 như answer accuracy, không dùng 24/29 như retrieval recall, và không tuyên bố chống hallucination. Tất cả labels vẫn assistant-silver/dev, academic review pending.
