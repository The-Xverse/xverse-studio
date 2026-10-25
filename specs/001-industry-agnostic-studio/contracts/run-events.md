# Run event and evidence projection contract v1

**Status**: planned transport/presentation contract. Canonical lifecycle and observation evidence remains with its originating runtime/Argus records.

## Event envelope

Each event has:

| Field | Meaning |
|---|---|
| `schemaVersion` | `1.0`; unknown incompatible envelopes trigger resync/error rather than silent reinterpretation. |
| `eventId` | Stable unique envelope identity for client deduplication. |
| `runId`, `snapshotId` | Immutable run context. |
| `sequence` | Monotonic server stream sequence within the run; decimal integer encoded safely across languages. |
| `type` | Closed registered event kind. |
| `recordedAt` | Backend receipt/record time; not substituted for simulation/device event time. |
| `sourceTime` | Optional original tick/timestamp, clock domain, resolution and mapping/uncertainty reference. |
| `source` | Provider/runtime/observer identity and raw source record reference. |
| `elementRefs` | Zero or more stable XDL resource/element references. |
| `evidenceClass` | `observed`, `derived`, `inferred`, or `unknown`. |
| `payload` | Type-specific schema, bounded and redacted. |
| `evidenceRefs` | Original record/artifact identities and integrity scope where available. |

`sequence` orders delivery; it does not prove physical causality across clocks. Stream generation after a backend restart retains monotonic continuity or emits an explicit discontinuity and resync requirement.

## Event kinds

- `command.accepted`, `command.delegated`, `command.completed`, `command.rejected`, `command.failed`, `command.unknown`.
- `run.state_changed`, `run.reconciling`, `run.ownership_unknown`.
- `element.state_changed`, `readiness.observed`, `connection.observed`.
- `log.appended`, `observation.available`, `observation.gap`.
- `fault.activation_requested`, `fault.activation_observed`, `fault.recovery_observed`.
- `cleanup.updated`, `evidence.updated`, `evaluation.updated`.
- `stream.gap`, `stream.resync_required`, `capabilities.changed`.

Requested fault activation is not evidence that a fault occurred. A connection event must identify whether it describes declared configuration, resolved routing or observed traffic. No traffic is `unobserved` unless the expectation/time window establishes a failure.

## SSE delivery and reconnect

`GET /api/v1/runs/{runId}/events?after={cursor}` returns `text/event-stream`. SSE `id` is an opaque resumable cursor; `event` is the registered event kind; `data` contains the envelope. The client may also use `Last-Event-ID`; if both are supplied they must agree or the request rejects. Heartbeats carry no semantic events and do not advance simulation time.

Delivery is at-least-once. Clients deduplicate by eventId and apply state updates only when state versions advance. Reconnect resumes after the acknowledged cursor; it must never issue another start request. When the cursor has expired, return `410 CURSOR_EXPIRED` with the earliest retained cursor and state/evidence resync URLs. The client obtains current run state and paged history before resuming.

The backend bounds subscriber buffers. A slow browser may lose presentation samples with an explicit `stream.gap` range/count and retrieval route; required canonical evidence is not silently discarded. If canonical collection itself loses data, emit `observation.gap`, retain the loss reason and propagate incompleteness into evaluation.

## Observations and logs

Observation queries select an observer, bounded time interval and clock-domain interpretation. Results include unit/schema, original clock/domain, mapping identity/uncertainty, coverage/gaps, reduction method and evidence integrity. Display decimation must preserve discontinuity markers and expose its method. Metrics read admitted canonical data rather than decimated graph points.

Log records carry severity, source, source timestamp where present, receive time, correlation/run IDs and element refs when known. Redaction occurs before exposing protected fields. Arbitrary stderr availability is provider-specific; do not promise or collect a private stream that the upstream contract excludes.

## Evidence and evaluation

Evidence status is independently `pending|collecting|complete|partial|invalid|unavailable`. Original reader integrity verdicts are retained. An index rebuild cannot upgrade a partial or invalid original evidence set. Export identifies source digests, reader version, limits and selection.

Evaluation events carry evaluator identity, metric definition, evidence input references, value/unit and separate `status` (`not_started|running|complete|unavailable|error`) and `verdict` (`pass|fail|indeterminate` or null). Run completion does not create a passing evaluation. See [experiment-evaluation.md](experiment-evaluation.md).

## Tests

Exercise duplicate delivery, reconnect, expired cursors, backend recovery, out-of-order raw provider records, state-version checks, slow consumer gaps, canonical collection gaps, mixed clocks, unavailable source timestamps, private-log exclusion, corrupted evidence, and mapping between a selected event and its exact model revision.
