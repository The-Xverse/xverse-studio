# T027 slice review

T027 remains in progress. Its description, dependencies and acceptance cases are
unchanged; the task count remains48 completed/42 in progress/10 blocked.

| Existing task clause | Current implementation and observed evidence | Remaining scope |
| --- | --- | --- |
| Run plan and Start | The existing preflight dialog submits a frozen snapshot. Eight new actual configured native backend/browser journeys use keyboard Start and verify one run, a valid snapshot and an unchanged Project. | Complete environment and startup-boundary matrix. |
| Startup state | `RunStartupStatus.tsx` separates reported preparation, rejected startup, recorded start, post-start failure and unresolved ownership. Actual mismatch, injected launch refusal, owned Linux interruption and normal Stop pass at1024 and1440. | Other pending/history branches are presentation logic, not newly observed native startup transitions. |
| Stop and cleanup | New normal Stop reaches stopped/complete; actual guarded post-start interruption reaches failed/unknown. The broader cohort retains lost Stop acknowledgement, duplicate request and unresolved-ownership views. | The entire prepare/stop/evidence-finalization fault matrix and positive failed-cleanup recovery are not established by these cases. |
| Evidence and outcome | Rejected workers have no journal or recorded start; evidence stays unavailable. Started interruption remains distinct from cleanup and verdict. Broader cases retain same-version evidence updates and recorded unavailable/partial/invalid distinctions. | Recorded/transport fixtures do not establish live provider finalization or integrity. |
| Optional operations | Every new native scenario receives backend422 for unsupported Pause; the UI identifies unavailable operations. Current generic controls implement admitted Stop/Cancel. | A genuinely admitted optional-operation provider and its controls/transitions remain absent. A mocked capability flag cannot close this clause or AC-027. |
| Immutable input identity | Existing Results frozen-input inspection and draft/run isolation remain; new journeys verify snapshot integrity/revision and unchanged canonical Project. Native rejection regressions also verify unchanged snapshot file/database bytes and same-key one-run recovery. | Supported live mutation with old/new value, authority, source time and outcome is not demonstrated. |

The full current backend suite passes1166 cases with no skips. The affected
browser suite passes30 cases, including the new eight; these totals overlap and
are not additive. A browser/backend input bridge changes only the descriptive
reference-provider implementation digest. Native Windows remains held; live Lite,
physical, human/AT/SADS and independent milestone gates remain open. This is a
primary-agent slice review, not independent milestone approval.
