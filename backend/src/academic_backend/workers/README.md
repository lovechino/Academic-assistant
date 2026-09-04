# Workers

Job entrypoints cho ingestion được phê duyệt, cập nhật/thu hồi index và background work về sau. Worker xác thực job scope, hỗ trợ retry/idempotency và gọi use case, không nhân bản logic chunk/index.

Chưa chọn queue/worker framework. Chưa có consumer hay scheduled task được khởi chạy.
