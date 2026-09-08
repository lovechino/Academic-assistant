# HARNESS-SUPERVISOR-01 execution handoff

2026-09-08. **Needs review / host observer blocked**, not enforcement acceptance.

## Authority and placement

User approved packages 1–5, package 6 stops before real model. This bounded card
implements supervisor/transport and staged smoke, not all five packages. No existing
container operations, daemon/WSL changes, installs, secrets, real source/model/PDF
processing, product runtime, checkout promotion or product GO.

OWNER: scripts development tooling. SEARCH: rg files for supervisor/collector,
rg classes/functions/callers in collector/validator, read owner/tests and placement
blueprint/template. DECISION: new supervisor owns real I/O; reuse collector and
validator unchanged. Tests scripts/tests; Python stdlib + existing Docker only.
Exact six outputs in [card](tasks/HARNESS-SUPERVISOR-01.json). check-task/begin
preceded edits; run harness-supervisor-01-r1, 257 Git-visible baseline paths.
Card before baseline; unrelated dirty work, checker, plan/state and approvals kept.

## Execution and honest failures

Fresh preflight: Docker Snap 29.6.1, cgroup v1, memory/swap/pids/CPU support reported;
running=2, WSL available RAM 2501 MiB/swap unused; Windows C/E free
40,866,238,464 / 113,600,655,360 bytes at observation, not reservations.

Public registry manifest/config fetched with anonymous token kept out of output.
Recomputed manifest SHA matches recorded child digest; config SHA:
9356cb064a7cbecce9a3ccba46e7fd5459d3a3e939db884ef7fbf3f757cc5ec8.
linux/amd64, inherited defaults and four diff_ids checked. Pinned pull succeeded;
local image/config/diff_ids checked at admission. Image stays cached; no image
removal/prune. Signatures/SBOM/CVEs not verified, no Dockerfile build/pip install.

Preserved failures: isolated bootstrap initially lacked exact module loading (before
job/create); two admissions rejected before create because child tried to raise
inherited hard CPU limit. Fixed isolated bootstrap/same hard limit and added tests.
Initial Linux unittest invocation used unsupported importable top-level directory;
corrected discovery from repo cwd. No failed attempt silently labeled PASS.

Initial real scenarios: happy validation; fake PASS -> JSON_INVALID; bounded stdout
1 MiB + 8 KiB -> STDOUT_LIMIT; hang -> SYNTHETIC_COMMAND_DEADLINE; cancel ->
OPERATOR_SYNTHETIC_CANCEL. Second happy checked total API timer. Each task-created
exact ID removed and GET 404 confirmed; these are not eight-group HB acceptance.

Observer job academic-hpc2-f1f4a54b473b4108b858645235372c3f, container
49b0a82415496165076b9cbb7ba5b0757ea0bc7d4d0633aa4121209b880bfeff:
host status UID/GID=65532, CapEff=0, NoNewPrivs=1, Seccomp=2; namespace read denied
to observer -> HOST_OBSERVER_NOT_READY, 2.485s, cleanup confirmed absent.
No elevated workaround. Private receipts contain synthetic IDs/hashes/counts and
control fields, not raw proposals/logs/secrets; they are not protected approval.

## Verification and review

Final focused tests: Linux `python3 -B -m unittest discover -s scripts/tests
-p test_agent_harness_supervisor.py -v`: 25/25 passed, zero skips. Windows same
discovery via py -3.11: 21 passed, four explicitly skipped Linux-only methods.
Isolated bootstrap, inherited limits, total deadline and parent process tests are
real local subprocess/signal tests; their Docker transport/cleanup is fake.

Fixed capture supervisor-verify-02 completed 2026-09-08T10:01:29.445413+00:00:
175 harness methods discovered (171 executed on Windows, four Linux skips above),
exit 0; structure 921/921, 60 Python syntax files, 17 PDF source hashes, zero
structure failures/skips. Earlier supervisor-verify-01 was before admission pin
addition, 174 methods; superseded for final source, not rewritten. Journal test
count includes skips and does not itself expose their count: keep this distinction.

