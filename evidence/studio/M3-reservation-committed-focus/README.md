# Reservation read focus after React commit

Latest checkpoint: source43 full602 ends601pass/1parameter-selection failure, retained separately. The narrow successor repair passes71 affected browser/performance2 on342 unchanged inputs; full604 has not been rerun locally. T026 separately closes its complete transport component, bringing counts48/42/10 withzero accepted milestones. See [parameter successor](../M2-parameter-selection-identity/). Earlier checkpoint text below retains its original scope.

Published `449fbd5` PR CI passed 561 browser cases and failed the 1440×900
reservation-options alert-focus assertion. Push CI passed all 562. The PR's exact
event scheduling was not recorded; both outcomes remain in the native CI dossier.

The read hook scheduled animation-frame focus immediately after setting result or
error state. React could commit the alert after that callback, leaving its ref
absent when focus ran. A labelled control delays MessageChannel scheduling while
retaining native animation frames. Both viewports fail the original focus check
before repair and pass afterward. Captured frames show the alert absent before
repair and present at the final focus callback after repair. This control establishes
the race; it does not establish the exact original CI timing.

The hook now records a focus request and schedules it from an effect after the
pending/result/error state commits. Disposal, generation, dialog and active-element
guards remain; effect cleanup cancels the pending frame. No authority, reservation,
provider call, request identity or timeout contract changes.

All 36 affected native reservation journeys pass, including the original and added
delayed-commit variants, navigation/retry, same-key recovery, ownership/permission,
history and deliberate focus/dialog preservation. Controlled two-case red/green
is separate from those 36; the cohorts must not be added as unique acceptance cases.
Typecheck/build pass. The full 602-case successor browser run and separate performance
checks are running/queued separately; no clean successor package is claimed yet.

`amendment.json` proves the exact inverse restores the original production file and
the original test body/assertions/deadlines plus all content outside the timing
variant remain unchanged. Only text/JSON observations are retained publicly. Raw
fixture databases, sessions and screenshots remain private. These fixture results
do not establish native Windows, physical-device, human/AT or milestone acceptance.
