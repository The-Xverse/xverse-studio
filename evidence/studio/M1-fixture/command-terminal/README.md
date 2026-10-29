# Native Stop/Cancel terminal boundaries

Ten new actual native Linux worker cases and eight existing command/event
regressions pass: **18 passed, zero failures/errors/skips, 75.21 seconds**.
The [binding](candidate-binding.json) records 389 identical before/after inputs.
All prior 388 inputs and all 116 packaged payloads remain byte-identical to the
published build. This is a tests-only addition; the prior 1,250 backend /92 affected
browser /2 performance results retain their original execution scope. An expanded
full suite, browser rerun and package rebuild were not performed.

Each boundary below runs for both Stop and Cancel using the original worker PID,
birth time, fixed argument vector and owner identity. The worker and clock are
unchanged. Faults affect mailbox delivery, the test-owned process, or one recorded
identity field. No equipment is involved.

| Actual boundary | Verified outcome |
| --- | --- |
| Signed delivery after final sample/command poll | Exactly one canonical `RUN_COMPLETED_BEFORE_COMMAND` failure; natural completion and full sample coverage remain. |
| Signed delivery after original worker exit | Backend `RUN_TERMINAL_BEFORE_COMMAND`; sealed canonical journal unchanged. |
| Held delivery and original-child interruption | Run/command remain `unknown`, cleanup unknown and evidence partial; history is a verified prefix. No replay or respawn. |
| Held delivery and recorded birth mismatch | Controls denied and command unknown even after actual natural completion. Restoring precisely the test-faulted original birth permits normal validation of the original terminal evidence; command then fails unexecuted. This does not demonstrate a user recovery interface or permission to adopt another process. |
| Acceptance held through real exit and intervening reconciliation | Actual reconciliation settles the command before delegation resumes. No mailbox is written and the failure is never reopened. |

All cases preserve frozen snapshot/request/project identity, exact original-key
Start and command receipts, and one run/two operations. The final-poll and post-exit
cases additionally reject payload-changing reuse of the command key. No test
promotes process completion to a functional verdict.

[JUnit](tests.junit.xml), [command/output](run.log), [verification](verification.json),
[native witnesses](native-witnesses.json) and [environment](environment.json) retain
the actual results. Pytest warns about `record_property` with xunit2; all ten JSON
properties are present and separately parsed. The environment recorder enumerates
tracked files; the 389-input maps also bind the then-untracked new test. Only Python
commands executed these tests; its observed default Node installation was unused.

The original four-case execution and exact earlier test source remain under
[history/initial-four](history/initial-four/verification.json). It overlaps the final
ten cases and is not added to the 18-case total. The eight related regressions
include explicitly labelled in-process and evidence fixtures and retain that scope.

T033 stays open for the complete lifecycle/fault/recovery clause review, including
the still-unproved native cleanup-interruption timing. Native Windows remains held;
external Lite, physical, human/AT/SADS and independent gates remain open.
Counts remain **49 completed /41 in progress /10 blocked**, zero accepted milestones.
