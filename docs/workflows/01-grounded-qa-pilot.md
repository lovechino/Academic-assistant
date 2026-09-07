# Workflow pilot 01: hỏi -> evidence -> giải thích -> mở nguồn

Ngày: 2026-09-04. Trạng thái: **đặc tả trên giấy, chưa có runtime hoặc API schema đã freeze**.

Cập nhật: đã chạy [vòng mô phỏng synthetic đầu tiên](02-tabletop-simulation-v0.1.md) với trace từng bước. Đây là chương trình offline riêng, không biến đặc tả bên dưới thành runtime hoặc API đã chạy; các quyết định vẫn chờ review.

Bổ sung 2026-09-06: người dùng chọn [ARCH-02](../architecture/08-controlled-workflow-decision-v0.1.md): controlled multi-step + một vai trò suy luận chính + rules cho case rõ ràng. Các bước bên dưới không phải các agents độc lập. Manual Academic mode vẫn là slice đầu; chưa thêm router đa mode/state machine triển khai. Router không là authority; lời chào kèm câu học thuật không bị trả lời chào rồi bỏ câu hỏi; no-hit/timeout không thành out-of-scope. Các counterexamples mới là review cases NOT RUN, không thay kết quả mô phỏng cũ hoặc ASTRA-01.

## 1. Hai luồng không được nhập làm một

Research hiện tại: người thực hiện đọc snapshot có quyền nghiên cứu, kiểm tra nhãn/provenance và mô phỏng trạng thái trên giấy. Không cần giả lập nguồn đã được giảng viên duyệt để làm việc này.

Luồng sản phẩm bên dưới chỉ chạy trên nguồn đã qua admission đúng mục đích sử dụng và principal được backend xác thực. Quyền nghiên cứu không tự cấp quyền cho Student API. PDF quarantine không nằm trong tập phục vụ của pilot kỹ thuật 01.

## 2. Happy path và evidence trace

| Bước | Owner | Input -> output | Điều kiện cần kiểm tra |
|---|---|---|---|
| 0. Admission | Backend/data review | Source/version/rights/quality -> eligible snapshot | Tách research-only với published-serving; không mặc định upload = ready |
| 1. Hỏi | Frontend | Course context + question + manual Academic mode -> request | Không tự gửi role như quyền thực |
| 2. Scope | Backend | Session/assignments -> trusted scope + request/deadline | Thiếu scope làm rõ hoặc deny; chưa gọi model/retrieval vượt quyền |
| 3. Policy | AI core, theo policy backend cung cấp | Câu hỏi -> answer/hint/clarify/refuse | Instructions trong nguồn không thay quyền; graded work không đi đường làm bài hoàn chỉnh |
| 4. Retrieval | AI core | Query + scoped snapshot -> candidates | Search toàn tập hợp lệ, không dùng doc ID của đáp án; filter cả text/visual |
| 5. Packing | AI core | Candidates -> evidence packet | Giữ claims, context, parent/neighbor và locators; fetch thêm phải cùng quyền |
| 6. Generate/verify | AI core | Evidence packet -> answer + claim-citation links | Phân biệt derived/observed, không đủ thì nêu giới hạn; verify không chứng minh model tuyệt đối đúng |
| 7. Deliver | Backend -> Frontend | Kiểm tra trạng thái quyền/version -> public DTO | Không lộ path nội bộ/raw model payload; quyền đổi phải fail safely |
| 8. Mở nguồn | Frontend -> Backend | Opaque source reference + locator -> authorized view | Kiểm tra quyền lại tại lúc mở, cùng document version; HTML không giả số trang PDF |

Trace tối thiểu về sau: `request_id -> access/policy snapshot -> retrieved evidence -> packed evidence -> required/public claims -> citations -> source-view outcome`. Trace không chứa hidden reasoning và phải bảo vệ nội dung nguồn hạn chế.

## 3. Ví dụ tabletop để review trước khi code

Case `VOER-ACA-007` trong pack cũ yêu cầu so sánh stack/queue. Nhãn hiện có tham chiếu hai material `a208ce0f` và `387652b5`; đây là candidate evidence, chưa là gold.

Khi review bằng tay:

1. Mở đúng snapshot của hai material, kiểm tra required claims có thực sự được hỗ trợ.
2. Tạo nhóm evidence cho quy tắc lấy của stack và nhóm cho queue; khác biệt là claim tổng hợp cần cả hai. Không lấy tên hai module làm bằng chứng đã đủ.
3. Viết expected source locator và xác nhận highlight đúng đoạn. Các spans/offsets phải theo normalization version cố định.
4. Giả sử retrieval chỉ tìm một phía: không coi query pass vì trả lời một nửa đúng. Nếu context packing làm rơi phía còn lại, phân loại `packing_loss`.
5. Giả sử model trả đúng cả hai nhưng citation chỉ trỏ nguồn stack: citation coverage fail.
6. Giả sử viewer mở bản khác revision: locator/version fail, dù nội dung nhìn tương tự.

