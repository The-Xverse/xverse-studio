"""Bounded credential-free exchange. Imports are inert; run journals remain immutable."""

import io
import zipfile
import zlib
from fastapi import Request
from fastapi.responses import Response
from xverse_studio.api.models import Export
from xverse_studio.storage.core import Problem, canonical, digest, uid, atomic
from xverse_studio.security.files import MAX_EXPANDED, check_portable_text, safe_name
from xverse_studio.security.managed_io import read_bounded, SafeIOError
from xverse_studio.evidence.reader import verify_journal


def capture(root, path, *, missing_ok=False):
    try:
        return read_bounded(root, path, MAX_EXPANDED)
    except SafeIOError as error:
        if error.code == "FILE_MISSING":
            if missing_ok:
                return None
            raise Problem("EVIDENCE_UNAVAILABLE", "The selected bundle is unavailable.", 404) from None
        if error.code == "LIMIT_EXCEEDED":
            raise Problem("LIMIT_EXCEEDED", "The exchange byte limit is 16 MiB.", 413) from None
        if error.code == "SECURE_IO_UNAVAILABLE":
            raise Problem("SECURE_IO_UNAVAILABLE", "Secure native exchange acquisition is unavailable on this host.", 503) from None
        if error.code == "SOURCE_CHANGED":
            raise Problem("EVIDENCE_CHANGED", "The selected bytes changed during acquisition; retry with a fresh observation.", 409) from None
        raise Problem("EVIDENCE_INVALID", "The selected exchange source cannot be acquired safely.") from None


