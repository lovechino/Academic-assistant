# Mô phỏng workflow QA v0.1 — kết quả từng bước

Ngày chạy: 2026-09-04. **Đã chạy offline bằng state machine và generator stub**, không chỉ viết expected behavior. Chưa có Backend/Frontend/AI agent thật, không gọi LLM/network hoặc sửa corpus/nhãn VOER.

## 1. Cách đọc kết quả

- Câu hỏi giả lập: “So sánh nguyên tắc lấy phần tử của stack và queue.”
- Hai nhóm evidence: stack/LIFO và queue/FIFO. Ba ý phải trả lời: stack, queue, so sánh cả hai.
- Hai tài liệu hoàn toàn synthetic: stack cho lớp A/B; queue chỉ cho lớp A. Hai actor synthetic; không giả mạo giảng viên phê duyệt nguồn thật.
- Nội dung fixture được viết mới, chỉ mượn hình dạng yêu cầu của ACA-007. Không tải nguồn thật vào simulator hoặc biến research-only thành published.
- PASS nghĩa là **hành vi quan sát khớp kỳ vọng đã viết cho fixture**, không có nghĩa câu hỏi đã được trả lời đủ hay hệ thống thật an toàn. Một lần chặn đúng có thể PASS logic nhưng không hoàn thành hành trình người dùng.
- “Generator stub” chọn câu trả lời viết sẵn theo evidence. Mọi bộ đếm `generator_stub_calls` chỉ là gọi hàm giả lập; **actual_llm_calls = 0**.
- Các hàng dưới là log hành động/đầu ra có thể quan sát, không phải hidden reasoning.

Tệp chạy: [fixtures](../../data/evaluation/simulations/grounded-qa-tabletop-v0.1/fixtures.json), [kết quả JSON đầy đủ](../../data/evaluation/simulations/grounded-qa-tabletop-v0.1/results.json), [runner và hướng dẫn](../../ai-core/experiments/workflow-tabletop/README.md).

## 2. Tổng hợp, không phải điểm benchmark

11/11 tình huống khớp kỳ vọng; 132 bước được ghi log. Trong 66 hành động truy cập source quan sát ở các lượt baseline, 0 hành động vi phạm quyền theo fixture. Mỗi hành động được tính theo một source ở retrieval, context expansion, model input, delivery hoặc viewer; đây không phải số HTTP request hoặc chứng nhận RBAC.

Kết quả hành trình: **3 đủ câu trả lời và mở nguồn; 3 trả lời một phần; 3 chặn trước phát answer; 2 đã phát answer nhưng mở nguồn sau đó bị chặn**. Không tính những con số này thành GAP của 10 câu silver: đây là tập tình huống cố ý tạo lỗi, không phải mẫu benchmark.

| ID | Tình huống | Evidence retrieval → packed đầu → cuối | Answer gửi ra | Viewer | Logic |
|---|---|---|---|---|---|
| SIM-01 | Luồng bình thường | 2/2 → 2/2 → 2/2 | Đủ 3/3 ý | Mở đúng nguồn | Khớp kỳ vọng |
| SIM-02 | Packing cắt mất cuối đoạn queue, sửa được | 2/2 → 1/2 → 2/2 | Đủ 3/3 ý | Mở đúng nguồn | Khớp kỳ vọng |
| SIM-03 | Packing mất đoạn queue, không lấy lại được | 2/2 → 1/2 → 1/2 | Một phần: 1/3 ý | Mở đúng nguồn | Khớp kỳ vọng |
| SIM-04 | Generator stub dẫn sai phiên bản | 2/2 → 2/2 → 2/2 | Chặn: citation sai | Không phát citation | Khớp kỳ vọng |
| SIM-05 | Thu hồi nguồn sau retrieval, trước model input | 2/2 → 2/2 → 2/2 | Chặn: quyền thay đổi | Không phát citation | Khớp kỳ vọng |
| SIM-06 | Thu hồi nguồn sau generation, trước delivery | 2/2 → 2/2 → 2/2 | Chặn: quyền thay đổi | Không phát citation | Khớp kỳ vọng |
| SIM-07 | Cache chưa hết TTL nhưng nguồn đã bị thu hồi | 1/2 → 1/2 → 1/2 | Một phần: 1/3 ý | Mở đúng nguồn | Khớp kỳ vọng |
| SIM-08 | Lớp B hỏi cùng câu, cache thuộc lớp A | 1/2 → 1/2 → 1/2 | Một phần: 1/3 ý | Mở đúng nguồn | Khớp kỳ vọng |
| SIM-09 | Cache dẫn v1 nhưng nguồn hiện hành là v2 | 2/2 → 2/2 → 2/2 | Đủ 3/3 ý | Mở đúng nguồn | Khớp kỳ vọng |
| SIM-10 | Đã nhận câu trả lời, mở citation khi v1 không còn | 2/2 → 2/2 → 2/2 | Đủ 3/3 ý | Chặn: bản cũ không còn | Khớp kỳ vọng |
| SIM-11 | Đã nhận câu trả lời, sau đó nguồn bị thu hồi | 2/2 → 2/2 → 2/2 | Đủ 3/3 ý | Chặn: mất quyền | Khớp kỳ vọng |

Ở SIM-05/SIM-06, packet vẫn có đủ 2/2 nhóm về mặt text; **coverage không thay quyền truy cập**. Chốt quyền chặn sử dụng/phát hành, không giả vờ evidence chưa từng được tìm thấy.

## 3. Trace từng tình huống

Mỗi lượt bắt đầu từ fixture sạch, không kế thừa state lượt trước. Scope/policy/admission là giả định synthetic đã nêu, không phải chức năng production. Những thay đổi nguồn được cài tại ranh giới bước, chưa chạy đồng thời.

