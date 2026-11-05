# ADR-0071 — Keyboard recovery for unavailable diagnostic reads

Date: 2026-11-05. Status: implemented; scoped Linux verification retained.
Traces: T038, T097; NFR-006, NFR-011; existing ADR-0012 explanations.

An initial failed diagnostic read displays an alert without any retry action in
the panel. Recovering requires leaving and reopening that view. A controlled
HTTP503 followed by the actual saved Autoverse diagnosis reproduces the missing
action at both required desktop sizes. Recorded-fact presentation, keyboard event
navigation and selected text contrast pass separately on the original candidate.
The HTTP503 is a labelled transport fixture, not a new observed provider failure.

Add one explicit refresh button alongside the explanation heading. Its label is
Retry explanation while a read is unavailable and Refresh explanation otherwise.
Keep the same button DOM node through loading, failure and success, preserving
current keyboard focus without moving it when the user chooses another control.
Use the existing nonce, abort, coalescing and subject-isolation mechanism: this
repeats only the authenticated read and does not repeat an operation/provider call.
An error remains visible until a successful response; no automatic retry is added.

This applies to the shared readiness/run explanation renderer. No endpoint,
permission, executable input, state vocabulary or diagnostic inference changes.
Canonical facts, uncertainty, receipt/source clock separation and event references
remain authoritative. Browser setup uses a copy of an actual completed Autoverse
recording with no provider installed and the existing optional contributor-only
CPU/device isolation. This adds no application runtime requirement.

Verify failed reads, explicit retry, stable focus, original facts, keyboard evidence
navigation, selected text contrast and unclipped actions at1024x768 and1440x900.
Retain the original counterexamples and repeat the existing recorded playback
suite against the resulting UI. No Windows work, actual assistive-technology,
physical provider, native simulator, full regression or milestone pass is implied.
T038/T097 and the complete M0–M4 acceptance remain open.

Source60afba9 passes six diagnostic checks and the original unchanged22 playback
checks on553 stable Git-bound inputs and six reproduced UI assets. Build/typecheck,
contributor lint, architecture and planning checks pass. Original two missing-retry
failures and the initial six-case cohort remain separate. Evidence and component
review: `evidence/studio/M1-diagnostic-keyboard-20261105/`.
