# Historical assessment inspection retains focus and readable disclosure text

Source `27faf837790835466f05ca56f815edf1f71f7779` passes31 selected checks:
12 new native keyboard journeys at1024×768/1440×900 and19 unchanged older browser/
response-guard cases. Both final cohorts match572 Git-bound source inputs and six
UI assets, reproduced exactly in a second build. Typecheck, targeted helper lint,
architecture and planning checks pass; build warnings are retained.

Explicit assessment inspection previously left focus outside the report/error after
its triggering button became disabled. Six initial product failures reproduce this
at both sizes. The repair captures only explicit inspection/paging origins and
focuses the report heading or read error after the current request completes. The
existing request/abort guards remain; an additional intent/focus/dialog check
preserves newer keyboard work. Automatic initial loading does not capture focus.
The display identity/schema guard is byte-identical to its predecessor.

The first cohort is4pass/8fail: six product focus failures and two incorrect test
assumptions about the source dialog. SourceEditor intentionally focuses selected
XDL text, rather than Close. Corrected source-dialog controls join the four original
passing controls; all six pass on the original UI. The initial focus repair then
passes10/12. Its remaining two failures come from a self-imposed2px test threshold:
the browser's visible, bounded1px auto outline is valid under the plan's visible-
focus requirement, which specifies no numeric thickness. The test now checks
positive visible outline width and retains focus/bounds requirements.

The same disclosure control has a separate measured text-contrast defect. Its10px
normal text measures3.3855:1 against white at both sizes. The added contrast check
fails twice before the text repair. Darkening only `.json-details summary` from
`#7a8da8` to`#536580` raises the measured ratio to5.9306:1, above the existing4.5
threshold. The native1px ring remains unchanged. This is selected-text CSS colour
measurement, not complete accessibility certification. A mistaken anchored grep
selected zero tests in an earlier attempt; that setup failure is separate.

The final12 journeys inspect six actual stored definitions/results: pass, fail,
indeterminate, numeric metric and evaluation error remain distinct. They cover
native selection/exact-data disclosure, explicit refresh, HTTP refusal and actual
retry, foreign-result identity refusal, newer focus, a newer source dialog and
departure during a held actual read. The ordinary backend has no registered
Autoverse mapping: support is correctly unsupported and new evaluation stays
disabled. Historical results remain readable; no new evaluator admission is
invented. The19 older cases retain their distinct no-definition recording,
labelled display fixture and response-counterexample scopes.

Both final cohorts preserve original database/recording bytes, copied canonical
bytes and execution ledgers. Backend/browser handles exit, roots release and all
21/16 captured descendant pidfds exit, with zero capture races or observed GPU
descriptors at readable capture time. Short-lived children may be missed; no
general GPU-health claim follows. CPU/minimal-device browser isolation is optional
contributor tooling. No live Autoverse provider, model or new evaluation is started.

The initial native prerequisite audit wrongly expected supported evaluation without
an installed provider mapping and failed. A fresh diagnostic instead observes valid
snapshot integrity, six definitions/six stored results and the actual unsupported
reason, while preserving source/copy bytes and releasing its root. This is retained
as preparation history, not a passing new-evaluation case.

Sixty-five source artifacts retain original/derived hashes. Public derivatives
replace operator/tool/workspace paths and loopback origins and normalize trailing
whitespace;14 private session values are absent. Raw screenshots/credentials stay
private. See [verification](verification.json), [measurements](disclosure-measurements.json),
[review](review.md) and [remaining coverage](coverage.json).

Counts remain72 completed /18 in progress /10 blocked; zero accepted milestones.
T038/T097 stay open. Fresh registered mapping/evaluation submission, other added
flows, actual AT and required-host acceptance remain unverified. Windows stays
separately frozen; the full original goal remains active.
