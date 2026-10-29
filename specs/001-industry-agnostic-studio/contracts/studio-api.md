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
| `GET /projects/{projectId}/inspection` | Read-only project inspection (amendment): example scope, import provenance, declared profile locks verified with admission's identity/sidecar/duplicate checks, supporting files (never executed), unresolved extension payloads by schema position and unparsed documents; never fetches, installs or runs a dependency | M1 |
| `GET /projects/{projectId}/presentation` | Effective inert domain presentation (amendment; ADR-0017): sanitized labels for core terms, allowlisted icons, form groups, bound or blueprint-default domains, conflicts where domains disagree (core terms kept) and all admitted domains for cross-industry labelling; never semantics | M2 |
| `GET /projects/{projectId}/communication?runId=` | Declared/resolved/observed communication projections (amendment): authored flows; the run provider's resolution with transport, scope and limitations; observed samples per observer-targeted flow with source, clock, freshness (live/stale/final) and integrity; `not_collected` when no observer targets a flow; Lite and owned evidence never labelled native X-COM | M2 |
| `GET /projects/{projectId}/connections` | Read-only connection admission 1.0: per-flow checks, feedback cycles, network links, coupling status and admitted contracts; see ADR-0014 | M2 |
| `GET/POST /projects/{projectId}/deployment-variants`, `PATCH .../deployment-variants/{documentId}` | Named authored Deployment/Scenario variants (amendment): list, clone with expected revision, and rebind (target, realization, artifacts, resources) returning recomputed compatibility and resolution without committing an ambiguous selection | M2 |
| `GET /projects/{projectId}/deployment-variants/{documentId}/resolution` | Read-only deployment resolution 1.0 (amendment): binding compatibility, resource/time/network constraints, effective-value chains with undefined precedence rejected, and portable intent separate from unresolved environment/secret references; see ADR-0015 | M2 |
| `GET /projects/{projectId}/deployment-variants/{documentId}/comparison` | ADR-0028: two distinct Deployment documents, one required current revision and provider descriptor; shared System source witness, paired static resolution, declared targets/mappings and explicit unmeasured/unknown outcomes; no runtime authority | M2/M3 |
| `GET /projects/{projectId}/deployment-variants/{documentId}/physical-bindings` | Read-only physical-binding observations (amendment; ADR-0018): authoritative selected source and current revision, logical references joined to server inventory, identity/interface/metadata/readiness facts, unresolved and provider-failure diagnostics; no reservation, probe, secret resolution or execution authority | M3 |
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
| `GET /runs/{runId}/timeline` | Read-only scenario/evidence timeline 1.0 (ADR-0019): verified frozen selection, distinct intention/recorded/evaluation rows, explicit admitted clock placement or unplaced reasons, original gaps/integrity, bounded pages and input-bound cursors; no execution or evaluation authority | M4 |
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
| `GET /assets/{assetId}/probe-options` | ADR-0027 amendment: independently granted observation eligibility and installed binding pin; no provider contact or runtime authority | M3 |
| `POST /assets/{assetId}/probes` | ADR-0027 amendment: explicit current binding digest, observe-only scope and idempotency key; durable owner operation with bounded observation/unknown result; no lease or runtime grant | M3 |
| `GET /assets/{assetId}/reservation-options` | ADR-0025 amendment: current principal/asset request eligibility for each independently granted scope; bounded explicit inventory only, no lease or runtime grant | M3 |
| `POST /assets/{assetId}/reservations` | Requested permitted scope/duration; returns provider fencing token reference | M3 |
| `GET /reservations` | ADR-0025 amendment: cursor-paged signed-in principal's local ownership history and request eligibility; no provider inspection or reacquisition | M3 |
| `GET /reservations/{reservationId}` | Observed ownership, scope, fencing identity, expiry, last renewal and uncertainty | M3 |
| `POST /reservations/{reservationId}/renewals` | Expected fencing identity and requested deadline; same-scope extension only; backend performs ongoing active-run renewal | M3 |
| `POST /reservations/{reservationId}/reconciliations` | Empty closed body and idempotency key; inspect the installed provider for the original owner/fence without reacquiring (ADR-0024 amendment) | M3 |
| `DELETE /reservations/{reservationId}` | Release owned reservation; returns operation; cannot release another owner's token | M3 |
| `POST /campaigns` | Frozen base snapshot, bounded parameter matrix, concurrency/stop policy | M4 |
| `POST /campaigns/preview` | Side-effect-free authoritative bounded expansion; no campaign/child allocation | M4 |
| `GET /campaigns` | Cursor-paged workspace campaign history with frozen input provenance | M4 |
| `GET /campaigns/{campaignId}` | Child run identities and aggregate status, never synthetic run verdicts | M4 |
| `POST /campaigns/{campaignId}/cancel` | Stop scheduling children; separately request permitted cancellation of active children | M4 |
| `POST /retention/plans` | Explicit project/run/artifact IDs and retention rule; returns a read-only dependency-aware deletion plan and state fingerprint | M4 |
| `GET /retention/plans/{planId}` | Planned removals, protected dependencies, blockers, counts/bytes when known and expiry | M4 |
| `POST /retention/plans/{planId}/apply` | Explicit selected plan ID/fingerprint; idempotently applies only still-eligible removals and reports each outcome | M4 |

