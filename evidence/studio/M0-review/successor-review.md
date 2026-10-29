# M0 successor review

Reviewer `/root/xdl_baseline`; separate from root's repairs. Original findings remain unchanged in
`findings.md`. Date: 2026-10-25. The reviewer added independent regression tests in
`tests/contract/test_review_regressions.py` without editing root-owned implementation modules.

First successor run: `python -m pytest tests/contract/test_review_regressions.py -q` under the pinned
environment with ambient PYTHONPATH/plugins disabled and temporary/cache files on the selected
filesystem. **Nine passed, one failed**. This run includes the M1 regression cases described in the
separate successor review.

- M0-R01: repaired boundary passes direct source mutation, inert archive import, and export of a
  deliberately injected older persisted URI credential. Errors do not echo the synthetic secret marker.
- M0-R02: all six Windows-forbidden filename characters are rejected by the shared portable path gate.
- M0-R03: a nonempty artifact lock containing a missing, restricted, pinned dependency survives export
  byte-for-byte.
- M0-R04: a metadata *write* failure after rename now preserves revision 1, removes this attempt's
  uncommitted revision 2, and permits a later save. However, a subsequent SQLite *commit* failure
  remains unresolved: the transaction rolls back to revision 1 after `_commit` has returned, leaving
  unreferenced revision 2. `test_sqlite_commit_failure_preserves_prior_revision_and_allows_retry`
  fails on `assert not projects._dir(projectId, 2).exists()`.

M0-R04 remains open for this second failure window, explicitly covered by the original finding's
request to handle SQLite commit failure as well as write failure. No criteria were weakened. Record
the next successor's affected verification after the author repairs transaction-level rollback.

Second successor: root added transaction rollback callbacks registered for the owned staged revision.
The callback runs after an uncommitted SQLite transaction rolls back; a post-commit acknowledgement
error does not trigger deletion when SQLite reports no active transaction. Focused regression plus
project-store suite passed **13 tests**. An added test then exercised an error *after* SQLite's actual
commit and confirmed committed revision 2 and both old/new source directories remain readable.
Implementation-source identity now contributes to capability digests; a read-only source-byte fixture
confirmed changing effective worker bytes changes the capability identity without modifying files.
M0-R04's metadata-write and pre-commit failure windows are closed by the affected tests. Abrupt process
death or filesystem failure during cleanup remains distinct from those controlled exceptions.

Final focused verification: **17 passed** across independent review regressions, project persistence
and native backend subprocess crash/recovery. The capture detected an exchange-module change during
that run, so it explicitly records `sourceUnchangedDuringVerification: false`; it is not presented as
a single unchanged-candidate claim. The other eight reviewed modules retained their hashes.
Affected credential/export/lock and exchange regressions were then repeated: **11 passed** with all
nine reviewed source identities unchanged throughout. See `final-focused-verification.json` and
`final-exchange-successor-verification.json` for commands, outcomes, sanitized environment and source
identities. An added post-commit-error case also proves that a completed SQLite commit is preserved
when its acknowledgement fails; rollback cleanup does not remove committed sources.

Current disposition: M0-R01 through M0-R04 are closed for the exercised native Linux boundaries.
Native Windows, complete migration/packaging, external integrations and the full M0 acceptance gate
remain separate unfinished obligations. This review does not mark a milestone complete.

Root follow-up before repair: portable exports screened credentials but did not reject literal host-local
file URIs or absolute home/drive paths embedded in authored text. This can leak private environment
bindings even though no file is fetched. Repair must refuse such portable exports with a safe diagnostic,
preserve authored bytes, and never echo the rejected value. Source inspection remains inert.
