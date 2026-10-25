# Legacy delivery review and repair

STREAM-R01 (high): the bounded batch removed its earliest data frames under byte pressure for both
transport versions, while only 1.1 had an explicit gap control. A terminal five-record disposable
canonical journal with 800-character messages, 8 KiB pending budget and 2 KiB frame limit delivered
only sequences 4 and 5 to legacy 1.0. The underlying journal remained unchanged. This violates
consecutive compatibility delivery even though canonical collection itself lost nothing.

STREAM-R02 (medium): a legacy next record beyond the frame limit passed `prepare`, committed HTTP
200 SSE headers and then closed with no data. Retrying the same acknowledged position repeated
the empty response rather than receiving an actionable typed refusal.

Original direct receipt: `legacy-before.json`. Permanent regression receipt before product repair:
`legacy-before-tests/verification.json` (two failed, one passed). The original failures are retained.

The shared data-frame encoder now checks the next legacy frame during preparation, before headers.
It returns 413 `STREAM_FRAME_TOO_LARGE` with history/recovery routes. A legacy batch retains a bounded
consecutive prefix, breaking before its byte budget is exceeded. A later oversized frame cannot
discard an already queued prefix; after that prefix, reconnect returns the typed refusal. Negotiated
1.1 retains its explicit bounded-tail gap policy. Neither repair edits canonical events.

The direct successor `legacy-successor.json` delivers all five records in order, rejects the oversized
next record with typed 413, and records identical original journal hashes. Permanent affected/full
stream successor results and independent review are recorded separately; this document alone does
not establish full-candidate acceptance or native Windows support.
