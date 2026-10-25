import base64
import io
import zipfile


def test_project_exchange_preserves_sources_layout_and_no_execution(client):
    p = client.post("/api/v1/projects", json={"name": "Portable System Ω"}).json()
    source = {id: d["content"] for id, d in p["documents"].items()}
    response = client.put(
        f"/api/v1/projects/{p['projectId']}/layout",
        headers={"If-Match": str(p["presentationRevision"])},
        json={"positions": {"controller": {"x": 42.0, "y": 24.0}}},
    )
    assert response.status_code == 200, response.text
    op = client.post(
        f"/api/v1/projects/{p['projectId']}/exports",
        headers={"Idempotency-Key": "export"},
        json={"revision": p["revision"]},
    )
    assert op.status_code == 202, op.text
    archive = client.get(op.json()["result"]["downloadUrl"])
    assert archive.status_code == 200
    files = zipfile.ZipFile(io.BytesIO(archive.content))
    assert "owner.key" not in files.namelist()
    imported = client.post(
        "/api/v1/projects/imports",
        json={"archiveBase64": base64.b64encode(archive.content).decode()},
    )
    assert imported.status_code == 201, imported.text
    copy = imported.json()
    assert copy["projectId"] != p["projectId"]
    assert sorted(d["content"] for d in copy["documents"].values()) == sorted(
        source.values()
    )
    assert copy["layout"]["positions"]["controller"]["x"] == 42.0
    a = client.post(
        f"/api/v1/projects/{p['projectId']}/compilations",
        json={"revision": p["revision"]},
    ).json()
    b = client.post(
        f"/api/v1/projects/{copy['projectId']}/compilations",
        json={"revision": copy["revision"]},
    ).json()
    assert a["planDigest"] == b["planDigest"]
    assert client.get("/api/v1/runs").json()["items"] == []


import json

import pytest
from ruamel.yaml import YAML

from xverse_studio.xdl import examples


def _archive(documents, manifest=None, extra=None):
    data = io.BytesIO()
    with zipfile.ZipFile(data, "w") as z:
        z.writestr("project.studio.json", json.dumps(manifest or {
            "formatVersion": "1.0", "name": "Imported scenario",
            "resources": [{"path": "xdl/" + n, "format": "yaml"} for n in documents],
            "profiles": [], "layoutFiles": []}))
        for name, content in documents.items():
            z.writestr("xdl/" + name, content)
        for name, content in (extra or {}).items():
            z.writestr(name, content)
    return base64.b64encode(data.getvalue()).decode()


def _import(client, archive):
    return client.post("/api/v1/projects/imports", json={"archiveBase64": archive})


@pytest.mark.parametrize("example", [e["id"] for e in examples()])
def test_prepared_examples_onboard_ready_with_exact_bytes(client, example):
    entry = next(e for e in examples() if e["id"] == example)
    project = client.post("/api/v1/projects", json={"name": entry["name"], "blueprintRef": example})
    assert project.status_code == 201, project.text
    project = project.json()
    contents = {d["path"].rsplit("/", 1)[-1]: d["content"] for d in project["documents"].values()}
    assert contents == entry["documents"]
    # The guided entry states what it demonstrates and what stays unavailable.
    assert entry["scope"] == "owned_reference" and entry["maturity"] == "fixture"
    assert entry["limitations"] and entry["expectedObservations"]
    validation = client.post(f"/api/v1/projects/{project['projectId']}/validations",
                             json={"revision": project["revision"]}).json()
    assert validation["valid"]
    preflight = client.post(f"/api/v1/projects/{project['projectId']}/preflights",
                            json={"revision": project["revision"]}).json()
    assert preflight["status"] == "ready"
    assert client.get("/api/v1/runs").json()["items"] == []  # onboarding executes nothing


@pytest.mark.parametrize("change,code", [
    (lambda m: m.update(formatVersion="2.0"), "FORMAT_UNSUPPORTED"),
    (lambda m: m["resources"].append({"path": "xdl/missing.xdl.yaml", "format": "yaml"}), "MANIFEST_INVALID"),
    (lambda m: m.update(resources=[]), "MANIFEST_INVALID"),
])
def test_invalid_imports_are_refused_without_creating_a_project(client, change, code):
    documents = examples()[0]["documents"]
    manifest = {"formatVersion": "1.0", "name": "Broken",
                "resources": [{"path": "xdl/" + n, "format": "yaml"} for n in documents],
                "profiles": [], "layoutFiles": []}
    change(manifest)
    before = len(client.get("/api/v1/projects").json()["items"])
    response = _import(client, _archive(documents, manifest))
    assert response.status_code in (400, 409, 422), response.text
    assert response.json()["code"] == code
    assert len(client.get("/api/v1/projects").json()["items"]) == before


def test_unsafe_archive_paths_are_refused(client):
    documents = examples()[0]["documents"]
    before = len(client.get("/api/v1/projects").json()["items"])
    response = _import(client, _archive(documents, extra={"../escape.txt": "x"}))
    assert response.status_code in (400, 422)
    assert response.json()["code"] in ("UNSAFE_ARCHIVE", "UNSAFE_PATH", "INVALID_ARCHIVE")
    assert len(client.get("/api/v1/projects").json()["items"]) == before


