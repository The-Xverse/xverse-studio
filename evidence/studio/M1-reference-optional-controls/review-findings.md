# Remaining verification findings

Update, 2026-10-28: the observation-ordering finding below is repaired in the
current uncommitted candidate. The backend persists an independent
`observationVersion` only when read metadata changes; the browser accepts newer
observations without advancing the worker lifecycle version. Both polling and
control callbacks use the ordering guard. Actual native browser loss/recovery
at both viewport sizes and the ordering contract passed (3/3); backend recovery
and persistence checks passed (12/12). The broader affected browser cohort passed
80/80, with no skips or flaky results and all 377 selected inputs unchanged.
Private originals are `observation-red`, `observation-native`,
`observation-green`, and `observation-affected` under
`.studio-local/reference-controls/`; sanitized publication remains pending.

Fresh full backend verification passes1,199/1,199 as `observation-backend-full`, with377 inputs unchanged. Native frozen-intent timeline2 and separate performance2 also pass on the identical map.
The previous full result (1181 passed, four failed) remains a failed historical
candidate; the focused clock repair passed 13 checks. T027 remains in progress
pending the fresh full result, remaining verification, and clause review.
The finding description below records the pre-repair behavior.

The pre-repair full backend verification had four failures and retains its
complete outcome. The earlier 60 affected browser and two performance results
retain their exact candidate scope; they did not establish all ownership-
observation transitions.

The pre-repair review of the actual `mergeRun` function revealed a missing case. A worker's
lifecycle version can stay unchanged while the backend temporarily loses and
then verifies its ownership observation. At that same version, the browser merge
preserves its previous lifecycle and spreads absent optional fields from the old
object. An executed Node probe of the current function gives these results:

| Incoming authoritative observation | Current browser state | Merged result |
| --- | --- | --- |
| unknown at worker version 1 | running at worker version 1 | running |
| running with no current reason at worker version 1 | unknown with `OWNERSHIP_UNKNOWN` at worker version 1 | unknown with the obsolete reason |

This probe uses labelled metadata fixtures, not native/browser execution. Its
case is grounded in the native recovery regressions, where the original real
worker retains its lifecycle version across the observation interruption. The
existing backend continues refusing controls while ownership is unknown.

The finding required an independently ordered backend observation projection while
retaining the provider's lifecycle version and its CAS meaning. A newer full
observation must update uncertainty/recovery and clear absent optional reasons;
an older observation must not regress newer truth. Legacy lifecycle-version
guards and no-op read persistence must remain. Actual native backend/browser
recovery at the unchanged lifecycle version and stale-observation negative cases
are required before component closure. This is an implementation finding within
the existing truthful-state requirements, not a new task or changed acceptance.
