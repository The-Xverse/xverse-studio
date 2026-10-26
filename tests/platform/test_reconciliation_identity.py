"""Process-identity failure injection; never inspect or signal a real PID."""

import psutil
import pytest

from xverse_studio.projects.service import Projects
from xverse_studio.runs.service import Runs
from xverse_studio.storage.core import Store, atomic, canonical
from xverse_studio.xdl import XDLAdapter


@pytest.mark.parametrize("observation", ["reused_birth", "missing", "denied"])
def test_restart_rejects_current_identity_loss_and_shutdown_never_delegates(
    tmp_path, monkeypatch, observation
):
    from xverse_studio.runs import service as run_module

    store = Store(tmp_path)
    adapter = XDLAdapter()
    projects = Projects(store, adapter)
    runs = Runs(store, projects, adapter)
    run_id, operation_id = "run-identity-fixture", "op-identity-fixture"
    # Persisted run and worker state agree: only the current process differs.
    record = {
        "runId": run_id,
        "operationId": operation_id,
        "state": "reconciling",
        "stateVersion": 1,
        "cleanup": "in_progress",
        "evidence": "collecting",
        "ownerDigest": "fixture-owner",
        "pid": 12345,
        "createTime": 123.0,
        "createdAt": 0,
        "capabilities": ["cancel"],
    }
    store.put("run", run_id, record)
    store.put(
        "operation", operation_id, {"operationId": operation_id, "status": "delegated"}
    )
    atomic(
        runs.directory(run_id) / "state.json",
        canonical({**record, "state": "running"}).encode(),
    )
    contacts, delegated = [], []

    class ReusedProcess:
        def create_time(self):
            return 124.0

        def is_running(self):
            return True

        def status(self):
            return psutil.STATUS_RUNNING

    def current_process(pid):
        contacts.append(pid)
        assert pid == 12345
        if observation == "missing":
            raise psutil.NoSuchProcess(pid)
        if observation == "denied":
            raise psutil.AccessDenied(pid)
        return ReusedProcess()

    def forbid_spawn(*args, **kwargs):
        pytest.fail("Reconciliation must never respawn a run")

    monkeypatch.setattr(run_module.psutil, "Process", current_process)
    monkeypatch.setattr(run_module.subprocess, "Popen", forbid_spawn)
    monkeypatch.setattr(runs, "command", lambda *args, **kwargs: delegated.append(args))
    result = runs.read(run_id)
    assert contacts == [12345]
    assert result["state"] == "unknown" and result["cleanup"] == "unknown"
    assert result["reason"] == "OWNERSHIP_UNKNOWN"
    assert store.get("operation", operation_id)["status"] == "unknown"
    runs.shutdown()
    assert delegated == []
    assert not (runs.directory(run_id) / "command.json").exists()