Resource bodies, schemas and generated client types are implemented together from the data model and these contracts; contract tests must reject incompatible request variants. Unsupported milestone routes return `404` with capability discovery making their absence explicit.

### Reservation authority amendment (ADR-0024)

The reservation request selects `scope: observe|stimulate|destructive` (default
`observe`) and integer `durationSeconds` from 1–300 (default 30). Each scope needs
its own current server-owned principal/asset grant and declared provider capability.
The body cannot supply an owner, grants, provider installation or executable data.
Renewal takes the existing fencing identity (1–256 characters) and the same bounded
duration; it cannot widen scope or reacquire. The additional reconciliation route
requires an empty closed body and an idempotency key. It inspects only the original
installed provider/fence; a lost original fence remains unknown. Explicit owner
cleanup can release a known lease after grant revocation. Terminal history confers
no authority and its repeated cleanup does not contact a provider.

The backend persists the operation/key mapping and reservation identity before
delegation, then commits unknown lease intent before the provider call. API results
carry `operationId`, `reservationId`, operation status and result/error references.
Read the reservation separately for ownership, expiry and uncertainty; a completed
old operation receipt is not a current lease grant. Restart preserves operation
identity, marks pending work/nonterminal leases unknown and never repeats reserve.

Capabilities add `labReservations` with contract version, configured/unavailable
status, server-installed lease descriptors, evidence scope, independent scopes and
storage/call bounds. This is separate from executable provider admission. Existing
asset/placement observations still report unavailable physical runtime admission
and `activeReady=false` until that integration is implemented. A typed native-host
configuration is required for positive reservation routes; the stock launcher
installs none. A fixture is identified as a fixture and supplies no live-device
acceptance. Physical commands, active-run renewal and ownership-loss integration
remain unfinished. No HTTP/project/profile input can install this configuration.

### Reservation observation amendment (ADR-0025)

Both added GETs carry `contractVersion=1.0`, the authenticated `principal`, numeric
`observedAt` in the server lease clock, `runtimeAdmission=unavailable` and empty
`physicalCommands`. Request options bind the exact `assetId`, configured/unavailable
lease-service status, provider ID/evidence scope, maximum duration of 300 seconds,
and three ordered `scopes` entries (`scope`, boolean `eligible`, bounded reason codes).
Eligibility requires the exact current grant, declared capability, resolved identity
and observed availability. It is advisory: reserve independently rechecks its contract.
No client principal/grant/provider-installation parameter is accepted.

`GET /reservations` uses the standard cursor/1–200 limit contract and returns only
the principal's records. Each closed lease view adds `requests.renew|release|reconcile`
booleans describing operations available to request from this local observation.
The mutating endpoints still recheck current provider/asset pins and ownership.
History performs no provider call and never implicitly reconciles. It preserves
unknown ownership; an elapsed owned deadline uses the existing expiry transition.
Terminal history has no active authority. Each page is an independent observation;
concurrent changes can alter page membership. The browser requests 50 rows and at
most 20 pages from the bounded 1,000-record ledger, with explicit refresh/retry.

## Catalog and profile operations

