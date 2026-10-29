# Live-follow presentation review before repair

Scope: successor of1c25714, read-only presentation/HTTP query changes. No provider,
SDK, execution authority, source writer or process ownership changes.

Verified65 affected backend checks, including original-order/newest-order pages,
source-immutable captures and order-bound signed cursors. Five controlled browser
cases pass: newest following and pinned causes; error retention/hidden/off-tab
pause; serial slow reads and late-response rejection;10second timeout/retry; final
capture then no further polling. A targeted visibility-resume check also passes.
These browser cases use explicitly labelled projection fixtures, not live evidence.
Initial backend14pass/1failure was an accidentally moved test block referencing an
out-of-scope variable; corrected before the65-case pass, with the failed log retained.

R01 minor: the timeout diagnostic unconditionally promises following will retry,
including manual reads with Follow off. Make the text accurately describe both
manual retry and optional following. Existing timeout behavior is otherwise verified.

Review confirms stale responses cannot cross current run/view/order/filter/request
boundaries, payload policy is unchanged, and a selected record/cause remains pinned
while inspected. Polling pauses outside the active visible view, retains the last
capture on failure and uses a finite deadline. Newest ordering preserves original
ordinals and clock domains; no full-message or hard-real-time promise is introduced.

After repairing R01, verify actual automatic capture/message updates against the
approved native simulation and record the exact candidate. Existing completed
two-run evidence remains valid for its original candidate and is not relabelled.
