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
