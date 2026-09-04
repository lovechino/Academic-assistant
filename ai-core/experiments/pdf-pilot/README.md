# PDF pilot offline helpers

- `profile_local.py`: khảo sát 17 PDF / 236 trang; **ghi lại** `data/raw/pdf-pilot/manifest.json` và output `data/processed/pdf-pilot/audit-v0.1/` khi chạy.
- `audit_layout_order.py`: diagnostic trên 13 annotations; **ghi lại** `data/processed/pdf-pilot/layout-diagnostic-v0.1/extractions.json` khi chạy.

Sau khi di chuyển, cả hai dùng repo root ở `Path(__file__).resolve().parents[3]`. Vị trí `data/` không đổi; chạy từ thư mục làm việc khác vẫn định vị đúng nguồn.

Đây là helper lịch sử có side effects, không phải import-safe library hay CLI sản phẩm. Không chạy để chỉ kiểm tra cách bố trí source. Dùng [structural verifier](../../../scripts/README.md); nếu thật sự tái chạy khảo sát, lưu run/version mới hoặc bảo vệ snapshot trước.

Dependencies của helper hiện có: `pdfplumber`, `pypdf`; chưa thêm chúng vào runtime AI core. Tài liệu nguồn và dẫn xuất tiếp tục cách ly theo [source notice](../../../data/raw/pdf-pilot/SOURCE-NOTICE.md).
