# Content Unit & Index Contract v0.1.1

Clarification 2026-09-06 sau review: corrected draft, chưa freeze hoặc human sign-off. [WP-01.1 repair registry](../evaluation/29-review-regression-and-metric-clarifications-v0.1.md) ghi chín findings, regression results và cases chưa chạy. Boundary cụ thể theo [contract v0.1.1](../../contracts/content-unit-index.md).

## 1. Mục tiêu và phạm vi

Tài liệu này chốt mô hình logic từ tệp nguồn đến bằng chứng được đưa vào câu trả lời. Nó là đầu ra của WP-01 và là đầu vào cho thiết kế multimodal/OCR, evaluation registry và AI Core workflow sau này.

Phạm vi của v0.1:

- tách định danh vật lý, định danh học liệu, phiên bản, biểu diễn, đơn vị cấu trúc, đơn vị retrieval và projection trong index;
- giữ lineage từ câu trả lời về đúng snapshot, phiên bản, trang/vùng và bytes nguồn;
- tách nội dung, độ tương tự, xung đột và quyền truy cập thành các khái niệm độc lập;
- mô tả quy trình publish, revoke và query ở mức contract;
- xác định các metric bắt buộc trước khi có runtime implementation.

Ngoài phạm vi:

- chọn database, vector database, object store hoặc message broker cụ thể;
- chốt parser, OCR/VLM, embedding production hay reranker production;
- viết orchestration/runtime trong `ai-core/src/academic_ai/`;
- đặt SLA production khi chưa có số đo pilot.

## 2. Nguyên tắc nền

1. Một hash giống nhau chỉ chứng minh bytes giống nhau, không chứng minh hai tài liệu có cùng quyền sở hữu, quyền sử dụng, trạng thái xuất bản hay ý nghĩa học thuật.
2. Độ tương tự chỉ tạo ứng viên để xem xét. Nó không tự tạo quan hệ `same_as`, không tự merge và không được loại bỏ một phiên bản đang có xung đột.
3. Backend/PDP là nguồn quyết định quyền truy cập. AI Core và index chỉ nhận capability hoặc filter snapshot có thời hạn; chúng không tự cấp quyền.
4. Mọi derived content truy về immutable source snapshot và locator; trong quarantine còn gắn submission. Sau approval, serving content phải có promotion binding sang immutable material version; không tạo version giả để parse trước review.
5. Tài liệu upload ở quarantine không đi trực tiếp vào content store phục vụ người dùng hoặc serving index.
6. Parent context, hình ảnh, OCR và dependency expansion không được phép mở rộng ra ngoài tenant, resource scope, phiên bản và purpose đã được cấp.
7. Nội dung tài liệu là dữ liệu không tin cậy. Chỉ control plane đáng tin cậy mới được cấu hình workflow, tool, policy và prompt hệ thống.

## 3. Chuỗi object chuẩn

```text
raw blob
  -> submission/quarantine receipt
  -> immutable source snapshot
  -> quarantine representations + blocks/atoms (inspection-only)
  -> approved immutable promotion binding
  -> tenant-owned material
  -> immutable material version
  -> bound representations / additional derived representations
  -> page/slide/region
  -> structural block and atom
  -> retrieval unit + context unit + dependency edges
  -> index projections in isolated surfaces
  -> authorized candidate set
  -> evidence packet
  -> grounded answer and citations
```

Mũi tên biểu diễn lineage hoặc derivation, không mặc định biểu diễn quyền sở hữu hay quyền truy cập.

## 4. Hệ định danh