### SIM-01 — Luồng bình thường

| Bước | Stage / owner | Kết quả quan sát |
|---:|---|---|
| 1 | Request/scope / Frontend -> Backend giả lập | **ALLOW** — Session fixture xác định actor/course/scope. Không có role tự khai hoặc auth thật. |
| 2 | Policy / AI core giả lập | **ALLOW** — Fixture là câu hỏi khái niệm, cho phép giải thích. Không chạy classifier hay kiểm thử graded-work policy. |
| 3 | Cache / Backend giả lập | **MISS** — Không có cache; đi tiếp retrieval. |
| 4 | Retrieval / AI core giả lập | **COMPLETE** — Retriever stub trả 2/2 nhóm evidence trong scope hiện tại; không đo ranking/search thật. |
| 5 | Packing / AI core giả lập | **COMPLETE** — Context thực chứa 2/2 nhóm đủ span; tên document còn trong packet không bù phần text đã cắt. Độ dài span: 60, 57 codepoint. |
| 6 | Kiểm tra trước model / Backend + AI core giả lập | **ALLOW** — Kiểm tra quyền và revision hiện tại ngay trước model input; chạy tuần tự, chưa kiểm thử race thật. |
| 7 | Generate stub / AI core giả lập | **BUFFERED** — Tạo 3/3 claim từ template cố định; câu trả lời đang giữ trong buffer, chưa gửi cho user. |
| 8 | Verify citation / AI core giả lập | **ALLOW** — Liên kết claim-citation khớp groups và packet; chỉ kiểm tra cấu trúc fixture, không đo semantic entailment. |
| 9 | Delivery / Backend -> Frontend giả lập | **FULL** — Gửi 3/3 claim và citation đã kiểm tra; đủ câu hỏi trong fixture. |
| 10 | Mở nguồn / Backend/source viewer giả lập | **OPEN** — Mở đúng đoạn nguồn giả lập theo revision/hash/span; chưa có UI highlight thật. syn-stack v1, [0,60). |
| 11 | Mở nguồn / Backend/source viewer giả lập | **OPEN** — Mở đúng đoạn nguồn giả lập theo revision/hash/span; chưa có UI highlight thật. syn-queue v1, [0,57). |
| 12 | Đối chiếu kỳ vọng / Observer offline | **PASS** — So sánh trạng thái thực chạy với kỳ vọng fixture và các hành động truy cập quan sát được. |

**Người dùng nhận:** “Stack lấy phần tử đưa vào sau cùng trước. Queue lấy phần tử được đưa vào sớm nhất trước. Stack ưu tiên phần tử mới vào; queue ưu tiên phần tử vào sớm.”

Kết luận: 3/3 ý đã gửi; 1 lần gọi stub; 0 lần repair; lỗi đầu tiên: không có. Khớp expected fixture.

### SIM-02 — Packing cắt mất cuối đoạn queue, sửa được

| Bước | Stage / owner | Kết quả quan sát |
|---:|---|---|
| 1 | Request/scope / Frontend -> Backend giả lập | **ALLOW** — Session fixture xác định actor/course/scope. Không có role tự khai hoặc auth thật. |
| 2 | Policy / AI core giả lập | **ALLOW** — Fixture là câu hỏi khái niệm, cho phép giải thích. Không chạy classifier hay kiểm thử graded-work policy. |
| 3 | Cache / Backend giả lập | **MISS** — Không có cache; đi tiếp retrieval. |
| 4 | Retrieval / AI core giả lập | **COMPLETE** — Retriever stub trả 2/2 nhóm evidence trong scope hiện tại; không đo ranking/search thật. |
| 5 | Packing / AI core giả lập | **INCOMPLETE** — Context thực chứa 1/2 nhóm đủ span; tên document còn trong packet không bù phần text đã cắt. Độ dài span: 60, 28 codepoint. |
| 6 | Repair context / AI core giả lập | **RECOVERED** — Thử lại đúng một lần có lọc quyền: khôi phục đủ 2/2 nhóm. |
| 7 | Kiểm tra trước model / Backend + AI core giả lập | **ALLOW** — Kiểm tra quyền và revision hiện tại ngay trước model input; chạy tuần tự, chưa kiểm thử race thật. |
| 8 | Generate stub / AI core giả lập | **BUFFERED** — Tạo 3/3 claim từ template cố định; câu trả lời đang giữ trong buffer, chưa gửi cho user. |
| 9 | Verify citation / AI core giả lập | **ALLOW** — Liên kết claim-citation khớp groups và packet; chỉ kiểm tra cấu trúc fixture, không đo semantic entailment. |
| 10 | Delivery / Backend -> Frontend giả lập | **FULL** — Gửi 3/3 claim và citation đã kiểm tra; đủ câu hỏi trong fixture. |
| 11 | Mở nguồn / Backend/source viewer giả lập | **OPEN** — Mở đúng đoạn nguồn giả lập theo revision/hash/span; chưa có UI highlight thật. syn-stack v1, [0,60). |
| 12 | Mở nguồn / Backend/source viewer giả lập | **OPEN** — Mở đúng đoạn nguồn giả lập theo revision/hash/span; chưa có UI highlight thật. syn-queue v1, [0,57). |
| 13 | Đối chiếu kỳ vọng / Observer offline | **PASS** — So sánh trạng thái thực chạy với kỳ vọng fixture và các hành động truy cập quan sát được. |

**Người dùng nhận:** “Stack lấy phần tử đưa vào sau cùng trước. Queue lấy phần tử được đưa vào sớm nhất trước. Stack ưu tiên phần tử mới vào; queue ưu tiên phần tử vào sớm.”

