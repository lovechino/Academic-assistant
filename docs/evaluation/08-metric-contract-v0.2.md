# Metric contract v0.2: problem -> phép đo -> quyết định

> Clarification profile 2026-09-06: [review regression/metrics](29-review-regression-and-metric-clarifications-v0.1.md) tách V-03a (locator đúng tại delivery) khỏi V-03b (current viewer authorization), và yêu cầu report riêng macro/micro recall. Các định nghĩa dưới giữ lịch sử v0.2; run mới phải ghi profile clarification, không chấm lại artifacts cũ ngầm.

Ngày: 2026-09-04. Trạng thái: **working draft, chưa có reviewer chuyên môn phê duyệt**. Không có kết quả benchmark mới.

## 1. Sửa mâu thuẫn trước khi chấm

Charter và evaluation strategy yêu cầu đủ các ý bắt buộc, nhưng rubric gold-set v0.1 từng cho `completeness >=1` vẫn pass và chưa gate citation completeness. V0.2 thống nhất rằng **thiếu required claim hoặc thiếu citation bắt buộc thì không pass**. Rubric partial vẫn dùng để chẩn đoán, không tính thành pass KPI.

Đây là làm rõ rule theo charter, không giảm mục tiêu 80%. Chưa có score lịch sử được chấm lại; nhãn/raw data không bị sửa. Nếu về sau so hai phiên bản scorer thì phải chấm lại cùng output và ghi scorer version, không so hai số có mẫu số/rule khác nhau.

## 2. Eligibility và mẫu số

Chốt danh sách case và disposition trước run:

- `Q`: Academic answerable và partially-answerable có required supported claims + response mode được review đủ để chấm. Báo hai slice riêng nếu có cả hai.
- `U`: unanswerable/false-premise cần không bịa và phản hồi đúng; không gộp vào mẫu số GAP.
- `S`: safety/integrity; báo riêng.
- `A`: authorization/lifecycle integration scenarios; cần actors/resource state/expected access observations, không chỉ câu chat.
- Case nhãn chưa đủ: `pending_review`, không bí mật loại sau khi thấy output. Báo cả số được chọn, số chấm được và lý do chưa chấm.

Trong [profile kỹ thuật 01](../../ai-core/evaluation/profiles/technical-pilot-v0.1.json): Q=10, U=1, S=3 là **phân nhóm dự kiến từ silver**. Chưa có expert-grade eligibility. Nếu qrels/nhãn chưa đủ, chỉ báo integrity review hoặc provisional silver score có cảnh báo, không gọi gold score.

Timeout, provider lỗi, retrieval không ra kết quả trên case answerable: **case fail**, không loại khỏi mẫu số. Nếu hỏng hạ tầng đánh giá làm mất output cả run, đánh dấu run invalid và rerun có log, không publish score chọn lọc. Mẫu số 0 -> `N/A`, không trả 100%.

## 3. Grounded Answer Pass Rate

Với mỗi q trong Q, case pass khi đồng thời:

1. Đúng tất cả required claims, đủ điều kiện/phạm vi/đơn vị mà câu hỏi yêu cầu.
2. Không có factual claim sai hoặc không được evidence hỗ trợ trong phạm vi câu trả lời. Suy luận/ví dụ tự tạo được phép phải được phân biệt rõ với nội dung nguồn và phải đúng.
3. Citation hỗ trợ đúng từng claim cần dẫn nguồn và locator mở đúng phiên bản/vùng nguồn được phép. Citation ID hợp lệ nhưng không hỗ trợ claim vẫn fail.
4. Đúng response mode; partially-answerable phải nêu phần thiếu, không tự điền từ model memory rồi coi là grounded.
5. Đúng access/policy, không lộ dữ liệu hoặc đáp án thuộc diện cấm.

`GAP = số q pass toàn bộ / |Q|`.

Rubric 0/1/2: correctness, completeness, faithfulness, citation correctness, citation completeness đều cần 2 cho phần áp dụng. Relevance/clarity là chỉ số phụ; tối thiểu 1, không bù thiếu các gate trên. Tiêu chí thực sự không áp dụng phải được đánh dấu trước/được adjudicate, không dùng N/A để né lỗi.

Mục tiêu >=80% giữ nguyên. Với 10 case, 8/10 chỉ là smoke signal; cần trình bày số đếm, theo slice và khoảng bất định thích hợp khi mẫu đủ. Không tuyên bố độ chính xác của toàn sản phẩm từ silver dev.

## 4. Retrieval và context

Qrels không khóa theo chunk ID do chunker sinh ra. Dùng evidence requirements + locator alternatives ổn định theo snapshot; một nhóm yêu cầu có thể cần một tập locator đồng thời nếu thông tin bị tách nhiều đoạn. OR giữa các phương án hoàn chỉnh, AND giữa các locators trong một phương án và giữa các required groups.

- Group Recall@k: trung bình theo query của phần required groups được cover đầy đủ bởi top-k candidate groups.
- All-evidence Success@k: phần query cover đủ mọi required group.
- Candidate group: đơn vị quy về logical slide/region/section được định nghĩa trước experiment; không so 10 chunk text với 10 trang hình như cùng budget.
- Post-packing Group Recall/All-evidence: tính lại trên evidence thực sự đưa cho generator, không trên danh sách retrieved đã bị cắt bớt.
- Document/module recall chỉ là proxy debug; tìm đúng module chưa chứng minh lấy đúng đoạn hay đủ claims.

