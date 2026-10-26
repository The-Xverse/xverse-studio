# Linux keyboard instance/history successor — 2026-10-26

Partial T038/T067 evidence for AC-031/NFR-006 at 1024×768 and 1440×900. Eight focused journeys pass:
complete instance authoring/history at both viewports, plus delayed-history departure, deliberately
moved focus and newer same-project history at both viewports. T038/T067 remain in progress; no
milestone, native Windows or complete accessibility acceptance is claimed.

The final full browser successor passed **97 checks**, no failures/skips/flakes, with source and fixed
inputs unchanged. Typecheck, build, architecture, descriptive compatibility and planning-package
structure passed. The separate final-source two-viewport performance refresh passed one warm-up plus
30 measurements per workload; counts overlap the functional suite and must not be added.

| Viewport | Selection p95 | Open/validation p95 | 200-row history p95 |
| --- | --- | --- | --- |
| 1024×768 | 24.1 ms | 1648.1 ms | 446.5 ms |
| 1440×900 | 25.2 ms | 1708.3 ms | 447.3 ms |

The fixtures retain 200 elements/400 connections and 50,000 recorded events. History warm-ups were
440.7/1933.6 ms, excluded from the declared warmed distributions along with cold provisioning/journal
verification. Raw samples and model validation outcomes are under `performance/`; this measures
Studio/browser fixture presentation, not simulator/device capacity.

The critical wizard uses native Tab/Enter, arrows, Space and keyboard text entry. Native radio groups
have one Tab entry; arrows select their other options. No programmatic focus, selection, input fill,
scroll or pointer click drives the critical authoring path. Private authentication and owned project
setup use the existing helper/API; they are separate from this scoped keyboard claim.

The journey selects a project-owned definition, rejects `Bad_ID` with textual Review status and no
write, then chooses a distinct identifier, role filter/node placement, deployment variant, simulated
realization, target and artifact metadata. Review explicitly states that nothing is built, flashed or
executed. One actual `/edits` transaction contains `add_element` and `add_binding`; its revision
advances once. The canonical System has the new component instance/definition reference/node, and
the Deployment has a separate binding. Reusable definition bytes remain identical.

Enter and toolbar-origin Ctrl+Z/Ctrl+Shift+Z then exercise Undo/Redo as new authoritative revisions.
Original and created source bytes are restored exactly, without rewriting history or definition
sources. Authoritative validation passes after the final restoration. The project's run identity set
is unchanged. Selecting a simulated binding does not prove that a provider admits or executes the
additional instance; no run/build/flash/provider operation is requested.

## Reproduced defects and repairs

- Undo/Redo restored the right bytes but left focus on BODY after the initiating control disabled.
  The successor restores an enabled initiating toolbar control, or its enabled opposite, after busy
  state clears. Actual focus outline and viewport/scroll-container bounds are checked.
- A real restore response held until after Home navigation reopened the departed project. The old
  handler started a fresh load using its obsolete project closure. The successor guards the captured
  project/load context and uses the full committed Project already returned by restore. Backend
  restoration authority, revisions and run snapshots are unchanged.
- Per-project completed history persists for return, while a comparison against the original tab
  history prevents an older response from replacing a newer head. Real native navigation/reopening
  and a newer real edit verify both the visible revision/value and exact retained history head.
- The first repair missed shortcuts while a history toolbar control itself was focused. Independent
  review found that bypass; six counterchecks passed while both shortcut wizard journeys failed.
  Shortcuts now share the completion/focus path for toolbar origins. Other origins keep their
  existing behavior, and original-control preference is independent of shortcut direction.

Focus restoration requires matching project/load/intent/section/modal context and focus still on
the originating control or BODY. It does not steal deliberately moved focus or reopen a departed
workspace. Late errors do not overwrite a newer context. `independent-review.md` retains the initial
shortcut finding and final scoped PASS.

Original reports/logs are retained under `history-focus-red/`, `history-navigation-red/` and
`shortcut-focus-red/`. The initial navigation red case was at the default 1440×900 viewport; its final
counterchecks run at both required viewports. `selector-failure/`, `history-navigation-selector/` and
`history-apply-selector/` are harness corrections: the owned presentation calls the modal Add Unit,
Duration's accessible name includes its unit, and Apply must be scoped to its parameter form. They
are not product failures. `initial-wizard-pass/` records the narrower creation path before history
was added. Counts overlap and must not be added. No tests were skipped.

All eight selected wizard text measurements pass the existing scoped 4.5:1 check, minimum 4.6849:1.
These are normal-size CSS sRGB text/background samples under the helper's supported-paint limits,
not global conformance or actual screen-reader execution. No CSS repair was necessary for these
measured wizard pairs. Raw colors/layers, native focus geometry, actual semantic outcomes and browser
identity are under `journeys/`; full and separate performance outcomes are in `verification.json`.
The environment recorder's tracked-source subset is supplemental; the authoritative source/input
identity includes the new test in `application-and-input-hashes.json`.

Backend/services/Python tests/contributor/compatibility inputs are byte-identical to the passing
851-test 13ff409 cohort; they were not rerun for this frontend-only change. The proof is in
`backend-source-equivalence.json`. Actual native Windows, assistive-technology assessment and wider
accessibility/failure acceptance remain open. Component completion stays 47/100; no milestone is
accepted. This evidence never substitutes for live provider or physical-device acceptance.
