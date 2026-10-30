"""Private host declarations: real API/files, no provider/path/secret contact."""

import base64
from concurrent.futures import ThreadPoolExecutor
import io
import json
import os
import zipfile

import pytest


def project(client):
    r = client.post("/api/v1/projects", json={"name": "Private bindings Ω"})
    assert r.status_code == 201, r.text
    return r.json()


def entries(tmp_path):
    return [
        {"bindingId": "model", "kind": "artifact", "reference": "urn:example:model", "providerId": "studio.reference", "path": str(tmp_path / "Uncontacted Ω artifact.bin")},
        {"bindingId": "asset", "kind": "asset", "reference": "urn:example:asset", "providerId": "uninstalled.fixture", "assetId": "fixture:uncontacted-asset"},
        {"bindingId": "credential", "kind": "credential", "reference": "urn:example:credential", "providerId": "uninstalled.fixture", "credentialRef": "secret://fixture-handle"},
    ]


def put(client, pid, values, revision=0, **extra):
    return client.put(f"/api/v1/projects/{pid}/local-bindings", headers={"If-Match": str(revision)},
                      json={"formatVersion": "1.0", "bindings": values, **extra})


def test_private_declarations_have_their_own_revision_and_no_executable_identity(client, tmp_path, monkeypatch):
    p = project(client)
    path = f"/api/v1/projects/{p['projectId']}/local-bindings"
    before = client.post(f"/api/v1/projects/{p['projectId']}/compilations", json={"revision": p["revision"]}).json()
    store = client.app.state.studio.store
    counts = {k: store.all(k) for k in ["run", "snapshot", "operation", "project", "revision"]}
    empty = client.get(path)
    assert empty.status_code == 200 and empty.json()["bindingRevision"] == 0, empty.text
    assert empty.headers["ETag"] == '"0"' and empty.json()["bindings"] == []
    assert store.all("project_local_bindings") == []

    def forbidden(*args, **kwargs):
        pytest.fail("Saving declarations must not contact a compiler, provider or native workload")

    with monkeypatch.context() as patch:
        patch.setattr(client.app.state.studio.adapter, "compile", forbidden)
        patch.setattr(client.app.state.studio.runs, "provider_descriptors", forbidden)
        patch.setattr("xverse_studio.runs.service.subprocess.Popen", forbidden)
        response = put(client, p["projectId"], entries(tmp_path))
    assert response.status_code == 200, response.text
    result = response.json()
    assert result["bindingRevision"] == 1 and response.headers["ETag"] == '"1"'
    assert result["bindings"] == entries(tmp_path)
    assert result["validation"] == "unverified" and result["executionAllowed"] is False and result["environmentChanged"] is False
    assert {k: store.all(k) for k in counts} == counts
    after = client.post(f"/api/v1/projects/{p['projectId']}/compilations", json={"revision": p["revision"]}).json()
    assert after["planDigest"] == before["planDigest"] and after["semanticDigest"] == before["semanticDigest"]
    head = store.get("project_local_bindings", p["projectId"])
    assert not any(value in json.dumps(head) for value in [entries(tmp_path)[0]["path"], "secret://fixture-handle"])
    sidecar = store.root / head["sidecar"]
    assert sidecar.is_file() and sidecar.stat().st_mode & 0o077 == 0
    assert json.loads(sidecar.read_text())["bindings"] == result["bindings"]
    assert client.get(path).json() == result
    assert not (tmp_path / "Uncontacted Ω artifact.bin").exists()


