"""Private stopped-root recovery: bytes and ownership, rather than portable exchange."""

import json
import os
import sqlite3
import subprocess
import sys

import pytest

from xverse_studio.storage.core import Store


def recovery():
    from xverse_studio.host.recovery import (
        backup_full,
        restore_full,
        verify_backup,
        RecoveryError,
    )

    return backup_full, restore_full, verify_backup, RecoveryError


def stopped_root(root):
    store = Store(root)
    store.put("project", "project-1", {"projectId": "project-1", "revision": 1})
    store.put("session", "old-session", {"expiresAt": 9999999999})
    source = root / "projects/project-1/revisions/1/system.yaml"
    source.parent.mkdir(parents=True)
    source.write_bytes("name: System Ω\r\n".encode())
    journal = root / "runs/run-1/journal.ndjson"
    journal.parent.mkdir(parents=True)
    journal.write_bytes(b'{"immutable":"recorded"}\n')
    (root / "bootstrap.json").write_text('{"bootstrapToken":"expired-private-token"}')
    return store


def test_full_backup_restore_bytes_database_and_fresh_sessions(tmp_path):
    backup, restore, verify, _ = recovery()
    root, saved, target = (
        tmp_path / name for name in ["data Ω", "private backup Ω", "restored Ω"]
    )
    original = stopped_root(root)
    result = backup(root, saved)
    assert result["fileCount"] >= 3
    assert verify(saved)["integrity"] == "valid"
    assert not (saved / "files/bootstrap.json").exists()
    restore(saved, target)
    restored = Store(target)
    assert restored.get("project", "project-1") == original.get("project", "project-1")
    assert restored.all("session") == []
    for name in [
        "projects/project-1/revisions/1/system.yaml",
        "runs/run-1/journal.ndjson",
    ]:
        assert (target / name).read_bytes() == (root / name).read_bytes()
    assert not (target / "bootstrap.json").exists()
    assert not (target / ".recovery-incomplete").exists()


@pytest.mark.parametrize(
    "kind,body",
    [
        ("run", {"state": "unknown", "cleanup": "unknown"}),
        ("run", {"state": "running", "cleanup": "not_started"}),
        ("campaign", {"status": "pending"}),
        ("campaign", {"status": "complete", "children": [{"state": "pending"}]}),
        ("operation", {"status": "delegated"}),
    ],
)
def test_backup_refuses_unsettled_execution_without_modifying_source(
    tmp_path, kind, body
):
    backup, _, _, error = recovery()
    root = tmp_path / "source"
    store = stopped_root(root)
    store.put(kind, "unsettled", body)
    with pytest.raises(error, match="RECOVERY_EXECUTION_UNSETTLED"):
        backup(root, tmp_path / "backup")
    assert store.get(kind, "unsettled") == body
    assert not (tmp_path / "backup").exists()


def test_backup_and_restore_refuse_overwrite_nesting_and_link_escape(tmp_path):
    backup, restore, _, error = recovery()
    root = tmp_path / "source"
    stopped_root(root)
    with pytest.raises(error):
        backup(root, root / "nested")
    saved = tmp_path / "backup"
    backup(root, saved)
    with pytest.raises(error, match="RECOVERY_TARGET_EXISTS"):
        backup(root, saved)
    existing = tmp_path / "existing"
    existing.mkdir()
    (existing / "keep").write_bytes(b"preserve")
    with pytest.raises(error, match="RECOVERY_TARGET_EXISTS"):
        restore(saved, existing)
    assert (existing / "keep").read_bytes() == b"preserve"
    outside = tmp_path / "outside"
    outside.write_bytes(b"never copy")
    try:
        (root / "escape").symlink_to(outside)
    except OSError:
        pytest.skip("Host denies symlink creation; native Windows remains held")
    with pytest.raises(error, match="RECOVERY_UNSAFE_FILE"):
        backup(root, tmp_path / "unsafe")


@pytest.mark.parametrize(
    "mutation", ["corrupt", "extra", "missing", "path", "unknown-schema"]
)
def test_restore_rejects_corrupt_or_incompatible_backup_before_creating_target(
    tmp_path, mutation
):
    backup, restore, _, error = recovery()
    root, saved, target = (tmp_path / name for name in ["source", "backup", "target"])
    stopped_root(root)
    backup(root, saved)
    file = saved / "files/projects/project-1/revisions/1/system.yaml"
    if mutation == "corrupt":
        file.write_bytes(b"corruption")
    elif mutation == "extra":
        (saved / "files/extra").write_bytes(b"unlisted")
    elif mutation == "missing":
        file.unlink()
    else:
        manifest = json.loads((saved / "manifest.json").read_text())
        if mutation == "path":
            manifest["files"][0]["path"] = "../escape"
        else:
            manifest["databaseSchema"] = 999
        (saved / "manifest.json").write_text(json.dumps(manifest))
    with pytest.raises(error):
        restore(saved, target)
    assert not target.exists()


def test_cli_full_backup_and_restore_and_live_owner_refusal(tmp_path):
    _, _, _, _ = recovery()
    root, saved, target = (tmp_path / name for name in ["source", "backup", "restored"])
    stopped_root(root)
    command = [sys.executable, "-I", "-m", "xverse_studio.host.launcher"]
    for args in [
        ["--data-dir", str(root), "--backup-full", str(saved)],
        ["--data-dir", str(target), "--restore-from", str(saved)],
    ]:
        result = subprocess.run(
            command + args, capture_output=True, text=True, timeout=15
        )
        assert result.returncode == 0, result.stderr
        assert "expired-private-token" not in result.stdout + result.stderr
    from xverse_studio.host.ownership import own_root

    with own_root(root):
        result = subprocess.run(
            command
            + ["--data-dir", str(root), "--backup-full", str(tmp_path / "locked")],
            capture_output=True,
            text=True,
            timeout=15,
        )
        assert result.returncode != 0
        assert "RECOVERY_ROOT_OWNED" in result.stderr
    assert not (tmp_path / "locked").exists()


