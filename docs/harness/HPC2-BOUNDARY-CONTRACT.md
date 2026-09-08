# HPC-2 boundary contract v0.1 — draft, chưa enforcement

2026-09-08. Development harness, không academic-agent runtime. User giao tiếp tục
sau review HPC-1 để viết boundary contract **trước khi chọn công nghệ cách ly**.
Không cấp quyền host, cài môi trường, chạy worker/model, materialize hay apply file.
[Design nền](PATCH-ONLY-DESIGN.md), [validator hiện có](PATCH-VALIDATOR.md),
[handoff của lượt này](HARNESS-BOUNDARY-01-handoff.md).

Các từ “phải/deny” dưới đây là yêu cầu cho profile tương lai, không mô tả máy hiện
tại. Worker có cùng full host rights với controller là `unsupported_enforcement`.
Không đổi ASTRA-01/explicit product GO, WP-04, quarantine hoặc ARCH-02.

## 1. Điểm xuất phát và threat model

Review read-only trước lượt này chưa tìm thấy defect cần sửa ngay trong subset
validator. 36 tests và 6 probes pass; 3.000 mutation diagnostics có 2.965 reject,
35 valid, 0 unexpected exception. Đây là evidence lịch sử trong hội thoại, chưa
versioned probe script/golden oracle; **không rerun hoặc nâng thành host acceptance**.
Giữ bốn integration risks: context giả, materialization/link race, validation bị
nhầm thành approval, admission/packet/quota thiếu. Chúng đã được khai báo, không
được ghi thành bốn incidents mới hoặc findings tự động đóng bởi tests.

Giả định đối kháng: worker/candidate/test code có thể cố đọc ngoài scope, ghi controls,
giả identity/PASS, chèn instructions vào source/logs, replay output hoặc làm cạn tài
nguyên. Host operator và approved controller release là trust assumptions; nếu host
admin/kernel/controller bị chiếm thì profile không hứa bảo vệ. Không chứng minh
không còn side channel bằng một bộ test nhỏ. Không dùng secrets hoặc học liệu thật
làm sentinel; fixture là dữ liệu synthetic mới, riêng khỏi repo người dùng.

## 2. Actors và resource/action permissions đích

Mặc định deny; mỗi quyền phải được ánh xạ sang cơ chế thực và owner cụ thể ở lúc
chọn môi trường. Actor là trách nhiệm, không yêu cầu nhiều LLM hoặc nhiều services.

| Actor | Được đọc | Được ghi / hành động | Bắt buộc không có |
|---|---|---|---|
| User/host operator | Review packet, bounded evidence theo quyền | Duyệt exact profile/scope; provisioning trong task được cấp quyền riêng | Approval ngầm từ Markdown/worker label |
| Controller/supervisor | Approved release, scope record, snapshot được cấp, current job state | Tạo job/packet/grant, cấp quota, stop job; ghi controls/evidence riêng | Chạy candidate code/plugin/commands hoặc tự cấp thêm nguồn |
| Input snapshot builder | Exact source inputs được cấp cho job | Copy vào private immutable input store, tạo manifest | Scan/copy toàn checkout/home, follow links ra ngoài grant, ghi nguồn gốc |
| Validator + candidate builder | Controller context, bounded submitted bytes, sealed base slice | Validate; tạo candidate riêng trong controller-owned store | Import worker modules/config, dùng worker path làm host destination, ghi checkout thật |
| Worker | Job packet + approved tool/runtime assets, không toàn repo | Scratch/outbox riêng; gửi proposal qua một kênh bounded | Controls/checker/receipts, host secrets/cache/private PDFs, network hay promotion socket |
| Test executor | Copy của sealed candidate, approved fixture/runtime cho đúng job | Scratch/log channel riêng; chạy fixed profile trong isolation đã kiểm chứng | Accepted store, source snapshot gốc, reviewer credentials, host/process/network ngoài profile |
| Independent observer | Host-side lifecycle/denial/resource observations, expected test inventory | Ghi evidence ngoài quyền worker/executor | Tin stdout/counts tự khai như bằng chứng duy nhất; nhận lệnh từ payload |
| Reviewer/viewer | Escaped bounded diff/evidence đúng job | Reviewer decision qua kênh riêng về sau | HTML/remote images/URL fetch tự động, execute Markdown hoặc tự promote |
| Acceptance controller | Chỉ dành trước cho HPC-3 | Chưa có hành động accept/apply ở HPC-2 | Dùng `valid_in_memory_only` hoặc journal row làm authorization |

