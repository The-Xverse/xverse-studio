# Autoverse journal-opening review — 2026-10-30

Candidate `6847b974e8f71aadc614bb69562373597ea86ae4` fixes the actual native worker's
missing startup report when exclusive journal creation fails. **T033 remains in
progress; counts stay 62 completed / 28 in progress / 10 blocked, with zero accepted
milestones.** This is an Autoverse integration supplement to the original fixture
matrix, not a replacement for that matrix or resolution of its late-Stop mismatch.

Both original native reproductions accepted Start with 202, then exposed unknown
lifecycle and cleanup because the worker exited without a report. The worker now
closes its unused selector and publishes an original owner-bound failure before
any runtime acquisition. It reuses `EVIDENCE_OPEN_FAILED`, so the existing shared
startup/diagnosis views explain journal creation and storage recovery. No shared
industry branch or new public operation is introduced. Existing journal objects
are preserved; no replacement writer, canonical failure event or executed/effective
input identity is invented. Failed report publication still propagates and leaves
ownership/cleanup unknown. Existing worker functions other than initialization
and the classic entry point are semantically unchanged.

Four final native/Chromium cases pass on the same 456 committed source inputs and
six unchanged tested UI assets:

- An existing directory refuses journal creation. The original report records
  failed startup, complete cleanup, unavailable native evidence and no workload
  start. The API retains the separate invalid-reader verdict.
- An existing regular file refuses creation without changing its bytes. Original
  Start retry returns the same receipt; the browser displays the startup rejection,
  storage recovery guidance and separate invalid Evidence card.
- Obstructing report publication as well keeps Start, lifecycle and cleanup unknown.
  The browser displays unresolved startup/ownership, with no automatic run mutation.
- A complete nominal Autoverse demo reaches Android boot/APK and observed telemetry,
  then passes double-click/two-tab receipt recovery, duplicate/reordered original
  event delivery, all-page close/reopen, exact Stop retry and native cleanup.

Separate same-agent readback verifies exact source/Git identities, original requests,
snapshots, authoritative compiled plans, ledger counts, preserved journal objects,
owner identities, native exits and root locks. The negative runs acquire no workload
resources. The nominal run releases 16 recorded component instances and three exact
container/configuration/start identities; its 65-record journal is valid. Four
original worker/backend/browser-driver instances are absent and four root locks
release. All six original operator UI assets and 21 original platform evidence files
remain unchanged. The operator is not restarted.

The [phase history](phase-history.json) preserves both original failures and test
corrections. The first post-fix inspector incorrectly expected private process
fields in a public API body; it now reads the protected native ledger. The first
browser expectation confused terminal retained-history availability with integrity;
the final test checks the distinct availability label and invalid Evidence card.
Neither correction changes product assertions to manufacture execution success.
Uncommitted early source inputs are retained as exact private archives verified
against their original hashes; final cases bind committed source.

This is a component self-review with separate readback, not an independent milestone
review. No new package, full suite, default-window expiry repeat, whole-platform,
Pygame, standalone Lite, physical, second-industry, performance or human acceptance
is claimed. The T011 reference exception stays limited to T011. Continue the full
original M0–M4 scope and retain T033's outstanding fixture/fault obligations.
