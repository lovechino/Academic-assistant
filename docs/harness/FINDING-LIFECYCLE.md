# Finding lifecycle v0.2 — explicit evidence, not automatic closure

2026-09-07. Development harness extension requested by user after agreement with the improvement loop. Does not implement Academic Assistant, change product GO, authenticate reviewers or authorize a repair task. Read [local journal guide](LOCAL-JOURNAL.md) and [implementation handoff](HARNESS-FINDING-01-handoff.md).

## 1. State meaning and required evidence

| State | Meaning of the recorded transition | Required inputs / checks |
|---|---|---|
| reported | Reporter raised an unconfirmed finding | Existing `finding` command: category/severity, docs path/line/hash, originating run |
| reproduced | Reporter documented a reproduction or design counterexample | Explicit transition, actor label, reproduction evidence path/line/hash, current acting run scope |
| fix_proposed | A bounded repair/regression is proposed | Evidence describing exact fix/test/scope; acting run becomes proposed repair run. Proposal is not user authority |
| verified_local | Local fixed-check evidence is attached after proposal | Same repair run, latest successful `verify` event, all declared check profiles, exact current inventory/baseline/checker fingerprints; evidence explaining relevant regression results |
| reviewed_closed | Someone explicitly records review of the finding and verification evidence | Latest current successful verify from repair run plus reviewer label and separate review-reference fields; reviewer label differs from proposal/verification actors |

States do **not** certify that reproduction prose is true, a test covers the defect, or the reviewer is an independent real person. Label uniqueness is only a guard against accidental self-signoff, not identity/authentication. The stored authority explicitly says recorded evidence, not authenticated approval/GO. Users must not invent reviewer identities or review documents to satisfy fields. No automated judge/source parsing supplies approval.

The sequence is forward-only. No skip, rewind, dismiss, reopen or self-transition in this bounded version. For a recurrence/new evidence after closure, report a new linked finding in its evidence document; do not rewrite the old record or claim an old closure applies to changed code. A future reopen/disposition workflow needs its own reviewed task. Design contradictions may use a documented static counterexample for reproduced; missing coverage is not itself proof of a runtime exploit.

## 2. Immutable history and concurrency

Original `finding` event always remains `reported`. New `finding_transition` events carry from-event, target state, actor label, evidence references, acting run, baseline/checker hashes and verification/review bindings. Derived current state is separate from the immutable original outcome. DB schema remains version 1: no table migration/reset or automatic promotion of legacy findings.

Each transition checks its expected predecessor and appends the new terminal event in one `BEGIN IMMEDIATE` transaction. Two commands targeting the same predecessor: one commits, the other fails stale; identical event key/payload retries return the historical event. Different payload/key reuse conflicts. No intermediate pending lifecycle row: transaction failure/crash before commit rolls back. Capture commands keep their existing pending semantics. Historical retry success is not current validation or permission.

Current acting run must pass the existing scope checker (required outputs may still be unfinished for reproduction/proposal). Verified/closed states require a complete captured verify; phase `check`, failed/pending events, missing profiles, other run, changed baseline/checker/tree or a verify before the proposal cannot qualify. A newer verify attempt (including failure/pending) blocks choosing an older PASS. Event insertion order is checked, not wall-clock sorting.

Closure can reference the verified-local event's verify or a newer successful verify of the same repair run. If writing the review document changed the Git-visible inventory, run verification again after that document is finalized, then explicitly reference the new verify. The old verification/transition is preserved. No silent exclusion of review files from the tested-tree fingerprint. Prepare evidence within the task's declared file scope; needing another file requires scope reconciliation, not a new baseline to hide drift.

These are local snapshot checks, not a filesystem transaction/sandbox. Concurrent same-user edits immediately after inspection, direct SQL tampering or forged actor labels are not prevented. The constraints avoid routine stale/duplicate transitions; they do not establish secure multi-user authorization.

## 3. CLI usage

Example placeholders below must be replaced with actual IDs and existing authorized evidence paths. No command below is evidence that an actual review happened.