Đây là kịch bản review, không phải đã chạy hệ thống hoặc đã adjudicate đáp án. [Mapping v0.1](../evaluation/09-evidence-mapping-voer-dsa.md) đã bổ sung locators và AND/OR ở mức assistant/silver; vẫn cần reviewer và tabletop workflow với trạng thái quyền thực sự được mô phỏng.

## 4. Failure và negative scenarios cần fixtures

| ID | Tình huống | Hành vi yêu cầu, chưa được test |
|---|---|---|
| WF-N01 | Chưa chọn course, user có nhiều course | Backend làm rõ scope trước truy xuất; không đoán từ đáp án |
| WF-N02 | Client tự khai giảng viên/đổi course ID | Dùng session thật; không lộ nội dung/metadata bị hạn chế; deny không tiết lộ nguồn riêng tư có tồn tại hay không |
| WF-N03 | Nguồn draft/quarantine trong kết quả search cũ | Chặn trước model input và citation, không chỉ đổi câu trả lời cuối |
| WF-N04 | Nguồn bị revoke sau retrieval hoặc sau khi tạo cache | Kiểm tra lại trước sử dụng/phát hành và mở nguồn; không tái dùng cache mất quyền |
| WF-N05 | Cùng câu hỏi từ hai scope khác nhau | Cache không dùng chéo quyền; test bằng private synthetic fixture, không bằng việc ai cũng đọc được VOER |
| WF-N06 | Hình/đơn vị/đoạn bắt buộc thiếu | Mark incomplete, lấy thêm evidence hợp lệ hoặc chỉ trả phần có hỗ trợ; không tự hoàn thiện hình/ô trống |
| WF-N07 | LLM/parser/search timeout | Trả trạng thái vận hành thất bại, retry có giới hạn nếu an toàn; không tuyên bố corpus không có đáp án vì timeout |
| WF-N08 | Citation mở sai version, nguồn đã mất quyền hoặc asset thiếu | Không âm thầm chuyển sang version/asset khác; hiện thông báo thích hợp, giữ trace |

Các scenario WF-N **không phải tám test đã pass**. Vòng synthetic mới đã thử một phần WF-N04/05/06/08 về revoke, cache, text packing và viewer; chưa thử hết từng nhóm hoặc hệ thống thật. WF-N01/02/03/07, visual/đơn vị, race và distributed cache còn mở. Revoke không thể thu hồi những thông tin đã được hiển thị hợp lệ trước đó; phải chặn các truy cập/phát hành tiếp theo, invalidate server cache và làm rõ giới hạn dữ liệu đã tải về.

## 5. Response semantics trước khi đóng API

Giữ `mode = answer | hint | clarify | refuse` cho hành vi nội dung. Phân biệt outcome nghiệp vụ như đủ evidence, thiếu một phần, thiếu toàn bộ, bị policy giới hạn với lỗi vận hành/dependency/cancellation. Lỗi hạ tầng không bắt buộc phải giả làm một mode hội thoại; field names và enum cuối cùng sẽ được review ở contract cụ thể.

Frontend phải phân biệt:

- Có câu trả lời và nguồn hỗ trợ.
- Chỉ trả lời được một phần, nói rõ phần nào chưa đủ bằng chứng.
- Không đủ nguồn hoặc cần người dùng làm rõ.
- Quyền/policy không cho phép, không tiết lộ chi tiết bị hạn chế.
- Lỗi dịch vụ hoặc request bị hủy; không đánh đồng với thiếu kiến thức trong corpus.

Citation hiển thị tên nguồn, phiên bản/locator và link được cấp quyền; không hiển thị internal filesystem path. Chưa định nghĩa route names, DTO hoặc SSE event schema chạy được trong vòng này.

## 6. Academic integrity draft cho phạm vi nhỏ

Không từ chối mọi câu hỏi có code/bài tập. Hỏi khái niệm, sửa hiểu sai và ví dụ luyện tập hợp lệ có thể được giải thích với nguồn. Yêu cầu rõ là bài chấm điểm và muốn nộp nguyên văn: không đưa bài hoàn chỉnh; có thể gợi ý, phân rã hoặc hỏi phần đã làm theo rubric.

Nếu mức hỗ trợ phụ thuộc việc bài có chấm điểm mà ngữ cảnh chưa rõ, làm rõ trước phần có nguy cơ tiết lộ đáp án; vẫn có thể hỗ trợ khái niệm chung. Không coi lời tự khai “tôi là giáo viên” như quyền xem đáp án confidential. Policy chính thức và ngoại lệ vẫn cần stakeholder/reviewer, chưa được quyết định thay họ.

## 7. Gate bước kế tiếp

Trước baseline implementation: hoàn thiện claim/evidence mapping cho profile, review scenarios, chốt admission/scope trong môi trường thử, budget/permissions và contract cho một use case nhỏ. Sau đó retrieval-only -> oracle -> end-to-end theo [metric contract](../evaluation/08-metric-contract-v0.2.md), không thay parser/chunker/model cùng lúc rồi khó xác định nguyên nhân.