Catalog entry IDs resolve server-admitted immutable metadata, not arbitrary URLs or executable paths. A blueprint entry includes the exact XDL resource set, profile locks, artifact/provider references and declared scope. Missing dependencies remain visible. `POST /projects` may select this admitted blueprint by ID/version/digest; a later catalog update cannot silently alter an existing project.

Profile binding supplies `baseRevision` and a bounded list of `{profileId, version, schemaDigest, presentationDigest}`. The backend checks namespaces, semantic compatibility and payload schemas, then creates a transactional project revision. It returns `422 PROFILE_CONFLICT` for conflicting/redefined semantics and never installs or executes code as part of selection. Selecting a profile cannot make an OS-incompatible provider available. Preflight also reports authored Profile resources (amendment): an unadmitted extension namespace is a blocking `PROFILE_UNRESOLVED` diagnostic (source preserved, unresolved), and an authored resource for an admitted namespace whose version, `schemaRef`, `conflictPolicy` or `compatibleApiVersions` differ from the admitted semantics is a blocking `PROFILE_CONFLICT` diagnostic.

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

`POST .../edits` accepts a bounded transaction: `baseRevision`, `edits[]`. Each edit has an operation kind and schema-validated arguments referring to stable XDL resources/elements. Initial operations are `add_element`, `remove_element`, `set_parameter`, `connect_endpoints`, `disconnect_flow`, `set_binding`, and `rename_display_label`. Adding an element selects a declared semantic kind and catalog template; it does not submit an arbitrary browser node blob. Removal reports impacted references and requires an explicit replacement/removal set. Unsupported schema/profile content is never discarded to make an edit succeed. `add_binding` (amendment) creates a Deployment binding for an element of that Deployment's System: binding ID, element ID, declared realization class, an existing target whose declared lifecycle is copied, and optional declared artifact choices; it is the realization choice of the instance wizard, separate from role and placement (`add_element` `nodeId`). `set_time_mapping` (amendment) adds, replaces by `mappingId`, or removes (`remove: true`) one Deployment time mapping between two declared System time domains with a mapping description and a finite non-negative tolerance; the authoritative validator checks the domains, and mapping accuracy is never evaluated. `set_flow_contract` (amendment) declares or removes one System flow's owned connection contract (ADR-0016): `causality: unit-delay` and/or a `linear` `converter` (`fromUnit`, `toUnit`, finite `scale`, `offset`); omitting both removes it. It adds the connections Profile resource once if absent; admission and the selected provider decide the verdict, and nothing is converted or delayed by the edit.

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

Campaign presentation amendment (ADR-0020): preview/list/detail add
`campaignVersion: "1.0"` and `baseInput`. Verified `baseInput` identifies the frozen
`snapshotId`, `snapshotDigest`, `projectId`, `revision`, `selection` and `providerId`.
It requires the campaign's base identity digest and managed canonical snapshot bytes
to agree. Otherwise it is `{status: "unavailable", reason: "SNAPSHOT_INTEGRITY"}`;
child states remain readable and no current draft supplies a fallback. Existing
`baseSnapshotDigest` identifies the complete planner base object, including its own
snapshot digest; it is distinct from `baseInput.snapshotDigest`. Stored records are
unchanged. List pagination precedes verification. Preview creates no campaign or
child. Cancellation returns separate active cancellation outcomes and never attests
terminal cleanup or assertion success. Backend scheduling/recovery remains independent
of browser polling. HTTP/XDL/profile/evaluator versions are unchanged.

Kinds are a closed registry: `stop` and `cancel`; conditionally `pause`, `resume`, `step`, `reset`, `set_parameter`, and `activate_fault`/`recover_fault`. Capability discovery declares exact scope and parameter schemas. Provider authorization and state are checked again even if the frontend previously enabled a button.

ADR-0030: the owned reference 1.2.0 conditionally admits `set_parameter` for the
explicit live-target model input. `parameters` contains exactly `inputId: "target"`,
`expectedValue` and `value`; both values are finite numbers in [-100,100]. Commands
retain the existing idempotency key and `expectedStateVersion`. Stale state or
an unsettled command returns 409 `STATE_CONFLICT`; stale old value returns 409
`LIVE_INPUT_CONFLICT`. Invalid values, unsupported input and exhausted 32-change
budget return 422 `LIVE_INPUT_INVALID|LIVE_INPUT_UNSUPPORTED|LIVE_INPUT_LIMIT`.
Unadmitted capability returns 422 `CAPABILITY_UNSUPPORTED` before delegation.

