# Native lifecycle conformance review — 2026-10-30

Candidate `f17b29482deac85ac576640a2bf55e5b72857b2c` completes the original T021 test clauses. Three actual
Autoverse executions pass: complete-demo backend restart and natural completion,
startup cancellation, and actual CARLA loss during partial startup. The full
mapping is in [clause-audit.json](clause-audit.json). Counts are **61 completed,
29 in progress and 10 blocked**; zero milestones are accepted.

Concurrent initial Start requests and retries return one receipt. Changed bodies
conflict; the same receipt survives backend restart and terminal retry. A separate
active duration 31 draft changes the authoritative plan while the actual worker
retains its frozen duration 30 source and plan. Unsupported controls create no
mailbox or operation. Temporary loss of the mutable report's owner identity yields
unknown state/cleanup and blocks Stop, then exact report restoration resumes the
same original observation. The brief test-only worker suspension does not pause
the simulator or grant a Pause capability. Canonical journals are never rewritten.

The original backend is killed through its native child handle. The replacement
backend reconciles the same original worker/run; a same-key Start never respawns.
Fresh enrollment is honestly unavailable while the existing demo resources run.
The original worker finishes naturally, with valid journal integrity, available
evidence and no functional verdict. Startup cancellation never reaches running;
actual component loss produces failed lifecycle and partial evidence with confirmed
cleanup. Neither negative is complete-demo success. Twenty-two recorded component
process instances and three workers exit; four backend launch instances are absent,
three exact containers are stopped and all three root locks release. Independent
readback verifies original source/effective plans, snapshot/journal digests, native
resources and actual ledger counts. All 449 committed inputs, 6 UI assets and 21
original platform evidence files remain unchanged.

The first restart attempt exposed a test-driver error: it checked second-child
identity immediately and then reused stale first-owner facts during failed cleanup.
The individual failed identity field was not captured, so its transient cause is
not reconstructed. That attempt remains failed. Its original worker later completed
and all resources/root lock were independently verified released without guessed
signals. The successor retains each new original child before acknowledgement and
waits boundedly for full native identity agreement. Both a normal crash/restart
guard and an intentionally failed acknowledgement guard verify cleanup. The first
readback inspector also expected source content in metadata; its KeyError is retained
and corrected to anchored, digest-checked native revision files. No demo is replayed
for that readback correction. All phases are qualified, never summed or hidden.

Application/runtime/UI code is unchanged; the prior 427 Autoverse API/native CLI and
8 browser checks are inherited through 448 unchanged inputs and 6 UI assets, not
rerun or presented as new executions. No new package, Pygame, standalone Lite,
whole-platform, physical or second-industry execution is claimed. The T011-only
reference exception is not extended. Current review/readback is a self-review,
not a new independent milestone review. T025 browser reconnection, T033's full
fixture guided matrix, human and external acceptance remain separately open.
