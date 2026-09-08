# HARNESS-JOURNAL-01: local SQLite tooling handoff

Follow-up: [HARNESS-FINDING-01](HARNESS-FINDING-01-handoff.md) implements the user-approved direction as explicit finding lifecycle tooling. Results/counts/hashes below remain the historical v0.1 observation, not verification of the later code. Existing real findings are not auto-promoted/closed.

2026-09-07. User states they have read the WP04 review and asks to update the harness, considering CLI/local DB scope tracking and gradual improvement. Implemented as development tooling only; not explicit scoped product-runtime GO or verified independent Astra identity. State/master plan unchanged; ARCH-02 remains controlled multi-step/one reasoning role/manual Academic. No product source, dependency install, paid model, external processor, historical generator, actual material deletion or deployment.

## Scope / baseline

Card [HARNESS-JOURNAL-01](tasks/HARNESS-JOURNAL-01.json), maintenance HARNESS-01, exact eight files. `harness-journal-01-r1` began after checked card, 218 Git-visible paths, HEAD `d7e89e4`, before output edits. Preexisting 17 WP04 repair paths preserved as baseline; no rebaseline or state/approval mutation. Plan SHA stays `062e9216632341880e66104b9a2955ddc5c965f86b7c75b1bf7bd37950e67b04`.

## Changes

- [Journal CLI](../../scripts/harness_journal.py): fixed local SQLite path, version/root validation, run scope snapshots, explicit check/verify observations, evidence-linked reported findings, read-only reports and bounded template suggestions.
- [Focused tests](../../scripts/tests/test_agent_harness_journal.py): synthetic local persistence, duplicate/concurrent calls, interrupted/failed commits, stale baselines, safe projections and read-only/error boundaries. No product behavior tests.
- Existing checker: fixed test discovery includes journal tests; research cards cannot edit the new journal script. Existing gate/rules retained, no profile granting runtime work.
- Harness README, [CLI guide](LOCAL-JOURNAL.md), scripts README and this handoff. SQLite journal is an explicit ignored local side effect, outside Git-visible scope monitoring; not a product data store or replacement for baseline.

## Evidence

Initial focused run before final review additions: 24/24 journal unittest methods passed in 11.579 seconds. Final journal suite has 27 methods plus 31 existing core methods.

Actual `py -3.11 -B scripts/harness_journal.py capture --run harness-journal-01-r1 --event journal-final-verify-01 --phase verify --require-local-data` called the unchanged fixed verification workflow and completed at `2026-09-07T09:28:53.667163+00:00`: outcome passed, 58 tests, both profile exit codes 0; 787/787 structure checks, 52 Python syntax checks, 17 PDF hashes, skips/failures 0. Exactly eight output paths differed from the original maintenance baseline. Source hashes checked, not PDF processing; these are local tooling checks, not product/model acceptance.

Checker fingerprints at that observation: `agent_harness.py` = `466421b7bddc5d8c3baa8220dae96bc18605f8fba8d353003f3db87dbecdbe6c`; `harness_journal.py` = `394f3aa29b0540b29d73ed9ab0bc8417dfa0417d8daf2cf5a9125ee3da762403`. The captured inventory fingerprint refers to the pre-final-handoff revision; recording results changes this Markdown, not code. Final scope/structure checks remain on the original run baseline; no rebaseline.

Explicit local side effect: initialized `tmp/agent-harness/journal.sqlite3` using CLI; no existing database overwritten. It is Git-ignored and not protected by the Git-visible scope detector. Demo event `journal-demo-stale-head-01` performed only `check` on historical run `wp04-repair-recovery-01-r1` and returned exit 1 / blocked / `head_drift`; no historical generator or tests rerun on that old run, no baseline repair. This is a current observation of stale run metadata, not a new product defect.

Demo finding `journal-gap-concurrency-01` references LOCAL-JOURNAL line 70 with evidence SHA `1607df052045adee07df442ea78ae6839b2e44fd502296807efdf27d8c627371`; reported test_gap/P2, not confirmed runtime bug. Threaded duplicates are tested; process/distributed coverage and broader adoption remain outside demonstrated scope. `suggest --run harness-journal-01-r1` returned one proposal requiring review from two sampled events, `mutations_performed=false`. No task/card/auto-fix generated. `git diff --check` exit 0.

## Self-review and limits

Database uniqueness/transactions prevent an accidental duplicate event from rerunning its fixed check. Crash leaves pending; no auto-resume/retry or artificial PASS. DB finish failure is nonzero. Terminal records cannot be overwritten through CLI, but same-user SQL/filesystem tampering remains possible. Snapshots/evidence digests are not signed authority. Suggestions are fixed strings and never interpret evidence/DB text as instructions.

The system does not always discover bugs. A finding is a reporter assertion; a check fail can be operational, stale state or missing outputs. Currentness is not inferred from past PASS. No finding auto-resolution, self-modification, approval switch, product instrumentation, backup/pruning or continuous monitoring. Secret minimization does not make filesystem metadata public-safe. Concurrency coverage and actual verification are recorded separately, not sold as distributed exactly-once.

## Next handoff

Use [LOCAL-JOURNAL](LOCAL-JOURNAL.md) for explicit init/capture/report on an already authorized task. Continue evidence → proposed bounded regression → authorized repair → verification/review; do not auto-create work from suggestions. Product harness enablement still needs exact review/GO record and a separate scoped change; this maintenance does not provide it. Product recovery retention/role decisions remain in WP04 docs, not configured in this CLI.
