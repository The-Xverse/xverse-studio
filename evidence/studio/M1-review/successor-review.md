# M1 successor review

Reviewer `/root/xdl_baseline`; separate from root's repairs. Original findings remain unchanged in
`findings.md`. Date: 2026-10-25. Independent regressions are in
`tests/contract/test_review_regressions.py`; root-owned implementation files were not changed by the
reviewer.

The first successor focused run had nine passing tests and one remaining M0 SQLite-commit failure.
All M1 regression cases passed:

- M1-R01: actual HTTP compilation and preflight reject missing scenario/deployment references and a
  wrong-kind selected reference with `SELECTION_UNRESOLVED`.
- M1-R02: externally changing committed Scenario bytes blocks validation, compilation, preflight and
  export with `REVISION_CONFLICT`, while preserving both source bytes and the recorded revision.
- M1-R03: a real owned reference child is launched with durable owner identity already persisted.
  The parent-side first birth inspection is deliberately denied after Popen; run and operation remain
  `unknown`, and retrying the same key does not launch another child. Subsequent reconciliation
  verifies command line, root and exact creation time and adopts the one actual owned worker. Its
  normal supported cancellation/exit completes; no process-name or arbitrary-PID kill is used.
  A separate fixture proves that matching PID/create-time evidence with the wrong executable argv is
  rejected, retaining unknown ownership. A restart that first occurs only after a birth-unrecorded
  worker has exited remains a separate untested recovery envelope; this live-child test does not
  establish it.
- M1-R04: direct API stop/cancel options reject with `COMMAND_PARAMETERS_UNSUPPORTED` before
  recording a new operation or writing a command file.

The M1 repairs close these specific reviewed root-module boundaries on the native Linux reference
lane. They do not close Windows, Lite, CARLA, hardware, novice usability, performance or full milestone
acceptance. Source identities and final affected-suite results are recorded with the next completed
successor run.

Second successor deepened M1-R03's exact-authority negative. The current recovery check only tests
whether `-m`, the worker module string and the root appear anywhere in argv. An owned fixture with
argv `python -m unrelated_workload <owned-root> xverse_studio.providers.worker` was incorrectly
adopted as running: the expected worker module appeared only as an argument to another module.
`test_reconciliation_does_not_adopt_a_matching_pid_with_wrong_argv[True]` fails. No actual unrelated
process was controlled or killed; the negative uses a declared process-inspection fixture. The
real-child lost-birth recovery test still passes.

M1-R03 remains open for this exact-invocation verification gap. Match the actual admitted invocation
structure (including module flag position, executable identity/compatible resolution and exact root),
not set membership of unrelated argv tokens, before adopting a birth-unrecorded process. The focused
run at this point has **12 passing tests, one failing test**. This finding is recorded before root
repairs the invocation predicate.

Final successor: launch persists a digest of the exact admitted argv before Popen, then uses that same
array to start the worker. Birth recovery compares the entire observed invocation identity rather
than token membership, together with the root-bound owner digest and exact process creation time.
Both wrong-invocation fixtures now reject adoption; real lost-birth recovery still identifies exactly
one owned worker. Native backend kill/restart/reconnect/cancel remains passing.

The final focused review, project persistence and native recovery suite passed **17 tests**. An
exchange-module edit occurred during that run and is reported in its source capture. Only the affected
exchange regressions were repeated on the successor: **11 passed** with all nine reviewed source
identities unchanged. Exact commands/results/hashes are retained in the M0 review's
`final-focused-verification.json` and `final-exchange-successor-verification.json`. The app hook added
for evidence exchange is covered by that affected successor run; runtime ownership code did not
change between those runs.

Current disposition: M1-R01 through M1-R04 are closed for these native Linux reference-provider
boundaries. Native Windows, a birth-unrecorded worker already exited before first recovery, external
live integration, novice usability and complete milestone acceptance are not established by this
focused review.
