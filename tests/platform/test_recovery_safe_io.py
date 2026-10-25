"""Owned Linux acquisition-race fixtures; no Windows or provider execution."""

from pathlib import Path
import sqlite3

import pytest

from xverse_studio.host.recovery import backup_full, restore_full, RecoveryError
from xverse_studio.storage.core import Store


def private_root(path, marker):
    store = Store(path)
    store.put("review-marker", "scope", {"value": marker})
    return store


def test_transient_source_parent_symlink_cannot_substitute_outside_bytes(
    tmp_path, monkeypatch
):
    source = tmp_path / "source"
    private_root(source, "source")
    directory = source / "sub"
    directory.mkdir()
    file = directory / "owned.bin"
    file.write_bytes(b"original owned bytes")
    outside = tmp_path / "outside"
    outside.mkdir()
    (outside / "owned.bin").write_bytes(b"outside owned fixture")
    held = tmp_path / "held"
    original_open = Path.open
    swaps = []

    def raced_open(path, mode="r", *args, **kwargs):
        if path == file and mode == "rb":
            directory.rename(held)
            directory.symlink_to(outside, target_is_directory=True)
            try:
                handle = original_open(path, mode, *args, **kwargs)
                swaps.append(True)
            finally:
                directory.unlink()
                held.rename(directory)
            return handle
        return original_open(path, mode, *args, **kwargs)

    with monkeypatch.context() as patch:
        patch.setattr(Path, "open", raced_open)
        try:
            backup_full(source, tmp_path / "backup")
        except RecoveryError:
            pass
        else:
            assert (
                tmp_path / "backup/files/sub/owned.bin"
            ).read_bytes() == b"original owned bytes"
    assert file.read_bytes() == b"original owned bytes"


def test_sqlite_original_path_is_never_reopened_during_backup(tmp_path, monkeypatch):
    source = tmp_path / "source"
    private_root(source, "source")
    outside = tmp_path / "outside"
    private_root(outside, "outside")
    held = tmp_path / "held"
    connect = sqlite3.connect
    prefix = (source / "studio.sqlite").as_uri()
    swaps = []

    def raced_connect(path, *args, **kwargs):
        if isinstance(path, str) and path.startswith(prefix):
            source.rename(held)
            source.symlink_to(outside, target_is_directory=True)
            try:
                connection = connect(path, *args, **kwargs)
                swaps.append(True)
            finally:
                source.unlink()
                held.rename(source)
            return connection
        return connect(path, *args, **kwargs)

    with monkeypatch.context() as patch:
        patch.setattr(sqlite3, "connect", raced_connect)
        try:
            backup_full(source, tmp_path / "backup")
        except RecoveryError:
            pass
        else:
            with connect(tmp_path / "backup/files/studio.sqlite") as db:
                assert (
                    '"source"'
                    in db.execute(
                        "SELECT body FROM records WHERE kind='review-marker'"
                    ).fetchone()[0]
                )
    assert Store(source).get("review-marker", "scope")["value"] == "source"


def test_stopped_root_committed_wal_is_preserved_without_source_sqlite_writes(tmp_path):
    source = tmp_path / "source"
    private_root(source, "initial")
    connection = sqlite3.connect(source / "studio.sqlite")
    try:
        connection.execute("PRAGMA journal_mode=WAL")
        connection.execute("PRAGMA wal_autocheckpoint=0")
        connection.execute(
            "UPDATE records SET body=? WHERE kind='review-marker'",
            ('{"value":"committed-in-wal"}',),
        )
        connection.commit()
        before_db = (source / "studio.sqlite").read_bytes()
        before_wal = (source / "studio.sqlite-wal").read_bytes()
        backup_full(source, tmp_path / "backup")
        assert (source / "studio.sqlite").read_bytes() == before_db
        assert (source / "studio.sqlite-wal").read_bytes() == before_wal
        restore_full(tmp_path / "backup", tmp_path / "restored")
        assert (
            Store(tmp_path / "restored").get("review-marker", "scope")["value"]
            == "committed-in-wal"
        )
    finally:
        connection.close()


def test_anchor_reader_rejects_parent_symlink_and_preserves_root_boundary(tmp_path):
    from xverse_studio.security.managed_io import open_read, SafeIOError

    root = tmp_path / "root"
    root.mkdir()
    outside = tmp_path / "outside"
    outside.mkdir()
    (outside / "value").write_bytes(b"outside")
    (root / "redirect").symlink_to(outside, target_is_directory=True)
    with pytest.raises(SafeIOError):
        with open_read(root, root / "redirect/value") as stream:
            stream.read(1)
    with pytest.raises(SafeIOError):
        with open_read(root, outside / "value") as stream:
            stream.read(1)


