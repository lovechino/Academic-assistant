# HARNESS-COLLECTOR-02 repair handoff

2026-09-08. Pure collector repair; verified_local, independent review pending.

## Placement and scope

USER_REQUEST: quick correction after read-only review. RESPONSIBILITY/OWNER:
extend scripts/harness_collector.py development tooling, no new implementation.
CONTRACTS: COLLECTOR.md v0.2 and existing HPC2 boundary/profile. EXISTING_SEARCH:
rg MAX_EVENTS/start_requested/harness_collector across scripts and collector docs;
read existing owner and test callers. DECISION: extend source/tests, retain HPC1
parser unchanged. DEPENDENCIES unchanged: dataclasses/hashlib/re; tests under
scripts/tests. EXACT_OUTPUTS: source, tests, COLLECTOR.md, README, test map, handoff.
No product layers, new module, checker, plan/state or dependency changes.

Card [HARNESS-COLLECTOR-02](tasks/HARNESS-COLLECTOR-02.json) checked/begun before
outputs; run harness-collector-02-r1, baseline 255 Git-visible files, no rebaseline.
Preserved unrelated edits and prior handoffs as historical evidence.

## Review dispositions

1. P2 shared quota: repaired in pure slice. Removed timer/control competition and
   arbitrary fragmentation cap; nonempty accepted events are bounded by bytes.
   Empty chunks fail immediately. Control stop evidence survives exhausted data.
2. P1 real watchdog: remains explicitly pending; not claimed repaired. Caller
   ticks do not preempt blocked I/O. No real transport/watchdog launched here.
3. Start ambiguity: modeled with required start_requested -> starting -> start.
   Cancel/disconnect/deadline during starting retain stop_required/start_unconfirmed;
   trusted stop observation can reconcile without resurrecting the capture. Real
   exact-ID registry, in-flight API reconciliation and cleanup remain pending.

API changes are explicit in COLLECTOR.md: events -> data_events in snapshot,
EMPTY_CHUNK rejection, and start_requested required before start. No external
collector callers were found outside the existing tests in scoped rg search.

## Evidence and limitations

Focused command: py -3.11 -B -m unittest discover -s scripts/tests
-p test_agent_harness_collector.py -v: 30 methods passed (23 previous methods with
one replaced plus seven new). Cases include 4091-byte fragmentation, 5999 timer
ticks, byte overflow followed by stop, missing start response/cancel/disconnect/
deadline and stop before start acknowledgment. This is synthetic, not OS evidence.

Fixed command: `harness_journal.py capture --run harness-collector-02-r1 --event
collector-repair-verify-01 --phase verify --require-local-data` passed: 150 harness
methods, structure 910/910, 58 Python syntax files, 17 PDF hashes, zero failures/skips.
Scope check found exactly six declared outputs; git diff --check exit 0.
Capture finished `2026-09-08T04:35:10.651650+00:00`; observed tree SHA-256
`c359460f1117a9d6ed4a8ae1305211c154bbdbdf4418f610190a8a5cafa960f4`
precedes this evidence update, not the final revision. Scope/structure/diff repeated
after handoff update; no further code/test edits after fixed verification.
Self-review checked that old capture cannot return after failure, clock/byte caps
remain, tick ignores quota but not deadline, and stop_required false does not mean
container removed. Independent review pending; no approval or automatic closure.

No Docker/WSL/model/PDF processing, historical generators, image pull, worker
subprocess, DB/apply or product code. All HB host groups NOT RUN. Next: review
repair, then scope real supervisor/watchdog and its failure tests independently.
Keep manual Academic/option 2 and ASTRA explicit product GO pending.
