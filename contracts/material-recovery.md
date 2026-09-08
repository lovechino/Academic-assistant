# Material deletion and recovery boundary — draft v0.1

2026-09-07. Backend-owned logical contract, not API/state-machine implementation. [Policy proposal](../docs/governance/06-material-deletion-recovery-v0.1.md) explains scope and unresolved retention/roles. All REC cases in the [test map](../docs/evaluation/37-wp04-behavior-security-review-v0.1.md) are NOT RUN. This future admission/lifecycle lane is outside the first manual QA fake-adapter slice; no product GO.

## 1. Target and authority

- Resolve an opaque exact submission, material or material-version target under authenticated subject + active tenant + owner binding + action + purpose + expected current revision. Filenames, source instructions and client hashes are not target authority. A material-wide delete includes its versions; a version-only delete does not imply deletion of siblings. Backend pins the affected set at commit, rejects stale previews/concurrent additions rather than silently broadening the operation.
- Actions are separate: `inspect_trash_metadata`, `soft_delete`, `restore_to_review`, `purge`. Metadata inspection does not authorize bytes, generic search/model use, restore or purge. Restricted content inspection needs its own exact assignment/processing policy. Upload, view, share, previous ownership or platform administration alone grants none of these new actions.
- A share recipient may not delete/restore the owner's resource. Removing a local shortcut is a different use case. Owner-side deletion disables dependent public/share access; restore never recreates old public publications/shares/grants. No cross-tenant duplicate/existence disclosure, including trash listings, batch counts and failure messages.

## 2. Soft-delete and retained data

Backend atomically records a tombstone, affected identity/version set, actor/decision reference, new monotonic lifecycle generation, deletion time and policy-pinned recoverability deadline/hold disposition. These are protected metadata, not source instructions. Publication/review state and retention state are separate axes; no deleted item is serving-eligible merely because its previous content status was published.

Effective deletion participates in the same authoritative ordering/fencing as revoke. Subsequent search/hydration, dependency reads, model-use admission, answer/history replay, delivery and source viewer release MUST deny use of the deleted resource. In-flight protected operations use existing full-influence/current-boundary rules; already lawfully released bytes cannot be recalled. Tombstoning/removing index/cache copies is asynchronous cleanup, not the security barrier. Stale index/parse/review jobs and late callbacks cannot activate or overwrite a newer lifecycle generation.

Immutable bytes, provenance/locators and review history MAY remain in restricted retention storage if policy permits. Retention does not preserve permission to read or process them. Quarantined/known-forbidden content remains restricted; restore is not sanitization, incident clearance or permission for external OCR/VLM. Mandatory audit failure prevents the protected state change unless durable admission evidence exists under the reviewed policy.

## 3. Restore-to-review, not undo-authorization

Backend rechecks current restore authority, deletion instance/generation, expiry, hold/security/rights restrictions, ownership, complete available artifacts and current parent lifecycle. Restore MUST NOT rewind security/policy epochs, undo deny records, revive expired membership or replay historical grants/approval/public/share bindings. Historical review is evidence to reassess, not current approval.

A successful restore creates a new nonserving recovery revision linked to the immutable original snapshot/version and deletion record. For a published/archived material lineage, any later republication creates a new immutable material version/promotion binding according to the content contract; immutable original bytes may be reused with verified provenance, never mutated. A restored pre-promotion submission remains in restricted intake; it is not fabricated into an approved material version.

Current content/rights/security review and a separate authorized publication action are required before staging/atomic activation. No reviewer means pending, not automatic publication. A deleted material parent continues to block a restored child; parent restore does not clear independently deleted children. Required dependencies are checked independently: restore does not recursively restore them or mark missing visual/context complete. No silent superseding of a newer active version.

## 4. Restore/purge races and physical reachability

Restore, purge claim and conflicting lifecycle mutations require an authoritative per-target generation/CAS or equivalent serialization with resource/reference reservation. Restore wins only if it atomically reserves recoverable artifacts before an irreversible purge claim; purge then cannot delete those artifacts while that reservation is valid. Purge wins first → restore unavailable, including during partial physical cleanup. Failed restore stays nonserving; reservation expiry/recovery must be bounded and fenced. Technology and timeout choices are open, not an assumed transaction across all stores.

Purge work is idempotent and tracks each authoritative reference/derivative/storage destination to completion; partial purge is not reported as complete. A retry resumes the same purge operation, not a fresh delete with new retention. Tombstone/security journal remains effective throughout failure/restart. Deadline expiry may make restore unavailable before physical removal; an approved retention hold can delay purge without granting serving access or automatically extending ordinary restore authority.

Physical blob deletion/crypto-erasure MUST verify authoritative reachability and holds across all live/retained submissions, versions, derivative references and restore reservations in the dedup domain. New reference creation and purge claims must serialize on that ownership/reachability boundary too; checking a stale refcount once is insufficient. Never delete other owners' bytes because one upload shares a hash. Client-supplied hash/refcount is not authoritative. Cross-tenant dedup is not selected; if required later, tenant-isolation and erasure/key semantics need separate review.

## 5. Idempotency, replay and UX

An operation key is scoped by subject, tenant and action, with server-canonical payload binding exact target set, expected revision and policy profile. Same key/different payload → conflict; same key/same operation → its status under current status-read permission, no second mutation. Delete and restore have distinct action namespaces. Duplicate delete MUST NOT reset the recoverability deadline; stale restore/replay cannot undo a later delete. Each fresh authorized operation needs a current generation and an appropriate new identity.

Responses expose only permitted opaque references, actual outcome and recoverability limits. UI distinguishes moved-to-trash, restore-pending-review, expired/unavailable and purge-pending/complete without revealing unauthorized existence. Deletion confirmation shows exact authorized scope; irreversible purge needs a distinct confirmation/privileged policy. UI callbacks obey [request/view generation binding](http-api.md). No product route/schema/retention days selected here.

## 6. Backups, rollback and checkpoints

Backup recovery is disaster recovery, not ordinary user restore. Restore into isolation; reconcile the authoritative current deletion/revoke/purge journal and policy before any serving/publication. A backup cannot restore old ACLs, grants, active aliases or tombstoned content to service. If journal freshness/completeness is unavailable, remain nonserving. Copies subject to erasure remain blocked and must be handled by the chosen backup-retention policy; do not promise instant erasure of every backup or guaranteed recovery after purge/crypto-erasure.

Before lifecycle implementation: resolve retention/role/hold rules, recovery scope, audit and reservation/serialization design. Before real data: prove storage/versioning/backup behavior, derivatives inventory, current-policy fencing and REC integration schedules. Recovery correctness cannot be inferred from fake tests. Before any republish: current rights/content approval and complete atomic serving manifest remain mandatory.
