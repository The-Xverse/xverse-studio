# T023 Linux reconciliation component review

Scope is the complete T023 component under ADR-0036, with original T022 dependency,
requirements FR-013/FR-014/NFR-005 and AC-007/008/009 retained. This primary-agent
review is not independent milestone acceptance. Final results are recorded in
verification.json; a result is not inferred from this matrix.

| Existing task clause | Implementation and executed evidence |
| --- | --- |
| Restart reconciliation without blind respawn | `Runs.read` observes persisted original identities. Actual native backend crash/restart tests retain the original worker, one run, the same Start receipt and immutable snapshot. Native pre-launch acceptance crash tests preserve unknown intent without dispatch replay. The separate recorded-rerun regression forbids replay of unknown dispatch. |
| Ownership-verified cleanup | Provider worker owns release of its original temporary directory. Eight worker cleanup cases exercise actual owned children and resource retention/replacement. Three Linux x86-64 ptrace cases deliver real SIGINT at the verified original rmdir boundary for duration/Stop/Cancel. No release is inferred from lifecycle termination. |
| Uncertain ownership and cleanup separate from termination | Known stopped lifecycle remains stopped when cleanup is unknown; unresolved resource identity and partial evidence remain explicit. Controlled later PID reuse/missing/denied inspection rejects mutations and shutdown delegation. Native cleanup obstruction/interruption cases verify actual distinct outcomes. |
| Native original handles, PID reuse and lost handles | Fifteen process-identity fault cases replace OS observations before lookup; these are labelled fixtures, not actual kernel PID reuse. Actual lost-birth acknowledgement recovery keeps one native child. Two wrong-argv controls reject false adoption. Native backend/task tests use original Popen/task handles; a lost backend task handle cannot use parent-PID liveness as task completion. |
| Reconcile uncertain command outcomes | Authenticated corruption cases reject malformed, stale or foreign-owner reports before promotion, including present-invalid startup reports. Accepted operation identities and canonical parameter fingerprints cannot be rebound. Provider-only maintenance receipts stay opaque. Actual owned reporter threads prove terminal lifecycle can precede cleanup/result completion; final receipts are reacquired only after producer completion, with repeated owner/version/state checks. Unresolved outcomes stay unknown and no command is resent. |
| Browser disconnection does not own execution | Existing native backend recovery and control paths retain process ownership independently of UI. Sixteen native browser startup/normal Stop/active failure/preparation/evidence/cleanup fault journeys at 1024 and 1440 widths verify the resulting immutable-input and separate-status presentation. The complete cursor/reconnect component remains separately traced to T026; these sixteen cases are not a full browser suite. |
| Read-only recovery and immutable evidence | Tests compare original report/request/snapshot/journal bytes, receipt identity and managed-file inventories. Ten run-read persistence cases retain ownership/integrity inspection while suppressing unchanged metadata writes. Opaque provider receipts create no Studio operation. |

ADR-0037 records actual implementation allocation in `runs/service.py`,
`providers/worker.py` and `host/launcher.py` instead of duplicating cleanup
in the originally planned reconcile.py/cleanup.py modules. Original paths remain
in the task's trace history. No requirement, task ID, dependency or acceptance
scope is removed by that allocation.

All original diagnostic failures remain in the phase ledgers. The first expanded
native cohort's owner-only maintenance-receipt incompatibility was repaired;
unknown provider-only receipt identities/statuses cannot allocate or mutate a
Studio ledger row. The proposed cancelled result status was corrected against
the existing six-value RunControls contract. The final reacquisition negatives
reproduce both stale-version and terminal-state replacement before repair.

The historical late-Stop operation/canonical-code mismatch remains unresolved:
its original raw records were not retained. The new reporter barriers reproduce
a premature/stale-result failure class; they do not identify the old interleaving.
T033's complete runtime fault/live-tuning review remains open. Do not relabel the
old failed run as passed, or infer full live/physical/milestone acceptance.

Windows delivery is outside this release scope; original failures remain historical.
No companion source, provider implementation/SDK, physical permit or running user
demo is changed by this reconciliation repair.

Final current-source results: **124 unique backend cases pass** across125 passing
invocations (one explicit preflight case overlaps the broader owner cohort).
**22 unique browser cases pass**:16 startup/failure cases, three native reconnect
cases on the initial run, and three labelled reconnect/control projection cases
on the corrected isolated root. The initial reconnect run remains3passed/3failed;
all three failures were the helper's correct root restriction, before their
fixture assertions. No test/helper safety rule or product source was relaxed.
All404 selected inputs remain identical across these final stages. Original
113-case and58-case passing observations retain their own earlier source scope.
