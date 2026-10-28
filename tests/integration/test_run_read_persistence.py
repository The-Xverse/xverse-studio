"""Owned reference reads retain new facts without rewriting unchanged records."""

from copy import deepcopy
import hashlib
import json
import time

import pytest

from test_advanced_api import prepared, start, wait_run


def terminal_run(client, *, cancel=False):
    project, preflight = prepared(client)
    if cancel:
        response = client.post(
            f"/api/v1/projects/{project['projectId']}/edits",
            headers={"If-Match": str(project["revision"])},
            json={
                "baseRevision": project["revision"],
                "edits": [
                    {"kind": "set_parameter", "parameterId": "duration", "value": 10.0}
                ],
            },
        )
        assert response.status_code == 200, response.text
        response = client.post(
            f"/api/v1/projects/{project['projectId']}/preflights",
            json={"revision": response.json()["revision"]},
        )
        assert response.status_code == 200 and response.json()["status"] == "ready"
        preflight = response.json()
    rid = start(client, preflight)
    command = None
    if cancel:
        deadline = time.monotonic() + 20
        while time.monotonic() < deadline:
            run = client.get("/api/v1/runs/" + rid).json()
            if run["state"] == "running":
                break
            assert run["state"] not in {"failed", "unknown", "stopped"}
            time.sleep(0.02)
        assert run["state"] == "running"
        response = client.post(
            f"/api/v1/runs/{rid}/commands",
            headers={"Idempotency-Key": "owned-read-cancel"},
            json={"kind": "cancel", "expectedStateVersion": run["stateVersion"]},
        )
        assert response.status_code == 202, response.text
        command = response.json()["operationId"]
    ended = wait_run(client, rid)
    assert ended["state"] == "stopped", ended
    manager = client.app.state.studio.runs
    child = manager.children.get(rid)
    if child is not None:
        child.wait(timeout=10)
    baseline = client.get("/api/v1/runs/" + rid).json()
    if command:
        observed = json.loads((manager.directory(rid) / "state.json").read_text())
        assert observed["commandResults"][command]["status"] == "completed"
    return rid, baseline


def sql_writes(client, monkeypatch):
    store = client.app.state.studio.store
    original = store.put
    writes = []

    def observed(kind, identity, body, db=None):
        if db is not None and kind in {"operation", "run"}:
            writes.append((kind, identity, deepcopy(body)))
        return original(kind, identity, body, db)

    monkeypatch.setattr(store, "put", observed)
    return writes


@pytest.mark.parametrize("cancel", [False, True])
def test_repeated_terminal_reads_do_not_rewrite_unchanged_run_or_operations(
    client, monkeypatch, cancel
):
    rid, baseline = terminal_run(client, cancel=cancel)
    root = client.app.state.studio.runs.directory(rid)
    hashes = {
        p: hashlib.sha256(p.read_bytes()).hexdigest()
        for p in root.rglob("*")
        if p.is_file()
    }
    writes = sql_writes(client, monkeypatch)
    for _ in range(3):
        response = client.get("/api/v1/runs/" + rid)
        assert response.status_code == 200 and response.json() == baseline
        response = client.get("/api/v1/runs", params={"limit": 1})
        assert response.status_code == 200 and response.json()["items"] == [baseline]
    assert writes == [], (
        "An unchanged observation must not rewrite run/start/command records."
    )
    assert all(
        hashlib.sha256(p.read_bytes()).hexdigest() == value
        for p, value in hashes.items()
    )


def test_new_terminal_cleanup_observation_still_persists_once(client, monkeypatch):
    rid, baseline = terminal_run(client)
    studio = client.app.state.studio
    state = studio.runs.directory(rid) / "state.json"
    original = state.read_bytes()
    observed = json.loads(original)
    # Controlled late worker observation on an owned, already exited fixture.
    observed.update(
        cleanup="unknown",
        reason="owned_late_cleanup_observation",
        stateVersion=baseline["stateVersion"] + 1,
    )
    writes = sql_writes(client, monkeypatch)
    try:
        state.write_text(json.dumps(observed))
        response = client.get("/api/v1/runs/" + rid)
        assert response.status_code == 200
        current = response.json()
        assert current["state"] == "stopped" and current["cleanup"] == "unknown"
        assert current["stateVersion"] == observed["stateVersion"]
        assert current["reason"] == "owned_late_cleanup_observation"
        saved = studio.store.get("run", rid)
        assert (
            saved["cleanup"] == "unknown"
            and saved["stateVersion"] == observed["stateVersion"]
        )
        assert [(kind, identity) for kind, identity, _ in writes] == [("run", rid)]
        writes.clear()
        assert client.get("/api/v1/runs/" + rid).json() == current
        assert writes == []
    finally:
        state.write_bytes(original)


def test_unchanged_worker_state_does_not_hide_new_journal_corruption(
    client, monkeypatch
):
    rid, baseline = terminal_run(client)
    studio = client.app.state.studio
    journal = studio.runs.directory(rid) / "evidence.jsonl"
    original = journal.read_bytes()
    writes = sql_writes(client, monkeypatch)
    try:
        journal.write_bytes(original + b'{"owned_invalid_journal_fixture":true}\n')
        response = client.get("/api/v1/runs/" + rid)
        assert response.status_code == 200
        current = response.json()
        assert (
            current["state"] == baseline["state"] and current["evidence"] == "invalid"
        )
        assert studio.store.get("run", rid)["evidence"] == "invalid"
        assert [(kind, identity) for kind, identity, _ in writes] == [("run", rid)]
        writes.clear()
        assert client.get("/api/v1/runs/" + rid).json() == current
        assert writes == []
    finally:
        journal.write_bytes(original)


def test_changed_observation_cannot_report_success_when_persistence_fails(
    client, monkeypatch
):
    rid, baseline = terminal_run(client)
    studio = client.app.state.studio
    state = studio.runs.directory(rid) / "state.json"
    original = state.read_bytes()
    observed = json.loads(original)
    observed.update(cleanup="unknown", stateVersion=baseline["stateVersion"] + 1)
    put = studio.store.put

    def unavailable(kind, identity, body, db=None):
        if kind == "run" and identity == rid and body.get("cleanup") == "unknown":
            raise OSError("owned changed-observation persistence unavailable")
        return put(kind, identity, body, db)

    monkeypatch.setattr(studio.store, "put", unavailable)
    try:
        state.write_text(json.dumps(observed))
        with pytest.raises(
            OSError, match="owned changed-observation persistence unavailable"
        ):
            client.get("/api/v1/runs/" + rid)
        saved = studio.store.get("run", rid)
        assert saved["cleanup"] == baseline["cleanup"]
        assert saved["stateVersion"] == baseline["stateVersion"]
    finally:
        state.write_bytes(original)
