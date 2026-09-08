# SOURCE-BASE-01 — canonical scaffold and placement handoff

2026-09-07. User requested a base source template to prevent coding agents duplicating
functions in arbitrary folders. This change standardizes the existing scaffold and
development checks only; no product source, package, fake runtime, install, external
processor, model call or historical artifact generator. Product GO is still absent.

## Scope and baseline

Card [SOURCE-BASE-01](tasks/SOURCE-BASE-01.json), maintenance HARNESS-01; run
`source-base-01-r1`, original baseline 226 Git-visible paths, created before output
edits. Eleven exact output paths. Existing WP04/contracts/journal edits were present
at baseline and must remain intact. Card created before baseline; it records the
user request, not independent authorization. State, plan, core harness and journal
implementation are not in scope and were not intentionally edited.

## Deliverables and placement decisions

- [Placement blueprint](../architecture/11-source-placement-blueprint-v0.1.md): one
  responsibility owner, canonical reserved source addresses, imports and test placement.
  Clarifies application/retrieval/agents, application/workers and feature/components.
- [Source task template](SOURCE-TASK-TEMPLATE.md): record actual existing-code search,
  reuse/extend/new, exact paths, contracts, tests and gates. No new task JSON keys.
- Root AGENTS/README, source-layout history and harness README point to the blueprint.
  Physical component scaffold and its README bytes are unchanged; the map clarifies
  older broad wording without creating another source tree.
- [Layout checker](../../scripts/verify_source_layout.py): Git-visible pre-product
  filenames/markers only, integrated into the existing structure verifier; common
  marker inventory is defined once. New roots/runtime/component files fail, as do
  missing markers and unsupported linked paths. No allow-runtime/product GO switch.
- [Focused tests](../../scripts/tests/test_agent_harness_source_layout.py) join the
  existing fixed harness test glob. Disposable synthetic Git repos only.

Reuse search actually performed: `rg --files` for applicable AGENTS and source files;
read component/root/layer READMEs, existing source-layout/ARCH-02 and verifier/harness
code. `git ls-files --cached --others --exclude-standard ai-core backend frontend infra tests`
confirmed that outside experiments there are README markers and one design-only eval
profile, not existing runtime implementations to move/copy. The old structure verifier
already owns syntax/links/PDF hash checks; reuse it and add a narrow path check instead
of a second competing verification flow. No semantic search of nonexistent runtime
symbols is claimed; future workers must search again as code appears.

## Actual verification

Initial focused placement suite: 14 tests passed in 0.749s before timeout and simulated
link/reparse cases were added. Standalone layout check on the workspace passed with
230 observed Git-visible paths and 28 markers at that point. Final focused suite:
16 tests passed in 1.724s, including simulated link/reparse rejection and timeout.

`py -3.11 -B scripts/harness_journal.py capture --run source-base-01-r1 --event source-base-verify-01 --phase verify --require-local-data`
recorded `passed`, finished `2026-09-07T13:00:50.731697+00:00`: **84 harness tests**
(68 existing core/journal + 16 placement), **820/820 structure checks**, 54 Python
syntax checks, 17 PDF source hashes verified, failures/skips 0, both profile exit codes
0. Standalone structure output also reported layout pass, 231 Git-visible files and
28 required markers. These are local tooling/integrity results, not product tests.

Scope check used the original baseline and found exactly the eleven allowlisted
output paths; no state/plan/HEAD rebaseline or core harness/journal change. Existing
component source and historical experiment changes = none against that baseline.
`git diff --check` exit 0. The capture's tree hash
`433788efa9a166abff67b1dda357ad4dafddf380096e4c2f03db053272a4b76e`
refers to the tree before this final handoff text update; no code changed afterward.
Final structure/scope checks retain the original run, not a replacement baseline.

Self-review confirmed the blueprint explicitly narrows older broad layer wording,
separates backend admission from AI QA reasoning, keeps evaluation labels out of
runtime, and does not claim actual imports or product behavior were tested. Status:
`verified_local` for development tooling; placement/content acceptance needs review.

## Limits / pending

Source-base is documentation + read-only development tooling, not executable boilerplate.
Reserved filenames are future addresses, not assertions that implementations exist.
No product runtime source changed; backend authority, manual Academic and ARCH-02 remain.
This is not a semantic duplication detector, import linter, sandbox or authenticated
review. Ignored files, external writes, same-user tampering and runtime hidden under
allowed docs/scripts/experiments remain outside these mechanical checks.

Structure now requires a Git checkout for inventory, including source-only checkouts;
an archive without Git metadata fails rather than silently skipping placement coverage.
Actual Windows junction/symlink races, multi-model behavior and product tests are NOT RUN;
link/reparse handling tests use simulated metadata, not a security proof. Human review
of placement conventions is pending. No academic labels/rights/gates were promoted.

## Next

User can review the map and hand the bounded placement template to another agent.
Before product source is introduced, require explicit scoped GO after ASTRA review,
then a separately scoped product harness/import-boundary profile. Do not relax this
checker to make a runtime card pass. This task does not advance WP/phase or authorize
automatic implementation from a reserved source path.
