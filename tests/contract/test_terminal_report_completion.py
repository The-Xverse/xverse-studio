"""Real owned BackendTask reporter with controlled metadata; no workload/device admission."""

from contextlib import contextmanager
import json
import threading

import pytest

from test_run_observation_corruption import controlled_run
from xverse_studio.providers.backend_task import BackendTask
from xverse_studio.runs import service
from xverse_studio.storage.core import atomic, canonical


@contextmanager
def reporter(client, status):
    run, path = controlled_run(client)
    published, finish = threading.Event(), threading.Event()

    def target(task_id):
        partial = {**run, "state": "stopped", "stateVersion": 2, "cleanup": "in_progress",
                   "evidence": "collecting", "commandResults": {}}
        assert partial["ownerTaskId"] == task_id
        atomic(path, canonical(partial).encode())
        published.set()
        if not finish.wait(20):
            raise TimeoutError("Owned reporter finalization was not released")
        result = {"status": status}
        if status == "failed":
            result["code"] = "CONTROL_CALLBACK_FAILED"
        atomic(path, canonical({**partial, "cleanup": "complete", "evidence": "unavailable",
                                "commandResults": {run["pendingCommandId"]: result}}).encode())
        return 0

    task = BackendTask(target)
    run.update(executionKind="backend-task", ownerTaskId=task.task_id, pid=task.pid, createTime=task.create_time)
    client.app.state.studio.store.put("run", run["runId"], run)
    client.app.state.studio.runs.children[run["runId"]] = task
    task.start()
    try:
        assert published.wait(5) and task.poll() is None
        yield run, path, task, finish
    finally:
        finish.set()
        assert task.wait(5) == 0


@pytest.mark.parametrize("status", ["completed", "failed", "accepted", "delegated"])
def test_terminal_lifecycle_does_not_finish_a_live_original_task_command(client, monkeypatch, status):
    with reporter(client, status) as (run, path, task, finish):
        original = path.read_bytes()
        observed = client.get("/api/v1/runs/" + run["runId"])
        assert observed.status_code == 200 and observed.json()["state"] == "stopped", observed.text
        assert observed.json()["cleanup"] == "in_progress"
        operation = client.get("/api/v1/operations/" + run["pendingCommandId"]).json()
        assert operation["status"] == "delegated" and "code" not in operation
        assert task.poll() is None and path.read_bytes() == original
        assert client.app.state.studio.runs.children[run["runId"]] is task
        finish.set()
        assert task.wait(5) == 0
        operation = client.get("/api/v1/operations/" + run["pendingCommandId"]).json()
        assert operation["status"] == ("unknown" if status in ("accepted", "delegated") else status)
        if status == "failed":
            assert operation["code"] == "CONTROL_CALLBACK_FAILED"
        else:
            assert "code" not in operation
        assert client.get("/api/v1/runs/" + run["runId"]).json()["cleanup"] == "complete"
        assert len(client.app.state.studio.store.all("operation")) == 2
        if status in ("accepted", "delegated"):
            store = client.app.state.studio.store
            original_put = store.put
            writes = []

            def counted_put(kind, identity, body, db=None):
                if kind == "operation":
                    writes.append(identity)
                return original_put(kind, identity, body, db)

            monkeypatch.setattr(store, "put", counted_put)
            for _ in range(3):
                assert client.get("/api/v1/operations/" + run["pendingCommandId"]).json()["status"] == "unknown"
            assert writes == []


def test_finished_original_task_reacquires_final_receipt_after_a_stale_terminal_read(client, monkeypatch):
    with reporter(client, "completed") as (run, path, task, finish):
        stale = path.read_text()
        finish.set()
        assert task.wait(5) == 0
        final = path.read_bytes()
        assert json.loads(final)["commandResults"][run["pendingCommandId"]]["status"] == "completed"
        # Delay captured bytes after the real anchored read, without replacing
        # containment checks or the report decoder/identity validation.
        original_read = service.read_bounded
        reads = []

        def delayed_snapshot(root, candidate, maximum):
            captured = original_read(root, candidate, maximum)
            if candidate == path:
                reads.append(candidate)
                if len(reads) == 1:
                    return stale.encode()
            return captured

        monkeypatch.setattr(service, "read_bounded", delayed_snapshot)
        response = client.get("/api/v1/runs/" + run["runId"])
        assert response.status_code == 200 and response.json()["state"] == "stopped", response.text
        # Inspect the receipt immediately: another GET must not be needed to repair a false failure.
        operation = client.app.state.studio.store.get("operation", run["pendingCommandId"])
        assert operation["status"] == "completed" and "code" not in operation
        assert len(reads) >= 2 and path.read_bytes() == final


@pytest.mark.parametrize("fault", ["older-version", "changed-terminal"])
def test_final_reacquisition_cannot_settle_from_a_regressed_report(client, monkeypatch, fault):
    with reporter(client, "completed") as (run, path, task, finish):
        first = path.read_text()
        finish.set()
        assert task.wait(5) == 0
        final = json.loads(path.read_text())
        final.update(stateVersion=1 if fault == "older-version" else 3,
                     state="stopped" if fault == "older-version" else "failed")
        atomic(path, canonical(final).encode())
        original_bytes = path.read_bytes()
        original_read = service.read_bounded
        reads = []

        def delayed_snapshot(root, candidate, maximum):
            captured = original_read(root, candidate, maximum)
            if candidate == path:
                reads.append(candidate)
                if len(reads) == 1:
                    return first.encode()
            return captured

        monkeypatch.setattr(service, "read_bounded", delayed_snapshot)
        response = client.get("/api/v1/runs/" + run["runId"])
        assert response.status_code == 200, response.text
        assert response.json()["state"] == "stopped" and response.json()["stateVersion"] == 2
        operation = client.app.state.studio.store.get("operation", run["pendingCommandId"])
        assert operation["status"] == "unknown" and "code" not in operation
        assert len(reads) >= 2 and path.read_bytes() == original_bytes
