# Linux diagnostic operability successor — 2026-10-26

Partial evidence for T038/T067, AC-031 and NFR-006/NFR-011. Both tasks remain **in progress**;
no milestone or complete accessibility acceptance is claimed. Native Windows remains held at the
user's request. Source identity is in `application-source-hashes.json` and `verification.json`.

The final source passed eight targeted diagnostic journeys and the complete 85-check browser suite,
with no failures, skips or flakes and unchanged application/test source. Typecheck, production build,
architecture boundaries and planning-package structure passed. The backend, contributor scripts and
Python tests are byte-identical to the 851-test b2cf71a cohort; those tests were not rerun for this
frontend-only slice. `backend-source-equivalence.json` retains the exact comparison.

| Journey, repeated at 1024×768 and 1440×900 | Actual scope |
| --- | --- |
| Invalid-source recovery | Save invalid YAML through the real source editor; inspect the public-validator explanation, navigate its offered source action using Tab/Enter, restore the selected source and validate authoritatively |
| Retained evidence and next actions | Real recorded journal with clock domains, telemetry gaps and partial evidence; keyboard Inspect events and retained focus on the Events & logs tab |
| Lost ownership / cleanup / unavailable evidence | Explicit transport-only fixtures produced by the production explanation function; textual facts/hypotheses, no writes, no Stop/Cancel offered; no live failure claim |
| Stale plan and recovery | Actual saved input change after freezing a preflight; backend PLAN_STALE disables Start; the offered Recheck reads current saved inputs, freezes a new plan and restores focus |
| Artifact recovery | Explicit transport-only missing-artifact explanation and recovery; no actual missing provider/artifact acceptance claim |
| Late readiness response | Actual saved revision change and held owned preflight response; navigate through Home and the Workspace breadcrumb before release; Home stays selected and the modal stays closed |

All critical navigation/actions in these journeys use native Tab/Shift+Tab and Enter; source input
uses keyboard editing. API/recorded-fixture setup is identified in the test source. Runtime controls
remain backend-admitted. Actual Chromium version, Linux architecture and viewport are attached to
each final diagnostic journey under `journeys/`.

## Confirmed repairs and retained failures

- Muted and severity text failed contrast on their actual backgrounds. Darker foregrounds repair
  the measured pairs. The final 26 selected rendered pairs all pass 4.5:1; the minimum is 4.5919:1.
  `contrast-summary.json` retains colors, alpha layers, font sizes and ratios; `css-color-repair.json`
  separately retains computed old/new flat-color controls.
- Inspecting diagnostic events unmounted the focused button and left focus on BODY. It now focuses
  the persistent Events & logs tab, and the test asserts selection and focus.
- A server-reported stale plan left Start enabled and Recheck reused the cached revision. Staleness
  now remains sticky for that frozen preflight, and Recheck loads the current saved revision.
- Independent review found that the new current-project refresh could restore an old project after
  leaving it or overwrite newer context. Navigation, modal intent and selection changes invalidate
  pending readiness requests; both project-load generation and subject/request guards are checked.
  The held-response regression failed before this repair and passes afterward.

`initial/`, `focus-inspection/`, `first-successor/`, `stale-action-red/`, `navigation-race-red/` and
`navigation-selector-failure/` preserve original logs/reports. The two initial/focus reports are
snapshots of the same failed run, not independent repetitions. Some intermediate failures were
harness issues: the now-unmounted focus target, a headless Ctrl+R shortcut, an ambiguous Workspace
selector and cleanup of a held route. They were corrected without skipped tests. Passing intermediate
83-check evidence remains in local scratch; it is superseded by the final 85-check report here.

The contrast helper follows [WCAG 2.2 contrast minimum](https://www.w3.org/TR/WCAG22/#contrast-minimum)
and [relative luminance](https://www.w3.org/TR/WCAG22/#dfn-relative-luminance), using CSS sRGB
alpha composition through explicit opaque backgrounds. Unsupported gradients/images, ancestor
opacity, filtering or blending fail the measurement instead of assuming a background. This evidence
covers selected normal-size text and supported paint, not arbitrary masks, text-fill overrides,
complex backdrop composition or global WCAG conformance. Visible focus is asserted in the existing
operability journeys; no overall AAA focus-appearance claim is made.

The final source also has a separate performance refresh under `performance/`: one warm-up and
30 measurements per viewport for 200 elements/400 connections and the first 200 rows of 50,000
recorded events. These are Studio/browser fixture measurements, not simulator or device performance.
Full-suite and targeted/performance counts overlap and must not be added.

| Viewport | Selection p95 | Open/validation p95 | History p95 |
| --- | --- | --- | --- |
| 1024×768 | 25.6 ms | 1683.5 ms | 430.5 ms |
| 1440×900 | 22.7 ms | 1669.8 ms | 430.7 ms |

The 1440×900 history warm-up took 2941.9 ms; it is retained and excluded from the declared warmed
30-sample p95, as specified by the workload. Initial provisioning/cold journal verification is also
excluded. This result does not establish a cold-start history latency target.

Remaining gates include assistive-technology assessment, other declared browser/paint coverage,
the complete native-platform matrix and live provider failures where required. No screen-reader,
native Windows, external-provider or physical-device success is inferred from this dossier.
