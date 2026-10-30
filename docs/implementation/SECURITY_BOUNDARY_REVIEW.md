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
Next investigate with bounded coded diagnostics and exact-owner readback, retaining
unknown whenever ownership/release cannot actually be established.

The remaining review covers every original T010 clause:

| Clause | Current review disposition |
| --- | --- |
| Local binding, sessions and origins | Native launcher binds loopback; API has exact Host/Origin, one-use bootstrap, session expiry and mutation CSRF checks. Fresh target negatives must cover malformed and expired credentials, not merely reuse historical smoke checks. |
| Bounded project-file access on native Linux | Read acquisition is anchored. ADR-0042 repairs the reproduced revision-write/rollback gap. Continue auditing exchange/download, imported evidence and metadata access rather than treating one repaired path as the entire clause. |
| Inert imports | T009 hostile import evidence exists. Revision allocation now uses the repaired native writer. Confirm original project/profile/script/unknown payload refusals against Autoverse and preserve all existing projects without dispatch. |
| Redaction and credential exclusion | Inspect actual portable project/run exports and ordinary diagnostics. Exercise session/bootstrap/authorization material explicitly; private delivery or provider-owned private logs are not ordinary export streams. Do not rewrite immutable Argus or historical source bytes. |
| Admitted execution and ownership only | T004's installed complete-demo evidence covers new-work/active compatibility, frozen inputs and owned cleanup. Audit other routes and imported metadata for registration/dispatch bypasses; unknown content never grants execution authority. |

These are remaining verification obligations, not newly claimed passes or a new
smaller definition of T010. Current counts stay57/33/10 and zero accepted milestones.
Full AC-003/032, independent milestone and external/human gates remain separate.
Windows is outside current delivery scope under ADR-0036.
