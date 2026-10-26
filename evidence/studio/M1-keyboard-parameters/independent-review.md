# Independent scoped review — 2026-10-26

Separate read-only reviewer `t076_hybrid_tests`; no edits or suites. Preliminary review
required edit-generation preservation for an explicit revert while saving, project/
document/Scenario/parameter identity, explicit non-success from resolving error wrappers,
and the exact retained preflight ID. These cases were included in the browser checks.

Implementation review remained open for numeric normalization: `5.0` submitted as typed
5 could succeed without changing the authored value, leaving Apply enabled and focus
unrestored. The reviewer also found a misplaced test scope and out-of-scope readiness
assertion. The syntax invocation ran no cases and is retained as a harness error, not
product evidence. The numeric case was then reproduced against the real backend at
both viewports and repaired through explicit successful acknowledgement of the matching
field generation. Failed saves and newer text do not normalize.

Follow-up review PASS (four-call bound, no tests/edits). Obsolete responses cannot
acknowledge forms, replace newer history or steal focus. Draft identities include
project, document, Scenario and parameter. The test scopes are corrected, and readiness
checks assert the exact preflight ID. Numeric normalization uses an actual successful
transaction. No remaining blocker was found for the reviewed Linux partial scope.

Root's subsequent 24-case successor additionally exercises navigation to a second
prepared project with the same parameter ID and its newer unsaved input. All 24 pass
with unchanged application/test source. The secondary fixture's initial stale Home list
is retained separately and corrected before the keyboard journey, without a product
change. The first full 141-check gate then exposed a separate focus loss during delayed
inert presentation regrouping: 140 passed, one failed. That failure remains retained.

Four controlled real-presentation cases reproduced two field-focus failures and two
passing deliberate-focus counterchecks. The additional layout-phase repair restores
only a removed focused node's same-key replacement, with current identity, BODY/no-modal
and deliberate-blur guards. Separate review PASS (three-call bound, no edits/tests);
no blocking production issue was found. The reviewer requested a rendered group-legend
assertion so ignoring/freezing metadata cannot pass. It was added before the final
source freeze. Root's final 28-case successor passes with unchanged application/test
source, including the actual returned grouping, current field and moved-focus cases.
The repeated full browser/performance gates are separate execution evidence.

T038/T067 remain in progress. Native Windows, actual assistive-technology assessment and
complete accessibility acceptance remain open. These are authored parameter edits and
ready preflight observations; no Start, live mutation or physical operation is claimed.
