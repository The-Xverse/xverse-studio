# T048 Linux exchange review

Reviewed T048's complete amended scope and its completed T043/T044/T046/T047
dependencies. This adds native exchange verification to existing implementation;
no product code or task definition changes.

| Task clause | Evidence |
| --- | --- |
| Round-trip, layout, conflicts and failed-edit recovery | All 17 current actual CLI/library and HTTP round-trip cases pass, including the two explicit missing-dependency corpus cases. They compare source/digest differences, preserve layout-only identity, reject stale writers/failed edits and restore earlier exact source as a new revision. |
| Exchange between isolated native Linux workspaces | Two new cases launch actual native backend subprocesses over localhost HTTP, using separate source and target data roots. Each target is stopped and reopened. Original process handles stop all six final-run launchers. No TestClient server, remote backend or container substitutes for them. |
| Spaces, Unicode and line endings | Both data roots and a source filename contain spaces/Unicode. Exact CRLF bytes survive archive exchange; a later LF save and native reopen preserve the supported reference's exact compiled plan. The actual isolated pinned CLI emits that same plan. |
| Host-specific bindings and identity | An original-root session returns401 in the target root. Private root material is absent from the portable archive and remains unchanged; new envelope IDs preserve XDL identities and opaque metadata. A declared physical binding remains preserved and blocked with the same compiler/CLI diagnostic, before workload dispatch or any provider installation. |

The first run retains one pass/one fail: the test incorrectly expected the
selected Phase1 compiler to emit a physical executable plan. The authoritative
`XDL1-PLAN-REALIZATION-UNSUPPORTED` result is correct. The pre-repair review records
that finding; the repaired test compares its explicit rejection and null plan,
while executable-plan equivalence applies to the supported reference case.

Final result: **19 passed, zero failures/errors/skips**, 45.63s. All prior 401
input hashes remain identical; only the native exchange test is added. Commands,
case ledgers and 402 current source hashes are retained here. The initial failed
attempt used pytest's default temporary root; the final execution explicitly uses
the project-local selected filesystem.

T048's Linux component can close. AC-002 as a whole, M2 acceptance, actual physical
admission, live-industry substitution and human study remain separate obligations.
This proves no native Windows, physical execution or every-message trace capability.
