# Native reservation restart review

This supplement addresses T073/T074 interruption evidence without changing the
application or provider fixture. It is an implementation self-review, not a
replacement for the separate independent milestone acceptance review.

The two permanent cases use actual configured HTTP, authentication, CSRF, durable
operation/lease storage, a native server process and normal same-root startup.
Before SIGKILL, the exact child UID, parent, argv and Linux process birth identity
must still match the recorded owned process. All remaining live children receive
owned cleanup on test failure. Each host retains its allocated listening socket.
No imported endpoint, user command, driver or physical resource is contacted.

Recovered lease state and historical receipt state are checked independently.
The original completed receipt cannot enable current ownership: the restored
lease is unknown, renewal refuses, and an explicit same-reservation inspection
cannot reacquire it. The restarted provider observation proves zero reserve,
renew, release or stop callbacks, while admitting the three actual inventory
binding checks. Both scenarios create no run and retain unavailable runtime
admission. The deliberately killed host has no normal shutdown observer record;
only the restarted host's actual required record supplies callback evidence.

The initial private client-context misuse failed before acquisition. A later
private probe expected one inventory read, but the actual wrapper checks the
binding before uncertain renewal refusal and twice around reconciliation. That
expectation was corrected to the exact four-call list after inspecting the source;
the original failure, source and amendment remain retained. No application edit
was needed. The new permanent tests pass separately from the published backend
suite. Their final whitespace formatting preserves the exact tested Python AST.

All 159 selected published backend/fixture/lock bytes and all 315 ongoing browser
verification inputs remain exact. The one new Python-only test source has its own
hash, two-case pytest report and formatting amendment; it is not retroactively
included in the browser freeze or a claimed full 1070-test backend run.

The volatile provider dictionary dies with the backend, so these cases establish
conservative provider-state loss handling. They do not establish persistent
external-provider recovery, crash during delegation/final receipt persistence,
automatic active-run renewal, admitted stop policy, physical cleanup, native
Windows or hardware acceptance. T073/T074 and all milestone gates remain open.

Final-source follow-up: both permanent pytest scenarios pass again on the exact
formatted test source (zero failures/skips, one existing framework warning).
The fresh final XML, actual native process observations and source hash are
retained separately; the first two passes and formatting proof stay historical.
No fresh full1070 backend execution or broader acceptance is claimed.
