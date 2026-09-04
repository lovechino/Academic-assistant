# Evidence contract example checks

Focused validator bằng Python 3.11+ standard library, không phải JSON Schema validator tổng quát hoặc code runtime. Kiểm tra [năm ví dụ từ nguồn VOER thật](../../../data/evaluation/silver/voer-dsa-contract-examples-v0.1/README.md) theo [đặc tả](../../../docs/architecture/05-evidence-pipeline-contract.md).

Từ root:

```powershell
python -X utf8 ai-core/experiments/evidence-contract/verify_examples.py
```

Chỉ đọc raw source, mapping, examples, evaluator sidecar và in JSON. Không ghi file, cài package, gọi network/model hoặc chạy helper PDF. Exit code khác 0 nếu baseline sai hoặc mutation mong đợi không được phát hiện; malformed input ngoài fixture có thể raise exception, không phải API validation behavior.

Kiểm tra:

- Identity/version/hash và text offsets đúng representation nguồn.
- Element/chunk/window/packet lineage, source text không bị thay, header không làm evidence.
- Citation dùng item có trong packet; đủ các nhóm AND/OR theo mapping ở phía evaluator.
- Không đưa required claims/qrels vào mock model input; không tự nâng research lên serving hoặc giả token-fit khi chưa đo.
- Chín mutation riêng kiểm tra các quy tắc đó thực sự có ảnh hưởng.

Coverage tính theo source spans, không theo semantic entailment. Qrels chưa exhaustive/gold. Candidate chunks và answer drafts chọn bằng tay chỉ phục vụ contract, không dùng kết quả này để chọn chunking/indexing strategy.

`validation.json` là snapshot kết quả có hash examples/sidecar/mapping/verifier. Chạy lại không tự ghi đè; khi có thay đổi có chủ đích phải ghi rõ version/history. Không import helper này từ product source.
