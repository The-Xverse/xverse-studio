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

Client completion amendment (2026-10-26): a completed restore persists its per-project tab history
only while that head still equals the one read at initiation. It never merges over a newer head.
Visible project/history state, notices and errors apply only to the initiating project and load
generation. The full Project returned by restore is already `projects.read` at commit; the browser
uses that authoritative result directly instead of starting a new load that could recapture obsolete
navigation intent. Other actors can still advance a later revision; normal revision conflicts and
explicit reload remain authoritative. No endpoint, stored format, restoration authority or immutable
revision changes.

After a toolbar-origin Undo/Redo completes, focus returns to the enabled originating history control
or its enabled opposite. Enter and graph shortcuts share this path for toolbar origins; other shortcut
origins keep their existing behavior. Restoration waits for busy state to clear and requires matching
project/load/intent/section/modal context, with focus still on the origin or BODY. It never overrides
deliberately moved focus or navigation. This is client completion handling, not a new runtime control.

Verification: `tests/e2e/wizard-accessibility.spec.ts` exercises native instance creation/binding,
exact-byte Undo/Redo through Enter and shortcuts, departure, deliberately moved focus and a newer
same-project edit/history head at both required viewports. Original failures, independent review and
the successor are retained in `evidence/studio/M2-keyboard-instance/`. These are Linux partial results;
native Windows and complete accessibility acceptance remain open.

Generic edit completion amendment (2026-10-26): semantic edits capture their initiating
project/load/selection intent and tab history before sending the expected-revision transaction.
The returned full committed Project supplies the new visible head directly; no captured refresh
starts another project load. A reply cannot replace a known newer head. The completed step persists
only while the stored tab history still equals its initial value, including after departure; visible
history and feedback remain scoped to the current context. An equal-head acknowledgement preserves
newer readiness. Obsolete errors do not appear in a departed workspace. Local forms receive explicit
success only for a current acknowledgement, independently of whether an older backend operation
committed. Backend validation, revision promotion and immutable run snapshots are unchanged.

Parameter drafts belong to project/document/Scenario/parameter identities. Field edit generations
preserve newer text, including explicitly retyping the old authored value while a save is pending,
and unrelated dirty fields survive a returned Project. Only a matching submitted generation may be
normalized by its acknowledgement. Same-value numeric text (for example `5.0` submitted as typed
`5`) requires explicit successful completion before normalization; a resolving failure wrapper is
not success. Retained input is labelled unsaved alongside the current saved value and associated
parameter guidance. Draft state and control references are bounded by the current parameter set.

After a current successful Apply disables, focus can return to the corresponding enabled field.
Restoration requires the same field identity and generation, a current authored value, no modal,
and focus still on the origin or BODY. Newer edits, deliberately moved focus and another project's
controls take precedence. These are scoped browser completion and input-recovery rules, not live
parameter mutation or additional runtime admission.

Inert presentation metadata may arrive after editing begins and regroup parameter forms. When that
commit replaces the currently focused control, the same semantic field receives focus in the layout
phase only if the old node is disconnected, its replacement still exists, focus is on BODY and no
modal is active. A deliberate blur clears the witness. Metadata continues to apply; it is not frozen
to avoid focus transitions. The native presentation countercheck asserts the returned group legend
as well as preserved input/focus and unchanged canonical documents.

Source completion and recovery amendment (2026-10-26): source PUT already returns the
authoritative committed Project. Source saves now share the revision-commit guard with deployment
authoring instead of starting a captured project refresh. A reply applies only to the selected
project/load generation and cannot replace a known equal or newer head. Current feedback also
requires the initiating intent; obsolete failures cannot appear in a departed workspace. A current
revision conflict remains visible inside the source modal and through the existing explicit
Load current revision action after closing it. Other failures retain the in-editor text and show
error-specific guidance rather than recommending a reload for every refusal. An actual size refusal
does not acknowledge a save or advance the canonical revision.

Source shortcut keys are case-normalized, including Ctrl/Meta+Shift+Z, and ignore Alt and IME
composition. A synchronous send guard prevents overlapping submissions from one editor. After a
current request finishes and disabled controls re-enable, focus may return to the same document/text
only when it remains in the active source dialog and focus is still on its initiating control or
BODY. Deliberately moved focus, another document/editor and a different modal take precedence.
The guidance is associated with the textarea; comparison text has scoped rendered-contrast evidence.

Recovery keeps the 500 ms debounce and 50-step text history. Its 512 KiB document bound is measured
in UTF-8 bytes; oversized text is immediately reported and leaves the last bounded cache intact.
Recovered text is explicitly the last cached version and may omit newer uncached edits. Cache reads
that fail fall back to editable canonical source with a persistent keep-copy warning. That fallback
and any new edits cannot overwrite or remove the unread cache. Restoring read access and reopening
or switching permits explicit recovery of that text. Persistence cleanup reads the latest known
Project, so an old effect cannot recreate a just-saved draft against an obsolete baseline. A current
acknowledgement removes only cache text equal to its submission; departed/newer editors retain their
own recovery state. Storage failure after a commit is a recovery warning, not a failed server save.

Verification: `tests/e2e/source-accessibility.spec.ts` covers native source Undo/Redo and shortcut/
button save, exact source and other-document preservation, actual stale refusal and explicit compare/
retry, held real responses with newer navigation/history/drafts/readiness/focus, the exact UTF-8
cache boundary and real backend size refusal. Scoped browser-storage read-failure fixtures verify
canonical fallback and unread-cache preservation; they do not establish platform-filesystem failure
handling. Native Linux evidence belongs in `evidence/studio/M2-keyboard-source/`; Windows, actual
assistive technology, external-file adoption and complete milestone acceptance remain separate.
