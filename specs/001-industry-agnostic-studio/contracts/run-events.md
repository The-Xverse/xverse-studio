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

## Owned evidence query 1.0 implementation

Capabilities advertise `contracts.evidenceQuery: "1.0"` separately from HTTP major v1. Both
`GET /runs/{runId}/history` and `/observations` accept exact `elementRef`, `sourceProviderId`,
`observerRef`, `clockDomain`, `startTick`, `endTick`, `recordedFrom`, `recordedUntil`, `cursor`, and
`limit` (1–200, default 200). History additionally accepts `type` and `severity`; observations accept
`field`. Unknown and duplicate selectors reject instead of being ignored. IDs are at most 512
characters; ticks use `^-?(?:0|[1-9][0-9]*)$` with a 32-character bound. Source and receipt intervals
are half-open and cannot be combined. UTC bounds require an explicit timezone and at most six
fractional digits. Unsupported calendar/encoding values reject rather than normalize silently.

The response keeps `items`, original `integrity` and `nextCursor`, and adds `projectionVersion`,
`effectiveFilter`, `evidenceScope`, `counts` (total/candidate/matched/returned/omitted records),
`quality`, bounded whole-run `facets`, `facetsComplete`, and per-event `presentation` metadata.
`quality` distinguishes missing/malformed source time, another clock, missing receipt time and an
unsupported receipt encoding. The presentation's normalized UTC receipt is derived; raw history
events and observation `recordedAt`/`sourceTime` retain original values. Known numeric reference-v1
receipt seconds never pass through a millisecond magnitude heuristic. Invalid/unknown encodings
remain unavailable. Top-level `mapping` is null without admitted mapping evidence; reported source
resolutions are not inferred unit conversions.

Observation field selection returns only that value field, with source/units preserved; full original
event payloads remain inspectable through history. Missing source ticks are null, not zero. Gaps retain
their original identities/reasons regardless of display filtering, with `gapCount` and `gapsComplete`
for bounded enumeration. This does not establish canonical collection coverage. New cursors reject
another route/run/filter context; old numeric history cursors are restricted to the legacy selectors.
See ADR-0010 for the reader acquisition, precision, compatibility and native-platform boundary,
and the negotiated transport recovery contract below for retention-expiry/resynchronization.

The owned v1 stream uses unique event IDs and canonical nonnegative decimal-string sequences
(`0|[1-9][0-9]*`, at most 32 characters; actual first sequence is `1`). Malformed digest/identity/sequence
proof invalidates the read; missing digest proof retains verified-prefix status. This clarification
does not rewrite existing canonical events or introduce a new external runtime admission.

## Owned presentation transport 1.1

The current application selects `GET /runs/{runId}/events?streamVersion=1.1&after={cursor}`.
Default `streamVersion=1.0` retains the legacy run-prefixed/integer read-position compatibility.
Unknown or duplicate selectors reject. Query `after` and `Last-Event-ID` must agree. Cursors are
bounded to 2,048 characters. Version 1.1 uses opaque `st1.` proof-bound run/snapshot/sequence/digest
positions. A legacy position under 1.1 requires 410 `STREAM_RESYNC_REQUIRED`, because an index cannot
establish historical source continuity. Canonical data envelopes and their original digests stay 1.0.

Capabilities advertise `contracts.events: "1.1"` and `limits.eventStream`: replay window 1,000,
pending canonical frames 200, pending encoded bytes 1,048,576 including a 4,096-byte control reserve,
maximum frame bytes 262,144, global subscribers 16 and per-run subscribers four. A reserved extra
control slot reports presentation gaps. Quota refusal is retryable 429 `STREAM_SUBSCRIBER_LIMIT`.
Legacy delivery preserves consecutive prefixes under byte pressure; an oversized next legacy frame
rejects 413 `STREAM_FRAME_TOO_LARGE` before headers, with recovery/history routes.

Before headers, an expired proof-bound position returns 410 `CURSOR_EXPIRED`, exact missing range/
count, `earliestAvailableCursor`, `resumeAfterCursor` (the boundary before the first retained event),
and `stateUrl`, `historyUrl`, `resyncUrl`, `evidenceUrl`. `earliestCursor` aliases that resume boundary.
Source discontinuity returns 410 `STREAM_RESYNC_REQUIRED` with null unknown loss counts. Unavailable
acquisition is retryable 503 `STREAM_SOURCE_UNAVAILABLE`; invalid original proof is 422
`EVIDENCE_INVALID`. Unsupported canonical kinds reject 422 `STREAM_ENVELOPE_UNSUPPORTED`, without
changing the original cryptographic verdict or retained bytes.

After headers, notices use `event: studio.stream_control`, no `id`, and a JSON object containing
`streamVersion: "1.1"`, `type` (`stream.gap|stream.resync_required|stream.error|stream.end`),
`runId`, `snapshotId`, `reason`, nullable `firstMissingSequence`, `lastMissingSequence`, `missingCount`,
and the retrieval routes. A gap includes its exact contiguous range/count and proof-bound
`resumeAfterCursor`; an error retains the original error code as reason. Slow-consumer/byte/oversized
presentation omissions never delete canonical evidence or manufacture `observation.gap` records.
Terminal end is emitted only after reading stopped/failed source state through its final watermark.
Unknown lifecycle remains pollable/reconnectable.

`GET /runs/{runId}/resync` accepts no query selectors. Its response is
`{streamVersion, runId, snapshotId, run, history, resumeCursor, watermark, stateUrl, historyUrl,
resyncUrl, evidenceUrl}`. `history` contains at most 200 original items within the encoded byte/frame
bounds, `nextCursor: null`, original `integrity`, total `omittedRecords`, and
`oversizedOrBudgetOmissions`; its retrieval route exposes paged retained history. `watermark` binds
the current canonical sequence/digest even when the display tail is bounded. The response is
unfiltered recovery state, never a replacement for canonical evidence or a filtered evidence cursor.
Missing terminal proof may retain `verified_prefix` and is displayed as such; invalid/unavailable
sources cannot be upgraded by recovery. No recovery operation issues Start or another mutation.
The 1,048,576-byte recovery budget applies to the complete encoded UTF-8 response, including
`run`, the history tail and envelope. Metadata is accounted before selecting records. If metadata
alone exceeds the response budget, 413 `STREAM_RECOVERY_TOO_LARGE` returns current-state and paged
history routes; no successful recovery watermark is acknowledged by the browser.

The browser acknowledges only accepted envelopes, awaits state/history recovery before reconnect,
and retains unknown omission counts as unknown. Transport disposal releases its bounded resources
without stopping backend execution. See ADR-0011 for exact scope, compatibility and verification.

## Verification obligations

Exercise duplicate delivery, reconnect, expired cursors, backend recovery, out-of-order raw provider records, state-version checks, slow consumer gaps, canonical collection gaps, mixed clocks, unavailable source timestamps, private-log exclusion, corrupted evidence, and mapping between a selected event and its exact model revision.
### Ordered run observations (ADR-0022 amendment)

Full run metadata may include a nonnegative safe-integer `observationVersion`.
This is a durable backend projection order, independent of the worker-owned
`stateVersion` used for command CAS. Reconciliation increments it only when an
already changed run projection needs persistence; unchanged reads and legacy
records do not acquire extra writes merely to initialize it.

For the same run/snapshot and worker version, a newer complete observation
replaces the previous projection, including absent optional reasons. Older
observations cannot overwrite newer truth. Worker lifecycle regression guards
remain authoritative; legacy responses retain conservative behavior. This
additive metadata field changes no canonical journal sequence, cursor, source
clock, executable identity or command authority.
