# Metadata dictionary v0.1

Ngày cập nhật: 2026-09-04

## 1. Thiết kế

Metadata được chia thành bảy nhóm: identity, educational context, provenance, rights/access, lifecycle, technical extraction và evaluation support.

Các tên trường nghiệp vụ bên dưới tham khảo Dublin Core cho metadata tài nguyên và Schema.org/LRMI cho tài nguyên học tập. Đây là application profile tối giản của dự án, không phải triển khai đầy đủ mọi trường của các chuẩn.

## 2. Identity và mô tả

| Field | Type logic | Bắt buộc | Quy tắc |
|---|---|---:|---|
| document_id | string | Có | Bất biến và duy nhất |
| title | text | Có | Tên chính thức |
| alternative_title | text/list | Không | Tên viết tắt hoặc tên cũ |
| description | text | Có | Mô tả ngắn do owner duyệt |
| document_type | enum | Có | Dùng controlled vocabulary |
| subject_tags | list | Có | Thuật ngữ môn học có kiểm soát |
| keywords | list | Không | Từ khóa tự do có review |
| language | BCP 47 | Có | `vi`, `en` hoặc danh sách ngôn ngữ |
| creator | person/org | Có | Tác giả/đơn vị tạo tài liệu |
| contributor | list | Không | Người đóng góp |

## 3. Educational context

| Field | Bắt buộc | Ý nghĩa |
|---|---:|---|
| course_id | Có | Mã môn |
| department | Có | Đơn vị sở hữu |
| educational_level | Có | Trình độ/năm học nếu áp dụng |
| learning_resource_type | Có | Textbook, presentation, handout, lab... |
| teaches | Không | Chuẩn đầu ra hoặc năng lực được dạy |
| learning_objectives | Không | Mục tiêu học tập liên quan |
| prerequisite_topics | Không | Kiến thức tiên quyết |
| syllabus_unit | Không | Chương/tuần/chủ đề trong đề cương |
| intended_audience | Có | student, lecturer hoặc cả hai |

## 4. Provenance và version

| Field | Bắt buộc | Ý nghĩa |
|---|---:|---|
| source | Có | Nguồn nhận tài liệu |
| owner | Có | Người chịu trách nhiệm hiện tại |
| version | Có | Phiên bản nghiệp vụ |
| supersedes | Không | Document version bị thay thế |
| effective_from | Có | Bắt đầu có hiệu lực |
| effective_until | Không | Hết hiệu lực |
| created_at | Có | Ngày tạo nếu biết |
| modified_at | Có | Ngày sửa cuối |
| received_at | Có | Ngày trung tâm nhận |
| checksum | Có sau ingest | Dấu vết file vật lý |
| provenance_note | Không | Lịch sử hoặc vấn đề nguồn gốc |

## 5. Rights và access

| Field | Bắt buộc | Ý nghĩa |
|---|---:|---|
| rights_status | Có | clear, restricted hoặc unknown |
| license_or_permission | Có | URI/văn bản/quyết định cho phép |
| sensitivity | Có | Mức nhạy cảm |
| allowed_roles | Có | Role được phép đọc |
| allowed_courses | Có | Course scope |
| allowed_terms | Có | Term scope hoặc `all_valid_terms` |
| allowed_cohorts | Không | Lớp/cohort nếu cần |
| download_allowed | Có | Cho phép tải file gốc hay chỉ xem |
| quote_allowed | Có | Có được đưa đoạn trích vào câu trả lời không |

`rights_status = unknown` hoặc thiếu access scope đồng nghĩa với không được index vào production retrieval.

## 6. Lifecycle và review

| Field | Bắt buộc | Ý nghĩa |
|---|---:|---|
| lifecycle_status | Có | draft, in_review, published, archived... |
| submitted_by | Khi review | Người gửi duyệt |
| reviewed_by | Khi review | Người phê duyệt/từ chối |
| reviewed_at | Khi review | Thời điểm review |
| review_decision | Khi review | approved, rejected, changes_requested |
| next_review_at | Khi publish | Lịch review lại |
| retirement_reason | Khi archive | Lý do ngừng sử dụng |

## 7. Technical extraction

| Field | Bắt buộc | Ý nghĩa |
|---|---:|---|
| file_name | Có | Tên file gốc; không dùng làm ID |
| media_type | Có | MIME type |
| file_size | Có | Byte |
| page_slide_count | Có | Số trang/slide hiển thị |
| text_layer | Có | native, OCR, mixed, none |
| parser_profile | Khi ingest | Parser/OCR configuration version |
| extraction_quality | Khi ingest | pass, warn, fail |
| reading_order_quality | Khi ingest | pass, warn, fail |
| table_formula_quality | Nếu có | pass, warn, fail |

## 8. Chunk và citation metadata

Mỗi chunk phải kế thừa access metadata và có thêm:

- chunk_id.
- document_id và document_version.
- page_number/slide_number.
- section_path và heading.
- chunk_sequence.
- character/token offsets nếu khả dụng.
- evidence_text_hash.
- access scope đã chuẩn hóa.
- source locator để giao diện mở đúng vị trí.

Không cho phép chunk thiếu `document_id`, version hoặc page/slide đi vào production index.

## 9. Nguồn chuẩn tham khảo

- [DCMI Metadata Terms](https://www.dublincore.org/specifications/dublin-core/dcmi-terms/)
- [Schema.org LearningResource](https://schema.org/LearningResource)
- [Schema.org learningResourceType](https://schema.org/learningResourceType)
- [1EdTech LTI Resource Search](https://www.1edtech.org/standards/lti-rs/intro)

