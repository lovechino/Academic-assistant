# AI application

Nơi đặt use case ingestion/query/explanation/learning guidance và ports nhỏ cho model, search, render/source fetch. Phối hợp pipeline theo budget và scope nhận từ backend.

Application không phụ thuộc FastAPI hay backend repository. Entry point/composition sẽ inject adapters; không import concrete adapter vào domain. Chưa có use case đang chạy.
