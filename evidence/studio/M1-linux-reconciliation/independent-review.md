# T023 Linux partial audit — 2026-10-26

A separate read-only agent inspected the current code/tests; it executed no tests in this audit.
The full Linux verification is recorded separately. T023 stays **in progress**.

Existing executable coverage:

- `tests/platform/test_native_recovery.py::test_native_backend_crash_reconcile_and_clean_shutdown`
  kills the owned backend, verifies its worker survives with unchanged birth identity, restarts
  against persisted storage, retains one run and the original Start receipt, then cancels and checks
  stopped state and complete cleanup.
- `tests/contract/test_review_regressions.py::test_post_spawn_lost_birth_is_unknown_then_recovers_one_exact_owned_worker`
  injects AccessDenied after an actual spawn, preserves uncertainty, recovers the exact worker and
  verifies one launch.
- The same file's `test_reconciliation_does_not_adopt_a_matching_pid_with_wrong_argv` cases reject
  misleading command lines despite a matching synthetic PID/birth.
- `tests/contract/test_run_events.py::test_pending_command_becomes_unknown_when_ownership_is_lost`
  alters persisted birth identity and checks unknown lifecycle, cleanup and pending-command outcome.
- Its `test_accepted_command_fails_when_owned_workload_fails_first` and
  `test_accepted_command_that_never_reaches_worker_reconciles_failed` distinguish lifecycle from
  cleanup and unapplied commands without rewriting evidence.
- `tests/integration/test_recorded_replay_and_rerun.py::test_restart_unknown_dispatch_never_replays_start`
  forbids replay after unknown dispatch.

Remaining direct Linux test gaps identified by the audit:

1. Matching persisted run/worker state but a different *current* process birth time (live PID reuse).
2. NoSuchProcess/AccessDenied while inspecting identity during later reconciliation, rather than
   only the initial launch acknowledgement.
3. Explicit regression that unknown ownership prevents shutdown command delegation.

The implementation guards these branches, but inspection alone is not execution evidence. Native
Windows installation/testing remains held at user request and cannot be inferred from Linux.
