import time


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
