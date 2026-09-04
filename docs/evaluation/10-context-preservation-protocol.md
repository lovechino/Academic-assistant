# Protocol v0.1: chunking có làm mất hoặc ghép sai context không?

Ngày: 2026-09-04. **Thiết kế thí nghiệm, chưa chạy, chưa có score/nhãn mới.** Căn cứ [nghiên cứu chunking](../architecture/06-chunking-research-and-dependency-design.md), [metric contract v0.2](08-metric-contract-v0.2.md) và [experiment matrix cũ](05-chunking-indexing-experiment.md).

Cập nhật vòng tiếp nối: [R0 annotation/source review](11-context-review-round0.md) đã tạo 30 probe / 31 biến thể silver, 29 nhóm và 7 dependency candidates. Nội dung dưới đây giữ làm protocol; các câu “dự kiến/chưa tạo” mô tả thời điểm lập kế hoạch. Chưa chạy chunker/retrieval/generation; serializer R0 vẫn còn việc.

## 1. Câu hỏi và giả thuyết có thể bác bỏ

- H1: grouping theo cấu trúc và dependency làm giảm mất điều kiện/định nghĩa so với fixed splitting, tại cùng budget.
- H2: mở theo dependency giảm phần thừa so với parent expansion mà không giảm complete-evidence rate.
- H3: bộ phát hiện vùng khó không được cải thiện “recall” bằng cách nối mọi thứ hoặc đánh dấu mọi đoạn là chưa hỗ trợ.
- H4: thêm header có lợi cho retrieval nhưng không tự làm evidence đầy đủ hơn nếu phần nguồn bắt buộc chưa được lấy.

Nếu không quan sát được cải thiện ổn định, giữ phương án đơn giản hơn; không chọn winner theo tên thuật toán.

## 2. Tách ba tập, tránh tự tạo thước đo để thắng

**Structural review set:** vị trí nguồn, nhóm nội dung, dependency cần/không được nối. Annotator xem nguồn, không dựa vào kết quả chunker. Mỗi nhãn ghi proposed/verified/disputed/unresolved, reviewer và lý do. Assistant pre-label vẫn là silver; tự kiểm tra hai lần không thành hai reviewer độc lập.

**QA evidence set:** giữ nguyên 10 QA / 30 claims / 25 groups / 22 locators đã có. OR giữa phương án evidence hoàn chỉnh; AND giữa các locator trong một phương án và các nhóm bắt buộc. Không biến mapping cũ thành ranh giới chunk, không coi đó là 22 câu hỏi độc lập.

**Runtime candidate metadata:** chỉ cấu trúc/quan hệ suy từ nguồn, không reference answer, gold target hay query-to-locator mapping. Evaluator được dùng labels để chấm nhưng không được dùng chúng để chọn child/neighbor cho hệ thống được chấm.

Cả 16 module hiện tại đã dùng cho phát triển: coi là **dev**, không tuyên bố holdout chưa từng thấy. Holdout nghiệm thu sau này cần tài liệu/nhãn riêng, quyền sử dụng và người review phù hợp. Freeze eligibility trước mỗi run; nguồn chưa chắc báo pending, không loại sau khi thấy fail.

## 3. Bộ 30 probe dự kiến

Đây là inventory cần gắn nhãn, không phải 30 test đã tạo hoặc đã pass. Một probe là thử cấu trúc/context, không nhất thiết là một câu hỏi học thuật.

| IDs | Số | Nội dung cần phủ |
|---|---:|---|
| CP-01..04 | 4 | Evidence qua hai p; hai ý cùng p; list cần câu dẫn; đoạn tự đủ không cần mở rộng |
| CP-05..08 | 4 | Khai báo + thao tác Stack; code lớn; pseudocode lẫn prose; công thức bị gắn nhầm cờ code |
| CP-09..12 | 4 | Công thức + cận; sub/sup; đơn vị/giả định; notation trong nguồn chưa chắc |
| CP-13..16 | 4 | Ô trống; header dùng td; bảng diễn tiến cần trạng thái trước; hai bảng gần nhau nhưng khác đối tượng |
| CP-17..20 | 4 | Alt là tên file; caption candidate sai; asset bị thiếu ở fixture; câu hỏi phụ thuộc hình chưa được review |
| CP-21..24 | 4 | Nhóm vượt cap; expansion cứu được; so sánh cần hai phía; expansion vẫn không đủ |
| CP-25..30 | 6 | Không nối qua heading không liên quan; biến cùng tên khác phạm vi; sai version; đoạn gần ảnh không phải caption; chỉ dẫn bất tín trong nguồn; lệch Unicode/entity offsets |
| Tổng | 30 | Positive, negative và failure-path; không chỉ happy path |

