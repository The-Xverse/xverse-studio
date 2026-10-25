# Read-only literal scope audit: T025 and T027

Audit after the `expiry-green` 16-check native Linux/Chromium receipt. No tests were rerun,
no source/tests/tracker were changed, and no Windows action was taken. This does not close
milestone acceptance or waive task-specific platform/live clauses.

## T025 — keep open

Literal task: duplicate-Start, two-tab retry, UI-disconnect, event-order, cursor-expiry and
resynchronization tests; changed-payload idempotency conflicts; command.failed versus
acceptance; browser reconnection on both supported native backend/browser combinations.

Verified owned Linux components in this cohort:

- `run-reconnect.spec.ts`: real 16-second owned execution with a 0.01-second timestep continues during a 12-second
  browser-only delivery pause; source records 138 → 1,385; actual HTTP 410 CURSOR_EXPIRED after cursor 145;
  real resync while running with original verified_prefix scope; refreshed readback keeps
  one run. Canonical journal-prefix/snapshot bytes and final journalDigest are checked.
- Unknown recorded-fixture state remains nonterminal; awaited bounded 200-record state/history
  resync and read-only reconnect do not acquire runtime authority or fabricate a loss count.
- `session-contract.spec.ts`: ordered acceptance before cursor acknowledgement, duplicate
  deduplication, proof/context/schema failures, bounded frames, resync awaiting, lifecycle
  versions, partial integrity and resource cleanup. These are inert protocol fixtures.
- Backend sources contain sequential identical-Start replay/changed-payload 409 in
  `tests/contract/test_runtime_lifecycle.py`, principal/route/reopen scope tests in
  `test_idempotency_scope.py`, and restart/expiry/fork/slow-consumer transport cases in
  `tests/integration/test_stream_recovery.py`. This audit inspected them but did not rerun them;
  parent owns exact-candidate backend verification.

Remaining concrete task obligations:

1. No browser test double-clicks Start, or performs the same Start retry from two browser tabs
   after a lost acknowledgement. Existing API replay is sequential and is not this browser case.
2. Active stream cancellation/pause is verified, but actual page close/reopen during an active
   owned run is not explicitly exercised by these tests; the final native refresh occurs after
   the run stops. AC-008's precise close/reopen procedure remains a separate check.
3. `command.failed` appears in the admitted kind registry, but repository search found no
   owned producer/failure-path regression demonstrating an accepted command that later fails.
   A 422 unsupported command or 409 stale-state rejection is not that case. Verify both the
   canonical event and separate operation/lifecycle outcomes in API and browser.
4. Native Windows backend/browser repetition remains NOT_RUN under the user's hold. Do not
   mark T025 fully complete on Linux evidence alone.

An adjacent software gap makes the missing browser cases useful: `App.start` retains its key
only in `startKey` useRef, and stores the run ID only after the Start response and follow-up GET.
A lost response followed by refresh loses the pending request identity in the browser; project
loading selects only a locally stored lastRun. Unlike the existing frozen-rerun pending key,
there is no durable Start receipt/retry view to recover that unknown acknowledgement. Do not
assume a second newly keyed Start represents a retry of the original request.

## T027 — substantial implementation, do not recommend full closure

Present implementation and relevant evidence:

- `PreflightReview.tsx` presents the snapshot-bound compiled plan, independent readiness,
  exact provider bounds, expiry and guarded Start; T020 browser receipts cover those views.
- `ResultsView.tsx` displays current run/snapshot identity, verified frozen-input inspection,
  lifecycle status, and independent execution/verdict/cleanup/evidence cards. Normal owned
  start/finish, immutable readback, and same-stateVersion evidence updates have browser evidence.
- The owned Stop/Cancel API is capability/authority/state checked; buttons exist in Results.
  Backend contract/native recovery tests cover cancellation, but the current browser suite does
  not exercise the Stop/Cancel progress/uncertainty view.

Concrete remaining control-view gaps:

1. Stop/Cancel visibility depends on a hard-coded active-state list, not admitted
   `run.capabilities`; no explicit unavailable-operation reason is displayed. The list also
   differs from backend command states (e.g. ready/paused). This is a UI gap despite backend
   enforcement. Pause/step/reset/restart/live-change support is not implied by absence of buttons.
2. `App.command` discards the accepted operationId and immediately fetches the run. There is no
   control-operation acceptance/delegation/failure/unknown view, and every click generates a
   fresh key. Stop/cancel response loss and retry therefore lack a concrete persisted receipt
   and do not distinguish accepted from successfully executed control requests in the UI.
3. Cleanup has a separate value, but no dedicated unresolved-owned-resource details or
   actionable ownership/reconciliation explanation. A generic unknown card/raw event list is
   not evidence that FR-014's unresolved-resource view is complete.
4. No browser checks presently observe startup/stop/partial-start/cleanup-failure transitions
   and their controls. Normal finish, generic status text and backend tests alone do not verify
   all of the requested control-view behavior. Keep the AC-006/007/027 environment clauses open.

Next ready independent Linux slice after the publication/checkpoint freeze: introduce an
owned control-operation receipt/status view with admitted capability/state gating and explicit
unsupported reasons; preserve pending Start/Stop/Cancel request identity across acknowledgement
loss; add actual two-tab/lost-response and accepted-command-failure browser cases using the
owned provider. Keep startup/cleanup uncertainty explicit. Continue Windows/live acceptance
only when its independent environment/authority prerequisites become available.
