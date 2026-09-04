# Ingestion

Nơi triển khai quy tắc biến parsed elements thành cấu trúc học liệu: logical slide, table continuation, figure-caption, formula-variable, semantic child/parent và source provenance.

Parsing/OCR bằng thư viện cụ thể nằm ở infrastructure. Không chunk chuỗi text mất layout rồi coi đó là ground truth; không publish/index tài liệu chưa được backend xác nhận đủ điều kiện.

Đặc tả hiện tại ở [context-preserving chunking](../../../../docs/architecture/01-context-preserving-chunking.md). Đây chưa phải pipeline đã triển khai.
