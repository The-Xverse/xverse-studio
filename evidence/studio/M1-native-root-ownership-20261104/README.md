# Native workspace ownership: selected checks pass, browser verification interrupted

Candidate `412083230b996a4bf9e5799762e8c063746e8c95` acquires workspace ownership
through the original held directory and regular single-link lock file. Existing
lock bytes are never written or truncated. Contention, unavailable native
primitives and unsafe acquisition stay distinct. The launcher retains a prepared
root and checks the interrupted-restore marker after taking ownership; recovery
passes its existing source/destination anchors directly. See
[ADR-0068](../../../docs/architecture/ADR-0068-native-workspace-ownership.md).

Linux requires current-user root/lock ownership, uses nonblocking exclusive
`flock`, rechecks the acquired file against its name and tightens root permissions
only after winning. Windows uses private owner ACLs, held ancestor handles and
native immediate byte locking without a preparatory write. The Windows ownership
implementation is a candidate: **actual Windows execution is NOT_RUN**.

[Verification](verification.json) records 140 passing selected Linux checks with
zero failures, errors or skips. They cover ownership, original recovery/migration
cases, portable Windows path/ABI rules and 11 checks using the original completed
Autoverse recording and explicitly labelled decoded-copy inputs. The executable
reference migration case is deselected under the current Autoverse scope. No model,
provider, simulator or physical workload is started by this cohort. Owned helper
processes test real lock contention. These are selected results, not a full
regression or a native Windows pass.

The original 12 Windows test/helper functions are unchanged; five native ownership
cases extend the suite to 16 actual native cases. They cover second-process
contention, unchanged existing bytes, held ancestor names, hardlinks/junctions,
unchanged inherited root ACLs and original owned-process termination/release.
Linux collection proves none of those Windows behaviors. The original 14 assertions
from the first Linux counterexample cohort remain present.

The separate ordinary-launcher browser run reuses a copy of the actual T088
recording, without installing its provider or starting a workload. Backend
readiness and login complete, and the Home UI loads, but browser interaction fails
waiting for the Home button to become stable. **Zero browser cases pass: 11 fail
and 11 are skipped after interruption.** The original driver is interrupted after
repeated failures; this is not a passing browser cohort. Original-handle cleanup
verifies backend/driver exit, root-lock release, unchanged canonical source/copy
bytes and unchanged run/operation/evaluation/idempotency counts.

The user reports a frozen PC display and failure to reach a text login console.
Read-only kernel observations show repeated NVIDIA GPU progress timeouts, including
before this latest browser cohort. A cause for the graphics stall or the browser
failures is not established. All current verification processes exit. Further
graphical verification is stopped while display recovery is unresolved. No desktop,
graphics driver, GPU reset or reboot is performed by the agent. These observations
do not establish an application regression fix, a successful recovery or acceptance.

All 549 selected code/tool/config inputs match committed Git and remain unchanged
through the recorded stages; six UI assets remain identical to the earlier verified
build. No new build is claimed. Architecture, planning-package, descriptive-baseline
and the recorded lint/name checks pass. Existing task definitions, statuses,
dependencies, requirement/acceptance mappings and milestone states are unchanged;
only T002/T039 progress notes/evidence links change. The [audit](audit.json)
records those distinctions.

[Attempts](attempts.json) retain the initial 6-failure/4-pass counterexamples,
the exit-error and launcher failures, the private-root failure and intermediate
passing cohorts. A permission-ordering mistake is caught by the refused-contender
case: the 81-case intermediate has 80 passes and one failure. Moving permission
hardening after successful acquisition yields 17 ownership passes and the final
140-case selected pass. An initial private-driver Node/cache path precondition
fails after the completed selected/static checks, before browser startup. Its path
is corrected and the completed prefix is retained without repeating those checks.
This is distinct from the subsequent real browser failures. Exact commands and
qualifications are in [commands.json](commands.json); raw XML, full intermediate
patches, process identities and browser artifacts remain private.

Same-agent component review checks acquisition identity, shared-write scope for
Windows contenders, absence of pre-lock writes, error mapping at entry/exit,
caller-exception preservation, permission ordering and anchored recovery callers.
It does not supply an independent milestone review. Windows recovery inventory
and SQLite handling, worker process ownership, native provisioning and complete
installed/browser/persistence/crash acceptance remain open. No package, performance,
whole-regression or full milestone pass follows from this component.

**71 completed / 19 in progress / 10 blocked; zero accepted milestones.**
T002/T039 remain in progress. No additional task closes.
