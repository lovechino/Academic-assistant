# HARNESS-PATCH-01 — patch-only và ranh giới cưỡng chế (draft v0.1)

Boundary follow-up 2026-09-08: sau review read-only HPC-1 đã có [HPC-2 contract](HPC2-BOUNDARY-CONTRACT.md)
về actors/resources/channels/admission và independent host evidence. Chỉ docs, chưa
chọn/cấu hình môi trường; xem [handoff](HARNESS-BOUNDARY-01-handoff.md). Review không
tìm defect cần sửa ngay trong subset không phải human acceptance hoặc host GO.

Forward update 2026-09-08: user giao tiếp tục bounded HPC-1; đã có [pure in-memory
validator](PATCH-VALIDATOR.md) và synthetic tests, xem [handoff](HARNESS-PATCH-02-handoff.md).
Chỉ triển khai subset parser của design, chưa có protected runner hoặc hard deadline.
Không coi thử prototype là human acceptance toàn HPD-01..08; budgets bên dưới vẫn
cần review, phần chưa implement không thành bảo đảm hiện hành.

Trạng thái lịch sử 2026-09-07: **Chỉ thiết kế; chưa có launcher, patch parser/applier, sandbox,
protected validator, approval service hoặc promotion đang chạy.** User đồng ý tiến
hành bước thiết kế sau khi hỏi cách tránh agent bỏ qua Markdown. Không phải quyền
đổi ACL, cài VM/container, chạy model, push Git hoặc mở product implementation.

## 1. Mục tiêu và mức bảo đảm

Không cố chứng minh model đã đọc/hiểu 100% instructions. Mục tiêu là giảm phụ thuộc
vào sự tự giác: worker không có quyền ghi repo được tiếp nhận; thay đổi chỉ được
nhận qua một boundary độc lập kiểm scope, evidence và quyền hiện hành.

- **Hiện có:** [CLI harness](README.md), [SQLite journal](LOCAL-JOURNAL.md),
  [placement map](../architecture/11-source-placement-blueprint-v0.1.md) và checker
  Git-visible. Chúng là local detectors, worker cùng quyền ghi có thể bỏ qua/sửa.
- **Thiết kế này:** packet được cung cấp chủ động; candidate độc lập repo chính;
  validator/policy đáng tin cậy; chạy code trong môi trường không có quyền promotion;
  review và tiếp nhận đúng snapshot. Mọi bảo đảm đều có điều kiện vào các boundary này.
- **Không bảo đảm:** semantics đúng, hết duplicate, hết hallucination, sandbox không
  có lỗ hổng, admin/host bị chiếm vẫn an toàn. Thêm reviewer model không thay OS/tool
  permissions. Hiện chưa đo mức tuân thủ của model nào theo thiết kế này.

Scope là **development harness**, không là workflow AI học thuật. Giữ ARCH-02,
manual Academic, backend authority, quarantine và ASTRA-01 + explicit product GO.
Không tạo topology multi-agent sản phẩm hoặc tự spawn development agents.

## 2. Actors và ranh giới quyền đích

Các actor sau là vai trò phần mềm/người, không bắt buộc là các LLM hoặc microservices.

| Actor | Được làm trong thiết kế | Không được có |
|---|---|---|
| Người giao việc/reviewer | Duyệt scope, xem evidence, quyết định nhận/reject exact candidate | Lấy lời tự nhận của worker làm human approval |
| Trusted controller | Chụp snapshot được phép, đóng packet, kiểm admission/quotas, điều phối | Thực thi shell/code lấy từ patch/Markdown hoặc nhập candidate như plugin |
| Worker | Đọc packet cấp riêng, đề xuất changeset; sandbox scratch nếu được cấp | Ghi repo chính/control store, đọc secrets/nguồn ngoài scope, tự grant/push/accept |
| Trusted validator | Kiểm format/path/scope/digests bằng release được pin ngoài quyền worker | Import checker/config từ candidate hoặc tin kết quả PASS của worker |
| Test executor | Chạy candidate code/tests trong sandbox không credentials, trả observations | Ghi controls/repo chính, gọi promotion, network mặc định, chọn quyền cho mình |
| Acceptance controller | Kiểm receipt + review + current grant; cập nhật protected accepted pointer | Chạy candidate code, bỏ currentness check, áp file tùy ý vào checkout người dùng |

