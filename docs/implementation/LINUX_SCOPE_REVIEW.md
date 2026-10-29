# Linux scope amendment review

Authority: user requested continuation of remaining tasks and removal of Windows
requirements on2026-10-29. ADR-0036 defines the amended target without regenerating
IDs or weakening unrelated requirements.

Reviewed constitution1.1.0, AGENTS, spec, plan, research, provenance, contracts,
acceptance, normative task descriptions, traceability, CI scope, support matrix,
installation/recovery guides and descriptive compatibility. Native Windows gate
language is superseded. Foreign Windows-style paths remain inert Linux security
inputs; statistical time windows are unrelated and remain required. Historical
implementation/CI/failure records retain their original candidate qualifications.

The specification validator preserves75requirements,8success criteria,100tasks
and32acceptance cases. The descriptive compatibility checker passes with Windows
OUT_OF_SCOPE_ADR0036. No Linux task status was promoted merely by removing a gate.
Current statuses remain49completed/41in_progress/10blocked pending task-by-task
Linux evidence review; zero broader milestones are accepted.

The review identified stale current-language remnants in project-format atomic
save, provider portability, task execution rules and several later task descriptions.
Those were corrected before this final pass, while historical notes remain intact.
No blocking scope inconsistency remains in the amended normative host requirements.
Other requirements, including actual hardware permission and first-time-user
measurements, remain; they cannot be replaced by fixtures or invented results.

Next technical task: reconcile active run observations before aggregate preflight
counts so a completed original task does not remain RESOURCE_BUSY until a separate
GET. Preserve unknown ownership as active and retain signed/original-handle checks.
Then audit foundation/native Linux recovery/packaging tasks in dependency order.
