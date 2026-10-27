# Finite campaigns

Open **Experiments → Campaigns**. Obtain a ready preflight for the current revision
with **Preflight & run**, then return to the draft. This does not start a run.

Enter numeric parameter arrays, maximum runs, maximum total simulated seconds,
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
means nothing was created. Linux owned-reference evidence does not admit external,
physical or native Windows provider execution.