Controller/validator/acceptance có thể cùng ứng dụng tin cậy nhưng không cùng quyền
OS với worker/test executor. Worker output, test logs, source comments, Markdown,
URLs và SQLite rows là **untrusted data**, không executable instructions/authority.
Nếu worker vẫn có host shell toàn quyền, phải báo `unsupported_enforcement`, không
giả vờ wrapper đã chặn được đường đi vòng. Một worktree mới không tạo OS isolation.

Các rule được máy thi hành phải nằm trong **policy release có version được người
phụ trách duyệt**. Markdown giải thích policy; worker không tự biến đoạn văn bất kỳ
thành quyền. Thay đổi policy/checker/test bắt buộc đi qua maintenance review riêng,
không được dùng chính bản sửa chưa duyệt để chứng nhận candidate cùng lượt.

## 3. Packet chủ động — không chỉ giao link Markdown

Controller tạo packet từ baseline được người dùng đặt trong scope, gồm:

1. Instructions áp dụng + brief + request thật + một task đã duyệt scope.
2. Contract/placement sections bắt buộc, bytes/version/hash và source classification.
3. Exact readable paths và exact writable paths/operations — **hai tập khác nhau**.
4. Tiêu chí acceptance, fixed check profile, quota, thời hạn, pending decisions/gates.
5. Định danh repo/task/job/generation, policy/checker/input-manifest digests.

Nội dung được đưa vào input bằng kênh instructions/data riêng phù hợp runtime.
Hash receipt chỉ chứng minh packet được chuẩn bị/giao đúng bytes, không chứng minh
model đã đọc hoặc hiểu. Context budget phải dùng tokenizer của model thực + reserve
cho tools/output; thiếu required input hoặc quá context thì chia task, không cắt rules.
Không suy budget model phát triển từ BGE-M3.

Snapshot không đồng nghĩa copy toàn working tree: chỉ đưa files đã duyệt; không
credentials, `.git` metadata/hooks/config, caches, private/quarantine data, raw journal
hoặc evaluator secrets. Dirty tracked/untracked file chỉ được đưa vào snapshot khi
người giao việc nhận biết nó thuộc baseline; không tự stash/reset/commit để làm sạch.
Read-only copy không được tạo bằng hardlink tới host. Worker không tự tải các URL
trong packet; yêu cầu thêm context là đề xuất scope, không tự cấp quyền đọc.

Đầu tiên chỉ thử synthetic/public-safe text. Hosted inference/provider egress cần
quyết định riêng: network của test executor luôn tách khỏi gateway gọi model.
Không thể vừa mở full network cho worker vừa gọi đó là local-only isolation.

## 4. Changeset đầu tiên — chọn format nhỏ để kiểm được

**Đề xuất cho prototype:** JSON changeset UTF-8 version 1, không nhận raw Git diff,
archive hoặc executable script. “Patch-only” mô tả cách giao thay đổi, không bắt buộc
là định dạng unified diff. Prototype chỉ validate trong bộ nhớ trên fixture synthetic,
không ghi candidate vào filesystem/repo thật và không gọi model.

| Trường | Yêu cầu thiết kế |
|---|---|
| Envelope | `schema_version`, `job_id`, `generation`, `base_manifest_sha256`, `changes`; đúng keys/types, reject duplicate/unknown keys, không coercion |
| Mỗi change | `path`, `operation`, `before_sha256`, `content_utf8`; không command, URL fetch, mode, permission, target ref hoặc approval field |
| Operations | Chỉ `create` và `update` regular text file; create yêu cầu path vắng tại base, before = null; update yêu cầu before hash khớp exact bytes |
| Text | Giữ exact UTF-8 bytes sau decode/encode; reject BOM, NUL, invalid UTF-8/lone surrogate; không tự trim, normalize newline hay sửa whitespace |
| Paths | Repo-relative POSIX canonical, exact match allowlist; ASCII path ở v1 (nội dung tiếng Việt vẫn UTF-8), không auto-correct tên |
| Kết quả parser | Typed valid candidate hoặc lỗi rõ; đây không là verified/approved/accepted |

