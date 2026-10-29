# Run control receipts and command outcomes — Linux owned reference

Scope: T025/T027 software components and the CI-reported expiry flake. No task, milestone or
Windows/live-provider acceptance is claimed. `verification.json` identifies the exact source digest.

## Changes

- **History reads during active runs.** Fresh-host push CI for `fb8ddb6` failed the native expiry
  browser check: `totalRecords` dropped by 126 because one secure acquisition raced a journal append
  and returned an empty `unavailable` projection (`../native-ci/ubuntu-24.04-fb8ddb65-runs.json`).
  The reader now re-acquires at most four times before reporting `unavailable`; the hash chain and
  declared digest still decide integrity. The test counts only `verified_prefix` projections.
- **Accepted-command failure producer.** An owner-signed stop/cancel that the reference workload never
  applied (run finished first, or the workload failed) records `command.failed` in the canonical
  journal and a `failed` operation with its code. A delegated command whose worker reached a terminal
  state without applying it is reconciled to `failed` (`RUN_TERMINAL_BEFORE_COMMAND`, operation record
  only; the sealed journal is not rewritten). Lost ownership makes it `unknown`, not `failed`.
  Delegation is serialized with reconciliation so it cannot reopen a settled outcome.
- **Durable browser receipts.** Start and Stop/Cancel persist their idempotency key and payload before
  sending. A lost acknowledgement, refresh, page close/reopen or second tab retries the same request;
  a fresh-identity Start is refused while a receipt is unresolved.
- **Control views.** Stop/Cancel appear only when the run admits them, and are disabled with a stated
  reason when state or a pending control forbids them. Operation views distinguish sending,
  unacknowledged, accepted, delegated, completed, rejected, failed and unknown. Unknown ownership or
  unresolved cleanup shows an explicit view that never targets processes by name, PID or port.

## Verification

See `verification.json`: 499 backend tests; typecheck/build; 44/44 browser checks with performance
measurements (one earlier performance-mode failure is retained and was repaired); red/green proof for
each new regression; independent review with all nine findings repaired (`independent-review.md`).

## Remaining obligations

- T025: repetition on both supported native backend/browser combinations (Windows held).
- T026: depends on T025; Linux full browser/expiry successor now passes.
- T027: AC-006/007/027 environment clauses, live partial-start and cleanup-failure transitions, and
  optional controls from an admitted provider. Browser failed/unknown operation views use a
  presentation-only operation fixture; producers are proven at the API.