Kết luận: 3/3 ý đã gửi; 1 lần gọi stub; 1 lần repair; lỗi đầu tiên: packing_loss. Khớp expected fixture.

### SIM-03 — Packing mất đoạn queue, không lấy lại được

| Bước | Stage / owner | Kết quả quan sát |
|---:|---|---|
| 1 | Request/scope / Frontend -> Backend giả lập | **ALLOW** — Session fixture xác định actor/course/scope. Không có role tự khai hoặc auth thật. |
| 2 | Policy / AI core giả lập | **ALLOW** — Fixture là câu hỏi khái niệm, cho phép giải thích. Không chạy classifier hay kiểm thử graded-work policy. |
| 3 | Cache / Backend giả lập | **MISS** — Không có cache; đi tiếp retrieval. |
| 4 | Retrieval / AI core giả lập | **COMPLETE** — Retriever stub trả 2/2 nhóm evidence trong scope hiện tại; không đo ranking/search thật. |
| 5 | Packing / AI core giả lập | **INCOMPLETE** — Context thực chứa 1/2 nhóm đủ span; tên document còn trong packet không bù phần text đã cắt. Độ dài span: 60, 28 codepoint. |
| 6 | Repair context / AI core giả lập | **PARTIAL** — Thử lại đúng một lần có lọc quyền: vẫn chỉ 1/2 nhóm; không bù từ model memory. |
| 7 | Kiểm tra trước model / Backend + AI core giả lập | **ALLOW** — Kiểm tra quyền và revision hiện tại ngay trước model input; chạy tuần tự, chưa kiểm thử race thật. |
| 8 | Generate stub / AI core giả lập | **BUFFERED** — Tạo 1/3 claim từ template cố định; câu trả lời đang giữ trong buffer, chưa gửi cho user. |
| 9 | Verify citation / AI core giả lập | **ALLOW** — Liên kết claim-citation khớp groups và packet; chỉ kiểm tra cấu trúc fixture, không đo semantic entailment. |
| 10 | Delivery / Backend -> Frontend giả lập | **PARTIAL** — Gửi 1/3 claim và citation đã kiểm tra; ghi rõ phần thiếu, không tính hoàn thành câu hỏi. |
| 11 | Mở nguồn / Backend/source viewer giả lập | **OPEN** — Mở đúng đoạn nguồn giả lập theo revision/hash/span; chưa có UI highlight thật. syn-stack v1, [0,60). |
| 12 | Đối chiếu kỳ vọng / Observer offline | **PASS** — So sánh trạng thái thực chạy với kỳ vọng fixture và các hành động truy cập quan sát được. |

**Người dùng nhận:** “Stack lấy phần tử đưa vào sau cùng trước. Chưa đủ bằng chứng được phép sử dụng để giải thích queue và hoàn tất so sánh.”

Kết luận: 1/3 ý đã gửi; 1 lần gọi stub; 1 lần repair; lỗi đầu tiên: packing_loss. Khớp expected fixture.

### SIM-04 — Generator stub dẫn sai phiên bản

| Bước | Stage / owner | Kết quả quan sát |
|---:|---|---|
| 1 | Request/scope / Frontend -> Backend giả lập | **ALLOW** — Session fixture xác định actor/course/scope. Không có role tự khai hoặc auth thật. |
| 2 | Policy / AI core giả lập | **ALLOW** — Fixture là câu hỏi khái niệm, cho phép giải thích. Không chạy classifier hay kiểm thử graded-work policy. |
| 3 | Cache / Backend giả lập | **MISS** — Không có cache; đi tiếp retrieval. |
| 4 | Retrieval / AI core giả lập | **COMPLETE** — Retriever stub trả 2/2 nhóm evidence trong scope hiện tại; không đo ranking/search thật. |
| 5 | Packing / AI core giả lập | **COMPLETE** — Context thực chứa 2/2 nhóm đủ span; tên document còn trong packet không bù phần text đã cắt. Độ dài span: 60, 57 codepoint. |
| 6 | Kiểm tra trước model / Backend + AI core giả lập | **ALLOW** — Kiểm tra quyền và revision hiện tại ngay trước model input; chạy tuần tự, chưa kiểm thử race thật. |
| 7 | Generate stub / AI core giả lập | **BUFFERED** — Tạo 3/3 claim từ template cố định; câu trả lời đang giữ trong buffer, chưa gửi cho user. |
| 8 | Verify citation / AI core giả lập | **BLOCK** — Revision citation không khớp evidence packet; loại toàn bộ bản nháp, không phát citation sai. |
| 9 | Delivery/viewer / Backend giả lập | **SKIP** — Chỉ gửi thông báo lỗi kiểm chứng; không có citation để mở. |
| 10 | Đối chiếu kỳ vọng / Observer offline | **PASS** — So sánh trạng thái thực chạy với kỳ vọng fixture và các hành động truy cập quan sát được. |

**Người dùng nhận:** “Chưa xác minh được trích dẫn cho câu trả lời này. Vui lòng thử lại.”

Kết luận: 0/3 ý đã gửi; 1 lần gọi stub; 0 lần repair; lỗi đầu tiên: citation_support. Khớp expected fixture.

### SIM-05 — Thu hồi nguồn sau retrieval, trước model input