Reject absolute/drive/UNC/device paths, `.`/`..`, slash lặp, backslash, colon/ADS,
glob, control chars, phần tên kết thúc dot/space, Windows device names kể cả có
extension, case-fold collision và file/directory prefix collision. Không hỗ trợ
Unicode filenames ở v1; phải khai báo giới hạn này, không silently exclude.
Không percent-decode/URL-decode path; không nhận aliases để khớp allowlist. ID/hash
được parse đúng định dạng, generation là số nguyên dương, không bool/float/string.
Mỗi segment v1 chỉ có ASCII letters/digits/underscore/hyphen/dot, bắt đầu bằng
letter/digit; dấu `%`, whitespace và các cách viết tên ngoài tập này đều reject.
Kiểm collision với cả baseline manifest, không chỉ giữa các changes. Allowlist
không được biến directory hoặc protected file có tên alias thành writable file.

Reject delete, rename/copy, binary, symlink/junction/reparse, hardlink, submodule,
permission/executable-mode change, `.git*` controls, `.env*`, package/lock/install hooks,
baseline/policy/checker/approval writes. Mỗi path chỉ một operation; giới hạn này áp dụng
cả trước lẫn sau materialization, không chỉ header do worker khai báo.

Prototype valid fixtures chỉ sửa exact synthetic `docs/notes/*.md` paths trong grant
(ký hiệu này mô tả họ fixture, **không dùng glob như quyền ghi**). Khi thử end-to-end
đầu tiên cũng chỉ docs thường, không instructions/contract/policy authority. Không
cho code sản phẩm qua đường docs. Syntax hợp lệ không đủ chấm ý nghĩa tài liệu.

