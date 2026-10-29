# Full recovery review — 2026-10-25

Candidate before repair: ba5ef0a33c8d161096420cad4b868205830ba1fd.

- REC-001: only metadata backup is executable; complete matching source/evidence recovery requires manual filesystem copying. Add a private stopped-root backup/verify/restore workflow with exact file digests and no overwrite.
- REC-002: restoring unsettled worker/campaign/operation state into a second root could replay ownership or pending scheduling. Require settled execution before backup and restore; retain immutable historical bytes and invalidate browser sessions on restore.
- REC-003: existing metadata backup can create an empty source database when the selected root is wrong. Refuse missing databases before opening SQLite.
- REC-004: interrupted restore must remain visibly unusable, rather than allowing a partial root to start.

Tests first: `.venv/bin/python -I -m pytest tests/platform/test_full_recovery.py --basetemp=.studio-local/recovery-first -q --tb=short`, with host plugins disabled and TMPDIR on loop10: **13 failed**, all because `xverse_studio.host.recovery` does not exist. No Windows installation/test executed. This is gap reproduction, not acceptance evidence.

CLI-REC-001 (2026-10-25, before repair): the launcher calls Path.resolve before the full-backup/restore adapter. A source-root symlink therefore bypasses the recovery function's explicit no-link policy: the real native CLI reports a valid backup for the linked root. The new `test_cli_maintenance_does_not_resolve_source_or_destination_links` failed in0.31s before repair. Pass lexical absolute input to full-maintenance admission; retain the existing ordinary launch-root behavior separately. Also reject a dangling restore-target link before creating the pointed-to directory. All fixture roots are private loop10 test data.