@pytest.mark.parametrize("fault", ["missing-cas", "stale-cas", "duplicate-id", "duplicate-reference", "extra-field", "unknown-version", "inline-secret", "relative-path", "credential-value", "too-many"])
def test_invalid_binding_writes_refuse_before_head_or_sidecar_allocation(client, tmp_path, fault):
    p = project(client)
    body = {"formatVersion": "1.0", "bindings": entries(tmp_path)}
    headers = {"If-Match": "0"}
    if fault == "missing-cas":
        headers = {}
    elif fault == "stale-cas":
        headers = {"If-Match": "1"}
    elif fault == "duplicate-id":
        body["bindings"][1]["bindingId"] = body["bindings"][0]["bindingId"]
    elif fault == "duplicate-reference":
        body["bindings"][1].update(reference=body["bindings"][0]["reference"], providerId=body["bindings"][0]["providerId"])
    elif fault == "extra-field":
        body["bindings"][0]["command"] = "never execute"
    elif fault == "unknown-version":
        body["formatVersion"] = "99.0"
    elif fault == "inline-secret":
        body["bindings"][0]["reference"] = "https://user:synthetic-private-marker@example.invalid/item"
    elif fault == "relative-path":
        body["bindings"][0]["path"] = "../outside"
    elif fault == "credential-value":
        body["bindings"][2]["credentialRef"] = "password=synthetic-private-marker"
    elif fault == "too-many":
        body["bindings"] = [{**entries(tmp_path)[0], "bindingId": f"id{i}", "reference": f"urn:example:{i}"} for i in range(33)]
    result = client.put(f"/api/v1/projects/{p['projectId']}/local-bindings", headers=headers, json=body)
    assert result.status_code in (412, 422, 428), result.text
    assert "synthetic-private-marker" not in result.text
    store = client.app.state.studio.store
    assert store.all("project_local_bindings") == []
    assert not (store.root / "projects" / p["projectId"] / "local-bindings").exists()


def test_two_writers_cannot_publish_the_same_binding_revision(client, tmp_path):
    p = project(client)
    with ThreadPoolExecutor(max_workers=2) as pool:
        responses = list(pool.map(lambda _: put(client, p["projectId"], entries(tmp_path)), range(2)))
    assert sorted(r.status_code for r in responses) == [200, 412]
    assert client.get(f"/api/v1/projects/{p['projectId']}/local-bindings").json()["bindingRevision"] == 1


def test_portable_exchange_never_copies_private_locators_or_grants_bindings(client, tmp_path):
    p = project(client)
    assert put(client, p["projectId"], entries(tmp_path)).status_code == 200
    op = client.post(f"/api/v1/projects/{p['projectId']}/exports", headers={"Idempotency-Key": "private-bindings-export"}, json={"revision": p["revision"]})
    assert op.status_code == 202, op.text
    raw = client.get(op.json()["result"]["downloadUrl"]).content
    with zipfile.ZipFile(io.BytesIO(raw)) as archive:
        assert all("local-bindings" not in name for name in archive.namelist())
        assert all(entries(tmp_path)[0]["path"].encode() not in archive.read(name) and b"secret://fixture-handle" not in archive.read(name) for name in archive.namelist())
    imported = client.post("/api/v1/projects/imports", json={"archiveBase64": base64.b64encode(raw).decode()})
    assert imported.status_code == 201, imported.text
    other = client.get(f"/api/v1/projects/{imported.json()['projectId']}/local-bindings")
    assert other.status_code == 200 and other.json()["bindingRevision"] == 0 and other.json()["bindings"] == []


@pytest.mark.parametrize("target", ["reference", "assetId"])
def test_host_paths_cannot_masquerade_as_portable_identifiers(client, tmp_path, target):
    p = project(client)
    body = entries(tmp_path)
    body[0 if target == "reference" else 1][target] = "/srv/private-host-only"
    response = put(client, p["projectId"], body)
    assert response.status_code == 422 and "private-host-only" not in response.text, response.text


def test_complete_sidecar_size_is_bounded_before_file_allocation(client):
    p = project(client)
    body = [{"bindingId": f"model{i}", "kind": "artifact", "reference": f"urn:example:{i}",
             "providerId": "studio.reference", "path": "/" + "x" * 3900} for i in range(32)]
    response = put(client, p["projectId"], body)
    assert response.status_code == 413 and response.json()["code"] == "LIMIT_EXCEEDED", response.text
    store = client.app.state.studio.store
    assert store.all("project_local_bindings") == []
    assert not (store.root / "projects" / p["projectId"] / "local-bindings").exists()


