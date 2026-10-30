"""Controlled report corruption; no real PID, worker, device or native result implied."""

import json
import time

import pytest


def controlled_run(client):
    studio = client.app.state.studio
    run = {"runId": "run-corruption-fixture", "operationId": "op-corruption-start", "providerId": "studio.reference",
           "snapshotId": "snapshot-corruption-fixture", "state": "running", "stateVersion": 1,
           "cleanup": "not_started", "evidence": "collecting", "ownerDigest": "controlled-owner",
           "pid": 12345, "createTime": 123.0, "createdAt": 0, "capabilities": ["cancel"],
           "pendingCommandId": "op-corruption-pending", "evidenceScope": "owned_reference"}
    studio.store.put("run", run["runId"], run)
    studio.store.put("operation", run["operationId"], {"operationId": run["operationId"], "kind": "start",
                     "runId": run["runId"], "status": "delegated"})
    studio.store.put("operation", run["pendingCommandId"], {"operationId": run["pendingCommandId"], "kind": "stop",
                     "runId": run["runId"], "status": "delegated"})
    directory = studio.runs.directory(run["runId"])
    directory.mkdir(parents=True)
    return run, directory / "state.json"


def forbid_process_authority(monkeypatch):
    from xverse_studio.runs import service

    def forbidden(*args, **kwargs):
        pytest.fail("Malformed reports cannot authorize process lookup, launch or control")

    monkeypatch.setattr(service.psutil, "Process", forbidden)
    monkeypatch.setattr(service.subprocess, "Popen", forbidden)


@pytest.mark.parametrize("fault", ["root-list", "root-string", "root-number", "missing-state", "state-list", "unknown-state",
                                  "missing-version", "boolean-version", "string-birth", "cleanup-list", "evidence-object",
                                  "results-list", "result-string", "unknown-result-status", "cancelled-run-result", "deep-json", "nonfinite-result", "surrogate-result"])
def test_corrupt_report_stays_unknown_and_cannot_delegate(client, monkeypatch, fault):
    run, path = controlled_run(client)
    report = {**run, "state": "stopped", "cleanup": "complete", "evidence": "complete", "commandResults": {}}
    if fault.startswith("root-"):
        report = {"root-list": ["not a state"], "root-string": "not a state", "root-number": 42}[fault]
    elif fault == "missing-state":
        report.pop("state")
    elif fault in ("state-list", "unknown-state"):
        report["state"] = ["stopped"] if fault == "state-list" else "invented-state"
    elif fault == "missing-version":
        report.pop("stateVersion")
    elif fault == "boolean-version":
        report["stateVersion"] = True
    elif fault == "string-birth":
        report["createTime"] = "123.0"
    elif fault == "cleanup-list":
        report["cleanup"] = ["complete"]
    elif fault == "evidence-object":
        report["evidence"] = {"status": "complete"}
    elif fault == "results-list":
        report["commandResults"] = []
    elif fault in ("result-string", "unknown-result-status"):
        report["commandResults"] = {run["pendingCommandId"]: "completed" if fault == "result-string" else {"status": "invented"}}
    elif fault == "cancelled-run-result":
        report["commandResults"] = {run["pendingCommandId"]: {"status": "cancelled"}}
    elif fault in ("nonfinite-result", "surrogate-result"):
        report["commandResults"] = {run["pendingCommandId"]: {"status": "completed",
                                   "result": {"value": float("nan") if fault == "nonfinite-result" else "\ud800"}}}
    raw = ("[" * 10000 + "0" + "]" * 10000) if fault == "deep-json" else json.dumps(report)
    path.write_text(raw)
    forbid_process_authority(monkeypatch)
    try:
        response = client.get("/api/v1/runs/" + run["runId"])
        assert response.status_code == 200, response.text
        observed = response.json()
        assert observed["state"] == observed["cleanup"] == "unknown" and observed["evidence"] == "partial"
        assert observed["reason"] == "OWNERSHIP_UNKNOWN"
        for operation_id in (run["operationId"], run["pendingCommandId"]):
            operation = client.get("/api/v1/operations/" + operation_id)
            assert operation.status_code == 200 and operation.json()["status"] == "unknown"
        refused = client.post(f"/api/v1/runs/{run['runId']}/commands", headers={"Idempotency-Key": "corrupt-no-authority"},
                              json={"kind": "cancel", "expectedStateVersion": observed["stateVersion"]})
        assert refused.status_code == 409 and refused.json()["code"] == "STATE_CONFLICT"
        assert len(client.app.state.studio.store.all("operation")) == 2
        assert not path.with_name("command.json").exists() and client.app.state.studio.runs.children == {}
        assert path.read_text() == raw
    finally:
        # Only this controlled fixture is removed; no provider process or real report exists.
        path.unlink(missing_ok=True)