Controller/builder/observer có thể chia sẻ trusted deployment nếu quyền được giới
hạn đúng trách nhiệm; tuyệt đối không chạy untrusted executor trong quyền đó. Worker
và executor cũng tách scratch/job artifacts; một bên không sửa input hoặc observation
của bên kia. Read access vẫn là tiết lộ dữ liệu: mount read-only không cho phép đọc
secrets. Không gắn host home, SSH agent, credential store, desktop session, clipboard,
drive/daemon/admin sockets hoặc endpoint điều khiển host vào worker.

## 3. Ba tập dữ liệu không được nhập làm một

1. **Required task inputs/read grant:** instructions áp dụng, brief, task, contract
   sections, source được cấp; có classification, version, byte hashes và limits.
   Source text là data; instructions có authority chỉ từ kênh được controller chọn
   theo yêu cầu/rules thực, không từ filename hoặc lời tự nhận của worker.
2. **Writable proposal grant:** exact path/action set, subset độc lập; đọc được
   AGENTS/contract không có nghĩa được sửa chúng. Thay controls/checkers phải qua
   maintenance review riêng, không chứng nhận chính bản sửa chưa duyệt.
3. **Candidate base slice:** đầy đủ files/types/bytes của target slice được seal,
   không phải toàn repo hoặc chỉ những file worker dự kiến sửa. Phải kiểm cả aliases
   và collision với files/dirs khác trong namespace đích trước materialization.

HPC-1 `baseline` chỉ chấp nhận synthetic notes và không có packet admission. Không
đưa AGENTS/contracts vào API đó rồi nới notes policy để “cho chạy”; required-input
manifest phải riêng. Bounded first host trial vẫn synthetic notes; general repo/code
tasks là extension sau review, không tận dụng docs như đường vòng product code.

## 4. Data channels và binding

Đây là boundary specification, chưa wire schema/runtime commands mới. Không thêm
fields vào JSON task card hoặc changeset v1 hiện hành trong lượt này.

| Kênh | Nội dung được phép | Kiểm phía nhận / không được tin |
|---|---|---|
| Operator → controller | Exact scope/profile và quyết định thật | Identity/control channel độc lập worker; không lấy `approved=true` trong source |
| Controller → worker | Immutable packet đã được cấp quyền, job/generation/profile IDs | Required inputs đủ và đúng hashes; không silently drop rules vì hết context |
| Worker → ingress | Một bounded changeset UTF-8 cho job attempt hiện hành | Endpoint/session gắn job từ controller; worker khai job ID chỉ để đối chiếu, không chọn target repo/grant |
| Ingress → validator | Captured bytes bất biến + context trusted-side | Wire/schema/path/hash/budget; reject cả candidate, không partial output có quyền |
| Builder → executor | Sealed candidate copy + fixed execution profile | Recompute manifest, không lấy lại mutable outbox sau validation |
| Executor → observer/report | Untrusted bounded logs và return data | Host observer xác nhận lifecycle/required observations; stdout/exit 0 không là approval |
| Observer → reviewer | Versioned evidence, escaped diff nếu được phép | Bind đúng candidate/job/attempt; thiếu observer hoặc evidence → unverified, không PASS |

Trusted job record phải gắn repo identity, task/request, job/generation/attempt,
read/write grant version, packet/base digests, checker/runtime/profile digests,
deadline và trạng thái còn hiệu lực. Candidate digest hiện tại **không** chứa tất
cả những trường đó; cần outer binding được bảo vệ trước host integration. Không
chấp nhận serialized `ValidatedCandidate` tự dựng như kết quả trusted validation.
HPC-3 sẽ xác định receipt/review/currentness/acceptance; record HPC-2 chỉ observations.

Kênh chưa chọn: không mặc định shared folder, named pipe, HTTP hay archive an toàn.
Adapter phải chứng minh giới hạn bytes trước spool/decode và không cho caller truyền
arbitrary host path, shell command, environment, PID hoặc profile executable. IDs
opaque do controller quản lý; duplicate/late submit không mở job mới hoặc tự retry.
Full acceptance exactly-once/replay semantics vẫn thuộc HPC-3, không suy từ reject
stale ingress. Worker không gọi service bằng quyền controller qua confused deputy.

## 5. Snapshot/materialization và execution boundary

- Snapshot capture phải gắn quyền đọc hiện hành và bytes đã seal; manifest không
  được hash một bản rồi giao bản khác. Dirty source được người dùng nhận biết trong
  scope; không stash/reset/commit hoặc lấy HEAD thay toàn working content.
