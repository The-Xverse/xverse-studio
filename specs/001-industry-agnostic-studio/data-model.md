# Data Model: Studio projections and durable records

**Status**: planned contract, version 1.0. All examples describe intended Studio metadata, not new XDL syntax.

## Ownership and identities

The existing platform owns XDL `Component`, `System`, `Deployment`, `Scenario`, and `Profile` semantics. Studio stores a project envelope, presentation metadata and operational records around those resources. It must not serialize browser node objects as an alternative system definition.

| Entity | Identity and important fields | Owner / invariants |
|---|---|---|
| Project | opaque `projectId`, display name, revision, declared resource files, profile lock, artifact references | Studio; project ID never substitutes for an XDL resource identifier. |
| ProjectRevision | `projectId` + monotonically increasing revision, file digests, semantic digest when available, author/action/time | Immutable after commit. Writes use expected revision. Invalid drafts may be saved but never run. |
| XdlResourceRef | `apiVersion`, `kind`, namespace, name, version | XDL authority; resolution uses included resources and admitted schemas. |
| ElementRef | resource reference + element ID | Stable semantic reference; display rename/layout change does not allocate a new logical entity. |
| GraphProjection | revision + projected nodes/edges and source-map references | Derived/cacheable. Node/edge IDs carry XDL refs; no independent executable configuration. |
| LayoutDocument | schema version, resource scope, node positions, collapsed groups, viewport, annotations that affect presentation only | Studio sidecar; excluded from semantic plan hashing. Dangling refs are reported and repairable. |
| ProfileLockEntry | namespace, schema version, schema digest, presentation-package digest, provenance | Project input; multiple namespaces permitted; conflicts reject composition. |
| ProviderDescriptor | provider ID/version, interface version, implementation digest, realization classes, operations, limits, time/evidence capabilities | Runtime registry; capabilities are discoverable facts or unknown, not frontend guesses. |
| PhysicalAsset | asset ID, provider binding, observed identity, firmware identity or unknown, endpoint credential reference, reservation state | Environment inventory; endpoint and credentials are not logical Device identity. |
| Reservation | reservation ID, asset ID, owner/run association, lease/fencing token, expiry, status | Provider authority; possession of an old token does not confer control. |
| ValidationReport | input revision/digest, validator identity, diagnostics, unresolved namespaces | Derived; static validity is separate from target readiness. |
| CompiledPlan | immutable plan bytes/digest, compiler identity, input identities and limitations | Platform-generated; Studio may inspect, not edit the derived plan. |
| Preflight | preflight ID, snapshot digest, provider-capability digest, resource reservations, readiness facts, expiry, status | Backend admission record; start rechecks freshness and ownership. |
| RunSnapshot | snapshot ID/digest, frozen authored inputs, compiled plan, deployment/scenario selection, artifact/profile/provider identities, seed, clocks, observers and limits | Immutable; secret values excluded. Unavailable required immutable identities block admission. |
| Run | run ID, snapshot ID, authority reference, state version, lifecycle/cleanup/evidence/evaluation statuses, created/updated timestamps | Backend projection of provider/Argus facts; no browser ownership. |
| CommandRecord | idempotency key, canonical payload digest, scope, operation ID, state/result, provider correlation | Durable before delegation; exact replay returns the existing operation; conflicting reuse rejects. |
| ProbeOperation (ADR-0027) | operation ID, principal, exact asset/provider/binding identity, observe-only scope, declared resource refs, backend deadline, state and closed observation result | Studio metadata outside XDL; original request is durable before contact, duplicate keys never re-probe, restart retains unknown, source clock and receipt time remain separate; no lease, readiness or runtime authority. |
| EventEnvelope | event ID, run ID, stream sequence, type, timestamps/domain, source/element refs, evidence class, payload | Append-only UI stream; canonical evidence refs retained; replay can deliver duplicates. |
| EvidenceRef | run ID, original evidence identity/digest, reader/version, integrity verdict, availability, clock metadata | Read-only canonical evidence; derived index may be rebuilt. |
| Evaluation | evaluator ID/version/digest, metric definition, input evidence refs, value/unit, verdict, missing-data/uncertainty policy | Separate from lifecycle success. Never evaluate opaque XDL strings implicitly. |
| Campaign | campaign ID, frozen base snapshot, bounded parameter matrix, concurrency limit, stop policy, child run IDs | M4 local coordination; each child run has independent identity and evidence. |

