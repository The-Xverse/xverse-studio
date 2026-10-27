"""Private local backups. These contain secrets and are not portable project bundles.

All effects are explicit and stopped-root only. A new destination is reserved before
copying, and an incomplete restore is never eligible for launcher startup.
"""

from __future__ import annotations

import hashlib
from contextvars import ContextVar
from contextlib import closing, contextmanager, ExitStack
import json
import os
from pathlib import Path, PurePosixPath
import sqlite3
import stat
import time
import unicodedata
import uuid

from xverse_studio.host.ownership import own_root, RootOwnedError, RootUnsafeError
from xverse_studio.security.files import safe_name
from xverse_studio.storage.core import Problem, canonical, digest
from xverse_studio.security.managed_io import (
    SafeIOError,
    AnchoredDirectory,
    create_directory,
    open_read,
    open_write,
    open_directory,
    make_directory,
    stat_file,
    remove_tree,
    unlink,
)

MAX_FILES = 100_000
MAX_BYTES = 64 * 1024**3
MAX_MANIFEST = 32 * 1024**2
TRANSIENT = {"studio.lock", "bootstrap.json", "studio.sqlite-wal", "studio.sqlite-shm"}
TERMINAL = {
    "run": {"stopped", "failed"},
    "campaign": {"complete", "cancelled"},
    "operation": {"completed", "failed", "rejected", "cancelled"},
}


_ANCHORS = ContextVar("recovery_anchors", default=())


def _io_root(path):
    path = Path(path).absolute()
    candidates = [a for a in _ANCHORS.get() if path.is_relative_to(a.path)]
    return max(candidates, key=lambda a: len(a.path.parts)) if candidates else Path("/")


def _check_named(anchor):
    with open_directory(Path("/"), anchor.path) as descriptor:
        expected, current = os.fstat(anchor.descriptor), os.fstat(descriptor)
        if (expected.st_dev, expected.st_ino) != (current.st_dev, current.st_ino):
            _fail("RECOVERY_SOURCE_CHANGED")


@contextmanager
def _bound(path, *, check_name=True):
    with open_directory(_io_root(path), path) as descriptor:
        anchor = AnchoredDirectory(Path(path).absolute(), descriptor)
        _ANCHORS.set((*_ANCHORS.get(), anchor))
        try:
            yield anchor
            if check_name:
                _check_named(anchor)
        finally:
            _ANCHORS.set(tuple(item for item in _ANCHORS.get() if item is not anchor))


class RecoveryError(ValueError):
    pass


def _fail(code):
    raise RecoveryError(code)


def _root(path):
    path = Path(path).absolute()
    if ".." in path.parts or any(p.is_symlink() for p in [path, *path.parents]):
        _fail("RECOVERY_UNSAFE_FILE")
    return path


def _names(entries):
    folded = set()
    spellings = {}
    for name in entries:
        try:
            safe_name(name)
        except (ValueError, Problem):
            _fail("RECOVERY_UNSAFE_FILE")
        folded_name = unicodedata.normalize("NFC", name).casefold()
        if folded_name in folded:
            _fail("RECOVERY_PATH_COLLISION")
        folded.add(folded_name)
        for part in [name, *_parents(name)]:
            key = unicodedata.normalize("NFC", part).casefold()
            if key in spellings and spellings[key] != part:
                _fail("RECOVERY_PATH_COLLISION")
            spellings[key] = part
    if any(p in folded for name in folded for p in _parents(name)):
        _fail("RECOVERY_PATH_COLLISION")


def _parents(name):
    return [str(p) for p in PurePosixPath(name).parents if str(p) != "."]


def _inventory(root, *, skip_transient=False):
    files, total = [], 0
    with open_directory(_io_root(root), root) as descriptor:
        # Root alias is owned and held; directory entries are never followed.
        scan = Path(f"/proc/self/fd/{descriptor}")
        for parent, dirs, names in os.walk(scan, followlinks=False):
            for name in [*dirs, *names]:
                path = Path(parent) / name
                info = path.lstat()
                if stat.S_ISLNK(info.st_mode) or not (
                    stat.S_ISDIR(info.st_mode) or stat.S_ISREG(info.st_mode)
                ):
                    _fail("RECOVERY_UNSAFE_FILE")
                if stat.S_ISREG(info.st_mode):
                    relative = path.relative_to(scan).as_posix()
                    if skip_transient and relative in TRANSIENT:
                        continue
                    total += info.st_size
                    files.append(relative)
                    if len(files) > MAX_FILES or total > MAX_BYTES:
                        _fail("RECOVERY_LIMIT_EXCEEDED")
    _names(files)
    return sorted(files)