CP-22 và CP-24 tương ứng ý nghĩa SIM-02 và SIM-03, không tái sử dụng số pass tabletop như kết quả mới. Đối với CP-23, phải có cả biến thể đủ hai phía và thiếu một phía; chúng là subcases và cần báo số riêng khi tạo suite, không ngầm tăng mẫu số “30”.

Seed đã biết để annotator bắt đầu:

- CP-01: `list-data` hoặc `problem-ipo` trong [validation cấu trúc](../../data/processed/voer-dsa-structure-v0.1/validation.json).
- CP-02: `stack-push` / `stack-pop`, cùng node `n-7644daf60e0c208f`.
- CP-05: Stack `n-b0ddd30e2c28bebc` (Data S), `n-f667616a6e211102` (int t), `n-448aba3961c89a52` (PUSH); chưa khẳng định bộ ba này là context đầy đủ của toàn thuật toán.
- CP-08: Mảng `n-b4334d953bfd1507` là công thức có dấu `{`, một false-positive của code heuristic đã quan sát.
- CP-09: Mảng `n-8d8bccb9e878742f`, `n-7480b5243d8a7f0f`, `n-517cb22b4aec7594`: cận, công thức, giải thích. Cần review nội dung trước nhãn học thuật.
- CP-13..15: Stack table `n-261e330b0dbfad08`; 14 hàng / 56 ô. Hàng đầu có nhãn cột nhưng không có th.
- CP-16: Queue tables `n-2776cfff25553040` và `n-ff96a7654f86c635`, lần lượt Stack–Deque và Queue–Deque.
- CP-17: 69 image references hiện có alt là tên file; lựa chọn mẫu phải được ghi trước run, không suy ra cần hình chỉ từ việc có ảnh.

Các probe chưa có source span/expected đầy đủ phải giữ `pending_annotation`. Không được báo 30/30 coverage chỉ vì đã đặt ID. Nếu chưa có đủ mẫu thật, dùng fixture synthetic và ghi rõ provenance, không sửa raw corpus để tạo lỗi.

## 4. Bốn vòng tách biệt

### R0 — Review grouping và serializer, chưa retrieval

Chốt representation mới có rich text/source alignment, group/dependency sidecar và disposition từng vùng. Kiểm tra code detection cả false-positive lẫn false-negative trên mẫu có review; tương tự link hình/bảng. Không lấy số lượng flags làm quality score.

### R1 — Chunking-only

Cố định representation, eligibility và tokenizer; mọi config nhìn cùng nguồn. Thử lại C0 fixed và C2 structure-medium theo matrix cũ, nhưng phải ghi cả target/cap/overlap và phân bố token thực tế. Đây là so sánh hai cấu hình tổng hợp, không được quy mọi khác biệt cho boundary nếu size/overlap khác.

Để tách ảnh hưởng: thêm fixed có cùng hard cap và overlap=0; sau đó ablate overlap=64, rồi chạy size sweep riêng. Giữ serializer/header không đổi trong phép thử boundary. Không tự cắt các vùng lỗi ra khỏi baseline để làm đẹp kết quả.

Oversized/incomplete object được báo bằng disposition; toàn bộ source vẫn còn truy được. Nếu config không giữ row/formula được như hard gate, ghi fail diagnostic, không đưa output đó vào serving. R1 không có retrieval recall hay answer score.

### R2 — Retrieval và packing, chưa generation

Giữ nguyên child set và ranking để so các packer:

| Packer | Context sau child | Biến chính |
|---|---|---|
| X0 | Không mở rộng | Baseline mất context |
| X1 | Parent expansion với cap | Lợi ích của parent |
| X2 | Dependency expansion với cùng cap | Lợi ích của mở rộng có chọn lọc |

Không bắt đầu bằng full sweep C0–C8 × I0–I5. Sau R1 mới chọn tokenizer/retriever local đã được chấp thuận và pin version; vòng nghiên cứu này chưa cài hoặc chọn model. Sparse và dense là các run riêng. Late chunking giữ cùng boundary; header giữ cùng body; nếu thêm cả hai cùng lúc chỉ kết luận về package, không về từng thành phần.

