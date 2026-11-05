# ADR-0082: Select retained results without a browser preference

Date: 2026-11-05. Status: implemented; component verification recorded separately.

The native Orca journey found that Results hid its recorded-run selector when no
run was selected. A fresh browser therefore could not open an existing Autoverse
recording. Earlier result journeys initialized the browser's last-run preference,
which concealed this case. Two native browser counterexamples reproduce it at
1024×768 and 1440×900.

Results now displays a project-scoped recorded-run picker in the same header
position before and after selection. Selection does not create or replay a run.
The existing public `GET /runs` endpoint supplies pages of at most 200 records,
filtered by the current project. The inspected endpoint uses forward numeric
offset cursors; incompatible identities, shapes, oversized pages and regressing
or unsafe cursors produce a labelled error. A read has a 15-second deadline.
Refresh and page navigation are explicit, with no unbounded page accumulation.
Previously loaded choices remain identified when a later read fails.
The current selected run supplies its own status when also present in an older
list response; list metadata cannot overwrite a newer selected-run projection.
Two additional controlled stale-list counterexamples establish this precedence.

The selected project keys the picker. A departed component aborts its read;
responses cannot navigate or restore focus. The picker stays mounted when an
empty Results view acquires a selected run. Refresh and pagination buttons also
stay mounted and enforce `aria-disabled` in their handlers, preserving focus
when reaching the first or last page. The empty view explains selection and new
run creation without claiming that no evidence exists.

No backend, provider, compiler, executable identity, evidence or permission
contract changes. Existing historical selections remain valid. The native backend
and browser remain the product; the optional Linux Orca verification tools use a
private process/mount/IPC namespace, authenticated CPU framebuffer, private
D-Bus/AT-SPI session and eSpeak NG through an ALSA null sink. These are contributor
verification prerequisites, not application dependencies or auditory usability
measurements. They start no provider workload.

Affected verification: T030 result inspection and the open T038/T097 accessibility
work under AC-010, AC-011 and AC-031. Preserve the original task IDs and scope.
Browser failure/paging fixtures remain labelled separately from actual retained
Autoverse records and real Orca/AT-SPI observations. Full authoring, lab, campaign,
export, human usability and required-host acceptance remain separate gates.
Windows work remains frozen; this Linux evidence establishes no Windows result.
