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