## Logical dimensions

Role (`controller`, `sensor`, `actuator`, `gateway`, `service`, `observer`, process role) describes purpose. Realization describes model/software/emulated/physical implementation. Placement selects an execution target or asset. They are separate properties connected by validated deployment bindings. A profile may specialize role names; it may not change the meaning of the three dimensions.

Relationship types are disjoint:

- Communication: XDL endpoints/interfaces/flows with declared transport binding.
- Model coupling: declared provider-specific model relationship with compatible physical/numerical semantics; unavailable provider prevents execution.
- Deployment: logical element to target/artifact/resource/asset.
- Traceability: model or experiment to requirement/evidence; a link is not a passing verdict.

## State machines

### Project authoring

`draft → validated → compiled` are derived states of a particular revision. A new semantic edit creates a new draft and invalidates reports/preflights tied to prior inputs. A layout-only edit does not invalidate semantic compilation, though it creates a presentation revision. Unsupported profiles preserve source bytes and report unresolved; they cannot reach executable readiness.

### Run lifecycle projection

`requested → preparing → ready → running → stopping → stopped` is the normal path. Provider failures can enter `failed`; cancellation enters `stopping` and records its reason. `paused` is legal only with declared capability and a provider observation. `reconciling` is an explicit temporary state after service recovery; unresolved authority becomes `unknown`, not `stopped`.

Provider states are mapped through a versioned adapter. The projection must retain the raw provider state and reason; it must not invent evidence that the upstream lifecycle does not supply.

Independent result dimensions remain visible:

| Dimension | Values |
|---|---|
| Lifecycle | requested, preparing, ready, running, paused, stopping, stopped, failed, reconciling, unknown |
| Cleanup | not_started, in_progress, complete, failed, unknown |
| Evidence | pending, collecting, complete, partial, invalid, unavailable |
| Evaluation execution | not_started, running, complete, unavailable, error |
| Assertion / aggregate verdict | pass, fail, indeterminate; null when not evaluated |

A terminal lifecycle state does not imply cleanup or evidence completion. A pass verdict does not erase missing evidence outside the evaluation's scope. Run-list summaries must expose unresolved dimensions rather than collapse them into a green success badge.

### Command lifecycle

`accepted → delegated → completed|rejected|failed|unknown`. Persist acceptance and idempotency mapping before contacting a provider. A crash between delegation and acknowledgment is reconciled with the provider using the stable operation ID. Do not treat retrying HTTP as permission to start another run.

## Integrity, transactions and retention

- Save all files in a semantic edit transaction or none; use staged writes and atomic manifest revision change. Detect external file changes before commit.
- SQLite stores metadata, command intent/results, stream cursors and evidence indexes. It is not a replacement for Maestro/Argus journals.
- Preserve original authored bytes in run snapshots, alongside canonical plan and digests. Source formatting and semantic identity are different notions.
- Credentials are references resolved by the backend/provider; snapshots and exports contain no secret values or authentication tokens.
- Delete/export operations resolve explicit project/run IDs within configured roots. Symlinks, traversal and archive escapes are rejected before materialization.
- Active run inputs and required evidence are never purged by automatic retention. Data loss, corrupted indexes and unavailable evidence are diagnosed explicitly.
- Time values retain source clock/domain, mapping ID, uncertainty and ordering sequence. Unsynchronized domains remain distinguishable in charts and metrics.
