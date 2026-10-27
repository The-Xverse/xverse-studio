# ADR-0020 — Frozen campaign preview and retained history

Status: implementation in progress; acceptance unproven.
Date: 2026-10-27.

T090/FR-058 require finite preview, explicit budgets and stop policy, immutable
child identities and retained history. The existing backend already owns expansion,
durable child claims, admission, cancellation and restart reconciliation. The old
browser uses a local cardinality estimate, fixes the policy to continue and loses
access to the selected campaign after leaving the view.

Expose additive `campaignVersion: "1.0"` and `baseInput` presentation fields on
the existing preview/list/detail responses. Verify the retained base snapshot,
its campaign identity digest and its managed immutable bytes before reporting its
project/revision, selected System/Deployment/Scenario, provider and snapshot digest.
Failed verification reports unavailable provenance; child scheduling states remain
visible. Inspection never repairs a record or advances the scheduler. Paginate before
verifying list rows. Canonical stored campaigns, snapshots and evaluator contracts
are unchanged. HTTP major v1 remains unchanged.

Move campaign presentation to a feature component. Read authoritative preview before
creation; expose run/time budgets, advertised concurrency and stop policy. Retry an
unchanged request with its original idempotency key. A separately explicit new request
requires a new preview. Editing a later form cannot change an accepted submission.
Bound response shape, read deadlines, history pages and child input inspection.
Read-only polling never schedules, replays or retries a child. Unknown dispatch is
left to backend reconciliation. Cancellation acceptance, child state, cleanup and
assertion verdict remain separate.

Workspace history identifies each frozen project. Current drafts never supply a
retained campaign's provenance; cancellation from a different project or unverified
base is disabled in presentation and backend ownership remains authoritative.
An explicit child inspection reads its existing run and protected snapshot and
checks campaign/child/parent identity and actual parameter values before display.
No provider API, arbitrary seed execution, reservation or physical authority is added.

Verify actual native owned campaigns at 1024×768 and 1440×900, preview without
allocation, budget refusals, immutable children, retained reopen, cancellation,
failure policy, idempotent retries and late acknowledgements. Label transport/failure
fixtures. Native Windows, actual assistive technology and full AC-028 remain separate
gates. Keep task IDs and full M0–M4 acceptance scope intact.

Native worker-failure verification amendment: the unmodified owned worker now has
a Linux-only controlled failure regression. After an actual sample, the test checks
the exact Popen child, PID/birth, launch-argument digest and persisted owner, observes
its declared sleep point, and delivers SIGINT to that single owned PID. It never
changes worker arguments, provider descriptors, protected snapshots or journal bytes.
The worker records its own failed/partial/unknown-cleanup outcome and exits with 1.
Its journal remains an append-only verified prefix, not sealed complete evidence.

With stop_on_failure the pending child is cancelled without a Start. With continue
the next child receives current admission and executes normally. Campaign-operation
completion reports coordination completion; it does not replace failed child state,
unknown cleanup, partial evidence or an unevaluated assertion verdict. Same-key
creation retry and repeated inspection cannot allocate another child or rewrite
the failed worker's terminal journal. Base and child snapshot identities stay intact.

The tests use an authenticated in-process HTTP service and actual native workers.
They do not verify native launcher restart, arbitrary failure points, interrupted
journal writes, external/physical providers or native Windows. The Linux fault
fixture requires its observed kernel sleep point; unavailable observations cannot
be substituted with a fake worker. Windows remains a separate held lane. No product
API, provider operation, OS requirement or execution authority is added.

Native delegation-recovery conformance amendment (2026-10-27):
`tests/platform/test_campaign_delegation_recovery.py` embeds a bounded test-only
backend pause after real Start returns and before campaign acknowledgement. The
claim is durably dispatching without its run ID while the existing Start receipt
and actual unchanged reference worker are verified. This is explicit initial-backend
instrumentation, not a product hook or an uninstrumented timing observation.

The test kills only its owned backend after process-birth validation; the successor
uses the ordinary native launcher. Four Linux cases cover an original worker still
running, already normally complete, and failed after an owner/PID/birth/argv and
kernel-sleep-verified SIGINT under continue and stop_on_failure. Recovery must retain
the original child/run/worker identities, schedule only pending work, preserve the
canonical base/child snapshots and Project, and deduplicate repeated same-key retries.
The failed worker's own unknown cleanup, partial prefix-verified evidence and null
verdict remain distinct from campaign coordination. Its journal sequence/digest chain
and immutable terminal bytes are checked independently. No stored record, worker
code, argv, owner file or canonical journal is rewritten to force the fault.

These cases make the retained supplemental probes repeatable in the backend suite.
The tested prototype passed four cases; main-candidate verification is a separate
required result. Initial-backend pause and Linux-only kernel/process scope remain
explicit. Arbitrary interruption points, mid-journal writes, native Windows, live
external/physical providers and full task/milestone acceptance remain separate gates.
