# HPC-1 — synthetic in-memory changeset validator

2026-09-08. Profile `hpc1_synthetic_notes_v1`; tooling prototype **verified local /
needs review**, không phải sandbox, applier hay approval service. User “tiếp tục”
cho phép prototype nhỏ sau [design](PATCH-ONLY-DESIGN.md), không ký toàn bộ HPD-01..08.
[Card](tasks/HARNESS-PATCH-02.json), [evidence handoff](HARNESS-PATCH-02-handoff.md).

## 1. Đã có và cách thử

[Implementation](../../scripts/harness_patch_validator.py) nhận bytes JSON và context
synthetic do bên gọi cung cấp, trả immutable typed candidate hoặc `ValidationError`
với static error code. Không đọc/ghi filesystem, Git, DB, network hoặc thực thi nội
dung candidate. CLI chỉ có demo tích hợp; chưa nhận file thật, stdin hoặc lệnh apply.

```powershell
py -3.11 -B scripts/harness_patch_validator.py --demo
py -3.11 -B -m unittest discover -s scripts/tests -p test_agent_harness_patch_validator.py -v
```

Demo thực chạy: một create tiếng Việt → `valid_in_memory_only`, 1 file / 38 content
bytes; đổi path sang file không được grant → `OUT_OF_SCOPE`, `applied: false`.
Không file nào được áp bởi demo, không đăng ký finding giả hoặc gọi model.

API hiện tại: `make_context(job_id=..., generation=..., baseline=..., allowed=...)`
nhận hai dict riêng `path -> bytes` và `path -> create|update`, copy thành frozen
tuples. Sau đó `validate_changeset(raw_bytes, context=context)` kiểm toàn candidate.
Context không nhận từ trường tự khai trong changeset. **Caller vẫn có thể tự tạo
context giả**; chưa có authenticated controller. Không nối API này với quyền host.

## 2. Wire contract và byte identity

Envelope đúng năm keys: `schema_version` (integer 1), `job_id`, `generation`,
`base_manifest_sha256`, `changes`. Mỗi change đúng bốn keys: `path`, `operation`,
`before_sha256`, `content_utf8`. Duplicate keys ở mọi object và unknown keys bị reject;
không coercion, không float/NaN/Infinity, bool không là integer hợp lệ.

- `create`: exact path/action grant, path vắng trong baseline, before = JSON null.
- `update`: exact path/action grant, path có trong baseline, before = SHA-256 bytes cũ.
- Hash wire phải là 64 ký tự lower-case hexadecimal; không normalize.
- Giữ UTF-8 content sau JSON decode, LF/CRLF/whitespace và empty text; không tự trim.
  Reject wire UTF-8 BOM, content bắt đầu U+FEFF, NUL, invalid UTF-8/lone surrogate.
  U+FEFF nằm giữa text không bị cấm. Empty text hợp schema, chưa chắc đạt task.
- Không nhận delete/rename/copy/binary/mode/link/submodule, archive hoặc raw diff.
  Không kiểm được loại file thực: baseline chỉ là synthetic bytes do caller cung cấp.

Baseline manifest là SHA-256 canonical JSON gồm profile và sorted
`[path, "regular_utf8", sha256(bytes)]` cho **mọi** baseline file, kể cả read-only.
Context digest thêm job/generation và sorted exact path/action grants. Candidate
digest thêm sorted changes `[path, operation, before_sha256, sha256(content)]` vào
context digest. Canonical JSON dùng sorted object keys, separators `,`/`:`, ASCII
escaping. Request digest tách riêng, hash exact wire bytes. Đổi JSON whitespace/key
order có thể giữ candidate digest nhưng đổi request digest; đổi baseline/grant/bytes
thay binding. Đây không là Git tree, signed receipt, full packet hay backup.

Result chứa frozen tuples và immutable bytes, không tự trả mutable file tree hoặc
áp từng change. Nếu một change lỗi thì không trả candidate một phần. Python frozen
dataclass ngăn mutation thông thường, **không** là boundary chống cùng-process actor.
Gọi lại trả cùng diagnostic, không chứng minh exactly-once acceptance/replay defense.

## 3. Exact scope và giới hạn prototype

