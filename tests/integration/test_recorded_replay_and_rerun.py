"""Recorded reads are inert; a rerun is a separately admitted owned execution."""
import base64
import time

import pytest

from xverse_studio.api.reruns import Reruns


def original_run(client):
    project = client.post("/api/v1/projects", json={"name": "Recorded replay and rerun"}).json()
    project = client.post(f"/api/v1/projects/{project['projectId']}/edits", headers={"If-Match": "1"},
                          json={"baseRevision": 1, "edits": [{"kind": "set_parameter", "parameterId": "duration", "value": .2}]}).json()
    preflight = client.post(f"/api/v1/projects/{project['projectId']}/preflights", json={"revision": project["revision"]}).json()
    assert preflight["status"] == "ready", preflight
    response = client.post("/api/v1/runs", headers={"Idempotency-Key": "original-recorded-run"}, json={"snapshotId": preflight["snapshotId"], "preflightId": preflight["preflightId"]})
    assert response.status_code == 202, response.text
    run_id = response.json()["runId"]
    deadline = time.monotonic() + 12
    while time.monotonic() < deadline:
        run = client.get("/api/v1/runs/" + run_id).json()
        if run["state"] == "stopped":
            return project, run
        if run["state"] in {"failed", "unknown"}:
            raise AssertionError(run)
        time.sleep(.05)
    raise AssertionError(run)


def rerun(client, run_id, key="fresh-rerun"):
    response = client.post(f"/api/v1/runs/{run_id}/reruns", headers={"Idempotency-Key": key}, json={})
    assert response.status_code == 202, response.text
    operation = client.get("/api/v1/operations/" + response.json()["operationId"])
    assert operation.status_code == 200, operation.text
    return response.json(), operation.json()


def test_recorded_reads_create_nothing_and_fresh_rerun_uses_original_frozen_inputs(client):
    project, original = original_run(client)
    store = client.app.state.studio.store
    runs = client.app.state.studio.runs
    frozen = store.get("snapshot", original["snapshotId"])
    snapshot_path = store.root / "snapshots" / original["snapshotId"] / "snapshot.json"
    journal_path = runs.directory(original["runId"]) / "evidence.jsonl"
    before = (snapshot_path.read_bytes(), journal_path.read_bytes(), store.all("evaluation"))
    for endpoint in ("observations", "history", "evidence"):
        assert client.get(f"/api/v1/runs/{original['runId']}/{endpoint}").status_code == 200
    assert len(store.all("run")) == 1
    assert len(store.all("snapshot")) == 1
    # A later editable draft is deliberately different. It is not the rerun source.
    changed = client.post(f"/api/v1/projects/{project['projectId']}/edits", headers={"If-Match": str(project["revision"])},
                          json={"baseRevision": project["revision"], "edits": [{"kind": "set_parameter", "parameterId": "target", "value": 2.0}]})
    assert changed.status_code == 200, changed.text
    accepted, operation = rerun(client, original["runId"])
    assert operation["status"] == "completed", operation
    child_id = operation["result"]["runId"]
    child = store.get("run", child_id)
    assert child_id != original["runId"]
    assert child["snapshotId"] != original["snapshotId"]
    copied = store.get("snapshot", child["snapshotId"])
    assert copied["documents"] == frozen["documents"]
    assert copied["configuration"]["target"] == 1
    assert copied["planDigest"] == original["planDigest"]
    assert copied["parentSnapshotId"] == original["snapshotId"]
    assert copied["sourceRunId"] == original["runId"]
    assert copied["capabilityDigest"]
    assert rerun(client, original["runId"])[0] == accepted
    assert len(store.all("run")) == 2
    assert (snapshot_path.read_bytes(), journal_path.read_bytes(), store.all("evaluation")) == before


@pytest.mark.parametrize("target", ["file", "database"])
def test_original_snapshot_tamper_rejects_before_creating_child(client, target):
    _, original = original_run(client)
    store = client.app.state.studio.store
    snapshot = store.get("snapshot", original["snapshotId"])
    if target == "file":
        path = store.root / "snapshots" / original["snapshotId"] / "snapshot.json"
        path.write_bytes(path.read_bytes() + b"\n")
    else:
        snapshot["configuration"]["target"] = 99
        store.put("snapshot", snapshot["snapshotId"], snapshot)
    response = client.post(f"/api/v1/runs/{original['runId']}/reruns", headers={"Idempotency-Key": "tampered-source"}, json={})
    assert response.status_code == 422, response.text
    assert response.json()["code"] == "SNAPSHOT_INTEGRITY"
    assert len(store.all("run")) == 1
    assert len(store.all("snapshot")) == 1


