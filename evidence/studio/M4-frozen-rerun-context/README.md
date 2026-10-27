# Frozen rerun acknowledgement and presentation context

An actual owned rerun's delayed HTTP acknowledgement previously selected its child
and returned to Results after the user had deliberately selected Model. Both native
desktop widths reproduced the defect. The source experiment completed normally;
this was a browser presentation defect, separate from execution ownership.

The browser now selects the verified child only while the originating Results
instance, run/snapshot, result tab and focus remain current, with no newer dialog.
Normal completion still selects the admitted child. A newer view, annotation draft,
focus or selected run survives late completion. The backend continues to own runs.

The existing fifteen-second acknowledgement budget now bounds the POST, operation
reads and child read. Aborting a browser read does not cancel backend execution.
Synchronous submission guards prevent repeated pending delivery. Explicit retry
keeps the source run's stored idempotency key, and a completed receipt clears only
its own key. Operation, source run, parent/new snapshot, child/start-operation,
project and owned-reference scope must match before the child can be selected.
Mismatched or uncertain responses keep their request identity for retry.

Fresh main verification passes37 affected browser checks and separate performance2,
with289 source/test/config/lock/ADR/guide/compiled inputs identical across/within both
stages. The37 include16 new cases at1024x768/1440x900,18 comparison cases, the existing
annotation and late evidence-filter workflows, and the entire original studio flow.
No existing assertions were removed. Actual lost HTTP acknowledgements and labelled
operation/child DTO faults retry the same key and retain exactly one admitted child.
The DTO fixtures change transport fields only, not snapshots or canonical journals.

The previous fresh932 backend result is inherited:217 of its218 selected inputs
remain identical, and the sole difference is the non-executable ADR0021 amendment.
Backend/runtime/Python-test sources are unchanged; fresh collection remains932.
The two new browser files do not enter pytest. This is not a newly executed full
backend suite. The previous full397 belongs to comparison candidate9a0f189. Current
full browser collection is413; no413 pass is inferred from the focused37 proof.

The original native red, isolated source proposal, TypeScript inference failure,
invalid pre-build browser attempt, corrected2/16/37 isolated successors and exact
sources remain at ../M4-recorded-comparison/follow-on-rerun/. The invalid attempt
failed before the product workflow and was already terminal when inspected; no
process was signalled. That historical proposal is now promoted to main, followed
by fresh main37/performance2 verification. Backend authority and XDL semantics do
not change. No new provider, physical operation or deterministic replay is admitted.

The implementation agent's review is not independent milestone acceptance. The
read deadline and protection of a different tab's newer stored key have source
review, without separate timed/cross-tab acceptance cases. Native Windows, actual
AT/human/novice work, broader providers and complete task dependencies remain open.
T091 stays in progress; counts47 completed/43 in progress/10 blocked, zero milestones.

Performance retains the existing200-element/400-flow and50000-record workloads,
one warm-up and30 repetitions. It does not prove live rerun/campaign scalability.

| Viewport | Selection p95 | Open/validation p95 | History p95 |
| --- | --- | --- | --- |
| 1024x768 | 28.0 ms | 1659.5 ms | 447.0 ms |
| 1440x900 | 27.4 ms | 1644.9 ms | 446.1 ms |

Selected candidate digest: `sha256:614fe52d94b32609b74a98e5308522fc564a51a6c5c5998159957e927abc096b`. Environment sourceDigest is tracked-only before commit; the289-input map includes new files and compiled assets. Clean committed successor package verification is retained below.

Clean candidate `24050875d8b0169f4d4e384a32776425bc7e577d` passed offline native Linux package provisioning from the prepared cache, startup/UI, Unicode persistence, public compilation and owned shutdown. All 104 manifest/archive/file hashes and six tested UI assets are verified; candidate-binding.json checks 283 committed source/fixed inputs plus six compiled assets. Native Windows remains held.
