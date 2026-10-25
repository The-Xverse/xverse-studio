# ADR-0006: Stopped-root private backup and explicit restore

Status: implementation in progress; Linux verification is recorded separately. Windows installation and tests remain on user hold.

The metadata-only backup cannot independently recover matching source revisions, immutable snapshots and journals. The launcher therefore provides a separate private directory backup with a versioned manifest and per-file SHA-256 identities. This is an administrative local backup containing private ownership material, not a project/evidence export. Checksums establish byte integrity, not producer authenticity.

The existing OS-native launcher lock also excludes maintenance. Full backup and restore require database schema 1, SQLite integrity and terminal run/campaign/operation state. Unknown ownership or pending work blocks the operation; recovery never starts a worker or replays a campaign. Each destination must be new, outside its source tree. Symlinks, special files, portable path collisions and exceeded bounds are refused. Limits are 100,000 files, 64 GiB total bytes and a 32 MiB manifest.

SQLite is copied using its public backup API, including committed WAL content, then normalized to DELETE journaling in the backup only. Source documents and evidence are copied byte for byte. The source is not migrated. Transient launcher lock/bootstrap/WAL/SHM files are excluded. Verification checks exact file membership, sizes, digests, schema and settled execution before a restore target is created. Copy/verification failures retain an incomplete target for inspection; a restore marker blocks launcher startup. A retry requires another new destination.

Restore preserves historical source/evidence/operation identities and clears browser sessions. The next launcher generates a fresh bootstrap token. No supported schema upgrade or downgrade is inferred from copying a root; updates still need exact-candidate compatibility evidence and matching rollback backups.

Affected tasks: T039, T098; requirements NFR-003, NFR-004, NFR-009, NFR-012; AC-032. Full acceptance stays open, including the held native Windows lane and clean offline provisioning.
