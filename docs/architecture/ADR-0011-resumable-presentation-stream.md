# ADR-0011: Proof-bound presentation delivery and read-only recovery

Status: implemented owned transport under successor verification; no milestone acceptance claim.

FR-013/FR-021 require browser reconnection without transferring lifecycle ownership to the browser.
An integer delivery index alone cannot prove continuity after backend recovery, and a slow browser
must not silently lose presentation samples. The HTTP major remains v1; capabilities advertise
`contracts.events: "1.1"` independently of the unchanged canonical envelope `schemaVersion: "1.0"`.

The Studio application explicitly selects `streamVersion=1.1`. Its `st1.` opaque cursor binds the
run, immutable snapshot, canonical sequence and original record digest. The before-first-record
position uses sequence zero and the zero digest. The decoder rejects duplicate/unknown fields,
noncanonical encoding, invalid types and another run/snapshot. A valid cursor is a read position,
never authority to execute. Reacquisition verifies its original prefix proof before advancing.
Missing or changed proof requires recovery, rather than substituting the current source digest.
Legacy integer or run-prefixed positions remain available under the default compatibility version
1.0; selecting 1.1 with such a position requires explicit state/history recovery.

The 1.1 presentation replay window contains 1,000 canonical records. An expired acknowledged
position returns HTTP 410 `CURSOR_EXPIRED` before headers, with the exact omitted range/count,
earliest available position, resume-after boundary and retrieval routes. An unprovable old source
returns 410 `STREAM_RESYNC_REQUIRED` with unknown loss counts. Unavailable acquisition returns
retryable 503; invalid original evidence returns 422. Unknown event kinds are refused separately
from cryptographic integrity, using the contract's closed registry before interpolating SSE fields.

`GET /api/v1/runs/{runId}/resync` is a read-only, unfiltered current-state/history acquisition. It
returns the immutable context, original reader verdict, bounded history tail, explicit omitted-record
counts, current watermark/proof cursor and retrieval routes. It neither issues commands nor edits
snapshots, journals or evidence status. Running `verified_prefix` evidence is usable with its limited
integrity label; invalid/unavailable evidence does not become a successful recovery.
The 1 MiB recovery limit applies to the entire UTF-8 JSON response, including current run metadata,
history, watermarks and retrieval routes. Metadata is charged before selecting the display tail;
omission counts and the original source watermark remain exact. Metadata alone beyond that bound
returns 413 `STREAM_RECOVERY_TOO_LARGE` with state/history routes. The browser stops automatic
recovery and exposes the presentation-limit refusal rather than acknowledging a replacement cursor.

Each subscriber holds at most 200 pending canonical frames and 1 MiB of encoded pending data/control
budget, with a 4 KiB control reserve and maximum data frame size 256 KiB. One extra reserved control
slot reports a contiguous omitted presentation range. The service allows at most 16 subscriptions
globally and four per run, rejecting excess admission with retryable 429. These limits describe the
owned local service, not external provider throughput. Oversized 1.1 records remain in canonical
history and produce a presentation gap with retrieval routes. Legacy 1.0 delivers a bounded prefix
without dropping earlier events; its next oversized record returns typed 413 before SSE headers.
An oversized record first encountered during a legacy open stream closes that connection after
delivering the preceding prefix; reconnect at that position returns the same typed refusal.

Transport notices use `event: studio.stream_control`, have no SSE id, and identify their own
`streamVersion: "1.1"`. They never create canonical event sequence numbers or digests. Explicit
gap/resync/error/end controls remain separate from original `observation.gap` collection evidence.
Collection gaps remain visible to evaluation; a presentation gap alone does not rewrite coverage.
The source reader's 64 MiB/100,000-record bounds continue to apply independently.

Response and iterator cleanup both release subscription leases, including cancellation before the
iterator is entered. Closing a browser releases only presentation resources. Unknown lifecycle
remains reconnectable; terminal transport closure requires the actual stopped/failed source state.
Backend run ownership, command idempotency and provider process identity remain unchanged.

The browser acknowledges a cursor only after its consumer accepts the envelope. It verifies context,
order and proof continuity, deduplicates a bounded tail, awaits recovery before reconnecting, and
cancels readers/timers/listeners on context change. Independent lifecycle versions and evidence/
cleanup facets are merged separately so equal lifecycle versions cannot hide fresh evidence facts.
Read generations prevent obsolete run responses from retargeting the active view.
The parser reserves one transport-control slot independently of its 200 canonical-frame limit, so
network coalescing cannot turn an allowed batch into an unknown gap. Early dialog keyboard listeners
are installed during layout, before an asynchronously mounted preflight can receive Escape. Existing
native keyboard and focus-restoration expectations remain verification obligations.

Compatibility and verification: XDL, compiled plans, assertion v1, original journals and executed
inputs retain their existing identities. New transport/recovery schemas are additive and explicitly
negotiated. Findings, original failures, deterministic producer/private-log fixtures, native running
recovery and independent successors are retained in `evidence/studio/M1-event-stream/` and
`evidence/studio/M1-session/`. Fixture results do not establish external Argus/private-runtime/device
admission. Native Windows installation/testing remains held; its secure I/O implementation remains
unavailable. Full T025 dual-platform verification and M0–M4 acceptance remain separate obligations.
