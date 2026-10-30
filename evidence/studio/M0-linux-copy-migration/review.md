# T007 Linux persistence and migration review

The existing task and T001 dependency remain; the following checks cover each
amended Linux clause. This is a primary-agent component review, not independent
M0 or AC-002/032 acceptance. Commands and original phase results are retained.

| T007 clause | Evidence |
| --- | --- |
| Project revision and atomic persistence | Four project-store cases verify revisions, conflicts, source/layout separation, line endings and collision refusal. Existing review regressions exercise metadata failure, SQLite commit failure, post-commit error and external source conflict without losing the last committed revision. |
| Stable references and source/semantic identity | Seventeen actual CLI/library round-trip cases compare supported plans and resource identities across comments, Unicode, JSON, CRLF and edits; failed/stale edits retain the previous source. |
| Backup-preserving migration | Twenty-eight new migration cases first expose in-place version0 promotion and unknown-version mutation. Explicit copy migration retains original bytes plus a verified schema0 private backup, advances only staged metadata to1, invalidates copied sessions and writes a versioned textual/stored-identity diff before startup is enabled. It changes no envelope/XDL version. Native supported-project compilation proves actual unchanged plan before/after, not an invented semantic upgrade. |
| Preview/report, explicit application and rollback | Migration returns a candidate without serving or dispatching. Review its private report, then explicitly launch that new root. Copy, upgrade, report and semantic/file-integrity failures retain the original/verified backup and an ineligible marked candidate; startup refuses it. A new destination/backup retry succeeds from the unchanged original. Existing full restore/rollback and secure acquisition races remain covered separately. |
| Native paths, locks and replacement semantics | Real roots contain spaces/Unicode. Source locks, nesting, existing targets, symlinks, settled execution and lease checks precede promotion. Fifteen secure-recovery cases exercise descriptor traversal, actual openat/directory swaps, committed WAL and late namespace changes. Two additional startup cases distinguish schema0 refusal from schema1 committed in WAL. |
| Inert foreign paths, case collisions, reserved names and line endings | Direct portable-path and symlink/case archive negatives cover drive/UNC/ADS/reserved/trailing names on Linux; project-store/round-trip/native exchange cases preserve CRLF and support LF revision changes without changing the supported plan. These remain hostile-input checks, not Windows delivery gates. |
| Isolated native Linux exchange | Two actual source/target/reopen workspace cases retain portable source, unknown metadata, layout and logical XDL identity while creating new envelope identities and refusing foreign sessions. Unsupported physical declarations stay preserved and blocked; no device is contacted. |
| Real native migration application | A completed actual native reference run is migrated by the native CLI, then explicitly reopened through a new native launcher. Its one original run, immutable snapshot/journal/request bytes, project revision and authoritative plan remain. Old sessions return401; no run is replayed. |
| Browser operation on migrated data | Separate actual Chromium journeys at1024x768 and1440x900 authenticate freshly, open the original project, run authoritative validation, reload the same revision and retain one stopped historical run. Original source is unchanged; no workload is started by these browser journeys. |

Final results:135 affected cases plus2 portable-path cases and2 additional WAL
startup cases pass (139 unique). The first407 source/config/test inputs stay
identical; the additional WAL test file is the408th. Six compiled UI assets remain
separately identical. Original diagnostic phases are not relabelled as final passes.

ADR-0038 specifies the concrete already-existing metadata0-to-1 transition. It
never invents a predecessor XDL/project format or treats unknown versions as valid.
The report's semantic scope is exact preserved non-session stored text/receipts
and original authored/run-file identities, with no new execution admission. Actual
supported plan equality is independently verified using the pinned compiler.
This completes T007's persistence/migration testing component. T008's broader
implementation/dependencies and M0/AC-032/independent release gates remain open.