Chỉ exact synthetic paths dưới `docs/notes/`, đuôi `.md`, ASCII, POSIX slash.
Nested notes được phép nếu cấp từng path; không glob grants. Segment bắt đầu bằng
ASCII letter/digit, phần còn lại chỉ letters/digits/underscore/hyphen/dot. Reject
absolute/drive/UNC/device/traversal/backslash/ADS, reserved Windows names, terminal
dot/space, percent/glob/control/Unicode filenames. Không normalize hoặc URL-decode.
Kiểm cả file và directory-component case collisions, file/directory prefix aliases
giữa baseline và grants/changes. Mỗi path chỉ một grant và một change.

Không cho component source, scripts, harness controls, `.git`, `.env` hoặc package
files qua profile này; known instruction filenames `AGENTS.md`, `CLAUDE.md`,
`GEMINI.md`, `SKILL.md`, `copilot-instructions.md` cũng bị reject dưới notes.
Một file notes có nội dung policy/code độc hại vẫn có thể hợp schema: cần semantic
review và rendering an toàn về sau; đây không là prompt-injection detector.

| Limit được code kiểm | Giá trị | Lỗi tiêu biểu |
|---|---|---|
| Raw bytes đã được caller cấp | 1..1,048,576 bytes | `REQUEST_LIMIT` |
| JSON nesting / structural punctuation ngoài strings | ≤6 / ≤4096 dấu `{`, `[`, `,`, `:` | `JSON_DEPTH`, `JSON_STRUCTURE_LIMIT` trước decoder |
| Integer lexical length / generation | ≤10 ký tự / 1..2,147,483,647; job ASCII alnum-hyphen 3..64 | `JSON_NUMBER`, `CONTEXT_INVALID` hoặc mismatch |
| Changed files / grants | 1..10 mỗi tập | `CHANGE_COUNT`, `CONTEXT_LIMIT` |
| Decoded content | ≤262,144 bytes/file, ≤786,432 bytes tổng | `CONTENT_LIMIT`, `TOTAL_CONTENT_LIMIT` |
| Path length / segments | ≤180 ASCII chars / ≤12 | `PATH_INVALID` |
| Synthetic baseline | ≤64 files, ≤4,194,304 bytes tổng | `CONTEXT_LIMIT` |

Wire cap và decoded cap đều áp dụng; Unicode JSON escaping có thể chạm wire cap
trước decoded cap. Baseline limits **không** là kiểm required-input packet/model
token budget. Caller đã giữ bytes trước khi gọi; chưa có streaming admission,
concurrency queue cap hoặc OS RAM quota. Depth/punctuation được scan trước
`json.loads`; standard decoder kiểm grammar sau đó. Không tự retry.

**Chưa implement 10s wall deadline** của design, one-active-attempt/fence, queue/log
quota, protected interpreter/import paths hoặc host/process limits. Fixed harness
verify vẫn giới hạn subprocess 60s, không thay deadline/enforcement của validator.
Muốn đưa vào runner thật phải giải quyết các thiếu hụt này; unit-test timing không
chứng minh worst-case deadline. Các mức trên là profile thử nghiệm, chưa freeze.

## 4. Evidence và điểm dừng

36 methods trong [tests](../../scripts/tests/test_agent_harness_patch_validator.py)
đã pass ở lượt focused; có nhiều subtests nhưng không tính từng variant thành một
method. Đây là exposed developer-authored synthetic regressions, chưa nhãn độc lập
hoặc benchmark model. [Test map](PATCH-ONLY-TEST-MAP.md) phân biệt scoped parser
coverage với host/packet/acceptance chưa chạy. Xem handoff cho full verification.

Errors và `.summary()` chỉ có static codes/counts/digests, không raw source/path.
Candidate giữ content để bên gọi sử dụng; không đưa thẳng nó vào logs/Markdown/HTML.
Một test patch các I/O APIs thường gặp và đưa shell/HTML/URL/ANSI vào content: chúng
được giữ như data, không chạy trong validator. Đây không là host egress proof hoặc
frontend rendering test; mã chạy khi import và môi trường Python chưa được harden.

Bước phù hợp tiếp: read-only review prototype + bổ sung đối chiếu design nếu cần,
rồi mới chọn HPC-2 host isolation/quota/control ownership với người dùng. Chưa có
launcher, materializer, receipt verifier, acceptance/CAS, cancel/revoke service,
rollback store hoặc integration với journal. Không áp vào checkout dirty hiện tại.
HPC-3/4, model metrics, quyền/backup/provider đều chưa được nghiệm thu. ASTRA-01 và
explicit scoped product GO vẫn pending; prototype không mở khóa sản phẩm.
