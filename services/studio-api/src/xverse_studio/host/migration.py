"""Explicit stopped-root copy migration; never starts providers or execution."""

from contextlib import closing
import hashlib
import sqlite3

from xverse_studio.host import recovery as r
from xverse_studio.storage.core import canonical, digest


REPORT = "migration-report.json"


def _metadata_identity(path):
    """Hash stored text in bounded chunks, excluding invalidated browser sessions."""
    result = hashlib.sha256()
    with r.open_read(r._io_root(path), path) as held, closing(sqlite3.connect(
            f"file:/proc/self/fd/{held.fileno()}?mode=ro&immutable=1", uri=True)) as db:
        counts = {}
        for table, keys, values, condition in (
            ("records", "kind,id", ["body"], "WHERE kind!='session'"),
            ("idempotency", "scope,key", ["fingerprint", "result"], ""),
        ):
            fields = [*keys.split(","), *values]
            types = " OR ".join(f"typeof({field})!='text'" for field in fields)
            if db.execute(f"SELECT 1 FROM {table} WHERE {types} LIMIT 1").fetchone():
                r._fail("RECOVERY_DATABASE_INVALID")
            if db.execute(f"SELECT 1 FROM {table} WHERE length(CAST({keys.split(',')[0]} AS BLOB))>4096 OR length(CAST({keys.split(',')[1]} AS BLOB))>4096 LIMIT 1").fetchone():
                r._fail("RECOVERY_DATABASE_INVALID")
            rows = db.execute(f"SELECT rowid,{keys} FROM {table} {condition} ORDER BY {keys}")
            counts[table] = 0
            for row_id, *identity in rows:
                result.update(canonical([table, *identity]).encode())
                for field in values:
                    size = db.execute(f"SELECT length(CAST({field} AS BLOB)) FROM {table} WHERE rowid=?", (row_id,)).fetchone()[0]
                    result.update(canonical([field, size]).encode())
                    for offset in range(1, size + 1, 65536):
                        chunk = db.execute(f"SELECT substr(CAST({field} AS BLOB),?,65536) FROM {table} WHERE rowid=?", (offset, row_id)).fetchone()[0]
                        result.update(chunk)
                counts[table] += 1
        sessions = db.execute("SELECT count(*) FROM records WHERE kind='session'").fetchone()[0]
    return {"digest": "sha256:" + result.hexdigest(), "counts": counts, "sessions": sessions}


def _report(backup, destination, manifest):
    before = _metadata_identity(backup / "files/studio.sqlite")
    after = _metadata_identity(destination / "studio.sqlite")
    if before["digest"] != after["digest"] or before["counts"] != after["counts"] or after["sessions"]:
        r._fail("MIGRATION_SEMANTIC_MISMATCH")
    files = []
    for entry in manifest["files"]:
        if entry["path"] != "studio.sqlite":
            if r._hash(destination / entry["path"]) != {k: entry[k] for k in ("size", "digest")}:
                r._fail("MIGRATION_SEMANTIC_MISMATCH")
            files.append(entry)
    report = {
        "format": "studio.metadata-migration-report", "version": 1,
        "sourceSchema": 0, "targetSchema": 1,
        "textualDiff": "--- schema0\n+++ schema1\n-PRAGMA user_version=0;\n+PRAGMA user_version=1;\n-Copied browser sessions\n+Browser sessions invalidated\n",
        "sessionsInvalidated": before["sessions"],
        "semanticDiff": {"before": before["digest"], "after": after["digest"], "unchanged": True,
                         "scope": "Exact stored non-session JSON text and idempotency receipts; no XDL version reinterpretation or new execution admission.",
                         "counts": after["counts"]},
        "unchangedFiles": files,
        "backupFilesDigest": manifest["filesDigest"],
        "activation": "Review this private report, then explicitly start Studio with the new candidate root. The original root is unchanged.",
    }
    with r.open_write(r._io_root(destination), destination / REPORT) as output:
        output.write(canonical(report).encode())
    return {"report": REPORT, "reportDigest": digest(report), "sourceSchema": 0, "targetSchema": 1}


def migrate_full(source, backup, destination):
    source, backup, destination = (r._root(p) for p in (source, backup, destination))
    roots = (source, backup, destination)
    if any(a == b or a.is_relative_to(b) or b.is_relative_to(a)
           for i, a in enumerate(roots) for b in roots[i + 1:]):
        r._fail("RECOVERY_NESTED_TARGET")
    if backup.exists() or destination.exists():
        r._fail("RECOVERY_TARGET_EXISTS")
    try:
        r._backup_full(source, backup, schema=0)
        result = r._restore_full(backup, destination, schema=0, report=_report)
    except (sqlite3.Error, UnicodeError):
        raise r.RecoveryError("RECOVERY_DATABASE_INVALID") from None
    return {**result, "status": "migrated"}
