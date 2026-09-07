# Dense retrieval R2 — BGE-M3 local

Baseline retrieval-only dùng `BAAI/bge-m3` revision `5617a9f61b028005a4858fdac845db406aefb181`. Corpus không rời máy; model chạy bằng ONNX Runtime CPU, float32, CLS pooling theo upstream config và L2 normalization. Exact dot product được dùng thay ANN/vector DB để không đưa thêm sai số vào pilot 216 vectors.

## Phạm vi

- Chunker: `structure-512-o0` của R1, mở rộng nguyên trạng từ 4 lên toàn bộ 16 module của cùng snapshot.
- Evaluation: 10 câu answerable assistant-silver, 25 evidence groups, 22 locators; 6 tài liệu không có qrel vẫn nằm trong index làm distractor.
- Input encoder: text normalization trên từng boundary đã đóng băng; không header, overlap, generated context, parent expansion, BM25, reranker hoặc fine-tune.
- Một chunk chỉ có hình không còn text sau projection và bị loại có kiểm soát. Đây là baseline text-only, không phải xử lý ảnh.

Model files local nằm trong `tmp/models/` và không commit. Config khóa revision, kích thước và SHA-256 của hai file ONNX. Derived corpus, vectors và kết quả nằm trong `data/processed/voer-dsa-dense-r2-v0.1/`, cũng không commit theo data policy.

## Tái hiện

Tạo venv local rồi cài đúng [requirements lock](requirements.lock.txt). Tải đúng các file model tại revision đã pin vào `tmp/models/bge-m3-5617a9f61b028005a4858fdac845db406aefb181/`; script từ chối file sai size/hash.

```powershell
./tmp/r2-bge-m3-venv/Scripts/python.exe -X utf8 ai-core/experiments/dense-retrieval-r2/prepare_corpus.py --summary
./tmp/r2-bge-m3-venv/Scripts/python.exe -X utf8 ai-core/experiments/dense-retrieval-r2/run_dense_retrieval.py
./tmp/r2-bge-m3-venv/Scripts/python.exe -X utf8 ai-core/experiments/dense-retrieval-r2/audit_dense_retrieval.py --output data/processed/voer-dsa-dense-r2-v0.1/validation.json
```

Run hiện tại encode 216 chunks trong 192,932 giây và 10 queries trong 1,392 giây trên CPU 4 threads, batch 1. Audit đạt 18/18 checks và 3 guards; deterministic probe có max absolute delta 0.

| K | Evidence-group recall | All-evidence success | Any-evidence hit | Macro qrel-chunk recall |
|---:|---:|---:|---:|---:|
| 1 | 76% | 60% | 90% | 75% |
| 3 | 80% | 70% | 90% | 80% |
| 5 | 84% | 80% | 90% | 85% |
| 10 | 88% | 80% | 100% | 90% |
| 20 | 100% | 100% | 100% | 100% |

Chi tiết và cách diễn giải: [R2 report](../../../docs/evaluation/14-dense-retrieval-r2-bge-m3.md). Đây là diagnostic trên dev silver, không phải agent/answer accuracy.
## Historical-profile notice (2026-09-06)

This runner reproduces the frozen R2 baseline. Its legacy plain-text projection can collapse sub/sup and other rich semantics; do not use it as new generator evidence. The versioned repair and regression tests are in [context-integrity-v0.1](../context-integrity-v0.1/README.md). Existing config/input/vector/result hashes and implementation remain unchanged; no corrected retrieval score is claimed.
