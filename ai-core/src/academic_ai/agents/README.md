# Agents

Nơi đặt router và workflow cho Academic Assistant, Learning Assistant, Knowledge Hub khi bắt đầu implementation. Workflow gọi các use case qua hợp đồng, không tự mở DB hoặc sửa quyền/phê duyệt.

Graph topology, node behavior và tool permissions phải tách rõ. Không hard-code thuật toán parsing/retrieval vào node; không để tài liệu được truy xuất trở thành system instruction.

Chưa có LangGraph runtime hay agent đang chạy. Prompt có phiên bản đặt tại [prompts](../../../prompts/README.md).
