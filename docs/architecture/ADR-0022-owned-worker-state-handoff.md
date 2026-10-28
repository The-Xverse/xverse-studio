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
when reconciliation already needs to persist changed metadata. Legacy records
are not rewritten merely to initialize it. Stable reads still perform no writes.

At the same worker lifecycle version, the browser accepts a newer complete
observation, including removal of obsolete optional reasons, and refuses an older
observation. Different run/snapshot identities and older worker versions remain
refused. Legacy responses retain their existing conservative merge behavior;
they cannot overwrite an already ordered modern observation. This counter grants
no command, process or physical authority. Native denial/recovery and browser
polling tests retain the same worker version and immutable run identities.