| Object | Vai trò | Bất biến chính | Không được dùng như |
|---|---|---|---|
| `blob_ref` + `raw_sha256` | Tham chiếu bytes vật lý và kiểm tra toàn vẹn | Bytes bất biến; hash được giữ nội bộ | ID học liệu công khai hoặc bằng chứng quyền sở hữu |
| `submission_id` | Một lần upload/acquire vào quarantine | Gắn tenant, actor, thời điểm và trạng thái kiểm tra | ID tài liệu đã xuất bản |
| `source_snapshot_id` | Snapshot nguồn bất biến cùng restriction và acquisition metadata | Không bị sửa tại chỗ | Material version thay đổi được |
| `material_id` | Học liệu logic do một tenant quản lý | ID opaque, không suy ra từ hash | Fingerprint dùng để dedup xuyên tenant |
| `material_version_id` | Một phiên bản học liệu bất biến | Thay nội dung hoặc metadata có nghĩa thì tạo version mới | Trường version có thể overwrite |
| `representation_id` | Một biểu diễn text/render/OCR/layout/visual cụ thể | Có producer, config, version, hash, quality và lineage | Bản thay thế duy nhất cho nguồn |
| `page_id` / `logical_surface_id` | Trang vật lý hoặc slide/section logic | Locator ổn định trong material version | Chỉ số trang hiển thị mơ hồ |
| `region_id` | Vùng có bbox/polygon hoặc DOM/text offsets | Thuộc đúng surface và representation | Vùng ghép từ min/max span không liên tục |
| `block_id` | Khối cấu trúc như heading, paragraph, table, figure | Không cắt mất cấu trúc đã nhận diện | Chunk retrieval tùy ý |
| `atom_id` | Đơn vị nhỏ nhất không được cắt trong một chunk profile | Có exact source fragments | Token window thuần túy |
| `content_group_id` | Nhóm atom được đề xuất hoặc review là cùng ngữ cảnh | Thành viên được liệt kê rõ, có trạng thái review | Khoảng liên tục suy ra bằng min/max |
| `retrieval_unit_id` | Child unit dùng cho lexical/dense retrieval | Derived, có profile/version/hash và source fragments | Nguồn trích dẫn độc lập với lineage |
| `context_unit_id` | Parent/window để hydrate và pack context | Không mặc định được vectorize hoặc citable | Mở rộng tự do sang tài liệu khác |
| `claim_span_id` | Vùng mang một claim có thể so sánh | Truy về atom/region chính xác | Toàn bộ tài liệu |
| `claim_delta_id` | Khác biệt claim có ý nghĩa giữa các phiên bản/nguồn | Giữ cả hai phía và rule phát hiện | Kết luận phiên bản nào đúng |
| `conflict_set_id` | Tập các claim chưa thể đồng thời coi là sự thật đã thống nhất | Append-only; resolution là record riêng | Cơ chế overwrite claim cũ |
| `dependency_edge_id` | Cạnh có kiểu giữa các unit | Có scope, provenance, rule version, review state | Quyền vượt scope |
| `index_projection_id` | Bản chiếu của retrieval unit lên một search surface | Rebuildable; thuộc một `index_build_id` | Source of truth |
| `candidate_relation_id` | Quan hệ ứng viên như `candidate_similar` | Có evidence và threshold/version | `same_as`, merge hoặc publication approval |
| `evidence_packet_id` | Input thực tế được phép đưa cho generator | Bị ràng buộc bởi auth, snapshot và budget | Cache dùng chung thiếu policy key |

ID đưa ra ngoài tenant phải là opaque server-generated ID. Hash, MinHash, embedding fingerprint và đường dẫn lưu trữ là dữ liệu nội bộ; không được dùng để làm lộ việc tenant khác có hay không có cùng nội dung. Public/named-share binding giữ resource-owner tenant riêng với active tenant của request; chỉ PDP/broker được resolve exact binding. Multi-source packet giữ các item/lineage riêng, không nới query thành cross-tenant wildcard.

## 5. Mô hình biểu diễn

Một material version có thể có nhiều biểu diễn song song:

- `raw`: bytes gốc;
- `text_layer`: text có sẵn trong PDF/HTML;
- `normalized_text`: text được chuẩn hóa kỹ thuật, không thay thế nguồn;
- `canonical_text`: bản phục vụ so sánh/dedup, vẫn giữ alignment về nguồn;
- `page_render`: ảnh render của trang/slide;
- `ocr`: text do OCR sinh;
- `layout`: block, reading order, table/figure geometry;
- `visual_description`: mô tả được sinh từ hình, biểu đồ hoặc sơ đồ.

Mỗi representation phải ghi:

- `representation_id`, `representation_type`;
- `source_snapshot_id` và origin phân biệt quarantine (`submission_id`) với material (`material_version_id` + promotion binding);
- producer/model/tool, revision, config hash và thời điểm tạo;
- content hash và artifact reference;
- quality state: `complete`, `partial`, `failed`, `not_applicable`;
- confidence khi có nghĩa, nhưng không biến confidence thành truth;
- alignment map về physical page, bbox/polygon, DOM path hoặc text offsets;
- xung đột đã phát hiện với representation khác.

