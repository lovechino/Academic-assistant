# WP-04 review packet handoff v0.1

2026-09-07. Request: user đồng ý scope text-first/visual-limited và chuẩn bị WP-04/Astra, sau đó “Tiếp tục”. Status: verified_local cho kiểm tra cơ học, needs_Astra_review cho workflow. ASTRA đã thông báo trong hội thoại; **chưa có review output hoặc explicit product GO**.

## Scope và baseline

Card [WP04-REVIEW-PACKET-01](../harness/tasks/WP04-REVIEW-PACKET-01.json); run `wp04-review-packet-01-r1`, baseline 209 Git-visible paths sau governance transaction và card, trước sáu output edits. Plan SHA `062e9216632341880e66104b9a2955ddc5c965f86b7c75b1bf7bd37950e67b04`. Không resume/rebaseline run cũ sau state change. Giữ nguyên preexisting user/research edits, không commit/push.

Đã tách [governance transaction](../harness/WP02-WP04-reconciliation.md): user scope confirmation, brief/plan/state/harness recovery nhất quán, next WP-04, ASTRA pending. Transaction đó có frozen-state verify BLOCKED và independent scope/integrity evidence riêng; không gọi nó là PASS của research run này.

## Đã thay đổi

- [Workflow packet](../architecture/10-ai-core-workflow-review-packet-v0.1.md): hai lanes, Q0..Q9, public ports/authority, influence lineage, fenced protected operations, partial/conflict/context, retry/cancel/idempotency, symbolic budget ledger, telemetry, dependency candidates và WPD-01..07.
- [Behavior/security map](37-wp04-behavior-security-review-v0.1.md): 26 future WPT review cases, owners/test levels/metrics/checkpoints; không phải đã chạy.
- [Astra guide](../roadmap/04-astra-review-guide-v0.1.md): ordered inputs, copyable read-only prompt, findings template và stop/GO rules; không tự gọi Astra.
- Handoff này; docs index và handoff 36 nối recovery tới packet, state không đổi trong research run.

## Bằng chứng thực thi

`py -3.11 -B scripts/agent_harness.py verify --run wp04-review-packet-01-r1 --require-local-data`: all_checks_passed tại 2026-09-07T00:18:04 UTC, 31/31 harness tests, 733/733 structure checks, 50 Python files syntax-valid, 17 PDF source hashes, skips/failures = []; đúng sáu output paths. `git diff --check` exit 0. Sau self-review bổ sung barrier cho helper/judge model calls ở Q2/Q7 và WPT-14, rerun structure vẫn 733/733; không nhận đó là model behavior test. Handoff kết quả được ghi sau checks; final scope check trên cùng baseline, không rebaseline.

Public read-only upstream license/model-card check cho FlagEmbedding/BGE-M3, pypdf và Tesseract ngày 2026-09-07; links/caveats ở packet §10. Không pin release/commit hoặc chọn/install product dependencies; không license/legal clearance cho corpus. Mermaid diagrams được kiểm ở mức source bằng self-review, chưa chạy renderer visual QA.

### Artifact fingerprints để đối chiếu lúc giao review

SHA-256 đọc từ bytes sau self-review; không là chữ ký hoặc immutable Git commit. Nếu file đổi phải reviewer pin lại, không áp verdict cũ sang revision mới. Input contracts/brief/plan cũng cần snapshot lúc reviewer bắt đầu.

| Artifact | SHA-256 |
|---|---|
| Workflow packet 10 | `2229862cb41d498ab620a345e6eb9421276f959b664eff79775f05faa918f4e5` |
| Test map 37 | `6f811812906208e19f1339fe996451f3c2d9d158e885fd696e1c23dfe98a8715` |
| Astra guide 04 | `d6b4b472185e29a4ec26cebf8ef70b91cabe4845460fe39a0bb6b6f7d747b33d` |

Không chạy WPT/RC integration, RAGAS, semantic scorer, model/OCR/parser benchmark, PDF processing hoặc historical helper. Không sửa code, data, contracts, registry, runtime dependency manifests, harness checker hoặc approvals. Các kết quả historical ở references giữ đúng ngày/phạm vi, không nhận là tests của run này.

## Self-review và residual risks

ARCH-02 giữ nguyên; không agents tự chủ/tool escalation. First slice text-first không xóa visual requirement; enough A/B cho compare, SIM-03 chỉ supported partial. No-hit khác operational error, oracle labels không vào generator. Auth envelope không model-visible; release rechecks full influence set, không chỉ citations. Deferred admission/index lane không kéo upload/OCR vào first code.

Q state names/ports là review proposals, chưa schema freeze/runtime. Atomic admission/fencing, durable idempotency/cancel ordering chưa có implementation proof; fake tests chưa chạy. Generator/semantic verifier/thresholds/budgets, rights/labels/calibration và source fidelity còn pending; WPD table chỉ rõ checkpoint. Không tuyên bố deterministic checks bảo đảm semantic truth hoặc prompt injection đã giải quyết tuyệt đối.

Same-assistant self-review không là Astra/human review. Reader phải xem packet và actual findings trước GO; control snapshot giữ pre_product_research và không có approval switch.

## Handoff tiếp theo

Đọc Astra guide và packet/test map; người dùng có thể giao reviewer read-only theo prompt. Chờ review findings thực; generic continue chưa có findings chỉ phục hồi trạng thái/chuẩn bị review, không P6. Sau nhận findings, sửa trong bounded task nếu được giao, rồi user explicit scoped GO sau review. Không tự tạo thread, thay model, cài stack hoặc gửi nguồn ra provider.
