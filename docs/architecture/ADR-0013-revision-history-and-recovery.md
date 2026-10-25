# ADR-0013: Revision history, undo/redo transactions and explicit source recovery

Status: implemented owned components under verification; no M2 acceptance claim.

FR-026, FR-028 and NFR-009 require undo/redo with reference integrity, atomic saves that never corrupt
the last saved revision, stale writes that conflict while both versions stay recoverable, and autosave
that never rewrites an active run snapshot. Revisions were already immutable directories behind a
transactional pointer, but only the current project metadata existed. If committed files changed on
disk, every save refused and no supported path led out; the committed bytes of that revision could
not be recovered.

Each committed revision now writes a `revision` record (origin, document paths/formats/digests,
sidecar digests and manifest) in the same transaction as the project pointer, and a content-addressed
copy of every document and sidecar under the project's `objects/` directory. Copies are verified
against their digests when read and are never served when they do not match; a revision-directory file
serves only when it still matches the recorded digest. The history listing is cursor-paged (at most
200 per page, newest first) and omits manifests.

Undo/redo is `POST /projects/{projectId}/revisions/{revision}/restore` with `If-Match`: a new forward
revision built from the verified copies of an earlier revision. History is append-only. A stale
`If-Match` is `412 REVISION_CONFLICT`; missing or mismatching copies are `409 REVISION_UNRECOVERABLE`
with no change. The browser keeps a per-tab, bounded (50) stack of graph steps; each step names the
revision it restores and the revision at which it is valid. Steps chain only through revisions the tab
produced: an edit that does not follow the stack top starts a new stack, the next step is rebound only
when its recorded revision equals the restored target, and history is cleared when the loaded revision
was not produced by it. A step is never applied over another session's change. Text editing keeps its
own source-editor undo; the graph shortcut ignores text fields, dialogs, IME composition and busy state.

Autosave is the existing source-editor draft recovery: drafts are kept per tab in session storage
(at most 512 KiB per document, 500 ms debounce, 50 text-undo steps) and an oversized draft is reported,
not silently dropped. Autosave never commits a revision and never touches a run snapshot.

Externally changed sources are resolved only by `POST /projects/{projectId}/recoveries` with
`If-Match`, `expectedRevision` and an explicit `adopt_external` or `restore_revision` action. Recovery
observes documents and sidecars with a bounded raw read that tolerates missing, unsafe, oversized and
non-UTF-8 files, so a project that `GET` reports as `PROJECT_UNAVAILABLE` can still be restored; the
browser offers that from the error notice. Before committing, the observed bytes of every changed file
are written to an immutable backup named by digest, with committed/observed digests and observation
status, retrievable through the recovery routes. Adopting is refused unless every document is present
UTF-8 text; sidecars are never adopted from disk and keep their recorded content. Sidecar changes now
also mark the project `modified`, so no save or undo silently replaces them. Recovery is refused when
everything matches. The changed revision directory remains for inspection.

Compatibility: existing revisions without records stay readable; the history reports them as
unrecorded and they cannot be restored. Content copies add storage proportional to distinct document
bytes. Layout and run snapshots are unaffected; restore and recovery never alter a run snapshot.
Project retention removes `objects/`, recovery backups and their records with the project; they are
not pruned individually.

Verification: `tests/integration/test_edit_conflicts.py` (history, add/connect/disconnect/remove undo
and redo with exact bytes and validation, stale restore, concurrent saves, tampered/missing history,
external write preservation and both recovery actions, interrupted staging, leftover staged revision,
active-run snapshot isolation) and `tests/e2e/draft-run-isolation.spec.ts`. Native Windows file-locking
and case-collision behavior remain T048 obligations.
