# Finite campaign workflow — native Linux component evidence

The campaign feature now consumes the existing authoritative preview and retained
history APIs. Users can inspect exact frozen inputs, set run/time budgets and stop
policy, create a finite campaign, inspect immutable child inputs, cancel scheduling
and reopen history after leaving the view. Backend scheduling, durable claims,
permissions, recovery and provider admission remain authoritative.

Fresh full backend **881**, focused browser **42**, full browser **379** and separate
two-viewport performance **2** pass. Browser stages have no skips, flakes or failures.
All **276 selected source/test/build/lock/config/ADR and compiled-UI inputs** match
across and within stages, including six compiled assets. Backend input maps also
remain unchanged through the fresh full run and retained candidate. This advances
T089/T090 and related verification; no M0–M4 milestone or Studio 1.0 is accepted.

## Frozen identity and authority

Existing preview/list/detail responses add campaignVersion 1.0 and verified baseInput
metadata. Both the planner base identity and managed immutable snapshot bytes must
verify before frozen project/revision, System/Deployment/Scenario, provider and snapshot
digest are reported. Unverifiable provenance is unavailable, not a draft fallback;
child states remain readable. The planner base digest includes the snapshot digest
and is deliberately distinct from that snapshot's digest. Stored records stay intact.
List slicing precedes snapshot verification. Private source copies/principal fields
stay outside the public DTO. Actual request/OpenAPI schemas are unchanged.

Authoritative preview allocates no campaign/child. Creation rechecks prior admission.
The browser validates bounded presentation/resource shapes; it does not compile,
plan, grant provider permission or evaluate assertions. Seeds, arbitrary imported
parameters and physical repetition require their own admitted provider contract.

Workspace history has pages of 20 under the existing 128-record retained envelope.
Foreign frozen project/revision identity stays explicit. An existing child inspection
verifies run/snapshot, parent, campaign/child key and actual matrix parameter values.
Current project edits never replace historical inputs. Unknown dispatch can only be
resolved by backend reconciliation; refresh/polling never resubmits a child.

Creation/cancellation have synchronous pending guards. Unchanged in-view retries
reuse their original idempotency key; a separately explicit new request needs a new
preview. The key is not persisted across unmount/reopen; the guide directs users to
retained history after a lost acknowledgement. Reopening never auto-resubmits.
Requests have bounded cancellation/deadlines, context/generation/mount guards and
focus preservation. A newer form cannot alter an already accepted request.

Cancellation acceptance, active cancellation outcomes, observed child state, cleanup
and assertion verdict remain separate. Pending children are cancelled while permitted
active-child cancellation is requested separately. No terminal cleanup is inferred
from an acknowledgement. Foreign-project or unverified-base presentation cannot issue
cancellation; backend principal and provider checks remain in force.

## Actual verification and retained failures

The final focused cohort combines 14 new campaign journeys, 27 Scenario/timeline/
authoring regressions and the existing end-to-end reference workflow. Campaign cases
at 1024x768 and 1440x900 use actual owned preflight, native child execution, immutable
snapshots and backend control. They prove preview without allocation, total-time
budget refusal, exact policy/body, repeated pending submission, child identities and
parameters, retained reopen with zero writes, actual rejected first-child admission
and stop-on-failure policy, pending cancellation with one request, and held real 202
acknowledgements preserving newer drafts/Home/focus and original accepted parameters.
The actual canonical Project remains unchanged by campaign execution/inspection.

A supplemental actual native backend crash/restart probe passes on the same276 selected
inputs. After rejected child admission, it crashes only its owned backend while a second
child is actually running and a third is pending. The worker retains PID/birth identity,
same-principal idempotent creation returns the original campaign, original child keys and
active snapshot stay intact, and only the pending child is newly scheduled. Two distinct
runs/snapshots settle without duplicates or authored Project changes. This is additional
evidence, not part of the881 count. The first probe stopped before crash because coordinator
start acknowledgement did not yet imply actual worker running; its failure stays retained.
The successor explicitly observes preparing→running before crash. This covers known-active
restart after rejected admission. A separate native crash lands after the durable dispatch
claim but before any durable Start receipt or run record. After restart the first child
remains unknown, the second pending, and repeated reads/same-key campaign retry allocate
no run or replay. The operation reports CHILD_OWNERSHIP_UNKNOWN. Both probes preserve all
276 selected input bytes; their private launcher data/credentials are excluded. The dispatch
controller copy was observed after the run, not hashed before it. Neither probe establishes
a crash after delegation, a failed worker, seed/hardware provider support or Windows.

