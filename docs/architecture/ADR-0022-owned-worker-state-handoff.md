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
