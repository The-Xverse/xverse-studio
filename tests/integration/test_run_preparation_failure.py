"""Accepted Start survives a private preparation I/O failure without launching.

The fault touches only this test's managed run directory. Canonical inputs and
durable request identities remain real; no provider response is substituted.
"""

from pathlib import Path
import time

import pytest

from test_advanced_api import prepared
from xverse_studio.storage.core import canonical


@pytest.mark.parametrize("boundary", ["directory", "owner.key", "request.json", "temporary_directory"])
def test_accepted_preparation_failure_settles_once_without_launch_or_input_changes(
    client, monkeypatch, boundary
):
    from xverse_studio.runs import service as module

    project, preflight = prepared(client)
    studio = client.app.state.studio
    snapshot = canonical(studio.store.get("snapshot", preflight["snapshotId"]))
    snapshot_file = studio.store.root / "snapshots" / preflight["snapshotId"] / "snapshot.json"
    snapshot_bytes = snapshot_file.read_bytes()
    payload = {"snapshotId": preflight["snapshotId"], "preflightId": preflight["preflightId"]}
    headers = {"Idempotency-Key": "owned-preparation-" + boundary}
    original_write, original_mkdir = module.atomic, Path.mkdir
    faults, launches, interleaved = [], [], []

    def denied_write(path, body):
        path = Path(path)
        if path.name == boundary and path.parent.parent == studio.store.root / "runs":
            faults.append(path.name)
            if boundary == "request.json":
                interleaved.append(studio.runs.read(path.parent.name))
            raise PermissionError("Labelled owned preparation denial")
        return original_write(path, body)

    def denied_directory(path, *args, **kwargs):
        if (boundary == "directory" and path.parent == studio.store.root / "runs" and path.name.startswith("run-")) or (boundary == "temporary_directory" and path.name == "tmp" and path.parent.parent == studio.store.root / "runs"):
            faults.append(boundary)
            raise PermissionError("Labelled owned preparation denial")
        return original_mkdir(path, *args, **kwargs)

    def no_launch(*args, **kwargs):
        launches.append(True)
        pytest.fail("Preparation failed before native launch was permitted")

    with monkeypatch.context() as fault:
        fault.setattr(module, "atomic", denied_write)
        if boundary in ("directory", "temporary_directory"):
            fault.setattr(Path, "mkdir", denied_directory)
        fault.setattr(module.subprocess, "Popen", no_launch)
        accepted = client.post("/api/v1/runs", headers=headers, json=payload)
        assert accepted.status_code == 202, accepted.text
        receipt = accepted.json()
        rid = receipt["runId"]
        assert faults == [boundary] and launches == []
        assert client.post("/api/v1/runs", headers=headers, json=payload).json() == receipt

    # Removing the transient fault does not replay an already accepted request.
    assert client.post("/api/v1/runs", headers=headers, json=payload).json() == receipt
    observed = client.get("/api/v1/runs/" + rid).json()
    assert observed["state"] == "failed" and observed["reason"] == "PREPARATION_FAILED"
    assert observed["cleanup"] == "complete" and observed["evidence"] == "unavailable"
    assert observed["verdict"] is None
    if interleaved:
        assert observed["stateVersion"] == interleaved[0]["stateVersion"]
        assert observed["observationVersion"] > interleaved[0]["observationVersion"]
    assert not any(key in observed for key in ["startedAt", "effectivePlanDigest"])
    operation = client.get("/api/v1/operations/" + receipt["operationId"]).json()
    assert operation["status"] == "failed" and operation["code"] == "PREPARATION_FAILED"
    assert studio.runs.children == {}
    directory = studio.runs.directory(rid)
    assert not any((directory / name).exists() for name in ["state.json", "evidence.jsonl", "command.json"])
    assert len(studio.store.all("run")) == 1
    assert studio.projects.read(project["projectId"]) == project
    assert canonical(studio.store.get("snapshot", preflight["snapshotId"])) == snapshot
    assert snapshot_file.read_bytes() == snapshot_bytes
    diagnosed = client.get("/api/v1/runs/" + rid + "/diagnostics").json()
    assert any(f["code"] == "PREPARATION_FAILED" for f in diagnosed["findings"])
    assert "No execution took place" in str(diagnosed)
    # The failed run does not retain an active capacity reservation.
    fresh = client.post(
        f"/api/v1/projects/{project['projectId']}/preflights",
        json={"revision": project["revision"]},
    )
    assert fresh.status_code == 200 and fresh.json()["status"] == "ready"


