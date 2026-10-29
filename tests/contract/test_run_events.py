import os
import time
import base64
import json


def stream_cursor(run_id, snapshot_id, sequence="0", record_digest="0" * 64):
    payload = json.dumps(
        {"r": run_id, "s": snapshot_id, "q": sequence, "d": record_digest},
        sort_keys=True,
        separators=(",", ":"),
    ).encode()
    return "st1." + base64.urlsafe_b64encode(payload).decode().rstrip("=")


def test_stream_cursor_grammar_rejects_coercion_and_wrong_context(tmp_path):
    from xverse_studio.events import EventStreams
    from xverse_studio.storage.core import Store, Problem
    import importlib.util
    from pathlib import Path

    path = Path(__file__).resolve().parents[1] / "fixtures/evidence/stream_fixtures.py"
    spec = importlib.util.spec_from_file_location("strict_stream_fixture", path)
    fixture = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(fixture)
    source = fixture.AdvancingJournal(tmp_path / "new-public-journal")
    source.append(2)
    streams = EventStreams(Store(tmp_path / "new-store"), source)
    invalid = [
        "+1",
        " 1 ",
        "01",
        "-1",
        "1.0",
        "other-run:1",
        "fixture-stream:extra:1",
        stream_cursor("other-run", source.snapshot_id),
        stream_cursor(source.run_id, "other-snapshot"),
        stream_cursor(source.run_id, source.snapshot_id, True),
        stream_cursor(source.run_id, source.snapshot_id, "01"),
        stream_cursor(source.run_id, source.snapshot_id, "0", "not-a-digest"),
        "st1.not-json",
        "st1." + base64.urlsafe_b64encode(b"[]").decode().rstrip("="),
        "st1."
        + base64.urlsafe_b64encode(
            b'{"r":"fixture-stream","r":"fixture-stream","s":"fixture-snapshot","q":"0","d":"'
            + b"0" * 64
            + b'"}'
        )
        .decode()
        .rstrip("="),
        "st1."
        + base64.urlsafe_b64encode(
            json.dumps(
                {
                    "r": source.run_id,
                    "s": source.snapshot_id,
                    "q": "0",
                    "d": "0" * 64,
                    "extra": "ignored",
                }
            ).encode()
        )
        .decode()
        .rstrip("="),
    ]
    for cursor in invalid:
        try:
            streams.prepare(source.run_id, cursor=cursor, version="1.1")
        except Problem as error:
            assert error.code == "CURSOR_INVALID", (cursor, error.code)
        else:
            raise AssertionError(f"Cursor must reject rather than coerce: {cursor!r}")


def test_stream_cursor_same_source_survives_manager_restart(tmp_path):
    from xverse_studio.events import EventStreams
    from xverse_studio.storage.core import Store
    import importlib.util
    from pathlib import Path

    path = Path(__file__).resolve().parents[1] / "fixtures/evidence/stream_fixtures.py"
    spec = importlib.util.spec_from_file_location("restart_stream_fixture", path)
    fixture = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(fixture)
    source = fixture.AdvancingJournal(tmp_path / "new-restart-journal")
    source.append(3)
    store = Store(tmp_path / "new-restart-store")
    cursor = stream_cursor(
        source.run_id, source.snapshot_id, "2", source.records[1]["digest"]
    )
    original = source.path.read_bytes()
    first = EventStreams(store, source).prepare(
        source.run_id, cursor=cursor, version="1.1"
    )
    second = EventStreams(store, source).prepare(
        source.run_id, cursor=cursor, version="1.1"
    )
    assert first == second
    assert source.path.read_bytes() == original


def test_completed_stream_reconnect_is_read_only(client):
    p = client.post("/api/v1/projects", json={"name": "events"}).json()
    p = client.post(
        f"/api/v1/projects/{p['projectId']}/edits",
        headers={"If-Match": str(p["revision"])},
        json={
            "baseRevision": p["revision"],
            "edits": [
                {"kind": "set_parameter", "parameterId": "duration", "value": 0.2}
            ],
        },
    ).json()
    pf = client.post(
        f"/api/v1/projects/{p['projectId']}/preflights",
        json={"revision": p["revision"]},
    ).json()
    r = client.post(
        "/api/v1/runs",
        headers={"Idempotency-Key": "events-once"},
        json={"snapshotId": pf["snapshotId"], "preflightId": pf["preflightId"]},
    ).json()
    rid = r["runId"]
    for _ in range(100):
        if client.get("/api/v1/runs/" + rid).json()["state"] == "stopped":
            break
        time.sleep(0.05)
    response = client.get(f"/api/v1/runs/{rid}/events")
    assert response.status_code == 200
    ids = [line[4:] for line in response.text.splitlines() if line.startswith("id: ")]
    assert len(ids) == len(set(ids)) and ids
    cursor = ids[1]
    replay = client.get(f"/api/v1/runs/{rid}/events", params={"after": cursor})
    remaining = [
        line[4:] for line in replay.text.splitlines() if line.startswith("id: ")
    ]
    assert remaining == ids[2:]
    assert client.get("/api/v1/runs").json()["items"][0]["runId"] == rid
    assert len(client.get("/api/v1/runs").json()["items"]) == 1
    assert (
        client.get(
            f"/api/v1/runs/{rid}/events",
            params={"after": cursor},
            headers={"Last-Event-ID": ids[0]},
        ).status_code
        == 422
    )


