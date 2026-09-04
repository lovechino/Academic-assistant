# Evidence packet boundary — draft v0.1

Trạng thái: đặc tả để review, không phải OpenAPI/JSON Schema hoặc DTO đã freeze. [Mô hình nguồn và ví dụ](../docs/architecture/05-evidence-pipeline-contract.md) là tài liệu đồng hành.

## 1. Tách ba vùng dữ liệu

| Vùng | Producer → consumer | Được chứa gì? |
|---|---|---|
| Internal source/processing registry | Backend + AI ingestion → internal pipeline | Raw path, checksums, parser versions, elements/chunks và access references |
| Generation input | AI packing → generator adapter | Câu hỏi, phạm vi tin cậy cần thiết, source fragments thật, context headers được đánh dấu, budget/quality |
| Public answer/source projection | Backend → Frontend | Answer/status, claim-citation links, tên nguồn được phép, opaque source reference, version/locator cần thiết |

Evaluator-only sidecar không thuộc ba vùng trên. Không chứa reference answer/qrels/expected claims trong generator input, chunk payload hoặc filter. Cũng không chuyển toàn bộ internal registry/raw paths tới frontend.

## 2. Evidence packet đề xuất

Tên field còn có thể đổi khi đóng schema. Các kiểu ở đây là mô tả, không phải generated runtime types.

| Field | Kiểu/điều kiện | Ý nghĩa |
|---|---|---|
| `packet_id` | Nonempty string | Identity của đúng lần đóng context; repack tạo revision/identity mới |
| `request_id` | Nonempty string, ở request envelope | Correlate các bước; không phải quyền truy cập |
| `document_ref` trên item | ID + source version/hash + representation ID/hash | Gắn evidence vào snapshot xác định |
| `items` | Ordered array | Chỉ các fragments thực sự được serialize để dùng; ghi thứ tự và đối tượng visual nếu áp dụng |
| `item_id` | Unique within packet | Claim/citation trỏ tới item này, không trỏ candidate đã bị bỏ |
| `origin_ref` | Chunk hoặc context-window reference | Lineage để debug retrieval/expansion; không thay source locator |
| `span` / `source_locators` | Text spans hoặc locators đúng format | Có hệ tọa độ, bounds, source content/asset reference và checksum |
| `context_header` | Text + origin + `citable=false` trong profile này | Metadata/context giúp đọc; không được dùng thay evidence |
| `quality_flags`, dependency availability | Theo item/packet, nullable khi chưa đo | Tách text validity, reading order, thiếu ảnh/bảng/định nghĩa; unknown không phải pass |
| `integrity_state` | Pending/validated/rejected theo verifier và version | Chỉ structural integrity, không đồng nghĩa answerability |
| `answerability_assessment` | Status + method/version + reasons nếu đã chạy | Chưa assessment phải là not_assessed; không gán complete từ gold qrels |
| `budget` | Measurement state, tokenizer/accounting profile, limits, actual/estimated usage | Phải tính serialized input thật; không suy token từ codepoint |

Scope/capability từ Backend và các lần recheck quyền nằm trong trusted execution context; ví dụ local chỉ có `serving_authorized=false`, không phải credential. Production cần current policy/admission trước retrieval, expansion, model input, delivery và source view theo threat model; packet fields không tự bảo đảm điều đó.

## 3. Invariants bắt buộc khi triển khai

1. Text/asset phải khớp source locator và representation. Nếu rút ngắn fragment, cập nhật locator, content hash và omission trace; không giả gửi đủ span gốc.
2. Element → chunk → parent/window → packet phải cùng document version và provenance. Nhiều tài liệu chỉ được kết hợp ở packet bằng các item riêng, không nén thành một chunk mất identity.
3. Một claim có thể cần nhiều citations. Citation chỉ hợp lệ khi gắn item đã được dùng, hỗ trợ claim và còn truy cập đúng version; không chỉ có ID tồn tại.
4. Contiguous spans có thể hợp lại để cover một evidence requirement. Việc serialize/join phải giữ reading order và không chèn header làm đứt nội dung; không bắt một chunk chứa trọn mọi ý.
5. Source/hash/representation đổi phải remap; JavaScript UTF-16 index không được áp trực tiếp thay Unicode codepoint offset. PDF/page/bbox là nhánh riêng, không ép lên HTML.
6. Budget unknown không cho phép kết luận fit. Header/tool/history/ảnh/output reserve cũng chiếm ngân sách ngoài text nguồn.
7. Public source reference là opaque lookup handle, không phải raw path, bearer credential vô thời hạn hoặc quyền mở nguồn. Viewer/backend phải kiểm tra lại.
8. Instructions trong source là dữ liệu không đáng tin cậy. Tách field không tự giải quyết prompt injection; cần policy/tool constraints và tests riêng.

## 4. Result và failure semantics

AI core trả answer draft, claim-citation links, assessment/limitations và structured failure khi có. Backend quyết định projection được phép và currentness tại delivery; frontend không sửa citation sang bản hiện hành cho tiện.

Phải phân biệt:

- Packet integrity invalid: thiếu/sai lineage, hash, locator hoặc asset; không đưa nội dung lỗi vào generation như đã kiểm chứng.
- Evidence insufficient: chưa đủ phần được hỗ trợ trong context; có thể fetch/repack trong cùng quyền/ngân sách. Không tự kết luận corpus không có đáp án.
- Permission/admission changed: fail safely, không cứu request bằng nguồn trái quyền hoặc cache cũ.
- Dependency timeout/cancellation/budget exhaustion: lỗi vận hành/giới hạn cụ thể, không gán nhãn unanswerable do thiếu kiến thức.
- Answer draft/citation invalid: chặn/review/retry theo policy được chốt, không mặc định phát stream trước kiểm chứng.
- Viewer unavailable/denied: báo đúng tại lần mở; không đổi lịch sử rằng output trước đó đã từng gửi hợp lệ.

Exact enum/HTTP status/SSE events chưa chốt. Retry count, partial-answer UX và cách pin historical version còn mở; các ví dụ không áp đặt chúng.

## 5. Profile ví dụ hiện tại và hạn chế

[Năm ví dụ local](../data/evaluation/silver/voer-dsa-contract-examples-v0.1/README.md) dùng HTML-in-JSON VOER. Source metadata/quotes/hash là thật; selection/chunks/candidate lists/repair traces/answer drafts được viết bằng tay. `index_plan.status=not_built`, `answerability_assessment=not_assessed`, token fields null, viewer chưa có và serving bị tắt.

Chỉ `examples[].model_input` mô tả generator input. `answer_draft` là mock output ngoài input; `evaluation-sidecar.json` và coverage diagnostics chỉ ở evaluator. Code helper không gọi model hoặc chứng minh authorization runtime.

Chưa có JSON Schema tổng quát cho PDF/multimodal hoặc exact API compatibility guarantee. Khi triển khai use case đầu, đóng discriminated schemas và thêm contract/integration tests cho các nhánh thực sự hỗ trợ trước khi phát hành.
