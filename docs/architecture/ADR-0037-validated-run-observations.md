# ADR-0037: Validate persisted ownership observations before promotion

Status: implemented and verified for the Linux reconciliation component. Applies to T023's existing Studio
provider-state reconciliation, on the Linux scope of ADR-0036.

## Decision

Treat a decoded provider state file as a report to inspect before promoting its
fields into run or operation metadata. Require an object with a known lifecycle,
nonnegative integer `stateVersion`, positive integer PID, finite nonnegative
process birth time and nonempty owner identity. Reject Boolean numeric identities.
If present, cleanup/evidence outcomes must be known string values, and command
results must be objects with string status fields. Existing admitted platform
evidence `available` remains an availability fact, independent of complete evidence.
Opaque additional report/result fields remain intact; these shape checks confer
no authority and do not replace original PID/birth/argv/task/owner comparisons.

Before any metadata promotion, a reported result naming an existing Studio
operation must identify an original non-Start command accepted for this run.
Unknown provider-only receipt IDs remain opaque and create no ledger row; they
do not invalidate independently verified lifecycle facts. Reserved accepted operation,
run, kind, principal, parameter and expected-version fields cannot be changed by
a result; compare their canonical JSON identity rather than Python numeric
equality. Preserve additional provider result metadata. Existing Studio command
results use the same six v1 statuses as RunControls: accepted, delegated, completed,
rejected, failed and unknown. Cancel is an operation kind, not an extra receipt
status; other operation families have their own vocabularies. Provider-only status
values remain opaque. Require finite UTF-8 JSON
before SQLite serialization, so a malformed nested value cannot partially promote
state or receipts. An unresolved pending command becomes unknown without a usable
report even when an earlier lifecycle observation is already terminal.

A report cannot lower the verified lifecycle version or reopen an already
terminal lifecycle. Reject such observations before process inspection or control
admission; preserve the recorded version and terminal facts. No lifecycle reset
is currently admitted. A future reset capability needs its explicit transition
contract rather than silently treating an old report as a new execution.

Use the same checks on the initial read and the existing terminal reacquisition.
Malformed JSON, excessive decoder nesting or invalid known fields yield no new
admissible observation. Existing active ownership becomes `unknown` with partial
evidence under the current policy; pending commands remain unknown and cannot be
delegated. Already committed terminal facts and completed receipts are preserved.
The existing initial-report grace applies only when that report is absent. A
present malformed or mismatched report cannot inherit it, even during preparing.

Terminal lifecycle alone does not finish its producer or settle an unreported
command. Keep an accepted/delegated result pending while its original task/process
handle is alive. When completion is verified through that handle or the recorded
native process identity, reacquire the final report and inspect its exact original
command result before deriving an unexecuted fallback. A lost backend task handle
cannot use its parent PID as completion evidence. Unreadable final reports or
uncertain producer completion leave the command unknown, while known termination
and cleanup facts remain separately visible. Never re-deliver a settled command.
An exited producer reporting only accepted/delegated progress leaves an unknown
outcome. Progress entries cannot downgrade already known receipts or resolve an
unknown outcome. Repeated unchanged inspection performs no operation metadata
write; original source progress stays available in the unmodified report.
The original state, snapshot, request and canonical evidence bytes are never
rewritten to repair a report. Restoring the original valid report may permit the
existing identity-aware reconciliation; no restart, new dispatch or permit follows.

This is a fail-closed inspection repair of the existing private report envelope,
not a new platform entry point, execution API, ownership grant or physical permit.
No database, historical run or provider implementation identity is migrated.

## Implementation allocation

Retain the existing `runs/service.py` ownership facade and its provider boundary.
Reconciliation is implemented by `Runs.read`, terminal reacquisition and command
inspection there; `providers/worker.py` retains actual reference resource release,
and `host/launcher.py` retains native foreground ownership/shutdown. The original
T023 `runs/reconcile.py`/`runs/cleanup.py` paths were planned module targets. Record
these actual delivery paths in its trace rather than duplicate cleanup authority
or move provider-owned release into the control service. Requirements, task ID,
dependencies and acceptance obligations remain unchanged.

## Verification

Controlled corruption cases first exercise the original failure through actual
authenticated API requests without contacting any real PID. Repeat valid native
reference/backend-task lifecycle, restart and terminal-reacquisition checks after
repair. Distinguish those native observations from controlled report fixtures.
Retain original failures and exact source bindings. The historical transient
late-Stop result-code mismatch remains a separate unresolved observation; this
repair must not claim to reconstruct its missing original interleaving.
