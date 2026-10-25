# Independent review — revision history, undo/redo and recovery (2026-10-25)

A separate read-only reviewer inspected the first T045/T046 candidate against FR-026, FR-028, NFR-009,
AC-014, T045/T046 and the existing persistence, retention and private-backup code. All confirmed
findings were repaired before the verified successor.

| # | Finding | Disposition |
|---|---|---|
| 1 | Undo could silently revert a change it never recorded: steps were pushed without a continuity check and rebinding made stale steps valid again. | Steps chain only through this tab's revisions: a non-following edit starts a new stack; rebinding requires the next step's revision to equal the restored target; history is reconciled against each loaded revision. Browser regression interleaves a source save between graph edits. |
| 2 | Ctrl+Z on an empty stack reported an undo that never happened. | Empty steps are no-ops without a notice; the shortcut requires a step and ignores IME composition. |
| 3 | Recovery was unreachable for missing/non-UTF-8/oversized/unsafe sources, and tampered sidecars were reported intact and could be replaced by undo without backup. | Recovery observes with a tolerant bounded raw read; adopting requires present UTF-8 documents; restore works from history. Sidecar changes mark the project modified and block saves/undo; recovery backs them up and keeps recorded sidecar content. Browser restore-only recovery from the `PROJECT_UNAVAILABLE` notice. |
| 4 | Tests did not prove some claims (unchecked restore status, missing object never tested, sealing failure untested, private backup untested). | Assertions added; lost/tampered copy fallback and double-loss refusal, sealing-failure rollback, and full private backup/verify/restore of history and recovery backups are tested. |
| 5 | Recovery backup paths built from document paths could exceed the private backup's name bound. | Backups are named by digest. |
| 6 | History listing loaded every record (with manifests) and could not page past 200. | SQL-bounded, cursor-paged listing without manifests. |

The reviewer also stated that bounded autosave was missing. The source editor already keeps per-tab draft
recovery bounded to 512 KiB per document with a visible over-limit message; ADR-0013 now records this.

Retained limitations: restoring an older revision does not re-check catalog/artifact retention or
profile-lock registry state (preflight and Start still enforce admission); orphaned content copies
from rolled-back transactions are not pruned; on hosts without secure native I/O every restore reports
history as unrecoverable; graph history is per tab and does not follow edits made in other tabs.