The 21-row history paging and wrong identity/version/unknown-provenance cases are
explicitly labelled transport fixtures derived from one real completed campaign.
They allocate no extra runs and do not establish 21 native campaigns or live provider
support. Unverified extra project fields cannot supply verified provenance. Existing
backend recovery cases include separately labelled durable-state/ownership injection;
browser reload alone is not native backend restart evidence; the supplemental native probe above has its own narrower scope.

Historical reports/maps/logs and exact available source snapshots retain all described
failures. The API baseline failed two missing provenance/version fields. Browser
baselines failed missing history controls after real children completed. The first
successor had two history passes and two Stop policy accessibility failures before
preview; an explicit select name repairs the label. The first deep-input probe passed
two cases without ready UI preflight and did not exercise body serialization. The
corrected ready probe failed both widths by removing authoring for deeply nested JSON;
flat finite numeric array/axis bounds repair it without relaxing backend admission.
Original error-stack data was not attached. The final bounds cases retain authoring,
prevent allocation and permit correction. The first local formatter command stopped
for a missing repo-local CLI before type/build; its cached-tool successor passes.

## Measurements and remaining scope

The separate NFR workload keeps its existing 200 elements/400 flows and 50,000 retained
history records, one warm-up and 30 repetitions. It is not a live campaign scalability
benchmark. Read/acknowledgement deadlines are source-reviewed, not timed native cases.

| Linux viewport | Selection p95 | Open/validation p95 | History p95 |
| --- | --- | --- | --- |
| 1024x768 | 23.8 ms | 1675.9 ms | 445.4 ms |
| 1440x900 | 27.8 ms | 1692.3 ms | 430.6 ms |

Selected input digest: `sha256:992dfffd87556a0b2b136846cf457e8cdeda208544d468ee9fb55bd39a1eeb95`. Run receipts identify the
predecessor HEAD because execution used a development worktree; a subsequent clean
committed source/package binding identifies exact tested bytes. The environment
helper's sourceDigest is tracked-only before commit and omits newly untracked files
and compiled UI; application-and-input-hashes.json is the full selected candidate map.
Actual owned browser/toolchain/environment identity is retained without private argv,
authentication state or launcher data.

An independent T091 probe found a positive comparison compatibility claim for deliberately
altered stored snapshot metadata. After isolated26 and proposed4 checks, the main API now
uses its existing managed snapshot verifier before comparison. Main29 focused checks and
the fresh881 suite pass the repair. Raw failure/isolated controls remain under
follow-on-comparison/. Full comparison/replay scope remains pending; this integrity repair
does not complete T091 or establish a defect-free release. A further labelled contract-fixture
probe has1 healthy control pass and7 failures: absent/different/invalid time-window bounds
and absent observer identity are still accepted. These are open full-T091 regressions,
retained under follow-on-comparison/window-proposal/, not part of the passing881 tests
and not by themselves native-run proof. A separate public API probe with three actual owned
reference runs reproduces the unequal-window claim: equal200000-tick windows are compatible,
but the current comparator also calls the complete300000-tick window compatible. Canonical
journals/snapshots and the authored Project remain unchanged by comparison. An isolated core
proposal passes9 API/fixture cases, retaining the equal-window control and rejecting unequal
windows. It is not applied to this frozen main candidate or part of the881 tracked tests.
Review of that initial proposal found an invalid nonnegative-clock assumption. The corrected
isolated successor preserves signed canonical ticks and large-integer precision and passes12
API/fixture cases. The original source/result and review remain retained. Full comparison/
report work follows this checkpoint.

The earlier full run ended378/1 with a final keyboard Stop state-conflict alert. Its
actual five-second worker completed naturally; no Stop operation was accepted. Original
request timing was not collected, so exact timing is unproven. The fixture now declares
an admitted30-second horizon through the existing parameter form and proves accepted/
completed Stop, not merely a stopped state. A bounded timing attachment and AST proof
preserve all84 original assertion expressions and add12. The first amendment failed
before Stop because an exact label omitted the displayed unit; its selector is corrected.
No application deadline, assertion or performance threshold was relaxed.

T089/T090 and wider verification/release tasks remain partial. The audited count stays
47 completed, 43 in progress and 10 blocked, with zero accepted milestones. Native
Windows remains held; actual AT/human, external/physical/seed-provider and complete
M0–M4 acceptance gates remain open. Root review is not independent milestone review.
No companion repository, device registration/reservation, flashing/stimulation or
cloud publication/deployment is performed.

Clean candidate `86d664716b2467be2ee712b2edaf49b043d81409` passed offline native Linux package provisioning from the prepared cache, startup/UI, Unicode persistence, public compilation and owned shutdown. All 102 manifest/archive/file hashes and six tested UI assets are verified; candidate-binding.json checks 270 committed source/fixed inputs plus six compiled assets. Native Windows remains held.
