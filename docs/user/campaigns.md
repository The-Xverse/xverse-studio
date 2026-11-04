# Finite campaigns

Open **Experiments → Campaigns**. Obtain a ready preflight for the current revision
with **Preflight & run**, then return to the draft. This does not start a run.

Enter numeric parameter arrays, maximum runs, maximum total declared seconds,
concurrency and stop policy. **Preview campaign** asks the backend for exact frozen
input identities, cardinality and the time estimate without creating a campaign.
**Create campaign** rechecks admission and allocates a retained campaign. Each child
receives its own immutable snapshot. An unchanged retry uses the same request key;
use **New campaign request**, then preview, to intentionally allocate another one.

Only admitted parameter/provider combinations execute. Seed axes and physical
repetition require separate admission. Preview does not promise every child will
pass runtime admission or produce a successful assertion verdict.

**Refresh campaign history** reads workspace history in pages of 20. Open a retained
record to inspect its frozen project, revision, snapshot and child identities.
**Inspect child inputs** verifies an existing run's protected snapshot against that
campaign. Current drafts do not replace historical inputs. Unverifiable provenance
is marked unavailable; unknown dispatch requires backend reconciliation.

A child's displayed scheduling state describes campaign coordination. A `running`
child has an accepted start and can still be preparing at the runtime. Use the
recorded run's status in Results for observed execution state. Input verification
establishes identity; it does not establish process liveness.

Closing the browser does not stop scheduling. **Stop scheduling** cancels pending
children and separately asks the backend to cancel active children where admitted.
An acknowledgement does not prove termination or cleanup. Read the observed child
states and any cancellation outcomes. Refreshing never replays or restarts a child.

If submission cannot be confirmed, refresh history before starting another request.
While this form is mounted, retrying the unchanged request uses the original key.
After reopening, inspect retained history rather than assuming that a lost response
means nothing was created. Provider evidence is scoped separately. The verified classic Autoverse duration
campaign does not establish physical-device or native Windows execution.

**Stop on failure** cancels children that have not started after a child fails or
is rejected. **Continue** considers the remaining children under current admission
checks. Neither policy turns a failed run into a successful result.

A **complete** campaign means coordination has ended. Read each child's execution,
cleanup, evidence and assertion status separately in Results. A failed worker can
leave unknown cleanup and partial, prefix-verified evidence; those observations
remain distinct from a complete journal or a passing assertion.

## Classic Autoverse duration campaigns

Classic provider 0.4.0 admits integer `durationSeconds` from 30 through 1800, with
one child at a time. Obtain a new ready preflight: older snapshots keep their
original capabilities. The form shows the admitted range and **Use admitted
parameter example** fills a one-value matrix without starting anything. For example:

```json
{"durationSeconds": [30, 31]}
```

A two-run budget of 62 declared seconds covers that matrix's conservative time
estimate. For this provider, duration is elapsed host time after the complete
runtime reaches running; component preparation, Android boot and cleanup add wall time.
The owned reference provider's declared duration remains simulated time. A time
budget is not a promise that external startup will finish within that interval.

Each Autoverse child rechecks full source, profile, connection, deployment and
installation admission. An active or unknown run keeps the installation occupied.
The original frozen base supplies child inputs even after a newer draft is saved.
Applied seeds remain unavailable; seed axes are rejected. External randomness and
clock mappings retain their existing limitations. Platform mode has no campaign
contract and is unavailable for campaigns.

Actual native duration, cancellation and backend restart cases have Android/APK,
vehicle speed, snapshot, retry and cleanup evidence. Current browser preview/history
and child-input inspection are verified at both desktop sizes. Full campaign GUI
submission and the broader live fault matrix remain acceptance work; consult the
current implementation status for their results.
