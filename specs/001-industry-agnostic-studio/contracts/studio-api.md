# Studio HTTP API contract v1

**Status**: planned normative interface; implementation and generated OpenAPI are M0–M4 tasks. The API is a Studio facade, not a claim that the inspected Lite runtime already provides these routes.

## Common rules

- Base path `/api/v1`; JSON is UTF-8. Unknown request fields reject with `422`; omitted optional fields use documented defaults only. IDs are opaque strings, never filesystem paths.
- The backend serves the browser UI and API natively on Linux or Windows on an explicitly configured loopback host by default. Use authenticated local sessions, an exact Origin/Host allowlist, CSRF protection for mutations and no permissive CORS. A native launcher obtains a short-lived one-use bootstrap secret through local delivery; secrets are not URL query parameters or logs. WSL is not an implicit dependency. Remote exposure requires a later deployment design.
- Every authenticated error carries `code`, `message`, `requestId`, `retryable`, and optional `diagnostics[]` and `currentRevision`. Diagnostics reference stable model elements/source locations; errors do not expose credentials or unrestricted host paths.
- A project response includes `revision` and an ETag. A mutation supplies `If-Match`; absence is `428`, stale revision `412`. It never overwrites another editor's work silently.
- Side-effecting asynchronous operations require `Idempotency-Key`, scoped by authenticated principal and operation route/resource. A repeated key and identical canonical request returns the same operation/run; a different payload returns `409 IDEMPOTENCY_CONFLICT`. Persist mapping before delegation and retain it for at least the associated operation/run retention period. Reconnecting the same principal preserves this scope; a new browser tab is not a new run owner.
- `202` means durably accepted, not executed successfully. Operations expose `accepted|delegated|completed|rejected|failed|unknown` and result/error references. A timeout after delegation is `unknown` until reconciliation.
- Request, upload, graph, result-page, retention and event-buffer limits are advertised by capabilities and enforced server-side. Rejected limits return `413` or a typed `422` diagnostic before execution.

## Routes

