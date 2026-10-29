# Active project and requested-operation context — Linux partial evidence

This repairs project-context handling under FR-002/FR-023/FR-026 and NFR-006,
with partial T038/T067 evidence at 1024×768 and 1440×900. All 24 new context
cases plus 38 existing recovery cases pass; the full 233-browser successor and
separate two-case performance run also pass. Application, compiled UI, runtime and
performance inputs match across these runs; every input stayed unchanged within
each run. One unrelated display-test setup changed before the final full run and
has an explicit input-difference control and affected retest. Type/build,
architecture, compatibility and spec checks pass. No milestone is accepted and
the component count remains 47/100. Windows remains held at user request.

The active Project remains the rendered workspace until a current successful
load is accepted. Failed requests carry a separate target ID; recovery guidance
names that project explicitly. A recovery commits independently on the backend,
but cannot replace another workspace after the operator resumes authoring there.
Workspace interaction has its own sequence so unsaved parameter input counts as
intent without invalidating legitimate revision acknowledgements. Recovery context
is captured at submission, including when its error panel immediately unmounts.
Creation/import requests advance navigation generation at initiation, and their
continuations require an accepted load. Startup metadata cannot reopen a remembered
project after newer navigation. No backend contract or execution authority changes.

## Direct transaction evidence

The native Tab/Enter journeys use the real isolated Linux backend and public API.
Authentication and fixture preparation are separate helpers. Controlled unreadable
files are confined to the owned browser-test data root, with path, real path and
original bytes checked before modification and restoration in finally. No arbitrary
host root, provider or device is accessed. These focused cases never Start a run.

Actual B recovery replies are held after commit while the still-visible A workspace
receives a newer source draft, source save or parameter draft. Releasing B preserves
A's exact source/cache/context/focus or parameter value. Actual A PUTs advance once
and are acknowledged before releasing B; other A documents remain exact. B advances
once independently and its real recovery backup preserves the observed bytes.
Both projects' run sets remain unchanged.

Actual successful and failed HTTP 409 B reads are held while the operator returns to A
and saves source. Late replies and the creation continuation preserve the new modal,
acknowledgement and active identity without leaking an obsolete error. A held HTTP 201
creation reply has the same counter; its backend-created project stays retained.
Two actual creation POST replies are held, then the older is released while the
newer is pending; the latest creation intent wins, and both projects stay intact.
Actual HTTP 200 startup discovery and a labelled controlled HTTP 503 metadata failure cannot
reopen a project or display a late error after explicit Home. The HTTP 503 is a transport
fixture, not evidence of a live provider failure. Delayed-import completion is
source-reviewed without a dedicated held-import journey.
Post-hydration create/import modal continuation, retained-pointer supersession and
newer state of the same run also lack dedicated hydration journeys. The Source
counter covers reload hydration and modal preservation directly.

The existing 38 recovery cases retain positive foreign recovery with no intervening
authoring, boot recovery, current refusal/focus, actual stale HTTP 412, equal/newer head
and exact history/readiness, Home, deliberately moved focus, pending submissions,
history failure/shape/window/absence and actual preserved backup bytes. These
counterchecks ensure the new guards do not disable legitimate recovery.

## Retained failures and review

initial-red/ records the first 10-case run: nine failures and one pass. Four failures
were fixture errors (the accessible Duration name includes its unit; unreadable
project reads return HTTP 409). That run is not counted as ten product failures. After
those corrections and an explicit response/client settlement barrier, context-red/
records ten actual failures on unchanged 077d581. ten-successor/ records their first
repair passing before the extra creation/startup counters were added.

The first expanded 56-case cohort overlapped an asynchronous build. Its actual result
was 55 pass/one failure, but compiled assets were not frozen or included in its older
map. overlapping-build/ retains that failed run and its classification as invalid
candidate verification. It is never relabelled a pass. The final build completed
before the successor target began; all six compiled assets are in its before/after
map; the later unrelated setup-input difference is declared separately.