def _in_process_owned_run(client, monkeypatch, duration=0.5):
    """Admit a real owned run but execute its worker in this process, under test control."""
    from types import SimpleNamespace
    from xverse_studio.runs import service

    class Launched:
        pid = os.getpid()

        def __init__(self, argv, **kwargs):
            self.argv = argv

        def poll(self):
            return 0

    monkeypatch.setattr(service.subprocess, "Popen", Launched)
    p = client.post("/api/v1/projects", json={"name": "command outcomes"}).json()
    p = client.post(
        f"/api/v1/projects/{p['projectId']}/edits",
        headers={"If-Match": str(p["revision"])},
        json={
            "baseRevision": p["revision"],
            "edits": [
                {"kind": "set_parameter", "parameterId": "duration", "value": duration}
            ],
        },
    ).json()
    pf = client.post(
        f"/api/v1/projects/{p['projectId']}/preflights",
        json={"revision": p["revision"]},
    ).json()
    started = client.post(
        "/api/v1/runs",
        headers={"Idempotency-Key": "command-outcome-start"},
        json={"snapshotId": pf["snapshotId"], "preflightId": pf["preflightId"]},
    )
    assert pf["status"] == "ready" and started.status_code == 202, started.text
    started = started.json()
    root = client.app.state.studio.runs.directory(started["runId"])
    return started["runId"], root, SimpleNamespace


def _run_worker(monkeypatch, root, namespace, on_tick):
    from xverse_studio.providers import worker

    ticks = []

    def sleep(_):
        ticks.append(len(ticks))
        on_tick(len(ticks))

    # Every tick sleeps exactly once; the hook observes deterministic tick boundaries.
    monkeypatch.setattr(
        worker, "time", namespace(time=time.time, monotonic=lambda: 0.0, sleep=sleep)
    )
    monkeypatch.setattr(worker.sys, "argv", ["worker", str(root)])
    return worker.main(), ticks


def _journal(root):
    return [json.loads(line) for line in (root / "evidence.jsonl").read_bytes().splitlines()]


def _command(client, rid, key):
    run = client.get("/api/v1/runs/" + rid).json()
    assert run["state"] == "running", run
    response = client.post(
        f"/api/v1/runs/{rid}/commands",
        headers={"Idempotency-Key": key},
        json={"kind": "stop", "expectedStateVersion": run["stateVersion"]},
    )
    assert response.status_code == 202, response.text
    return response.json()


def test_accepted_command_after_final_tick_fails_canonically_without_execution(
    client, monkeypatch
):
    rid, root, namespace = _in_process_owned_run(client, monkeypatch)
    accepted = {}

    def on_tick(tick):
        if tick == 5:  # final 0.1s tick of a 0.5s run, after its last command check
            accepted.update(_command(client, rid, "late-stop"))

    code, ticks = _run_worker(monkeypatch, root, namespace, on_tick)
    assert code == 0 and len(ticks) == 5 and accepted["status"] == "accepted"
    run = client.get("/api/v1/runs/" + rid).json()
    operation = client.get("/api/v1/operations/" + accepted["operationId"]).json()
    assert run["state"] == "stopped" and run["evidence"] == "complete"
    assert operation["status"] == "failed"
    assert operation["code"] == "RUN_COMPLETED_BEFORE_COMMAND"
    records = _journal(root)
    failed = [r for r in records if r["type"] == "command.failed"]
    assert [r["payload"]["operationId"] for r in failed] == [accepted["operationId"]]
    assert failed[0]["payload"]["kind"] == "stop"
    assert not any(
        r["type"] in ("command.delegated", "command.completed") for r in records
    )
    stopped = [r for r in records if r["type"] == "run.state_changed"][-1]
    # Acceptance is not execution: the lifecycle outcome remains the natural completion.
    assert stopped["payload"]["reason"] == "duration_complete"
    history = client.get(f"/api/v1/runs/{rid}/history", params={"type": "command.failed"})
    assert history.json()["integrity"] == "valid"
    assert [i["eventId"] for i in history.json()["items"]] == [failed[0]["eventId"]]


