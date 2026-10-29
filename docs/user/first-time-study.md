# Prepared first-time-user study (not yet executed)

This is the SC-001 procedure. No participant result exists merely because this script exists.
Recruit five people who have not used X-Verse Studio. Record their actual native platform/browser;
a cohort does not replace the automated Linux/Windows native installation matrix.

Prepare the pinned candidate and scoped example before the participant starts. Record provisioning
and preparation time separately. Start the local backend, prepare the one-use local sign-in delivery,
and ensure the reference examples and browser assets are available offline. Do not include simulator
or toolchain downloads in the prepared 15-minute task. Obtain consent for anonymized task observations;
store no names, account identifiers, credentials or private screen content in public evidence.

Read this prompt, then start the timer:

> Open the process-control reference example. Find a parameter and change its target to 0.8. Run the
> example and find its recorded result. Then select the reference stuck-sensor fault, run a new frozen
> snapshot and explain which observed evidence supports the fault and which result remains uncertain.

Do not direct them to a control or terminal command. A question answered with instructions, a hint,
or facilitator action counts as intervention and is recorded even if the task subsequently succeeds.
The facilitator may stop an unsafe or out-of-scope action; that attempt is not an unassisted completion.
The participant may use packaged help. Keep the default five-second horizon so the frozen assessment
window and coverage agree. A successful lifecycle is distinct from the assessment verdict.

Record one row per anonymous participant with candidate/code digest, environment, preparation seconds,
start/end time, completion seconds, target edit, first run ID/snapshot, result located, fault run ID,
observed fault explanation, assertion interpretation, terminal use, assistance count/details and outcome.
Failures/timeouts remain failures. Retain exact defect observations before repairs and run the affected
walkthrough again on a successor candidate; do not overwrite the original observations.

SC-001 passes only when at least four of five first-time users complete within 900 seconds with no
terminal commands or facilitator intervention. A Playwright run, an agent walkthrough or a screenshot
cannot count as one of those five participants. Current outcome: **BLOCKED / no recruited cohort**.
