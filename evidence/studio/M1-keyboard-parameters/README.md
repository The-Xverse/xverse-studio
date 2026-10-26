# Linux keyboard parameter completion — 2026-10-26

Partial T038/T067 evidence at 1024×768 and 1440×900 for AC-031/NFR-006. All 28 focused
checks and the complete 145-check browser successor pass without failures/skips/flakes.
Application/runtime/test inputs match the final focused run. Full and performance runs
record identical source/fixed inputs, including ADR-0013/0015, unchanged during each
run; the targeted runner's narrower map excludes architecture documents. Count remains
47/100 components, no milestone accepted. Windows and full actual assistive-technology
acceptance remain open.

The exact owned reference has one Scenario. Critical interactions use native Tab/Enter
and keyboard text entry. Authentication and project fixtures use the existing helper/
API before the critical flow. The main journey rejects Duration 31 through the actual
native maximum 30 constraint, focuses the field and sends no mutation. Revision and
documents stay unchanged. Correcting to 6 submits one typed set_parameter transaction,
advances once, changes only the Scenario's duration, preserves all other parsed Scenario
content and every other document's bytes, and passes authoritative validation. The
project's run identity set stays unchanged; no Start or live parameter mutation occurs.

## Reproduced defects and repair

`completion-red/` retains the settled original cohort: 12 actual failures and two passing
deliberate-focus counterchecks. Duration guidance lacked an accessible association;
successful Apply lost focus after disabling; old responses reopened Home, replaced a
newer tab history, erased newer same-field/other-field drafts and dismissed a newer
ready preflight. All held responses come from actual server commits; only browser
delivery is delayed. `failure-red/` separately records real 412 refusal in current and
departed contexts: current failure correctly retained the draft, while both departed
contexts showed obsolete errors. `normalization-red/` records a review-found edge in
the initial repair: successful 5.0-as-typed 5 left the field dirty when source value was
unchanged. Its actual success now normalizes only the matching submitted generation.

Generic edit completion captures project/load/selection intent and tab history before
sending the revision-checked transaction. The response already contains the authoritative
Project; completion no longer starts a fresh load from an obsolete closure. Known newer
heads are preserved and history writes compare with the captured initial head. Current
forms receive explicit success; obsolete responses and errors cannot acknowledge them.
Equal-head completion preserves newer readiness, including its exact preflight ID.
ADR-0013 documents these client rules; backend contracts and immutable run inputs are
unchanged.

Drafts belong to project/document/Scenario/parameter identities. Per-field generations
preserve newer text, including an explicit revert to 5 while saving 6, and other dirty
fields survive a returned Project. Unchanged metadata does not erase dirty intent.
Only a matching submitted generation may normalize after acknowledgement; a resolving
failure wrapper is not success. Unsaved input and its current saved value are labelled
and associated with the control. State/references are bounded by the current field set.
These parameter drafts are in memory while the form is mounted; this slice does not
claim new reload/navigation autosave persistence beyond the existing source recovery.

Apply completion restores focus to its enabled field only for the same identity and
edit generation, current authored value, no modal and origin/BODY focus. Native outline
and viewport bounds pass. Counterchecks preserve deliberately moved focus and a second
project's newer draft with the same parameter ID. Real stale failures retain the input,
show the current-context error and never normalize or acknowledge focus. Every lane
retains its own project run set; no run is created.

The first full 141-check cohort ended with 140 passed and one failure: a second project
kept its newer input but lost focus when delayed inert presentation metadata regrouped its fields.
That actual failure is retained under full-presentation-focus-failure/. Four controlled
presentation cases then reproduced two field-focus failures and two passing moved-focus
counterchecks. The repair tracks the focused semantic control and restores its same-key
replacement only after removal, with BODY/no-modal and deliberate-blur guards. Returned
grouping is asserted in the final test; presentation is applied rather than frozen.
The final 28-case cohort includes these four cases. Their original/full outcomes remain
separate from the final 145 successor and must not be counted as extra passes.

## Test harness corrections and evidence scope

`initial-red-before-settle-barrier/` used an empty global busy label as completion proof;
a newer action could already have cleared it, so its two readiness passes were too weak.
The final no-run fixtures explicitly wait for finite request quiescence after release,
draining response-triggered refreshes before asserting state. This exposed the actual
readiness failure retained in completion-red; the original results were not relabelled.

`test-scope-syntax-error/` is the later misplaced assertion/scope edit: the invocation
executed no cases. Its log/source is retained as a harness error. `secondary-project-fixture-cache/`
prepared the second project after the page's initial project list loaded; its row was
not in that cached list. Reloading the first project completes fixture setup before
the keyboard journey. That correction required no product change. `twenty-two-successor/`
predates the final two project-isolation counterchecks. Counts overlap and must not be
added. Independent implementation and follow-up review pass after normalization/scope
repairs; the final full suite is separate execution evidence.

## Final verification

Typecheck/build, architecture, descriptive compatibility consistency and spec structure
pass. Backend/Python/contributor/compatibility inputs remain byte-identical to the passing
851-test 13ff409 cohort; they were not rerun for this frontend-only slice. Hash proof is
retained. The environment recorder's tracked-source subset is supplemental; the full
source/input map includes the new test. This is native Linux Chromium, with no claim
of Windows, actual AT or global accessibility conformance.

All 2 selected parameter guidance text/paint samples pass the scoped
4.5:1 check, minimum 4.6849:1. No CSS change was needed. The helper's
supported-paint limits and the remaining global contrast/AT matrix remain explicit.

Separate final-source performance passes one warm-up plus 30 measured samples per
workload/view: 200 elements/400 connections and 50,000 retained events. Raw distributions,
warm-ups and authoritative model-validation outcomes are retained under performance/.
Cold preparation is excluded by the declared profile. These measure Studio/browser
presentation, not provider, simulator or device capacity.

| Viewport | Selection p95 | Open/validation p95 | 200-row history p95 |
| --- | --- | --- | --- |
| 1024x768 | 28.5 ms | 1655.7 ms | 446.6 ms |
| 1440x900 | 28.6 ms | 1663.3 ms | 446.9 ms |
