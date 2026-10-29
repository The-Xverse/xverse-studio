# Physical-placement inspection — partial native Linux evidence

The independent read-only portion of T075 now presents T072's authoritative placement
observations in the Deployment workflow. Final 118 targeted browser journeys cover
46 new placement cases, 36 inventory, 20 deployment and 16 source regressions. The
full 339-browser suite and separate two-viewport performance checks pass. All
276 source/compiled/fixed inputs are identical across and within these
final stages, including six compiled UI assets. Type/build/architecture/compatibility
checks pass. The backend and admission contracts are unchanged.

T075 remains in progress. T074's durable provider reservation integration, connection
tests and actual device admission remain unavailable. AC-021–024 remain blocked,
Windows is held at the user's request and actual assistive-technology acceptance is
open. The component count stays 47/100; no milestone is accepted.

## Behavior and boundaries

Inspect physical placements makes an explicit GET for the selected authored Deployment
and committed revision. The report adapter checks version, exact project/document/revision
and selected System/Deployment context. The backend owns source validation, inventory
resolution and interface requirements; the browser performs no asset join. It retains
only bounded public fields. Identity, required interfaces, observed firmware, metadata,
provider OS declarations, evidence scope, availability, permission and blocked activation
are separate. Neither a matched asset nor an admission-looking label grants authority.

Invalid source reports are distinct from valid reports containing no physical/hybrid
bindings and from unavailable observations. Hyphenated authoritative XDL diagnostics
are preserved. When validation empties the variant list, inspection alone can use a
unique matching authored display identity. Duplicate or absent identities keep it
unavailable; this fallback is never supplied to execution or authoring controls.

One response contains at most 1,000 bindings, displayed in local pages of 50. Each
row remains accessible without another inventory read. Inventory/interface truncation,
provider diagnostics and unknown facts remain visible. The 30-second abort deadline
is source reviewed, not directly timed in these browser witnesses. Canonical state
is never committed or reloaded to acknowledge a GET. Stale revision refusal requires
explicit reopen. Context/generation/abort guards suppress obsolete reports and errors;
native pending resubmission creates one read, and deliberate focus/newer dialogs survive.

The adjacent resolution table now wraps its inherited nowrap headers. A diagnostic
cohort proved that the long Value sources heading caused whole-page overflow at 1024
pixels. The scoped rule preserves full text and table semantics. Long public Unicode
metadata and expanded raw inspection remain observable without horizontal page overflow.

## Verification scope and retained failures

Actual public source save and read APIs establish physical declarations, empty binding
sets, invalid source, stale 412 and explicit reopen recovery. A strict realpath-checked
file in the newly owned browser root is temporarily made non-UTF-8 for actual 409
refusal and restored in finally. Held actual reports exercise Home, new project,
changed variant, newer committed revision, source dialog and deliberate focus. Full
canonical Project objects, supporting files, revisions and run sets are preserved.
The newer-revision case performs one expected UI source save before monitoring the
late read; other inspection phases perform no mutative requests. No Start, device
operation, provider registration, reservation, connection or stimulation occurs.

Positive matched metadata, malformed contexts/authority and maximum reports are
explicitly labelled transport fixtures. They do not establish actual hardware,
device firmware, provider OS support or physical execution. The existing public
inventory fixture is read by e2e tests only; no backend/runtime input changed.

Historical cohorts are retained with exact maps/reports/logs/tests and classifications:

- initial-red: two missing-control failures on the unchanged committed UI.
- first-successor: 38 passed, including all inventory regressions.
- invalid-source-red: two failures from disabled inspection after source invalidity.
- invalid-source-successor: two passed/two failed, reproducing client rejection of
  the actual XDL-PARSE-YAML diagnostic. The real validator result is retained.
- expanded-first: 37 passed/one 1024 overflow failure.
- overflow-diagnostic: one passed/one failed on unchanged product; measured width
  1382 and resolution-table right edge 1381.875 at the 1024 viewport.
- expanded-successor: 98 passed/two failed from a fixture assumption that document
  IDs were globally unique. Both projects use doc-3. The corrected successor verifies
  the destination GET/report projectId and its project-local document identity.
- before-source-setup-targeted: 102 passed on the unchanged product. The first full
  339 then ended 338 passed/one failed before its deliberate-focus assertions:
  holdPut.ready expired at its default 10-second setup observation wait. Performance
  did not run. The owned source save completed as revision 2; the original request
  timings were not collected, and the host-load cause is unproven.

The replacement source helper bounds both actual PUT transport and setup observation
at 30 seconds, records at most 64 timing events and still requires the real response
before the unchanged focus/source assertions. No application deadline or performance
threshold changed. source-setup-input-control.json proves all bytes outside that
one helper unchanged, and the exact diff and original source snapshot are retained.
All 275 other source/compiled/fixed inputs match the failed full and earlier 102 cohort;
final 118/full 339/performance 2 share all 276 inputs. The final target expands to
include all 16 affected source journeys. This does not relabel the earlier failure
passed or assert that the original focus countercheck ran.

No failed cohort is relabelled passed. The duplicate authored identity refusal was a
source-review finding with a new successor witness, not a prior reproduced red.
The root implementation review is not independent review or milestone acceptance.

## Measurements and identity

One warm-up plus 30 repetitions retains the declared 200-element/400-flow workload
and evidence history with 50,000 records and at most 200 displayed rows.

| Native Linux viewport | Selection p95 | Open/validation p95 | History p95 |
| --- | --- | --- | --- |
| 1024x768 | 29.5 ms | 1653.1 ms | 446.2 ms |
| 1440x900 | 27.8 ms | 1648.3 ms | 445.9 ms |

Selected rendered text checks cover 30 paint pairs with a
minimum ratio of 4.60581:1 against a 4.5:1 threshold. Focus,
control bounds and descriptions have native browser witnesses at both viewports.
This is scoped Chromium evidence, not overall accessibility or assistive-technology
certification. The environment includes an actual owned live browser executable,
version and SHA256 observation without private arguments or authentication state.

Final input digest: `sha256:6bd1453314475a21039e72e0f1872863fafce79f4939104c395b3d5b9b188cc4`. The recorded Git identity is
the predecessor; a later clean candidate/package binding establishes exact committed
identity. Backend 851 results are inherited through 163 exact unchanged backend/Python/
contributor/compatibility inputs and unchanged-command CI scheduling control, not a
new local backend run. Both predecessor 24c55d5 CI runs succeeded with their own
terminal receipt; those outcomes cover that predecessor and successor CI is separate.

Clean candidate `6d21e8f8d12909b5448b44d3b25d7ece4a7d905c` passed offline native Linux package provisioning from the prepared cache, startup/UI, Unicode persistence, public compilation and owned shutdown. All 100 manifest/archive/file hashes and six tested UI assets are verified; candidate-binding.json checks 270 committed source/fixed inputs plus six compiled assets. Native Windows remains held.
