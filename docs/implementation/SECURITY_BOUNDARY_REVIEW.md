# T010 Linux security boundary review — 2026-10-30

T010 remains in progress. Its dependencies T004/T008/T009 have component evidence;
the full original security scope still requires its own clause review. Current
confirmation targets actual enrolled Autoverse projects and the complete demo.
No generic reference workload substitutes for current confirmation.

The first reproduced gap concerns writes and rollback, not secure reads. Four
actual Autoverse parent-swap cases write into an owned foreign test directory;
two also lose the original foreign empty revision directory. All return409 after
later source acquisition, which does not prevent those prior effects. Two ordinary
Autoverse edit/compile cases retain the plan but fail private permission checks.
The original six failures remain retained. ADR-0042 anchors shared atomic writes,
publishes original revision directories without overwriting existing names and
restricts cleanup to the recorded original device/inode. First6 and then18 target
cases pass, including late collisions, actual short writes, pre/post-write and
post-publication metadata failures, and unsupported publication refusal. Final
source-bound confirmation passes153 API/native CLI cases and4 native browser
checks on429 unchanged source/config/test inputs plus6 UI assets. Clean installed
complete-demo confirmation is mixed, as recorded below. Evidence is retained under
`evidence/studio/M0-anchored-project-writes/`.

Clean candidatef754d1b package165 matches159 committed payloads,6 tested UI assets,
all429 inputs and canonical SDK12615d402. Its installed complete demo reaches
native publication and passes15 incompatible-input refusals,4 nonfinite refusals
and corrupt-snapshot refusal. The terminal assertion fails: lifecycle is stopped
but Android cleanup and its Stop receipt remain unknown. All16 original processes
are absent and3 exact container/start identities are later observed stopped; those
later facts do not rewrite the original result. The terminal same-key retry is not
reached. Root lock releases,21 original platform files and all captured inputs
remain unchanged. Preserve this failed live observation; do not replay to hide it.

The source cleanup review finds that optional Android shutdown and mandatory
container Stop share one exception boundary, and a CLI timeout skips final readback.
The original swallowed exception prevents assigning that as the demonstrated cause.
ADR-0043 now verifies original-owner readback after command uncertainty and retains
bounded constant codes in actual state and the canonical terminal event. The new
controlled baseline runs real Docker Stop to exit0, loses acknowledgement and
reproduces unknown. Clean candidatec8336a2 package166 then passes165 target API/native
CLI and4 browser checks on432 unchanged inputs plus6 UI assets, followed by3 complete
installed demo runs: both command acknowledgement-loss cases and nominal original
Docker. Each verifies release, original receipt/same-key retry, canonical resource
facts,16 original processes absent,3 exact containers stopped and21 platform files
unchanged. Original failed observations remain. See
`evidence/studio/M1-owned-container-readback/`; this resolves that mechanism, not all
T010 or the full lifecycle matrix. Continue the original clauses below.

ADR-0045 now repairs reproduced bounded exchange/download/imported-file gaps.
Final337 Autoverse API/native CLI and8 native browser checks pass on436 unchanged
inputs/6UI. The clean complete installed demo verifies exact source snapshot and
journal export, preserved external_demo/available scope/status, inert import with
unsupported-reader limitations, original-bound detail and identical export retry.
All16 original processes/3 exact containers are stopped and21 original platform
files unchanged. Original race reports and failed/corrected phases remain under
`evidence/studio/M0-bounded-evidence-exchange/`. Continue native metadata and the
remaining import/execution clauses; this component does not close full T010.

The remaining review covers every original T010 clause:

Session/content follow-up under ADR-0044 now passes317 enrolled Autoverse API/native
CLI and8 native browser checks on435 unchanged inputs/6UI. It rejects malformed
CSRF, corrupt/non-finite native sessions, non-finite opaque JSON and tested inline
credential assignments/escaped values, preserving ordinary data/external handles.
Diagnostic locations are bounded/redacted and early refusals retain security
headers. The separately reproduced gridToken false positive is repaired, with
original outcomes retained. Clean candidate90d6a45 package167 runs the complete
actual demo and refuses12 invalid-caller input/Stop requests without effects,
before successful owned cleanup and same-key retry. All16 original processes/3
exact containers are stopped and21 original platform files unchanged. See
`evidence/studio/M0-session-portable-boundary/`. This advances the first/fourth
clauses; full T010 closure still requires the remaining access/import/metadata/
execution review. That checkpoint identified exchange/imported-evidence filename reopens; the
ADR-0045 follow-up above repairs them. Remaining metadata/import/execution review
stays open.

| Clause | Current review disposition |
| --- | --- |
| Local binding, sessions and origins | Native launcher binds loopback. ADR-0044 confirms exact Host/Origin, one-use/expired bootstrap, session integrity/expiry, CSRF, safe early headers and live running-control refusal against Autoverse. No wider remote/multi-user authority is introduced. |
| Bounded project-file access on native Linux | Read acquisition is anchored. ADR-0042 repairs the reproduced revision-write/rollback gap. ADR-0045 repairs bounded exchange/download/imported-evidence acquisition and exact capture/export identity. Continue remaining native metadata access and the complete clause review. |
| Inert imports | T009 hostile import evidence exists. Revision allocation now uses the repaired native writer. Confirm original project/profile/script/unknown payload refusals against Autoverse and preserve all existing projects without dispatch. |
| Redaction and credential exclusion | ADR-0044 confirms known credential assignments/headers/JSON escapes across actual Autoverse authoring/import/legacy export, safe diagnostic locations and exact external-handle round trips. ADR-0045 verifies screened run export with exact original snapshot/journal bytes. Finish remaining read-path review; private delivery/provider-owned private logs remain separate. No immutable Argus/history bytes are rewritten. |
| Admitted execution and ownership only | T004's installed complete-demo evidence covers new-work/active compatibility, frozen inputs and owned cleanup. Audit other routes and imported metadata for registration/dispatch bypasses; unknown content never grants execution authority. |

These are remaining verification obligations, not newly claimed passes or a new
smaller definition of T010. Current counts stay57/33/10 and zero accepted milestones.
Full AC-003/032, independent milestone and external/human gates remain separate.
Windows is outside current delivery scope under ADR-0036.