Opt-in run metadata adds `liveInputs`, `liveValues: {target: number}`,
`liveMutationCount` and `controlLimits.maxLiveMutations`. These observations do
not replace the frozen `configuration`. Durable operations retain the original
parameters and server-authenticated principal; a confirmed operation adds
`result.mutation` as specified by the event contract. Lost acknowledgement
retains the original request identity and exact payload in browser storage.
Proposal review after an observed state/value change is explicit.

Command parameters must be representable as finite UTF-8 JSON before runtime
lookup and idempotency fingerprinting. Nonfinite numbers (including overflowed
JSON exponents), nested nonfinite values and unencodable strings return422
`REQUEST_INVALID`; no operation or live effect is created. Opaque valid JSON is
preserved, and provider-specific admission still applies independently.

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

## Read-only physical observations 1.0 (ADR-0018)

`GET /assets` returns an allowlisted inventory observation with bounded paging, `complete`,
`truncated`, `activeReady: false`, unavailable physical-provider admission and safe diagnostics.
The facade observes at most 32 explicitly registered providers and 1,000 inventory entries, retaining
at most 100 inventory diagnostics (`/assets` also includes its one fixed unavailable-admission
diagnostic). Per asset it exposes at most 64 interface declarations, examines at most
64 capabilities and 16 host-OS entries, and bounds public metadata strings to 256 characters.
Invalid, ambiguous, failed or truncated observations make completeness false. Private provider data,
endpoints and credential-bearing fields are not a public inventory representation. Provider inventory
methods must honor their trusted bounded-call contract; this facade does not install providers or
supply a new timeout/admission framework.

`GET /projects/{projectId}/deployment-variants/{documentId}/physical-bindings` optionally takes the
expected `revision`; a stale revision rejects with 412. It asserts project integrity and uses the
pinned authoritative validator before parsing or observing inventory. Its report names the current
source revision, selected document, System and Deployment, preserves each canonical logical reference,
and joins physical/hybrid placements through the target's opaque `externalAssetRef`. Interface
requirements derive from the selected System's declared endpoints/interfaces; browser-supplied
requirements or inventory labels cannot override them. Unsupported endpoint references stay unresolved
and are never contacted or echoed.

The report keeps `bindingObservationVersion: "1.0"`, `sourceValid`, `inventoryComplete`, per-binding
identity/interfaces/metadata/availability/admission/permission facts and diagnostics. Missing evidence
remains unknown. `activeReady` is false and `runtimeAdmission` unavailable; neither a matching asset
nor an `admitted_integration` string in its observation confers active authority. The report changes
no XDL, project revision, deployment admission, run snapshot or portable export, and performs no
reservation, command, probe or secret resolution. Physical reservation/control APIs remain unadmitted.


## Scenario/evidence timeline 1.0 amendment (ADR-0019)

`GET /runs/{runId}/timeline` is an additive read projection, not a runtime/provider
operation. Implementation and combined UI verification are in progress. Its closed
query accepts optional `snapshotId` (exact expected identity), `clockDomain`, opaque
`cursor` and `limit` (1–200, default 100). Duplicate/unknown selectors and malformed
cursors are rejected; a foreign snapshot or changed cursor context returns 409.

The response carries `timelineVersion: "1.0"`, `readOnly: true`, exact `runId`,
`snapshotId`, `snapshotDigest`, `projectId`, frozen `projectRevision` and selected
`System`/`Deployment`/`Scenario` references. Managed snapshot verification and
full-source authoritative validation precede parsing. Current draft source is never
an executed-intent fallback. `inputIdentity` binds the exact bounded input observation.

Rows have stable `id`, `layer` (`intent|recorded|evaluation`), `kind`, evidence scope
and `position`. Position retains the original clock and decimal-string tick, an
admitted tick unit or null, `aligned|unplaced`, and an explicit reason for unplaced
facts. Evaluation positions additionally retain the half-open window's `endTick`.
Same-axis placement does not establish causality or observed success. Receipt UTC
and encoding are separate from source time. The installed reference-v1 codec alone
admits its microsecond ticks. Only that exact run/provider/effective-input context
admits authored seconds in the same simulation clock. Unsupported mappings/units,
missing source times and opaque fault activation/recovery remain unplaced.

