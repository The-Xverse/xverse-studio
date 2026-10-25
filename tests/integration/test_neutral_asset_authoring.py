"""Logical asset edits are atomic authored changes with no execution side effects."""
from copy import deepcopy


def test_http_logical_asset_authoring_is_inert_atomic_and_execution_is_unavailable(client, monkeypatch):
    import subprocess

    def forbidden(*args, **kwargs):
        raise AssertionError("Logical asset authoring must not create a process")

    monkeypatch.setattr(subprocess, "Popen", forbidden)
    project = client.post("/api/v1/projects", json={"name": "Neutral logical assets"}).json()
    pid = project["projectId"]
    doc_id = next(key for key, doc in project["documents"].items() if doc["path"].endswith("system.xdl.yaml"))
    before = deepcopy(project)
    edit = {"kind": "add_logical_asset", "documentId": doc_id, "assetKind": "device", "elementId": "logical-device",
            "properties": {"capabilities": ["measurement"], "supportedRealizationClasses": ["simulated", "physical"], "nodeId": "plant-node"},
            "endpoints": [{"id": "logical-device-out", "ownerId": "logical-device", "interfaceId": "state", "direction": "output"}]}
    response = client.post(f"/api/v1/projects/{pid}/edits", headers={"If-Match": "1"}, json={"baseRevision": 1, "edits": [edit]})
    assert response.status_code == 200, response.text
    changed = response.json()
    assert changed["revision"] == 2
    assert changed["documents"][doc_id]["content"] != before["documents"][doc_id]["content"]
    assert all(changed["documents"][key]["content"] == doc["content"] for key, doc in before["documents"].items() if key != doc_id)
    validation = client.post(f"/api/v1/projects/{pid}/validations", json={"revision": 2})
    assert validation.status_code == 200, validation.text
    assert validation.json()["valid"]
    preflight = client.post(f"/api/v1/projects/{pid}/preflights", json={"revision": 2})
    assert preflight.status_code == 200, preflight.text
    assert preflight.json()["status"] != "ready"
    assert client.get("/api/v1/runs").json()["items"] == []

    invalid = edit | {"elementId": "broken-device", "properties": edit["properties"] | {"nodeId": "missing"}, "endpoints": []}
    rejected = client.post(f"/api/v1/projects/{pid}/edits", headers={"If-Match": "2"}, json={"baseRevision": 2, "edits": [invalid]})
    assert rejected.status_code == 422, rejected.text
    after = client.get(f"/api/v1/projects/{pid}").json()
    assert after["revision"] == 2
    assert after["documents"] == changed["documents"]
    stale = client.post(f"/api/v1/projects/{pid}/edits", headers={"If-Match": "1"}, json={"baseRevision": 1, "edits": [invalid]})
    assert stale.status_code == 412
