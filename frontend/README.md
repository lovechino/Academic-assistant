# Frontend

Owner của trải nghiệm người dùng. Hiện chỉ có khung source; chưa có trang web chạy được, package manifest hoặc UI đã thiết kế.

| Thư mục | Trách nhiệm |
|---|---|
| `src/app/` | Routes, layout và composition giao diện |
| `src/features/` | Academic Assistant, Learning Assistant, Knowledge Hub và review workspace |
| `src/components/` | UI components dùng chung thật sự |
| `src/lib/` | Backend API client, DTO mapping, UI utilities |
| `public/` | Chỉ static assets được phép public |
| `tests/` | Component/accessibility/contract và UI tests về sau |

Next.js là hướng dự kiến trong đề bài và tương đồng P-122; chưa chốt/cài version. Không copy package lock, node_modules, UI thương mại hoặc cấu hình từ P-122.

Frontend chỉ gọi backend qua [HTTP contract](../contracts/http-api.md). Không giữ model keys, gọi vector DB trực tiếp hoặc quyết định quyền thực. Nút bị ẩn không thay kiểm tra ACL phía server.

Citation viewer phải hiển thị nguồn/trang/region và trạng thái thiếu evidence; URL ảnh/PDF được backend cấp theo quyền. Không đưa PDF cách ly vào `public/`.
