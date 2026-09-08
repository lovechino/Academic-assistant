# HARNESS-FINDING-01: explicit finding lifecycle handoff

2026-09-07. User explicitly requested implementation after accepting the evidence → proposed regression → authorized repair → verification/review direction. Scope is local development tooling, not academic product runtime or GO. No installs, models, external processor, source PDF processing, product code or historical artifact generators.

## Scope and baseline

Card [HARNESS-FINDING-01](tasks/HARNESS-FINDING-01.json), maintenance HARNESS-01; run `harness-finding-01-r1`, baseline 223 Git-visible paths at HEAD `d7e89e4`, before seven output edits. Existing WP04/journal changes preserved. No state/plan/checker/baseline rewrite or product-profile relaxation. Master plan SHA remains `062e9216632341880e66104b9a2955ddc5c965f86b7c75b1bf7bd37950e67b04`.

## Implemented

- [Journal CLI](../../scripts/harness_journal.py): `transition` and read-only `history`; original findings stay reported while append-only transition events derive reproduced/fix_proposed/verified_local/reviewed_closed.
- Atomic expected-predecessor + append and strict legal sequence, idempotent retries, no rewriting terminal events. SQLite schema v1 unchanged; no migration/reset.
- Verification binding: same proposed repair run, complete latest passed verify after proposal, current baseline/checker/Git-visible tree; old PASS cannot hide newer failure/pending.
- Closure requires explicit review doc/path/line/hash and a reviewer label distinct from repair/verification actors. Labels are self-declared metadata, NOT authenticated identity/independent acceptance. No automatic closure when tests pass.
- Report derived states + deduplicated state-aware suggestions; [guide](FINDING-LIFECYCLE.md) explains workflow, evidence and limits. Prior handoff and README link forward without rewriting historical evidence.

## Actual verification

Initial focused suite: 36 journal unittest methods passed in 21.780 seconds before the final newer-verify guard/test was added.

Final `py -3.11 -B scripts/harness_journal.py capture --run harness-finding-01-r1 --event finding-final-verify-01 --phase verify --require-local-data` recorded passed at `2026-09-07T09:46:05.785305+00:00`: 68 tests (31 core + 37 journal), both fixed profile exit codes 0, 798/798 structure checks, 52 Python syntax checks, 17 PDF hashes, skipped/failures 0. Exactly seven output paths changed against the original baseline. All counts are local tooling checks, not academic/product acceptance.

At verification, journal script SHA-256 = `fe3956ebe5caf4b74d4cb24990dda7d2e3a3fbde9e58608efc8adae92e9c5b77`; core checker remains `466421b7bddc5d8c3baa8220dae96bc18605f8fba8d353003f3db87dbecdbe6c`. The recorded inventory hash refers to files before final handoff text; no code changed after verification. Final structure/scope checks use this same baseline, not a new run.

Actual read-only demo: `history --finding journal-gap-concurrency-01` returned the existing finding in state reported, with its original origin run, evidence hash and event intact. No real finding transitions/closures were written; all forward/closed transition demos were synthetic tests. Existing DB schema remains 1 without migration, reset or overwrite. The only workspace journal write this turn is the verification event above. `git diff --check` exit 0.

## Self-review / remaining limits

Complete lifecycle is exercised only with synthetic test evidence/reviewer labels. Existing reported concurrency-coverage finding is not falsely closed. No true reviewer identity, semantic truth detector, automatic fix/approval/reopen/dismissal, backup or migration is introduced. Current task does not itself authorize resolution of another finding.

The CLI enforces mechanical evidence bindings, not whether a named test reproduces the bug or a Markdown file contains a truthful review. Counterexamples for same-user forged labels/SQL/baseline remain outside a voluntary local tool's guarantees. History uses one DB read snapshot; aggregate report/suggestions are bounded samples, not an atomic all-bug dashboard. Scope/tree checks cannot lock out hostile filesystem writes after observation. Scan cap is explicit and fails closed; scale/indexed migration needs separate review.

All closure records remain revision-scoped historical local evidence; no product readiness or ASTRA acceptance follows. Process-kill/power-loss/multi-host tests and independent review of this tooling are NOT RUN. ARCH-02 and all academic-source safety rules remain unchanged.

## Next

Use the lifecycle on an actual authorized repair with reproduction and reviewer evidence. Read [FINDING-LIFECYCLE](FINDING-LIFECYCLE.md), recover the finding head, and propose a bounded regression before changes. Do not manufacture closure evidence or create new work automatically from suggestions. Product implementation still requires explicit scoped GO and a separate harness change bound to that authority.
