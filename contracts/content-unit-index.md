# Content Unit & Index Boundary Contract v0.1.1

## Status

- Contract type: corrected logical boundary draft (2026-09-06); review findings addressed in specification, runtime validation pending. This is not human sign-off.
- Applies to: backend, AI Core, indexing workers and evaluation artifacts.
- Does not select a runtime technology or assert that the product is implemented.
- Normative words `MUST`, `MUST NOT`, `SHOULD` and `MAY` describe the intended boundary.

## 1. Authority boundary

1. Backend/PDP MUST remain authoritative for identity, tenant membership, material lifecycle, approval and access decisions.
2. AI Core MUST consume a bounded authorization context; it MUST NOT infer, broaden or grant access.
3. Indexes MUST be treated as rebuildable projections, never as content, lifecycle or authorization truth.
4. Source content, metadata extracted from source content and model output MUST be treated as untrusted data.

## 2. Canonical identifiers

The boundary uses these logical identifiers:

| Identifier | Meaning |
|---|---|
| `blob_ref` | Internal content-addressable reference to immutable bytes |
| `submission_id` | One tenant-scoped quarantine/upload attempt |
| `source_snapshot_id` | Immutable acquired source snapshot and restrictions |
| `material_id` | Opaque tenant-owned logical learning material |
| `material_version_id` | Opaque immutable version of a material |
| `representation_id` | A derived text/render/OCR/layout/visual representation |
| `logical_surface_id` | Physical page, logical slide, section or equivalent surface |
| `region_id` | Exact bbox/polygon/DOM/text-offset region |
| `block_id` | Structural block |
| `atom_id` | Smallest indivisible unit for a chunk profile |
| `retrieval_unit_id` | Derived child unit eligible for retrieval |
| `context_unit_id` | Parent/window used for hydration and packing |
| `dependency_edge_id` | Typed, scoped relation between units |
| `claim_span_id` | Exact claim-bearing source region |
| `claim_delta_id` | Meaningful difference between claim spans |
| `conflict_set_id` | Set of unresolved or reviewed conflicting claims |
| `index_projection_id` | One projection on a search surface |
| `index_build_id` | Immutable build manifest identity |
| `candidate_relation_id` | Evidence-backed non-authoritative candidate relation |
| `evidence_packet_id` | Internal evidence envelope with a separately serialized model-input projection |

Externally visible resource IDs MUST be opaque. Content hashes, embeddings, fingerprints and storage paths MUST NOT be exposed as tenant-visible identities or cross-tenant existence oracles.

## 3. Identity and version invariants

1. Byte equality MAY permit internal physical storage reuse only when storage policy allows it.
2. Byte equality MUST NOT merge submissions, materials, material versions, ownership, rights, approvals or ACLs.
3. Any meaningful source or publication change MUST create a new immutable `material_version_id`; a published version MUST NOT be overwritten in place.
4. Every representation and structural atom MUST trace to an immutable source snapshot. During quarantine it MUST bind `submission_id`; it MUST NOT require a material version that does not exist yet. Every serving retrieval unit and projection MUST additionally bind an immutable material version through an approved promotion record.
5. A unit containing fragments from multiple effective authorization scopes MUST be rejected.
6. A non-contiguous group MUST enumerate its member fragments; it MUST NOT be represented as an inferred min/max range.

## 4. Representation contract

Each representation record MUST contain:

```yaml
representation_id: opaque-id
representation_type: raw|text_layer|normalized_text|canonical_text|page_render|ocr|layout|visual_description
source_snapshot_id: opaque-id
origin:
  stage: quarantine
  submission_id: opaque-id
producer:
  name: string
  revision: string
  config_hash: internal-hash
artifact_ref: internal-reference
content_hash: internal-hash
quality_state: complete|partial|failed|not_applicable
alignment_map_ref: internal-reference
created_at: timestamp
```

`origin` is discriminated: `quarantine` requires submission + snapshot and forbids a fabricated material version; `material` requires material version + snapshot + promotion reference. Promotion creates a new immutable binding to the original artifact/hash and representation, not a mutation of quarantine history. A representation derived after promotion references that binding. Serving/index admission cannot accept a quarantine-origin reference alone. Backend owns the promotion record and rechecks current restrictions even though the acquisition snapshot is immutable.

Text normalization, OCR and visual descriptions MUST NOT replace the original representation. Conflicting representation outputs MUST be retained and identified. Required-modality failures MUST fail closed according to query policy.

Serialization MUST retain semantic distinctions (sub/superscripts, operators, negation, units, table-cell boundaries and blank values). Locator/chunk-ID coverage alone MUST NOT establish fidelity of serialized model text. Unsupported or lossy representations MUST be flagged before use. Canonical dedup text MUST NOT be reused as citable/model evidence.