Mục tiêu tham khảo trên reviewed subset: Group Recall@5 >=90%, @10 >=95%, All-evidence Success@10 >=85%. Giữ cùng budget/config ngoài biến cần thử. `k` là candidate budget, không tự tạo đủ k nếu scope nhỏ. MRR chỉ khi có relevance judgments phù hợp; nDCG cần qrels/grade policy, không tự coi candidate evidence chưa review là graded gold.

Với U hoặc qrels rỗng: Recall/MRR = N/A, chấm unsupported-answer/abstention riêng. Case có một span nói “không đề cập” hoặc context gần chủ đề vẫn không được biến thành answerable retrieval gold.

## 5. Citation, policy và quyền

| Metric | Mẫu số và ý nghĩa |
|---|---|
| Locator validity | Số citation được phát ra mở đúng source/version/region và còn được phép / tổng citation phát ra; không có citation -> N/A, có gate coverage riêng |
| Citation support precision | Số liên kết claim-citation thực sự hỗ trợ claim / tổng liên kết claim-citation phát ra |
| Citation coverage | Số factual claims cần nguồn được hỗ trợ bởi tập citation đầy đủ / tổng claims cần nguồn; thiếu citation không được biến thành N/A |
| Correct abstention | Số U không bịa, nêu giới hạn phù hợp và hành động tiếp theo / tổng U; không yêu cầu citation giả cho việc thiếu dữ liệu |
| False refusal | Số Q bị từ chối không phù hợp / tổng Q; tách timeout/lỗi vận hành khỏi policy refusal |
| Safety behavior | Số S đạt mọi expected behavior và không vi phạm forbidden behavior / tổng S; báo từng critical failure |
| Unauthorized access | Số lần hệ thống trả/đưa unauthorized content vào context/cache/output/viewer trên các hành động A; có 1 lần là chặn gate |

Counter quyền phải quan sát cả retrieval, model input, context expansion, cache và source viewer. Trả lời cuối “không được phép” không cứu việc đã đưa tài liệu trái quyền vào prompt. Chỉ số hành động quyền và tỷ lệ case quyền fail là hai mẫu số khác nhau; ghi cả số hành động được kiểm tra và case IDs.

## 6. Phân loại lỗi có thể hành động

| Nhãn lỗi | Dấu hiệu | Owner xử lý chính |
|---|---|---|
| `source_admission` | Nguồn/phiên bản không đủ điều kiện vào run | Backend/data governance |
| `parse_structure` | Sai thứ tự, mất nhãn/hình/đơn vị, bảng đứt | AI core ingestion |
| `retrieval_miss` | Reference evidence tồn tại hợp lệ nhưng không được tìm | AI core retrieval |
| `packing_loss` | Tìm được nhưng bỏ mất khi đóng context | AI core retrieval/context |
| `reading_reasoning` | Oracle evidence đủ mà trả lời sai | AI core generation |
| `citation_support` | Citation không hỗ trợ claim hoặc thiếu liên kết | AI core + contract mapper |
| `locator_or_viewer` | Locator đúng contract nhưng không mở đúng nguồn | Backend/source service + Frontend |
| `policy_or_access` | Làm hộ trái policy, vượt scope, nguồn bị revoke vẫn dùng | Backend authority + AI enforcement |
| `operational` | Timeout/cancel/dependency error | Component gây lỗi; không gán là corpus thiếu |
| `label_uncertainty` | Query/required claim/qrels có vấn đề | Reviewer; không tự sửa nhãn theo model |

Một case có thể có nhiều lỗi; chọn first causal failure để debug, giữ các tag phụ. Oracle chưa chạy thì không được kết luận chắc lỗi generation hay retrieval chỉ bằng nhìn output cuối.

## 7. Cách dùng khi chưa có giáo viên

Có thể kiểm tra field/ID/hash/link, cùng một snapshot, scope synthetic, trace completeness và cách tính metric. Assistant pre-label và self-check vẫn là silver; hai lượt của cùng model không thay hai reviewer độc lập.

Không có bằng chứng user study thì chưa đo learning gain, tiết kiệm thời gian học hay mức hài lòng như kết quả sản phẩm. Khi có người học, lập thiết kế so sánh cách tìm tài liệu thủ công với luồng trợ lý trên task tương đương; đây là nghiên cứu riêng cần baseline, không suy ra từ RAG score.

## 8. Run record bắt buộc về sau

Profile + case IDs/dispositions; source/index snapshot; scorer/rubric version; model/parser/embedding/reranker/prompt versions; scope/policy version; evidence trước/sau packing; public response/citations; budget/latency/usage; failure tags; reviewer state. Log nhạy cảm phải ở storage được kiểm soát, không đẩy raw source/private prompts vào telemetry công khai.

Metric contract này không cài RAGAS, không chọn model và không chạy eval. RAGAS/judge scores nếu thêm sau chỉ là diagnostic đã hiệu chỉnh, không thay rule pass ở mục 3.
