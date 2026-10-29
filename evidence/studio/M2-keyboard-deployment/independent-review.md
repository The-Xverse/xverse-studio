# Independent scoped review — 2026-10-26

Separate read-only reviewer `t076_hybrid_tests`: initial review, two calls, no edits or
suites. The actual API shapes support direct authoritative Project completion: clone
and binding updates wrap a full Project; mapping edits return it directly. Departure
guards and focus handling addressed the original eight reproduced cases. The review
remained open for two additional risks:

- Explicit new-clone selection fell back to the sole old cached variant during loading.
- An acknowledgement for the same revision already loaded by newer readiness cleared
  that readiness despite obsolete selection intent.

Both were then reproduced against the real backend at both viewports. The first
readiness fixture used extra clock/resource declarations and returned blocked before
the timing invariant was reached; that harness mismatch is retained separately.
The corrected readiness fixture uses the exact admitted reference and an ordinary
native binding save, with no extra clock/resource admission. It observed a real ready
dialog and then its loss after the older acknowledgement. No Start was requested.

Follow-up review PASS, two calls including source inspection; no edits or suites. An
unresolved explicit selection no longer exposes another variant's forms, and loading
is announced. Equal/older acknowledgements cannot invalidate the already-current
Project or newer readiness. All Project assignments share a synchronous head reference
so this comparison is current before React renders. API handling remains correct;
accepted revisions reconcile history and contextual completion guards preserve newer
selections/drafts. Mapping-removal focus respects context, modals and deliberately
moved focus. The tests compare the complete intended Deployment spec and matching
cloned Scenario, exact requests/revisions and unchanged original documents. Root's
18-case unchanged-source successor passed.

No confirmed blocking issue remains for this reviewed slice. Scope remains selected
native Linux Chromium authoring/focus behavior. T038/T067, Windows and full actual
assistive-technology acceptance remain open. Declared resource or time relationships
establish neither reservation, clock accuracy nor execution.