The first frozen successor passed 56 focused and 227 full browser checks, then both
performance journeys failed before retained-history measurement: Results navigation
superseded the overly broad cached-run context guard. Those outcomes and their
source/compiled maps remain under before-run-context/. A dedicated actual retained-run
counter reproduced missing metadata at both viewports while Home departures passed
(cached-run-red/: two failures/two passes). Run hydration now requires current
project/load, the same stored pointer and matching returned ownership, independently
of the stricter navigation-continuation acceptance. New Results, Source-modal and
Home cases use real held metadata from the inert registered journal fixture; no run
is started. Relevant metadata can restore after Results/Source interaction while
Home remains departed. Replacement target/full/performance results apply to the
repaired candidate; the earlier performance failure is never relabelled a pass.
The older local wrapper recorded the failed child status but returned zero itself;
the retainer still refused the failed gate and no task update ran. Replacement
wrappers propagate the child exit status before downstream retention/documentation.

The first 62-case replacement was interrupted for a known test selector error:
12 passed, two Source cases failed, one was interrupted and 47 did not run. The
modal-preservation assertion passed and hydration added a count to the Results tab's
accessible name; the subsequent exact-name selector was wrong. Its raw result remains
under source-selector-interrupted/. The corrected selector includes the count. These
metadata cases now use the existing small inert registered-reader fixture rather than
the 50,000-record workload, with public hash-integrity/count checks. The separate
performance workload still uses 50,000 records; no performance threshold was reduced.

The next full 233 run ended 232 passed/one failure before the incompatible-time/unit
display assertions: its actual 0.2-second reference fixture was still observed as
running when the default 10-second poll expired. The retained worker journal shows
normal duration completion, cleanup complete and evidence complete. Individual old
HTTP poll timings were not recorded, so no host-load cause is asserted. The original
232/1 remains failed under reference-stop-timeout/.

Independent review supported a bounded 30-second prerequisite-observation wait for
this display test, retaining the real runtime and all display assertions. It now
records at most 64 timestamped HTTP/state/version observations and explicitly fails
failed/unknown/HTTP-error outcomes. The affected case passed with real preparation
then stopped/version 2 observations (affected-setup-successor/). All bytes outside
this one setup block are identical. test-input-control.json and test-setup-change.diff
retain both file hashes and the exact change; final full 233 uses the corrected test.
The earlier 62/performance 2 maps retain their original test hash; all 265 other inputs
match the final full map. No application/performance workload or threshold changed,
and the measured performance was not rerun for different numbers.

Independent read-only review found the missing create/import initiation generation.
It was repaired and the overlapping creation counter was added. Final source review
passed with the delayed-import limitation above; it did not run tests or establish
native Windows, assistive-technology or broader acceptance. See independent-review.md.

## Measurements and candidate identity

One documented warm-up and 30 repetitions per viewport; retained raw distributions:

| Viewport | Selection/inspector p95 | Open/validation p95 | History p95 |
|---|---:|---:|---:|
| 1024x768 | 27.3 ms | 1651.4 ms | 446.2 ms |
| 1440x900 | 26.9 ms | 1708.5 ms | 446.1 ms |

All 20 selected guidance/history/foreign-target text and
paint pairs pass 4.5:1, minimum 4.7634:1. This is not a global
accessibility claim. No CSS change was required.

Final full-run input digest: `sha256:89e3e2cd015843e5e924fc6404c9099f1d65e8dc6e85b40ba4fd1d2bbe6f5b80` (266 source/compiled/fixed
inputs). The environment recorder's tracked-source subset is supplemental; the
authoritative map also includes the new test and compiled UI. Its Git identity names
the base commit, while this input digest and the later candidate binding identify
the tested successor. Backend 851 results are inherited through 163 exact unchanged inputs plus the
reviewed unchanged-command CI scheduling control; they were not rerun locally for
this frontend-only repair. See backend-input-inheritance.json. Both previous 077d581
Ubuntu24 CI runs passed backend, browser and clean package stages; their retained
receipt is separate from this successor's local verification. Current-candidate CI
and clean package evidence require their own exact identities.

Clean candidate `e82b511b7ab6265dfe0f14cd46efb356f57d4a7c` passed offline native Linux package provisioning from the prepared cache, startup/UI, Unicode persistence, public compilation and owned shutdown. All 100 manifest/archive/file hashes and six tested UI assets are verified; candidate-binding.json checks 260 committed source/fixed inputs plus six compiled assets. Native Windows remains held.
