# HPC-2 Docker preflight — 2026-09-08

Status: metadata investigation complete; **execution blocked pending prerequisites**.
Specializes [Docker profile](HPC2-DOCKER-PROFILE.md), not an executable launcher or GO.

## 1. Daemon: version difference explained

Current read-only observations at approximately `2026-09-08T04:15:15Z`:

| Observation | Interpretation |
|---|---|
| `snap list docker`: 29.6.1, revision 3579, latest/stable, publisher canonical | Installed Snap metadata; not independent binary attestation |
| `snap services docker`: docker.dockerd enabled/active | This is the active management service; ordinary docker.service is not its name |
| `systemctl show snap.docker.dockerd.service`: MainPID 208, active/running | Matches the observed dockerd PID in this session only |
| `/proc/208/cgroup`: snap.docker.dockerd.service; `/snap/docker/current` resolves to revision 3579 | Corroborates Snap ownership; PID is not a reusable stable identity |
| Ordinary docker.service inactive; `/usr/bin/docker` is Ubuntu package version 29.1.3 in prior preflight | Two packaging paths explain CLI/server mismatch; do not start a second daemon |
| Reading `/proc/208/exe` with current user gives no executable path | Direct binary hash/loaded executable proof remains unavailable; no sudo/root workaround attempted |

[Snap Store](https://snapcraft.io/docker) lists Canonical as verified publisher and
29.6.1 stable; it states this Snap is built by Canonical, not published by Docker Inc.
This supports the packaging explanation, not a complete supply-chain/security audit.
The historical `+dirty` build suffix alone is not evidence of compromise.

Previous read-only preflight in this conversation: Ubuntu initially stopped, first
API calls failed because socket was absent; later socket/daemon appeared and API
reported two running containers. Error-path zero fields were not valid counts.
WSL startup can activate configured services; no explicit service/container start
was issued. Cgroup v1 and missing blkio throttling warnings remain unresolved.
No workload env/log/content was inspected. Do not inventory other-project image
layers or reuse those application images as harness fixtures.

## 2. Selected candidate, not admitted image

Provisional synthetic-only choice: Docker Official Image
`docker.io/library/python:3.11.16-slim-bookworm`, platform `linux/amd64`.
Reasoning: existing harness uses Python 3.11+, standard-library JSON/hash/stream
fixtures need no pip install; this avoids introducing a second fixture language.
Not a product dependency choice, smallest-image claim or security endorsement.
[Official image page](https://hub.docker.com/_/python) provides the tag and source links.

Public [Hub tag metadata](https://hub.docker.com/v2/repositories/library/python/tags/3.11.16-slim-bookworm)
retrieved over HTTPS with 20s request timeout, no image layers downloaded:

| Pin | Observed value |
|---|---|
| Tag/index digest | `sha256:528257d48c1da0dcecc2e725d1ae34498d60c965f1241e39cd6a85a8859bdf84` |
| Linux/amd64 child digest | `sha256:b1add8a6f2aca6bcfcf0b9c9b522352f7ce0d62a3d556a2f2f32511aa0cca250` |
| Platform size reported by API | 47,790,378 bytes; not installed disk usage or peak pull space |
| Platform status | active; does not mean security approved |

Candidate immutable reference for a future separately authorized acquisition:
`docker.io/library/python@sha256:b1add8a6f2aca6bcfcf0b9c9b522352f7ce0d62a3d556a2f2f32511aa0cca250`.
Index and child digest are different objects; neither is the local image config ID.
These are **registry-reported pins**, not locally recomputed hashes/signatures.
Before admission, verify manifest bytes/digest and platform, config/layer chain,
local image identity and provenance; tag drift requires review, not silent refresh.

The linked [Dockerfile at commit 688a0b8](https://github.com/docker-library/python/blob/688a0b86bb44289df16a363e9f41d90514c1a5f9/3.11/slim-bookworm/Dockerfile)
uses Debian bookworm-slim and Python 3.11.16, ends in CMD python3, and has no explicit
USER/VOLUME/HEALTHCHECK/ENTRYPOINT declaration in that file. This does not establish
effective inherited image configuration or prove that the reported digest was built
from that commit. It includes package tooling; no runtime package installation is
allowed. Effective config/layers, signatures/attestations, SBOM/license inventory
and vulnerability review remain NOT VERIFIED. Do not execute Dockerfile snippets.

Prior filtered local inventory returned no matches for python/alpine/busybox/ubuntu/
hello-world; this is historical and limited to those reference filters, not proof
there is no usable untagged or differently named image. No pull was performed.

## 3. Readiness and next bounded work

| Gate | Disposition |
|---|---|
| Daemon manager identification | Resolved to Snap with service/PID/cgroup evidence; binary provenance partial |
| Image family/platform choice | Proposed as above; content acquisition/verification pending |
| Effective identity/mount/network/cgroup controls | NOT RUN; source or CLI metadata cannot establish enforcement |
| Trusted launcher and bounded live collector | Not implemented; must exist before untrusted worker execution |
| Deadline/cleanup/observer calibration | Not implemented or measured; positive controls must precede hostile probes |
| Shared-host headroom/impact approval | Pending; do not change Snap refresh policy, daemon config or old workloads |

Separate stages avoid a circular gate: first implement/test controller with fake
transport and bounded synthetic streams (no Docker execution); then acquire/inspect
the reviewed image under explicit scope; then authorize harmless real-container
controls; only after those controls work consider bounded adversarial probes.
Image acquisition alone does not authorize container start. Do not silently loosen
profile caps to pass, run privileged, refresh Snap, restart WSL or prune containers.

HB-01..08: executed=0, NOT RUN=8, pass rate=N/A. All product gates stay unchanged.
Next useful implementation proposal is the **development-tooling fake-transport
collector/controller slice**, with exact source ownership/card and tests, not an
Academic AI runtime or full-shell coding agent. Scope it separately before coding.