| Bước | Stage / owner | Kết quả quan sát |
|---:|---|---|
| 1 | Request/scope / Frontend -> Backend giả lập | **ALLOW** — Session fixture xác định actor/course/scope. Không có role tự khai hoặc auth thật. |
| 2 | Policy / AI core giả lập | **ALLOW** — Fixture là câu hỏi khái niệm, cho phép giải thích. Không chạy classifier hay kiểm thử graded-work policy. |
| 3 | Cache / Backend giả lập | **MISS** — Không có cache; đi tiếp retrieval. |
| 4 | Retrieval / AI core giả lập | **COMPLETE** — Retriever stub trả 2/2 nhóm evidence trong scope hiện tại; không đo ranking/search thật. |
| 5 | Packing / AI core giả lập | **COMPLETE** — Context thực chứa 2/2 nhóm đủ span; tên document còn trong packet không bù phần text đã cắt. Độ dài span: 60, 57 codepoint. |
| 6 | Sự kiện sau retrieval/packing / Backend giả lập | **EVENT** — Thu hồi nguồn queue; tăng revocation epoch. Không thể thu hồi nội dung đã hiển thị trước đó. |
| 7 | Kiểm tra trước model / Backend + AI core giả lập | **BLOCK** — Nguồn trong packet không còn hợp lệ; hủy request, không đưa packet vào generator stub. |
| 8 | Generate/deliver/viewer / Pipeline giả lập | **SKIP** — Không tạo answer/citation; chỉ trả thông báo chung, không tên nguồn riêng tư. |
| 9 | Đối chiếu kỳ vọng / Observer offline | **PASS** — So sánh trạng thái thực chạy với kỳ vọng fixture và các hành động truy cập quan sát được. |

**Người dùng nhận:** “Quyền hoặc trạng thái tài liệu đã thay đổi. Vui lòng gửi lại yêu cầu.”

Kết luận: 0/3 ý đã gửi; 0 lần gọi stub; 0 lần repair; lỗi đầu tiên: policy_or_access. Khớp expected fixture.

### SIM-06 — Thu hồi nguồn sau generation, trước delivery

| Bước | Stage / owner | Kết quả quan sát |
|---:|---|---|
| 1 | Request/scope / Frontend -> Backend giả lập | **ALLOW** — Session fixture xác định actor/course/scope. Không có role tự khai hoặc auth thật. |
| 2 | Policy / AI core giả lập | **ALLOW** — Fixture là câu hỏi khái niệm, cho phép giải thích. Không chạy classifier hay kiểm thử graded-work policy. |
| 3 | Cache / Backend giả lập | **MISS** — Không có cache; đi tiếp retrieval. |
| 4 | Retrieval / AI core giả lập | **COMPLETE** — Retriever stub trả 2/2 nhóm evidence trong scope hiện tại; không đo ranking/search thật. |
| 5 | Packing / AI core giả lập | **COMPLETE** — Context thực chứa 2/2 nhóm đủ span; tên document còn trong packet không bù phần text đã cắt. Độ dài span: 60, 57 codepoint. |
| 6 | Kiểm tra trước model / Backend + AI core giả lập | **ALLOW** — Kiểm tra quyền và revision hiện tại ngay trước model input; chạy tuần tự, chưa kiểm thử race thật. |
| 7 | Generate stub / AI core giả lập | **BUFFERED** — Tạo 3/3 claim từ template cố định; câu trả lời đang giữ trong buffer, chưa gửi cho user. |
| 8 | Verify citation / AI core giả lập | **ALLOW** — Liên kết claim-citation khớp groups và packet; chỉ kiểm tra cấu trúc fixture, không đo semantic entailment. |
| 9 | Sự kiện sau generation / Backend giả lập | **EVENT** — Thu hồi nguồn queue; tăng revocation epoch. Không thể thu hồi nội dung đã hiển thị trước đó. |
| 10 | Delivery / Backend giả lập | **BLOCK** — Chốt quyền/version cuối phát hiện thay đổi; hủy buffer, không gửi answer/citation hoặc ghi response cache. |
| 11 | Viewer / Frontend giả lập | **SKIP** — Không có citation được phát ra để mở. |
| 12 | Đối chiếu kỳ vọng / Observer offline | **PASS** — So sánh trạng thái thực chạy với kỳ vọng fixture và các hành động truy cập quan sát được. |

**Người dùng nhận:** “Quyền hoặc trạng thái tài liệu đã thay đổi. Vui lòng gửi lại yêu cầu.”

Kết luận: 0/3 ý đã gửi; 1 lần gọi stub; 0 lần repair; lỗi đầu tiên: policy_or_access. Khớp expected fixture.

### SIM-07 — Cache chưa hết TTL nhưng nguồn đã bị thu hồi

