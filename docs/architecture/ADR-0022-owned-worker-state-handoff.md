# ADR-0022 — Owned worker launch and terminal observation

Status: implementation in progress; complete task and milestone acceptance unproven.
Date: 2026-10-27.

FR-013/FR-014, T023/T025/T026 and AC-007/AC-008/AC-009 require durable
ownership reconciliation without blind restart or guessed process authority.
During comparison/history verification, actual owned-reference workers were
reported unknown before eventual successful termination. Source review and
explicit regressions identified two observation defects. Preparation before
native launch consumed the existing five-second initial-observation window.
Separately, reading a running state immediately before the worker's final atomic
state replacement and exit could discard the now-available terminal observation.

Record `launchStartedAt` immediately after `Popen` acknowledges the admitted
argument-vector launch. Apply the existing five-second preparing window from
that timestamp, falling back to `createdAt` for older records. Persisted request
creation and actual launch remain separate facts. The existing PID/process-birth
acknowledgement remains in place; no new process discovery or adoption path is
introduced. Startup beyond the window and lost identity still become unknown.

When an identity-matched nonterminal observation encounters a missing/exited or
zombie process, reacquire the worker state file once. Accept only a stopped/failed
state with the same nonempty owner digest, PID and process birth already recorded
by the backend. Missing, malformed, nonterminal or mismatched replacement state
remains unknown. A reused process birth or access-denied observation cannot use
this fallback. The read creates no process, sends no signal and writes no command.
Existing canonical journal verification still determines evidence quality;
terminal lifecycle does not imply complete or valid evidence.

Compatibility is additive metadata for owned reference runs. No XDL identities,
worker/provider implementation, external runtime contract, execution permits,
command semantics, caller deadlines or performance thresholds change. Windows
uses the same portable control code but requires independent native verification;
these tests cannot establish Windows or external/physical-provider acceptance.

Verify actual native workers after an explicitly injected preparation delay and
after exact owned-child exit with one explicitly stale file read. Retain the
initial fixture error separately from the corrected red reproductions. Add
negative file/process fixtures for owner/PID/birth changes and omissions,
nonterminal/malformed/disappeared files, denied access and PID reuse. Rerun
existing restart/crash, command, campaign, history and comparison checks, followed
by fresh full backend/browser and performance verification on frozen inputs.

## Startup rejection identity amendment — 2026-10-28

An owned worker can reject effective-input equality before opening its journal or
starting the workload. Its terminal rejection must carry the same PID, process
birth and owner digest as other worker observations. Without those fields, the
backend correctly refuses to adopt the record and eventually reports ownership
unknown, losing the available startup-failure fact.

The rejection now records those identity fields and its actual terminal receipt
time. It reports no workload start time or effective execution identities. No
journal is invented; evidence remains unavailable. The existing backend identity
checks and authoritative snapshot validation remain unchanged. The worker bytes
and therefore its existing implementation digest change; earlier preflights do
not gain admission to the successor implementation.

The browser presents reported startup separately from execution, cleanup,
evidence and verdict. A recorded start followed by failure is distinguished from
explicit launch/effective-input rejection. Missing history and uncertain ownership
remain unknown. These facts grant no controls or physical-state assurance.

Native regression faults only the private delegated request copy after normal
admission. Canonical Project/snapshot bytes remain unchanged, and the real worker
uses its original argument vector. Browser fixtures additionally label injected
launch refusal, actual ownership-verified Linux SIGINT after a sample, and normal
Stop. Neither fixture results nor this repair establish Windows, live-provider or
milestone acceptance.
### Resolved ownership diagnosis

After the existing PID/birth/owner checks establish a trusted worker observation,
the mutable run projection removes a prior `OWNERSHIP_UNKNOWN` or
`LAUNCH_ACKNOWLEDGEMENT_LOST` reason when the worker reports no current reason.
An explicitly unknown/reconciling worker projection cannot clear that diagnosis.
The worker lifecycle, cleanup and evidence fields already replace those uncertain
projections; retaining an obsolete ownership diagnosis alongside them is misleading.
Worker-reported reasons and every existing ownership/refusal check remain intact.
Two actual native recovery cases inject an OS-observation denial; one separately
labels a durable lost-acknowledgement reason. They verify refusal while unknown,
preservation of an injected reported-unknown observation, recovery of the original
worker, unchanged inputs and subsequent Pause/Cancel.

### Ordered backend observations without changing worker CAS

The worker's `stateVersion` remains authoritative for command comparison and
signed optional transitions. Losing or recovering a backend observation cannot
increment that worker-owned version. Run metadata therefore carries a separate
durable `observationVersion`, initialized to zero for new runs and advanced only
when reconciliation or a dispatch handoff needs to persist changed metadata. Legacy records
are not rewritten merely to initialize it. Stable reads still perform no writes.

At the same worker lifecycle version, the browser accepts a newer complete
observation, including removal of obsolete optional reasons, and refuses an older
observation. Different run/snapshot identities and older worker versions remain
refused. Legacy responses retain their existing conservative merge behavior;
they cannot overwrite an already ordered modern observation. This counter grants
no command, process or physical authority. Native denial/recovery and browser
polling tests retain the same worker version and immutable run identities.

### Accepted preparation failures and dispatch observations