Text layer và OCR không được silently overwrite nhau. Khi hai biểu diễn bất đồng ở vùng có ý nghĩa, hệ thống giữ cả hai, ghi `representation_conflict`, và áp dụng policy fail-closed nếu modality đó là bắt buộc cho câu hỏi.

## 6. Block, atom, retrieval unit và context unit

### 6.1 Atom-preserving chunking

Chunking bắt đầu từ cấu trúc tài liệu, không bắt đầu từ một cửa sổ token cố định. Một atom có thể là:

- heading kèm phạm vi áp dụng;
- paragraph/list item;
- table header, row hoặc cell group có quan hệ;
- figure caption, label hoặc callout;
- công thức cùng ký hiệu/định nghĩa bắt buộc;
- code block và phần prologue cần thiết;
- footnote/endnote cùng target;
- slide title, body region hoặc speaker note được phép dùng.

Chunk profile có thể gộp nhiều atom nhưng không được cắt atom quan trọng. Khi atom vượt budget, profile phải dùng rule chuyên biệt và giữ fragment map; không được cắt mù rồi mất header, đơn vị, định nghĩa hoặc điều kiện.

### 6.2 Retrieval unit

Một retrieval unit tối thiểu có:

- `retrieval_unit_id` và opaque lineage IDs;
- `source_fragments[]` theo thứ tự, mỗi fragment chỉ rõ atom/region, locator, offsets và hash;
- `source_text`: phần nguồn có thể trích dẫn;
- `retrieval_header`: metadata ngữ cảnh sinh quyết định, `citable=false`;
- `retrieval_text`: đầu vào tìm kiếm được tạo từ header + source text theo profile;
- `chunk_profile_id`, `chunk_profile_version`, `derivation_hash`;
- quality flags, modality và language;
- `context_unit_id` và dependency edges liên quan.

`retrieval_header` có thể mang tên môn/chương/mục nhưng không được giả làm nội dung nguồn. Citation validator chỉ cho phép trích từ source fragments hợp lệ.

R0 typed events giữ sub/sup/table/code, nhưng legacy stripping trong R2–R4 làm mất các phân biệt này. Profile mới phải chấm fidelity sau serialization; không dùng ID/chunk containment như bằng chứng text đưa model còn đúng nghĩa. [Experiment sửa lỗi](../../ai-core/experiments/context-integrity-v0.1/README.md) kiểm chứng subset text có giới hạn; chưa tạo lại corpus/vector hoặc chấm lại retrieval.

### 6.3 Context unit và dependency graph

Context unit dùng để hydrate sau retrieval. Nó có thể là parent section, một nhóm slide hoặc cửa sổ cấu trúc, nhưng không tự động trở thành ứng viên citable.

Các loại cạnh ban đầu:

- cấu trúc: `contains`, `parent_of`, `prev`, `next`, `continues_from`;
- ngữ nghĩa phụ thuộc: `requires_definition`, `requires_lead_in`, `requires_header`, `formula_context`, `code_prologue`;
- multimodal: `caption_of`, `explained_by`, `footnote_of`;
- phiên bản/xung đột: `version_predecessor`, `conflicts_with`;
- tìm kiếm, không phải truth: `candidate_neighbor`.

Mỗi traversal phải:

1. kiểm tra cùng tenant và effective resource scope;
2. kiểm tra version/lifecycle/purpose trước khi đọc target;
3. giới hạn số hop, số token và số unit;
4. phát hiện cycle;
5. ghi rõ edge provenance và rule version;
6. không biến một cạnh suy đoán thành quan hệ đã review.

Cạnh cần có requirement `required/optional/not_assessed`. Pack required closure cùng anchor, sau đó mới optional context. Nếu thiếu dependency/không fit, bỏ bundle hoặc mark dependent claims incomplete; không giữ anchor như đủ context. Post-pack closure phải chấm trên payload cuối, tách khỏi resolver reachability. Cross-version conflict/version edge chỉ được theo khi từng target/version được cấp rõ; same-version constraint chỉ áp dụng cho cấu trúc nội bộ một source unit, không cấm so sánh hai version hợp lệ.

