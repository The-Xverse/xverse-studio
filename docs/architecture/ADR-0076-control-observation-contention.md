# ADR-0076 — Derive presentation outside the lifecycle metadata lock

Date: 2026-11-05. Status: source-backed component verified; full live verification pending.
Traces: T096; NFR-008; AC-010/011/030. Windows remains frozen.

Two actual complete Autoverse pressure attempts fail with driver lease expiry.
ADR-0075 reduces repeated large-source decoding but does not resolve the failure.
Offline profiles of copied actual sources show cold journal and assertion admission
work taking seconds. Normal observation holds the shared metadata lock throughout
that work. Driver input and lifecycle commands also request those derived fields
before enforcing their own existing authority checks. Presentation can therefore
block a control request without supplying a control authorization prerequisite.

Keep report acquisition, original process/task ownership, command reconciliation,
state validation, provider/snapshot/capability enforcement and durable mutation
under the existing metadata serialization rules. An internal lifecycle-only read
serves input, commands and native shutdown. It does not inspect evidence or derive
assessment presentation. This is not exposed as a user-selectable API bypass.
Evidence quality cannot grant control authority and cannot prevent an otherwise
authorized owned Stop/Cancel. Driver leases, fencing, rate and sequence limits,
signed mailboxes and the original renderer/sensor workload remain unchanged.

For ordinary presentation reads, capture the exact stored row and reconciled local
observation under the metadata lock. Release that lock before bounded canonical
journal acquisition and assessment derivation. Reacquire it before publication;
publish the complete observation only if the stored row is still byte-equivalent
under canonical serialization to the captured row. Any newer observation version,
pending command or other row mutation forces a fresh read. After four conflicting
attempts, return the existing RUN_OBSERVATION_UNAVAILABLE error with retryable=true
and HTTP503. Never overwrite a newer observation or invent a fresh version for a
result that was not saved. Unchanged reads remain write-free; a changed observation
is still saved once, and persistence failures remain failures.

Journal identity/digest validation and assessment admission are unchanged. A
normal read still performs both. This change does not confer provider authority,
remove corrupt/stale report refusals or make terminal sources accept input. It
does not claim that every caller holding an outer metadata transaction can be
preempted; retain that limitation in review and verify the actual public pressure
paths. No lock is forcibly released, and no unbounded retry or background queue
is added.

Verification must retain deterministic stalled-journal/assessment counterexamples,
concurrent newer-row publication guards, unchanged-write/corruption/order semantics,
actual provider/input/ownership refusals, bounded conflict exhaustion and the
original live failures. Repeat the full actual Stop/Cancel pressure and declared
finite performance workloads before claiming T096 acceptance. Source-backed
terminal copies and explicit verification callbacks do not establish live latency.

Current component checks: five original synchronization/refusal cases fail on the
predecessor. Eleven final copied-source cases plus six existing input-surface
contract cases pass. The first expanded attempt records two test-instrumentation
failures from counting Store.put's wrapper and its recursive SQL call twice;
counting actual SQL writes retains the original one-write assertions. The affected
159-case stream/reader/corruption/input/cache cohort passes with native subprocess
contact forbidden and source bytes unchanged. No original pressure failure is
reclassified. Live harness diagnostics retain at most128 recent input frame and
following observation request durations/statuses, with no lease tokens or payloads.

The first full repeat on06aadb3 still fails and is retained. Its first two pressure
input responses succeed in0.066/0.046 seconds, but the following presentation GETs
take0.528/0.604 seconds. The third input receives lease expiry after0.556 seconds.
The contributor's serial frame/GET/sleep loop therefore does not maintain an
independent driver heartbeat. This does not establish a complete product fix or
justify any longer lease. Prepare a separate HTTP client while the lease is
released, then use an independent brake-frame thread during the same six-second
pressure/observation/prefix checks. Every failed heartbeat remains fatal; never
silently reacquire or relax authority. Join that thread before the planned command
and in finally cleanup. Retain its bounded timings/errors and original frame/GET
failure. The complete live Stop/Cancel and finite repeats remain required.

The independent-heartbeat repeat oncf0ea89 reaches completed Stop,0.492-second
acknowledgment,31.368-second terminal cleanup, advancing canonical counts60/65/67,
no heartbeat errors and verified16-resource/3-container release. The whole verifier
still fails: it incorrectly expects expectedStateVersion on the public Stop
operation. That operation has never promised this field; its accepted request is
bound in the durable idempotency fingerprint. Preserve the failed whole result.

Verify the exact request digest (including expectedStateVersion), route/key and
accepted result in retained read-only metadata, the public operation's run/kind/
ID/completed state, and the original owner-digest-bound HMAC mailbox and producer
completion for that ID. This uses the existing contract; no production field or
provider endpoint is added. Twelve source-backed checks pass, including eleven
changed request/operation/fingerprint/mailbox/key/producer refusals. Repeat the
whole cases to verify the remaining frozen-byte and ledger assertions, rather
than reclassifying the old failure as a full pass.

Later uninstrumented repeats still show intermittent lease expiry, including after
the event-loop repair; one completed Stop is insufficient to claim reliability.
An explicit contributor-host --trace-input-timing option now measures HTTP,
lifecycle, provider admission/input and owner/mailbox atomic-write durations in a
256-sample memory ring, written only at application shutdown. It delegates every
original operation and records no payload, lease/session token, path or exception
message. The existing valid-target host alone can select it; it cannot be combined
with fault injection or enabled by imported project data. Its ASGI refusal/privacy/
restoration check passes. These instrumented runs are diagnostic and require an
uninstrumented repeat before acceptance; no production debug API is added.