- Không hardlink từ host vào môi trường untrusted. Reject symlink/junction/reparse,
  unsupported file types/aliases, và không dựa vào `exists/resolve` rồi follow lại
  path mutable. Adapter cần phương án race-resistant được review theo OS thực.
- Chỉ tạo files trong controller-owned candidate area riêng; parent namespace không
  writable bởi worker. Capture output bytes một lần qua kênh kiểm soát, seal/hash,
  validate chính bytes đó; không kiểm xong rồi đọc lại outbox. Thay outbox sau capture
  không đổi candidate, output mới cần attempt được controller cấp.
- Copy cho executor không phải candidate store. Test/formatter thay bytes → không
  kế thừa evidence cũ, không promote scratch hoặc ignored files thành source mới.
- Trusted release bao gồm toàn import closure/config/required regressions và pinned
  runtime; worker không chọn CWD/PATH/import paths hoặc inject startup hooks vào nó.
  Fixed command vẫn thực thi code không tin cậy: chỉ executor được chạy candidate.
- Candidate text không được render thành active HTML/Markdown, remote image, ANSI
  escape hoặc command. Viewer dùng escaped text, không fetch URL. Error transports
  chỉ xuất mã lỗi an toàn; không serialize exception objects/traceback locals/source.
- Không có checkout writer/promotion trong host trial HPC-2. Cancel/timeout dừng job
  và invalidates tiếp nhận output mới; không thể “thu hồi” bytes worker đã đọc.
  Late observations giữ nhãn stale, không mở lại trạng thái hoặc tạo PASS hiện hành.

## 6. Admission, quotas và failure behavior

Giữ budget thử nghiệm của [design §7](PATCH-ONLY-DESIGN.md): request ≤1 MiB,
1..10 changes, ≤256 KiB/file, ≤768 KiB content; input packet ≤64 files/4 MiB;
validator 10s wall; executor 300s tổng/60s command, 2 GiB RAM, 32 processes,
256 MiB scratch; log ≤256 KiB/job, queue ≤10 candidates, một active candidate/job,
không auto retry. Đây là **proposed limits**, chưa benchmark hoặc host-enforced.

Tách raw changeset channel khỏi log channel: proposal hợp lệ có thể >256 KiB nhưng
không được in nó vào log để vượt cap. Supervisor áp byte/time/concurrency limits
trước đọc/spool, tính cả setup/children/cleanup, và quan sát việc dừng toàn process
tree. Controller cũng cần aggregate memory/disk/job quota; profile tổng và cleanup
grace còn phải chọn, không launch khi chưa có giá trị/cơ chế enforcement.

Input packet thiếu/over-budget → reject admission hoặc chia task có review; không
cắt required inputs. Model-token reserve chỉ chốt khi có model; host trial đầu dùng
deterministic synthetic producer, **không model/provider/network/install**. Không
suy model budget từ BGE-M3 hoặc từ bytes. Runtime assets phải được cấp/pin riêng,
không tải dependency/package hooks lúc worker/test chạy.

Timeout, quota exceed, observer mất, artifacts thiếu, kill chưa xác nhận hoặc source
mutation → explicit non-success; cap log không được che trạng thái failure. Cleanup
chỉ trên exact job-owned paths đã xác minh, không recursive delete workspace/home.
Cleanup thất bại giữ job unavailable + remediation, không tự coi đã sạch cho job sau.
Controller restart giữ trạng thái unknown/stale cho tới reconcile; không rerun mặc định.

## 7. Host acceptance evidence — tất cả NOT RUN

Expected tests phải do trusted side giữ; mỗi negative có positive control để phân
biệt “đã chặn” với “test chưa hề chạy”. Nguồn quan sát là host-side, không lời tự
khai bên trong sandbox. Các case sau cụ thể hóa HP-T, không tăng số executed tests.

