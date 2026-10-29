# Diagnose the current candidate

| Diagnostic | Meaning and supported next action |
|---|---|
| `UNAUTHORIZED` | Enter the current local one-use bootstrap; restart the native launcher if it expired. |
| `FORBIDDEN` | Use the exact loopback URL and authenticated session; restore same-origin CSRF requests. |
| `REVISION_CONFLICT` | Preserve drafts/external changes, reload and compare; do not overwrite another revision. |
| `MODEL_INVALID` | Inspect the authoritative XDL diagnostic and source location. Keep unknown content intact. |
| `PREFLIGHT_STALE` | Recompute preflight for the current exact inputs/capabilities before starting. |
| `CAPABILITY_UNSUPPORTED` | Select an admitted operation/template. Step/reset/live mutation are unavailable in this reference provider. Pause/Resume apply only to its owned simulation clock. |
| `PAUSE_BUDGET_EXHAUSTED` | The owned model reached its cumulative 30-second wall-time pause budget and stopped with incomplete simulation coverage. Inspect retained evidence and create a fresh run if needed. |
| `PREPARATION_FAILED` | The local run files could not be prepared; no workload launch was attempted. Retain the failed run, check local storage access and capacity, then recheck preflight before creating a fresh request. Retrying the original request returns its original receipt. |
| `EVIDENCE_OPEN_FAILED` | The provider could not create its canonical journal and did not start the workload. Preserve any existing files, check local storage access and capacity, and recheck preflight before a fresh request. |
| `EVIDENCE_FINALIZATION_FAILED` | The workload stopped, but its evidence could not be finalized. Inspect the separate cleanup outcome and preserve retained files; stopped execution does not imply resource release or valid and complete results. |
| `DEP-RUN-CONFIG` | An external public effective-input/plan contract is missing. Reference success cannot admit Lite/CARLA. |
| `OWNERSHIP_UNKNOWN` | Reconcile exact native ownership. Do not kill by PID/name/address or blindly restart. |
| `EVIDENCE_INVALID` | Preserve original bytes; do not use corrupted evidence to establish a verdict. |
| `PHYSICAL_PROVIDER_NOT_ADMITTED` | No device/provider/permission has been admitted. Offline authoring remains available. |
| `LIMIT_EXCEEDED` | Reduce the declared input/workload to the advertised bounds. |
| `EVIDENCE_FILTER_INVALID` | Use a supported source or receipt interval, exact integer source ticks, and one occurrence of each selector. |
| `CLOCK_SELECTION_REQUIRED` | Choose the original source clock explicitly; receipt time does not supply a clock mapping. |
| `CURSOR_INVALID` | Reset Results paging after changing a run, route or filter; do not reuse a previous selection's cursor. |
| `XDL1-PLAN-DEPENDENCY-CYCLE` | The selected platform compiler cannot compile this feedback plan. A compatible admitted path is required. |

An open port is not process ownership. If the chosen port is busy, select another unprivileged port
with `--port`, update the browser URL and leave the unrelated owner alone. Remote exposure is outside
this candidate. Do not enable permissive CORS or bind to all interfaces to conceal a local setup error.

Liveness is not functional health. Missing traffic without an admitted expected coverage window is
unobserved, not an established failure. Wall-clock receipt time never substitutes for simulation or
device time. Indeterminate assertion results preserve missing coverage and uncertainty reasons.

## Retained temporary resources

If Results reports failed or unknown cleanup, inspect **Resources requiring
inspection** and retain the run data. The owned reference releases only its
verified empty temporary directory; retained files and replacement identities
are left untouched. A stopped workload or complete evidence journal does not
confirm resource release. Follow the recovery guide before any manual cleanup;
retrying Start or Stop does not erase retained data or acquire another resource.
