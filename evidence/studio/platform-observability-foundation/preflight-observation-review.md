# Preflight active-count finding, before repair

Actual live-follow retry was blocked RESOURCE_BUSY after the original task had
finished and written its verified stopped/complete report. Its cached Studio run
still said running because that browser closed before a final GET. Reading the
original public run reconciled the terminal observation and the next preflight
succeeded. No original claim, provider state or evidence was reset.

The new actual-owned-child/API test reproduces this on source d6377c9: it waits on
the original backend task after a signed cancellation, performs no terminal GET,
and proves preflight is incorrectly blocked. Red result:1failed with RESOURCE_BUSY;
retained at .studio-local/linux-reassessment/preflight-red.xml/log.

Source review: Start already calls the existing identity/ownership/evidence-aware
read for every cached active run before its idempotent transaction. Preflight
instead counts cached states directly. Reuse the same reconciliation helper before
preflight's aggregate count, without changing the reader, Start ordering, transaction
boundaries or dispatch semantics. Unknown ownership stays in ACTIVE and continues
to consume capacity; no PID/name/port absence may establish release.

Verify the positive actual-owned-child regression together with existing unknown
capacity, lifecycle, original-owner and unchanged-read persistence cases. Linux
scope removal does not waive these ownership requirements.
