"""Transactional local metadata; immutable file revisions hold authored XDL."""

from __future__ import annotations
import contextlib
import hashlib
import json
import os
from pathlib import Path
import sqlite3
import threading
import time
import uuid


def uid(prefix=""):
    return prefix + str(uuid.uuid4())


def canonical(value):
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    )


def digest(value):
    raw = value if isinstance(value, bytes) else canonical(value).encode()
    return "sha256:" + hashlib.sha256(raw).hexdigest()


def atomic(path: Path, data: bytes):
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_name(path.name + "." + uuid.uuid4().hex + ".tmp")
    try:
        with temp.open("xb") as f:
            f.write(data)
            f.flush()
            os.fsync(f.fileno())
        os.replace(temp, path)
    finally:
        temp.unlink(missing_ok=True)


def contained(root: Path, path: Path):
    if not path.resolve().is_relative_to(root.resolve()):
        raise ValueError("Path escapes the managed workspace")
    return path


class Problem(Exception):
    def __init__(self, code, message, status=422, **details):
        self.code, self.message, self.status, self.details = (
            code,
            message,
            status,
            details,
        )
        super().__init__(message)


class Store:
    def __init__(self, root: Path):
        self.root = root.resolve()
        self.root.mkdir(parents=True, exist_ok=True)
        try:
            self.root.chmod(0o700)
        except OSError:
            pass
        self.dbpath = self.root / "studio.sqlite"
        self.lock = threading.RLock()
        self._rollback_hooks = {}
        with self.tx() as db:
            version = db.execute("PRAGMA user_version").fetchone()[0]
            if version not in (0, 1):
                raise Problem(
                    "MIGRATION_REQUIRED",
                    "Unsupported database version; restore a supported backup.",
                    503,
                )
            db.execute(
                "CREATE TABLE IF NOT EXISTS records (kind TEXT NOT NULL, id TEXT NOT NULL, body TEXT NOT NULL, PRIMARY KEY(kind,id))"
            )
            db.execute(
                "CREATE TABLE IF NOT EXISTS idempotency (scope TEXT NOT NULL, key TEXT NOT NULL, fingerprint TEXT NOT NULL, result TEXT NOT NULL, PRIMARY KEY(scope,key))"
            )
            db.execute("PRAGMA user_version=1")

    @contextlib.contextmanager
    def tx(self):
        with self.lock:
            db = sqlite3.connect(self.dbpath, timeout=15)
            try:
                db.execute("PRAGMA journal_mode=WAL")
                db.execute("PRAGMA foreign_keys=ON")
                db.execute("BEGIN IMMEDIATE")
                self._rollback_hooks[id(db)] = []
                yield db
                db.commit()
            except BaseException:
                uncommitted = db.in_transaction
                db.rollback()
                if uncommitted:
                    for cleanup in reversed(self._rollback_hooks.get(id(db), [])):
                        cleanup()
                raise
            finally:
                self._rollback_hooks.pop(id(db), None)
                db.close()

    def on_rollback(self, db, cleanup):
        self._rollback_hooks[id(db)].append(cleanup)

    def get(self, kind, id, db=None):
        if db is None:
            with self.tx() as db:
                return self.get(kind, id, db)
        row = db.execute(
            "SELECT body FROM records WHERE kind=? AND id=?", (kind, id)
        ).fetchone()
        if row is None:
            raise Problem("NOT_FOUND", "Requested record was not found.", 404)
        return json.loads(row[0])

    def put(self, kind, id, body, db=None):
        if db is None:
            with self.tx() as db:
                return self.put(kind, id, body, db)
        db.execute(
            "INSERT INTO records VALUES(?,?,?) ON CONFLICT(kind,id) DO UPDATE SET body=excluded.body",
            (kind, id, canonical(body)),
        )
        return body

    def all(self, kind, db=None):
        if db is None:
            with self.tx() as db:
                return self.all(kind, db)
        return [
            json.loads(r[0])
            for r in db.execute(
                "SELECT body FROM records WHERE kind=? ORDER BY rowid DESC", (kind,)
            )
        ]

    def idempotent(self, principal, route, key, payload, fn):
        if not key or len(key) > 128:
            raise Problem(
                "IDEMPOTENCY_REQUIRED",
                "Supply an Idempotency-Key of at most 128 characters.",
                428,
            )
        scope = principal + ":" + route
        fingerprint = digest(payload)
        with self.tx() as db:
            row = db.execute(
                "SELECT fingerprint,result FROM idempotency WHERE scope=? AND key=?",
                (scope, key),
            ).fetchone()
            if row:
                if row[0] != fingerprint:
                    raise Problem(
                        "IDEMPOTENCY_CONFLICT",
                        "This key already identifies a different request.",
                        409,
                    )
                return json.loads(row[1]), False
            result = fn(db)
            db.execute(
                "INSERT INTO idempotency VALUES(?,?,?,?)",
                (scope, key, fingerprint, canonical(result)),
            )
            return result, True
