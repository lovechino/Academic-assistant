# Permission matrix v0.1

Ngày cập nhật: 2026-09-04

Phạm vi: bảng role/action khởi đầu cho một trường/course. Với multi-tenant, external organization, free user và agent capability, tài liệu này phải được đọc cùng [kiến trúc phân quyền Zero Trust đa tổ chức v0.1](03-multi-tenant-zero-trust-authorization.md) và [authorization context contract](../../contracts/authorization-context.md). RBAC trong bảng dưới không đứng một mình để cấp quyền runtime.

## 1. Nguyên tắc

- Default deny: thiếu rule cho phép thì từ chối.
- Quyền đọc nội dung và quyền quản trị hệ thống là hai việc khác nhau.
- Mọi retrieval filter theo quyền trước khi lấy chunk hoặc tạo prompt cho LLM.
- Cache key phải bao gồm access scope và corpus snapshot.
- Không dùng prompt để bảo vệ tài liệu; enforcement phải diễn ra ở tầng dữ liệu/retrieval.
- Tài liệu `draft`, `in_review`, `rejected`, `archived` hoặc `quarantined` không xuất hiện với sinh viên.

## 2. Logical roles

- **Student:** người học thuộc course/cohort hợp lệ.
- **Lecturer Contributor:** giảng viên được upload và chỉnh draft của môn được phân công.
- **Course Owner/Approver:** chịu trách nhiệm phê duyệt nội dung một môn.
- **Knowledge Curator:** kiểm tra metadata, quyền, chất lượng và quản lý Hub.
- **System Administrator:** quản lý kỹ thuật, tài khoản và cấu hình; không mặc định có quyền đọc mọi nội dung học thuật hạn chế.

MVP có thể chỉ hiển thị hai nhóm người dùng “Sinh viên/Giảng viên”, nhưng quyền backend nên được phân rã theo các logical role trên để tránh cấp quyền quá rộng.

## 3. Action matrix

Ký hiệu: `Y` cho phép, `S` chỉ trong scope được giao, `N` không cho phép, `A` chỉ khi được cấp quyền đặc biệt và có audit.

| Action | Student | Lecturer Contributor | Course Owner | Curator | System Admin |
|---|:---:|:---:|:---:|:---:|:---:|
| Tìm/xem published document | S | S | S | S | A |
| Hỏi Assistant trên published corpus | S | S | S | S | A |
| Tải file gốc | S nếu document cho phép | S | S | S | A |
| Upload tài liệu | N | S | S | S | N |
| Sửa metadata draft | N | S | S | S | N |
| Gửi tài liệu đi review | N | S | S | S | N |
| Approve/publish | N | N | S | S theo assignment | N |
| Reject/request changes | N | N | S | S theo assignment | N |
| Archive/restore | N | N | S | S | N |
| Xem assessment confidential | N | A | S | A | A |
| Quản lý user-role assignment | N | N | N | N | Y |
| Thay đổi policy hệ thống | N | N | N | N | Y |
| Xem audit nghiệp vụ | N | S của bản thân | S theo course | S | Y metadata kỹ thuật |

## 4. Resource scope

Quyền hiệu lực là giao của các điều kiện; trong kiến trúc multi-tenant còn bắt buộc active tenant, resource relation, action, purpose, policy revision và agent/tool capability:

`tenant ∩ role ∩ relation ∩ action ∩ purpose ∩ course ∩ term ∩ cohort ∩ document status ∩ sensitivity ∩ current capability`, sau đó áp `explicit deny`.

Ví dụ: Student có role hợp lệ nhưng không thuộc course của tài liệu vẫn không được retrieve chunk. Giảng viên thuộc course nhưng tài liệu assessment confidential vẫn cần quyền đặc biệt.

## 5. Decision order

1. Xác thực user/session.
2. Lấy role assignments còn hiệu lực.
3. Xác định course/term/cohort scope.
4. Áp dụng explicit deny và sensitivity rules.
5. Chỉ retrieval trên tập document/chunk còn lại.
6. Kiểm tra lại source IDs trước khi generation và trước khi trả citation.
7. Ghi audit cho deny, privileged access và thay đổi quyền.

## 6. Test cases tối thiểu

- Student của Course A hỏi chính xác tiêu đề tài liệu Course B.
- Student đổi course ID trong URL/query.
- Lecturer upload draft rồi thử hỏi Assistant trước khi publish.
- Tài liệu bị archive nhưng chunk vẫn còn trong vector index cũ.
- Cache được tạo bởi lecturer rồi student gửi cùng câu hỏi.
- Prompt yêu cầu model bỏ qua quyền hoặc in hidden context.
- User có nhiều role với term hết hạn khác nhau.
- Citation ID hợp lệ về hình thức nhưng thuộc tài liệu không được phép.
- System admin thử đọc nội dung restricted mà không có content-access grant.

Mọi case unauthorized retrieval/citation phải đạt 100% deny.

## 7. Nguồn tham khảo

Thiết kế role-permission tham khảo mô hình RBAC của NIST, trong đó quyền được cấp qua role và giao dịch phải được role cho phép:

- [NIST Role-Based Access Control](https://csrc.nist.gov/Projects/role-based-access-control/faqs)
- [A Revised Model for Role-Based Access Control](https://www.nist.gov/publications/revised-model-role-based-access-control)
