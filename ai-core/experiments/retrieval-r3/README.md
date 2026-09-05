# Retrieval R3 — BM25, RRF, reranker và context packing

R3 giữ nguyên 216 text chunks, vectors và 10 case/25 evidence groups của R2 để tách đóng góp từng stage. Qrels chỉ đi vào evaluator sau khi candidate/ranking/packet đã tồn tại.

## Các artifact chạy thật

- `hybrid-results.json`: Unicode-word BM25 và RRF với BGE-M3 dense, prefetch depth 20/40/80.
- `reranker-results.json`: `BAAI/bge-reranker-v2-m3` revision `953dc6f6f85a1b2dbfca4c34a2796e7dde08d41e`, dynamic-int8 Linear weights từ upstream F32, CPU, batch 4; rerank nested pool 20/40/80 từ cùng RRF-depth-80 ranking.
- `packing-results.json`: pack ranking `reranker_pool_40` vào budget 1.024/2.048/4.096 token; so child-only, section-lead và cue-neighbor.
- `validation.json`: 71 integrity/metric checks, 2 negative guards và một warning đã khai báo.

Các file trên nằm ở `data/processed/voer-dsa-retrieval-r3-v0.1/` và không commit theo data policy. Model weights nằm trong `tmp/models/`.

## Chạy lại

BM25/RRF, packing và audit dùng venv R2; reranker dùng venv riêng với [dependency lock](requirements-reranker.lock.txt).

```powershell
./tmp/r2-bge-m3-venv/Scripts/python.exe -X utf8 ai-core/experiments/retrieval-r3/run_hybrid_retrieval.py
./tmp/r3-reranker-venv/Scripts/python.exe -X utf8 ai-core/experiments/retrieval-r3/run_reranker.py
./tmp/r2-bge-m3-venv/Scripts/python.exe -X utf8 ai-core/experiments/retrieval-r3/run_context_packing.py
./tmp/r2-bge-m3-venv/Scripts/python.exe -X utf8 ai-core/experiments/retrieval-r3/audit_retrieval_r3.py
```

Reranker score 800 pairs trong 593,579 giây, không pair nào bị truncation. Pool 40 đạt 25/25 evidence groups và 10/10 cases ở top 5. Đây là int8 diagnostic: cùng pair trong batch 4 và chạy riêng lệch raw logit 0,03069; không trình bày như F32/deterministic benchmark.

Packet 1.024 token chỉ giữ đủ 9/10 case; 2.048 token giữ 10/10 với ranking hiện tại. Section-lead expansion chỉ tăng dependency coverage text-path từ 4/6 lên 5/6; cue-neighbor không tăng. Một visual dependency không eligible cho text path.

Xem [báo cáo R3](../../../docs/evaluation/15-retrieval-r3-hybrid-rerank-packing.md) để đọc metric và failure analysis. Không dùng kết quả dev silver này làm production threshold.
