# Context annotation integrity audit

Helper offline, chỉ đọc và in JSON; không ghi đè data, không gọi model/network và không thực thi code trong nguồn.

Từ repository root:

```powershell
python -X utf8 ai-core/experiments/context-review/audit_review.py
```

Đã chạy bằng Python 3.12.14, standard library, không cài thêm dependencies. Exit 1 khi một integrity check/mutation detection thất bại.

Input: [enrichment nguồn](../../../data/processed/voer-dsa-enrichment-v0.1/README.md), [evaluator probes](../../../data/evaluation/silver/voer-dsa-context-probes-v0.1/README.md), raw và representation đã pin. Output đã lưu riêng ở validation.json trong evaluator pack.

Kiểm tra: source/ref hashes, version, membership, dependency targets/cycle, artifact research/evaluator boundaries, bảng/inline/blank regressions và expected fixture self-consistency. Mutation suite cố ý làm sai 12 trường hợp để kiểm tra validator.

Không xây nhóm tự động, không chấm semantic correctness, không chạy 30 probe qua chunker. Một validator đọc được field safety không thay kiểm thử chống prompt injection của runtime. Ghi rõ system_executions=0.

[Báo cáo review](../../../docs/evaluation/11-context-review-round0.md).
