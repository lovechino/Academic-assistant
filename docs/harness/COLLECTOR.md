# HPC-2 synthetic collector v0.2

2026-09-08. **Pure development-tooling prototype, not a Docker runner or sandbox.**
[Source](../../scripts/harness_collector.py),
[tests](../../scripts/tests/test_agent_harness_collector.py),
[repair handoff](HARNESS-COLLECTOR-02-handoff.md); [original history](HARNESS-COLLECTOR-01-handoff.md).

## Scope and usage

One collector owns one attempt. Test-only FakeTransport supplies an opaque handle,
logical integer clock and lifecycle observations. No sockets/subprocesses/threads,
timers, packet dispatch, database, model calls, image acquisition or file writes.
There is no real adapter/launcher or CLI accepting untrusted files/commands.

Run the bounded synthetic examples as named tests from the repository root:

```powershell
py -3.11 -B -m unittest discover -s scripts/tests -p test_agent_harness_collector.py -v
```

This does not begin a task, apply notes, run Docker or grant product GO. The existing
fixed harness profile discovers these tests without modifying its checker.

## Rules implemented in memory

| Stage | Rule / observed result |
|---|---|
| Admission | Exact immutable types, nonempty packet <=4 MiB and matching SHA-256; bounded caller pins and clock |
| Attach → start_requested → start | Record intent before dispatch; start without intent, early data or duplicate start invalidates attempt |
| Stream capture | stdout <=1 MiB, stderr <=256 KiB; check remaining capacity before append; overflow rejects whole capture |
| Diagnostics | stderr counted but NOT retained/rendered; summary contains fixed vocabulary/counts only |
| Data event bound | Nonempty chunks only; accepted data_events <= accepted bytes <=1.25 MiB; no separate fragmentation quota |
| Control/timer | tick/EOF/exit/stopped do not consume data quota; repeated invalid lifecycle events still fail; tick checks deadline |
| Start in flight | starting means acknowledgment missing; cancel/disconnect/timeout retains stop_required until trusted stopped observation |
| Completion | Both stream EOFs + exit 0 + trusted stopped observation + nonempty stdout; observation order can vary |
| Logical deadline | 60,000 ms from admission, inclusive boundary rejects; applies at every event and take |
| Failure | Cancel/disconnect/nonzero exit/protocol/clock/quota failures discard stdout, latch first reason |
| Stop acknowledgment | Failure may still need stop; trusted stopped observation clears stop_required but never restores capture |
| Capture | take returns frozen bytes/pins/hash once before deadline; complete is not validated or accepted |
| Late callbacks | Other handle rejected without changing this attempt; same-attempt protocol violation before take invalidates it; consumed object never reopens |

The byte caps constrain retained data, not allocation already performed by a caller.
stderr is deliberately discarded rather than offering an unsafe log viewer. Total
wire allowance is <=1.25 MiB through the two individual caps. A bytearray-to-bytes
copy during take transiently holds another <=1 MiB; packet/caller/test fixtures and
Python object overhead are outside this bound. No aggregate RAM/process cap exists.
The old shared 4096-event limit is removed: it incorrectly coupled timer polling
and stream fragmentation with completion controls. snapshot now exposes data_events
instead of events. Every accepted data event consumes >=1 byte; empty bytes fail
EMPTY_CHUNK. An adapter must map actual EOF to an EOF event and absence of data to
bounded waiting/tick, not empty stdout/stderr. At most 1,310,720 nonempty data events
can be accepted through the byte caps. Tick/control calls allocate no event history.
This is not CPU-rate enforcement: the trusted scheduler must still prevent busy
polling, unbounded reads, repeated terminal calls and event-loop starvation.

start_requested must succeed before an external start request is sent; then start
means confirmed start. A lost response leaves start_unconfirmed=true, including
after cancellation. Late start acknowledgment cannot reopen a failed capture.
stopped while starting records the observation but fails capture START_UNCONFIRMED.
The supervisor must retain exact container ID from create and reconcile pending
operations before asserting stopped; a point-in-time not-running observation while
start is still in flight is insufficient. stop_required=false is NOT proof of
container removal or cleanup of a created-but-never-started resource. No such
supervisor/registry or Docker side effect is implemented in this repair.

## Authority and non-goals

Attempt pins: job/generation/attempt, packet/context/release/profile hashes supplied
by trusted caller. Context pin is opaque, not proof of repo identity/read/write
grants. Constructor checks shape and packet digest, not current policy or signatures.
Handle identity routes events within one Python process only. Giving worker access
to this object or host shell defeats the trust assumption; it is not authentication.

Only worker stdout/stderr are data. Do not parse them into cancel/exit/stopped,
clock or other control events. Exit/stop in tests are fake observations, not proof
that a process tree or filesystem was actually cleaned. A pending stop must be
handled by a future supervisor; this module does not issue kill/cleanup commands.

Capture and validation stay separate. The integration test calls the existing
[HPC-1 validator](PATCH-VALIDATOR.md) with the caller's original matching context;
no parser/grant rules are copied into collector. Arbitrary `PASS` bytes can be
captured but fail changeset validation. Neither result authorizes apply/accept.

Serialized single-owner calls are required. No thread safety, atomic multi-process
fence, durable job registry, multi-job admission, crash recovery or cross-instance
replay protection. Creating another Collector does not consult previous attempts.
Cancel after take cannot recall returned bytes: currentness must be checked at
later validation/delivery/acceptance boundaries; HPC-3 is still pending.

Clock is caller-supplied and only checked on calls. A stalled process with no calls
will not time out itself. No real wall-clock watchdog, 10s validator limit, Docker
frame decoder, collector backpressure, image verifier, OS isolation or observer is
implemented. Never label these tests as host security PASS or model compliance.

## Coverage and next checkpoint

30 exposed synthetic test methods, including 24 completion-order permutations and
cancellation before/after each modeled boundary. This is deterministic regression,
not a concurrency stress test, held-out eval or exhaustive correctness proof.
All HB-01..08 remain NOT RUN; [test map](PATCH-ONLY-TEST-MAP.md) keeps inventories separate.

Next: review this pure prototype for missing transitions/bounds, then scope a real
supervisor/watchdog/transport adapter and protected ownership. Do not connect Docker
from a generic continuation without resolving [profile](HPC2-DOCKER-PROFILE.md)
and [preflight](HPC2-PREFLIGHT.md) prerequisites and explicit execution scope.

Review disposition: quota coupling repaired and tested; start-in-flight modeled,
but real reconciliation still pending. Independent watchdog/30s command deadline/
5s teardown budget and 10s validator enforcement remain integration blockers, not
resolved by these logical-clock tests.
