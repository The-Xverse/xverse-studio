# M0 independent review: first findings

Reviewer: `/root/xdl_baseline`, separate from the author of the reviewed security, project, storage,
exchange and host modules. Date: 2026-10-25. This first record precedes repair of these findings.
The reviewer did not modify those owned implementation modules. Tests used fresh isolated data roots
on the user-selected filesystem and did not access companion runtimes or physical equipment.

Reviewed source SHA-256 identities:

| Module under `services/studio-api/src/xverse_studio/` | SHA-256 |
|---|---|
| `security/files.py` | `39fcb1783ccf60d33898d654c2e0652885bbe78753942709403fafa24c5e5424` |
| `projects/service.py` | `4e86dd2ba461c19af8bbfa34357ce545d1be944a303ba8e36dd0daeb361f4aa6` |
| `storage/core.py` | `b0467a782a8f7b63d330c38032bed646c185d6835e693edf69d9dfd8b4223018` |
| `api/exchange.py` | `409c41c962aeabd369c2e47030218589d288c1fcd146877a7b936c845b365e11` |
| `host/launcher.py` | `e4781c3450c60ba5fd5dcd1fc3b22dd6ae106ec8831db6ada51d13c3d5b258a7` |

| ID | Severity | Finding and executed reproduction | Required repair / verification |
|---|---|---|---|
| M0-R01 | High | `security/files.py` credential detector accepts a synthetic URI containing userinfo credentials. `check_text` returned successfully. The same gate guards source persistence and portable export, allowing inline credential leakage in an inspect-only project. | Detect URI userinfo without echoing protected text. Add source/import/export tests including URI credentials and ensure diagnostics/export never contain the submitted value. |
| M0-R02 | Medium | `safe_name` accepts portable archive names containing Windows-forbidden `?`, `*`, `<`, and `|`. Direct calls accepted all four sample names. Such packages cannot retain their file identities on the required native Windows path. | Reject all forbidden Windows filename characters and ambiguous reserved-name variants before extraction; retain Linux/Windows portable-path negatives. |
| M0-R03 | High | Project export overwrites an imported `artifacts.lock.json` with a newly generated empty lock. An isolated project with one pinned restricted artifact exported with `entries: []`. This drops immutable dependency and restriction provenance. | Preserve an admitted existing artifact lock byte-for-byte, or explicitly reject invalid/unavailable lock content; generate an empty lock only when none exists. Round-trip a nonempty restricted/missing dependency lock without retrieving artifacts. |
| M0-R04 | High | `_commit` renames a staged revision before storing/committing metadata, but failure cleanup only removes the old stage path. Injecting a metadata write error after rename retained committed revision 1 and left orphan revision 2. Retrying revision 1 then returned `412 REVISION_CONFLICT`, preventing further saves. | Introduce recoverable commit bookkeeping or remove only this transaction's uncommitted owned target safely on rollback; handle SQLite commit failure as well as write failure. Verify prior revision remains readable and a later save/recovery succeeds without deleting committed history. |

Read-only inspection confirmed exact Origin/Host checks, session/CSRF enforcement, bounded inert ZIP
handling, explicit subprocess argument vectors, immutable source revisions, and revision-checked
mutations are present. This does not establish complete acceptance: Windows installation, path,
process-handle, browser and migration behaviour remain NOT_RUN. No native Windows support gate is
closed by this Linux review.

The semantic-edit helper was authored by this reviewer and is excluded from the independent-review
claim. A separate earlier self-review found global removal by equal element ID; that helper was
already repaired to stable resource URI scoping and regression-tested before this review was
requested. This record does not retroactively describe that as an independent pre-repair finding.

Status: findings open for the implementation author. Successor source hashes and affected test results
must be appended after repairs; the original observations above must remain unchanged.