def test_changed_current_plan_or_unavailable_provider_rejects_before_start(client, monkeypatch):
    from xverse_studio.api import reruns as module
    _, original = original_run(client)
    service = client.app.state.studio.reruns
    compile_original = service.adapter.compile
    def changed(*args, **kwargs):
        result = compile_original(*args, **kwargs)
        return {**result, "planDigest": "sha256:" + "0" * 64}
    with monkeypatch.context() as patch:
        patch.setattr(service.adapter, "compile", changed)
        response = client.post(f"/api/v1/runs/{original['runId']}/reruns", headers={"Idempotency-Key": "changed-compiler"}, json={})
        assert response.status_code == 422
        assert response.json()["code"] == "RERUN_INPUT_INCOMPATIBLE"
    with monkeypatch.context() as patch:
        patch.setattr(module, "descriptors", lambda: [{"providerId": "studio.reference", "available": False, "hostCompatible": True}])
        response = client.post(f"/api/v1/runs/{original['runId']}/reruns", headers={"Idempotency-Key": "provider-unavailable"}, json={})
        assert response.status_code == 503
    assert len(client.app.state.studio.store.all("run")) == 1


def test_invalid_old_evidence_does_not_change_source_inputs_or_prevent_fresh_observations(client):
    _, original = original_run(client)
    runs = client.app.state.studio.runs
    path = runs.directory(original["runId"]) / "evidence.jsonl"
    tampered = path.read_bytes() + b"tampered old journal\n"
    path.write_bytes(tampered)
    assert client.get(f"/api/v1/runs/{original['runId']}/evidence").json()["integrity"] == "invalid"
    _, operation = rerun(client, original["runId"])
    assert operation["status"] == "completed"
    child_id = operation["result"]["runId"]
    deadline = time.monotonic() + 12
    while time.monotonic() < deadline:
        child = client.get("/api/v1/runs/" + child_id).json()
        if child["state"] == "stopped":
            break
        time.sleep(.05)
    assert child["state"] == "stopped", child
    assert client.get(f"/api/v1/runs/{child_id}/evidence").json()["integrity"] == "valid"
    assert path.read_bytes() == tampered


def test_child_acknowledgement_loss_reconciles_mapping_without_duplicate_start(client, monkeypatch):
    _, original = original_run(client)
    runs = client.app.state.studio.runs
    start = runs.start
    calls = []
    def lost_ack(*args, **kwargs):
        calls.append(args)
        start(*args, **kwargs)
        raise OSError("synthetic acknowledgement loss after accepted child")
    with monkeypatch.context() as patch:
        patch.setattr(runs, "start", lost_ack)
        accepted, operation = rerun(client, original["runId"], "lost-child-ack")
        assert operation["status"] == "completed", operation
        assert rerun(client, original["runId"], "lost-child-ack")[0] == accepted
    assert len(calls) == 1
    assert len(client.app.state.studio.store.all("run")) == 2


def test_restart_unknown_dispatch_never_replays_start(client, monkeypatch):
    _, original = original_run(client)
    service = client.app.state.studio.reruns
    class Interrupted(BaseException):
        pass
    with monkeypatch.context() as patch:
        patch.setattr(service, "dispatch", lambda operation_id: (_ for _ in ()).throw(Interrupted()))
        with pytest.raises(Interrupted):
            service.create(original["runId"], "local-operator", "interrupted-rerun")
    before = len(client.app.state.studio.store.all("run"))
    with monkeypatch.context() as patch:
        patch.setattr(client.app.state.studio.runs, "start", lambda *args, **kwargs: (_ for _ in ()).throw(AssertionError("restart must never replay start")))
        restored = Reruns(service.store, service.projects, service.runs, service.adapter)
        restored.reconcile_pending()
        operations = [op for op in service.store.all("operation") if op.get("kind") == "rerun"]
        assert len(operations) == 1
        assert operations[0]["status"] == "unknown"
        assert restored.create(original["runId"], "local-operator", "interrupted-rerun") == {"operationId": operations[0]["operationId"]}
    assert len(service.store.all("run")) == before


def test_imported_evidence_has_no_run_authority_and_public_frozen_override_rejects(client):
    _, original = original_run(client)
    exported = client.post(f"/api/v1/runs/{original['runId']}/exports", headers={"Idempotency-Key": "rerun-import-boundary"}, json={}).json()
    archive = client.get(exported["result"]["downloadUrl"]).content
    imported = client.post("/api/v1/evidence/imports", json={"archiveBase64": base64.b64encode(archive).decode()})
    assert imported.status_code == 201, imported.text
    response = client.post(f"/api/v1/runs/{imported.json()['bundleId']}/reruns", headers={"Idempotency-Key": "import-is-not-run"}, json={})
    assert response.status_code == 404
    response = client.post(f"/api/v1/runs/{original['runId']}/reruns", headers={"Idempotency-Key": "forbidden-frozen-override"}, json={"allow_frozen": True})
    assert response.status_code == 422
    assert len(client.app.state.studio.store.all("run")) == 1