def test_unknown_database_version_and_incomplete_restore_refuse_startup(tmp_path):
    backup, _, _, error = recovery()
    root = tmp_path / "source"
    stopped_root(root)
    with sqlite3.connect(root / "studio.sqlite") as db:
        db.execute("PRAGMA user_version=999")
    with pytest.raises(error, match="RECOVERY_SCHEMA_UNSUPPORTED"):
        backup(root, tmp_path / "backup")
    (root / ".recovery-incomplete").write_text("interrupted")
    result = subprocess.run(
        [
            sys.executable,
            "-I",
            "-m",
            "xverse_studio.host.launcher",
            "--data-dir",
            str(root),
        ],
        capture_output=True,
        text=True,
        timeout=15,
    )
    assert result.returncode != 0
    assert "RECOVERY_INCOMPLETE" in result.stderr


def test_interrupted_restore_keeps_marker_and_original_backup(tmp_path, monkeypatch):
    backup, restore, verify, _ = recovery()
    from xverse_studio.host import recovery as module

    root, saved, target = (tmp_path / name for name in ["source", "backup", "target"])
    stopped_root(root)
    before = backup(root, saved)
    original_copy = module._copy
    calls = []

    def interrupted(source, destination):
        calls.append(source)
        if len(calls) == 2:
            raise OSError("controlled copy failure")
        return original_copy(source, destination)

    monkeypatch.setattr(module, "_copy", interrupted)
    with pytest.raises(OSError):
        restore(saved, target)
    assert (target / ".recovery-incomplete").is_file()
    assert verify(saved) == before


def test_missing_source_database_is_not_created_by_metadata_backup(tmp_path):
    target = tmp_path / "metadata.sqlite"
    source = tmp_path / "wrong-root"
    result = subprocess.run(
        [
            sys.executable,
            "-I",
            "-m",
            "xverse_studio.host.launcher",
            "--data-dir",
            str(source),
            "--backup",
            str(target),
        ],
        capture_output=True,
        text=True,
        timeout=15,
    )
    assert result.returncode != 0
    assert "RECOVERY_DATABASE_MISSING" in result.stderr
    assert not (source / "studio.sqlite").exists()
    assert not target.exists()


@pytest.mark.parametrize(
    "name",
    ["studio.sqlite-wal", "bootstrap.json", "studio.lock", ".recovery-incomplete"],
)
def test_forged_backup_cannot_restore_transient_authority_files(tmp_path, name):
    backup, restore, _, error = recovery()
    from xverse_studio.storage.core import digest

    root, saved, target = (tmp_path / key for key in ["source", "backup", "target"])
    stopped_root(root)
    backup(root, saved)
    forged = saved / "files" / name
    forged.write_bytes(b"forged")
    manifest = json.loads((saved / "manifest.json").read_text())
    manifest["files"].append({"path": name, "size": 6, "digest": digest(b"forged")})
    manifest["filesDigest"] = digest(manifest["files"])
    (saved / "manifest.json").write_text(json.dumps(manifest))
    with pytest.raises(error, match="RECOVERY_MANIFEST_INVALID"):
        restore(saved, target)
    assert not target.exists()


def test_lock_file_cannot_follow_symlink_or_block_on_special_file(tmp_path):
    backup, _, _, error = recovery()
    root = tmp_path / "source"
    stopped_root(root)
    outside = tmp_path / "outside"
    outside.write_bytes(b"preserve outside")
    (root / "studio.lock").symlink_to(outside)
    with pytest.raises(error, match="RECOVERY_UNSAFE_FILE"):
        backup(root, tmp_path / "symlink-backup")
    assert outside.read_bytes() == b"preserve outside"
    (root / "studio.lock").unlink()
    if hasattr(os, "mkfifo"):
        os.mkfifo(root / "studio.lock")
        with pytest.raises(error, match="RECOVERY_UNSAFE_FILE"):
            backup(root, tmp_path / "fifo-backup")


def test_cli_maintenance_does_not_resolve_source_or_destination_links(tmp_path):
    backup, _, _, _ = recovery()
    root = tmp_path / "source"
    stopped_root(root)
    alias = tmp_path / "source-link"
    alias.symlink_to(root, target_is_directory=True)
    command = [sys.executable, "-I", "-m", "xverse_studio.host.launcher"]
    selected = tmp_path / "selected-backup"
    result = subprocess.run(
        command + ["--data-dir", str(alias), "--backup-full", str(selected)],
        capture_output=True,
        text=True,
        timeout=15,
    )
    assert result.returncode != 0, (
        "Maintenance must not resolve a rejected source link into an admitted root"
    )
    assert not selected.exists()
    saved = tmp_path / "valid-backup"
    backup(root, saved)
    outside = tmp_path / "outside-destination"
    target = tmp_path / "target-link"
    target.symlink_to(outside, target_is_directory=True)
    result = subprocess.run(
        command + ["--data-dir", str(target), "--restore-from", str(saved)],
        capture_output=True,
        text=True,
        timeout=15,
    )
    assert result.returncode != 0
    assert not outside.exists()
