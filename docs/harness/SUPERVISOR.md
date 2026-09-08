# HPC-2 synthetic supervisor v0.1

2026-09-08. **Real bounded container trial, not a general coding-agent launcher.**
[Source](../../scripts/harness_supervisor.py),
[tests](../../scripts/tests/test_agent_harness_supervisor.py),
[handoff](HARNESS-SUPERVISOR-01-handoff.md). Development tooling, not product runtime.

## Scope and operator use

User authorized packages 1–5, subject to preceding safety gates. Package 6 stops
before real model/data/budget selection. This card implements the supervisor slice,
not all five packages. No accept/apply API exists. Only a trusted host operator may
invoke it after fresh Docker/headroom preflight. Never give this CLI, host shell or
socket to an untrusted coding agent. The current desktop agent is NOT contained.

Each invocation creates a new synthetic container:

```powershell
wsl.exe -d Ubuntu --cd /mnt/e/Academic-assistant --exec python3 -I -B scripts/harness_supervisor.py happy
```

Named fixtures: happy, fake-pass, overflow, hang, cancel, observe. No arbitrary
commands, paths, packets, grants, models or image arguments. Test discovery never
contacts Docker. CLI success is validated_synthetic_only, NEVER accepted/applied.
Negative fixtures intentionally return nonzero; blocked observer is not a pass.

## Implemented controls

- Parent/transport child are outside worker; worker has no host mounts, repo,
  socket, credentials, approval channel or network other than private loopback.
- Fixed command and notes-only packet; original context remains outside. Worker
  output cannot select host destinations, jobs, grants or control events.
- Isolated Python bootstrap loads two exact modules without repo sys.path. Three
  source-module hashes record identity, not a signed immutable installed release
  or full interpreter/OS attestation. Host account/release remain trusted.
- Reuses collector and validator. Capture consumed once; original context validates
  exact bytes. PASS text fails JSON validation, not interpreted as test evidence.
- Attach upgrade before start. Non-TTY frame length checked against remaining
  stream capacity before allocation; payload reads <=8 KiB, stdout <=1 MiB,
  stderr <=256 KiB discarded. Header <=8 KiB; API body <=1 MiB. No logs fallback,
  docker cp, tar extraction, host execution of payloads or active rendering.
- Image/config/diff_ids and effective settings checked before start: UID/GID 65532,
  cap-drop ALL, no-new-privileges, builtin seccomp, private namespaces, read-only
  root, memory/swap 512 MiB, CPU .5, pids 32, /work tmpfs 32 MiB/1024 inodes,
  shm 8 MiB, log-driver none, restart=no. Config equality is not a stress test.

The [Engine API reference](https://docs.docker.com/reference/api/engine/version/v1.46/)
describes attach upgrade/multiplexing. [Resource documentation](https://docs.docker.com/engine/containers/resource_constraints/)
describes equal memory/memory-swap limits; actual enforcement and daemon overhead
still need local observation. No kernel escape, fork/disk flood or network enabling.

## Watchdog, receipt and cleanup

Child waits for parent ACK after fsynced create intent, created exact ID and start
intent. No start before ID registration. Parent independently watches child I/O/
validation: 45s work, <=10s validation, <=30s command; ordinary API calls have 3s
total signal deadline, not just inactivity timeout. Attach inactivity timeout 3s
can fail quiet workloads earlier. Hang/cancel fixtures use 1s/.5s after start.
Each trusted process: 256 MiB address-space, 10 CPU-seconds, 64 FDs, 64 KiB file
size. Worker has separate caps; these do not cap Docker/OS aggregate overhead.

On failure, kill/join child, force-remove ONLY registered exact ID, require GET 404.
Never delete by name/label/glob, volumes or existing-container enumeration. Lost
create response blocks as unknown ownership; no guessed ID or automatic retry.
Removal/API ambiguity stays blocked. Observed elapsed >=60s rejects; timers cannot
guarantee preemption of uninterruptible kernel/daemon failures.

Private Linux /tmp/academic-hpc2-<operator-uid>: 0700, lock/receipts 0600, flock,
atomic replace+fsync, <=32 receipts of <=64 KiB. Pending/unresolved receipts block
admission. No auto-delete/rebaseline. Same host UID/admin can modify these; /tmp
is not reboot-durable backup. Not signed evidence, grant authority or acceptance DB.

**Known gap:** SIGKILL of supervisor parent/host failure may leave an orphan;
next launch blocks but no autonomous reaper exists. Independently supervised reaper,
restart/fence and lost create/start tests are required before hostile/general workers.
Killing CLI or one not-running snapshot is never cleanup proof.

## Observer blocker and continuation

The actual observe trial read UID/GID, CapEff, NoNewPrivs and Seccomp of its newly
created PID. Reading /proc/<pid>/ns/net returned PermissionError. Result is
HOST_OBSERVER_NOT_READY even when proposal validates; cleanup still runs. This is
missing observer privilege, NOT proof worker access was denied. PID lifetime/reuse
and tamper-resistant observation also need a reviewed acquisition mechanism.

| Authorized package | Disposition / requirement before closure |
|---|---|
| 1. Permission boundary | Fixed worker narrowed; general worker-only entry point/protected installed release still open. |
| 2. Supervisor | Implemented synthetic slice; parent-death/reaper, durable fence and host lost-create/start probes open. |
| 3. Image/smoke | Acquired/verified, bounded scenarios run; full effective quotas, signatures/SBOM/CVE review open. |
| 4. Eight HB groups | Partial mechanisms; independent read/egress controls blocked. No whole HB group accepted. |
| 5. Acceptance/rollback | NOT IMPLEMENTED/RUN; preceding evidence and protected reviewer/store boundary required. |
| 6. Real model | NOT RUN; model/data/budget not chosen. |

User/operator must choose narrowly privileged independent observation or a dedicated
isolated test environment before widened probes. No sudo, Docker root-equivalent
workaround, privileged container or daemon changes from this observer denial.
Ordinary in-scope tooling authorization remains; additional host privilege does not.

Package 5 restore must use immutable old/new snapshots and a reviewed current-base-
guarded new change; serialize cancel/revoke/accept and unique operation fingerprints;
atomic accepted pointer or durable intent plus crash reconciliation. No reset-hard,
history deletion or checkout overwrite. Local SQLite diagnostic rows cannot approve
a restore. Option 2/manual Academic and ASTRA explicit product GO remain unchanged.