def install_exchange(app, store, projects, runs):
    def make_bundle(files):
        target = io.BytesIO()
        with zipfile.ZipFile(target, "w", compression=zipfile.ZIP_DEFLATED) as z:
            if len(files) > 256:
                raise Problem("LIMIT_EXCEEDED", "Exchange file limit exceeded.", 413)
            total = 0
            for path, content in files.items():
                safe_name(path)
                if isinstance(content, str):
                    check_portable_text(content)
                    content = content.encode()
                total += len(content)
                if total > MAX_EXPANDED:
                    raise Problem(
                        "LIMIT_EXCEEDED", "Exchange expanded byte limit exceeded.", 413
                    )
                compressor = zlib.compressobj(zlib.Z_DEFAULT_COMPRESSION, zlib.DEFLATED, -15)
                compressed = compressor.compress(content) + compressor.flush()
                # Preserve the same source bytes without producing an entry
                # that the unchanged import compression-ratio guard rejects.
                compression = zipfile.ZIP_STORED if len(content) / max(1, len(compressed)) > 100 else zipfile.ZIP_DEFLATED
                z.writestr(path, content, compress_type=compression)
        data = target.getvalue()
        if len(data) > MAX_EXPANDED:
            raise Problem("LIMIT_EXCEEDED", "The exchange byte limit is 16 MiB.", 413)
        return data

    @app.post("/api/v1/projects/{projectId}/exports", status_code=202)
    def export_project(projectId: str, body: Export, request: Request):
        def accepted(db):
            p = projects.read(projectId, db)
            if body.revision != p["revision"]:
                raise Problem(
                    "REVISION_CONFLICT",
                    "Export requires the exact current project revision.",
                    412,
                    currentRevision=p["revision"],
                )
            projects.assert_manifest_intact(p)
            oid = uid("op-")
            manifest = p["manifest"] | {"layoutFiles": ["layout/model.json"]}
            files = {
                **p.get("supportingFiles", {}),
                "project.studio.json": canonical(manifest),
                "artifacts.lock.json": p.get("supportingFiles", {}).get(
                    "artifacts.lock.json",
                    canonical(
                        {
                            "formatVersion": "1.0",
                            "entries": [],
                            "limitations": [
                                "Only declared reference artifacts are available; imports never download artifacts."
                            ],
                        }
                    ),
                ),
                "layout/model.json": canonical(p["layout"]),
            }
            for doc in p["documents"].values():
                if digest(doc["content"].encode()) != doc["digest"]:
                    raise Problem(
                        "REVISION_CONFLICT",
                        "External changes must be resolved before exporting.",
                        412,
                    )
                files[doc["path"]] = doc["content"]
            bundle = make_bundle(files)
            atomic(store.root / "exports" / f"{oid}.zip", bundle)
            op = {
                "operationId": oid,
                "status": "completed",
                "result": {
                    "downloadUrl": f"/api/v1/exports/{oid}",
                    "digest": digest(bundle),
                    "size": len(bundle),
                    "evidenceScope": "project_only",
                },
            }
            store.put("operation", oid, op, db)
            return op

        result, _ = store.idempotent(
            request.state.principal,
            f"POST /projects/{projectId}/exports",
            request.headers.get("idempotency-key"),
            body.model_dump(),
            accepted,
        )
        return result

    @app.get("/api/v1/exports/{operationId}")
    def download(operationId: str):
        op = store.get("operation", operationId)
        if not op.get("result", {}).get("downloadUrl"):
            raise Problem(
                "NOT_FOUND", "This operation has no downloadable bundle.", 404
            )
        path = store.root / "exports" / f"{operationId}.zip"
        data = capture(store.root, path)
        if digest(data) != op["result"]["digest"]:
            raise Problem("EVIDENCE_INVALID", "Export integrity verification failed.")
        return Response(
            data,
            media_type="application/zip",
            headers={"Content-Disposition": 'attachment; filename="studio-bundle.zip"'},
        )

    @app.post("/api/v1/runs/{runId}/exports", status_code=202)
    def export_run(runId: str, request: Request):
        r = runs.read(runId)

        def accepted(db):
            snap = store.get("snapshot", r["snapshotId"], db)
            raw = capture(store.root, runs.directory(runId) / "evidence.jsonl", missing_ok=True)
            _, integrity = verify_journal(raw, r) if raw is not None else ([], "unavailable")
            files = {
                "snapshot.json": canonical(snap),
                "run.json": canonical(
                    {
                        k: v
                        for k, v in r.items()
                        if k not in ("pid", "createTime", "ownerDigest")
                    }
                ),
                "report.json": canonical(
                    {
                        "schemaVersion": "1.0",
                        "runId": runId,
                        "snapshotId": snap["snapshotId"],
                        "planDigest": snap["planDigest"],
                        "evidenceStatus": r["evidence"],
                        "integrity": integrity,
                        "evidenceScope": r.get("evidenceScope", "unknown"),
                        "limitations": [
                            "This bundle contains the original Studio provider journal; it does not admit another runtime, Argus reader or physical device.",
                            "Replay is recorded evidence inspection, not re-execution.",
                        ],
                    }
                ),
            }
            files["evaluations.json"] = canonical(
                [
                    row
                    for row in store.all("evaluation", db)
                    if row.get("runId") == runId
                ]
            )
            files["annotations.json"] = canonical(
                [
                    row
                    for row in store.all("annotation", db)
                    if row.get("runId") == runId
                ]
            )
            if raw is not None:
                try:
                    for line in raw.decode("utf-8").splitlines():
                        check_portable_text(line)
                except UnicodeError:
                    raise Problem(
                        "EVIDENCE_INVALID",
                        "Canonical evidence is not supported UTF-8 text.",
                    ) from None
                files["evidence/reference.jsonl"] = raw
            files["manifest.json"] = canonical(
                {
                    "formatVersion": "1.0",
                    "kind": "studio.evidence",
                    "files": {
                        path: digest(raw.encode() if isinstance(raw, str) else raw)
                        for path, raw in files.items()
                    },
                    "integrity": integrity,
                    "availability": r["evidence"],
                    "providerId": r["providerId"],
                }
            )
            bundle = make_bundle(files)
            oid = uid("op-")
            atomic(store.root / "exports" / f"{oid}.zip", bundle)
            op = {
                "operationId": oid,
                "status": "completed",
                "result": {
                    "downloadUrl": f"/api/v1/exports/{oid}",
                    "digest": digest(bundle),
                    "size": len(bundle),
                    "integrity": integrity,
                },
            }
            store.put("operation", oid, op, db)
            return op

        result, _ = store.idempotent(
            request.state.principal,
            f"POST /runs/{runId}/exports",
            request.headers.get("idempotency-key"),
            {},
            accepted,
        )
        return result
