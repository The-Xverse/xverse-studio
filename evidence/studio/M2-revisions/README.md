# Revision history, undo/redo transactions and source recovery — T045/T046

T045 and T046 are component-complete on Linux; see `verification.json`, ADR-0013 and
`independent-review.md`. No milestone or Windows acceptance is claimed.

- Every revision records origin and digests and keeps verified content-addressed copies.
- Graph undo/redo restores verified earlier bytes as new forward revisions; stale steps conflict and
  never overwrite another change; steps never cross changes the tab did not record.
- Externally changed, missing, non-UTF-8, oversized or unsafe sources and changed sidecars are
  preserved in a digest-named backup before an explicit adopt or restore; sidecars keep recorded content.
- Interrupted staging or history sealing leaves the last saved revision intact; leftover staged
  revisions block until resolved; draft edits, undo and recovery never change a run snapshot.
- Source-editor autosave is bounded per tab and never commits revisions.

Remaining: AC-014's per-platform file-locking/replacement/case-collision clauses and bidirectional
Windows exchange (T048); restore does not re-check retention/registry state (preflight still enforces).