def test_actual_openat_parent_swap_keeps_acquired_directory(tmp_path, monkeypatch):
    import os
    from xverse_studio.security.managed_io import open_read

    root = tmp_path / "root"
    root.mkdir()
    parent = root / "sub"
    parent.mkdir()
    (parent / "value").write_bytes(b"owned")
    outside = tmp_path / "outside"
    outside.mkdir()
    (outside / "value").write_bytes(b"outside")
    held = tmp_path / "held"
    original = os.open
    swaps = []

    def raced(name, flags, *args, **kwargs):
        if name == "value" and kwargs.get("dir_fd") is not None:
            parent.rename(held)
            parent.symlink_to(outside, target_is_directory=True)
            try:
                result = original(name, flags, *args, **kwargs)
                swaps.append(True)
            finally:
                parent.unlink()
                held.rename(parent)
            return result
        return original(name, flags, *args, **kwargs)

    monkeypatch.setattr(os, "open", raced)
    with open_read(root, parent / "value") as stream:
        assert stream.read() == b"owned"
    assert swaps


def test_actual_target_parent_swap_never_writes_outside(tmp_path, monkeypatch):
    import os
    from xverse_studio.security.managed_io import open_write

    root = tmp_path / "root"
    root.mkdir()
    parent = root / "sub"
    parent.mkdir()
    outside = tmp_path / "outside"
    outside.mkdir()
    held = tmp_path / "held"
    original = os.open
    swaps = []

    def raced(name, flags, *args, **kwargs):
        if name == "value" and flags & os.O_CREAT and kwargs.get("dir_fd") is not None:
            parent.rename(held)
            parent.symlink_to(outside, target_is_directory=True)
            try:
                result = original(name, flags, *args, **kwargs)
                swaps.append(True)
            finally:
                parent.unlink()
                held.rename(parent)
            return result
        return original(name, flags, *args, **kwargs)

    monkeypatch.setattr(os, "open", raced)
    with open_write(root, parent / "value") as stream:
        stream.write(b"owned")
    assert swaps
    assert (parent / "value").read_bytes() == b"owned"
    assert not (outside / "value").exists()


def test_acquisition_context_preserves_caller_exception(tmp_path):
    from xverse_studio.security.managed_io import open_read

    file = tmp_path / "value"
    file.write_bytes(b"owned")
    failure = OSError("owned caller failure")
    with pytest.raises(OSError) as caught:
        with open_read(tmp_path, file):
            raise failure
    assert caught.value is failure


def test_recovery_does_not_create_staging_inside_backup(tmp_path):
    source = tmp_path / "source"
    private_root(source, "source")
    saved = tmp_path / "backup"
    backup_full(source, saved)
    before = sorted(str(p.relative_to(saved)) for p in saved.rglob("*"))
    restore_full(saved, tmp_path / "restored")
    assert sorted(str(p.relative_to(saved)) for p in saved.rglob("*")) == before


def test_recovery_root_acquisition_does_not_resolve_untrusted_paths(
    tmp_path, monkeypatch
):
    source = tmp_path / "source"
    private_root(source, "source")
    original = Path.resolve

    def forbidden(path, *args, **kwargs):
        if path == source:
            raise AssertionError("must acquire lexical path without following links")
        return original(path, *args, **kwargs)

    monkeypatch.setattr(Path, "resolve", forbidden)
    backup_full(source, tmp_path / "backup")


def test_locked_root_identity_survives_ordinary_directory_replacement(
    tmp_path, monkeypatch
):
    import os

    source = tmp_path / "source"
    private_root(source, "source")
    foreign = tmp_path / "foreign"
    private_root(foreign, "foreign")
    original_bytes = (source / "studio.sqlite").read_bytes()
    foreign_bytes = (foreign / "studio.sqlite").read_bytes()
    inode = source.stat().st_ino
    held = tmp_path / "held"
    original = os.open
    swaps = []

    def raced(name, flags, *args, **kwargs):
        descriptor = kwargs.get("dir_fd")
        if (
            name == "studio.sqlite"
            and descriptor is not None
            and os.fstat(descriptor).st_ino == inode
            and not swaps
        ):
            source.rename(held)
            foreign.rename(source)
            swaps.append(True)
            try:
                return original(name, flags, *args, **kwargs)
            finally:
                source.rename(foreign)
                held.rename(source)
        return original(name, flags, *args, **kwargs)

    monkeypatch.setattr(os, "open", raced)
    backup_full(source, tmp_path / "backup")
    assert swaps
    with sqlite3.connect(tmp_path / "backup/files/studio.sqlite") as db:
        assert (
            '"source"'
            in db.execute(
                "SELECT body FROM records WHERE kind='review-marker'"
            ).fetchone()[0]
        )
    assert (source / "studio.sqlite").read_bytes() == original_bytes
    assert (foreign / "studio.sqlite").read_bytes() == foreign_bytes


