# Read-only Linux partial review — 2026-10-26

Reviewer: separate `t076_hybrid_tests` agent; scoped calls, no suites or writes. Final verdict:
**PASS for Linux partial scope**, no blocking finding remains in the reviewed slice. T038/T067 stay
open; no milestone acceptance follows.

| Reviewed issue | Finding / repair |
| --- | --- |
| Contrast | Supported CSS sRGB alpha composition, luminance and ratio calculations are correct; unknown paint fails explicitly. Darker foregrounds address measured failures. |
| Diagnostic focus | Inspect events focuses the persistent Events & logs tab after the originating button disappears. |
| Stale readiness | PLAN_STALE disables Start for that preflight; offered Recheck fetches current saved inputs, creates a fresh preflight and restores meaningful focus. Backend Start admission stays authoritative. |
| Navigation race | Initial review found late current-project/preflight reads could reopen departed workspaces or overwrite newer same-project context. Project-load generation, request sequence and subject guards now protect both response stages. Navigation, modal intent and execution-selection changes invalidate pending work. |
| Test scope | Real invalid-source recovery, actual stale saved-input changes and held-response navigation at both required viewports. Synthetic artifact/transport outcomes are labeled and confer no provider authority. |

The reviewer inspected the final guards and successor changes after repairs. Main-runner evidence
reports eight targeted and 85 complete browser checks passed; the reviewer did not rerun those suites.

Limits: Chromium/native Linux only, selected text/paint/workflows, no assistive-technology assessment,
no arbitrary mask/text-fill/complex backdrop claim. Native Windows stays held; complete accessibility,
milestone and live-provider acceptance remain open.
