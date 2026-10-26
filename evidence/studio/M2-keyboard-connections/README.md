# Linux keyboard connection authoring — 2026-10-26

Partial T038/T067 evidence for AC-031/NFR-006 at both required viewports. Two native
keyboard journeys pass. T038/T067 remain in progress; no milestone, native Windows or
complete accessibility acceptance is claimed.

The actual pre-repair browser accepted `Bad_ID` while the backend rejected its edit
with HTTP 422/INVALID_EDIT, preserving the exact documents and revision. The field
lacked a format description. `grammar-red/` retains both failures and completed
recovery outcomes. The repair matches the backend's lowercase/single-hyphen grammar,
adds a persistent field-associated instruction and derives `aria-invalid` for a
nonempty invalid value. Native constraint validation focuses the invalid field and
prevents that browser request. No length restriction was added; backend validation
remains authoritative and is independently exercised by an actual rejected API edit.

Critical authoring uses native Tab/Enter, select Home/arrows and keyboard text entry.
Disabled options are inspected through their native `disabled` property; arrows skip
them. Authentication and owned fixture creation use the existing helper/API. Setup
removes only `command-flow`; it preserves `state-flow`, endpoints and definitions.
The journey reads the interface-mismatch explanation and compatible-target guidance,
corrects the identifier, submits exactly one `connect_endpoints` edit, and verifies a
single revision advance. The canonical command flow retains endpoint identities,
interface, clock and ordered delivery. The complete parsed flow collection, all
non-flow System fields and every other document's bytes equal the original. Flow order
may differ because creation appends; original System bytes or semantic-digest equality
are not claimed. Keyboard expansion exposes admission checks; authoritative validation
passes. The project's run
set remains unchanged. Declaration/admission does not prove routing, observed traffic,
native X-COM or provider execution.

`harness-option-assertion/` is the original test-harness failure: Playwright's
`toBeDisabled` does not report this native disabled option as disabled. Inspection
showed the actual disabled attribute; the correct property assertion passes. This is
not a product defect. The two grammar failures were reproduced after that correction.

The full browser suite passed **99 checks**, no failures/skips/flakes, with source and
fixed inputs unchanged during its run. Independent review then suggested asserting
the complete flow collection, excluding an unexpected third flow. That supplementary
test assertion and attachment flag were added; the final affected two-viewport journey
passes again. Application/runtime/harness bytes are identical to the full 99-check candidate.
`full-browser-source-hashes.json`, `application-and-input-hashes.json` and
`test-strengthening-equivalence.json` distinguish these exact test sources. The exact
full-suite test bytes and six-line strengthening diff are retained as well. The full
suite was not rerun solely for the additional assertion. Counts overlap and must not
be added. The final-source separate performance refresh also passes:

| Viewport | Selection p95 | Open/validation p95 | 200-row history p95 |
| --- | --- | --- | --- |
| 1024x768 | 27.1 ms | 2228.5 ms | 462.2 ms |
| 1440x900 | 31.2 ms | 1714.5 ms | 461.7 ms |

Each performance workload retains one warm-up and 30 measured samples, using 200
elements/400 connections and 50,000 recorded events. Warm-ups and cold preparation are
excluded by the declared profile; raw samples and authoritative model validation are
retained separately. This measures Studio/browser presentation, not simulator capacity.

All 4 selected guidance text/paint pairs pass the scoped
4.5:1 helper check (minimum 4.6849:1). No CSS change was needed.
The helper's paint restrictions, native Linux Chromium scope, absence of actual
screen-reader assessment and broader accessibility gaps remain explicit. The
environment recorder's tracked-source subset is supplemental; the authoritative map
includes the new test. Typecheck/build, architecture, compatibility consistency and
spec structure passed. Exact unchanged backend/Python/contributor/compatibility
inputs inherit the passing 851-test 13ff409 cohort; backend tests were not rerun for
this frontend-only change. Scope remains 47/100 components, no milestone accepted.
