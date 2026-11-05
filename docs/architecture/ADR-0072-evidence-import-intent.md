# ADR-0072 — Evidence import respects current navigation and selection

Date: 2026-11-05. Status: implemented; scoped Linux verification pending.
Traces: T038, T097; NFR-006, NFR-011; inert exchange contract unchanged.

Actual evidence-import replies can arrive after leaving Home for Catalog or
explicitly reopening Home. The original handler opens its inspection dialog
unconditionally, stealing the newer view/focus. Actual malformed-archive failures
likewise add an obsolete error to Catalog. When two imports overlap, the older
reply can open its dialog and clear the newer operation's busy indication.
Controlled delays of actual201/422 replies reproduce these outcomes at both sizes.

Capture the existing project/navigation intent and an import-selection sequence
before reading the chosen file. Refuse to start an abandoned upload after file
reading; after a request is sent, show its response/error only if its initiating
intent and latest selection remain current. A late accepted bundle stays retained
by the backend. There is no cancellation/deletion/reimport or new execution right.

Bind the shared busy label to the latest action sequence, so an older completion
cannot clear a newer pending action. Preserve all action return values and existing
error handling; this sequence guard changes only clearing the busy indicator.
Import-specific stale errors are suppressed by the import's own context guard.

The browser checks use existing actual Autoverse bundles on a disposable target
copy with no live integration registered. Normal valid/damaged inspection and
malformed-archive refusal are distinct from delayed actual transport controls.
The first selected legacy1.0 archive lacks profile metadata: its four profile-row
failures are fixture-selection limits, separate from eight reproduced UI context
failures. The current prepared1.1 archive passes those four normal keyboard cases
on the unchanged product. Do not add absent metadata to the legacy bundle.

The overlapping-request test's initial busy=0 expectation encoded the observed
bug while the newer reply was still held. Strengthen that expectation to busy=1,
retaining the no-obsolete-dialog assertion and waiting for the actual first reply
body plus a browser frame. Final whole-suite execution requires12 accepted inert
imports and unchanged run/operation/evaluation/snapshot/campaign/preflight/key counts.
The existing inspection suite retains its original4-import expectation/assertions.

No Windows, provider/device, simulator, assistive-technology, full-regression,
performance, package or milestone acceptance is implied. T038/T097 remain open.
