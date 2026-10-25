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
