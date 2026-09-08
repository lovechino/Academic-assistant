# WP-04 repair + material recovery: affected review/handoff v0.1

2026-09-07. Status: corrected documentation draft / needs user review, verification recorded below. User requested fixes for three prior findings in docs/contracts/test map, affected-part re-review and accidental-file-delete recovery. Interpreted as learning materials, not repository files. No runtime code, installs, model calls, PDF processing, historical generators, external processors, data edits, commit or push by this task. ARCH-02 controlled multi-step/one reasoning role/manual Academic preserved. Recovery is future lifecycle scope, not first fake QA code.

## 1. Review source and baseline reconciliation

Findings originate from the immediately preceding read-only review in this conversation. Labels WP04-F01..03 below disambiguate them from historical WP01 F-01..09. Exact reviewer model/settings and independent Astra identity are unknown/not independently verified; no new external reviewer was invoked. This repair's re-review is same-assistant self-review, not independent/human acceptance. No observed runtime defect is claimed because product runtime is absent.

Card [WP04-REPAIR-RECOVERY-01](../harness/tasks/WP04-REPAIR-RECOVERY-01.json) created before baseline: documentation-only, 17 exact output paths, fixed harness/structure checks; card itself is not output authority. Run `wp04-repair-recovery-01-r1` began at HEAD `54b405da8f549f68835626b1f03d8c41cd233573`, 214 Git-visible files. First multi-file patch failed context validation and applied no output edits. After interruption, another actor's commit changed HEAD to `d7e89e4`; `check` returned BLOCKED: HEAD changed. Do not label r1 PASS.

Read-only reconciliation compared all baseline file SHA-256 values and the complete Git-visible path set: zero changed/missing/added files, 214 paths; working tree clean. The commit captured existing bytes including the prepared task card, not these repairs. User was notified; original r1 baseline was not overwritten. Continuation `wp04-repair-recovery-01-r2` began with the same checked card at the new HEAD before output edits. A later patch context error also applied no changes; successful patches stayed within scope. No checker/state/card edits to bypass failures.

Authoritative unchanged plan SHA-256: `062e9216632341880e66104b9a2955ddc5c965f86b7c75b1bf7bd37950e67b04`. State still pre_product_research, WP-04, ASTRA pending_review_and_explicit_user_go. Recovery chain remains state → scope record → handoff 36 → historical 38 → this record; no governance/control mutation.

## 2. Prior findings and repair disposition

### WP04-F01 — P1, design gap: validation-to-public-content binding

- Evidence: [evidence contract §4/4.1](../../contracts/evidence-packet.md), [packet Q7–Q9 / sequence / ports](../architecture/10-ai-core-workflow-review-packet-v0.1.md), [HTTP boundary](../../contracts/http-api.md). Prior draft validated an answer then described sanitized delivery without explicit immutable content/verdict binding.
- Counterexample: validate a superscript formula, sanitize to plain `x2`; or attach verdict A to another draft B in the same request. Locator/auth can remain valid while meaning changes. Violates “delivered claims/citations are exactly validated”; impact wrong mathematics/context or unsupported output.
- Fix: safe canonical public candidate before semantic validation, immutable candidate/draft/packet/input/influence/profile bindings, release exact accepted candidate plus independent current policy/fence; meaning-changing edits invalidate verdict. Renderer fidelity is separate from hashes; no implicit trustworthy model verdict.
- Affected re-review: same-input/different-output and sanitizer schedules are now explicitly rejected by the draft. Harmless faithful escaping is allowed; hash alone is not semantic/security proof. WPT-15/26 variants specified, NOT RUN. Exact schema, validator and renderer tests remain before respective implementation/integration checkpoints; not marked runtime-resolved.

### WP04-F02 — P1, design contradiction: C-04 aliased to CI-02b

- Evidence: [scorer 32 §2/stage separation](32-scorer-specification-v0.1.md), [measurement 17 §3.2](17-measurement-architecture-v0.1.md), [clarification 29 §§3–4](29-review-regression-and-metric-clarifications-v0.1.md). Old row combined resolver and post-pack recall despite different stages/denominators.
- Counterexample: resolver obtains d1,d2, packing loses d2 → expected C-04 2/2, CI-02b 1/2. Combining them masks context loss or assigns the wrong causal stage. Invariant: score stages and reference universes remain distinct.
- Fix: separate rows, observation points, predeclared evaluator anchor/requirement universe, owner and eligibility. Resolver unsupported-modality exclusion cannot flow into post-pack reference recall; omitted anchors/undeclared edges still count. Historical scores/artifacts unchanged.
- Affected re-review: count examples checked on paper only, not executed. WPT-10/12/24 variants specified, NOT RUN. Reference matching/labels and full scorer remain pending; resolve before scorer implementation/config-selection relying on these definitions. Empty valid oracle differs from absent oracle.

### WP04-F03 — P2, design gap: stale frontend callback after view switch

- Evidence: [authorization §6](../../contracts/authorization-context.md), [HTTP request/view binding](../../contracts/http-api.md), [WPT-18/21/26 variants](37-wp04-behavior-security-review-v0.1.md). Prior clear-state requirement did not cover a response already released by Backend and arriving after a tenant/conversation switch.
- Counterexample: valid A release → user selects B/clears UI → A callback renders/caches/appends to B. Backend may have acted correctly; client view isolation still fails. Already-released bytes cannot be recalled.
- Fix: request/conversation/non-reused view-session generation checked before every callback side effect; invalidate before view transition; abort best effort only. Backend binds persistence to original authenticated conversation, not current UI selector. Different conversation with same key is conflict.
- Affected re-review: late terminal/progress/viewer and A→B→A schedules explicitly blocked, still-current positive preserved. WPT owner now includes Frontend. Contract requirement addressed; executable callback/cache/history tests NOT RUN, required before UI integration. Client correlation is never authorization.

