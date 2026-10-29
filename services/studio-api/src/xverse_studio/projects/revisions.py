"""Immutable revision history, verified source copies and explicit conflict recovery.

Every committed revision records its document/sidecar digests and keeps a
content-addressed copy of each byte sequence outside the editable revision
directory. Restoring a revision (undo/redo) is a new forward revision built from
verified bytes; it never rewrites history. Recovery from externally changed or
unreadable sources first preserves the observed bytes in an immutable backup,
then commits an explicit choice as a new revision.
"""

from __future__ import annotations

import copy
import json
import time

from xverse_studio.security.files import check_text
from xverse_studio.security.managed_io import SafeIOError, open_read
from xverse_studio.storage.core import (
    Problem,
    atomic,
    canonical,
    contained,
    digest,
    uid,
)

RECOVERY_ACTIONS = ("adopt_external", "restore_revision")
MAX_PAGE = 200
MAX_SOURCE_BYTES = 16 * 1024 * 1024


class RevisionHistory:
    def __init__(self, projects):
        self.projects = projects
        self.store = projects.store

    def _root(self, pid, *parts):
        path = self.store.root / "projects" / pid
        for part in parts:
            path = path / part
        return contained(self.store.root, path)

    def _object(self, pid, value_digest):
        return self._root(pid, "objects", value_digest.split(":", 1)[1])

    def _read(self, path):
        """Bounded raw bytes, or a reason they cannot be observed safely."""
        try:
            with open_read(self.store.root, path) as source:
                data = source.read(MAX_SOURCE_BYTES + 1)
        except SafeIOError as exc:
            return None, "missing" if exc.code == "FILE_MISSING" else "unsafe"
        except (OSError, ValueError):
            return None, "unsafe"
        if len(data) > MAX_SOURCE_BYTES:
            return None, "oversize"
        return data, "present"

    def _verified(self, path, value_digest):
        data, status = self._read(path)
        return data if status == "present" and digest(data) == value_digest else None

    def seal(self, p, documents, db, origin):
        """Record a committed revision and keep verified copies of its bytes."""
        pid = p["projectId"]
        contents = [d["content"] for d in documents.values()] + list(
            p.get("supportingFiles", {}).values()
        )
        for content in contents:
            raw = content.encode()
            value_digest = digest(raw)
            # Content-addressed: an existing copy is reused only after verification.
            if self._verified(self._object(pid, value_digest), value_digest) is None:
                atomic(self._object(pid, value_digest), raw)
        record = {
            "projectId": pid,
            "revision": p["revision"],
            "origin": origin or {"kind": "edit"},
            "createdAt": time.time(),
            "documents": {
                id: {
                    "path": d["path"],
                    "format": d["format"],
                    "digest": digest(d["content"].encode()),
                }
                for id, d in documents.items()
            },
            "supportingFiles": {
                name: digest(content.encode())
                for name, content in p.get("supportingFiles", {}).items()
            },
            "manifest": copy.deepcopy(p.get("manifest", {})),
        }
        self.store.put("revision", f"{pid}:{p['revision']}", record, db)

    def list(self, pid, before=None, limit=50):
        self.store.get("project", pid)
        limit = max(1, min(int(limit), MAX_PAGE))
        with self.store.tx() as db:
            rows = db.execute(
                "SELECT body FROM records WHERE kind='revision' "
                "AND json_extract(body, '$.projectId')=? "
                "AND json_extract(body, '$.revision') < ? "
                "ORDER BY json_extract(body, '$.revision') DESC LIMIT ?",
                (pid, before if before is not None else 2**62, limit + 1),
            ).fetchall()
            earliest = db.execute(
                "SELECT MIN(json_extract(body, '$.revision')) FROM records "
                "WHERE kind='revision' AND json_extract(body, '$.projectId')=?",
                (pid,),
            ).fetchone()[0]
        records = [json.loads(row[0]) for row in rows]
        page = records[:limit]
        return {
            "items": [
                {k: r[k] for k in ("revision", "origin", "createdAt", "documents")}
                for r in page
            ],
            "nextBefore": page[-1]["revision"] if len(records) > limit else None,
            # Revisions committed before history recording carry no verified copy.
            "unrecordedBefore": earliest if earliest and earliest > 1 else None,
        }

    def contents(self, pid, revision):
        """Verified documents, sidecars and manifest of a recorded revision."""
        self.store.get("project", pid)
        try:
            record = self.store.get("revision", f"{pid}:{revision}")
        except Problem:
            raise Problem(
                "REVISION_UNRECOVERABLE",
                "This revision has no recorded history to restore from.",
                409,
                revision=revision,
            ) from None
        directory = self._root(pid, "revisions", str(revision))
        missing = []

        def load(value_digest, name):
            # Prefer the sealed copy; the revision directory serves only when it still matches.
            data = self._verified(self._object(pid, value_digest), value_digest)
            if data is None:
                data = self._verified(
                    contained(directory, directory / name), value_digest
                )
            if data is None:
                missing.append(value_digest)
                return ""
            return data.decode()

        documents = {
            id: {
                "path": d["path"],
                "format": d["format"],
                "content": load(d["digest"], d["path"]),
            }
            for id, d in record["documents"].items()
        }
        supporting = {
            name: load(value, name) for name, value in record["supportingFiles"].items()
        }
        if missing:
            raise Problem(
                "REVISION_UNRECOVERABLE",
                "Recorded bytes for this revision are missing or no longer match their digests; nothing was changed.",
                409,
                revision=revision,
                missingDigests=missing[:16],
            )
        return documents, supporting, record["manifest"]

    def restore(self, pid, expected, revision):
        """Undo/redo transaction: a new revision equal to a verified earlier one."""
        documents, supporting, manifest = self.contents(pid, revision)

        def change(p):
            p["supportingFiles"] = supporting
            p["manifest"] = copy.deepcopy(manifest)
            return documents

        return self.projects.mutate(
            pid,
            expected,
            change,
            origin={"kind": "restore", "fromRevision": revision},
        )

    def observe(self, p):
        """Compare every committed document and sidecar with the bytes now on disk."""
        directory = self._root(p["projectId"], "revisions", str(p["revision"]))
        observed = {}
        entries = [
            ("document", id, d["path"], d["digest"]) for id, d in p["documents"].items()
        ] + [
            ("sidecar", name, name, digest(content.encode()))
            for name, content in p.get("supportingFiles", {}).items()
        ]
        for kind, key, path, committed in entries:
            data, status = self._read(contained(directory, directory / path))
            actual = digest(data) if data is not None else None
            if status == "present" and actual == committed:
                continue
            observed[f"{kind}:{key}"] = {
                "kind": kind,
                "id": key,
                "path": path,
                "committedDigest": committed,
                "observedDigest": actual,
                "status": status,
                "bytes": data,
            }
        return observed

    def recover(self, pid, expected, action, revision=None):
        """Preserve externally changed bytes, then commit one explicit resolution."""
        if action not in RECOVERY_ACTIONS:
            raise Problem(
                "RECOVERY_ACTION_UNSUPPORTED", "Choose a supported recovery action."
            )
        if action == "restore_revision":
            restored = self.contents(pid, revision)
        with self.store.tx() as db:
            p = self.store.get("project", pid, db)
            if expected != p["revision"]:
                raise Problem(
                    "REVISION_CONFLICT",
                    "Project changed; reload before recovery.",
                    412,
                    currentRevision=p["revision"],
                )
            observed = self.observe(p)
            if not observed:
                raise Problem(
                    "RECOVERY_NOT_REQUIRED",
                    "Committed sources and sidecars match their recorded digests; no recovery is needed.",
                    409,
                )
            documents = None
            if action == "adopt_external":
                documents = {}
                for id, d in p["documents"].items():
                    entry = observed.get(f"document:{id}")
                    if entry is None:
                        content = self.projects._read_file(
                            self._root(pid, "revisions", str(p["revision"]), d["path"])
                        ).decode()
                    elif entry["status"] != "present":
                        raise Problem(
                            "RECOVERY_ADOPT_UNAVAILABLE",
                            "An external source is missing, unsafe or oversized; restore a recorded revision instead.",
                            409,
                            documentId=id,
                            observedStatus=entry["status"],
                        )
                    else:
                        try:
                            content = entry["bytes"].decode("utf-8")
                        except UnicodeError:
                            raise Problem(
                                "RECOVERY_ADOPT_UNAVAILABLE",
                                "An external source is not UTF-8 text; restore a recorded revision instead.",
                                409,
                                documentId=id,
                                observedStatus="not_text",
                            ) from None
                    documents[id] = {
                        "path": d["path"],
                        "format": d["format"],
                        "content": check_text(content),
                    }
            rid = uid("rec-")
            backup = self._root(pid, "recoveries", rid)
            preserved = {}
            for key, entry in observed.items():
                record = {k: v for k, v in entry.items() if k != "bytes"}
                if entry["bytes"] is not None:
                    # Name by digest: portable and independent of the source path length.
                    name = entry["observedDigest"].split(":", 1)[1]
                    atomic(backup / "files" / name, entry["bytes"])
                    record["backupFile"] = "files/" + name
                preserved[key] = record
            recovery = {
                "recoveryId": rid,
                "projectId": pid,
                "revision": p["revision"],
                "action": action,
                "restoredRevision": revision if action == "restore_revision" else None,
                "createdAt": time.time(),
                "preserved": preserved,
                # Sidecars are never adopted from disk; recorded content is kept.
                "sidecarPolicy": "recorded_content",
            }
            atomic(backup / "manifest.json", canonical(recovery).encode())
            self.store.put("recovery", rid, recovery, db)
            if action == "restore_revision":
                documents, supporting, manifest = restored
                p["supportingFiles"] = supporting
                p["manifest"] = copy.deepcopy(manifest)
            committed = self.projects.advance(
                p,
                documents,
                db,
                {"kind": "recovery", "action": action, "recoveryId": rid}
                | ({"fromRevision": revision} if revision is not None else {}),
            )
        return {"project": committed, "recovery": recovery}

    def recoveries(self, pid, limit=50):
        self.store.get("project", pid)
        limit = max(1, min(int(limit), MAX_PAGE))
        with self.store.tx() as db:
            rows = db.execute(
                "SELECT body FROM records WHERE kind='recovery' "
                "AND json_extract(body, '$.projectId')=? "
                "ORDER BY json_extract(body, '$.createdAt') DESC LIMIT ?",
                (pid, limit),
            ).fetchall()
        return {"items": [json.loads(row[0]) for row in rows]}

    def recovered(self, pid, rid, key):
        """Preserved bytes of one observed source, verified against their digest."""
        recovery = self.store.get("recovery", rid)
        entry = recovery.get("preserved", {}).get(key)
        if recovery["projectId"] != pid or entry is None:
            raise Problem("NOT_FOUND", "Recovered source not found.", 404)
        if "backupFile" not in entry:
            return {**entry, "content": None}
        backup = self._root(pid, "recoveries", rid)
        data = self._verified(
            contained(backup, backup / entry["backupFile"]), entry["observedDigest"]
        )
        if data is None:
            raise Problem(
                "RECOVERY_UNAVAILABLE",
                "The preserved bytes are unavailable or no longer match their recorded digest.",
                409,
            )
        try:
            text = data.decode("utf-8")
        except UnicodeError:
            return {**entry, "content": None, "encoding": "binary"}
        return {**entry, "content": text, "encoding": "utf-8"}