| ID / HP-T liên quan | Negative + positive control | Evidence bắt buộc |
|---|---|---|
| HB-01 / 03..06,19,29 | Fake context/target/profile/approval; control: đúng job grant nhận proposal | Trusted identity/grant binding, deny event, đúng bytes control; không apply |
| HB-02 / 03..04 | Thiếu/stale input; control: packet đủ, đọc contract nhưng không được sửa | Required-ID/hash inventory độc lập và dispatch/no-dispatch observation |
| HB-03 / 17..18 | Outbox mutation/link swap/alias; control: regular file copy exact bytes | Host sentinel không truy cập/sửa, sealed hash ổn định, file-type/handle observations |
| HB-04 / 19..20 | Shell/editor đọc/ghi host controls, secrets synthetic; control: scratch/read-granted hoạt động | Host access-denial evidence + read/write controls, không chỉ so hash để đo read leak |
| HB-05 / 20,24 | Egress qua direct/proxy/DNS/host service/child process; control: observer được hiệu chuẩn bằng synthetic endpoint được cấp riêng | Host network observations bao phủ channels; missing observation không tính 0 leaks |
| HB-06 / 21..22 | Import shadow, fake PASS/early exit/skipped tests; control: required black-box checks thực chạy | Release digest, independent expected check inventory, supervisor outcomes |
| HB-07 / 23..25 | Mutated test copy, hang/process/disk/log flood; control: workload bounded hoàn tất | Inventory trước/sau, resource peaks, deadlines, tree terminated + cleanup evidence |
| HB-08 / 27,35,39 | Cancel/late output, malicious logs; control: đúng active attempt + escaped text | No state resurrection; viewer không fetch/execute, truncation/error hiện rõ |

Network observer positive control ở môi trường synthetic được operator cấp riêng;
không mở network worker “tạm thời để test” rồi claim cùng profile đã deny. Các probes
phải bounded, staged từ harmless control tới adversarial; không fork bomb vô hạn
hoặc nhắm dữ liệu/máy ngoài scope. Chưa chọn/cấu hình/chạy các probes này.

Evidence record: case/version, config/OS/runtime/release/packet/base/candidate hashes,
job/attempt, quyền thực, expected/actual, timeouts/skips, protected observation IDs,
positive controls, reviewer và residuals. Không lưu raw secrets/prompt mặc định;
ACL/retention của evidence cần chốt, local SQLite journal không là protected store.

Báo executed/pass/fail/blocked/not_run riêng cho HB-01..08; hiện executed=0,
not_run=8, tỷ lệ pass/escape=N/A. Một critical escape chặn rollout; thiếu control
hoặc observer → unverified. Không dùng unit-test pass hoặc zero incidents/N=0 để ký
host acceptance, semantic task success, product GO hoặc “agent tuân thủ 100%”.

## 8. Quyết định trước lựa chọn môi trường

| Decision | Cần ghi nhận | Owner / điểm chặn |
|---|---|---|
| HB-D01 Trust domain | Worker/executor và trusted actors ánh xạ vào account/process/guest nào; host prerequisites | User + host operator trước provisioning; HPD-02 |
| HB-D02 Channels và release | Input/outbox transport, protected runtime/checker/evidence paths, bootstrap chain | Maintainer trước host integration; HPD-03 |
| HB-D03 Scope/quotas | Exact synthetic fixtures, overall controller budgets, teardown grace, fail behavior | User/operator trước host test; HPD-06 |
| HB-D04 Observation | Công cụ/owner quan sát access/network/process; positive-control protocol, evidence retention | Operator/reviewer trước claimed enforcement; HPD-03/07 |
| HB-D05 Acceptance/recovery | Chưa triển khai: protected pointer, actual reviewer identity, cancel/replay/crash, backup/restore | HPC-3/4 review riêng; HPD-04/05/07 |

Đánh giá công nghệ sau này phải điền từng requirement: supported có bằng chứng,
unsupported hoặc unknown; critical unknown không được trung bình điểm bù lại.
Không chọn môi trường chỉ vì tạo được worktree/container hoặc chạy được tests.
Lượt tiếp theo phù hợp là khảo sát **read-only** prerequisites và lập comparison
theo contract này; không install/enable feature/ACL/mount/network configuration.
Mọi provisioning hoặc execution thử nghiệm cần task có scope/authority riêng.

### Follow-up 2026-09-08: Docker profile, chưa host execution

Khảo sát sau checkpoint trên xác nhận Docker trong Ubuntu WSL truy vấn được;
[Docker synthetic profile](HPC2-DOCKER-PROFILE.md) lưu giới hạn bằng chứng và đề xuất
specialization với quotas nhỏ hơn, không đổi requirements chung. Đây không phải
environment acceptance: image/provenance, trusted collector, cgroup enforcement,
observer và shared-workload risk vẫn pending. HB-01..08 vẫn NOT RUN; chưa có
launcher, container execution hoặc HPC-3/4 acceptance. Next là review profile và
read-only preflight, không tự install/pull/build/create/start từ draft này.