| Bước | Stage / owner | Kết quả quan sát |
|---:|---|---|
| 1 | Request/scope / Frontend -> Backend giả lập | **ALLOW** — Session fixture xác định actor/course/scope. Không có role tự khai hoặc auth thật. |
| 2 | Policy / AI core giả lập | **ALLOW** — Fixture là câu hỏi khái niệm, cho phép giải thích. Không chạy classifier hay kiểm thử graded-work policy. |
| 3 | Sự kiện trước đọc cache / Backend giả lập | **EVENT** — Thu hồi nguồn queue; tăng revocation epoch. Không thể thu hồi nội dung đã hiển thị trước đó. |
| 4 | Cache / Backend giả lập | **REJECT** — Cache còn TTL nhưng không hợp lệ; không nạp payload, loại ứng viên khỏi lần đọc và tìm lại theo scope hiện tại. Key khác: revocation_epoch. |
| 5 | Retrieval / AI core giả lập | **INCOMPLETE** — Retriever stub trả 1/2 nhóm evidence trong scope hiện tại; không đo ranking/search thật. |
| 6 | Packing / AI core giả lập | **INCOMPLETE** — Context thực chứa 1/2 nhóm đủ span; tên document còn trong packet không bù phần text đã cắt. Độ dài span: 60 codepoint. |
| 7 | Repair context / AI core giả lập | **PARTIAL** — Thử lại đúng một lần có lọc quyền: vẫn chỉ 1/2 nhóm; không bù từ model memory. |
| 8 | Kiểm tra trước model / Backend + AI core giả lập | **ALLOW** — Kiểm tra quyền và revision hiện tại ngay trước model input; chạy tuần tự, chưa kiểm thử race thật. |
| 9 | Generate stub / AI core giả lập | **BUFFERED** — Tạo 1/3 claim từ template cố định; câu trả lời đang giữ trong buffer, chưa gửi cho user. |
| 10 | Verify citation / AI core giả lập | **ALLOW** — Liên kết claim-citation khớp groups và packet; chỉ kiểm tra cấu trúc fixture, không đo semantic entailment. |
| 11 | Delivery / Backend -> Frontend giả lập | **PARTIAL** — Gửi 1/3 claim và citation đã kiểm tra; ghi rõ phần thiếu, không tính hoàn thành câu hỏi. |
| 12 | Mở nguồn / Backend/source viewer giả lập | **OPEN** — Mở đúng đoạn nguồn giả lập theo revision/hash/span; chưa có UI highlight thật. syn-stack v1, [0,60). |
| 13 | Đối chiếu kỳ vọng / Observer offline | **PASS** — So sánh trạng thái thực chạy với kỳ vọng fixture và các hành động truy cập quan sát được. |

**Người dùng nhận:** “Stack lấy phần tử đưa vào sau cùng trước. Chưa đủ bằng chứng được phép sử dụng để giải thích queue và hoàn tất so sánh.”

Kết luận: 1/3 ý đã gửi; 1 lần gọi stub; 1 lần repair; lỗi đầu tiên: cache_stale_authorization. Khớp expected fixture.

### SIM-08 — Lớp B hỏi cùng câu, cache thuộc lớp A

| Bước | Stage / owner | Kết quả quan sát |
|---:|---|---|
| 1 | Request/scope / Frontend -> Backend giả lập | **ALLOW** — Session fixture xác định actor/course/scope. Không có role tự khai hoặc auth thật. |
| 2 | Policy / AI core giả lập | **ALLOW** — Fixture là câu hỏi khái niệm, cho phép giải thích. Không chạy classifier hay kiểm thử graded-work policy. |
| 3 | Cache / Backend giả lập | **REJECT** — Cache còn TTL nhưng không hợp lệ; không nạp payload, loại ứng viên khỏi lần đọc và tìm lại theo scope hiện tại. Key khác: principal, scope. |
| 4 | Retrieval / AI core giả lập | **INCOMPLETE** — Retriever stub trả 1/2 nhóm evidence trong scope hiện tại; không đo ranking/search thật. |
| 5 | Packing / AI core giả lập | **INCOMPLETE** — Context thực chứa 1/2 nhóm đủ span; tên document còn trong packet không bù phần text đã cắt. Độ dài span: 60 codepoint. |
| 6 | Repair context / AI core giả lập | **PARTIAL** — Thử lại đúng một lần có lọc quyền: vẫn chỉ 1/2 nhóm; không bù từ model memory. |
| 7 | Kiểm tra trước model / Backend + AI core giả lập | **ALLOW** — Kiểm tra quyền và revision hiện tại ngay trước model input; chạy tuần tự, chưa kiểm thử race thật. |
| 8 | Generate stub / AI core giả lập | **BUFFERED** — Tạo 1/3 claim từ template cố định; câu trả lời đang giữ trong buffer, chưa gửi cho user. |
| 9 | Verify citation / AI core giả lập | **ALLOW** — Liên kết claim-citation khớp groups và packet; chỉ kiểm tra cấu trúc fixture, không đo semantic entailment. |
| 10 | Delivery / Backend -> Frontend giả lập | **PARTIAL** — Gửi 1/3 claim và citation đã kiểm tra; ghi rõ phần thiếu, không tính hoàn thành câu hỏi. |
| 11 | Mở nguồn / Backend/source viewer giả lập | **OPEN** — Mở đúng đoạn nguồn giả lập theo revision/hash/span; chưa có UI highlight thật. syn-stack v1, [0,60). |
| 12 | Đối chiếu kỳ vọng / Observer offline | **PASS** — So sánh trạng thái thực chạy với kỳ vọng fixture và các hành động truy cập quan sát được. |

**Người dùng nhận:** “Stack lấy phần tử đưa vào sau cùng trước. Chưa đủ bằng chứng được phép sử dụng để giải thích queue và hoàn tất so sánh.”

Kết luận: 1/3 ý đã gửi; 1 lần gọi stub; 1 lần repair; lỗi đầu tiên: cache_scope_mismatch. Khớp expected fixture.

### SIM-09 — Cache dẫn v1 nhưng nguồn hiện hành là v2