def test_reserved_output_identity_survives_ordinary_directory_replacement(
    tmp_path, monkeypatch
):
    import os

    source = tmp_path / "source"
    private_root(source, "source")
    saved = tmp_path / "backup"
    foreign = tmp_path / "foreign"
    foreign.mkdir()
    sentinel = foreign / "sentinel"
    sentinel.write_bytes(b"outside owned fixture")
    held = tmp_path / "held"
    original = os.open
    swaps = []

    def raced(name, flags, *args, **kwargs):
        descriptor = kwargs.get("dir_fd")
        if (
            name == "manifest.json"
            and flags & os.O_CREAT
            and descriptor is not None
            and not swaps
        ):
            saved.rename(held)
            foreign.rename(saved)
            swaps.append(True)
            try:
                return original(name, flags, *args, **kwargs)
            finally:
                saved.rename(foreign)
                held.rename(saved)
        return original(name, flags, *args, **kwargs)

    monkeypatch.setattr(os, "open", raced)
    backup_full(source, saved)
    assert swaps
    assert (saved / "manifest.json").is_file()
    assert sorted(p.name for p in foreign.iterdir()) == ["sentinel"]
    assert sentinel.read_bytes() == b"outside owned fixture"


def test_stage_exit_preserves_still_active_output_anchor(tmp_path):
    from contextlib import ExitStack
    from xverse_studio.host import recovery

    source = tmp_path / "source"
    private_root(source, "source")
    destination = tmp_path / "destination"
    with ExitStack() as operation:
        operation.enter_context(recovery._bound(source))
        with recovery._staged_database(source):
            anchor = operation.enter_context(recovery._new_target(destination))
            assert recovery._io_root(destination) is anchor
        assert recovery._io_root(destination) is anchor
    assert recovery._io_root(destination) == Path("/")


def test_permanently_replaced_output_never_reports_success(tmp_path, monkeypatch):
    import os

    source = tmp_path / "source"
    private_root(source, "source")
    target = tmp_path / "target"
    foreign = tmp_path / "foreign"
    foreign.mkdir()
    (foreign / "sentinel").write_bytes(b"outside owned fixture")
    held = tmp_path / "held"
    original = os.open
    swaps = []

    def raced(name, flags, *args, **kwargs):
        if (
            name == "manifest.json"
            and flags & os.O_CREAT
            and kwargs.get("dir_fd") is not None
            and not swaps
        ):
            target.rename(held)
            foreign.rename(target)
            swaps.append(True)
        return original(name, flags, *args, **kwargs)

    monkeypatch.setattr(os, "open", raced)
    with pytest.raises(RecoveryError, match="RECOVERY_SOURCE_CHANGED"):
        backup_full(source, target)
    assert swaps
    assert sorted(p.name for p in target.iterdir()) == ["sentinel"]
    assert (target / "sentinel").read_bytes() == b"outside owned fixture"


def test_late_restore_namespace_change_recreates_owned_marker(tmp_path, monkeypatch):
    import os

    source = tmp_path / "source"
    private_root(source, "source")
    backup = tmp_path / "backup"
    backup_full(source, backup)
    target = tmp_path / "target"
    foreign = tmp_path / "foreign"
    foreign.mkdir()
    (foreign / "sentinel").write_bytes(b"outside owned fixture")
    held = tmp_path / "held"
    original = os.unlink
    swaps = []

    def raced(name, *args, **kwargs):
        if (
            name == ".recovery-incomplete"
            and kwargs.get("dir_fd") is not None
            and not swaps
        ):
            target.rename(held)
            foreign.rename(target)
            swaps.append(True)
        return original(name, *args, **kwargs)

    monkeypatch.setattr(os, "unlink", raced)
    with pytest.raises(RecoveryError, match="RECOVERY_SOURCE_CHANGED"):
        restore_full(backup, target)
    assert swaps
    assert (held / "studio.sqlite").is_file()
    assert (held / ".recovery-incomplete").is_file()
    assert sorted(p.name for p in target.iterdir()) == ["sentinel"]
    assert (target / "sentinel").read_bytes() == b"outside owned fixture"


def test_late_input_namespace_change_recreates_restore_marker(tmp_path, monkeypatch):
    import os

    source = tmp_path / "source"
    private_root(source, "source")
    backup = tmp_path / "backup"
    backup_full(source, backup)
    target = tmp_path / "target"
    held = tmp_path / "held-backup"
    original = os.unlink
    swaps = []

    def raced(name, *args, **kwargs):
        if (
            name == ".recovery-incomplete"
            and kwargs.get("dir_fd") is not None
            and not swaps
        ):
            backup.rename(held)
            swaps.append(True)
        return original(name, *args, **kwargs)

    monkeypatch.setattr(os, "unlink", raced)
    with pytest.raises(RecoveryError):
        restore_full(backup, target)
    assert swaps
    assert (target / "studio.sqlite").is_file()
    assert (target / ".recovery-incomplete").is_file()