Tạm đề xuất packet budgets 1.024 / 2.048 / 4.096 token để khảo sát đường cong, **không phải SLA hay cấu hình đã duyệt**. Chỉ dùng mức fit context window thật. Budget tính cả header, separator, source text lặp và mọi phụ thuộc; phần instructions/query/output reserve ở ngoài packet phải được ghi rõ. Tokenizer embedding và generator có thể khác, phải đếm lại input của từng bên.

Primary comparison dùng cùng B; top-k chỉ là diagnostic bổ sung. Theo metric contract, candidate groups phải có quy tắc quy về logical object/section đã freeze; báo cả raw child count và logical group count. Không để 10 chunk bé và 10 parent dài được xem là cùng chi phí.

### R3 — Generation và các tình huống đủ/thiếu

Chỉ chạy sau khi có quyền/model/budget. Oracle evidence để chẩn đoán generator là đường eval riêng, không lẫn vào retrieval run. Đo đủ claims/citations, false refusal trên answerable, phản hồi giới hạn phù hợp trên insufficient; không coi model tự nhận “đủ evidence” là ground truth.

## 5. Thước đo không bị đánh lừa bởi chunk lớn

Nguồn tham khảo phương pháp: Chroma đề xuất chấm precision/recall/IoU trên token có liên hệ với excerpt, thay vì chỉ trúng document/chunk. Đây là technical report dùng cả nhãn sinh tự động; áp dụng ý tưởng đo chứ không coi dataset đó là gold cho CTDL. [Evaluating Chunking Strategies for Retrieval](https://www.trychroma.com/research/evaluating-chunking).

Các định nghĩa dưới đây là **protocol của dự án**, không sao chép nguyên một scorer bên ngoài.

| Metric | Mẫu số / cách tính | Chống lỗi gì? |
|---|---|---|
| Locator fidelity | Fragment có source/version/span đúng / mọi fragment được tạo hoặc đưa vào packet; báo hai stage | Quote đúng chữ nhưng sai nguồn/vị trí |
| Mandatory-unit break | Số unit đã review bị split trái rule / mọi unit bắt buộc giữ của tập eligible | Cắt ngang row, formula hoặc block không có boundary an toàn |
| Forbidden-merge rate | Cặp/nhóm đã gắn nhãn không được ghép nhưng bị ghép / mọi negative grouping probe | Gom mọi p cho đủ context; không áp dụng cho hai evidence độc lập cùng nằm trong packet so sánh |
| Dependency coverage | Quan hệ cần thiết có đủ source fragments trong packet / mọi dependency đã review cần cho các anchor đang được đánh giá | Có phần thân nhưng thiếu định nghĩa/điều kiện |
| Complete-context rate | Probe có anchor + tất cả phụ thuộc bắt buộc trong budget / mọi probe answerable, eligible | Recall trung bình cao nhưng luôn thiếu một phần nhỏ quan trọng |
| Group Recall / All-evidence Success | Dùng AND/OR của metric contract; tính trước và sau packing | Tìm một phía của câu so sánh rồi tính là thành công |
| Packing retention | Nhóm evidence có trước packing và còn đầy đủ sau packing / mọi nhóm đầy đủ trước packing | Tìm được nhưng cắt mất khi đóng context |
| Rescue rate | Probe thiếu ban đầu nhưng đủ sau expansion / các probe thiếu ban đầu có phương án đủ đã review, hợp quyền và fit B | Đo SIM-02 đúng mẫu số; case không thể fit B báo riêng |
| Eligibility coverage | Số object/probe đã đủ điều kiện / toàn bộ object/probe được chọn trước run, kèm lý do còn mở | Loại toàn bộ vùng khó để có score cao |

Không có dependency/không có citation/không có probe đủ điều kiện thì metric tương ứng là N/A, không phải 100%. Các dependency biết trước chỉ ở evaluator; runtime phải tự lấy đúng qua cơ chế được thử.

### Token coverage và phần thừa

Pin một source-text projection có alignment và một evaluation tokenizer. Định danh token bằng document + source version + vị trí token occurrence, **không bằng từ vựng/token ID đơn lẻ**: hai chữ “Stack” ở hai vị trí không phải cùng evidence.

Với một phương án evidence đầy đủ E đã được annotate (gồm context bắt buộc) và tập source-token occurrences R có trong packet:

- Recall = |R ∩ E| / |E|.
- Precision = |R ∩ E| / |R|.
- IoU = |R ∩ E| / |R ∪ E|.
- Duplicate-source ratio = 1 − số source-token occurrences duy nhất / tổng số lần các occurrences đó xuất hiện trong packet.

Token occurrence chỉ tính được giữ nếu toàn bộ span của nó được packet cover; không ghi công cho một nửa ký hiệu. Header/summary sinh thêm không được tính vào evidence intersection nhưng vẫn tính vào budget và báo riêng overhead. Với nhiều phương án OR: chấm từng phương án hoàn chỉnh và công bố quy tắc chọn nhất quán trước run; không ghép nửa phương án này với nửa phương án khác để đủ điểm. Kết quả chính vẫn là group completeness, không tối ưu IoU đơn độc.

Nhãn evidence có thể chưa đầy đủ: precision/IoU lúc đó chỉ là provisional theo annotation, không khẳng định mọi token ngoài nhãn vô dụng. Với hình, ô trống, math rich structure: thêm object/relationship coverage, **không coi token IoU là thước đo đủ**. Token projection mới chưa được xây trong vòng này; legacy projection chỉ phục vụ compatibility các locator cũ.

## 6. Hard gates và cách báo cáo

Hard gates đề xuất cho config được phép đi tiếp: 100% locator/source lineage hợp lệ; 0 cross-version/access-body merge; 0 silent truncation; 0 mandatory-unit violation chưa khai báo; không dùng generated context thay evidence; không tự đánh dấu hình đã hiểu. Một fixture phạm gate là fail config, không giấu bằng score trung bình.

Mục tiêu coverage ≥95% của matrix cũ là target tham khảo; với bộ nhỏ phải ghi số đếm và từng lỗi, không lấy nó làm nghiệm thu. Hiệu quả retrieval/packing/answer phải báo riêng, cùng token/latency và tỷ lệ vùng chưa hỗ trợ. Với 10 QA dev chưa đủ để chọn winner cho toàn hệ thống; nhiều câu cùng module không phải mẫu độc lập. Khi đủ dữ liệu mới dùng ước lượng bất định theo document clusters, không bootstrap token như thể độc lập.

Run record cần: source/representation/enrichment/chunker/serializer/tokenizer/scorer versions; config; eligibility; source fragments trước/sau packing; unresolved dependencies; budget thực; failure stage; reviewer state. Version của thứ tự selection/dedup/overflow policy cũng phải pin.

## 7. Dataset bên ngoài: dùng cho phần nào?

| Nguồn | Vai trò phù hợp | Không thay được |
|---|---|---|
| [QASPER — NAACL 2021](https://aclanthology.org/2021.naacl-main.365/) | QA trên bài báo NLP với evidence do người trả lời cung cấp; tham khảo cách chấm đủ bằng chứng trong tài liệu dài | Tính đúng của code/công thức giáo trình Việt Nam; không mặc nhiên là transcript PDF/layout gold |
| [ViDoRe / ColPali](https://arxiv.org/abs/2407.01449) | Tách đánh giá truy hồi tài liệu giàu hình ảnh khỏi text retrieval | Liên kết caption chính xác, giữ từng hàng bảng hoặc chứng minh generator hiểu hình |
| [Chroma chunking evaluation](https://www.trychroma.com/research/evaluating-chunking) | Kiểm tra scorer ở mức source-token coverage/efficiency | Gold học thuật; corpus/dataset sinh tự động vẫn cần kiểm tra phạm vi và quyền trước sử dụng |

Chưa tải dataset nào trong vòng này. Chưa thấy bằng chứng trong các nguồn đã khảo sát đủ để khẳng định một chunker đã thắng trên đúng tổ hợp giáo trình tiếng Việt + pseudocode + công thức + sơ đồ của dự án.

## 8. Bước thực hiện tiếp theo

Tạo annotation sheet/JSON cho 30 probe dự kiến; đối chiếu từng vùng nguồn; tạo enrichment sidecar có version và unresolved states. Sau đó mới chạy R1 và in trace cho từng boundary: phần nào ở lại, phần nào được link, lý do split và cách recover. Chưa cần model, vector database hoặc UI sản phẩm để chuẩn bị bước này.