| Bước | Stage / owner | Kết quả quan sát |
|---:|---|---|
| 1 | Request/scope / Frontend -> Backend giả lập | **ALLOW** — Session fixture xác định actor/course/scope. Không có role tự khai hoặc auth thật. |
| 2 | Policy / AI core giả lập | **ALLOW** — Fixture là câu hỏi khái niệm, cho phép giải thích. Không chạy classifier hay kiểm thử graded-work policy. |
| 3 | Sự kiện trước đọc cache / Backend giả lập | **EVENT** — Nguồn queue chuyển v2; fixture không giữ bản v1 có thể mở. Cache/index cũ không được tự coi là hiện hành. |
| 4 | Cache / Backend giả lập | **REJECT** — Cache còn TTL nhưng không hợp lệ; không nạp payload, loại ứng viên khỏi lần đọc và tìm lại theo scope hiện tại. Key khác: catalog_epoch. |
| 5 | Retrieval / AI core giả lập | **COMPLETE** — Retriever stub trả 2/2 nhóm evidence trong scope hiện tại; không đo ranking/search thật. |
| 6 | Packing / AI core giả lập | **COMPLETE** — Context thực chứa 2/2 nhóm đủ span; tên document còn trong packet không bù phần text đã cắt. Độ dài span: 60, 80 codepoint. |
| 7 | Kiểm tra trước model / Backend + AI core giả lập | **ALLOW** — Kiểm tra quyền và revision hiện tại ngay trước model input; chạy tuần tự, chưa kiểm thử race thật. |
| 8 | Generate stub / AI core giả lập | **BUFFERED** — Tạo 3/3 claim từ template cố định; câu trả lời đang giữ trong buffer, chưa gửi cho user. |
| 9 | Verify citation / AI core giả lập | **ALLOW** — Liên kết claim-citation khớp groups và packet; chỉ kiểm tra cấu trúc fixture, không đo semantic entailment. |
| 10 | Delivery / Backend -> Frontend giả lập | **FULL** — Gửi 3/3 claim và citation đã kiểm tra; đủ câu hỏi trong fixture. |
| 11 | Mở nguồn / Backend/source viewer giả lập | **OPEN** — Mở đúng đoạn nguồn giả lập theo revision/hash/span; chưa có UI highlight thật. syn-stack v1, [0,60). |
| 12 | Mở nguồn / Backend/source viewer giả lập | **OPEN** — Mở đúng đoạn nguồn giả lập theo revision/hash/span; chưa có UI highlight thật. syn-queue v2, [0,80). |
| 13 | Đối chiếu kỳ vọng / Observer offline | **PASS** — So sánh trạng thái thực chạy với kỳ vọng fixture và các hành động truy cập quan sát được. |

**Người dùng nhận:** “Stack lấy phần tử đưa vào sau cùng trước. Queue lấy phần tử được đưa vào sớm nhất trước. Stack ưu tiên phần tử mới vào; queue ưu tiên phần tử vào sớm.”

Kết luận: 3/3 ý đã gửi; 1 lần gọi stub; 0 lần repair; lỗi đầu tiên: cache_stale_version. Khớp expected fixture.

### SIM-10 — Đã nhận câu trả lời, mở citation khi v1 không còn

| Bước | Stage / owner | Kết quả quan sát |
|---:|---|---|
| 1 | Request/scope / Frontend -> Backend giả lập | **ALLOW** — Session fixture xác định actor/course/scope. Không có role tự khai hoặc auth thật. |
| 2 | Policy / AI core giả lập | **ALLOW** — Fixture là câu hỏi khái niệm, cho phép giải thích. Không chạy classifier hay kiểm thử graded-work policy. |
| 3 | Cache / Backend giả lập | **MISS** — Không có cache; đi tiếp retrieval. |
| 4 | Retrieval / AI core giả lập | **COMPLETE** — Retriever stub trả 2/2 nhóm evidence trong scope hiện tại; không đo ranking/search thật. |
| 5 | Packing / AI core giả lập | **COMPLETE** — Context thực chứa 2/2 nhóm đủ span; tên document còn trong packet không bù phần text đã cắt. Độ dài span: 60, 57 codepoint. |
| 6 | Kiểm tra trước model / Backend + AI core giả lập | **ALLOW** — Kiểm tra quyền và revision hiện tại ngay trước model input; chạy tuần tự, chưa kiểm thử race thật. |
| 7 | Generate stub / AI core giả lập | **BUFFERED** — Tạo 3/3 claim từ template cố định; câu trả lời đang giữ trong buffer, chưa gửi cho user. |
| 8 | Verify citation / AI core giả lập | **ALLOW** — Liên kết claim-citation khớp groups và packet; chỉ kiểm tra cấu trúc fixture, không đo semantic entailment. |
| 9 | Delivery / Backend -> Frontend giả lập | **FULL** — Gửi 3/3 claim và citation đã kiểm tra; đủ câu hỏi trong fixture. |
| 10 | Sự kiện sau delivery / Backend giả lập | **EVENT** — Nguồn queue chuyển v2; fixture không giữ bản v1 có thể mở. Cache/index cũ không được tự coi là hiện hành. |
| 11 | Mở nguồn / Backend/source viewer giả lập | **OPEN** — Mở đúng đoạn nguồn giả lập theo revision/hash/span; chưa có UI highlight thật. syn-stack v1, [0,60). |
| 12 | Mở nguồn / Backend/source viewer giả lập | **BLOCK** — Bản được trích dẫn không còn khả dụng; không tự mở bản hiện hành hoặc dùng offset cũ. |
| 13 | Đối chiếu kỳ vọng / Observer offline | **PASS** — So sánh trạng thái thực chạy với kỳ vọng fixture và các hành động truy cập quan sát được. |

**Người dùng nhận:** “Stack lấy phần tử đưa vào sau cùng trước. Queue lấy phần tử được đưa vào sớm nhất trước. Stack ưu tiên phần tử mới vào; queue ưu tiên phần tử vào sớm.”

**Khi mở citation queue:** “Bản được trích dẫn không còn khả dụng.” Không tự chuyển sang v2. Lượt mở stack vẫn hợp lệ.

Kết luận: 3/3 ý đã gửi; 1 lần gọi stub; 0 lần repair; lỗi đầu tiên: locator_or_viewer. Khớp expected fixture.

### SIM-11 — Đã nhận câu trả lời, sau đó nguồn bị thu hồi