def test_corrupt_new_report_preserves_already_terminal_receipts(client, monkeypatch):
    run, path = controlled_run(client)
    store = client.app.state.studio.store
    run.update(state="stopped", cleanup="complete", evidence="unavailable")
    run.pop("pendingCommandId")
    store.put("run", run["runId"], run)
    for operation in store.all("operation"):
        operation["status"] = "completed"
        store.put("operation", operation["operationId"], operation)
    before = store.all("operation")
    path.write_text('["corrupt newer report"]')
    forbid_process_authority(monkeypatch)
    try:
        response = client.get("/api/v1/runs/" + run["runId"])
        assert response.status_code == 200, response.text
        assert response.json()["state"] == "stopped" and response.json()["cleanup"] == "complete"
        assert store.all("operation") == before and path.read_text() == '["corrupt newer report"]'
    finally:
        path.unlink(missing_ok=True)


@pytest.mark.parametrize("fault", ["foreign-operation", "start-result", "changed-run-id", "changed-kind", "changed-parameters"])
def test_report_results_cannot_rebind_or_modify_other_receipts(client, monkeypatch, fault):
    run, path = controlled_run(client)
    store = client.app.state.studio.store
    foreign = {"operationId": "op-another-run", "runId": "run-another-owner", "kind": "stop", "status": "delegated"}
    store.put("operation", foreign["operationId"], foreign)
    operation_id = foreign["operationId"] if fault == "foreign-operation" else run["operationId"] if fault == "start-result" else run["pendingCommandId"]
    result = {"status": "completed"}
    if fault == "changed-run-id":
        result["runId"] = "run-another-owner"
    elif fault == "changed-kind":
        result["kind"] = "start"
    elif fault == "changed-parameters":
        pending = store.get("operation", run["pendingCommandId"])
        pending["parameters"] = {"value": 1}
        store.put("operation", pending["operationId"], pending)
        result["parameters"] = {"value": True}  # Python equality is not JSON fingerprint equality.
    raw = json.dumps({**run, "state": "stopped", "cleanup": "complete", "evidence": "complete",
                      "commandResults": {operation_id: result}})
    path.write_text(raw)
    forbid_process_authority(monkeypatch)
    try:
        response = client.get("/api/v1/runs/" + run["runId"])
        assert response.status_code == 200 and response.json()["state"] == "unknown", response.text
        assert store.get("operation", foreign["operationId"]) == foreign
        for operation_id in (run["operationId"], run["pendingCommandId"]):
            operation = store.get("operation", operation_id)
            assert operation["runId"] == run["runId"] and operation["status"] == "unknown"
        assert store.get("operation", run["pendingCommandId"])["kind"] == "stop"
        assert path.read_text() == raw and not path.with_name("command.json").exists()
    finally:
        path.unlink(missing_ok=True)


@pytest.mark.parametrize("status", ["completed", "rejected"])
def test_valid_terminal_report_keeps_opaque_fields_and_reconciles_original_command(client, monkeypatch, status):
    run, path = controlled_run(client)
    report = {**run, "state": "stopped", "cleanup": "complete", "evidence": "unavailable",
              "commandResults": {run["pendingCommandId"]: {"status": status, "providerOpaque": {"kept": 42}},
                                 "provider-only-receipt": {"status": "provider-maintenance-finished", "providerOpaque": {"separate": True}}},
              "opaqueExtension": {"unknown": [1, 2, 3]}}
    raw = json.dumps(report)
    path.write_text(raw)
    forbid_process_authority(monkeypatch)
    try:
        response = client.get("/api/v1/runs/" + run["runId"])
        assert response.status_code == 200 and response.json()["state"] == "stopped", response.text
        operation = client.get("/api/v1/operations/" + run["pendingCommandId"]).json()
        assert operation["status"] == status and operation["providerOpaque"] == {"kept": 42}
        assert len(client.app.state.studio.store.all("operation")) == 2
        assert path.read_text() == raw and "opaqueExtension" not in response.json()
    finally:
        path.unlink(missing_ok=True)


def test_invalid_report_does_not_settle_a_pending_command_on_a_known_terminal_run(client, monkeypatch):
    run, path = controlled_run(client)
    store = client.app.state.studio.store
    run.update(state="stopped", cleanup="complete", evidence="unavailable")
    store.put("run", run["runId"], run)
    start = store.get("operation", run["operationId"])
    start["status"] = "completed"
    store.put("operation", start["operationId"], start)
    path.write_text('["corrupt newer report"]')
    forbid_process_authority(monkeypatch)
    try:
        response = client.get("/api/v1/runs/" + run["runId"])
        assert response.status_code == 200 and response.json()["state"] == "stopped", response.text
        assert response.json()["cleanup"] == "complete"
        assert store.get("operation", start["operationId"]) == start
        assert store.get("operation", run["pendingCommandId"])["status"] == "unknown"
        assert not path.with_name("command.json").exists()
    finally:
        path.unlink(missing_ok=True)