Intent rows preserve canonical references and declared identifiers; opaque/private
payload fields are not copied. Recorded rows preserve event identity, sequence,
evidence integrity and source-time status. A verified prefix of an invalid journal
remains inspectable but unplaced with invalid integrity. Unknown/malformed metadata
and unsupported numeric values do not become zero or silently trusted observations.
Gap details use an allowlisted projection. Original evidence bytes remain unchanged.
Evaluation rows retain exact definition/result/evidence digests, execution status,
verdict/value, coverage and partial state. A metric has no assertion verdict. A
historical evaluation's verdict is not an assessment of newly changed evidence;
`matchesCurrentEvidence` is explicit. The timeline never runs an evaluator.

`assessmentDefinitions` exposes up to 32 resolved declarations from the selected
frozen Scenario, including typed expressions, windows, declared coverage policy and
definition/profile/schema identities. `status: available|unavailable` and `complete`
distinguish resolved absence, truncation and resolver failure. Inspection does not
create evaluation jobs. These declaration identities bind cursor input identity;
evaluated rows must match the selected frozen definition pin. Provider-configuration
intent has its own unplaced row and configuration digest, not a fabricated Scenario
fault element or authored timestamp. Recorded source provider/version and immutable
evaluation reason codes/evaluator identity remain inspectable.

For `not_started`, `running`, `unavailable` or `error` execution, absent coverage or
partial metadata remains JSON null and is displayed as unknown. Such a job has no
verdict. This does not make otherwise verified recorded rows unavailable. Completed
results retain their required coverage/partial shape, and pass/fail requires complete,
non-partial coverage; missing metadata is never coerced into a known result.

`counts`, `inputsComplete`, `clockDomainsComplete`, `diagnosticsComplete`, original
reader gap completeness and `reduction` distinguish incomplete input observation
from page omission. Processing considers at most 50000 canonical records, 1000 source
intentions and 200 recent evaluation records. Existing reader byte/acquisition caps
still apply. The timeline does not attest canonical full-data coverage. Clock option
discovery cannot claim completeness after a processing cap. Each page contains at
most 200 rows, with exact integer tick ordering. An opaque continuation cursor binds
run/snapshot, clock, actual journal and evaluation input identities and interpretation.
Changed context returns `TIMELINE_CURSOR_STALE` and requires refresh from page one.


Recorded comparison amendment (ADR-0021): both comparison routes return
`comparisonVersion: "1.0"`, frozen `left`/`right` run/snapshot/project identities,
12 named `configuration` rows with `same|different|unavailable` and explicit side
availability, and at most 32 recorded `fields`. Original mode, compatibility,
differences/diagnostics and `rerunRequiresFreshAdmission` remain. Configuration is
read from verified protected snapshots, including full frozen provider identity,
compiled artifacts/profile/resource identities, capabilities, compiler and clocks;
no current-draft/provider fallback or invented clock applies. Missing provenance,
invalid/incomplete evidence, incompatible quantities/clocks, uncertain alignment,
gaps or missing/unequal exact original windows block like-for-like pairing. Source
ticks remain signed decimal strings. Each side retains its own recorded numeric
summary and quality; no interpolation or synthetic assertion verdict is produced.
Input values are bounded to 64 KiB, depth 20, 8,192 nodes and 2,048 entries per container;
excessive metadata is unavailable without changing protected inputs. Original gap counts
are retained. Recorded observer identity/unit semantics/clock must agree with the frozen
compiled declaration. Source reader limits remain unchanged.
`COMPARISON_LIMIT` is a typed 422 refusal. Inspection and recorded playback create
no workload; fresh execution retains backend admission and a new identity.


## Explicit observation amendment (ADR-0027)

The separate `labProbes` capability defaults to unavailable. A native host must
explicitly install the observation implementation and exact principal/asset
permission; existing reservation grants and descriptors remain unchanged.
`GET /assets/{assetId}/probe-options` reports version 1.0 eligibility, the separate
binding pin, authenticated principal, evidence scope and bounds without provider contact.

