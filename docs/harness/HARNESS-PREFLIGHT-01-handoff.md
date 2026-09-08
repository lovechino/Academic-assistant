# HARNESS-PREFLIGHT-01 handoff

2026-09-08; draft_complete, verified_local (mechanical), needs_review.

User requested daemon provenance and image selection after preflight. Current
read-only observations and public metadata are in [preflight](HPC2-PREFLIGHT.md).
The active daemon is identified as Canonical Docker Snap 29.6.1/revision 3579;
Ubuntu CLI 29.1.3 is a separate package path. Direct daemon executable proof remains
partial. Python 3.11.16 slim-bookworm Linux/amd64 is a metadata-pinned candidate,
not an acquired or security-approved image. No image layers downloaded.

Ownership: reuse existing Docker profile, extend README navigation; new canonical
preflight evidence document, not another source module. Searched existing harness
paths for preflight/image documents before creation. Card
[HARNESS-PREFLIGHT-01](tasks/HARNESS-PREFLIGHT-01.json) created/check-task/begin before
output edits; read-only investigation preceded baseline. Run harness-preflight-01-r1
has 247 Git-visible paths; exactly three output docs, no rebaseline.

Checks: `harness_journal.py capture --run harness-preflight-01-r1 --event
preflight-verify-01 --phase verify --require-local-data` passed: 120 test methods,
891/891 structure checks, 56 Python syntax files, 17 PDF hashes, zero failures/skips.
Scope check found exactly three declared output docs; git diff --check exit 0.
Capture finished 2026-09-08T04:17:54.029526+00:00. Observed tree SHA-256
`fe44b2be965cc26660e41b5bd5e200b65c9f34eb8ce714cdcc62127490c9263c`
precedes this evidence update; not the final handoff revision hash. Final scope,
structure and diff checks repeated after this update; no code/tests changed.
No historical generator reruns, no container/model/PDF processing. No install,
pull/build/create/start, sudo, daemon config changes or workload inspection.
All eight HB groups NOT RUN. Local checks do not certify Docker isolation.

Residuals: actual image/config/provenance, cgroup limits, bounded collector,
independent observers, headroom and shared-host impact. Next scoped proposal:
fake-transport controller/collector development-tooling tests before real-container
smoke. Image pull and smoke require separately explicit scope. No source placement
or product logic added; option 2/manual Academic and WP-04/ASTRA explicit GO pending.