Start acceptance is durable before the backend prepares its private run files.
An I/O failure creating the run directory, owner key, delegated request or worker
temporary directory now settles that same run and Start operation atomically as
`PREPARATION_FAILED`. No native launch was attempted, no workload start or journal
is invented, and runtime cleanup is complete because no runtime resources were
created. Partial private preparation files remain available for inspection. This
classification does not claim that storage is healthy or erase those files.
The ordinary Start receipt remains retryable with its original identity; removing
the fault never replays that accepted request. A new request needs a fresh review.

The existing native-launch failure path retains its distinct `LAUNCH_FAILED` and
unknown-cleanup outcome. Metadata persistence errors propagate; recording the run
and operation outcome in one transaction prevents a partially settled failure.

Preparation, launch and acknowledgement may overlap a run read. Each dispatch
handoff merges only its own new facts into the latest stored record and advances
the independent observation order in the same transaction. A late parent
acknowledgement therefore preserves a worker state/start/effective identity that
a read has already verified, along with a completed Start operation. This changes
no worker lifecycle version, command CAS, process adoption check, executable input
or native launch argument. Actual owned-worker interleaving tests distinguish
these boundaries from labelled I/O failures and presentation fixtures.

A completed or failed Start receipt is a historical outcome. A later parent-side
observation failure cannot regress it to unknown. When an earlier read has already
verified a terminal report with recorded PID, birth and owner identity matching
the parent's exact `Popen` child, a late missing-process acknowledgement also
preserves that terminal lifecycle and cleanup report. No new process identity is
adopted through this exception. A denied observation of a still-running worker
continues to make current ownership/cleanup unknown and blocks controls, while
the earlier confirmed Start remains completed. Native tests exercise both cases
with the original worker and verify the denied live control request.

### Journal opening and finalization failures

The owned worker creates its canonical journal before reporting a workload start.
An opening failure reports `EVIDENCE_OPEN_FAILED` with its trusted PID/birth/owner
identity, failed startup, the separately observed cleanup outcome and unavailable evidence. No
start time or effective execution identity is invented. Exclusive creation stays
in place: an existing journal is preserved rather than truncated or replaced.

Once model execution has stopped and its cleanup outcome is recorded, a failure in
evidence flush, synchronization, digest acquisition, close or final publication
does not undo those independent facts. The worker retains stopped lifecycle and the recorded cleanup outcome,
marks evidence partial and reports `EVIDENCE_FINALIZATION_FAILED` separately in
`evidenceFailure`. An existing termination reason, such as pause-budget exhaustion,
is preserved. Unpublished journal-completion markers are removed. The backend
still verifies the actual canonical source; an unsafe source stays invalid and
retained bytes at another private path are not silently substituted.

A failed journal append cannot prevent a separate terminal-state write. If that
write also fails, the backend retains its existing ownership uncertainty. Active
workload failures continue to report failed execution and unknown cleanup. No
exception is converted to functional success, and no imported command or private
platform API is introduced. Only the owned reference implementation digest changes;
source clock encodings, declared capabilities and external admission stay fixed.

Native Linux tests obstruct only their own journal path. One faults opening; one
retains an already-open journal under another owned name before obstructing its
original path, then verifies its unchanged prefix and complete hash chain after
the real worker exits. Browser fixtures use the same unmodified worker argv and
verify PID/birth/owner before the latter fault. These are filesystem failures,
not physical-provider cleanup or native Windows acceptance.

### Owned temporary-resource release

The backend already creates a private per-run temporary directory and supplies it
as the worker's `TMPDIR`, `TEMP` and `TMP`. The worker now observes that directory's
device/inode identity before compilation. A symlink, reparse point or unavailable
identity is not adopted. After the model stops, or a known startup rejection, it
attempts one `rmdir` of the same observed empty directory. It never enumerates or
recursively deletes its contents, follows a replacement link, or touches another
run's data. This is reference-provider resource management, not a new XDL resource
or a physical-provider release operation.

A failed release with the original identity still observable reports
`cleanup=failed`. Changed, missing or unobservable identity reports
`cleanup=unknown` and withholds deletion. Both carry one bounded `cleanupResources`
entry with a logical resource ID, kind, status and stable code; host paths and
retained file contents are excluded. A confirmed release reports an empty list.
The trusted state report and canonical `cleanup.updated` event retain the same
outcome. The backend copies that report through the existing ownership checks;
the browser and diagnostics identify the unresolved resource for inspection.
There is no automatic cleanup retry or new cleanup endpoint.

Model termination, command application, cleanup and journal integrity remain
separate. A Stop/Cancel applied to the model may complete while cleanup fails.
Healthy journal finalization can still be complete in that case. A concurrent
finalization error preserves failed/unknown cleanup and marks evidence partial;
an interrupted cleanup retains stopped model lifecycle with unknown release.
The worker exits nonzero for an unresolved release. Snapshot/project bytes,
worker CAS, native command authority, source clocks, limits and external runtime
admission remain unchanged; only the owned implementation digest changes.

Native Linux tests exercise empty release, retained bytes after Stop/Cancel or
duration completion, symlink/directory replacement, a missing adopted directory,
and concurrent journal-finalization failure. Retained and unrelated bytes remain
unchanged. These tests do not establish native Windows or physical cleanup.
