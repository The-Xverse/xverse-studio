# ADR-0069 — User hold on Windows work

Date: 2026-11-04. Status: active user execution hold.

The user instructs: "All the Windows related tasks must be frozen until I change it".

Freeze all Windows-specific implementation, tests, provisioning, packaging,
compatibility and acceptance activity until the user explicitly lifts this hold.
This applies wherever Windows work occurs, including the Windows obligations in
T002, T039, T098 and T100 and any corresponding feature/acceptance lanes. Preserve
the current code and historical evidence; do not revert it or promote it to passed.
Do not run Windows-specific tests, including their portable policy/ABI suite, while
the hold is active. Continue independently authorized Linux/Autoverse work.

This is an execution hold, not removal of requirements, task IDs, dependencies or
acceptance gates. Existing task statuses retain their component scope; Windows
remains NOT_RUN and no task/milestone closes because work is frozen. ADR-0063's
required-host obligations remain open. No new provider/device/publication authority
is granted. Only an explicit later user instruction lifts the hold.

The user additionally instructs: "after you finish the curret task, stop the work
until I decide to resume it". The current task is the Linux recorded-playback
verification with browser devices isolated. Its 22 checks pass on candidate
`ad8133460d7b43a77c71779368cee560a80c79e9`; save the evidence and then stop all work.
The global pause lasts until the user explicitly resumes. A later general resume
does not automatically lift the independent Windows hold. No task/milestone is
completed by either hold. Evidence:
`evidence/studio/M4-recorded-playback-device-isolation-20261104/`.

2026-11-05: the user reactivated the goal. This lifts the global pause for
independently authorized Linux/Autoverse work. The independent Windows freeze
remains active; no Windows work is resumed and no acceptance gate is waived.

Latest user instruction on 2026-11-05: finish the current task, then stop until
the user decides to resume. The current task is the scoped observation clock
failure repair (ADR-0070). Finish its verification and evidence only, then pause
the goal. Do not start another implementation or verification task. This later
stop supersedes the general resume; Windows remains independently frozen.

The current repair is now verified on source candidate a92f42e:59 selected Linux
checks pass on551 stable Git-bound inputs, with targeted static checks passed.
Evidence is retained in `evidence/studio/M3-probe-clock-overflow-20261105/`.
No task closes. Stop all work and pause the goal until explicit user resume.

The user subsequently reactivated the goal on 2026-11-05, after the clock repair
checkpoint was saved. This explicit resume lifts that global pause for independently
authorized Linux/Autoverse work. The Windows freeze remains active until separately
lifted. Original task, milestone, hardware and provider admission gates remain.
