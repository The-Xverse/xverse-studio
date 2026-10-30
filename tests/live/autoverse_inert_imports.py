"""Actual enrolled Autoverse imports cannot install or dispatch metadata commands."""

import base64
from copy import deepcopy
import io
import json
import os
import stat
import subprocess
import zipfile

import pytest
from ruamel.yaml import YAML

import autoverse_provider_admission as enrollment
from autoverse_provider_admission import application, authenticated, project
from xverse_studio.storage.core import digest

target = enrollment.target
PAYLOADS = [
    '{"hooks":{"start":"touch owned-import-sentinel"}}',
    'hooks:\n  start: touch owned-import-sentinel\n',
    '{"\\u0068ooks":{"start":"touch owned-import-sentinel"}}',
    '{"description":"<script>ownedImportSentinel()</script>"}',
    '{"description":"java\\u0073cript:ownedImportSentinel()"}',
    '{"exec":"touch owned-import-sentinel"}',
]


def archive(p, supporting, manifest=None):
    stream = io.BytesIO()
    with zipfile.ZipFile(stream, "w", compression=zipfile.ZIP_DEFLATED) as z:
        z.writestr("project.studio.json", json.dumps(manifest or p["manifest"]))
        for document in p["documents"].values():
            z.writestr(document["path"], document["content"])
        for name, content in supporting.items():
            z.writestr(name, content)
    return base64.b64encode(stream.getvalue()).decode()


def forbidden(*args, **kwargs):
    raise AssertionError("Imported metadata attempted to execute a command or dispatch a provider")


@pytest.mark.parametrize("payload", PAYLOADS)
def test_autoverse_profile_commands_are_rejected_before_allocation(target, tmp_path, monkeypatch, payload):
    provider, blueprint = target
    app = application(tmp_path / "Autoverse inert profile Ω", provider)
    with authenticated(app) as api:
        p = project(api, blueprint)
        monkeypatch.setattr(subprocess, "Popen", forbidden)
        monkeypatch.setattr(os, "system", forbidden)
        monkeypatch.setattr(app.state.studio.runs, "_dispatch", forbidden)
        response = api.post(
            "/api/v1/projects/imports",
            json={"archiveBase64": archive(p, {"profiles/presentation.json": payload})},
        )
        assert response.status_code == 422, response.text
        assert response.json()["code"] == "UNSAFE_PROFILE"
        assert len(app.state.studio.store.all("project")) == 1
        assert app.state.studio.store.all("run") == []
        assert app.state.studio.store.all("snapshot") == []
        assert not (tmp_path / "owned-import-sentinel").exists()


