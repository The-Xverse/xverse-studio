# Restart reconciliation — T023 Linux-only partial evidence

T023 remains open. The existing native crash/restart and contract tests identified in
`independent-review.md` were included in the unchanged-source full Linux run: 776 tests passed with
no failures or skips. The exact command, application/test hashes, environment and raw result are in
`../M3-physical-contracts/verification.json`, `application-source-hashes.json`, `environment.json` and
`backend.txt`. That cohort predates only the added two-viewport browser test; backend source and
these recovery tests are unchanged.

The separate audit executed no tests; it mapped actual test assertions to task clauses and identified
three remaining direct Linux regression gaps. Those gaps and the held native Windows lane prevent
closure. A persisted identity mismatch test is not described as actual operating-system PID reuse.
No unrelated process, device or port was targeted.