| Method / path | Request / result | Milestone |
|---|---|---|
| `GET /capabilities` | API/runtime and host OS/architecture identities, provider descriptors, supported operations, resource/graph/time limits, blocked reasons and evidence scope | M0 |
| `GET /projects` | Cursor-paged project summaries | M0 |
| `POST /projects` | `name`, optional admitted `blueprintRef`; returns project/revision | M0 |
| `GET /projects/{projectId}` | Manifest, resource summaries, revision, diagnostic summary, layout reference | M0 |
| `PUT /projects/{projectId}/documents/{documentId}` | Exact authored content + source format; expected revision; atomic save | M0 |
| `POST /projects/{projectId}/edits` | Typed semantic edit batch + expected revision; returns changed document IDs and validation status | M2 |
| `PUT /projects/{projectId}/layout` | Layout sidecar + expected presentation revision; no semantic mutation | M2 |
| `POST /projects/imports` | Bounded archive/upload handle; returns inspectable import report and newly allocated project only after safe extraction | M0/M2 |
| `POST /projects/{projectId}/exports` | Exact revision, inclusion policy; returns operation for a bounded credential-free archive | M2 |
| `POST /projects/{projectId}/validations` | `revision`; returns typed report tied to input/validator identities | M0 |
| `GET /projects/{projectId}/revisions?before=&limit=` | Append-only revision history, newest first, cursor-paged (≤200): origin, document digests; unrecorded legacy revisions are reported; see ADR-0013 | M2 |
| `POST /projects/{projectId}/revisions/{revision}/restore` | `If-Match`; new forward revision from verified copies of an earlier revision (undo/redo transaction) | M2 |
| `POST /projects/{projectId}/recoveries` | `If-Match`, `expectedRevision`, `adopt_external` or `restore_revision`; preserves observed external bytes before committing | M2 |
| `GET /projects/{projectId}/recoveries[/{recoveryId}/preserved?key=]` | Recovery backups and one preserved, digest-verified document or sidecar | M2 |
| `POST /projects/{projectId}/compilations` | `revision`, deployment/scenario refs; returns plan reference/digest or diagnostics | M0 |
| `GET /catalog` | Cursor-paged admitted templates/components/models/blueprints; filters by kind, role, profile, interface and provider availability | M2 |
| `GET /catalog/{entryId}` | Immutable entry identity/version/digest, XDL resource/template refs, parameter schema, provenance, maturity and dependencies | M2 |
| `GET /profiles` | Admitted namespace/version/schema/presentation identities and compatibility/conflicts; read-only discovery | M2 |
| `GET /profiles/{profileId}` | Exact schema/presentation metadata and dependency/limitation summary for an admitted profile | M2 |
| `POST /projects/{projectId}/profile-bindings` | Expected revision plus admitted profile IDs/versions/digests; creates explicit lock/resource changes or conflict diagnostics, never executes provider code | M2 |
| `POST /projects/{projectId}/preflights` | Revision + deployment/scenario/parameter selection; returns frozen snapshot and preflight result | M1 |
| `POST /runs` | `snapshotId`, `preflightId`, permitted run options; returns `runId`, `operationId`, state version | M1 |
| `GET /runs` | Cursor-paged filters by project, snapshot, status and time | M1 |
| `GET /runs/{runId}` | Reconciled state projection, version, capabilities and evidence summary | M1 |
| `POST /runs/{runId}/commands` | `kind`, `expectedStateVersion`, typed parameters; returns operation | M1/M3/M4 |
| `GET /operations/{operationId}` | Durable operation state, provider correlation and result/error | M0 |
| `GET /runs/{runId}/events?after={cursor}` | SSE stream; see [run-events.md](run-events.md) | M1 |
| `GET /runs/{runId}/evidence` | Cursor-paged evidence metadata, integrity/availability and authorized download handles | M1 |
| `GET /runs/{runId}/observations` | Bounded observer/time range; explicit clock/mapping and reduction metadata | M1/M4 |
| `GET /runs/{runId}/diagnostics` | Read-only explanation 1.0: evidence-linked facts, consequences, unconfirmed hypotheses, unknowns and closed next actions; see ADR-0012 | M1 |
| `GET /projects/{projectId}/preflights/{preflightId}/diagnostics` | Read-only explanation 1.0 of a frozen preflight's coded readiness findings and stale-plan assumptions | M1 |
| `POST /runs/{runId}/evaluations` | Snapshot-bound definition reference/digest and exact evidence selection; returns immutable evaluation ID and operation | M4 |
| `GET /runs/{runId}/evaluations` | Cursor-paged definition/input identities, execution status and pass/fail/indeterminate verdicts | M4 |
| `GET /evaluations/{evaluationId}` | Immutable definition/evaluator/evidence identities, values/units, execution status, verdict and reasons | M4 |
| `GET /runs/{runId}/annotations` | Cursor-paged revisioned comments/traceability links kept outside canonical evidence | M4 |
| `POST /runs/{runId}/annotations` | Typed annotation text or pinned trace link and optional element/evidence refs; returns annotation ID/revision | M4 |
| `PUT /annotations/{annotationId}` | Expected annotation revision and replacement content; retains revision history | M4 |
| `DELETE /annotations/{annotationId}` | Expected revision; creates a tombstone without altering referenced evidence | M4 |
| `GET /providers` | Admitted providers, versions, capabilities and unavailable dependencies | M0 |
| `GET /assets` | Explicitly scoped provider inventory; no unrestricted network scan | M3 |
| `POST /assets/{assetId}/reservations` | Requested permitted scope/duration; returns provider fencing token reference | M3 |
| `GET /reservations/{reservationId}` | Observed ownership, scope, fencing identity, expiry, last renewal and uncertainty | M3 |
| `POST /reservations/{reservationId}/renewals` | Expected fencing identity and requested deadline; same-scope extension only; backend performs ongoing active-run renewal | M3 |
| `DELETE /reservations/{reservationId}` | Release owned reservation; returns operation; cannot release another owner's token | M3 |
| `POST /campaigns` | Frozen base snapshot, bounded parameter matrix, concurrency/stop policy | M4 |
| `GET /campaigns/{campaignId}` | Child run identities and aggregate status, never synthetic run verdicts | M4 |
| `POST /campaigns/{campaignId}/cancel` | Stop scheduling children; separately request permitted cancellation of active children | M4 |
| `POST /retention/plans` | Explicit project/run/artifact IDs and retention rule; returns a read-only dependency-aware deletion plan and state fingerprint | M4 |
| `GET /retention/plans/{planId}` | Planned removals, protected dependencies, blockers, counts/bytes when known and expiry | M4 |
| `POST /retention/plans/{planId}/apply` | Explicit selected plan ID/fingerprint; idempotently applies only still-eligible removals and reports each outcome | M4 |