Baseline hash: 6f64978f4e433751d1836670c3eb0c1209d24c6014336506ad8462c63f799e48.
Observed tree before this handoff update:
e9861174addcbf2327600d3fcf56b5aeec2198ddda5ead001fc6996480940000.
Final supervisor source SHA: 15492d5663e79d375bf5f00d0f003fe6cc6a889a447e86f943ce7002dfe38b17;
test SHA: ed65c5362526d4ab53b8115ffd7d26a386f459aa462eb6230c6dc00f03df2f9d.
No source/test edits after this verification. Exact six-file scope and git diff
--check passed before capture; scope/structure/diff repeated after handoff update.
No historical generators; integrity checks read hashes only, not PDF processing.

### Final real trials on the final source revision

Every row has confirmed exact-ID absence after cleanup. Nonzero negative exits
are intentional; observer blocked is not counted as a passing security test.

| Scenario | Outcome | Seconds | Exact task-created container ID |
|---|---|---:|---|
| happy | validated_synthetic_only | 0.537 | 43af1f694e5cd0d8c58d1aa34e0d0042757ce215965a472661b13554bd3db222 |
| fake-pass | JSON_INVALID | 0.509 | 717f003107609532bb46e62165c4ff1244f4290cdee2b5f39936ac8daa2439f6 |
| overflow | STDOUT_LIMIT | 0.516 | 70fcfefa1cb30b7186fa0530409be0f700c94cd32292c0679367aab39745b0df |
| hang | SYNTHETIC_COMMAND_DEADLINE | 1.560 | 7c9d85b814e1067521d5b862e62a3895e2f814f3ecae351c6f1f3ff84b8a8f34 |
| cancel | OPERATOR_SYNTHETIC_CANCEL | 1.034 | f824a9bbd1a5025733b00dd8cd527493cd4b5659efb379ad9b3cd08c17d526f8 |
| observe | HOST_OBSERVER_NOT_READY | 2.488 | b34d4088edad0838c19cb71a6fc6d189d19a9b5547b14ee9eba27e0d4a1fc7df |

All six carry admission pins (also on failure): three-module release
9fdefd2f0cc43a343028d3e2d9c8b90ede3eea87885431ffc18cfece21a6c5bc,
profile 05faa84ce471829c7acd5613e77c1ec489f8abb97456ac0befd6cee8659afb92.
Successful result pins are checked against parent admission pins before recording.
Private receipts include per-job packet/context hashes, generation/attempt=1,
image ID; happy candidate SHA
8dd1e15d4c650bce0127add00783410a8112a1deb341cad4cb7dde12dab78281.
These are locally mutable observations, not cryptographic human authority.

Including development repetitions: 18 new containers created/removed, two rejected
admissions without container creation, one pre-bootstrap failure without a job.
Final daemon running count=2. No commands targeted preexisting containers; count
alone is not workload-health evidence. Removed synthetic container scratch is not
recoverable; no user source file deleted. Pinned image and small private receipts
remain local; no accepted candidate/file applied anywhere.

Self-review repaired bootstrap/inherited hard limits/API total-deadline issues.
Parent-death/orphan, lost create/start, observer, mutable host release, ephemeral
receipts, real approval/recovery and model integration remain OPEN in
[supervisor limits](SUPERVISOR.md). Independent review/sign-off not claimed.

## Stop and continuation

Packages 1–3 partially delivered; package 4 blocked on independent observation;
package 5 accept/rollback not implemented/run, package 6 not run. No complete HB
group accepted; no security pass rate inferred. Need user/operator choice for
narrowly privileged observation or dedicated test environment before elevating
host rights. Then reaper/fence + host failure probes, remaining HB controls,
protected synthetic acceptance/crash/restore. Ordinary authorized tooling can
continue; additional host privilege is not inferred. WP-04/ASTRA explicit product
GO remains pending. No claim of production readiness or 100% agent compliance.