| Bước | Stage / owner | Kết quả quan sát |
|---:|---|---|
| 1 | Request/scope / Frontend -> Backend giả lập | **ALLOW** — Session fixture xác định actor/course/scope. Không có role tự khai hoặc auth thật. |
| 2 | Policy / AI core giả lập | **ALLOW** — Fixture là câu hỏi khái niệm, cho phép giải thích. Không chạy classifier hay kiểm thử graded-work policy. |
| 3 | Cache / Backend giả lập | **MISS** — Không có cache; đi tiếp retrieval. |
| 4 | Retrieval / AI core giả lập | **COMPLETE** — Retriever stub trả 2/2 nhóm evidence trong scope hiện tại; không đo ranking/search thật. |
| 5 | Packing / AI core giả lập | **COMPLETE** — Context thực chứa 2/2 nhóm đủ span; tên document còn trong packet không bù phần text đã cắt. Độ dài span: 60, 57 codepoint. |
| 6 | Kiểm tra trước model / Backend + AI core giả lập | **ALLOW** — Kiểm tra quyền và revision hiện tại ngay trước model input; chạy tuần tự, chưa kiểm thử race thật. |
| 7 | Generate stub / AI core giả lập | **BUFFERED** — Tạo 3/3 claim từ template cố định; câu trả lời đang giữ trong buffer, chưa gửi cho user. |
| 8 | Verify citation / AI core giả lập | **ALLOW** — Liên kết claim-citation khớp groups và packet; chỉ kiểm tra cấu trúc fixture, không đo semantic entailment. |
| 9 | Delivery / Backend -> Frontend giả lập | **FULL** — Gửi 3/3 claim và citation đã kiểm tra; đủ câu hỏi trong fixture. |
| 10 | Sự kiện sau delivery / Backend giả lập | **EVENT** — Thu hồi nguồn queue; tăng revocation epoch. Không thể thu hồi nội dung đã hiển thị trước đó. |
| 11 | Mở nguồn / Backend/source viewer giả lập | **OPEN** — Mở đúng đoạn nguồn giả lập theo revision/hash/span; chưa có UI highlight thật. syn-stack v1, [0,60). |
| 12 | Mở nguồn / Backend/source viewer giả lập | **BLOCK** — Không thể truy cập nguồn này; không phát title/text/asset mới của nguồn bị chặn. |
| 13 | Đối chiếu kỳ vọng / Observer offline | **PASS** — So sánh trạng thái thực chạy với kỳ vọng fixture và các hành động truy cập quan sát được. |

**Người dùng nhận:** “Stack lấy phần tử đưa vào sau cùng trước. Queue lấy phần tử được đưa vào sớm nhất trước. Stack ưu tiên phần tử mới vào; queue ưu tiên phần tử vào sớm.”

**Khi mở citation queue:** “Không thể truy cập nguồn này.” Không phát thêm nội dung/tên nguồn bị chặn; nội dung đã gửi hợp lệ trước sự kiện không thể thu hồi. Lượt mở stack vẫn hợp lệ.

Kết luận: 3/3 ý đã gửi; 1 lần gọi stub; 0 lần repair; lỗi đầu tiên: policy_or_access. Khớp expected fixture.

## 4. Cố ý bỏ chốt kiểm tra: phép đo có bắt lỗi không?

Chạy lại một scenario với đúng một guard bị bỏ qua, còn observer vẫn đối chiếu live state. Đây là mutation trong chương trình offline; không cố truy cập hệ thống/tài liệu thật.

| Mutation | Scenario | Chốt bị bỏ | Vi phạm thực sự được observer ghi nhận | Phát hiện |
|---|---|---|---|---|
| M-01 | SIM-03 | packing | incomplete_packet_presented_as_full | Có |
| M-02 | SIM-04 | citation | invalid_citation_emitted | Có |
| M-03 | SIM-05 | pre_model | unauthorized_model_input | Có |
| M-04 | SIM-06 | delivery | unauthorized_delivery | Có |
| M-05 | SIM-07 | cache | unauthorized_cache_hydration | Có |
| M-06 | SIM-08 | cache | unauthorized_cache_hydration | Có |
| M-07 | SIM-09 | cache | stale_cache_hydration | Có |
| M-08 | SIM-10 | viewer_version | silent_viewer_version_substitution | Có |
| M-09 | SIM-11 | viewer_auth | unauthorized_viewer | Có |

9/9 mutation được phát hiện. Ví dụ bỏ chốt pre-model ở SIM-05 khiến nguồn đã revoke vào **model input**, dù chốt delivery còn bật và chặn câu trả lời cuối. Vì thế chỉ kiểm tra output cuối sẽ bỏ sót lỗi này. Bỏ validation cache khiến private/stale payload được nạp vào request, dù retrieval mới sau đó vẫn lọc đúng.

Fixtures, simulator và observer do cùng một người/assistant xây, nên đây chưa phải audit độc lập. Mutation chỉ chứng minh các chốt được nêu có thể ảnh hưởng kết quả của chính simulator này; không bao phủ mọi đường bypass.

## 5. Kiểm tra span để không nhầm “có document” với “đủ đoạn”

| Probe | Nhóm expected | Nhóm quan sát | Kết quả |
|---|---:|---:|---|
| adjacent_split_spans_union | 1 | 1 | Đạt |
| one_character_gap | 0 | 0 | Đạt |
| wrong_source_hash | 0 | 0 | Đạt |
| wrong_revision | 0 | 0 | Đạt |
| payload_text_does_not_match_span | 0 | 0 | Đạt |
| duplicate_span_not_double_counted | 1 | 1 | Đạt |
| partial_span_not_complete_evidence | 0 | 0 | Đạt |