## 5. Retrieval unit contract

Each retrieval unit MUST contain the logical equivalent of:

```yaml
retrieval_unit_id: opaque-id
material_id: opaque-id
material_version_id: opaque-id
source_snapshot_id: opaque-id
representation_ids: [opaque-id]
source_fragments:
  - atom_id: opaque-id
    region_id: opaque-id
    locator: structured-locator
    offsets: structured-offsets
    fragment_hash: internal-hash
    order: integer
source_text: string
retrieval_header:
  text: string
  citable: false
retrieval_text: string
context_unit_id: opaque-id|null
chunk_profile:
  id: string
  version: string
derivation_hash: internal-hash
quality_flags: [string]
```

Requirements:

- `source_text` MUST be derivable from ordered source fragments.
- `retrieval_header` MUST be deterministic for its profile and MUST NOT be presented as quoted source text.
- A chunker MUST preserve atoms designated critical by its profile.
- Changing a parser, representation or chunk profile version MUST change derivation identity and trigger a new index build before activation.
- A context unit MAY be hydrated only after a current scope check.

## 6. Dependency edge contract

An edge MUST include source, target, edge type, provenance, rule/model revision, confidence or review state when applicable, and authorization/version scope.

Initial allowed edge types are:

```text
contains, parent_of, prev, next, continues_from,
requires_definition, requires_lead_in, requires_header,
formula_context, code_prologue, caption_of, explained_by,
footnote_of, version_predecessor, conflicts_with,
candidate_neighbor
```

Traversal MUST be bounded by hop, token and unit budgets; MUST detect cycles; and MUST recheck tenant, effective resource scope, lifecycle, purpose and version before target content is hydrated.

Edges MUST distinguish required, optional and not-assessed dependencies. Required dependency closure MUST survive final serialization and budget accounting for a retained anchor. A closure that is unavailable, unauthorized, cyclic, beyond limits or too large MUST block that anchor's dependent claims (or omit the bundle with an incomplete reason). Optional context MUST NOT displace a required closure; an omitted anchor MUST NOT trigger standalone expansion. Pre-pack resolver recall MUST be reported separately from post-pack closure coverage. Cross-version `conflicts_with`/`version_predecessor` edges require explicit access to each pinned version; they do not force same-version equality or confer access.

## 7. Similarity and conflict contract

1. Retrieval scores, content fingerprints and embedding similarity MUST create at most a `candidate_similar` relation.
2. `candidate_similar` MUST NOT automatically become `same_as`, merge, delete, publish, approve or inherit access.
3. Claim deltas and conflicting source spans MUST be preserved independently of dedup decisions.
4. Conflict resolution MUST be an append-only authoritative/reviewer decision record; it MUST NOT rewrite source claims.
5. An evidence packet containing an unresolved material conflict MUST mark that state. The answer policy MUST not present the disputed claim as settled.

6. Conflict assessment MUST use `not_assessed`, `partial`, `completed_no_conflict_observed`, `unresolved` or `resolved`, with method/revision, assessed resource versions, authorized scope and completion/omission reasons. Neither an empty top-K result nor a missing conflict record proves absence of conflict.
7. Known, authorized conflicting claim sets MUST be checked for both-side coverage before generation; lookup/expansion remains bounded and authorized. An exact-match shortcut for duplicate candidate routing MUST NOT bypass this check. Missing a required side marks the claim incomplete. Unknown conflict status does not require refusing every lookup: a source-attributed answer may be allowed by the query policy, but MUST NOT claim cross-source agreement or resolved truth. Comparison/adjudication requiring an unassessed side cannot pass completeness.
8. Denied relation targets MUST NOT expose their IDs, titles, counts or existence in model/public warnings. Resolution MUST bind exact claims/versions; new versions require a new assessment.

## 8. Index projection contract

An index projection MUST contain or reference:

```yaml
index_projection_id: opaque-id
index_build_id: opaque-id
surface: lexical|dense|visual
namespace: opaque-namespace
tenant_partition: opaque-id
authorization_filter_handle: opaque-id
resource_policy_revision: string
publication_revision: string
lifecycle_snapshot: string
material_id: opaque-id
material_version_id: opaque-id
retrieval_unit_id: opaque-id
representation_versions: [string]
chunk_profile_version: string
retrieval_profile_version: string
model_revision: string|null
derivation_hash: internal-hash
quality_flags: [string]
serving_state: staging|active|tombstoned
```

Index payload authorization fields are prefilter copies only. A protected read MUST still be validated against current backend/PDP policy before hydration and delivery.

`tenant_partition` is the resource-owner partition, not automatically the request's active tenant. Public catalog and named-share access use the explicit resource binding in the authorization contract; no wildcard cross-tenant scan is permitted.

Embedding input MUST NOT contain ACLs, tenant secrets, reviewer-private notes or evaluation labels.