def test_preparation_failure_outcome_is_atomic_when_metadata_write_fails(client, monkeypatch):
    from xverse_studio.runs import service as module

    _, preflight = prepared(client)
    studio = client.app.state.studio
    original_write, original_put = module.atomic, studio.store.put

    def denied_request(path, body):
        if Path(path).name == "request.json" and Path(path).parent.parent == studio.store.root / "runs":
            raise PermissionError("Labelled owned preparation denial")
        return original_write(path, body)

    def denied_outcome(kind, identity, body, db=None):
        if kind == "operation" and body.get("code") == "PREPARATION_FAILED":
            raise OSError("Labelled owned outcome persistence failure")
        return original_put(kind, identity, body, db)

    with monkeypatch.context() as fault:
        fault.setattr(module, "atomic", denied_request)
        fault.setattr(studio.store, "put", denied_outcome)
        with pytest.raises(OSError, match="outcome persistence failure"):
            client.post(
                "/api/v1/runs",
                headers={"Idempotency-Key": "owned-preparation-outcome-failure"},
                json={"snapshotId": preflight["snapshotId"], "preflightId": preflight["preflightId"]},
            )
    runs = studio.store.all("run")
    assert len(runs) == 1 and runs[0]["state"] == "requested"
    assert studio.store.get("operation", runs[0]["operationId"])["status"] == "accepted"
    assert "reason" not in runs[0] and studio.runs.children == {}


@pytest.mark.parametrize("boundary", ["before_launch", "after_native_launch"])
def test_dispatch_preserves_newer_read_observations_during_preparation_and_acknowledgement(
    client, monkeypatch, boundary
):
    from xverse_studio.runs import service as module

    project, _ = prepared(client)
    project = client.post(
        f"/api/v1/projects/{project['projectId']}/edits",
        headers={"If-Match": str(project["revision"])},
        json={"baseRevision": project["revision"], "edits": [
            {"kind": "set_parameter", "parameterId": "duration", "value": 3.0},
        ]},
    ).json()
    preflight = client.post(
        f"/api/v1/projects/{project['projectId']}/preflights",
        json={"revision": project["revision"]},
    ).json()
    assert preflight["status"] == "ready"
    studio = client.app.state.studio
    original_write, original_launch = module.atomic, module.subprocess.Popen
    observations, children = [], []

    def read_during_preparation(path, body):
        result = original_write(path, body)
        if Path(path).name == "request.json" and Path(path).parent.parent == studio.store.root / "runs":
            observations.append(studio.runs.read(Path(path).parent.name))
        return result

    def read_before_launch_acknowledgement(argv, *args, **kwargs):
        child = original_launch(argv, *args, **kwargs)
        children.append(child)
        if boundary == "after_native_launch":
            deadline = time.monotonic() + 20
            while time.monotonic() < deadline:
                observed = studio.runs.read(Path(argv[-1]).name)
                if observed["state"] == "running":
                    observations.append(observed)
                    break
                time.sleep(0.02)
            else:
                raise AssertionError("The original owned worker did not report running")
        return child

    with monkeypatch.context() as interleaving:
        if boundary == "before_launch":
            interleaving.setattr(module, "atomic", read_during_preparation)
        interleaving.setattr(module.subprocess, "Popen", read_before_launch_acknowledgement)
        response = client.post(
            "/api/v1/runs",
            headers={"Idempotency-Key": "owned-dispatch-interleaving-" + boundary},
            json={"snapshotId": preflight["snapshotId"], "preflightId": preflight["preflightId"]},
        )
        assert response.status_code == 202, response.text
    rid = response.json()["runId"]
    persisted = studio.store.get("run", rid)
    assert len(children) == len(observations) == 1
    assert persisted["observationVersion"] > observations[0]["observationVersion"]
    assert persisted["stateVersion"] >= observations[0]["stateVersion"]
    assert "reason" not in persisted
    if boundary == "after_native_launch":
        assert persisted["state"] == "running"
        assert persisted["startedAt"] == observations[0]["startedAt"]
        assert persisted["effectivePlanDigest"] == observations[0]["effectivePlanDigest"]
        assert studio.store.get("operation", persisted["operationId"])["status"] == "completed"
    assert children[0].wait(timeout=15) == 0
    ended = client.get("/api/v1/runs/" + rid).json()
    assert ended["state"] == "stopped" and ended["cleanup"] == "complete"
    assert ended["snapshotId"] == preflight["snapshotId"]
    assert len(studio.store.all("run")) == 1
    assert studio.projects.read(project["projectId"]) == project


