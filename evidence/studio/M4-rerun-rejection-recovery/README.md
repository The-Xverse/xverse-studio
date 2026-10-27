# Recover after a verified rerun rejection

Two native browser cases filled the four-run owned-reference capacity, received
RESOURCE_BUSY, stopped all four through accepted owned commands and explicitly
requested another rerun. The browser kept returning the original rejected operation
with the same key. It could not obtain fresh admission after capacity became free.
Original protected snapshots and journals stayed intact. The original red remains
retained; this was a recovery defect, not an admission or ownership failure.

The browser now settles only a verified terminal rejection: the existing operation,
source run, parent/new snapshot identities must match; scope must be owned-reference;
there must be no child run/result; and the structured rejection error must declare
the original operation non-retryable. Only that request's own stored key is cleared.
A later explicit Rerun frozen inputs action can request fresh backend admission.
Reading rejection never starts a workload or rewrites the rejected operation.

A different stored key survives an older rejection, and the message explains that
the next action checks the retained request. Failed, unknown, incomplete,
contradictory or foreign-scope replies retain their key. Lost acknowledgements also
keep their key. A valid retry identifies the existing child without duplication.
The fifteen-second acknowledgement budget and backend authority remain unchanged.

Fresh main verification passes 69 affected native browser checks and two separate
performance checks. All 294 source/test/config/lock/ADR/guide/compiled inputs match
within and across both stages. The 69 consist of 18 new rejection cases, 31 existing
snapshot-inspection cases, 16 prior rerun cases and four annotation/evidence/shared
Model-inspector/whole-Studio workflows. The previous 18 comparison cases belong to
the earlier candidate; they are not claimed as freshly executed in this cohort.
Typecheck/build, architecture, compatibility and structural spec checks pass.

The 18 new cases also passed separately before promotion. Six use actual native
capacity refusal/release, normal/reopened views and real requests from a second
browser tab at both required widths. A settled old receipt preserves the second
tab's newer key; inspecting its refusal settles that request before fresh admission.
Fresh admission requires another explicit click and yields exactly one child with
the original 0.2-second inputs despite a newer 30-second draft. Canonical original
bytes stay unchanged. The separate first two-case successor also remains retained.

Twelve labelled transport cases follow one actual owned child and substitute
failed/unknown or rejected receipts with a child, absent error, retryable flag or
foreign scope. Repeated requests retain the same key and exactly one child. Removing
the fixture lets a valid retry select that existing child. These fixtures neither
rewrite protected files nor establish actual provider failures or physical admission.

Backend/runtime/Python-test sources are unchanged. The local 932 backend result is
inherited through 217 unchanged of 218 selected inputs and an ADR-only amendment.
The completed 7dd8 Ubuntu24 push/PR jobs also passed 932 backend tests, full 413 browser
checks and package smoke. Current full 462 is collected, NOT_RUN locally. This 69
is not a full 462 pass. The previous b38/4c inspection successor's 69 had a different
explicitly retained cohort, plus separate performance and clean package evidence.

This implementation-agent review is not independent milestone acceptance. Native
Windows remains held; actual AT/human/novice work, external/physical providers,
normative SADS and complete task dependencies retain their gates. Counts remain
47 completed, 43 in progress and 10 blocked; no milestone is accepted.
Clean committed successor package verification is pending.

Performance retains the existing 200-element/400-flow and 50,000-record workloads,
one warm-up and 30 repetitions; this does not establish live campaign scalability.

| Viewport | Selection p95 | Open/validation p95 | History p95 |
| --- | --- | --- | --- |
| 1024x768 | 28.0 ms | 1657.5 ms | 446.3 ms |
| 1440x900 | 28.4 ms | 1647.4 ms | 446.1 ms |

Selected candidate digest: `sha256:b5d33e37d00907fad70cd93525c7ad3097a47ffec3a71360fcc70db2d0320d3c`. Environment sourceDigest is tracked-only before commit; the 294-input map includes new files and compiled assets.
