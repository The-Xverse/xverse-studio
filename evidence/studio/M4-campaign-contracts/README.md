# T089 campaign contracts — partial progress

Candidate `89c973bdedcbd6f5f3671676479826b8b0d4a7f2` passes 46 focused contract checks
with zero failures, errors or skips on 504 unchanged Git-matching inputs. The tests
use the actual complete-demo Autoverse snapshot, an independent SQLite store and
an authenticated in-process API. They launch no workload.

Four original failures exposed oversized-integer conversion errors in matrix,
duration and total-time budget validation, plus an unhashable stop policy. The
planner now returns its declared campaign errors. The original 36-pass/4-fail
cohort and overlapping 46-pass successors remain distinct in [attempts](attempts.json).
The final pass is not a sum of predecessor results.

The checks establish stable bounded expansion, exact child keys, frozen-base
preservation, pre-expansion limits, strict concurrency types, occupied unknown/
running slots, rollback before delegation, durable SQLite dispatch intent,
same-identity acknowledgement, cancellation and failure-policy semantics. These
are coordination contracts. Explicit seed axes are inert data; the actual provider
continues to report uncontrolled external randomness with no applied seed.

Both campaign endpoints refuse an actual originally ready Autoverse snapshot before
mutable readiness, worker dispatch or campaign/run/operation/idempotency allocation.
The existing owned-reference restriction remains. These refusals establish no
positive campaign capability. Original recording, journal and database hashes stay
unchanged; existing snapshots and original environment resources are preserved.

The [coverage audit](coverage.json) leaves T089 in progress. Fresh actual child
snapshots, admitted parameter/seed mappings, resource reservations and native
crash/cancellation reconciliation remain incomplete for the current Autoverse target.
T090 and AC-028 remain open. Counts stay 67 completed / 23 in progress / 10 blocked,
with zero accepted milestones.

Only the campaign planner and one new test differ among the 504 inputs from the
last complete demo: 502 prior inputs are unchanged. The preceding live demo belongs
to `dfe5f09`; no new native runtime, browser, whole regression, performance, package,
Windows, physical or independent milestone acceptance is claimed. The latest
supplied AGENTS requires Windows verification, which remains unverified.

See [verification](verification.json), [review](review.md), the exact
[source hashes](source-inputs.json) and ADR-0058. Native environment reuse remains
available under the separately retained private owner/installation receipts.