@pytest.mark.parametrize("fault", ["malformed", "wrong-owner"])
def test_present_invalid_report_cannot_use_the_initial_startup_grace(client, monkeypatch, fault):
    run, path = controlled_run(client)
    store = client.app.state.studio.store
    run.update(state="preparing", createdAt=time.time(), launchStartedAt=time.time())
    store.put("run", run["runId"], run)
    report = ["malformed report"] if fault == "malformed" else {**run, "ownerDigest": "another-owner"}
    raw = json.dumps(report)
    path.write_text(raw)
    forbid_process_authority(monkeypatch)
    try:
        response = client.get("/api/v1/runs/" + run["runId"])
        assert response.status_code == 200 and response.json()["state"] == "unknown", response.text
        refused = client.post(f"/api/v1/runs/{run['runId']}/commands", headers={"Idempotency-Key": "invalid-startup-report"},
                              json={"kind": "cancel", "expectedStateVersion": run["stateVersion"]})
        assert refused.status_code == 409 and len(store.all("operation")) == 2
        assert not path.with_name("command.json").exists() and path.read_text() == raw
    finally:
        path.unlink(missing_ok=True)


@pytest.mark.parametrize("known_state,reported_version", [("paused", 1), ("stopped", 1), ("stopped", 2)],
                         ids=["paused", "stopped", "stopped-same-version"])
def test_stale_report_cannot_roll_back_verified_state_or_command_authority(client, monkeypatch, known_state, reported_version):
    run, path = controlled_run(client)
    store = client.app.state.studio.store
    run.update(state=known_state, stateVersion=2)
    if known_state == "stopped":
        run.update(cleanup="complete", evidence="unavailable")
        start = store.get("operation", run["operationId"])
        start["status"] = "completed"
        store.put("operation", start["operationId"], start)
    store.put("run", run["runId"], run)
    raw = json.dumps({**run, "state": "running", "stateVersion": reported_version, "cleanup": "not_started", "commandResults": {}})
    path.write_text(raw)
    forbid_process_authority(monkeypatch)
    try:
        response = client.get("/api/v1/runs/" + run["runId"])
        assert response.status_code == 200, response.text
        assert response.json()["stateVersion"] == 2
        assert response.json()["state"] == ("stopped" if known_state == "stopped" else "unknown")
        assert store.get("operation", run["pendingCommandId"])["status"] == "unknown"
        if known_state == "stopped":
            assert store.get("operation", run["operationId"])["status"] == "completed"
        assert path.read_text() == raw and not path.with_name("command.json").exists()
    finally:
        path.unlink(missing_ok=True)


@pytest.mark.parametrize("progress", ["accepted", "delegated"])
def test_provider_progress_cannot_erase_an_already_completed_receipt(client, monkeypatch, progress):
    run, path = controlled_run(client)
    store = client.app.state.studio.store
    command_id = run.pop("pendingCommandId")
    run.update(state="stopped", cleanup="complete", evidence="unavailable")
    store.put("run", run["runId"], run)
    for operation in store.all("operation"):
        operation["status"] = "completed"
        if operation["operationId"] == command_id:
            operation["result"] = {"original": 42}
        store.put("operation", operation["operationId"], operation)
    original = store.get("operation", command_id)
    raw = json.dumps({**run, "commandResults": {command_id: {"status": progress, "result": {"replace": "forbidden"}}}})
    path.write_text(raw)
    forbid_process_authority(monkeypatch)
    try:
        response = client.get("/api/v1/runs/" + run["runId"])
        assert response.status_code == 200 and response.json()["state"] == "stopped", response.text
        assert client.get("/api/v1/operations/" + command_id).json() == original
        assert path.read_text() == raw
    finally:
        path.unlink(missing_ok=True)


def test_native_exit_reacquisition_cannot_lower_the_verified_version(client, monkeypatch):
    """Controlled NoSuchProcess boundary; no actual process is inspected or controlled."""
    from pathlib import Path
    from xverse_studio.runs import service

    run, path = controlled_run(client)
    run["stateVersion"] = 5
    client.app.state.studio.store.put("run", run["runId"], run)
    first = json.dumps({**run, "commandResults": {}})
    raw = json.dumps({**run, "state": "stopped", "stateVersion": 4, "cleanup": "complete",
                      "commandResults": {run["pendingCommandId"]: {"status": "completed"}}})
    path.write_text(raw)
    original_read = Path.read_text
    reads = []

    def delayed_snapshot(candidate, *args, **kwargs):
        if candidate == path:
            reads.append(candidate)
            if len(reads) == 1:
                return first
        return original_read(candidate, *args, **kwargs)

    def exited(pid):
        assert pid == run["pid"]
        raise service.psutil.NoSuchProcess(pid)

    monkeypatch.setattr(Path, "read_text", delayed_snapshot)
    monkeypatch.setattr(service.psutil, "Process", exited)
    try:
        response = client.get("/api/v1/runs/" + run["runId"])
        assert response.status_code == 200, response.text
        assert response.json()["state"] == "unknown" and response.json()["stateVersion"] == 5
        operation = client.app.state.studio.store.get("operation", run["pendingCommandId"])
        assert operation["status"] == "unknown" and len(reads) >= 2
        assert path.read_text() == raw
    finally:
        path.unlink(missing_ok=True)
