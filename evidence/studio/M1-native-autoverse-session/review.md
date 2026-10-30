# Native Autoverse session conformance review — 2026-10-30

T025 completes its original conformance component. Counts become **62 completed,
28 in progress and 10 blocked**; no milestone or complete acceptance case is
promoted. The [clause audit](clause-audit.json) preserves the original task scope,
requirements, paths and dependencies.

The complete actual Autoverse demo passes double-click Start, lost-response retry
from two real tabs, changed-body idempotency conflict, exact duplicate delivery,
reversed delivery of original SSE frames, and closure/reopening of every UI page.
One original native worker and immutable snapshot persist throughout; reopening
issues no Start. Duplicate frames render once; reversed frames require real
resynchronization, with unique, increasing display sequences. Lost Stop receipts
retry with identical keys, bodies and server receipts. Separate durable readback
finds exactly one run, one Start, one Stop and two idempotency records.

Final candidate `022794083415b45a099264e557e64b6f2d7946c0` executes the real default
1,000-record expiry boundary using ordinary native telemetry only. At acknowledged
cursor 59, the browser holds event delivery while the original run continues. Real
HTTP 410 reports missing sequences 60–62, count 3. Recovery retains 200 original
records, discloses 862 presentation omissions and resumes at original watermark
1062. The active reader's `verified_prefix` scope is preserved. Browser connection
recovers before Stop; the final 1,064-record journal is valid and the separately
captured original prefix remains unchanged. No retention limit, input budget,
canonical record, clock or execution authority is changed to obtain this result.

Both selected successful browser/native cohorts retain 453 unchanged inputs and
six tested UI assets throughout their executions. The short double-click cohort
uses predecessor `ebec15d5be08618572e60a335620951eabfd59ea`; final source changes only
the expiry branch in two test files, removing optional driving acceleration and
authoring a supported 1,500-second duration. All application/UI/lock bytes remain
unchanged. Every cohort's inputs match its recorded Git candidate. The final
expiry case repeats the short session assertions as well. Original startup and
runtime command-failure evidence is inherited through unchanged product/UI bytes
and 450 shared prior inputs; those two cases are not presented as new executions.
See [phase history](phase-history.json) and [source witness](source-inputs.json).

The initial uncommitted short pass retains its exact earlier scope. Two expiry
attempts remain failed: one read-only status request raised `ECONNRESET`; another
optional control burst missed its 700ms publication acknowledgement bound. Their
causes remain unestablished. The backend was observed alive after the reset, and
later publication 20 was observed after the second failure. Test polling now
allows at most two connection-reset retries on read-only GETs, without retrying
HTTP errors or mutations. The final expiry check omits driving acceleration;
it does not establish a repair or acceptance of the earlier control timing.
Both failed attempts retain independent valid-journal/prefix and exact cleanup
readback. Raw private request headers are excluded from this public evidence.

Separate readback by the same agent verifies source/Git identities, compiled plans,
snapshot and journal digests, original owners/processes, cursor proofs and cleanup
facts. Across the two selected successful cohorts, 32 recorded component process
instances and two workers exit; two backend/browser-driver instances are absent
and both root locks release. Each native driver verifies three exact stopped
containers before a later test reuses them. Final readback verifies the final
start identities and explicitly qualifies earlier container reuse. Six original
operator UI assets and 21 original platform evidence files remain unchanged.
The operator is not restarted.

Architecture, compatibility, specification, Ruff and diff checks pass. The native
Ubuntu22.04.5 x86_64 / Chromium156 / Playwright1.64.1 lane is recorded precisely.
Node colour and Playwright slow-file notices are informational. This is a component
self-review with separate readback, not independent milestone acceptance. There
is no fresh package, whole-platform, Pygame, standalone Lite, physical, second-industry,
performance or human acceptance claim. Source clocks remain unmapped and functional
verdicts remain null. The T011 reference exception is not extended. Continue T033
and the remaining original M0–M4 scope; M5 remains deferred.
