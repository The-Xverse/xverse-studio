# ADR-0077 — Keep session metadata waits off the HTTP event loop

Date: 2026-11-05. Status: affected component verified; full live repeat pending.
Traces: T096; NFR-005/008; AC-010/011/030. Windows remains frozen.

The complete pressure repeat onb444243 again expires the driver lease, despite an
independent heartbeat. The0.492-second completed Stop fromcf0ea89 is a qualified
observation, not proof of a reliable full fix. Retain every original outcome.

The async HTTP security boundary calls synchronous Store.get for every session.
That lookup waits for the shared metadata lock and SQLite on the event-loop thread.
A deterministic source-backed counterexample holds the metadata lock, starts an
authenticated request and observes that even an unrelated static404 request cannot
complete until the lock is released. This remains possible after ADR-0076 moves
presentation derivation outside the lock. Offline current provider/snapshot
admission and lifecycle profiles are0.014/0.0014 seconds with profiler overhead;
they do not alone explain the live request delays.

Await the same session lookup through Starlette's existing AnyIO worker-pool
helper. The existing worker capacity limiter applies; no independent executor,
unbounded application work queue, session cache or stale authorization shortcut
is introduced. The lookup still runs once for every protected request. Host,
Origin, contract version, current session expiry and CSRF validation retain their
ordering and semantics. Expiry is evaluated after the awaited read, before
dispatch. Metadata exceptions retain the same refusal behavior. SQLite connections
are created and closed in the worker executing the existing Store method.

This change prevents a contended session lookup from freezing the entire HTTP
event loop. It does not remove metadata serialization, promise a live latency
bound, lengthen input leases or prove complete backpressure acceptance. Verify the
retained synchronization failure, affected source-backed observation/input/stream
guards and actual enrolled-descriptor authentication refusals without runtime
dispatch. Repeat the full rendered/sensor/Android Stop and Cancel pressure cases
and declared finite measurements before any T096 closure claim.

Component results: the expanded contact-forbidden cohort retains193 passes,
one fixture-path assertion failure and22 setup errors. The fixture used a path
without a suffix, which correctly returns the built SPA fallback200. A missing
`.txt` asset establishes the intended404; the event-loop regression then passes
independently. All193 earlier passing cases use identical application bytes;
the correction changes only that test path. The22 setup errors request a platform
entry absent from this current classic-only installation receipt. Do not fabricate
an enrollment or infer a platform pass; the22 actual classic bootstrap/session/
CSRF/Origin/host/expiry refusal cases in this run pass. No native subprocess contact
is attempted, and the original expanded failure remains retained. Together these
results cover194 applicable current component cases; no full216-pass or live claim.
