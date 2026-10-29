"""Process-identity failure injection; never inspect or signal a real PID."""

import psutil
import pytest
import json
from pathlib import Path

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


@pytest.mark.parametrize(
    "fault",
    [
        "owner_missing",
        "owner_changed",
        "pid_missing",
        "pid_changed",
        "birth_missing",
        "birth_changed",
        "still_running",
        "malformed",
        "wrong_shape",
        "disappeared",
        "denied",
        "reused_birth",
    ],
)
def test_terminal_reacquisition_never_upgrades_missing_or_conflicting_identity(
    tmp_path, monkeypatch, fault
):
    """Labelled file/process observations only; no real PID is inspected or signalled."""
    from xverse_studio.runs import service as run_module

    store = Store(tmp_path)
    adapter = XDLAdapter()
    runs = Runs(store, Projects(store, adapter), adapter)
    run = {
        "runId": "run-terminal-identity",
        "operationId": "op-terminal-identity",
        "state": "running",
        "stateVersion": 1,
        "cleanup": "not_started",
        "evidence": "collecting",
        "ownerDigest": "fixture-owner",
        "pid": 12345,
        "createTime": 123.0,
        "createdAt": 0,
        "capabilities": [],
    }
    store.put("run", run["runId"], run)
    store.put(
        "operation",
        run["operationId"],
        {
            "operationId": run["operationId"],
            "status": "delegated",
        },
    )
    statepath = runs.directory(run["runId"]) / "state.json"
    atomic(statepath, canonical(run).encode())
    terminal = {
        **run,
        "state": "stopped",
        "cleanup": "complete",
        "evidence": "complete",
    }
    for prefix, field, changed in (
        ("owner", "ownerDigest", "another-owner"),
        ("pid", "pid", 54321),
        ("birth", "createTime", 124.0),
    ):
        if fault == prefix + "_missing":
            terminal.pop(field)
        if fault == prefix + "_changed":
            terminal[field] = changed
    if fault == "still_running":
        terminal["state"] = "running"
    replacement = (
        "{invalid"
        if fault == "malformed"
        else "[]"
        if fault == "wrong_shape"
        else canonical(terminal)
    )
    original = Path.read_text
    reads, contacts = [], []

    def state_read(path, *args, **kwargs):
        if path == statepath:
            reads.append(path)
            if len(reads) > 1:
                if fault == "disappeared":
                    raise FileNotFoundError(path)
                return replacement
        return original(path, *args, **kwargs)

    class ReusedProcess:
        def create_time(self):
            return 124.0

    def process_observation(pid):
        contacts.append(pid)
        assert pid == 12345
        if fault == "denied":
            raise psutil.AccessDenied(pid)
        if fault == "reused_birth":
            return ReusedProcess()
        raise psutil.NoSuchProcess(pid)

    def forbid_spawn(*args, **kwargs):
        pytest.fail("Terminal observation cannot authorize process creation")

    monkeypatch.setattr(Path, "read_text", state_read)
    monkeypatch.setattr(run_module.psutil, "Process", process_observation)
    monkeypatch.setattr(run_module.subprocess, "Popen", forbid_spawn)
    result = runs.read(run["runId"])
    assert contacts == [12345]
    assert len(reads) == (1 if fault in ("denied", "reused_birth") else 2)
    assert result["state"] == "unknown" and result["cleanup"] == "unknown"
    assert result["reason"] == "OWNERSHIP_UNKNOWN"
    assert store.get("operation", run["operationId"])["status"] == "unknown"
    assert not (statepath.parent / "command.json").exists()
    assert runs.children == {}
