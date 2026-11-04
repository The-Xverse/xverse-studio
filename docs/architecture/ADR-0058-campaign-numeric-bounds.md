# ADR-0058 — Campaign validation rejects unrepresentable numeric inputs

Date: 2026-11-04. Status: implemented; scoped contract checks verified.

The finite campaign planner previously called `math.isfinite` directly on JSON
integers. Python admits integers too large for that conversion, so matrix values,
duration and total-time budgets could raise `OverflowError` instead of their
specified campaign errors. An unhashable stop policy could similarly escape as
`TypeError` at the pure planner boundary.

Use one private finite-number predicate that excludes booleans, nonnumbers,
nonfinite values and overflowing integer conversions. Preserve the existing
`INVALID_PARAMETER`, `INVALID_DURATION` and `CAMPAIGN_BUDGET` codes. Check stop
policy type before set membership and preserve `INVALID_STOP_POLICY`. Ordinary
finite values, exact integer child limits, stable Cartesian ordering, child keys,
base snapshots and the state machine retain their semantics. The HTTP body already
uses strict types; the new schema counterexamples verify that concurrency is not
coerced from booleans, floats or strings.

The T089 contract suite anchors decoded-copy planner/state checks to an actual
complete Autoverse snapshot. Explicit seed axes are inert planner data; the actual
provider records `external_uncontrolled_no_applied_seed`. Independent SQLite
metadata reopen verifies durable dispatch intent, ambiguous-start blocking and
stable acknowledgement identity. It is a metadata recovery check, not a native
backend crash or worker execution. Abstract parallel slots establish no reservation
or permission for physical equipment.

Both authenticated campaign routes still refuse the actual originally ready
Autoverse snapshot before mutable readiness, worker dispatch, campaign/run/operation
allocation or idempotency recording. The owned-reference campaign restriction is
preserved. No provider runtime, seed mechanism, resource permission, dependency,
shared industry dispatch, historical snapshot or canonical journal is changed.

Four original failures are retained; the final 46 contract checks pass on unchanged
inputs. T089 remains in progress: exact live child snapshots, admitted provider
parameter/seed mappings, reservations and native crash/cancellation reconciliation
still require evidence. T090 and AC-028 remain open. See
`evidence/studio/M4-campaign-contracts/`. The latest supplied AGENTS requires Windows
verification; these Linux contract checks do not establish it.
