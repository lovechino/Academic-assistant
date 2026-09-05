# Retrieval R4 — stability, comparison coverage và code prologue

R4 giữ bất biến corpus/chunks/vectors của R2 và ranking R3. Vòng này không chạy generation: nó kiểm tra ba failure còn mở của R3 bằng artifact mới, không sửa lịch sử R3.

## Artifact đã chạy

- `stability-results.json`: 80 cặp đầu từ RRF-depth-80, so F32/int8 và batch 1/4 trên cùng candidate IDs; qrels không tham gia chọn probe.
- `comparison-branches.json`: parser hẹp cho mẫu tiếng Việt `so sánh <quan hệ> của A và B`, rồi BGE-M3 + BM25/RRF riêng cho từng nhánh.
- `comparison-results.json`: BGE reranker trên 20 candidate mỗi nhánh, round-robin có dedup và coverage gate; qrels chỉ chấm sau khi merged ranking tồn tại.
- `code-prologue-results.json`: X3 đi lùi tối đa hai chunk trong cùng section khi anchor mang marker code, dừng ở prologue marker; dependency labels chỉ dùng hậu kiểm.
- `validation.json`: 60/60 integrity/metric checks, 3 negative guards và một finding về int8.

Các output nằm trong `data/processed/voer-dsa-retrieval-r4-v0.1/` và không commit theo data policy.

## Chạy lại

```powershell
./tmp/r3-reranker-venv/Scripts/python.exe -X utf8 ai-core/experiments/retrieval-r4/run_reranker_stability.py
./tmp/r2-bge-m3-venv/Scripts/python.exe -X utf8 ai-core/experiments/retrieval-r4/run_comparison_branches.py
./tmp/r3-reranker-venv/Scripts/python.exe -X utf8 ai-core/experiments/retrieval-r4/run_comparison_rerank.py
./tmp/r2-bge-m3-venv/Scripts/python.exe -X utf8 ai-core/experiments/retrieval-r4/run_code_prologue_packing.py
./tmp/r2-bge-m3-venv/Scripts/python.exe -X utf8 ai-core/experiments/retrieval-r4/audit_retrieval_r4.py
```

F32 giữ nguyên toàn bộ thứ tự của 80 cặp giữa batch 1/4, max raw-logit delta `1,53e-5`. Dynamic int8 giữ top-1 của 10/10 query nhưng có 19 pairwise inversions và max delta `1,084`; không dùng raw score/margin int8 làm threshold.

Comparison coverage giữ đủ hai branch ngay top 2 trên hai dev case và vẫn đủ 5/5 evidence groups ở top 3, nhưng mean binary nDCG@3 giảm từ `0,920` xuống `0,847`. Đây là guard có điều kiện, chưa phải ranking winner.

X3 cứu `dep-02` và `dep-03`, đạt 6/6 text dependencies; visual `dep-07` vẫn unsupported. X3 match 62/216 text chunks, nên cần negative context labels trước khi bật mặc định. Budget 1.024 vẫn chỉ đủ 9/10 case; 2.048 đủ 10/10 trong dev run hiện tại.

Xem [báo cáo R4](../../../docs/evaluation/16-retrieval-r4-stability-coverage-dependency.md). Không dùng các kết quả assistant-silver này để tuyên bố agent accuracy, chống hallucination hoặc production readiness.
