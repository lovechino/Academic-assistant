# Data catalog và phiếu kiểm kê v0.1

Ngày cập nhật: 2026-09-04

Trạng thái: khung hoàn tất; đã có pilot corpus công khai ở mức `research_reference`, chưa có corpus nội bộ được phê duyệt.

## 1. Phạm vi catalog

Catalog quản lý tài liệu ở cấp logical document. Một tài liệu có thể có nhiều phiên bản và nhiều file vật lý, nhưng phải có một `document_id` ổn định.

Các loại tài liệu dự kiến:

- Giáo trình.
- Slide bài giảng.
- Đề cương môn học.
- Tài liệu tham khảo.
- Hướng dẫn thực hành/lab.
- Bài đọc bổ sung.
- FAQ hoặc hướng dẫn học tập do giảng viên phê duyệt.

Đề thi, bài kiểm tra và đáp án được quản lý như loại nhạy cảm riêng; mặc định không publish cho Student Assistant.

## 2. Phiếu kiểm kê cấp môn

| Trường | Giá trị cần điền |
|---|---|
| course_id | Mã môn ổn định |
| course_title | Tên môn chính thức |
| department | Đơn vị phụ trách |
| term_scope | Học kỳ/năm áp dụng |
| content_owner | Người chịu trách nhiệm nội dung |
| backup_reviewer | Người review thay thế |
| languages | vi, en hoặc mixed |
| estimated_documents | Số logical documents |
| estimated_pages/slides | Quy mô gần đúng |
| dominant_formats | PDF, PPTX, DOCX, image... |
| scan_ratio | Tỷ lệ tài liệu cần OCR |
| sensitive_content | Có đề thi, đáp án, PII hoặc nội dung hạn chế không? |
| rights_status | clear, restricted, unknown |
| candidate_status | proposed, assessed, selected, rejected |

## 3. Phiếu kiểm kê cấp tài liệu

| Trường | Bắt buộc | Mô tả |
|---|---|---|
| document_id | Có | ID bất biến, không lấy file name làm ID |
| title | Có | Tên hiển thị |
| document_type | Có | Controlled vocabulary |
| course_id | Có | Môn sở hữu hoặc sử dụng |
| owner | Có | Content owner |
| current_version | Có | Phiên bản nghiệp vụ |
| effective_term | Có | Học kỳ/năm tài liệu có hiệu lực |
| language | Có | BCP 47 như `vi`, `en`, `vi-en` |
| source | Có | Nguồn gốc tài liệu |
| rights_status | Có | clear, restricted, unknown |
| access_scope | Có | Role/course/cohort được xem |
| lifecycle_status | Có | draft, in_review, published, archived |
| file_format | Có | MIME type/extension |
| page_or_slide_count | Có | Số trang/slide người dùng nhìn thấy |
| is_scanned | Có | yes, no, mixed |
| contains_tables | Có | yes/no |
| contains_formulas | Có | yes/no |
| contains_sensitive_material | Có | yes/no và loại |
| checksum | Khi ingest | Dùng cố định snapshot và phát hiện file đổi |
| reviewer | Khi review | Người phê duyệt |
| review_date | Khi review | Thời điểm review |
| notes | Không | Vấn đề về chất lượng hoặc sử dụng |

## 4. Inventory table

| document_id | title | type | course | owner | version | term | language | rights | access | status | scan | tables/formulas | sensitivity | notes |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| `voer-fe7df99c` | Cấu trúc dữ liệu và giải thuật | textbook | `cau-truc-du-lieu-va-giai-thuat` | Internal owner: unassigned; source attribution: Khoa CNTT ĐHSP KT Hưng Yên | snapshot `2026-09-04-r1` | unknown/currentness unverified | vi | clear for attributed reference; no model training | research sandbox | in_review | no | yes/yes | public | 16 module; source dates 2013; 69/69 images |
| `voer-d11e79e2` | Cơ sở dữ liệu | textbook | `co-so-du-lieu` | Internal owner: unassigned; source attribution: Ths. Phạm Hoàng Nhung | snapshot `2026-09-04-r1` | unknown/currentness unverified | vi | clear for attributed reference; no model training | research sandbox | in_review | no | yes/yes | public | 7 module; source dates 2013; missing 7/95 images |
| `voer-87a7b424` | Kinh tế học vi mô | textbook | `kinh-te-hoc-vi-mo` | Internal owner: unassigned; source attribution: PGS., TS. Lê Thế Giới | snapshot `2026-09-04-r1` | unknown/currentness unverified | vi | clear for attributed reference; no model training | research sandbox | in_review | no | no/yes | public | 11 module; source dates 2013; 1/1 image |

Ba dòng trên là collection-level inventory. Manifest cấp module nằm tại `data/raw/voer/module-manifest.csv`.

## 5. Controlled vocabularies ban đầu

### document_type

`textbook`, `lecture_slide`, `syllabus`, `reference`, `lab_guide`, `supplementary_reading`, `faq`, `assessment`, `answer_key`, `other`.

### rights_status

- `clear`: được phép ingest và phục vụ cho các role đã chỉ định.
- `restricted`: được phép lưu nhưng chỉ một phạm vi cụ thể được sử dụng.
- `unknown`: chưa được ingest vào production corpus.

### lifecycle_status

`draft`, `in_review`, `published`, `archived`, `rejected`, `quarantined`.

### sensitivity

`public`, `internal`, `restricted_course`, `assessment_confidential`, `personal_data`.

## 6. Data quality dimensions

Mỗi tài liệu được chấm `pass/warn/fail` theo:

- Provenance rõ ràng.
- Phiên bản và kỳ áp dụng rõ ràng.
- Quyền sử dụng rõ ràng.
- Đọc được bằng mắt.
- Text extraction/OCR đủ chất lượng.
- Page/slide numbering ổn định.
- Không chứa dữ liệu ngoài phạm vi.
- Metadata bắt buộc đầy đủ.
- Không trùng hoặc mâu thuẫn với bản chính thức mà không được đánh dấu.

Tài liệu có `fail` ở rights, owner, access scope hoặc sensitivity không được publish.

## 7. Corpus snapshot

Mỗi lần đánh giá phải ghi:

- Snapshot ID.
- Danh sách `document_id + version + checksum`.
- Ngày hiệu lực.
- Người phê duyệt.
- Tài liệu thêm, thay thế hoặc loại bỏ so với snapshot trước.

Không ghi KPI mà không nêu corpus snapshot vì câu trả lời đúng có thể thay đổi khi tài liệu đổi phiên bản.
