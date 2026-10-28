"""Real owned worker rejection; only its delegated request copy is faulted.

The authenticated service and worker run normally. A test-only write boundary
corrupts the private delegated copy after admission; immutable Project/snapshot
sources remain untouched. No imported code, equipment or external provider runs.
"""

import hashlib
import json
from pathlib import Path
import sys
import time

import pytest

from xverse_studio.storage.core import canonical, digest


@pytest.mark.parametrize("fault", ["configuration", "plan_digest", "pause_budget"])
def test_native_startup_rejection_preserves_identity_without_start_or_evidence(
    client, monkeypatch, fault
):
    from xverse_studio.runs import service as run_module

    created = client.post("/api/v1/projects", json={"name": "Owned startup rejection"})
    assert created.status_code == 201
    project = created.json()
    studio = client.app.state.studio
    preflight = client.post(
        f"/api/v1/projects/{project['projectId']}/preflights",
        json={"revision": project["revision"]},
    ).json()
    assert preflight["status"] == "ready"
    snapshot_id = preflight["snapshotId"]
    snapshot_file = studio.store.root / "snapshots" / snapshot_id / "snapshot.json"
    immutable_bytes = snapshot_file.read_bytes()
    immutable_record = canonical(studio.store.get("snapshot", snapshot_id))
    write = run_module.atomic
    injected = []

    def corrupt_delegated_copy(path, body):
        target = Path(path)
        if target.name == "request.json" and target.parent.parent == studio.store.root / "runs":
            request = json.loads(body)
            assert request["snapshot"]["snapshotId"] == snapshot_id
            assert request["snapshot"]["providerId"] == "studio.reference"
            if fault == "configuration":
                request["configuration"]["gain"] += 0.125
            elif fault == "plan_digest":
                request["snapshot"]["planDigest"] = "sha256:" + "f" * 64
            else:
                request["snapshot"]["providerIdentity"]["limits"]["maxPausedWallSeconds"] = 1
            injected.append(request["runId"])
            return write(path, canonical(request).encode())
        return write(path, body)

    monkeypatch.setattr(run_module, "atomic", corrupt_delegated_copy)
    payload = {"snapshotId": snapshot_id, "preflightId": preflight["preflightId"]}
    accepted = client.post(
        "/api/v1/runs",
        headers={"Idempotency-Key": "owned-startup-rejection-" + fault},
        json=payload,
    )
    assert accepted.status_code == 202
    result = accepted.json()
    run_id = result["runId"]
    worker = studio.runs.children[run_id]
    assert worker.wait(timeout=20) == 2
    assert injected == [run_id]
    directory = studio.runs.directory(run_id)
    state = json.loads((directory / "state.json").read_text())
    known = studio.store.get("run", run_id)
    assert known["launchArgvDigest"] == digest(
        [sys.executable, "-I", "-m", "xverse_studio.providers.worker", str(directory)]
    )
    response = client.get("/api/v1/runs/" + run_id)
    assert response.status_code == 200
    observed = response.json()
    deadline = time.monotonic() + 8
    while observed["state"] == "preparing" and time.monotonic() < deadline:
        time.sleep(0.05)
        observed = client.get("/api/v1/runs/" + run_id).json()
    assert observed["state"] == "failed", observed
    assert observed["reason"] == "EFFECTIVE_INPUT_MISMATCH"
    assert observed["cleanup"] == "complete"
    assert observed["evidence"] == "unavailable" and observed["verdict"] is None
    assert state["pid"] == worker.pid == known["pid"]
    assert state["createTime"] == known["createTime"]
    assert state["ownerDigest"] == digest((directory / "owner.key").read_bytes())
    assert "startedAt" not in state and "effectivePlanDigest" not in state
    assert not (directory / "evidence.jsonl").exists()
    assert not (directory / "command.json").exists()
    assert client.post(
        "/api/v1/runs",
        headers={"Idempotency-Key": "owned-startup-rejection-" + fault},
        json=payload,
    ).json() == result
    assert run_id not in studio.runs.children
    assert len(studio.store.all("run")) == len(injected) == 1
    assert snapshot_file.read_bytes() == immutable_bytes
    assert canonical(studio.store.get("snapshot", snapshot_id)) == immutable_record
    assert studio.projects.read(project["projectId"]) == project
    assert hashlib.sha256(immutable_bytes).hexdigest() == hashlib.sha256(snapshot_file.read_bytes()).hexdigest()