## 7. Độ tương tự, tương đương và xung đột

Kết quả E0.9 cho thấy một near-copy có thay đổi claim quan trọng thường có similarity cao hơn một paraphrase tương đương. Vì vậy:

- Char n-gram, MinHash, BGE-M3 hay model khác chỉ tạo `candidate_similar`;
- threshold là cấu hình candidate generation, không phải ngưỡng truth;
- không được auto-merge, auto-delete, auto-publish hay kế thừa quyền từ similarity;
- top-K review phải giữ cả ứng viên tương đương và ứng viên xung đột khi có thể;
- claim delta và conflict set được lưu riêng, không bị collapse bởi dedup;
- nếu packet chứa xung đột chưa được giải quyết, generator phải trình bày bất đồng hoặc abstain theo policy, không được trả lời như một kết luận thống nhất.

Quan hệ `same_as` chỉ được tạo bởi một quyết định có thẩm quyền và vẫn không làm hai tenant chia sẻ lifecycle, ACL hay quyền khai thác tài liệu.

Conflict assessment phải có `not_assessed`, `partial`, `completed_no_conflict_observed`, `unresolved`, `resolved`, assessed scope/version set và method/revision. `None` hoặc một top-K không có conflict không chứng minh đồng thuận. Known authorized conflicting sets cần đủ các phía trước generation; exact duplicate routing không thay bước này. Unassessed lookup có thể chỉ phát câu trả lời quy thuộc nguồn nếu policy cho phép; không được tuyên bố đã phân xử truth hoặc hoàn thành comparison thiếu phía. Denied targets không lộ existence qua warnings.

## 8. Các store và search surface logic

Thiết kế không khóa vendor. Các vai trò logic gồm:

| Surface/store | Vai trò | Authority |
|---|---|---|
| Catalog/lifecycle store | material, version, approval, ownership, policy handle | Backend authoritative |
| Immutable object store | bytes nguồn và derived artifacts | Integrity source, không quyết định quyền |
| Representation/source graph | page, region, block, atom, lineage, alignment | Derived evidence graph |
| Lexical projection | token/posting cho keyword/hybrid search | Rebuildable projection |
| Dense projection | vector cho semantic candidate retrieval | Rebuildable projection |
| Optional visual projection | image/region vector hoặc descriptor | Rebuildable, policy-gated |
| Dependency/claim graph | typed edges, claim delta, conflict set | Derived/reviewed records |
| Index manifest/alias | build composition và active serving snapshot | Promotion control plane |

BGE-M3 là baseline dense embedding hiện tại cho thí nghiệm, chưa phải lựa chọn production không thể thay đổi.

### 8.1 Index projection

Mỗi projection phải tham chiếu tối thiểu:

- `index_projection_id`, surface type và namespace;
- `index_build_id`, corpus snapshot và active/staging state;
- `retrieval_unit_id`, `material_id`, `material_version_id`;
- tenant partition và opaque authorization filter handle;
- lifecycle snapshot, relevant resource-policy/publication revisions và visibility state; subject/session/share revisions được kiểm riêng ở query;
- representation/chunk/retrieval profile versions;
- embedding/reranker model revision khi áp dụng;
- content/derivation hash và quality flags.

Không nhúng ACL, role, tenant secret, evaluation label hoặc reviewer note vào embedding text. Các trường filter trong payload chỉ là bản chiếu phục vụ prefilter; backend/PDP vẫn là authority.

Quarantine/staging index phải tách khỏi active serving index. Alias active chỉ chuyển sang một build đã được verify và re-authorize.

## 9. Publish, update và revoke

### 9.1 Publish

```text
quarantine submission
  -> safety/rights/integrity checks
  -> parse + representation generation
  -> duplicate/conflict review where required
  -> approved_for_staging
  -> immutable material version
  -> isolated index build
  -> manifest verification
  -> backend approval + current policy recheck
  -> atomic activation of serving alias
```

Một stale job không được promote nếu source snapshot, material version, approval, publishing-workload authority, relevant resource-policy/publication revision hoặc build manifest thay đổi. Unrelated user membership change không buộc rebuild vector. Activation dùng một serving snapshot tham chiếu đủ lexical/dense/graph/representation/optional visual surfaces; query pin manifest một lần. Check-and-CAS được serialize với relevant revoke/update, không switch alias riêng từng surface. Thay đổi nội dung tạo version mới; không sửa in-place version đã xuất bản.

