# ADR-0078 — Observe an already requested container Stop within its existing budget

Date: 2026-11-05. Status: component verified; full live repeats pending.
Traces: T096; FR-012/013/014; NFR-008/009; AC-010/030. Windows remains frozen.

After the session event-loop repair, a full actual Stop pressure case passes. The
equivalent Cancel case preserves its heartbeat but ends with cleanup unknown:
the owned score container's Stop CLI times out and one immediate inspection still
reports Running=true. A later separate read observes all three exact original
containers stopped, including the same start identity. The original cancellation,
unknown producer receipt and canonical journal remain unchanged and failed.

Studio already permits50 seconds per ordinary container and70 for Android,
further limited by any shorter caller deadline. A20-second Stop CLI timeout
currently causes immediate unknown after one read, although the daemon may still
be finishing that single accepted Stop and resource budget remains. A missing CLI
acknowledgment does not settle the daemon outcome. Increasing timeout budgets or
replaying Stop against a possibly replaced start is not justified.

After a Stop was actually attempted, if readback still reports the same original
container running, inspect it again every0.25 seconds within the unchanged
resource/caller deadline, with at most280 additional observations. Every inspection
rechecks complete container identity, exact StartedAt and strict Running type.
Changed identity/start, unavailable observation or exhausted budget remains unknown.
Never replay Stop, force-kill a container or extend a deadline. Preserve original
command timeout/failure diagnostics even when a later verified release succeeds.
An initially stopped target that reappears remains unknown immediately; it gains
no new mutation or polling authority from this change.

The retained source-backed timing reproduction uses the actual container identity
and controlled in-memory observation sequences. No Docker mutation is executed:
five intended release/replacement/deadline cases fail on the predecessor and two
existing refusal/deadline cases pass. Verify the successor and current actual
stopped-target inspection negatives, then repeat complete actual Stop/Cancel under
the same presentation pressure. This changes the provider implementation digest;
the existing rerun contract permits current implementation changes only through
fresh full preflight/Start with unchanged installation and frozen source semantics.
Do not rewrite original snapshots, installation receipts or failed cleanup evidence.

Successor checks pass: all seven source-backed timing/identity cases, all twelve
existing actual stopped-target inspection/refusal cases with Docker mutations
forbidden, and the combined201-case affected reader/input/contention/receipt/
cleanup/classic-authentication cohort with native subprocess contact forbidden.
That combined run preserves selected source inputs and records zero native contact
attempts. These component results do not upgrade the earlier failed Cancel or
establish live release timing on the changed provider.
