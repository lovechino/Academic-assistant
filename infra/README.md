# Deployment and local infrastructure

Nơi dành cho Docker/local compose, service configuration và deployment manifests khi cần triển khai. Hiện chưa có container, cloud resource hoặc service được tạo.

AI core là component độc lập về source, chưa bắt buộc deploy riêng. Có thể compose cùng backend trước; chỉ tách worker/model service khi chi phí, tài nguyên hoặc vận hành yêu cầu.

Không copy secrets, env, project IDs hay deployment config từ P-122. Không bake dữ liệu cách ly vào image. Dependencies và runtime versions sẽ được chọn, pin và kiểm tra ở phase implementation tương ứng.
