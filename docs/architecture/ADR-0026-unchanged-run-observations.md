# ADR-0026 — Persist changed run observations without rewriting identical records

Status: implemented; successor verification and milestone acceptance remain open.
Date: 2026-10-28.

## Context

Run/history reads reconcile the actual owned worker observation, command outcomes,
journal integrity and assessment summary. A private copy of an actual browser
test dataset showed421 SQLite record writes for200 already stable terminal run
reads. Every write stored the existing value; all returned run bodies and managed
run files stayed unchanged. These repeated writes occupy the shared metadata lock
and storage without recording a new fact. The separate original trace-claims
browser failure's request scheduling was not captured; this measurement does not
establish that failure's exact cause.

## Decision

Keep the existing per-store lock and perform the full observation/reconciliation
path on every read. Compare a run's final canonical JSON with the value read at
entry and persist only when it differs. Compare each observed start/command
operation before and after applying its recorded result in the same way. An
already unknown operation does not need another identical unknown write.

Use the existing canonical JSON representation, rather than Python value equality,
so changes in JSON type or numeric representation are not silently collapsed.
This is write suppression, not an observation cache. Ownership/PID/birth checks,
late terminal-state handling, pending-command reconciliation, journal verification
and assessment computation remain in their original order and remain authoritative.
New lifecycle, cleanup, ownership-loss, evidence-quality or assessment facts still
require the original durable writes. A failed changed-state write still fails the
read; it cannot report a new durable state as successfully recorded.

No endpoint, schema, executable input, permit, provider loading, lifecycle command,
worker implementation or physical capability changes. Metadata reads may still
write when they discover new information. Windows and external-provider support
retain their independent verification requirements. Stable reads do not establish
physical cleanup or safety.

## Verification

Use actual short owned reference workers and an acknowledged cancel to verify that
repeated single-run/history reads preserve complete responses and managed files
without SQL record writes. Controlled late worker metadata and journal corruption
must still be detected and persisted once, then stabilize without another write.
An injected failure while persisting a changed observation must propagate.
Rerun existing lifecycle/identity/history/command tests, the current backend suite,
affected browser flows and performance checks against the successor source.

Retain the200-read baseline, four failing regressions and the original passing
changed-write failure control. Re-measure the same private derived dataset after
repair and record response/file equivalence. Full milestone and original browser
failure closure require their own evidence; no test timeout or threshold changes.