@contextmanager
def _safe_errors():
    try:
        yield
    except SafeIOError as exc:
        code = {
            "SECURE_IO_UNAVAILABLE": "RECOVERY_SECURE_IO_UNAVAILABLE",
            "SOURCE_CHANGED": "RECOVERY_SOURCE_CHANGED",
            "TARGET_EXISTS": "RECOVERY_TARGET_EXISTS",
        }.get(exc.code, "RECOVERY_UNSAFE_FILE")
        raise RecoveryError(code) from None


def _hash(path):
    hasher, size = hashlib.sha256(), 0
    with _safe_errors(), open_read(_io_root(path), path) as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            size += len(chunk)
            if size > MAX_BYTES:
                _fail("RECOVERY_LIMIT_EXCEEDED")
            hasher.update(chunk)
    return {"size": size, "digest": "sha256:" + hasher.hexdigest()}


def _stream_copy(src, target):
    hasher, size = hashlib.sha256(), 0
    with open_write(_io_root(target), target, parents=True) as dst:
        for chunk in iter(lambda: src.read(1024 * 1024), b""):
            size += len(chunk)
            if size > MAX_BYTES:
                _fail("RECOVERY_LIMIT_EXCEEDED")
            dst.write(chunk)
            hasher.update(chunk)
    return {"size": size, "digest": "sha256:" + hasher.hexdigest()}


def _copy(source, target):
    with _safe_errors(), open_read(_io_root(source), source) as src:
        identity = _stream_copy(src, target)
    if _hash(target) != identity:
        _fail("RECOVERY_SOURCE_CHANGED")
    return identity


@contextmanager
def _staged_database(source, *, sanitize=False, staging_parent=None):
    """Copy DB+WAL via held source handles; SQLite opens ONLY private staging.

    The directory-descriptor URI retains WAL lookup in the staged directory.
    Original source descriptors remain held and verified until normalization
    and the caller's copy complete. No original SQLite connection is opened.
    """
    stage = (staging_parent or source.parent) / (".studio-recovery-" + uuid.uuid4().hex)
    with _safe_errors():
        with ExitStack() as reservation:
            stage_anchor = reservation.enter_context(
                _new_target(stage, check_name=False)
            )
            info = os.fstat(stage_anchor.descriptor)
            try:
                with ExitStack() as stack:
                    db = stack.enter_context(
                        open_read(_io_root(source), source / "studio.sqlite")
                    )
                    wal_path = source / "studio.sqlite-wal"
                    try:
                        wal = stack.enter_context(
                            open_read(_io_root(wal_path), wal_path)
                        )
                    except SafeIOError as exc:
                        if exc.code != "FILE_MISSING":
                            raise
                        wal = None
                    _stream_copy(db, stage / "studio.sqlite")
                    if wal is not None:
                        _stream_copy(wal, stage / "studio.sqlite-wal")
                    # All SQLite path acquisition is rooted in a held directory FD;
                    # its absolute ancestors are never reopened by SQLite.
                    with open_directory(_io_root(stage), stage) as directory:
                        base = f"file:/proc/self/fd/{directory}/"
                        with open_write(_io_root(stage), stage / "normalized.sqlite"):
                            pass
                        with (
                            closing(
                                sqlite3.connect(
                                    base + "studio.sqlite?mode=rw", uri=True
                                )
                            ) as src,
                            closing(
                                sqlite3.connect(
                                    base + "normalized.sqlite?mode=rw", uri=True
                                )
                            ) as dst,
                        ):
                            src.backup(dst)
                            dst.execute("PRAGMA journal_mode=DELETE")
                            if sanitize:
                                with dst:
                                    dst.execute(
                                        "DELETE FROM records WHERE kind='session'"
                                    )
                        _database(stage / "normalized.sqlite", immutable=True)
                        yield stage / "normalized.sqlite"
                    if wal is None:
                        try:
                            stat_file(_io_root(wal_path), wal_path)
                        except SafeIOError as exc:
                            if exc.code != "FILE_MISSING":
                                raise
                        else:
                            _fail("RECOVERY_SOURCE_CHANGED")
            finally:
                remove_tree(
                    Path("/"), stage, expected_identity=(info.st_dev, info.st_ino)
                )