def test_unknown_extension_is_preserved_inspectable_and_never_executed(client):
    documents = dict(examples()[0]["documents"])
    system = YAML(typ="safe").load(documents["system.xdl.yaml"])
    system["extensions"] = {"org.example.unresolved": {"script": "rm -rf /", "opaque": [1, 2, 3]}}
    out = io.StringIO()
    YAML().dump(system, out)
    documents["system.xdl.yaml"] = out.getvalue()
    response = _import(client, _archive(documents))
    assert response.status_code == 201, response.text
    project = response.json()
    stored = {d["path"].rsplit("/", 1)[-1]: d["content"] for d in project["documents"].values()}
    assert stored["system.xdl.yaml"] == documents["system.xdl.yaml"]
    validation = client.post(f"/api/v1/projects/{project['projectId']}/validations",
                             json={"revision": project["revision"]}).json()
    # The unresolved namespace is identified as such, not dropped or reported as a generic error.
    assert not validation["valid"]
    assert any(d["code"] == "XDL-SEMANTIC-PROFILE-MISSING" and "org.example.unresolved" in d["message"]
               for d in validation["diagnostics"])
    preflight = client.post(f"/api/v1/projects/{project['projectId']}/preflights",
                            json={"revision": project["revision"]}).json()
    assert preflight["status"] == "blocked"
    assert "XDL-SEMANTIC-PROFILE-MISSING" in {d["code"] for d in preflight["diagnostics"]}
    edit = client.post(f"/api/v1/projects/{project['projectId']}/edits",
                       headers={"If-Match": str(project["revision"])},
                       json={"baseRevision": project["revision"], "edits": [
                           {"kind": "set_parameter", "parameterId": "gain", "value": 0.5}]})
    assert edit.status_code == 422 and edit.json()["code"] == "MODEL_INVALID"
    op = client.post(f"/api/v1/projects/{project['projectId']}/exports",
                     headers={"Idempotency-Key": "unknown-extension-export"},
                     json={"revision": project["revision"]})
    exported = zipfile.ZipFile(io.BytesIO(client.get(op.json()["result"]["downloadUrl"]).content))
    assert exported.read("xdl/system.xdl.yaml").decode() == documents["system.xdl.yaml"]
    # Neither save path discards it: a layout save keeps every source byte, and a source
    # save stores exactly the authored text, extension included.
    pid = project["projectId"]
    system_id = next(i for i, d in project["documents"].items() if d["path"].endswith("/system.xdl.yaml"))
    layout = client.put(f"/api/v1/projects/{pid}/layout", headers={"If-Match": str(project["presentationRevision"])},
                        json={"positions": {"plant": {"x": 1.0, "y": 2.0}}})
    assert layout.status_code == 200, layout.text
    assert layout.json()["documents"][system_id]["content"] == documents["system.xdl.yaml"]
    edited = documents["system.xdl.yaml"].replace("description:", "description: Edited.", 1)
    assert edited != documents["system.xdl.yaml"]
    saved = client.put(f"/api/v1/projects/{pid}/documents/{system_id}",
                       headers={"If-Match": str(layout.json()["revision"])}, json={"content": edited})
    assert saved.status_code == 200, saved.text
    stored = client.get(f"/api/v1/projects/{pid}").json()["documents"][system_id]["content"]
    assert stored == edited and "org.example.unresolved" in stored and "rm -rf /" in stored
    assert client.get("/api/v1/runs").json()["items"] == []


@pytest.mark.parametrize("parameter,value,ready", [
    ("duration", 0.1, True), ("duration", 30, True),
    ("duration", 0, False), ("duration", 31, False), ("timestep", 0, False), ("gain", 50, False),
    ("fault", "stuck-sensor", True), ("fault", "bogus", False),
])
def test_parameter_validation_blocks_out_of_bound_drafts_at_admission(client, parameter, value, ready):
    project = client.post("/api/v1/projects", json={"name": "Parameters"}).json()
    edit = client.post(f"/api/v1/projects/{project['projectId']}/edits",
                       headers={"If-Match": str(project["revision"])},
                       json={"baseRevision": project["revision"], "edits": [
                           {"kind": "set_parameter", "parameterId": parameter, "value": value}]})
    assert edit.status_code == 200, edit.text  # a draft may hold an inadmissible value
    project = edit.json()
    preflight = client.post(f"/api/v1/projects/{project['projectId']}/preflights",
                            json={"revision": project["revision"]}).json()
    assert (preflight["status"] == "ready") is ready
    if not ready:
        codes = {d["code"] for d in preflight["diagnostics"]}
        # Numeric bounds report LIMIT_EXCEEDED; a categorical value outside its domain is unsupported.
        assert ("LIMIT_EXCEEDED" if parameter != "fault" else "CAPABILITY_UNSUPPORTED") in codes
        assert all(d.get("message") for d in preflight["diagnostics"])


def test_mistyped_parameter_values_are_refused_before_a_draft(client):
    project = client.post("/api/v1/projects", json={"name": "Typed parameters"}).json()
    edit = client.post(f"/api/v1/projects/{project['projectId']}/edits",
                       headers={"If-Match": str(project["revision"])},
                       json={"baseRevision": project["revision"], "edits": [
                           {"kind": "set_parameter", "parameterId": "duration", "value": "fast"}]})
    assert edit.status_code == 422 and edit.json()["code"] == "MODEL_INVALID"
    assert client.get(f"/api/v1/projects/{project['projectId']}").json()["revision"] == project["revision"]