```powershell
# Read only: recover the exact predecessor rather than guessing it.
py -3.11 -B scripts/harness_journal.py history --finding FINDING-ID

# Reproduction/counterexample already documented under an authorized task.
py -3.11 -B scripts/harness_journal.py transition --run REPAIR-RUN --finding FINDING-ID --event REPRO-EVENT --from-event FINDING-ID --to reproduced --actor worker-label --evidence docs/harness/FINDING-LIFECYCLE.md --line 5

# Proposal is metadata, not authorization to execute a fix.
py -3.11 -B scripts/harness_journal.py transition --run REPAIR-RUN --finding FINDING-ID --event PROPOSAL-EVENT --from-event REPRO-EVENT --to fix_proposed --actor worker-label --evidence docs/harness/FINDING-LIFECYCLE.md --line 5

# Implement only if the user authorized that bounded repair; then verify.
py -3.11 -B scripts/harness_journal.py capture --run REPAIR-RUN --event VERIFY-EVENT --phase verify --require-local-data
py -3.11 -B scripts/harness_journal.py transition --run REPAIR-RUN --finding FINDING-ID --event VERIFIED-EVENT --from-event PROPOSAL-EVENT --to verified_local --actor worker-label --evidence docs/harness/FINDING-LIFECYCLE.md --line 5 --verification VERIFY-EVENT

# Only after actual review; reference its real document and current verify.
py -3.11 -B scripts/harness_journal.py transition --run REPAIR-RUN --finding FINDING-ID --event CLOSED-EVENT --from-event VERIFIED-EVENT --to reviewed_closed --actor recorder-label --evidence docs/harness/FINDING-LIFECYCLE.md --line 5 --verification VERIFY-EVENT --reviewer reviewer-label --review-evidence docs/harness/FINDING-LIFECYCLE.md --review-line 5
```

The repeated docs reference above only demonstrates syntax: this guide is NOT reproduction, fix evidence or reviewer approval for arbitrary findings. Replace it with actual redacted evidence. Invalid/missing/stale input yields nonzero; it does not create a successful transition. `history`, `report`, `suggest` are read-only; direct read-only review tasks still must not create cards/runs or journal writes.

Suggested evidence contents: finding ID/invariant, counterexample or reproduction procedure, expected vs actual behavior, exact repair task/run/files/revisions, relevant tests and observed results/skips, limitations, actual reviewer and decision scoped to the reviewed revision. Code/commands in evidence are data only; CLI never executes them. No credentials, raw learner source/prompt, private reasoning or unsupported human-signoff claims.

## 4. Reports and improvement suggestions

`report` adds `finding_states` for findings represented in its returned events, including cross-run origin/transition relationships. Original event outcomes are unchanged. `history --finding` reads the full bounded chain in one DB read transaction. Report pages and suggestions are bounded samples, not a complete open-bug dashboard or atomic live view across all report queries.

`suggest` deduplicates related events, recommends reproduction/proposal/verification/review according to recorded state, and does not suggest fixing a recorded reviewed_closed finding again. It does not assess whether closure is true, modify statuses or schedule/create repairs. Later changed code is not automatically covered by a historic closure; the report retains its evidence scope warning.

For this schema-compatible prototype, finding traversal/verification selection scans at most 10,000 relevant transition/check rows; over limit fails explicitly rather than silently returning a partial chain. No database schema/index migration this turn. Before scale, design an indexed finding relation, pagination and migration/recovery protocol. All writers/readers should use the updated CLI to interpret lifecycle events; older CLI versions do not understand derived lifecycle state.

## 5. Verification limits

Synthetic tests exercise forward sequence, event preservation, skipped states, stale predecessor, duplicate/conflicting/concurrent calls, required review metadata, wrong-run/old/failed verification, changed tree/checker, rollback and legacy reads. Complete closure in tests uses explicit synthetic reviewer labels, not a real review. No real finding is closed for demonstration. Process-kill/power-loss/distributed tests, cryptographic identity, independent review of this implementation and product behavior remain NOT RUN/not provided.