def _settled_leases(db):
    """A stopped backend does not establish that a provider lease was released."""
    from xverse_studio.lab import LabError
    from xverse_studio.lab.persistence import validate_snapshot

    rows = db.execute("SELECT id,length(CAST(body AS BLOB)) FROM records WHERE kind='lab_registry' LIMIT 2").fetchall()
    if not rows:
        return
    if len(rows) != 1 or rows[0][0] != 'leases' or rows[0][1] > 2 * 1024 * 1024:
        _fail('RECOVERY_DATABASE_INVALID')
    try:
        raw = db.execute("SELECT body FROM records WHERE kind='lab_registry' AND id='leases'").fetchone()[0]
        snapshot = validate_snapshot(json.loads(raw))
    except (LabError, ValueError, TypeError, RecursionError):
        _fail('RECOVERY_DATABASE_INVALID')
    if any(record['status'] not in {'released', 'expired'} for record in snapshot['records']):
        _fail('RECOVERY_EXECUTION_UNSETTLED')


def _database(path, *, immutable=False):
    try:
        with (
            _safe_errors(),
            open_read(_io_root(path), path) as held,
            closing(
                sqlite3.connect(
                    f"file:/proc/self/fd/{held.fileno()}?mode=ro&immutable=1", uri=True
                )
            ) as db,
        ):
            if db.execute("PRAGMA user_version").fetchone()[0] != 1:
                _fail("RECOVERY_SCHEMA_UNSUPPORTED")
            if db.execute("PRAGMA integrity_check").fetchall() != [("ok",)]:
                _fail("RECOVERY_DATABASE_INVALID")
            _settled_leases(db)
            for kind, raw in db.execute(
                "SELECT kind,body FROM records WHERE kind IN ('run','campaign','operation')"
            ):
                record = json.loads(raw)
                if not isinstance(record, dict):
                    _fail("RECOVERY_DATABASE_INVALID")
                if (
                    record.get("state" if kind == "run" else "status")
                    not in TERMINAL[kind]
                ):
                    _fail("RECOVERY_EXECUTION_UNSETTLED")
                if kind == "run" and record.get("cleanup") not in {
                    "complete",
                    "not_started",
                }:
                    _fail("RECOVERY_EXECUTION_UNSETTLED")
                if kind == "campaign" and any(
                    not isinstance(child, dict)
                    or child.get("state")
                    not in {"stopped", "failed", "rejected", "cancelled"}
                    for child in record.get("children", [])
                ):
                    _fail("RECOVERY_EXECUTION_UNSETTLED")
    except (sqlite3.Error, ValueError, TypeError) as exc:
        if isinstance(exc, RecoveryError):
            raise
        raise RecoveryError("RECOVERY_DATABASE_INVALID") from None


@contextmanager
def _new_target(path, *, check_name=True):
    with _safe_errors(), create_directory(_io_root(path), path, parents=True) as anchor:
        _ANCHORS.set((*_ANCHORS.get(), anchor))
        try:
            yield anchor
            if check_name:
                _check_named(anchor)
        finally:
            _ANCHORS.set(tuple(item for item in _ANCHORS.get() if item is not anchor))


def backup_full(source, destination):
    source, destination = _root(source), _root(destination)
    if (
        source == destination
        or destination.is_relative_to(source)
        or source.is_relative_to(destination)
    ):
        _fail("RECOVERY_NESTED_TARGET")
    if not source.is_dir():
        _fail("RECOVERY_DATABASE_MISSING")
    try:
        with _safe_errors(), ExitStack() as operation:
            source_anchor = operation.enter_context(_bound(source))
            operation.enter_context(
                own_root(Path(f"/proc/self/fd/{source_anchor.descriptor}"))
            )
            try:
                stat_file(source_anchor, source / ".recovery-incomplete")
            except SafeIOError as exc:
                if exc.code != "FILE_MISSING":
                    raise
            else:
                _fail("RECOVERY_INCOMPLETE")
            files = _inventory(source, skip_transient=True)
            with _staged_database(source) as database:
                operation.enter_context(_new_target(destination))
                entries = []
                data = destination / "files"
                make_directory(_io_root(data), data, exclusive=True)
                for name in files:
                    identity = _copy(
                        database if name == "studio.sqlite" else source / name,
                        data / name,
                    )
                    entries.append({"path": name, **identity})
                _database(data / "studio.sqlite", immutable=True)
                if _inventory(source, skip_transient=True) != files:
                    _fail("RECOVERY_SOURCE_CHANGED")
            manifest = {
                "format": "studio.private-backup",
                "version": 1,
                "databaseSchema": 1,
                "createdAt": time.time(),
                "files": entries,
                "filesDigest": digest(entries),
            }
            with open_write(
                _io_root(destination), destination / "manifest.json"
            ) as output:
                output.write(canonical(manifest).encode())
            return _verified_manifest(destination)[1]
    except RootOwnedError:
        raise RecoveryError("RECOVERY_ROOT_OWNED") from None
    except RootUnsafeError:
        raise RecoveryError("RECOVERY_UNSAFE_FILE") from None