### 9.2 Revoke và thay đổi quyền

Khi tài liệu bị revoke hoặc ACL thay đổi:

1. backend/PDP từ chối protected read ngay theo policy hiện hành;
2. cache key cũ bị vô hiệu theo policy epoch;
3. projection được tombstone/remove khỏi serving alias bất đồng bộ;
4. background deletion có thể diễn ra sau theo retention policy;
5. audit giữ bằng chứng rằng khoảng thời gian propagation không tạo authorized delivery sai.

Không phụ thuộc vào việc vector index đã purge xong mới chặn truy cập. `revocation propagation latency` vẫn phải đo riêng, nhưng correctness gate là không có protected delivery sau khi policy đã có hiệu lực.

"Sau revoke" xác định bằng authoritative ordering point của protected release và revoke commit; không dùng network arrival timestamp. Delivery cần fenced/serialized admission mechanism được review và kiểm thử, không chỉ một check rồi gửi bất kỳ lúc nào. Recheck ở các boundary tiếp theo; bytes đã phát hợp lệ không thể thu hồi.

## 10. Query và evidence flow

```text
trusted request identity + purpose
  -> backend/PDP issues bounded authorization context
  -> authorized resource prefilter
  -> lexical/dense/visual candidate retrieval
  -> score normalization and fusion
  -> current-policy recheck before hydrate
  -> bounded dependency expansion
  -> conflict-aware context packing
  -> evidence packet
  -> generator
  -> entailment/citation validation
  -> backend delivery/viewer recheck
```

Không được retrieve toàn kho rồi redact sau. Mọi candidate, parent, hình ảnh và dependency target đều phải qua scope check trước khi nội dung được hydrate vào memory của AI Core.

Internal evidence envelope chứa metadata kiểm chứng; chỉ allowlisted `model_input` projection của nó được gửi generator. Envelope phải giữ riêng:

- source text có thể trích;
- retrieval-only header;
- physical/logical locators;
- version và representation lineage;
- conflict/quality state;
- authorization decision reference, purpose và expiry;
- packing decision, token cost và lý do loại bỏ unit.

Authorization decision/capability, internal tenant/subject/grant IDs, storage paths/hashes và evaluator sidecar không nằm trong model input. Model chỉ thấy local citation handles, nguồn/locator được phép và safe quality/completeness hints. Internal envelope ghi exact serialized model-input hash/profile/budget; sự có mặt của hash hoặc opaque ID không thay authorization.

Cache key tối thiểu phải bao gồm active tenant/effective policy digest, owner partitions/exact public-or-share bindings và revisions, action, purpose, policy epoch, serving snapshot, representation/chunk/dependency/retrieval versions, model và prompt version. Cache hit khác scope là lỗi nghiêm trọng.

## 11. Metrics và acceptance gates

Các target dưới đây là correctness gate cho tập kiểm chứng được review, không phải cam kết SLA production.

