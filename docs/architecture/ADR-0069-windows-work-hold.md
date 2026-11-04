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
