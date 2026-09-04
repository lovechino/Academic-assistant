# Cross-component tests

Nơi dành cho contract/integration/end-to-end giữa AI core, backend và frontend khi có implementation. Tests riêng từng component nằm ở `ai-core/tests/`, `backend/tests/`, `frontend/tests/`.

Các ca bắt buộc về sau: scope xuyên retrieval/fetch nguồn, revoke nguồn khi job đang chạy, citation bị từ chối sau revoke, error/stream mapping và review chỉ bởi actor được cấp quyền.

Hiện chưa có runtime test suite. `scripts/verify_structure.py` chỉ kiểm tra source scaffold và tham chiếu local; không cho biết chất lượng agents.
