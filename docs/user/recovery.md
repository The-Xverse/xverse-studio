# Update, backup and recovery

Stop the native launcher before copying or replacing its data directory. Preserve the entire selected
root: `studio.sqlite`, authored project revisions, immutable snapshots, run journals and metadata.
The database alone is not a full backup. Sessions and ownership secrets in that private root are
local material; never place the root in a portable project bundle or public evidence attachment.

The launcher can create a consistent metadata-only backup while it exclusively owns the root:

```text
uv run xverse-studio --data-dir .studio-local/data --backup .studio-local/backups/metadata.sqlite
```

The destination must not already exist. For full recovery restore the matching complete stopped data
root and restart the same pinned candidate. Existing source revisions and run snapshots are never
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

Campaign recovery reconciles existing child identities before scheduling pending work. An uncertain
start is never replayed. Interrupted evaluation/retention operations report uncertainty or error rather
than synthesizing success. Historical canonical journal bytes are read-only; annotations and derived
evaluations are separate records. Retention requires a dependency-aware dry-run plan and an explicit
fingerprint-checked apply. Active inputs and referenced evidence are protected.
