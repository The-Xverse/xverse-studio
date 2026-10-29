# Independent private-root recovery review

Reviewer: `experiments_lab`, independent of the root-authored recovery implementation.
Date: 2026-10-25. Scope: `host/recovery.py`, `host/ownership.py`, `host/launcher.py`
and ADR-0006. This review made no implementation edits and performed no Windows,
provider or physical-device operation. All repro data is an owned disposable
loop10 fixture.

Findings below were recorded **before repairs**. The author's 23 checks are
separate evidence and are not represented as this review's execution.

| ID | Severity | Finding before repair | Independent repro / required repair |
|---|---|---|---|
| REC-I01 | High | Backup hashing/copying validates path metadata before/after reads but does not bind the opened descriptor to that identity or reject raced ancestor redirection at acquisition. A directory can be transiently replaced with a symlink while `Path.open` acquires a file, then restored. The original leaf metadata is unchanged, while outside-source bytes are accepted as the backed-up source. | `independent-directory-swap-probe.json`: three controlled directory swaps caused `backup_full` to return `integrity: valid` with outside-source fixture bytes in `files/sub/owned.bin`; the original source bytes were unchanged and all three reviewed source hashes stayed unchanged. Anchor traversal to trusted managed directories, refuse symlink/reparse traversal during acquisition, and validate the actual opened descriptor identity before/after streaming in both hash and copy paths. Add the deterministic race regression before re-verifying restore. |

The deterministic probe swaps an **owned fixture directory** during descriptor
acquisition, opens an owned marker file outside the selected source root, and
restores the original directory before the function's path-stat check. It exercises
real Linux directory/symlink operations; no private production data is accessed.
The returned backup's own checksums describe the substituted bytes, so verifying
that backup again cannot establish the original source boundary. The manifest's
single-read handling does not repair this separate file-acquisition boundary.

Positive source observations: destinations use exclusive creation, restore writes
an incomplete marker before file materialization, launcher refuses that marker,
SQLite backup uses its public API, archive names/collisions/membership/digests and
terminal execution state are checked, sessions are invalidated, and maintenance
shares the native launcher ownership lock. Pending run/campaign/operation states
block rather than replay execution. These checks do not close REC-I01.

Status: REC-I01 open pending author repair and independent affected verification.
Windows installation/testing remains intentionally not run under the user's hold.
No full recovery/release acceptance claim is made by this component review.