Raw diff support là phần mở rộng riêng: Git có checks cho đường dẫn nhưng chúng
không thay resource/action policy; không dùng `--unsafe-paths` hoặc patch flags do
worker chọn. [Git apply](https://git-scm.com/docs/git-apply#Documentation/git-apply.txt---unsafe-paths).

## 5. Candidate và chuỗi bằng chứng

Luồng đích (đặc tả, chưa thực thi): **duyệt scope → đóng packet → worker đề xuất →
validate → seal candidate → checks → review → accept snapshot**. Chạy tests cần
sandbox đã kiểm chứng; không đạt prerequisite thì dừng trước bước đó.

### HP-I01..08 — invariants

| ID | Invariant bắt buộc |
|---|---|
| HP-I01 | Worker/test executor không thể ghi protected repo/control store hoặc đọc ngoài grant bằng mọi tools được cấp |
| HP-I02 | Policy/grant do trusted side cấp, gắn đúng repo/task/generation và không bị source/worker sửa |
| HP-I03 | Candidate chỉ chứa exact operations/bytes hợp scope, được dựng từ đúng full base manifest |
| HP-I04 | Receipt gắn candidate/input/profile/checker/runtime digests; old PASS không áp cho bytes khác |
| HP-I05 | Candidate code/tests không chạy với quyền của validator/promoter, không tự chứng nhận bằng stdout |
| HP-I06 | Review + grant còn hiệu lực tại điểm accept; cancel/revoke được serialize cùng accept |
| HP-I07 | Acceptance là một snapshot được tiếp nhận nguyên khối; duplicate/crash không tạo partial acceptance hoặc ghi đè user work |
| HP-I08 | Báo cáo phân biệt đề xuất, thử nghiệm, verified, reviewed, accepted; không nâng thành product GO |

Sealed candidate do controller copy từ dữ liệu đã validate vào storage worker không
ghi được, giữ manifest đầy đủ path/type/byte hashes. Không giữ reference tới outbox
mutable của worker. Test dùng bản sao tách riêng; artifact sau test không tự trở thành
candidate mới. Nếu formatter/test sửa source, phải xuất candidate mới và verify lại,
không mang kết quả từ candidate cũ. Policy phải phân biệt scratch outputs với source
bằng inventory độc lập, không dùng `.gitignore` của worker làm danh sách loại trừ.

Receipt tối thiểu: controller-assigned job/event/generation, base + candidate + packet
digests, grant/policy/checker bundle digest, interpreter/dependency/environment profile,
check IDs/expected count/exit/timeout/skips, attempt, timestamps, limits, outcome.
Checker bundle phải bao phủ **mọi** module/config/trusted regression mà verifier nạp;
chỉ hash hai CLI files như journal hiện tại không đủ cho enforcement mới. Test discovery
không để worker xóa/đổi tên tests nhằm làm số lượng 0 mà vẫn PASS. New worker tests là
evidence bổ sung, không tự thay protected required regressions.

Trusted validation không import candidate Python/JS, `.pth`, `sitecustomize`, plugins,
Git hooks/filters/config, package lifecycle scripts hoặc modules shadowing stdlib.
Runtime/interpreter/env/CWD/PATH/import paths và tools phải đến từ release được pin,
không từ candidate. Khi cần thực thi code/tests của candidate, sandboxed executor
chạy fixed profile với môi trường sạch; code được gọi qua một command cố định vẫn
là untrusted execution. Receipt do supervisor độc lập ghi từ quan sát thực, không
parse chuỗi `PASS` do candidate in như bằng chứng độc lập.

Exit 0/số test do candidate báo không chứng minh assertions đã chạy: candidate ở
cùng interpreter có thể monkeypatch runner hoặc thoát sớm. HPC-2 phải review đường
quan sát protected required tests (ví dụ black-box checks từ observer ngoài worker),
và không nâng self-reported counts thành trusted completion. Sandbox giới hạn tác
động của code xấu, không làm kết quả code xấu tự động đáng tin. Phần này chưa implement.

Logs/diff/evidence hiển thị dạng escaped text; không render HTML tùy ý, mở URL,
load remote image hoặc chạy terminal escape/command từ nội dung. Output/log có cap,
redaction và quyền đọc; không log raw prompt/source/private content mặc định.

## 6. Currentness, accept, cancel và recovery

**Không áp nhiều file lần lượt vào `E:/Academic-assistant` rồi gọi đó là atomic.**
Thiết kế ưu tiên protected immutable snapshot + một accepted pointer; mở/cập nhật
working checkout là thao tác riêng có user review, không thuộc slice đầu.

- Chỉ accept khi exact candidate + required verification receipt + actual reviewer
  decision cùng revision, grant chưa hết hạn/revoke, đúng active generation/attempt,
  và expected accepted-base vẫn đúng. Reviewer identity lấy từ kênh kiểm soát bên
  ngoài worker; field `reviewer: Alice` trong JSON/Markdown không phải bằng chứng.
- Serialize cancel/revoke/accept trong một authority. Mỗi operation có unique ID,
  fingerprint đầy đủ và expected predecessor/fence. Cùng ID/cùng payload là retry
  của observation cũ; cùng ID/khác payload bị reject. ID mới không được bypass
  uniqueness của acceptance theo job/generation/candidate.
- Acceptance có một điểm commit rõ. Cancel/revoke commit trước điểm đó → không
  accept; đến sau → báo `already_accepted` và yêu cầu remediation/recovery riêng,
  không giả vờ đã thu hồi side effect xảy ra. Callback muộn từ worker/tests không
  tự mở lại job hoặc chuyển generation cũ thành hiện hành.
- Candidate digest, checker/policy/input bundle hoặc base đổi → evidence stale;
  phải review/revalidate tương ứng. Không tự rebaseline, fuzzy apply, auto-merge hoặc
  dùng PASS cũ sau một verify mới pending/failed/cancelled. Marker/hash không tự cấp quyền.

**Candidate implementation direction cho accepted pointer:** trusted Git ref update
với expected old object, dùng private controller-owned store, không nhánh đang checkout
của người dùng. Git hỗ trợ kiểm old object khi cập nhật ref; đó không phải transaction
cho OS files, SQLite và audit cùng lúc. [Git update-ref](https://git-scm.com/docs/git-update-ref).
Không cấu hình Git/ref/storage trong lượt này; HPD-04 bên dưới còn pending.

Phải có durable intent trước accept và immutable receipt liên kết operation ID,
base/candidate/decision vào accepted record. Nếu crash sau cập nhật pointer nhưng
trước journal completion: reconcile từ accepted record đáng tin cậy, không chạy lại
side effects hoặc tự báo failure/success từ một dòng DB thiếu. Không dùng transaction
SQLite để tuyên bố atomic cross-store. Nếu không phân biệt được committed/uncommitted,
giữ `reconciliation_required`, không overwrite/reset để tiếp tục. Sau durable intent
nhưng trước commit mà current grant/review không còn hiệu lực thì không accept.

Với repo hiện tại đang dirty: không coi HEAD là toàn bộ baseline, không backup bằng
checksum và không rollback bằng reset. Source snapshot cần exact bytes của phần
được phép; controller không sửa working tree này trong slice đầu. Accepted patch
không có nghĩa đã checkout/merge/deploy hoặc học liệu được restore/publish.

Recovery giữ snapshot cũ + mới và receipt theo retention đã duyệt. Khôi phục là một
thay đổi mới có scope/review/current-base check; không xóa audit hoặc tự ghi đè sửa
đổi mới của người dùng. Nếu nghi lộ secret, revert code không thay credential rotation.
Không tự xóa tmp/DB/snapshots; backup/retention cần HPD-07, journal hiện tại không phải backup.

## 7. Budgets đề xuất cho slice nhỏ — chưa benchmark/freeze

| Limit | Giá trị khởi điểm đề xuất | Khi vượt/thiếu |
|---|---|---|
| Changeset request | 1 MiB bytes; JSON nesting ≤ 6 | Reject trước allocation/parsing không giới hạn |
| Output files | 1..10; ≤ 256 KiB/file, ≤ 768 KiB tổng content | Reject toàn candidate; không nhận phần vừa budget |
| Path | ASCII ≤ 180 chars, ≤ 12 segments | Unsupported/reject, không truncate |
| Input packet | ≤ 64 files, ≤ 4 MiB + model-token check khi có model | Chia task trước dispatch; không bỏ required rules |
| Pure validation | 10s wall, một candidate mỗi job attempt | Timeout fail closed; không tự retry |
| Test executor về sau | 300s tổng, 60s/command, 2 GiB RAM, 32 processes, 256 MiB scratch | Host-level limits + kill toàn process tree; chưa cấu hình/chạy |
| Output/log | 256 KiB/job, tổng controller queue ≤ 10 candidates | Quota trước khi spool; cap không che status/missing evidence |
| Retry/fan-out | 0 auto retry, 1 active candidate/job, 1 writer/promotion scope | Retry cần quyết định mới; generation/fence vẫn bắt buộc |
| Model/network/install | 0 cho prototype; test executor network deny | Hosted inference là profile riêng, chưa được chọn/cấp quyền |

Admission cần cap raw request lẫn decoded content, regex/path matching bounded,
total execution gồm setup/verification/cleanup. Không gọi tên limit trong JSON như
đã có OS enforcement. Chưa chọn worker/model nên chưa đặt tổng token/cost hợp lệ
cho một model run; không suy nó bằng zero chỉ vì chưa đo.

## 8. Rollout và quyết định cần review

| Checkpoint | Đầu ra và điều kiện đi tiếp | Hiện trạng |
|---|---|---|
| HPC-0 — design review | Review HPD-01..08, invariants và test map; chốt scope prototype | Packet của lượt này, user review pending |
| HPC-1 — offline validator | Schema/path/bytes/budget + synthetic tests, chỉ trong bộ nhớ; không apply/execute | 2026-09-08: pure parser subset có tests; xem PATCH-VALIDATOR. Hard deadline/packet admission chưa implement; checkpoint chưa được nghiệm thu |
| HPC-2 — real isolation | Chọn môi trường và chứng minh worker/tests không chạm host controls/secrets/network trái quyền | Có boundary draft HPC2-BOUNDARY-CONTRACT, chưa chọn/cấu hình hoặc host tests |
| HPC-3 — synthetic acceptance | Verify/review binding, concurrency/cancel/crash recovery trên store synthetic; không repo người dùng | NOT RUN, phụ thuộc HPC-2 cho execution |
| HPC-4 — limited adoption | User duyệt host controls/backup/reviewer channel, thử một task docs thường và audit độc lập | Chưa được cấp quyền; không product GO |

| Decision | Đề xuất / điều cần chốt | Ai quyết định và chặn gì |
|---|---|---|
| HPD-01 Format/scope | Typed UTF-8 create/update, docs synthetic, không raw diff/delete | 2026-09-08 user cho phép bounded prototype qua “tiếp tục”; format thử v1 chưa freeze hoặc sign-off toàn design |
| HPD-02 Isolation | Worker/test executor khác trust domain; cân nhắc Windows Sandbox/VM hoặc môi trường tương đương có kiểm thử | User + host operator trước HPC-2; chưa khảo sát cấu hình máy |
| HPD-03 Controls/checker | Pinned release/input allowlist/trusted regressions ngoài worker; cơ chế cấp/thu hồi grant | Maintainer/security review trước claimed enforcement |
| HPD-04 Accepted storage | Immutable candidate + protected pointer/CAS; không multi-file checkout atomic | Maintainer trước HPC-3; crash reconciliation phải có bằng chứng |
| HPD-05 Review identity | Kênh approve của user độc lập worker, decision gắn candidate/fence/current grant | User/maintainer trước HPC-3; label self-declared không đủ |
| HPD-06 Quotas/provider | Giới hạn bảng trên là đề xuất; worker/provider và inference egress chưa chọn | User trước model/network/paid operation; test limits trước HPC-2 |
| HPD-07 Audit/recovery | Protected evidence store + retention/backup/secret-redaction; journal hiện tại chỉ diagnostics | User/maintainer trước HPC-4, không tự migrate/export DB |
| HPD-08 Product separation | Không ASTRA bypass, không thay plan/state/source gate bằng patch accepted | Giữ bắt buộc ở mọi checkpoint; explicit product GO riêng vẫn chưa có |

Trên Windows, không mặc định Sandbox configuration là network-deny hoặc mapped
folder read-only: Microsoft mô tả networking mặc định bật và mapped-folder ReadOnly
mặc định false. Vì vậy cần cấu hình và kiểm tra thật trước khi tuyên bố cách ly.
[Microsoft Windows Sandbox](https://learn.microsoft.com/en-us/windows/security/application-security/application-isolation/windows-sandbox/windows-sandbox-configure-using-wsb-file).

Đề xuất least-privilege/action validation và human review là defense-in-depth, không
chứng nhận an toàn hoặc bảo đảm model tuân thủ 100%.
[OWASP agent/tool defenses](https://cheatsheetseries.owasp.org/cheatsheets/LLM_Prompt_Injection_Prevention_Cheat_Sheet.html#agent-specific-defenses).
Các nguồn chính thức được đọc 2026-09-07; lựa chọn format/budgets/rollout ở đây là
đề xuất của dự án, không phải lời hứa hay cấu hình đã triển khai từ các nguồn đó.

## 9. Đo và cách dùng với harness hiện tại

[Test map](PATCH-ONLY-TEST-MAP.md) tách parser, host isolation, receipt/acceptance và
semantic review. Báo attempted/blocked/escaped/accepted/rejected/pending, profile
version, numerator/denominator, exclusions và positive controls. Không lấy tỷ lệ
unit-test pass làm tỷ lệ obey của agents; zero escaped trong bộ nhỏ không là zero risk.

Current `check-task/begin/verify` vẫn không đổi. Không có lệnh `launch`, `apply`,
`accept`, `sandbox` hoặc approval switch mới. Không đưa fields changeset/receipt vào
JSON task card hiện hành. Local journal có thể ghi bằng chứng docs/checks đã chạy,
nhưng không làm trusted grant store hoặc tự nâng finding thành accepted code.

Điểm tiếp tục cập nhật 2026-09-08: prototype đã qua một vòng review read-only; boundary
contract HPC-2 đã được soạn để comparison/prerequisites read-only trước lựa chọn môi
trường. Không xem review là checkpoint acceptance. Không triển khai toàn launcher/promoter
hoặc cấp host privileges theo một câu “tiếp tục”. Nếu thiếu quyền thực để cưỡng chế,
vẫn có thể làm draft/diagnostic nhưng phải gọi đúng mức đó. Design/handoff ngày
2026-09-07 là evidence lịch sử, không được đọc như đã chạy prototype khi đó.