@pytest.mark.parametrize("unknown_profile", [False, True, "blank-prefixed"])
def test_autoverse_opaque_imports_preserve_source_and_never_confer_execution(
    target, tmp_path, monkeypatch, unknown_profile
):
    provider, blueprint = target
    app = application(tmp_path / "Autoverse opaque import Ω", provider)
    with authenticated(app) as api:
        p = project(api, blueprint)
        manifest = deepcopy(p["manifest"])
        opaque = {"entrypoint": ["touch", "owned-import-sentinel"], "future": [None, False, {"Ω": 7}]}
        manifest["futureOpaque"] = opaque
        note = "Inert command-shaped documentation: touch owned-import-sentinel\n"
        supporting = {"README.md": note}
        if unknown_profile:
            content = '{"type":"object","properties":{"opaque":{"type":"string"}}}'
            if unknown_profile == "blank-prefixed":
                content = "\n" * 50000 + content
            supporting["profiles/future.schema.json"] = content
            manifest["profiles"] = [{"namespace": "io.xverse.test.unadmitted", "version": "1.0.0",
                                     "schemaPath": "profiles/future.schema.json", "schemaDigest": digest(content.encode())}]
        monkeypatch.setattr(subprocess, "Popen", forbidden)
        monkeypatch.setattr(os, "system", forbidden)
        monkeypatch.setattr(app.state.studio.runs, "_dispatch", forbidden)
        encoded = archive(p, supporting, manifest)
        if unknown_profile == "blank-prefixed":
            # Stored ZIP entries keep the ordinary text under the same import
            # byte cap without the separate compression-ratio refusal.
            stream = io.BytesIO()
            with zipfile.ZipFile(io.BytesIO(base64.b64decode(encoded))) as source, zipfile.ZipFile(stream, "w") as output:
                for name in source.namelist():
                    output.writestr(name, source.read(name))
            encoded = base64.b64encode(stream.getvalue()).decode()
        response = api.post(
            "/api/v1/projects/imports",
            json={"archiveBase64": encoded},
        )
        assert response.status_code == 201, response.text
        imported = response.json()
        assert imported["projectId"] != p["projectId"]
        assert imported["manifest"]["futureOpaque"] == opaque
        assert imported["supportingFiles"]["README.md"] == note
        assert {d["path"]: d["content"] for d in imported["documents"].values()} == {
            d["path"]: d["content"] for d in p["documents"].values()}
        inspection = api.get(f"/api/v1/projects/{imported['projectId']}/inspection")
        assert inspection.status_code == 200
        assert app.state.studio.store.all("run") == []
        assert app.state.studio.store.all("snapshot") == []
        if unknown_profile:
            blocked = api.post(
                f"/api/v1/projects/{imported['projectId']}/preflights",
                json={"revision": imported["revision"], "providerId": provider.descriptor()["providerId"]},
            )
            assert blocked.status_code == 422, blocked.text
            assert blocked.json()["code"] == "PROFILE_UNRESOLVED"
            assert app.state.studio.store.all("run") == []
            assert app.state.studio.store.all("snapshot") == []
        exported = api.post(
            f"/api/v1/projects/{imported['projectId']}/exports",
            headers={"Idempotency-Key": "opaque-autoverse-export"},
            json={"revision": imported["revision"]},
        )
        assert exported.status_code == 202, exported.text
        data = api.get(exported.json()["result"]["downloadUrl"])
        assert data.status_code == 200
        with zipfile.ZipFile(io.BytesIO(data.content)) as z:
            assert json.loads(z.read("project.studio.json"))["futureOpaque"] == opaque
            assert z.read("README.md") == note.encode()
            if unknown_profile:
                assert z.read("profiles/future.schema.json") == content.encode()
            authored_paths = {d["path"] for d in imported["documents"].values()}
            expected_supporting = {name: z.read(name).decode() for name in z.namelist()
                                   if name != "project.studio.json" and name not in authored_paths}
        reopened = api.post(
            "/api/v1/projects/imports",
            json={"archiveBase64": base64.b64encode(data.content).decode()},
        )
        assert reopened.status_code == 201, reopened.text
        assert reopened.json()["supportingFiles"] == expected_supporting
        assert all(reopened.json()["supportingFiles"][name] == value
                   for name, value in imported["supportingFiles"].items())
        assert {d["path"]: d["content"] for d in reopened.json()["documents"].values()} == {
            d["path"]: d["content"] for d in imported["documents"].values()}
        assert reopened.json()["manifest"]["futureOpaque"] == opaque
        assert app.state.studio.store.all("run") == []
        assert not (tmp_path / "owned-import-sentinel").exists()


