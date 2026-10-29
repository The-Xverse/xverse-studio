# Native Linux shell operability — 2026-10-26

Partial T038/T067 evidence for NFR-006 and AC-031, following `../M1-accessible-diagnostics/`.
Both tasks remain in progress. No native Windows, screen-reader, complete accessibility or milestone
acceptance follows from this slice.

Four browser journeys pass against the owned native Linux backend in Chromium, two at 1024×768 and
two at 1440×900. Actual platform/browser versions are attached to each journey. Source identity,
final full-browser outcome and separate performance outcomes are recorded in `verification.json`.
Focused and full/performance counts overlap; do not add them.

The final full browser successor passed **89 checks**, no failures/skips/flakes, with source unchanged.
Typecheck, production build, architecture and planning-package structure passed. Its separate
performance refresh passed at both required viewports on the same source, with one warm-up and
30 measurements per workload. Raw distributions and validation outcomes are under `performance/`.

| Viewport | Selection p95 | Open/validation p95 | 200-row history p95 |
| --- | --- | --- | --- |
| 1024×768 | 27.9 ms | 1679.4 ms | 446.6 ms |
| 1440×900 | 27.1 ms | 1780.1 ms | 447.1 ms |

Workloads retain 200 elements/400 connections and 50,000 recorded events. History warm-ups were
418.5/1930.2 ms and are excluded from the declared warmed distributions; cold provisioning/journal
verification is also excluded. These measure Studio/browser fixtures, not simulator/device capacity.

Clean product commit `944a87502f1f986a3f2b5d72dd868aecabeaf167` passed a fresh offline Linux package
extraction with the prepared dependency cache, native startup/UI HTTP 200, Unicode persistence,
authoritative compilation and owned shutdown. `package/` retains its receipt and clean 98-file
manifest. All archive/file hashes and the exact tested frontend bytes were verified. Physical
source/cache/tool/temp paths were resolved; native Windows was not run. Fresh-host CI remains a
separate per-commit outcome, never inferred from the earlier e6c9de0/c4e31f6 passing runs.

| Journey | Observed behavior |
| --- | --- |
| Login instructions/error recovery | Native keyboard entry of a synthetic invalid token, real HTTP 401, password cleared, associated error/invalid state; editing clears stale feedback while retaining the instructions/help association |
| Main navigation | Named native navigation landmark, one current destination, Tab/Enter access through Workspace/Catalog/Laboratory/Environment; focused controls stay in the required viewport with visible outlines |
| Project form | Labelled field, native keyboard input, Escape returns focus to New project, then real project creation |
| Busy status | Real project response held for observation, textual Creating project notice inside the persistent polite live region, actual returned project identity, completion and modal close |

The login journey never reads or submits a real launcher secret. It uses deliberately invalid
synthetic strings, clears the field before evidence capture and records no cookies/bootstrap values.
The authenticated project journey uses the existing private session helper. The held response is
from the real backend, not a fulfilled synthetic project body. No run or physical action is requested.

## Findings and repairs

- Initial checks reproduced four failing journeys. Eighteen of 24 selected rendered text pairs
  failed the scoped 4.5:1 check. Login instructions/label/help measured about 2.792/3.129/2.364,
  idle navigation about 2.887, active navigation about 4.174, and busy text about 3.990.
  Foregrounds now use the existing darker muted text and selected blue.
- The main rail was an aside and active state existed only in visual styling. It is now a named
  navigation landmark; its selected button exposes `aria-current="page"`.
- Login instructions and actual 401 feedback were not associated with the password field.
  `aria-describedby` now links instructions/help/error, `aria-invalid` identifies rejection, and
  editing clears stale feedback. Backend authentication and bootstrap admission remain authoritative.
- Extending focus checks to Environment exposed a further real layout failure after an earlier
  review PASS: the focused Settings button moved to y=2911 at 1024×768 and y≈2661.7 at 1440×900
  when the tall Environment view rendered. The rail now keeps its flex width, has a viewport-bounded
  height, avoids vertical stretching and sticks while the document scrolls. The header retains its
  ordinary document scrolling. Final tests assert actual focused-button bounds, not focus alone.

All 24 final selected rendered pairs pass, with minimum 4.5204:1. `contrast-summary.json` retains
both initial and final colors, backgrounds, alpha layers, sizes and ratios. The existing helper uses
[WCAG 2.2 contrast minimum](https://www.w3.org/TR/WCAG22/#contrast-minimum) and
[relative luminance](https://www.w3.org/TR/WCAG22/#dfn-relative-luminance). Measurements cover sampled
normal-size text and supported CSS sRGB paint, including sampled transition states; unsupported paint
fails explicitly. This is not an exhaustive animation, hover, zoom or global conformance assessment.

`initial/` retains the four original failures. `recording-failure/` retains two later harness failures:
the test tried to read the error after verifying that editing removed it. Recording the rejected
state before editing repairs that test without changing the product. `rail-focus-red/` and
`rail-geometry-red/` retain the real geometry failure and its measured bounds. These are extensions
of one regression, not independent live failures. `targeted-successor/` retains the four-check pass.
Reports preserve their original artifact paths; JSON/text evidence is retained here independently
of the temporary browser-output paths. No tests were skipped.

The independent reviewer inspected the initial presentation repairs and then the new rail repair
separately. See `independent-review.md` for findings, follow-up and limits. Backend/services/scripts/
Python tests remain byte-identical to b2cf71a's 851-test cohort; they were not rerun for this frontend
slice. The exact checked file hashes are retained in `backend-source-equivalence.json`.

Native Windows stays held at the user's request. Actual assistive-technology execution, shorter
viewports, zoom and other browser engines remain outside this partial evidence; selected browser
semantics do not establish a full screen-reader assessment. Component count remains 47/100 and
no milestone is accepted.