def _verified_manifest(backup):
    backup = _root(backup)
    manifest_file = backup / "manifest.json"
    try:
        with (
            _safe_errors(),
            open_read(_io_root(manifest_file), manifest_file) as stream,
        ):
            raw = stream.read(MAX_MANIFEST + 1)
            if len(raw) > MAX_MANIFEST:
                _fail("RECOVERY_MANIFEST_INVALID")
        manifest = json.loads(raw.decode("utf-8"))
        if (
            manifest["format"] != "studio.private-backup"
            or manifest["version"] != 1
            or manifest["databaseSchema"] != 1
        ):
            _fail("RECOVERY_SCHEMA_UNSUPPORTED")
        entries = manifest["files"]
        if (
            not isinstance(entries, list)
            or not 1 <= len(entries) <= MAX_FILES
            or digest(entries) != manifest["filesDigest"]
        ):
            _fail("RECOVERY_MANIFEST_INVALID")
        names = [entry["path"] for entry in entries]
        if any(not isinstance(name, str) for name in names):
            _fail("RECOVERY_MANIFEST_INVALID")
        _names(names)
        if "studio.sqlite" not in names or any(
            name in TRANSIENT | {".recovery-incomplete"} for name in names
        ):
            _fail("RECOVERY_MANIFEST_INVALID")
        data = _root(backup / "files")
        if _inventory(data) != sorted(names):
            _fail("RECOVERY_FILES_MISMATCH")
        for entry in entries:
            if _hash(data / entry["path"]) != {k: entry[k] for k in ("size", "digest")}:
                _fail("RECOVERY_DIGEST_MISMATCH")
        _database(data / "studio.sqlite", immutable=True)
        return manifest, {
            "integrity": "valid",
            "fileCount": len(entries),
            "bytes": sum(e["size"] for e in entries),
            "filesDigest": manifest["filesDigest"],
        }
    except (KeyError, TypeError, json.JSONDecodeError):
        raise RecoveryError("RECOVERY_MANIFEST_INVALID") from None


def verify_backup(backup):
    backup = _root(backup)
    with _safe_errors(), _bound(backup):
        return _verified_manifest(backup)[1]


def restore_full(backup, destination):
    backup, destination = _root(backup), _root(destination)
    if destination.is_relative_to(backup) or backup.is_relative_to(destination):
        _fail("RECOVERY_NESTED_TARGET")
    with _safe_errors(), ExitStack() as operation:
        backup_anchor = operation.enter_context(_bound(backup, check_name=False))
        manifest, verified = _verified_manifest(backup)
        destination_anchor = operation.enter_context(
            _new_target(destination, check_name=False)
        )
        marker = destination / ".recovery-incomplete"
        with open_write(destination_anchor, marker) as output:
            output.write(
                b"Restore interrupted. Refuse startup; restore into a different new root.\n"
            )
        operation.enter_context(
            own_root(Path(f"/proc/self/fd/{destination_anchor.descriptor}"))
        )
        with _staged_database(
            backup / "files", sanitize=True, staging_parent=destination.parent
        ) as database:
            for entry in manifest["files"]:
                source = backup / "files" / entry["path"]
                expected = {k: entry[k] for k in ("size", "digest")}
                if entry["path"] == "studio.sqlite":
                    if _hash(source) != expected:
                        _fail("RECOVERY_SOURCE_CHANGED")
                    _copy(database, destination / entry["path"])
                elif _copy(source, destination / entry["path"]) != expected:
                    _fail("RECOVERY_SOURCE_CHANGED")
        _database(destination / "studio.sqlite", immutable=True)
        _check_named(backup_anchor)
        _check_named(destination_anchor)
        unlink(destination_anchor, marker)
        try:
            _check_named(backup_anchor)
            _check_named(destination_anchor)
        except BaseException:
            # A late namespace mismatch must not leave the owned restored root
            # eligible for startup after reporting an interrupted restore.
            with open_write(destination_anchor, marker) as output:
                output.write(b"Restore target binding changed. Refuse startup.\n")
            raise
    return {**verified, "status": "restored", "sessionsInvalidated": True}