@pytest.mark.parametrize("fault", [
    "traversal", "absolute", "drive", "case-collision", "symlink", "fifo",
    "oversized", "file-count", "future-version", "executable", "local-binding", "compression-ratio",
])
def test_autoverse_archive_boundaries_refuse_before_allocation(target, tmp_path, monkeypatch, fault):
    provider, blueprint = target
    app = application(tmp_path / "Autoverse hostile archive Ω", provider)
    with authenticated(app) as api:
        p = project(api, blueprint)
        manifest = deepcopy(p["manifest"])
        supporting = {}
        code, status = "UNSAFE_PATH", 422
        if fault in {"traversal", "absolute", "drive"}:
            supporting[{"traversal": "../outside.md", "absolute": "/outside.md", "drive": "C:/outside.md"}[fault]] = "inert"
        elif fault == "case-collision":
            supporting = {"README.md": "first", "readme.md": "second"}
            code = "UNSAFE_ARCHIVE"
        elif fault in {"symlink", "fifo"}:
            code = "UNSAFE_ARCHIVE"
        elif fault == "oversized":
            supporting["README.md"] = "x" * (1024 * 1024 + 1)
            code, status = "LIMIT_EXCEEDED", 413
        elif fault == "file-count":
            supporting = {f"xdl/extra-{i}.yaml": "# inert" for i in range(257)}
            code, status = "LIMIT_EXCEEDED", 413
        elif fault == "future-version":
            manifest["formatVersion"] = "2.0"
            code = "FORMAT_UNSUPPORTED"
        elif fault == "executable":
            supporting["xdl/start.sh"] = "touch owned-import-sentinel"
            code = "UNSAFE_ARCHIVE"
        elif fault == "local-binding":
            supporting["local-bindings/1.json"] = "{}"
            code = "UNSAFE_ARCHIVE"
        elif fault == "compression-ratio":
            supporting["README.md"] = "x" * 16384
            code, status = "LIMIT_EXCEEDED", 413
        stream = io.BytesIO()
        compression = zipfile.ZIP_DEFLATED if fault == "compression-ratio" else zipfile.ZIP_STORED
        with zipfile.ZipFile(stream, "w", compression=compression) as z:
            z.writestr("project.studio.json", json.dumps(manifest))
            for document in p["documents"].values():
                z.writestr(document["path"], document["content"])
            for name, content in supporting.items():
                z.writestr(name, content)
            if fault in {"symlink", "fifo"}:
                info = zipfile.ZipInfo("README.md")
                info.create_system = 3
                info.external_attr = ((stat.S_IFLNK if fault == "symlink" else stat.S_IFIFO) | 0o600) << 16
                z.writestr(info, "owned-import-sentinel")
        monkeypatch.setattr(subprocess, "Popen", forbidden)
        monkeypatch.setattr(os, "system", forbidden)
        monkeypatch.setattr(app.state.studio.runs, "_dispatch", forbidden)
        response = api.post(
            "/api/v1/projects/imports",
            json={"archiveBase64": base64.b64encode(stream.getvalue()).decode()},
        )
        assert response.status_code == status, response.text
        assert response.json()["code"] == code
        store = app.state.studio.store
        assert len(store.all("project")) == 1 and store.get("project", p["projectId"])["revision"] == p["revision"]
        assert store.all("run") == [] and store.all("snapshot") == []


def test_autoverse_unknown_xdl_payload_is_preserved_inspectable_and_blocked(target, tmp_path, monkeypatch):
    provider, blueprint = target
    app = application(tmp_path / "Autoverse unknown XDL Ω", provider)
    with authenticated(app) as api:
        p = project(api, blueprint)
        authored = deepcopy(p)
        document = next(d for d in authored["documents"].values() if d["path"] == "xdl/system.xdl.yaml")
        yaml = YAML()
        resource = yaml.load(document["content"])
        namespace = "io.xverse.test.unknown"
        payload = {"entrypoint": ["touch", "owned-import-sentinel"], "opaque": [None, False, {"Ω": 7}]}
        resource.setdefault("extensions", {})[namespace] = payload
        text = io.StringIO()
        yaml.dump(resource, text)
        document["content"] = text.getvalue()
        monkeypatch.setattr(subprocess, "Popen", forbidden)
        monkeypatch.setattr(os, "system", forbidden)
        monkeypatch.setattr(app.state.studio.runs, "_dispatch", forbidden)
        imported = api.post("/api/v1/projects/imports", json={"archiveBase64": archive(authored, {})})
        assert imported.status_code == 201, imported.text
        project_value = imported.json()
        imported_source = next(d for d in project_value["documents"].values() if d["path"] == document["path"])
        assert imported_source["content"] == document["content"]
        inspection = api.get(f"/api/v1/projects/{project_value['projectId']}/inspection")
        assert inspection.status_code == 200
        matches = [item for item in inspection.json()["unresolved"] if item["namespace"] == namespace]
        assert len(matches) == 1 and matches[0]["executionAllowed"] is False
        preflight = api.post(
            f"/api/v1/projects/{project_value['projectId']}/preflights",
            json={"revision": project_value["revision"], "providerId": provider.descriptor()["providerId"]},
        )
        assert preflight.status_code == 200 and preflight.json()["status"] == "blocked", preflight.text
        blocked = api.post(
            "/api/v1/runs", headers={"Idempotency-Key": "unresolved-autoverse-start"},
            json={key: preflight.json()[key] for key in ("snapshotId", "preflightId")},
        )
        assert blocked.status_code == 422 and blocked.json()["code"] == "ADMISSION_REJECTED", blocked.text
        assert app.state.studio.store.all("run") == []
