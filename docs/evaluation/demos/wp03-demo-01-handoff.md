# WP03-DEMO-01 — từng bước chạy harness

Ngày: 2026-09-06. Status: **verified_local**. Task: kiểm kê một report theo yêu cầu “thử chạy một task”. Worker và self-review là assistant hiện tại; không spawn agent/model khác, không API/model comparison và không independent human sign-off.

Card: [WP03-DEMO-01](../../harness/tasks/WP03-DEMO-01.json). Run: `wp03-demo-01-r1`. Baseline: `tmp/agent-harness/wp03-demo-01-r1.json`, 181 Git-visible paths; card được soạn trước baseline, hai output được tạo sau begin. Baseline giữ preexisting dirty/untracked work, không chứng minh ignored files hoặc remote operations.

## Step log

| Step | Hành động | Kết quả thực tế |
|---|---|---|
| 1. Orient | Đọc AGENTS/brief/harness, master plan và report; chạy `status` | Stage pre-product; next WP-03; ASTRA pending |
| 2. Scope | `check-task --task docs/harness/tasks/WP03-DEMO-01.json` | Valid declaration; đúng WP-03, documentation only, hai exact output paths |
| 3. Baseline | `begin --task docs/harness/tasks/WP03-DEMO-01.json --run wp03-demo-01-r1` | Baseline created; 181 paths, không ghi đè run cũ |
| 4. Execute | Hash inputs, đọc report/README/test source, đếm bằng `rg` | 23 method declarations; 9 findings; 21 unique RC IDs; inventory bốn evidence classes |
| 5. Self-review | Đối chiếu bảng với source locators và acceptance | Giữ historical vs NOT RUN; RC-14 partial coverage; không suy accuracy hoặc quyền từ fixtures |
| 6. Verify | Local harness/structure/scope và whitespace | PASS: 31/31 harness tests; 604/604 structure checks; 17 PDF hashes; không skip; hai output paths đúng allowlist |

Đầu ra nội dung: [evidence inventory](wp03-demo-01-evidence-inventory.md). Card không cho sửa docs index, source report, code, state/master plan hoặc data nên các file đó giữ nguyên. Không cần cài package, rerun historical generators hoặc sửa sản phẩm.

Lệnh kiểm tra chạy thật:

```powershell
py -3.11 -B scripts/agent_harness.py check --run wp03-demo-01-r1
py -3.11 -B scripts/agent_harness.py verify --run wp03-demo-01-r1 --require-local-data
git diff --check
```

`verify` exit 0; 48 Python files syntax-checked. Đối chiếu thêm ba SHA-256 thực tế với hashes ghi trong inventory: 3/3 khớp. Các số 31/604 là local checker results mới, tách biệt khỏi 23/554 historical trong report S1. Không có lỗi scope được quan sát trên Git-visible delta; không diễn giải thành zero security risk hoặc model accuracy 100%.

## Chưa chạy / chưa được suy ra

- 23 context regression methods: demo này chỉ đếm declarations và đọc historical report, không rerun behavior.
- 21 RC integration cases: vẫn NOT RUN. Bốn evidence classes không là bốn test case có nhãn.
- Chưa thử model nhỏ, chưa có H-01..07 model benchmark, chi phí/token usage không đo trong demo.
- Reviewer độc lập và academic acceptance chưa có. Harness pass không thay acceptance nội dung hoặc GO.

## Điểm bàn giao

Tiếp tục WP-03 inventory các packs còn lại nếu được giao; dùng source hashes và loại bằng chứng của demo làm mẫu, không copy số historical như run mới. Kế hoạch/state giữ nguyên; task nhỏ này không hoàn tất WP03-01 card lớn, toàn WP-03 hoặc ASTRA-01. Không tự mở WP-02/P5/P6.
