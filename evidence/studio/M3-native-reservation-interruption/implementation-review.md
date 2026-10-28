# Interruption implementation review

This is a component implementation self-review, not the independent milestone
acceptance review. The existing reservation backend, original fixture and existing
tests remain byte-identical; two new test source files add controlled timing and
native process coverage. The earlier volatile-provider test is reused unchanged.

The fixture pause only intercepts the selected reserve operation before calling
the original store method, or waits after the original provider's actual effect.
It does not replace routes, forge persisted operation/lease rows, change request
payloads or install a provider through HTTP/project data. The server retains its
allocated loopback socket. Test sessions use the actual bootstrap, Origin and
CSRF boundary. Server-owned policy grants only observe scope.

The controller establishes the expected committed state before SIGKILL, rather
than inferring a crash point from elapsed sleep or marker existence alone. The
marker identifies the timing hook; a separate read-only SQLite observation proves
the accepted/delegated operation and missing/unknown/owned lease state. The exact
original child UID, parent, argv and birth identity must still match before the
signal. All live children receive guarded cleanup after a failed assertion.

The JSON effect record belongs to the fixture provider and is written by its
normal reserve callback before acknowledgement. Reloading that fixture state
simulates continuity across backend death. The backend can recover owned state
only through explicit inspection of the original recorded fence. A provider's
unrecorded fence is not silently adopted. Original operation identity, immutable
historical uncertainty and current ownership remain separate. Byte-identical
effect files and zero post-restart reserve calls prove no fixture reacquisition.

All 107 focused tests pass with 319 selected inputs unchanged before/after. The
first post-completion manifest's misleading timing label is retained with an
explicit correction; only the final controller supplies the freeze claim. The
same 315 browser inputs remain unchanged by this supplement. The additional
three Python sources and CI workflow budget have their own hash amendment; no
retroactive browser freeze or full 1073-test backend success is claimed.

The whole-job CI budget changes separately from 75 to 120 minutes after the
published PR job hit GitHub's recorded 75-minute maximum following all 508 browser
passes. Package smoke was skipped by cancellation. Application timeouts, test
assertions and performance thresholds stay unchanged; the new job budget has not
yet executed remotely. The original cancelled outcome remains recorded.

The five native fixture cases do not complete physical command authorization,
automatic run renewal, ownership-loss policy, external provider/device recovery,
native Windows, actual physical cleanup or full milestone acceptance. T073/T074
stay open; no reservation-scope result is promoted into active-command authority.
