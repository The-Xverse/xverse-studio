# Update, backup and recovery

Stop the native launcher before copying or replacing its data directory. Preserve the entire selected
root: `studio.sqlite`, authored project revisions, immutable snapshots, run journals and metadata.
The database alone is not a full backup. Sessions and ownership secrets in that private root are
local material; never place the root in a portable project bundle or public evidence attachment.

For a complete private backup on the verified Linux lane, stop Studio and wait for all runs,
campaigns and operations to reach settled terminal states. Unknown ownership or pending work
must be reconciled in the original root first. Choose a new destination outside that root:

```text
.venv/bin/python -I -m xverse_studio.host.launcher --data-dir .studio-local/data --backup-full .studio-local/backups/before-update
```

The command verifies SQLite schema/integrity, copies matching project revisions, snapshots,
journals and private ownership files, and writes `manifest.json` plus `files/`. Every file has
an exact size and SHA-256 identity. Transient bootstrap, launcher lock and SQLite WAL/SHM files
are excluded; committed WAL transactions are included through SQLite's backup API. Limits:
100,000 files, 64 GiB total and a 32 MiB manifest. Keep the **entire private directory** together.
It contains secrets; never publish it or use it as portable project/evidence exchange. Its
checksums establish integrity, not authenticity.

Restore using the same pinned candidate into another **new** data root:

```text
.venv/bin/python -I -m xverse_studio.host.launcher --data-dir .studio-local/recovered-data --restore-from .studio-local/backups/before-update
.venv/bin/python -I -m xverse_studio.host.launcher --data-dir .studio-local/recovered-data --port 8876
```

The restore command verifies exact membership, digests, database version and settled execution
before creating the destination. It preserves original source/snapshot/journal bytes and historical
identities, invalidates browser sessions and starts no processes. Read the newly generated bootstrap
file after launching. Existing destinations, nested destinations, symlinks and special files are
refused. A failed/interrupted restore retains `.recovery-incomplete`; the launcher refuses that root.
Preserve it for diagnosis and restore into a different new destination. Never remove the marker to
promote a partial restore. Failed backups without a verified manifest are unusable.

Full recovery is covered by native Linux subprocess tests, including a completed reference run,
byte-identical evidence, unchanged compiled plan and absence of run replay. Native Windows installation
and testing remain **BLOCKED at user request**; these Linux results do not establish that lane.

The secure acquisition successor requires admitted native directory/handle primitives. The current
implementation supplies Linux descriptor traversal and fails explicitly on unsupported hosts; it
does not silently fall back to path-only checks. Native Windows secure file acquisition remains an
implementation/verification gap under the held Windows lane. See the [support matrix](../implementation/platform-support.md).

The launcher also retains the smaller metadata-only backup:

```text
uv run xverse-studio --data-dir .studio-local/data --backup .studio-local/backups/metadata.sqlite
```

The destination must not already exist. Metadata alone is insufficient for full recovery. Existing source revisions and run snapshots are never
migrated in place. Database version 1 is supported; unknown versions refuse startup with an explicit
migration requirement. No unverified forward migration or arbitrary downgrade is advertised.

For updates, stop Studio, retain the full backup and exact existing lockfiles/commit, check out the
reviewed successor, then run `uv sync --frozen`, `npm ci`, `npm run build`, and the native test command
`uv run python scripts/run_checks.py`. Restart using the same explicit data root only after the
successor's compatibility/upgrade evidence supports it. Roll back by restoring the prior candidate
and its matching stopped backup; do not combine new database metadata with old run files.

On a backend crash, the reference worker has its own bounded native lifetime. Restarting Studio reads
its exact persisted run/operation, worker owner digest and process creation identity. It reconciles
current state without replaying Start. Missing ownership evidence remains `unknown` and blocks active
commands. PID reuse is not ownership. Controlled backend-crash recovery is exercised by
`tests/platform/test_native_recovery.py`; Windows remains pending until executed natively there.

A project revision is committed through a staged directory and transactional metadata pointer. A failed
save cannot activate a partial multi-file revision. External modifications are preserved and produce
`REVISION_CONFLICT`; copy them to a separate trusted recovery location and compare explicitly before
creating a replacement revision. Abandoned staged revisions are retained for inspection rather than
automatically deleted. Invalid source drafts cannot enter executable readiness.

The XDL source editor keeps uncommitted text in this browser tab after a 500 ms debounce, up to
512 KiB of UTF-8 text per document. This cache is separate from saved revisions and private full-root
backups. A larger draft remains editable but cannot replace the last bounded cache; keep a local copy
before closing. Recovered text is the last cached version and can omit newer uncached edits. Review
it before saving. Closing the tab can remove its session cache.

If browser recovery storage cannot be read, Studio shows editable saved source and a keep-copy
warning. It preserves the unread cache instead of replacing it with that fallback or your new edits.
Keep those edits separately, restore browser storage access, then reopen the editor or switch
documents to read the cached draft again. A storage warning does not mean a server save failed.

Use Ctrl/Meta+Z and Ctrl/Meta+Shift+Z for source Undo/Redo, and Ctrl/Meta+S or **Save source revision**
to commit exact authored text. A revision conflict retains your local draft: close the editor, choose
**Load current revision**, reopen the document and use **Compare changes** before explicitly saving
again. A size refusal requires correcting the source; reloading cannot raise the document limit.
Saving changes the project's draft revision and never changes an active run's frozen inputs. These
browser recovery journeys have native Linux evidence; Windows verification remains held.

Campaign recovery reconciles existing child identities before scheduling pending work. An uncertain
start is never replayed. Interrupted evaluation/retention operations report uncertainty or error rather
than synthesizing success. Historical canonical journal bytes are read-only; annotations and derived
evaluations are separate records. Retention requires a dependency-aware dry-run plan and an explicit
fingerprint-checked apply. Active inputs and referenced evidence are protected.