Resource bodies, schemas and generated client types are implemented together from the data model and these contracts; contract tests must reject incompatible request variants. Unsupported milestone routes return `404` with capability discovery making their absence explicit.

## Catalog and profile operations

Catalog entry IDs resolve server-admitted immutable metadata, not arbitrary URLs or executable paths. A blueprint entry includes the exact XDL resource set, profile locks, artifact/provider references and declared scope. Missing dependencies remain visible. `POST /projects` may select this admitted blueprint by ID/version/digest; a later catalog update cannot silently alter an existing project.

Profile binding supplies `baseRevision` and a bounded list of `{profileId, version, schemaDigest, presentationDigest}`. The backend checks namespaces, semantic compatibility and payload schemas, then creates a transactional project revision. It returns `422 PROFILE_CONFLICT` for conflicting/redefined semantics and never installs or executes code as part of selection. Selecting a profile cannot make an OS-incompatible provider available.

## Evaluation, annotation and retention operations

An evaluation request supplies `snapshotId`, `definitionRef`, `definitionDigest` and bounded `evidenceRefs`. The definition must resolve from the frozen run inputs to the admitted evaluator contract; evidence must belong to that run and satisfy its clock/coverage/integrity rules. The backend records actual evidence digests and evaluator identity before execution, returns `202` with `evaluationId`/`operationId`, and preserves completed results immutably. Repeating the same idempotency key returns the same job; reevaluation is a distinct derived record referencing the same inputs. Definition edits require a new source revision and cannot modify a run snapshot or a completed evaluation. See [experiment-evaluation.md](experiment-evaluation.md).

Annotations are separate presentation/audit records with an ID, revision, author/session identity, timestamp, `kind` (`comment` or `trace_link`), text or typed target reference, and optional model/evidence references. Trace targets record URI and pinned revision or explicit unknown; a link is never proof of target validity or a passed requirement. Render inert escaped text or an allowlisted Markdown subset. Updates/deletes require expected revision and retain historical revisions/tombstones; canonical evidence bytes are never patched.

Annotation sidecar version 1.1 adds optional `target.claimStatus`: an opaque nonblank reported string
(maximum 256 characters; no C0/DEL controls), preserved exactly rather than interpreted as a verdict.
Legacy `{uri, revision}` targets remain valid and retain absent status. Optional `definitionRefs`
contains at most 32 unique `{definitionRef, definitionDigest}` pairs resolved against the run's frozen
definitions; the digest is `sha256:` followed by 64 lowercase hexadecimal digits. `elementRefs` may
identify frozen XDL resources such as Scenario as well as model elements; `evidenceRefs` identifies
same-run evidence. Model/definition associations require the intact canonical snapshot. Invalid,
cross-run or unavailable subject identities reject rather than silently dropping the association.
The existing assertion v1/profile schema is unchanged. See ADR-0009 for compatibility and evidence.

A retention plan is side-effect-free. It names exact IDs, dependency edges, protected active-run inputs, expiry and a fingerprint of the observed state. Apply is a separate explicit idempotent operation: recheck active ownership, references, permission and fingerprint before any deletion. Stale plans return `409 RETENTION_PLAN_STALE`. Block deletion of active-run inputs, shared required artifacts or protected evidence; report partial filesystem failures without claiming complete removal. No API accepts a glob or host path as a deletion target. Existing run/campaign state cannot be made successful by deleting its failed evidence.

## Semantic edit envelope

`POST .../edits` accepts a bounded transaction: `baseRevision`, `edits[]`. Each edit has an operation kind and schema-validated arguments referring to stable XDL resources/elements. Initial operations are `add_element`, `remove_element`, `set_parameter`, `connect_endpoints`, `disconnect_flow`, `set_binding`, and `rename_display_label`. Adding an element selects a declared semantic kind and catalog template; it does not submit an arbitrary browser node blob. Removal reports impacted references and requires an explicit replacement/removal set. Unsupported schema/profile content is never discarded to make an edit succeed.

## Preflight and start

Compilation is side-effect-free. Preflight performs only admitted read-only probes and validates existing reservations; acquiring a physical reservation is an explicit separate operation. Preflight freezes input bytes/plan/identities and returns:

```json
{
  "preflightId": "pf-example",
  "snapshotId": "snap-example",
  "status": "blocked",
  "planDigest": "sha256:<computed>",
  "capabilityDigest": "sha256:<computed>",
  "expiresAt": "<server timestamp>",
  "diagnostics": [{"code": "PROVIDER_UNAVAILABLE", "severity": "error", "message": "The selected realization has no admitted provider."}]
}
```

This is a shape illustration, not a valid runnable fixture. Only `status=ready` is start-eligible. A start rechecks expiry, input identities, provider compatibility, reservation/authority, artifact integrity and target readiness. Any changed assumption rejects with `409 PREFLIGHT_STALE` or `422 ADMISSION_REJECTED`; it never silently substitutes a target or model. The preflight TTL is bounded by the minimum freshness window of its dependent capabilities/reservations.

Provider launch receives the persisted run ID and operation ID. A start retry cannot create a second run. If the provider cannot prove whether the first start happened, expose `unknown` and reconcile; do not replay start.

The additive `readinessVersion: "1.0"` response contains independent records named `backend`,
`provider`, `model`, `artifacts`, `capabilities`, `target`, `resources`, `ownership`, `clocks` and
`authority`. Each has `status`, `message`, `elementRefs`, `diagnosticCodes`, `remediation` and optional
`facts`. Missing or unknown facts are not positive admission. Legacy `dimensions` strings are derived
from these same records. `limits` is the exact selected provider's limits object, or empty when not
advertised. An unavailable provider never inherits another provider's execution configuration.

`planPreview` is null without compilation, otherwise contains `snapshotId`, `snapshotDigest`,
`revision`, `selection`, `planDigest`, `semanticDigest`, `compiler`, `contributingDocuments`, `plan`
and `scope: "declared_intent_only"`. The preview grants no runtime-health or physical authority claim.
Start verifies canonical snapshot bytes and current provider identity/facts. Campaign creation rejects
snapshots lacking an originally ready matching preflight; existing idempotent requests resolve their
saved operation or payload conflict before new mutable admission is evaluated.

The selected adapter must also prove that its effective generated XDL/plan matches the requested snapshot before admission, and record effective identities after execution. The inspected Lite harness generates its own documents; if it cannot accept a requested edit, reject it rather than run a fixed preset under the edited snapshot's identity. See DEP-RUN-CONFIG in the plan and the provider contract.

## Commands and failures

Kinds are a closed registry: `stop` and `cancel`; conditionally `pause`, `resume`, `step`, `reset`, `set_parameter`, and `activate_fault`/`recover_fault`. Capability discovery declares exact scope and parameter schemas. Provider authorization and state are checked again even if the frontend previously enabled a button.

`stop` requests the declared orderly shutdown policy; `cancel` requests the admitted cancellation policy. Neither means force-kill all similar processes. Emergency hardware controls require a separately declared provider capability and do not replace equipment-level safety mechanisms.

| Code / HTTP | Meaning |
|---|---|
| `UNAUTHORIZED` / 401; `FORBIDDEN` / 403 | Session absent, origin/permission invalid or operation outside granted scope |
| `REVISION_CONFLICT` / 412 | Project changed; return current revision for explicit rebase |
| `STATE_CONFLICT` / 409 | Expected run state version is stale |
| `CAPABILITY_UNSUPPORTED` / 422 | Provider cannot perform this operation |
| `RESOURCE_BUSY` / 409 | Reservation/resource is owned elsewhere |
| `PROFILE_UNRESOLVED` / 422 | Source preserved but incompatible or absent semantics prevent execution |
| `PRECONDITION_FAILED` / 422 | Missing artifact, invalid clocks, incompatible interface or closed runtime admission |
| `PROVIDER_UNAVAILABLE` / 503 | Integration unavailable; no success implied |
| `EVIDENCE_UNAVAILABLE` / 404; `EVIDENCE_INVALID` / 422 | Evidence absent or integrity cannot support the requested read/evaluation |
| `LIMIT_EXCEEDED` / 413 or 422 | Bounded resource limit exceeded |

API contract tests must cover concurrency, origin checks, unknown fields, path/ID confusion, duplicate operations, capability rejection and stale preflight. Client-side disabling is usability only; the backend is the enforcement boundary.
