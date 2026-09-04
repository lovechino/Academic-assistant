# AI evaluation implementation

Nơi đặt harness/config/scorer khi bắt đầu chạy benchmark; hiện chưa triển khai. Protocol ở [docs/evaluation](../../docs/evaluation/01-evaluation-strategy.md), dữ liệu nhãn ở `data/evaluation/`, kết quả khảo sát ở `data/processed/`.

Tách parsing, retrieval, reading, answer, citation, pedagogy, routing và safety. Không copy bộ test vào nhiều nơi; luôn tham chiếu snapshot/split/version. Silver/dev và oracle evidence không thay test kín/gold.

Các script khảo sát hiện tại vẫn ở [experiments](../experiments/README.md), không được coi là harness nghiệm thu agents.

Đã có [profile technical pilot v0.1](profiles/technical-pilot-v0.1.json) tham chiếu 14 case silver đã có: 10 answerable, 1 abstention và 3 policy. Đây là selection manifest `design_only_not_executed`, chưa có runner/schema API hay kết quả score. Mẫu số và rule ở [metric contract v0.2](../../docs/evaluation/08-metric-contract-v0.2.md).

Mapping cho 10 answerable case nằm riêng trong [data/evaluation](../../data/evaluation/silver/voer-dsa-evidence-map-v0.1/README.md), không thay profile hoặc pack cũ. Verifier tại [experiments/evidence-mapping](../experiments/evidence-mapping/README.md) chỉ chấm integrity và set coverage toy, không phải runner RAG.

[Contract examples](../../data/evaluation/silver/voer-dsa-contract-examples-v0.1/README.md) minh họa năm packet trên ba câu tham chiếu. Expected claims/groups ở evaluator sidecar riêng, không truyền vào model input hoặc retrieval filter. Không coi các chunks chọn từ nhãn để minh họa thành dataset benchmark chunker.
