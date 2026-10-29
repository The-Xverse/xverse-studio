# Independent review — control receipts and command outcomes (2026-10-25)

A separate read-only reviewer inspected the pre-review working-tree diff (reader re-acquisition,
worker/backend command outcomes, durable browser receipts and the new tests) against the API/event
contracts, FR-012/013/014/016, T025/T027 and `../M1-session/literal-scope.md`. It ran no tests.
The pre-review candidate's 498 backend / 44 browser results are superseded by the repaired candidate.

## Confirmed findings and disposition

| # | Severity | Finding | Disposition |
|---|---|---|---|
| 1 | High | After a lost Start acknowledgement, Recheck rotated the Start key; a later Start overwrote the receipt and could admit a second run. | Repaired: a Start with a fresh identity is refused and disabled (stated reason) while an unresolved receipt exists. Browser regression covers Recheck-after-loss. |
| 2 | Medium-high | Delegation ran outside the store lock; a concurrent reconcile could settle the operation and delegation then overwrote it with `delegated` forever. | Repaired: delegation is serialized with reconciliation and only moves `accepted` → `delegated` while the run still names this pending command. Red/green contract regression. |
| 3 | Medium | `onRunUpdated` was an inline arrow; each streamed render restarted the operation-poll timer. | Repaired: stable callback in App and a ref inside RunControls. |
| 4 | Medium | 401/403 on a retry cleared the receipt, though session/origin refusal precedes the idempotency record. | Repaired: 401/403 keep the receipt unacknowledged. Principal scope is the constant `local-operator`, so new sessions keep idempotency scope. |
| 5 | Low | Ownership view claimed process identity was "not recorded"; the API deliberately withholds it. | Repaired: states that the backend holds it and the browser is not given it. |
| 6 | Low | Start receipt was cleared before the run pointer was stored. | Repaired: run pointer persisted first. |
| 7 | Low | A malformed command file in the worker error path could skip the failed-state save. | Repaired: state is saved before the separately guarded `command.failed` attempt. |
| 8 | Low | A response settling after a run switch could attach to the displayed run. | Repaired: receipts update only their own run's display state. |
| 9 | Low | Stored receipts were weakly validated; IDs went into URLs unencoded. | Repaired: kind/status/types validated; path IDs encoded. |

## Residual concerns retained

- Journal re-acquisition happens inside run reconciliation while the store lock is held. It is
  bounded to four attempts, but a large continuously appended journal can still hold the lock for
  several reads and may honestly report `unavailable`.
- Pending Start has no live cross-tab storage listener; another tab sees the receipt on project load.
  Retry from any tab reuses the same identity.
- Operations already left `delegated` by earlier candidates carry no `pendingCommandId` and are not
  retroactively reconciled.
- Double-click Start is proven by one request identity and one backend run; the disabled button may
  absorb the second click, so this case alone does not prove concurrent backend deduplication (the
  lost-acknowledgement two-tab case does deliver three identical requests).
- Browser `failed`/`unknown` operation views use a presentation-only operation fixture; the actual
  producers are proven by the API contract tests.