def test_binding_routes_enforce_sessions_origin_and_csrf_without_contact(client, tmp_path):
    p = project(client)
    path = f"/api/v1/projects/{p['projectId']}/local-bindings"
    assert client.get(path, headers={"Cookie": ""}).status_code == 401
    for headers in [{"Origin": "https://outside.invalid", "If-Match": "0"}, {"X-CSRF-Token": "invalid", "If-Match": "0"}]:
        assert client.put(path, headers=headers, json={"bindings": entries(tmp_path)}).status_code == 403
    assert client.app.state.studio.store.all("project_local_bindings") == []


def test_private_binding_changes_do_not_rewrite_current_source_or_layout(client, tmp_path):
    p = project(client)
    path = client.app.state.studio.projects._dir(p["projectId"], p["revision"]) / "project.studio.json"
    path.write_bytes(b'{"foreign":"unresolved source envelope"}')
    assert put(client, p["projectId"], entries(tmp_path)).status_code == 200
    assert client.get("/api/v1/projects/" + p["projectId"]).json()["sourceIntegrity"] == "modified"
    assert path.read_bytes() == b'{"foreign":"unresolved source envelope"}'


def test_declared_native_path_is_never_opened_or_inspected(client, tmp_path, monkeypatch):
    p = project(client)
    values = entries(tmp_path)
    target = values[0]["path"]
    for name in ("open", "stat", "lstat"):
        original = getattr(os, name)

        def guarded(path, *args, _original=original, **kwargs):
            if not isinstance(path, int) and os.fsdecode(path) == target:
                pytest.fail("A declaration must not open or inspect its artifact target")
            return _original(path, *args, **kwargs)

        monkeypatch.setattr(os, name, guarded)
    assert put(client, p["projectId"], values).status_code == 200
    assert client.get(f"/api/v1/projects/{p['projectId']}/local-bindings").json()["bindings"] == values


def test_import_rejects_private_sidecar_instead_of_adopting_host_state(client):
    p = project(client)
    result = client.post(f"/api/v1/projects/{p['projectId']}/exports", headers={"Idempotency-Key": "foreign-private-sidecar"}, json={"revision": p["revision"]})
    raw = client.get(result.json()["result"]["downloadUrl"]).content
    payload = io.BytesIO()
    with zipfile.ZipFile(io.BytesIO(raw)) as original, zipfile.ZipFile(payload, "w") as modified:
        for name in original.namelist():
            modified.writestr(name, original.read(name))
        modified.writestr("local-bindings/foreign.json", '{"formatVersion":"99.0","executionAllowed":true}')
    response = client.post("/api/v1/projects/imports", json={"archiveBase64": base64.b64encode(payload.getvalue()).decode()})
    assert response.status_code == 422 and response.json()["code"] == "UNSAFE_ARCHIVE", response.text
    assert len(client.app.state.studio.store.all("project")) == 1
    assert client.app.state.studio.store.all("project_local_bindings") == []


def test_source_and_layout_saves_keep_independent_binding_head(client, tmp_path):
    p = project(client)
    assert put(client, p["projectId"], entries(tmp_path)).status_code == 200
    store = client.app.state.studio.store
    head = store.get("project_local_bindings", p["projectId"])
    raw = (store.root / head["sidecar"]).read_bytes()
    doc = next(iter(p["documents"]))
    updated = client.put(f"/api/v1/projects/{p['projectId']}/documents/{doc}", headers={"If-Match": str(p["revision"])},
                         json={"content": "# retained private bindings\n" + p["documents"][doc]["content"], "format": "yaml"})
    assert updated.status_code == 200, updated.text
    layout = client.put(f"/api/v1/projects/{p['projectId']}/layout", headers={"If-Match": str(p["presentationRevision"])},
                        json={"positions": {"control": {"x": 100, "y": 10}}})
    assert layout.status_code == 200, layout.text
    assert store.get("project_local_bindings", p["projectId"]) == head
    assert (store.root / head["sidecar"]).read_bytes() == raw
    assert client.get(f"/api/v1/projects/{p['projectId']}/local-bindings").json()["bindingRevision"] == 1