`POST /assets/{assetId}/probes` accepts only required `expectedBindingDigest` and
optional `scope: "observe"`. An idempotency key is mandatory. Session/Host/Origin/
CSRF checks apply. Missing installation returns `503 PROBE_NOT_ADMITTED`, changed
binding `409 PROBE_BINDING_CHANGED`, and missing permission `403 FORBIDDEN`.
Unknown fields, imported endpoints, requested owners, active scopes and deadlines
reject before provider contact. The original operation/key mapping is durable
before delegation; a duplicate returns that original receipt even after restart
or installation/grant removal. A changed payload conflicts and never re-probes.

`GET /operations/{operationId}` filters this operation to its owner and closed
public projection. Operation completion acknowledges an `observed` or
`unavailable` result, not readiness or execution. Unknown acknowledgements/results
remain unknown. Accepted/delegated records become unknown on restart and are
never replayed. Source clock/domain/signed ticks/uncertainty and backend receipt
time are separate. Private bindings and unknown provider payloads stay excluded.

Limits: 32 bound installations; eight contacted resource references per binding;
1,000 operations of at most 16 KiB each; callback timeout greater than zero through
five seconds; one outstanding callback per observation provider ID and no queue.
Timeout retains capacity until actual return and discards late results.
No automatic import/open/refresh/preflight probe, reservation, physical command
or runtime-admission upgrade is introduced. The existing read-only physical-binding
report stays free of probe side effects. Backend and UI implementation are under
combined verification; full native/browser/package and actual hardware acceptance
remain open. Browser pending requests and at most 20 operation references persist
in a versioned session record bounded to128KiB; cached data is never an authority
grant and contains no private binding or cached result. Explicit retry preserves
the original request identity; inspection performs no provider callback.

## Revision-coherent deployment comparison (ADR-0028)

`GET /projects/{projectId}/deployment-variants/{documentId}/comparison` requires
`otherDocumentId` (1–128 characters), `revision` (positive safe integer) and optional
`providerId` (default `studio.reference`, at most128 characters). Both documents must be
Deployments of the same uniquely resolved System. Read Project once, enforce the expected
revision and committed-source integrity, validate the complete captured source set through the
selected platform, and resolve both variants with the same source dictionary/provider descriptor.
No installation, inventory, probe, reservation, preflight, run or command is requested.

The response has `comparisonVersion: "1.0"`, `scope: "static_deployment_comparison"`, exact
project/revision/provider identity and provider digest, `sharedSystem` with its document ID,
reference and exact source-byte digest, and `left`/`right` projections. The source-byte witness is
not an XDL semantic digest or a new executable identity. Each side carries its revision-bound
resolution, public declared targets and declared mappings. External asset handles, environment
paths and artifact source references are absent from this comparison projection. Target text
that cannot be projected is counted as unavailable rather than silently claiming complete metadata.

Mapping records retain origin, owner reference and source pointer. Deployment mapping IDs and
qualified clock references come from its canonical source. The selected Scenario schema instead
uses `sourceTimeDomainId`/`targetTimeDomainId` and has no mapping ID: report `mappingId: null`
and `/spec/timeMappings/{index}` without modifying source. Qualified clock identities stay distinct
in static relation checks. Declared mapping text/tolerance is never measured synchronization.

The comparison reports synchronization `unmeasured`, precise latency false, physical state and
cleanup `unknown`, fidelity `unverified`, and runtime admission `preflight_required`. Shared
logical source never establishes behavioural equivalence or physical-provider support. Provider
operations/clocks/native support are descriptor declarations, not permission from target strings.

Advertise/enforce `limits.deploymentComparison`:1,000 bindings, targets and combined mappings per
variant,64 target capability strings and2MiB response bytes. Stop mapping collection at limit+1;
refuse excess rather than returning a misleading partial comparison. Return412 for a stale revision
or external source drift,404 for missing documents/provider,422 for invalid/incompatible selections
or source, and413 for bounds. Existing session/Host/Origin protections apply.

The single-resolution route additionally accepts optional `revision`; supplied values are enforced,
while omitted revision retains latest-read compatibility. Committed-source integrity is always
required. Browser reads supply and validate revision/document/provider context, use one coherent
comparison response, bound display data/pages and suppress obsolete responses without moving focus
away from newer user intent. A malformed or unsupported response remains unavailable.
