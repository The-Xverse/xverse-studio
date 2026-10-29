# Presentation response-handler lifetime

Prior f985 push CI passed 944 backend tests but failed two intercepted presentation
body reads: Apply at 1024 and enum at 1440, with `Response has been disposed` at
`response.text()`. Its full browser result is 472 passed/2 failed and packaging was
not run. The same head's PR job passed 944/full 474/package 104. The exact mixed
receipt and raw-log hashes remain in the native-ci evidence; failed outcomes are
not replaced by later passes.

The test intercepts every presentation read, including reads caused by saving.
It released its initial reply and removed route registration at the end, but
`page.unroute(pattern)` does not drain already running callbacks. The pinned
Playwright 1.64.1 types and implementation distinguish waiting for callbacks from
silently ignoring their errors. The main cleanup now awaits
`page.unrouteAll({ behavior: "wait" })` after releasing the initial reply.
No handler/status/body assertion or timeout is weakened, and no error-suppression
mode is used. The inverse single-line replacement reproduces the original file
byte-for-byte, preserving all focus, canonical edit/history and no-run checks.

A separate owned native probe copies those original assertions and unmodified
actual HTTP 200 bodies. It holds later fetched body reads until finally, delays
100 ms, then closes its owned context and observes for 250 ms. Both original
cleanup cases reproduce disposed body errors after the application assertions.
Changing only that cleanup to wait makes both cases pass with the same gates,
delays, bodies and context-close boundary. Both full reports, source controls and
commands remain. This is a controlled reproduction of the reported boundary;
the exact original CI callback/context timeline was not captured.

The temporary probe is removed only after an exact-byte ownership check; neither
it nor its artificial context-close/delay code enters the main test. Fresh 48
parameter presentation, parameter accessibility and wizard journeys pass with zero
skips, unexpected or flaky outcomes. All other 315 selected inputs, every Python
and backend-test input, all runtime/browser performance inputs and all 110 customer
payloads match the verified API candidate. Backend 1055, default browser 83,
performance 2 and the clean native Linux package retain their separately qualified
M3-reservation-api evidence, including its generated-contract amendment. This test
change adds no application, metadata DTO, lock/dependency or canonical-document
behavior. No new full 474/backend/performance/package run is claimed here.

Structured actual reports/logs, exact hashes, tool versions and source controls are
retained after path/credential sanitization. Screenshots, authentication roots and
raw CI logs stay private; they do not satisfy missing live cases. Root review is by
the implementation agent, not independent milestone acceptance. Native Windows,
actual AT/human/SADS, physical providers/hardware/commands and wider M0–M4 gates
remain unfinished or blocked. Task states stay 47 complete/43 in progress/10 blocked,
zero accepted milestones, M5 deferred.