@pytest.mark.parametrize("late_observation", ["exited", "denied"])
def test_late_parent_acknowledgement_preserves_confirmed_start_and_terminal_facts(
    client, monkeypatch, late_observation
):
    from xverse_studio.runs import service as module

    project, _ = prepared(client)
    edited = client.post(
        f"/api/v1/projects/{project['projectId']}/edits",
        headers={"If-Match": str(project["revision"])},
        json={"baseRevision": project["revision"], "edits": [
            {"kind": "set_parameter", "parameterId": "duration", "value": 5 if late_observation == "exited" else 10},
        ]},
    )
    assert edited.status_code == 200, edited.text
    project = edited.json()
    preflight = client.post(
        f"/api/v1/projects/{project['projectId']}/preflights",
        json={"revision": project["revision"]},
    ).json()
    assert preflight["status"] == "ready"
    studio = client.app.state.studio
    real_launch, real_psutil = module.subprocess.Popen, module.psutil
    witnessed, children = [], []
    denied = {"enabled": True, "calls": 0}

    class OwnedObservationDenied:
        def __getattr__(self, name):
            return getattr(real_psutil, name)

        def Process(self, pid=None, *args, **kwargs):
            if denied["enabled"] and children and pid == children[0].pid:
                denied["calls"] += 1
                raise real_psutil.AccessDenied(pid)
            return real_psutil.Process(pid, *args, **kwargs)

    with monkeypatch.context() as interleaving:
        def acknowledge_after_verified_read(argv, *args, **kwargs):
            child = real_launch(argv, *args, **kwargs)
            children.append(child)
            rid = Path(argv[-1]).name
            deadline = time.monotonic() + 20
            while time.monotonic() < deadline:
                run = studio.runs.read(rid)
                if run["state"] == "running":
                    break
                time.sleep(0.02)
            else:
                raise AssertionError("The original worker did not establish a verified running observation")
            process = real_psutil.Process(child.pid)
            assert process.cmdline() == argv and run["pid"] == child.pid
            assert process.create_time() == run["createTime"]
            assert studio.store.get("operation", run["operationId"])["status"] == "completed"
            if late_observation == "exited":
                assert child.wait(timeout=20) == 0
                run = studio.runs.read(rid)
                assert run["state"] == "stopped" and run["cleanup"] == "complete"
            else:
                interleaving.setattr(module, "psutil", OwnedObservationDenied())
            witnessed.append(run)
            return child

        interleaving.setattr(module.subprocess, "Popen", acknowledge_after_verified_read)
        accepted = client.post(
            "/api/v1/runs",
            headers={"Idempotency-Key": "late-native-parent-ack-" + late_observation},
            json={"snapshotId": preflight["snapshotId"], "preflightId": preflight["preflightId"]},
        )
        assert accepted.status_code == 202, accepted.text
        rid = accepted.json()["runId"]
        assert len(children) == len(witnessed) == 1
        stored = studio.store.get("run", rid)
        operation = studio.store.get("operation", stored["operationId"])
        assert operation["status"] == "completed", operation
        assert stored["stateVersion"] == witnessed[0]["stateVersion"]
        assert stored["startedAt"] == witnessed[0]["startedAt"]
        assert stored["effectivePlanDigest"] == witnessed[0]["effectivePlanDigest"]
        assert stored["pid"] == witnessed[0]["pid"] == children[0].pid
        assert stored["createTime"] == witnessed[0]["createTime"]
        if late_observation == "exited":
            assert stored["state"] == "stopped" and stored["cleanup"] == "complete"
            assert "reason" not in stored
        else:
            assert denied["calls"] > 0
            assert children[0].poll() is None
            assert stored["state"] == "unknown" and stored["cleanup"] == "unknown"
            refused = client.post(
                f"/api/v1/runs/{rid}/commands",
                headers={"Idempotency-Key": "denied-observation-no-control"},
                json={"kind": "pause", "expectedStateVersion": stored["stateVersion"]},
            )
            assert refused.status_code == 409 and refused.json()["code"] == "STATE_CONFLICT"
            assert not (studio.runs.directory(rid) / "command.json").exists()
        denied["enabled"] = False
    assert children[0].wait(timeout=20) == 0
    ended = client.get("/api/v1/runs/" + rid).json()
    assert ended["state"] == "stopped" and ended["cleanup"] == "complete"
    assert ended["verdict"] is None and len(studio.store.all("run")) == 1
    assert studio.projects.read(project["projectId"]) == project
