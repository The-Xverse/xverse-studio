"""Owned hostile archives through the authenticated Linux import boundary (T009)."""

import base64
from contextlib import contextmanager
import io
import json
import random
import string
import subprocess
import zipfile

import pytest
from fastapi.testclient import TestClient

from xverse_studio.security.files import read_archive
from xverse_studio.storage.core import Problem
from xverse_studio.xdl import examples


def archive(entries, compression=zipfile.ZIP_STORED):
    data = io.BytesIO()
    with zipfile.ZipFile(data, "w", compression=compression) as bundle:
        for name, content in entries:
            bundle.writestr(name, content)
    return base64.b64encode(data.getvalue()).decode()


def project_entries(manifest):
    documents = examples()[0]["documents"]
    return [("project.studio.json", json.dumps(manifest)),
            *(("xdl/" + name, content) for name, content in documents.items())]


def manifest():
    return {"formatVersion": "1.0", "name": "Hostile import fixture",
            "resources": [{"path": "xdl/" + name, "format": "yaml"}
                          for name in examples()[0]["documents"]],
            "profiles": [], "layoutFiles": []}


@contextmanager
def unchanged_workspace(client, monkeypatch):
    existing = client.post("/api/v1/projects", json={"name": "Preserve existing System Ω"})
    assert existing.status_code == 201, existing.text
    before = client.get("/api/v1/projects").json()
    store = client.app.state.studio.store
    prior_records = store.all("project")
    source = client.get("/api/v1/projects/" + existing.json()["projectId"]).json()
    files = sorted(p.relative_to(store.root).as_posix() for p in (store.root / "projects").rglob("*") if p.is_file())
    monkeypatch.setattr(subprocess, "Popen", lambda *a, **k: pytest.fail("Project import must never dispatch"))
    yield
    assert client.get("/api/v1/projects").json() == before
    assert store.all("project") == prior_records
    assert client.get("/api/v1/projects/" + existing.json()["projectId"]).json() == source
    assert sorted(p.relative_to(store.root).as_posix() for p in (store.root / "projects").rglob("*") if p.is_file()) == files
    assert store.all("run") == [] and store.all("operation") == []


@pytest.mark.parametrize("shape", ["root-list", "root-null", "root-string", "profile-null", "profile-string",
                                   "name-object", "name-empty", "name-oversized", "layout-list", "nested-manifest"])
def test_malformed_manifest_shapes_have_typed_failure_without_mutation(client, monkeypatch, shape):
    value = manifest()
    extras = []
    if shape == "root-list":
        value = []
    elif shape == "root-null":
        value = None
    elif shape == "root-string":
        value = "not a project manifest"
    elif shape.startswith("profile-"):
        value["profiles"] = [None if shape == "profile-null" else "not a lock"]
    elif shape.startswith("name-"):
        value["name"] = {"unexpected": "shape"} if shape == "name-object" else "" if shape == "name-empty" else "x" * 121
    elif shape == "layout-list":
        value["layoutFiles"] = ["layout/model.json"]
        extras = [("layout/model.json", "[1,2,3]")]
    entries = project_entries(value) + extras
    if shape == "nested-manifest":
        entries[0] = ("project.studio.json", "[" * 10000 + "0" + "]" * 10000)
    with unchanged_workspace(client, monkeypatch):
        response = client.post("/api/v1/projects/imports", json={"archiveBase64": archive(entries)})
        assert response.status_code == 422, response.text
        assert response.json()["code"] == "MANIFEST_INVALID"


@pytest.mark.parametrize("attack", ["entry-count", "document-size", "compression-ratio", "expanded-total", "request-size"])
def test_archive_budgets_refuse_before_project_allocation(client, monkeypatch, attack):
    compression = zipfile.ZIP_STORED
    if attack == "entry-count":
        entries = [(f"xdl/source-{index}.yaml", "x") for index in range(257)]
    elif attack == "document-size":
        entries = [("README.md", "x" * (1024 * 1024 + 1))]
    elif attack == "compression-ratio":
        entries = [("README.md", "x" * 65536)]
        compression = zipfile.ZIP_DEFLATED
    elif attack == "expanded-total":
        # Each individual entry is within its size and ratio bounds; their sum is not.
        generator = random.Random(0)
        block = "".join(generator.choices(string.ascii_letters + string.digits, k=16384))
        entries = [(f"xdl/source-{index}.yaml", block * 64) for index in range(17)]
        compression = zipfile.ZIP_DEFLATED
    else:
        entries = [("README.md", "x" * (6 * 1024 * 1024))]
    encoded = archive(entries, compression)
    if attack == "expanded-total":
        with zipfile.ZipFile(io.BytesIO(base64.b64decode(encoded))) as bundle:
            assert all(info.file_size <= 1024 * 1024 and info.file_size / info.compress_size < 100
                       for info in bundle.infolist())
        assert len(json.dumps({"archiveBase64": encoded}).encode()) < 8 * 1024 * 1024
    with unchanged_workspace(client, monkeypatch):
        response = client.post("/api/v1/projects/imports", json={"archiveBase64": encoded})
        assert response.status_code == 413, response.text
        assert response.json()["code"] == "LIMIT_EXCEEDED"
        if attack == "request-size":
            assert "Request byte limit" in response.json()["message"]


def test_direct_import_parser_also_bounds_compressed_bytes():
    # HTTP bounds the base64 request first. Direct host callers still need the ZIP byte bound.
    encoded = archive([("README.md", "x" * (8 * 1024 * 1024))])
    with pytest.raises(Problem) as rejected:
        read_archive(encoded)
    assert rejected.value.code == "LIMIT_EXCEEDED" and rejected.value.status == 413
    assert "Compressed archive limit" in rejected.value.message


