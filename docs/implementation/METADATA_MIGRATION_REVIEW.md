# Metadata migration review — 2026-10-30

Reviewed source d285bca before repair. Store changes journal mode to WAL before
checking version and automatically promotes user_version0 in place. A controlled
existing schema0 loses its original version; a rejected999 schema still changes
its original SQLite bytes. Existing restore/backup reject unknown versions but
provide no supported copy migration. These findings keep T007/T008 open.

Fourteen new cases fail before implementation: two directly reproduce those
mutation failures, eleven fail at the absent migration function and one actual
native CLI refuses unknown arguments. Controlled unversioned fixtures use actual
existing records/idempotency shapes and real supported XDL; they are not evidence
of an unidentified released predecessor. ADR-0038 records exact compatibility,
copy/backup/report/activation and failure requirements before implementation.

The first implementation passes all14 cases. Additional failure tests initially
fail7/7: five used a connection proxy that SQLite.backup correctly refuses before
reaching the intended faults. Correct that NEW fixture to use an actual Connection
subclass. The missing-data-dir case exposed a real CLI default-target gap and also
used the real default path: its entirely test-generated candidate was verified
against its private fixture backup and moved intact into project-local retention.
The default path is absent again; no pre-existing user data was removed. The test
now sets XDG_DATA_HOME inside its isolated temporary root. Retain both outcomes;
this does not weaken any launcher/helper safety rule. Nontext SQLite values also
need an explicit typed refusal rather than candidate promotion.

Corrected failure fixtures reproduce three product gaps (untyped upgrade error,
implicit candidate root, nontext metadata), with four copy/report/integrity controls
passing. Repairs pass all26 expanded cases, including actual native reference
completion, CLI migration and explicit reopen without replay. Final format review
also reproduces both Boolean backup version fields being treated as integer0/1;
retain these two failures and require exact integer fields. Bound legacy schema
inspection and preserve every original source/input/failure qualification.

Final affected verification passes135 cases on407 unchanged tracked inputs and
six unchanged compiled UI files. Two separate portable-path checks pass. Two
additional permanent WAL-startup cases pass: a committed version1 in WAL opens,
while version0 refuses without changing the original database/WAL bytes. Only
that new test file extends the input set to408; all prior407 stay identical.
Actual Chromium on a separately migrated native candidate passes1024x768 and
1440x900 original-project open/validate/reload with no extra run. Its initial
private setup assertion counted pytest current symlink aliases twice; resolving
those generated aliases selects the one original source. The first setup failure
is retained. No original source or existing user demo was altered by this probe.
