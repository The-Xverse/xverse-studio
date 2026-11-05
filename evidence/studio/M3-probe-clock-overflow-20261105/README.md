# Observation clock overflow — scoped Linux verification

Source candidate: `a92f42e`. ADR-0070; partial T075. All 59 selected authenticated
ASGI checks pass: 18 new failure cases and 41 unchanged existing observation cases.
There are no failures, errors or skips. All 551 selected inputs are Git-bound and
unchanged throughout final verification. Six prior UI assets remain unchanged;
there is no new browser execution claim.

The original candidate reproduced 12 HTTP500s and six wrongly generic diagnostics
across two counterexample cohorts. Oversized backend/stored clock integers now
take the existing typed failure path. Provider uncertainty is an invalid response;
known clock failure survives delegation. Tests preserve original receipts and
corrupt stored bytes, forbid replay, and check that no active authority appears.
Controlled clocks/store corruption are owned fixtures, not an assertion that an
HTTP caller can control the host clock or edit storage.

The initial repaired 59-case cohort is retained separately. The final committed
candidate passes targeted lint/format, architecture boundaries, planning-package
validation and the 59-case cohort. A Starlette/httpx deprecation warning remains;
no dependency change is included. Raw XML and fixture stores stay private; public
case records, commands, outputs, versions, digests and attempt counts are retained.

Review: the change retains exact numeric type checks, catches only conversion
overflow, and adds the existing clock diagnostic to the worker's closed allowlist.
It does not coerce source tick strings, fabricate time, change endpoints, grant
permissions or repair historical records. Before-contact failure contacts no
callback; after-contact failure retains an unknown result and original receipt.
Existing HTTP tests are byte-identical; new assertion ASTs match the red cohort.
No further finding requires repair within this scoped change.

These checks use owned in-process callbacks on Linux, with no equipment, external
provider, workload, simulator or native server. No Windows tests/implementation,
full regression, browser, package, performance, hardware or milestone acceptance
is claimed. T073/T074 still require an admitted physical-command/runtime contract;
T075 remains incomplete. Counts stay **71 completed /19 in progress /10 blocked**,
with zero accepted milestones and zero new task closures.

The user requested stopping after this current task. Verification is finished;
retain the evidence and pause all work until explicit user resume. The independent
Windows freeze remains active until explicitly lifted.