def test_accepted_command_that_never_reaches_worker_reconciles_failed(
    client, monkeypatch
):
    rid, root, namespace = _in_process_owned_run(client, monkeypatch)
    accepted = {}

    def on_tick(tick):
        if tick == 2:
            accepted.update(_command(client, rid, "lost-delegation"))
            # Fault injection: the signed request is lost before the worker reads it.
            (root / "command.json").unlink()

    code, _ = _run_worker(monkeypatch, root, namespace, on_tick)
    assert code == 0
    run = client.get("/api/v1/runs/" + rid).json()
    operation = client.get("/api/v1/operations/" + accepted["operationId"]).json()
    assert run["state"] == "stopped" and "pendingCommandId" not in run
    assert operation["status"] == "failed"
    assert operation["code"] == "RUN_TERMINAL_BEFORE_COMMAND"
    # The sealed original journal is not rewritten to add a backend-side outcome.
    assert not any(r["type"].startswith("command.") for r in _journal(root))


def test_accepted_command_fails_when_owned_workload_fails_first(client, monkeypatch):
    rid, root, namespace = _in_process_owned_run(client, monkeypatch)
    accepted = {}

    def on_tick(tick):
        if tick == 2:
            accepted.update(_command(client, rid, "fail-before-stop"))
            raise RuntimeError("injected workload failure")

    code, _ = _run_worker(monkeypatch, root, namespace, on_tick)
    assert code == 1
    run = client.get("/api/v1/runs/" + rid).json()
    operation = client.get("/api/v1/operations/" + accepted["operationId"]).json()
    assert run["state"] == "failed" and run["cleanup"] == "unknown"
    assert operation["status"] == "failed"
    assert operation["code"] == "REFERENCE_WORKER_ERROR"
    failed = [r for r in _journal(root) if r["type"] == "command.failed"]
    assert [r["payload"]["code"] for r in failed] == ["REFERENCE_WORKER_ERROR"]


def test_pending_command_becomes_unknown_when_ownership_is_lost(client, monkeypatch):
    rid, root, namespace = _in_process_owned_run(client, monkeypatch)
    store = client.app.state.studio.store
    accepted = {}

    def on_tick(tick):
        if tick == 2:
            accepted.update(_command(client, rid, "ownership-lost"))
            # Fault injection: the recorded owner identity no longer matches the process.
            run = store.get("run", rid)
            run["createTime"] -= 60
            store.put("run", rid, run)

    _run_worker(monkeypatch, root, namespace, on_tick)
    run = client.get("/api/v1/runs/" + rid).json()
    operation = client.get("/api/v1/operations/" + accepted["operationId"]).json()
    assert run["state"] == "unknown" and run["reason"] == "OWNERSHIP_UNKNOWN"
    assert run["cleanup"] == "unknown"
    # Unknown is not failure: the command may have taken effect without proof.
    assert operation["status"] == "unknown"
    assert run["pendingCommandId"] == accepted["operationId"]


def test_delegation_never_reopens_a_concurrently_settled_command(client, monkeypatch):
    rid, root, namespace = _in_process_owned_run(client, monkeypatch)
    studio = client.app.state.studio
    actual = studio.store.idempotent
    settled = []

    def idempotent(principal, route, key, payload, fn):
        result, new = actual(principal, route, key, payload, fn)
        if route.endswith("/commands") and new:
            # Fault injection: a concurrent reconciliation settles the request after
            # acceptance commits but before delegation acquires the store lock.
            op = studio.store.get("operation", result["operationId"])
            op.update(status="failed", code="RUN_TERMINAL_BEFORE_COMMAND")
            studio.store.put("operation", op["operationId"], op)
            run = studio.store.get("run", rid)
            run.pop("pendingCommandId")
            studio.store.put("run", rid, run)
            settled.append(op["operationId"])
        return result, new

    monkeypatch.setattr(studio.store, "idempotent", idempotent)
    accepted = {}

    def on_tick(tick):
        if tick == 2:
            accepted.update(_command(client, rid, "settled-before-delegation"))
            assert not (root / "command.json").exists()

    code, _ = _run_worker(monkeypatch, root, namespace, on_tick)
    assert code == 0 and settled == [accepted["operationId"]]
    operation = client.get("/api/v1/operations/" + accepted["operationId"]).json()
    assert operation["status"] == "failed"
    assert operation["code"] == "RUN_TERMINAL_BEFORE_COMMAND"
    assert client.get("/api/v1/runs/" + rid).json()["state"] == "stopped"
    assert not any(r["type"].startswith("command.") for r in _journal(root))