Các hàng là shorthand; [measurement clarification v0.1.1](../evaluation/29-review-regression-and-metric-clarifications-v0.1.md#3-measurement-clarification-profile-v011) là định nghĩa numerator/denominator/eligibility/owner/N/A hiện hành. Chưa chạy khác với pass; historical scorer không bị đổi ngầm.

| ID | Metric | Target WP-01/WP-03 |
|---|---|---:|
| CU-01 | Physical/logical locator validity | 100% |
| CU-02 | Stage-aware lineage: submission/snapshot trước approval; thêm promotion/material version khi serving | 100% |
| CU-03 | Retrieval/context unit trộn nhiều effective resource scope | 0 |
| CU-04 | Critical atom bị cắt hoặc mất | 0 |
| CU-05 | Representation conflict được giữ lại thay vì overwrite | 100% |
| IX-01 | Unauthorized candidate/content exposure | 0 |
| IX-02 | Quarantine artifact vào serving hoặc unassigned inspection principal | 0 |
| IX-03 | Orphan hoặc stale projection tại thời điểm activation | 0 |
| IX-04 | Protected delivery sau policy-effective revocation | 0 |
| IX-05 | Conflicting claim bị dedup collapse | 0 |
| IX-06 | `candidate_similar` tự động biến thành equivalence/merge | 0 |
| IX-07a | Structural derivation drift, loại run IDs/timestamps/opaque ID encoding | 0 |
| IX-07b | Vector/ranking drift trên paired probes | Tolerance TBD trước run |
| IX-08 | Active build manifest coverage | 100% |
| IX-09 | Dependency expansion vượt scope/version/purpose | 0 |
| IX-10 | Cache hit sai effective scope | 0 |
| CR-01 | Recall của critical claim delta trên synthetic reviewed set | 100% |
| CR-02 | Unresolved conflict được giữ trong evidence packet | 100% |
| CR-03 | Câu trả lời coi unresolved conflict là fact đã thống nhất | 0 |

Latency, storage overhead, recall@K, nDCG, MRR, answer relevancy và chi phí vẫn được đo, nhưng không được dùng để đổi lấy vi phạm correctness/security gate.

## 12. Mapping từ thuật ngữ draft cũ

| Thuật ngữ draft | Thuật ngữ v0.1 | Lưu ý |
|---|---|---|
| `document_id` | `material_id` | Tenant-owned logical object |
| `document_version` | `material_version_id` | Immutable ID, không chỉ là số mutable |
| `element_id` | `block_id` hoặc `atom_id` | Chọn theo granularity |
| `chunk_id` | `retrieval_unit_id` | Derived search unit |
| `parent_id` | `context_unit_id` hoặc typed dependency edge | Không mặc định một parent duy nhất |
| vector point ID | `index_projection_id` | Projection rebuildable |
| `content_hash` | integrity/derivation field | Không phải public identity |
| `allowed_roles`, `course_id` trong index | authorization filter snapshot | Không phải authority |
| page number | physical page + logical label | Hai locator tách biệt |
| citation source | opaque source handle + exact fragments | Không lộ storage path/hash |

## 13. Failure modes bắt buộc kiểm thử

- cùng bytes được upload bởi hai giáo viên trong cùng trường nhưng có ownership/lifecycle khác nhau;
- gần giống nhau nhưng thay một con số, dấu phủ định, điều kiện hoặc đơn vị;
- OCR và text layer bất đồng ở công thức/bảng;
- hình chứa ý chính nhưng text chỉ có caption;
- heading nằm ở chunk trước, nội dung ở chunk sau;
- table header lặp sai hoặc row bị tách khỏi đơn vị;
- parent/dependency target đã revoke trong lúc query đang chạy;
- index job cũ hoàn thành sau version/policy mới;
- cache từ role/course/purpose khác;
- một content group gồm các vùng không liên tục;
- source có prompt injection yêu cầu bỏ policy hoặc gọi tool;
- citation đúng câu chữ nhưng trỏ sai version/page/region;
- unresolved conflict chỉ còn một phía sau fusion/packing.

## 14. Quyết định còn mở

Các quyết định sau chưa được chốt trong WP-01:

- encoding và lifecycle cụ thể của opaque IDs;
- physical multi-tenancy, storage-level dedup và encryption boundary;
- database/vector/object store cụ thể;
- parser, OCR, layout model và visual representation pipeline;
- topology của lexical/dense/visual indexes;
- embedding/reranker production và dimension/quantization;
- revoke propagation SLO, TTL và retention;
- claim adjudication workflow và vai trò reviewer;
- budget/threshold theo loại tài liệu và câu hỏi.

WP-02 sẽ xử lý representation multimodal/OCR. WP-03 sẽ chuyển các metric/gate thành evaluation registry có dataset, denominator và reporting schema. Sau review packet WP-04, việc thiết kế/triển khai AI Core product workflow chỉ bắt đầu khi qua ASTRA-01.

## 15. Acceptance của WP-01

WP-01 được coi là chốt ở mức thiết kế khi:

- không còn object nào đồng thời là content truth và authorization truth;
- mọi retrieval unit/index projection truy ngược được đến version, representation và locator;
- similarity, equivalence và conflict là ba trạng thái riêng;
- parent, dependency và multimodal hydration đều chịu cùng scope check;
- quarantine không có đường promote trực tiếp vào serving index;
- publish/revoke có manifest, policy epoch và stale-job protection;
- metric IDs được bàn giao rõ cho WP-03.