SIM-02/SIM-03 giữ cả hai document ID, nhưng cắt đoạn queue từ 57 xuống 28 codepoint; coverage giảm từ 2/2 xuống 1/2. Hai spans liền kề có thể hợp lại thành evidence đầy đủ: **không bắt buộc mọi ý nằm trong cùng một chunk**.

Probe thiếu một ký tự bị coi là chưa phủ trọn theo rule hình học bảo thủ, không khẳng định thiếu bất kỳ ký tự nào cũng làm mất nghĩa. Các spans này thuộc nguồn synthetic rất ngắn; chưa chứng minh parser PDF hoặc bộ đo semantic coverage đúng. Trong sản phẩm chưa có oracle biết sẵn mọi required group của câu hỏi mới; phát hiện thiếu evidence tự động cần được đánh giá riêng.

## 6. Các quyết định đề xuất để cùng review, chưa chốt

| ID | Quy tắc đề xuất | Bằng chứng từ mô phỏng | Đánh đổi / còn cần quyết định |
|---|---|---|---|
| D-01 | Khi thiếu evidence, thử fetch/repack cùng scope một lần; vẫn thiếu thì trả phần có nguồn và nói rõ phần chưa đủ | SIM-02 khôi phục; SIM-03 chỉ 1/3 ý, không được tính trả lời đủ | Một lần là giới hạn fixture, chưa phải retry tối ưu. Người dùng cần chốt có muốn partial answer hay chỉ thông báo thiếu nguồn |
| D-02 | Pilot đầu giữ toàn bộ answer trong buffer đến khi citation và quyền/version cuối hợp lệ | SIM-04/05/06 chặn được phát nội dung lỗi | Chưa stream nội dung học thuật sớm; có thể hiện tiến trình trung tính. Đổi sang streaming đòi hỏi mô hình bảo mật/test riêng |
| D-03 | Không tái dùng cache theo mỗi câu hỏi/TTL; kiểm tra principal/scope, policy, snapshot/revision và quyền hiện tại của mọi dependency trước khi nạp payload | SIM-07/08/09, M-05/06/07 | Baseline đầu có thể chưa bật answer/semantic cache. Metadata kiểm tra ở backend; không lộ cache từ lớp khác cho client; không xóa cache hợp lệ của lớp A chỉ vì lớp B bị miss |
| D-04 | Citation gắn revision/hash/locator; mở chính xác bản cũ chỉ khi còn được lưu và vẫn được phép; thiếu thì báo unavailable | SIM-10, M-08 | Fixture chỉ thử bản cũ KHÔNG còn. Chưa thử historical-version store hoặc cơ chế pin retention; không tự chuyển offset sang bản mới |
| D-05 | Recheck quyền trước model input, trước delivery và khi mở nguồn; cache invalidation là bổ trợ, không thay chốt đọc | SIM-05/06/07/11 | Cần authority/epoch đồng bộ thực; kiểm tra tuần tự chưa đóng được race giữa check và send. Sau delivery không thể “unsee” dữ liệu |
| D-06 | Đo evidence trước/sau packing trên source span và tính cả claim so sánh cần hai phía | SIM-02/03 và span probes | Oracle groups chỉ dùng đánh giá; không đưa đáp án/qrels vào retriever hoặc dùng chúng làm scope sản phẩm |

## 7. Chưa được thử và điểm dừng

- Chưa chạy real LLM, retriever, parser PDF, index, image/visual evidence, cost/latency, token budget thật hoặc đo GAP/RAGAS.
- Chưa có HTTP/auth/session thật, concurrency/TOCTOU, cancellation, streaming bytes, cache phân tán, log redaction, storage purge hay browser cache/download.
- Cache là dependency payload giả lập; chưa mô phỏng valid cache hit/replay, semantic-near-match hoặc physical eviction. Revocation được áp trực tiếp vào state, không chứng minh thời gian propagation.
- Viewer kiểm tra revision/hash/span với text, không dựng DOM/PDF UI/highlight. Không thay kiểm thử XSS, signed URL/download quyền thật.
- Partial answer là trạng thái hiển thị, không biến câu hỏi answerable thành pass. Với SIM-10/11 cần theo dõi riêng kết quả delivery và lần mở nguồn, không che failure bằng nhãn `full_answer`.
- WF-N01/02/03/07 (scope thiếu, role spoofing, admission draft/quarantine, timeout) và hình/đơn vị ở WF-N06 còn chưa mô phỏng; không coi bộ này thay đủ 8 WF-N hay 12 RBAC integration cases.
- Không đổi N1/N2/N3 hoặc nhãn silver thành gold; P05 mới hoàn thành vòng chạy synthetic đầu, **chưa có người dùng chốt D-01..D-06**.

Bước tiếp theo là người dùng review kết quả/quy tắc trên. Chưa tự triển khai baseline retrieval, cache, API hoặc agent sau vòng chạy này.

## 8. Kiểm tra artifact trước bàn giao

- Chạy lại runner cho kết quả JSON khớp hoàn toàn bản lưu, gồm fixture/runner hashes và toàn bộ traces.
- Structural verifier đạt 208/208 checks, năm file Python qua kiểm tra cú pháp, 17 PDF giữ đúng hash; không có check bị skip. Đây không phải runtime test suite.
- Toàn bộ 244 file `data/` có trước vòng này giữ nguyên SHA-256, không thiếu file. Chỉ thêm ba file `fixtures.json`, `results.json`, `README.md` trong thư mục mô phỏng mới.
- Các liên kết local trong README của bộ mô phỏng đều tồn tại. Không tạo/thay file runtime dưới `ai-core/src`, `backend/src` hoặc `frontend/src`.
