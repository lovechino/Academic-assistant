# HARNESS-COLLECTOR-01 handoff

2026-09-08. Implemented synthetic slice; verified_local, independent review pending.

## Placement packet

- USER_REQUEST: continue the proposed fake-transport collector/controller slice.
- RESPONSIBILITY: bound one in-memory attempt's stream capture and lifecycle.
- OWNER_AND_LAYER: scripts development tooling, not AI Core/backend/frontend.
- CONTRACTS: HPC2-BOUNDARY-CONTRACT §4/6; Docker profile §3–5; preflight next slice.
- EXISTING_SEARCH: rg --files harness/HPC2/PREFLIGHT and rg collect/transport/deadline/
  cancel in agent_harness.py, harness_patch_validator.py and parser tests. Existing
  harness invokes fixed subprocess checks, not a worker stream collector. HPC1 owns
  changeset parsing; no competing collector found in this scoped search.
- DECISION: new scripts/harness_collector.py; reuse HPC1 validator only in integration
  tests; extend existing test discovery without changing checker or validator.
- DEPENDENCIES: dataclasses/hashlib/re only in new source; test fixtures own fake
  transport; no runtime component imports, SDK, package installation or worker I/O.
- EXACT_OUTPUTS: collector, tests, COLLECTOR.md, this handoff, README, test map.
- TEST_PLACEMENT: scripts/tests/test_agent_harness_collector.py, exposed synthetic.
- OPEN_DECISIONS_AND_GATE: no real transport/watchdog/protected store or OS controls;
  ASTRA explicit product GO remains pending, option 2/manual Academic unchanged.
- REVIEW: self-review only; independent review pending.

Card [HARNESS-COLLECTOR-01](tasks/HARNESS-COLLECTOR-01.json) checked and begun before
output edits. Run harness-collector-01-r1, baseline 250 Git-visible files; preserve
preexisting edits and baseline. Six outputs, no plan/state/checker changes.

## Behavior and verification

[Usage and exact limits](COLLECTOR.md). Capture is bytes, not validation/approval.
First focused run passed 21 methods; added two boundary regressions during review
and tightened stopped-event type check. Final focused run: 23 methods passed.

Fixed command: `harness_journal.py capture --run harness-collector-01-r1 --event
collector-verify-01 --phase verify --require-local-data` passed: 143 total harness
methods (120 existing + 23 new), structure 905/905 checks, 58 Python syntax files,
17 PDF source hashes, zero failures/skips. Scope check: six exact declared outputs;
git diff --check exit 0. No checker reconfiguration to discover new tests.

Capture finished `2026-09-08T04:27:29.306125+00:00`, baseline SHA-256
`fa7bf99ddc86dd5365e45f745233438f4110203f8e9ae01cdc2a18df796f9e39`.
Observed tree `e0e3c5e406bf0d34311da255f741ba9184754327d9f1caea24bc5b8ba78b63e6`
precedes this handoff evidence update, not the final revision. After updating this
document, repeat scope/structure/diff; code/tests unchanged after fixed verification.

Tests cover positive fragmented UTF-8, exact/over caps, logical deadline, typed
clock, stale handles, duplicates/missing EOF/exit/stop, cancel boundaries, late
output, event flood, no raw logs in summaries and HPC1 integration. No fake PASS
is treated as authority. stopped acknowledgment after failure never restores output.

## Remaining work / honest evidence

All eight HB host groups NOT RUN. No Docker/WSL commands, pull/build/start, model,
PDF processing, DB/applier, historical generators or worker subprocess used here.
No 60s wall-clock watchdog, 10s validator enforcement, actual input delivery,
concurrent callers, cross-instance anti-replay or aggregate resource isolation.
The logical clock/opaque handle are trusted test inputs, not security mechanisms.
Returned bytes cannot be recalled after take; HPC3 currentness/acceptance remains open.

Next checkpoint: read-only review of pure prototype, then independently scoped
real supervisor/transport/watchdog proposal and execution authority. Do not connect
Docker merely because tests pass. No product runtime has begun.
