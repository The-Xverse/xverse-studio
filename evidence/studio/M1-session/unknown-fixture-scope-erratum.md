# Scope erratum: initial unknown-state recorded fixture

Some earlier M1-session verification prose described the unknown recorded fixture's first
resynchronization as HTTP 410. That was an overstatement: the browser test asserted the actual
resync request, bounded tail and unknown lifecycle behavior, but did not assert that initial
HTTP status. Raw reports and journals are retained unchanged.

With no initial cursor, EventStreams.prepare does not perform the acknowledged-cursor expiry
check. The bounded initial delivery instead uses a noncanonical SSE stream.gap with the known
N-minus-200 presentation count. That known range must not be relabelled as unknown because of
client frame/chunk handling. The separate inert unknown-loss protocol fixture remains useful
for genuinely unspecified counts.

Use expiry-green/verification.json, nativeReceipts.actual-window-expiry, for genuine HTTP 410
proof: the actual owned 16-second run with a 0.01-second timestep produced CURSOR_EXPIRED after acknowledged cursor 145,
then resynchronized while running with original verified_prefix integrity at watermark 1,398.
Its original journal prefix/snapshot bytes and final sealed digest were verified. This stronger
native case is independent of the unknown recorded fixture and its earlier prose correction.
