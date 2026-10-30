# ADR-0038: Explicit copy migration of known unversioned Studio metadata

Status: implemented and verified for the scoped Linux copy-migration component. Applies to T007/T008/T039 on the
Linux host required by ADR-0036. IDs, requirements and acceptance cases remain.

## Existing boundary and decision

Store currently accepts SQLite user_version0 and1, creates the records and
idempotency tables, and writes version1 in place. This proves a concrete existing
0-to-1 transition; it does not identify a released legacy package or admit unknown
XDL/project formats. Project envelopes remain1.0 and authored XDL is unchanged.

Replace that automatic upgrade with an explicit stopped-root copy workflow:
`--data-dir NEW_ROOT --migrate-from ORIGINAL_ROOT --migration-backup NEW_BACKUP`.
Require all three roots to be distinct, nonnested, nonsymlink native paths and
refuse existing destinations. Reuse the held-descriptor full-backup/restore
pipeline and its bounds, ownership locks, settled run/command/campaign/lease
checks, digest verification and incomplete-target marker. The supported source
is exactly user_version0 with the existing records/idempotency table shapes,
primary keys and no added triggers/views/tables/indices. Unknown versions or
unrecognized unversioned structures remain unsupported. Blank new SQLite roots
can still initialize; opening an existing metadata schema never silently upgrades.

Retain a verified private schema0 backup before allocating a schema1 target.
Only the staged database changes: advance its user_version and invalidate copied
browser sessions as existing full restore does. Preserve remaining stored JSON
text, idempotency receipts, identities, project/revision/layout/binding files,
immutable snapshots and canonical evidence exactly. No provider construction,
compile-time semantic upgrade, dispatch, lease acquisition or process startup is
part of migration. Existing private full-backup format1 records databaseSchema0
for this explicitly selected migration; normal backup/restore remain schema1.
A failed target stays marked incomplete. Original and completed backup stay
readable and unchanged; a backup without its verified manifest is unusable.

Write a versioned private migration report before target activation is enabled.
Include the schema textual diff, session invalidation count, exact before/after
stored project/receipt identity digests and unchanged non-database file identities.
State the semantic scope: preserving original authored bytes and stored metadata
is distinct from validating/compiling an unsupported XDL version. The pinned XDL
compiler remains authoritative; the native supported-project test compares actual
plans before/after. Never include session values, secret material or machine
paths in printed summaries. The report is private, outside portable project export.

Migration creates a candidate root and returns without serving or executing.
The user reviews its report and explicitly selects that root in a later normal
launcher invocation to apply it. Nothing replaces the source root or a working
project revision automatically; original run snapshots are never migrated in place.
On failure retain the original candidate/backup for inspection and select another
new destination. Unsupported versions require a separately specified migration,
not version relabelling or downgrade. Startup rejects them before enabling WAL or
writing schema changes. Read-only inspection honors committed SQLite WAL state.

## Verification

First reproduce automatic version0 promotion and unknown-version journal mutation
on isolated controlled metadata fixtures; never mutate the user's running roots.
Add positive copy migration, exact project/source/opaque metadata/receipt retention,
rollback/interruption and session invalidation checks. Cover source lock, unsettled
runs/operations/campaigns/leases, unsafe paths, unsupported schema/shape, overwrite,
copy/report/commit failure and marker preservation. Repeat existing secure recovery
race tests and exercise the actual native CLI plus supported XDL plan readback.
Synthetic unversioned fixtures are explicitly labelled; they do not establish an
unidentified released-upgrade path, full AC-032 or milestone acceptance.