@pytest.mark.parametrize("name,content,code", [
    ("profiles/untrusted.json", '{"script":"create-synthetic-marker"}', "UNSAFE_PROFILE"),
    ("profiles/untrusted.json", '{"help":"<script>create-synthetic-marker</script>"}', "UNSAFE_PROFILE"),
    ("profiles/untrusted.json", '{"help":"javascript:create-synthetic-marker"}', "UNSAFE_PROFILE"),
    ("README.md", "password: synthetic-private-marker", "CREDENTIAL_REJECTED"),
    ("README.md", "https://user:synthetic-private-marker@example.invalid", "CREDENTIAL_REJECTED"),
    ("xdl/run.py", "create-synthetic-marker", "UNSAFE_ARCHIVE"),
    ("xdl/start.sh", "create-synthetic-marker", "UNSAFE_ARCHIVE"),
])
def test_credential_script_and_executable_entries_are_inert_and_not_echoed(client, monkeypatch, name, content, code):
    with unchanged_workspace(client, monkeypatch):
        response = client.post("/api/v1/projects/imports", json={"archiveBase64": archive(project_entries(manifest()) + [(name, content)])})
        assert response.status_code == 422, response.text
        assert response.json()["code"] == code
        assert "synthetic-private-marker" not in response.text and "create-synthetic-marker" not in response.text


@pytest.mark.parametrize("name", ["//server/share/document.yaml", "\\\\?\\C:\\outside\\document.yaml", "\\\\.\\GLOBALROOT\\document.yaml"])
def test_foreign_device_and_unc_paths_cannot_escape_on_linux(client, monkeypatch, name):
    with unchanged_workspace(client, monkeypatch):
        response = client.post("/api/v1/projects/imports", json={"archiveBase64": archive([(name, "untrusted")])})
        assert response.status_code == 422 and response.json()["code"] == "UNSAFE_PATH"


def test_foreign_junction_metadata_cannot_create_a_filesystem_link(client, monkeypatch):
    info = zipfile.ZipInfo("xdl/junction")
    info.create_system = 0  # DOS directory and reparse-point attributes are untrusted metadata.
    info.external_attr = 0x410
    with unchanged_workspace(client, monkeypatch):
        response = client.post("/api/v1/projects/imports", json={"archiveBase64": archive([(info, "C:\\outside")])})
        assert response.status_code == 422 and response.json()["code"] == "UNSAFE_ARCHIVE"


@pytest.mark.parametrize("boundary", ["no-session", "foreign-host", "foreign-origin", "no-csrf"])
def test_import_mutations_require_the_original_session_host_origin_and_csrf(client, monkeypatch, boundary):
    payload = {"archiveBase64": archive(project_entries(manifest()))}
    with unchanged_workspace(client, monkeypatch):
        if boundary == "no-session":
            with TestClient(client.app, base_url="http://testserver") as anonymous:
                response = anonymous.post("/api/v1/projects/imports", headers={"Origin": "http://testserver"}, json=payload)
            assert response.status_code == 401 and response.json()["code"] == "UNAUTHORIZED"
        else:
            headers = {"Host": "foreign.invalid"} if boundary == "foreign-host" else {
                "Origin": "http://foreign.invalid"} if boundary == "foreign-origin" else {"X-CSRF-Token": ""}
            response = client.post("/api/v1/projects/imports", headers=headers, json=payload)
            assert response.status_code == 403 and response.json()["code"] == "FORBIDDEN"


def test_allowed_foreign_reparse_metadata_remains_plain_inert_source(client, monkeypatch, tmp_path):
    outside = tmp_path / "outside-source.yaml"
    outside.write_bytes(b"private outside bytes must not be read or changed")
    value = manifest()
    value["resources"] = [{"path": "xdl/reparse.yaml", "format": "yaml"}]
    info = zipfile.ZipInfo("xdl/reparse.yaml")
    info.create_system, info.external_attr = 0, 0x400  # foreign reparse metadata
    target_text = str(outside)
    encoded = archive([("project.studio.json", json.dumps(value)), (info, target_text)])
    monkeypatch.setattr(subprocess, "Popen", lambda *a, **k: pytest.fail("Foreign link metadata must never dispatch"))
    response = client.post("/api/v1/projects/imports", json={"archiveBase64": encoded})
    assert response.status_code == 201, response.text
    project = response.json()
    document_id = next(iter(project["documents"]))
    path = client.app.state.studio.projects.document_path(project["projectId"], document_id)
    assert path.is_file() and not path.is_symlink() and path.read_text() == target_text
    assert outside.read_bytes() == b"private outside bytes must not be read or changed"
    preflight = client.post(f"/api/v1/projects/{project['projectId']}/preflights", json={"revision": project["revision"]})
    assert preflight.status_code == 200 and preflight.json()["status"] == "blocked"
    assert client.get("/api/v1/runs").json()["items"] == []


def test_valid_import_preserves_unknown_manifest_and_xdl_payloads(client, monkeypatch):
    value = manifest()
    value["org.example.opaque"] = {"labels": ["kept", 42], "unknownVersion": "900"}
    encoded = archive(project_entries(value))
    monkeypatch.setattr(subprocess, "Popen", lambda *a, **k: pytest.fail("Project import must never dispatch"))
    response = client.post("/api/v1/projects/imports", json={"archiveBase64": encoded})
    assert response.status_code == 201, response.text
    project = response.json()
    assert project["manifest"]["org.example.opaque"] == value["org.example.opaque"]
    assert {doc["path"].removeprefix("xdl/"): doc["content"] for doc in project["documents"].values()} == examples()[0]["documents"]
    assert client.get("/api/v1/runs").json()["items"] == []
