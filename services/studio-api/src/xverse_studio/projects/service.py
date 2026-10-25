from __future__ import annotations
import json
import os
import shutil
import stat
import time
import unicodedata
from xverse_studio.storage.core import (
    Problem,
    atomic,
    canonical,
    digest,
    uid,
    contained,
)
from xverse_studio.security.files import safe_name, check_text, read_archive
from xverse_studio.security.managed_io import open_read, SafeIOError


class Projects:
    def __init__(self, store, adapter):
        self.store, self.adapter = store, adapter

    def _dir(self, pid, rev):
        return contained(
            self.store.root, self.store.root / "projects" / pid / "revisions" / str(rev)
        )

    def document_path(self, pid, docid):
        p = self.store.get("project", pid)
        if docid not in p["documents"]:
            raise Problem("NOT_FOUND", "Document not found.", 404)
        return contained(
            self.store.root,
            self._dir(pid, p["revision"]) / p["documents"][docid]["path"],
        )

    def _read_file(self, path, *, max_bytes=1024 * 1024):
        """Bound opened source bytes even when a committed file changed externally."""
        try:
            limit = min(1024 * 1024, max_bytes)
            with open_read(self.store.root, path) as source:
                info = os.fstat(source.fileno())
                if not stat.S_ISREG(info.st_mode):
                    raise OSError("Source is not a regular file")
                if info.st_size > limit:
                    raise Problem(
                        "REVISION_CONFLICT",
                        "External source bytes exceed the document or complete-project read bound. Preserve them before recovery.",
                        412,
                    )
                data = source.read(limit + 1)
        except SafeIOError as exc:
            if exc.code == "SECURE_IO_UNAVAILABLE":
                raise Problem(
                    "PLATFORM_IO_UNAVAILABLE",
                    "Secure native file acquisition is not admitted on this host. Its native platform acceptance remains open; see the support matrix.",
                    503,
                ) from None
            if exc.code == "SOURCE_CHANGED":
                raise Problem(
                    "REVISION_CONFLICT",
                    "The opened source changed during inspection. Preserve its bytes before recovery.",
                    412,
                ) from None
            raise Problem(
                "PROJECT_UNAVAILABLE",
                "A committed source or sidecar is unavailable or unsafe. Preserve the selected data root before recovery.",
                409,
            ) from None
        except (OSError, ValueError):
            raise Problem(
                "PROJECT_UNAVAILABLE",
                "A committed source or sidecar is unavailable or unsafe. Preserve the selected data root before recovery.",
                409,
            ) from None
        if len(data) > limit:
            raise Problem(
                "REVISION_CONFLICT",
                "External source bytes exceed the document or complete-project read bound. Preserve them before recovery.",
                412,
            )
        return data

    def read(self, pid, db=None):
        p = self.store.get("project", pid, db)
        result = {
            **p,
            "documents": {},
            "sourceIntegrity": "intact",
            "sourceDiagnostics": [],
        }
        source_bytes = sum(
            len(value.encode("utf-8"))
            for value in p.get("supportingFiles", {}).values()
        )
        for id, d in p["documents"].items():
            file = (
                self.store.root
                / "projects"
                / pid
                / "revisions"
                / str(p["revision"])
                / d["path"]
            )
            try:
                data = self._read_file(
                    file, max_bytes=max(0, 16 * 1024 * 1024 - source_bytes)
                )
                source_bytes += len(data)
                content = data.decode("utf-8")
            except UnicodeError:
                raise Problem(
                    "PROJECT_UNAVAILABLE",
                    "Committed source bytes are not UTF-8. Preserve them before recovery.",
                    409,
                ) from None
            actual_digest = digest(content.encode("utf-8"))
            if actual_digest != d["digest"]:
                result["sourceIntegrity"] = "modified"
                result["sourceDiagnostics"].append(
                    {
                        "code": "REVISION_CONFLICT",
                        "severity": "error",
                        "documentId": id,
                        "expectedDigest": d["digest"],
                        "actualDigest": actual_digest,
                        "message": "Source bytes changed outside the committed revision. They remain available for inspection; preserve them and recover before saving or execution.",
                    }
                )
            result["documents"][id] = {
                **d,
                "content": content,
            }
        return result

    def sources(self, p):
        return {d["path"]: d["content"] for d in p["documents"].values()}

    def assert_intact(self, p):
        if any(
            digest(d["content"].encode()) != d["digest"]
            for d in p["documents"].values()
        ):
            raise Problem(
                "REVISION_CONFLICT",
                "Committed source bytes changed externally; preserve and compare before execution.",
                412,
                currentRevision=p["revision"],
            )
        for name, expected in p.get("supportingFiles", {}).items():
            if not (
                name.startswith("profiles/")
                or name == p.get("manifest", {}).get("artifactLock")
            ):
                continue
            file = (
                self.store.root
                / "projects"
                / p["projectId"]
                / "revisions"
                / str(p["revision"])
                / name
            )
            if self._read_file(file) != expected.encode():
                raise Problem(
                    "REVISION_CONFLICT",
                    "A pinned profile or artifact sidecar changed externally; preserve it before recovery.",
                    412,
                    currentRevision=p["revision"],
                )

    def _commit(self, p, documents, db):
        names = [
            "project.studio.json",
            *[d["path"] for d in documents.values()],
            *p.get("supportingFiles", {}),
        ]
        normalized = []
        for name in names:
            safe_name(name)
            normalized.append(unicodedata.normalize("NFC", name).casefold())
        if len(set(normalized)) != len(normalized) or any(
            a.startswith(b + "/") for a in normalized for b in normalized if a != b
        ):
            raise Problem(
                "PROJECT_PATH_COLLISION",
                "The transaction contains colliding portable file or directory identities.",
            )
        if (
            sum(len(d["content"].encode()) for d in documents.values())
            + sum(len(v.encode()) for v in p.get("supportingFiles", {}).values())
            > 16 * 1024 * 1024
        ):
            raise Problem(
                "LIMIT_EXCEEDED",
                "The complete project source and sidecar limit is 16 MiB.",
                413,
            )
        target = self._dir(p["projectId"], p["revision"])
        if target.exists():
            raise Problem(
                "REVISION_CONFLICT",
                "A staged revision already exists; reload and recover the prior revision.",
                412,
            )
        stage = target.with_name(target.name + "." + uid("stage-"))
        try:
            for doc in documents.values():
                safe_name(doc["path"])
                check_text(doc["content"])
                file = contained(stage, stage / doc["path"])
                atomic(file, doc["content"].encode())
            for name, content in p.get("supportingFiles", {}).items():
                safe_name(name)
                check_text(content)
                atomic(contained(stage, stage / name), content.encode())
            metadata = {
                k: v
                for k, v in p.items()
                if k not in {"documents", "sourceIntegrity", "sourceDiagnostics"}
            }
            metadata["documents"] = {
                id: {k: v for k, v in d.items() if k != "content"}
                | {"digest": digest(d["content"].encode())}
                for id, d in documents.items()
            }
            atomic(
                stage / "project.studio.json", canonical(metadata["manifest"]).encode()
            )
            target.parent.mkdir(parents=True, exist_ok=True)
            stage.rename(target)
            self.store.on_rollback(
                db, lambda: shutil.rmtree(target) if target.exists() else None
            )
            self.store.put("project", p["projectId"], metadata, db)
        except BaseException:
            if stage.exists():
                shutil.rmtree(stage)
            elif target.exists():
                shutil.rmtree(target)
            raise
        return self.read(p["projectId"], db)

    def create(
        self,
        name,
        blueprint=None,
        documents=None,
        provenance=None,
        *,
        supporting=None,
        manifest_template=None,
        layout=None,
    ):
        if documents is None:
            from xverse_studio.xdl import examples

            entries = examples()
            if isinstance(entries, list):
                entries = {e.get("id", e.get("entryId")): e for e in entries}
            key = blueprint or next(iter(entries))
            if key not in entries:
                raise Problem(
                    "BLUEPRINT_UNAVAILABLE", "Select an admitted catalog blueprint."
                )
            entry = entries[key]
            documents = entry.get("documents", entry.get("sources"))
            if not documents:
                raise Problem(
                    "BLUEPRINT_UNAVAILABLE",
                    "Blueprint has no admitted authored inputs.",
                )
            provenance = {
                "blueprintRef": key,
                "evidenceScope": "owned_reference",
                "maturity": "fixture",
            }
        normalized = {}
        for i, (path, content) in enumerate(documents.items()):
            safe_name(path)
            if isinstance(content, dict):
                content = content["content"]
            normalized[f"doc-{i}"] = {
                "path": path
                if path.startswith(("xdl/", "profiles/"))
                else "xdl/" + path,
                "format": "json" if path.endswith(".json") else "yaml",
                "content": content,
            }
        if not normalized or len(normalized) > 128:
            raise Problem(
                "LIMIT_EXCEEDED", "A project requires 1–128 explicit documents."
            )
        pid = uid("prj-")
        p = {
            "projectId": pid,
            "name": name,
            "revision": 1,
            "presentationRevision": 1,
            "layout": layout or {"positions": {}},
            "supportingFiles": supporting or {},
            "createdAt": time.time(),
            "manifest": {
                "formatVersion": "1.0",
                "projectId": pid,
                "name": name,
                "resources": [
                    {"path": d["path"], "format": d["format"]}
                    for d in normalized.values()
                    if d["path"].startswith("xdl/")
                ],
                "profiles": [],
                "layoutFiles": [],
                "artifactLock": "artifacts.lock.json",
                "provenance": provenance or {},
            },
        }
        if manifest_template:
            p["manifest"] = {
                **manifest_template,
                "projectId": pid,
                "name": name,
                "provenance": provenance or {},
            }
        with self.store.tx() as db:
            return self._commit(p, normalized, db)

    def mutate(self, pid, revision, transform):
        with self.store.tx() as db:
            p = self.read(pid, db)
            if revision is None:
                raise Problem(
                    "REVISION_REQUIRED",
                    "Supply If-Match with the current revision.",
                    428,
                )
            if revision != p["revision"]:
                raise Problem(
                    "REVISION_CONFLICT",
                    "Project changed; reload before saving.",
                    412,
                    currentRevision=p["revision"],
                )
            for d in p["documents"].values():
                if digest(d["content"].encode()) != d["digest"]:
                    raise Problem(
                        "REVISION_CONFLICT",
                        "A committed source was edited externally. Preserve and compare it before recovery.",
                        412,
                        currentRevision=p["revision"],
                    )
            docs = transform(p)
            p["revision"] += 1
            p["manifest"]["resources"] = [
                {"path": d["path"], "format": d["format"]}
                for d in docs.values()
                if d["path"].startswith("xdl/")
            ]
            return self._commit(p, docs, db)

    def save(self, pid, docid, revision, content, format):
        def change(p):
            if docid not in p["documents"]:
                raise Problem("NOT_FOUND", "Document not found.", 404)
            docs = p["documents"]
            docs[docid] = {
                **docs[docid],
                "content": check_text(content),
                "format": format,
            }
            return docs

        return self.mutate(pid, revision, change)

    def layout(self, pid, revision, layout):
        with self.store.tx() as db:
            p = self.store.get("project", pid, db)
            if revision is None:
                raise Problem(
                    "REVISION_REQUIRED", "Supply the presentation revision.", 428
                )
            if revision != p["presentationRevision"]:
                raise Problem(
                    "REVISION_CONFLICT",
                    "Layout changed; reload before saving.",
                    412,
                    currentRevision=p["presentationRevision"],
                )
            p["layout"] = layout
            p["presentationRevision"] += 1
            sidecar = contained(
                self.store.root,
                self.store.root
                / "projects"
                / pid
                / "layout"
                / f"{p['presentationRevision']}.json",
            )
            if sidecar.exists():
                raise Problem(
                    "REVISION_CONFLICT",
                    "A staged layout revision needs explicit recovery.",
                    412,
                )
            atomic(sidecar, canonical(layout).encode())
            self.store.on_rollback(db, lambda: sidecar.unlink(missing_ok=True))
            p["presentationRef"] = f"layout/{p['presentationRevision']}.json"
            p["manifest"]["layoutFiles"] = ["layout/model.json"]
            self.store.put("project", pid, p, db)
        return self.read(pid)

    def import_archive(self, encoded):
        files = read_archive(encoded)
        try:
            manifest = json.loads(files.get("project.studio.json", "{}"))
            if manifest.get("formatVersion") != "1.0":
                raise Problem(
                    "FORMAT_UNSUPPORTED",
                    "Only project envelope 1.0 can be imported. Original bytes remain unchanged.",
                )
            resources = manifest.get("resources", [])
            paths = [safe_name(r["path"]) for r in resources]
            if (
                not paths
                or len(set(paths)) != len(paths)
                or any(p not in files or not p.startswith("xdl/") for p in paths)
            ):
                raise Problem(
                    "MANIFEST_INVALID",
                    "The manifest must explicitly name existing XDL resources.",
                )
            layout = {}
            for name in manifest.get("layoutFiles", []):
                safe_name(name)
                if name not in files or not name.startswith("layout/"):
                    raise Problem(
                        "MANIFEST_INVALID", "A declared layout sidecar is unavailable."
                    )
                layout = json.loads(files[name])
            for profile in manifest.get("profiles", []):
                for key in ("schemaPath", "presentationPath"):
                    if profile.get(key):
                        name = safe_name(profile[key])
                        if name not in files or not name.startswith("profiles/"):
                            raise Problem(
                                "MANIFEST_INVALID",
                                "A declared profile sidecar is unavailable.",
                            )
            supporting = {
                name: content
                for name, content in files.items()
                if name not in paths and name != "project.studio.json"
            }
            return self.create(
                manifest.get("name", "Imported System"),
                documents={p: files[p] for p in paths},
                provenance={
                    "imported": True,
                    "originalProjectId": manifest.get("projectId"),
                    "limitations": ["Host-local bindings require revalidation."],
                },
                supporting=supporting,
                manifest_template=manifest,
                layout=layout,
            )
        except (KeyError, TypeError, ValueError):
            raise Problem(
                "MANIFEST_INVALID", "The project manifest is malformed."
            ) from None