Quarantine and staging projections MUST be isolated from active serving namespaces. Only a verified immutable build manifest MAY become active.

## 9. Build and activation contract

An `index_build_id` MUST identify an immutable manifest containing:

- authorized corpus/material-version snapshot;
- representation, parser, chunk, dependency and retrieval profile versions;
- search surface and model revisions;
- expected and produced unit/projection counts;
- rejected/quarantined/partial item counts and reasons;
- integrity hashes and build timestamps;
- source approval reference, publication revision and per-resource policy revisions relevant to build/promotion;
- verification outcome.

Activation MUST fail when:

- the build is incomplete, stale or has orphan projections;
- source approval/lifecycle changed;
- relevant publication/resource-policy revisions or expected corpus snapshot changed;
- any serving projection points to quarantine-only content;
- mandatory quality gates fail.

Activation MUST expose one atomic `serving_snapshot_id` referencing the complete lexical/dense/source-graph/representation manifest and optional visual surface (explicit absent/unsupported if disabled). A query pins that manifest once; adapters MUST reject mismatched surface versions rather than mix generations. Implementations may use one catalog pointer; they need not rely on a transaction across all stores. Publication validation and compare-and-set MUST be serialized with relevant revoke/update decisions; a recheck followed by an unguarded alias write is insufficient. Failed builds leave the previous snapshot active if it is still permitted; cleanup is asynchronous. Rollback must pass current admission checks.

Subject/session/membership/share revisions govern query capabilities and cache freshness; they are distinct from build content/publication revisions. An unrelated user's membership change does not invalidate unchanged content vectors. Revocation of the publishing workload or its approval still blocks promotion. A global epoch is a conservative fallback, not permission to skip validation; its availability cost must be measured.

## 10. Revocation contract

1. Backend/PDP MUST deny access immediately when a revocation or ACL change becomes effective.
2. Cache invalidation MUST include policy epoch and effective-scope changes.
3. Serving projections MUST be tombstoned or removed asynchronously and propagation latency MUST be measured.
4. AI Core MUST NOT rely on physical index deletion as the authorization barrier.
5. A job built against an older approval, material version or policy epoch MUST NOT reactivate revoked content.

The authorization boundary MUST define an authoritative ordering point for protected operations and revocation commits. No operation ordered after an effective revoke may deliver protected content; an operation admitted before revoke must be rechecked at subsequent protected boundaries. Minimum-revision reads alone do not close a check-then-send race: the delivery gate must use a fenced admission/serialization mechanism whose semantics are tested. Already delivered bytes cannot be recalled. Network arrival time is not the authorization linearization timestamp. Exact technology and propagation SLO remain implementation-review decisions.

## 11. Evidence packet handoff

Before generation, each evidence item MUST reference:

- material and immutable material version;
- retrieval unit and exact source fragments;
- representation(s) and physical/logical locator;
- citable source text separated from retrieval-only metadata;
- quality, modality and conflict state;
- current authorization decision reference and purpose;
- dependency-expansion provenance;
- packing decision and token accounting.

The INTERNAL evidence envelope contains the fields above. A separate allowlisted `model_input` projection contains question, permitted conversation, local citation handles, source content/locators, marked context headers and safe completeness/quality warnings. It MUST NOT contain capabilities, authorization decision IDs, internal tenant/subject/grant IDs, storage paths, internal hashes or evaluator labels. The internal envelope records `model_input_sha256`, serialization profile and measured budget for the exact bytes/assets supplied to the generator. Authorization trace and evaluator sidecar stay outside that projection. Citation validation resolves local handles internally and rejects unsupported text or a locator/version mismatch.

## 12. Required correctness metrics

Implementations and experiments MUST report the applicable metric IDs defined in the architecture document:

- content unit: `CU-01` through `CU-05`;
- index/security: `IX-01` through `IX-10`;
- claim/conflict: `CR-01` through `CR-03`.

Definitions, eligibility, snapshot-time semantics and regression cases are corrected in [review regression and metric clarifications](../docs/evaluation/29-review-regression-and-metric-clarifications-v0.1.md). That registry takes precedence over shorthand metric names; historical results keep their original scorer/profile.

Unauthorized exposure, quarantine leakage, scope-crossing expansion, cross-scope cache hits, automatic equivalence from similarity and conflict collapse have a zero-tolerance target on the reviewed verification set.

## 13. Open implementation decisions

This contract intentionally leaves vendor selection, physical tenancy, storage dedup policy, OCR/VLM pipeline, production embedding/reranker, index topology, retention, revoke SLO and reviewer workflow open for later decisions.

The detailed rationale, term mapping, test cases and metric table are in [Content Unit & Index Contract v0.1](../docs/architecture/07-content-unit-index-contract-v0.1.md).