## 3. Accidental deletion proposal and affected-scope review

[Recovery policy](../governance/06-material-deletion-recovery-v0.1.md) + [Backend contract](../../contracts/material-recovery.md), linked from lifecycle, permission, authorization, content/index and HTTP docs. Proposes restricted soft-delete → restore-to-review → separately approved republication. No production retention duration or new role grant selected.

Static counterexample walkthrough (not test PASS): old approval/share/epoch cannot revive; delete denies serving before index cleanup; restore/purge ordering must reserve artifacts; refcount check includes concurrent new refs and restore pins; duplicate delete cannot extend deadline; stale restore cannot undo new delete; parent/child and required dependencies remain independent; backup restore needs current tombstone/revoke/purge journal. These are requirements, not claims that storage/PDP implements them. REC-01..08 cover the schedules and positive controls, all NOT RUN.

Residual/open decisions: retention/holds/clock/quotas, role/step-up/dual approval, lifecycle schema, reservation expiry/recovery, physical refcounts/key ownership, derivative inventories, backup RPO/RTO and journal durability. Must resolve before lifecycle/storage implementation or real data checkpoints stated in the contract. Purged/crypto-erased bytes may be unrecoverable. Deletion does not recall bytes sent before its authoritative ordering point.

## 4. Coverage and WPD disposition

Read/re-reviewed affected contents: evidence, HTTP, authorization, content-unit/index contracts; packet 10; metric definitions 17/32 and relevant clarification 29 sections; WPT map 37; governance lifecycle 02/permission 01; new recovery docs; guide 04 and handoffs/index links. Recovered brief/harness/current plan/scope record/ARCH-02 and historical handoff 38. No fresh full audit of every earlier research document, experiment, source corpus, runtime component or external vendor. No PDF inspection, generator reruns or independent review this turn.

| Decision | Disposition after repair | Remaining checkpoint |
|---|---|---|
| WPD-01 | Preserve manual Academic, one reasoning role; no autonomous tools, semantic cache, automatic model retry or prevalidated answer stream in proposed fake slice | User confirms exact first-code scope after review; not GO here |
| WPD-02 | Preserve unknown/unsupported/SIM-03/AND-OR evidence; WP04-F02 stage contradiction corrected | Reference matching/full discovery/semantic evaluation still pending |
| WPD-03 | Add immutable release binding and client generation to existing current-authority fences | D/B schedules after GO; real ordering/durability proof before protected data |
| WPD-04 | Candidate/projection/render and request/conversation boundaries clarified, not schema frozen | Exact supported typed representation/schema and renderer profile before corresponding code |
| WPD-05 | Models/tokenizers/budgets/licenses/egress unresolved, fake finite fixtures do not choose them | Before real model/provider adapters |
| WPD-06 | Rights/reviewers/labels/calibration still missing; restore never bypasses them | Before relevant data use/publication/quality claims |
| WPD-07 | Harness remains research-only; r1 reconciliation does not open runtime permission | Separate harness task linked to actual review + explicit scoped GO |

Verdict recommendation: three reported issues are addressed **at draft contract/test-spec level**; affected-scope self-review found no additional unblocked contradiction in these specific counterexamples. This is sufficient to present the corrected exact fake-QA slice for user/reviewer consideration, not independent Astra acceptance, GO, production readiness or proof of runtime safety. Recovery lane is a separate draft with decisions to close before its implementation; do not make it a hidden expansion of first slice.

## 5. Verification and next handoff

`py -3.11 -B scripts/agent_harness.py verify --run wp04-repair-recovery-01-r2 --require-local-data` returned `all_checks_passed=true` at `2026-09-07T07:44:09.192317+00:00`: 31/31 harness methods, 774/774 structure checks, 50 Python syntax checks, 17 PDF source hashes, skipped/failures = []; exact 17 output paths. Hash verification is not PDF parsing/processing. `git diff --check` exit 0. Following verification, only scorer subsection placement, guide wording and this evidence record were finalized; final structure/scope checks use the same r2 baseline, not a new run. Mechanical checks are not semantic acceptance.

New WPT variants/REC tests, real auth/storage/renderer integration, RAGAS/human calibration and model behavior are NOT RUN. Historical arithmetic/context scores have not been regenerated. Mermaid source reviewed textually, not rendered/visually tested.

Repair snapshot fingerprints (SHA-256 of local bytes, not a signed commit or reviewer approval; other contracts must also be pinned by the next reviewer):

| Artifact | SHA-256 |
|---|---|
| Packet 10 | `06b14602e24a2520adeeb67db5d4f6ea00cd757a882c12475074383da3378bba` |
| Test map 37 | `4a8d00a24ac9904c1c35a73be59b280197b47a84c1c8f1fd62371d14ca5a31ce` |
| Guide 04 | `dc3b866457864a11e123eed73fbf19295ea168c87f26a8a4a27b89f164790102` |
| Recovery contract | `bfce2bf7f1b8884e24739c5e34f6e16b89ad341e0de9c4d70fbe30990b581250` |
| Recovery policy | `f95ee4d5ca3500f714889c23b5f7883825192072a368aede417f48a33c442229` |

Next: user/reviewer examines these repairs and recovery proposal; independent ASTRA review if not established, then explicit GO tied to the exact packet revision/slice before runtime. Retention duration and privileged recovery role choices can wait for the separate lifecycle package. Generic continue is not product GO or permission to delete/restore actual files.
