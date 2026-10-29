# Independent scoped review — 2026-10-26

Separate read-only reviewer `t076_hybrid_tests`; no edits or test execution.
Design review identified the unreadable-project trap: clearing the global error unmounts
its RecoveryPanel before the API result arrives. App must own project/load/intent context,
accept the returned Project without a captured load, initialize a genuinely different
project and preserve its run ownership. The review also requested synchronous pending
submission protection and separate unknown/absent history observations.

Implementation review found no blocking state/context issue. The unreadable path survives
unmount, initializes the right project and scopes retained-run reads by project/load/intent
and returned ownership. Equal/newer heads preserve history/readiness. Current errors receive
focus; departed errors are suppressed. Retry focus and pending controls are scoped.
The remaining finding was an out-of-window successful history reply: positive safe revision
alone was insufficient. Both actual counterchecks failed on that first repair. Rejecting
revisions above the requested revision closes the finding. Follow-up read-only review PASS
for the Linux partial scope. Native repeated-Enter evidence proves pending controls/one
request, while the independent same-tick guard remains source-reviewed rather than claimed
as a separately proven native event race.

The first full 209-check cohort then completed with 201 pass/eight failures. All eight were
the helper's 220-forward-Tab exception before intended navigation/focus and response release.
Post-finally snapshots already show completed recovery, so the reviewer correctly rejected
them as evidence of failure-time focus. A controlled 200-row navigation-only metadata probe
then captured actual BODY focus: 220 forward Tabs did not reach Home, while six native
Shift+Tabs did at each viewport. Only the real owned target was recovered; no added row
was activated. This establishes the helper limitation, not project-list persistence.

Final bounded review confirmed the corrected helper uses native keys, asserts the exact
target's focus before Enter and performs no direct focus injection. All 264 declared
unchanged product/compiled/fixed inputs match their recorded hashes; only that recovery
test changed. The original full result remains failed 201/8. Successor execution is a
separate gate, not established by this review. No product repair or broader acceptance
claim follows from the helper correction.

T038/T067 remain partial. Native Windows, actual AT and complete accessibility/milestone
acceptance remain open. Fixtures access only declared owned browser-test data, never an
unrelated file root, live device or simulator. No Start/replay authority is introduced.
