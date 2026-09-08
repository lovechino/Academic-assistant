# HARNESS-PATCH-01 — patch-only design handoff

2026-09-07. User requested proceeding after the proposal to design patch-only and
permission boundaries first. The active scope is design/docs, not implementation
of launcher/parser/applier, OS permission changes, model runs or product GO.
Updated AGENTS supplied during the turn retains these repository boundaries.

## Scope / baseline

Card [HARNESS-PATCH-01](tasks/HARNESS-PATCH-01.json), maintenance HARNESS-01;
`check-task` succeeded and `begin --run harness-patch-01-r1` captured 232 Git-visible
paths before output edits. Five exact output files: design, test map, this handoff,
harness README and MODEL-NEUTRAL-TASK. Card prepared before baseline. All preexisting
WP04, journal and source-base edits must remain intact; no rebaseline/state/plan change.

## Deliverables

- [Design](PATCH-ONLY-DESIGN.md): controller-supplied inputs; separate worker, validator,
  sandboxed executor and acceptance permissions; 8 invariants; bounded UTF-8 changeset;
  immutable candidate/receipt/review bindings; cancel/replay/crash/recovery requirements.
- [Test map](PATCH-ONLY-TEST-MAP.md): 40 identified positive/adversarial specifications,
  expected outcomes and evidence/checkpoints. **All HP-T01..40 NOT RUN**; no fixtures,
  new unit tests, agent benchmark or host isolation trials were created/executed.
- Existing harness/model-neutral entry docs link to this proposal without replacing
  current CLI rules, adding task-schema fields or making planned commands callable.

Reuse/placement: read current core harness, layout checker and prior handoffs/journal
limits. Keep scope checking/journal as existing development diagnostics; a future
trusted release must live outside worker write authority and cover its whole dependency
bundle, not just reuse two CLI hashes as an enforcement claim. No second source tree,
runtime module, product ports or product state machine introduced.

Primary references read 2026-09-07: Git apply/update-ref, Microsoft Windows Sandbox
configuration and OWASP agent/tool defenses, linked next to the supported statements
in the design. Proposed format/limits/rollout are project design choices, not measured
performance or a source-provided guarantee. No external processor received repo/source data.

## Review / decisions

Self-review kept the following counterexamples explicit:

- A wrapper under the same full-privilege host account cannot prevent bypass.
- Packet delivery/hash is not proof of model comprehension; JSON/MD reviewer labels
  and old local journal PASS are not authority.
- Path checks include Windows aliases, baseline collisions and linked-file risks;
  raw diff, delete, binary and mode changes are excluded from the proposed first slice.
- Fixed commands may still execute untrusted tests; exit 0/self-reported counts do
  not prove assertions ran, and require protected observer design at HPC-2.
- Accepted pointer/current grant need serialized commit semantics; neither SQLite
  transactions nor a Git ref update make dirty multi-file checkout writes atomic.
- Cancellation after commit cannot pretend to undo accepted effects; recovery is a
  new authorized change, not reset/rebaseline or automatic deletion.

HPC-0 design review is pending. HPD-01..07 remain proposals/choices; HPD-08 retains the
existing product separation rule, with explicit product GO still absent. An actual
worker platform, protected review channel, checker release, limits and accepted store
must be chosen/tested at their checkpoints, not inferred from this packet.

## Actual verification

`py -3.11 -B scripts/harness_journal.py capture --run harness-patch-01-r1 --event patch-design-verify-01 --phase verify --require-local-data`
recorded `passed`, finished `2026-09-07T15:26:13.175940+00:00`: 84 existing harness
tests, 833/833 structure checks, 54 Python syntax checks, 17 PDF source hashes,
skipped/failures 0; both profiles exit 0. These are mechanical checks of the current
repo, not execution of HP-T01..40 or enforcement validation.

Read-only case-ID inventory found 40 rows, 40 unique HP-T IDs, no missing IDs from
01..40. That checks enumeration only, not scenario completeness or expected truth.
Scope check against the original baseline found exactly five allowlisted outputs;
no core harness/journal/source/checker/state/plan changes in this run. `git diff --check`
exit 0. Preexisting changes are preserved, not claimed as authored by this task.

Captured tree digest `4c43e1a094bee4243abaea9920cbcceec5b681251a73dfaa5eba8a8c8a95a3f0`
refers to the tree before this final handoff evidence update. No design/test-map/code
changed afterward. Final structure/scope checks keep the same original baseline.
Disposition: design `draft_complete / needs_review`; local mechanical verification
passed, but no human acceptance, enforceable boundary, model reliability or GO claim.

## Residual risks / NOT RUN

No hard enforcement, launcher, sandbox, OS ACL, broker, parser, candidate acceptance,
authenticated review, protected audit/backup or import-boundary linter implemented.
Host-admin compromise, sandbox escape, semantic defects/duplication, provider retention,
logs/evidence injection, malicious tests and cross-store recovery remain risks requiring
the specified defenses plus real evidence. Existing same-user mutable controls remain.

No installs, models, PDF processing, historical generators, Git promotion/ref writes,
push/commit, global config or product source edits. Corpus checks, if run below, are
checksum reads only. Pure fixture prototypes and all host/model/adversarial scenarios
are NOT RUN; integrity/test-tool PASS cannot be called model compliance or product readiness.

## Next bounded step

User reviews HPD-01 and HPC-1 scope. Then a separately authorized pure in-memory
changeset validator on synthetic text fixtures is the recommended implementation,
without filesystem apply, command execution, model calls or OS changes. Do not jump
from this design to an all-in-one privileged launcher/promoter. ASTRA-01 and explicit
scoped product GO remain independent, unchanged gates.
