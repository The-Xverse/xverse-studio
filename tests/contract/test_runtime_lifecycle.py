import time
import concurrent.futures


def prepared(client, duration=0.5):
    p = client.post("/api/v1/projects", json={"name": "Owned runtime"}).json()
    # Typed source edit keeps all upstream XDL authority and admitted topology.
    r = client.post(
        f"/api/v1/projects/{p['projectId']}/edits",
        headers={"If-Match": str(p["revision"])},
        json={
            "baseRevision": p["revision"],
            "edits": [
                {"kind": "set_parameter", "parameterId": "duration", "value": duration}
            ],
        },
    )
    assert r.status_code == 200, r.text
    p = r.json()
    pf = client.post(
        f"/api/v1/projects/{p['projectId']}/preflights",
        json={"revision": p["revision"]},
    )
    assert pf.status_code == 200, pf.text
    assert pf.json()["status"] == "ready", pf.text
    return p, pf.json()


def start(client, pf, key="start-once"):
    r = client.post(
        "/api/v1/runs",
        headers={"Idempotency-Key": key},
        json={"snapshotId": pf["snapshotId"], "preflightId": pf["preflightId"]},
    )
    assert r.status_code == 202, r.text
    return r.json()


def wait(client, rid, state="stopped", timeout=8):
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        r = client.get("/api/v1/runs/" + rid).json()
        if r["state"] == state:
            return r
        if r["state"] in ("failed", "unknown") and state not in ("failed", "unknown"):
            raise AssertionError(r)
        time.sleep(0.05)
    raise AssertionError(r)


def test_idempotent_dispatch_immutable_snapshot_and_scope(client):
    p, pf = prepared(client)
    r = start(client, pf)
    assert start(client, pf) == r
    assert len(client.get("/api/v1/runs").json()["items"]) == 1
    conflict = client.post(
        "/api/v1/runs",
        headers={"Idempotency-Key": "start-once"},
        json={"snapshotId": "other", "preflightId": pf["preflightId"]},
    )
    assert (
        conflict.status_code == 409
        and conflict.json()["code"] == "IDEMPOTENCY_CONFLICT"
    )
    ended = wait(client, r["runId"])
    assert ended["cleanup"] == "complete" and ended["evidence"] == "complete"
    assert ended["effectivePlanDigest"] == pf["planDigest"]
    assert ended["verdict"] is None
    obs = client.get(f"/api/v1/runs/{r['runId']}/observations").json()
    assert len(obs["items"]) == 5
    assert obs["items"][0]["values"]["value"] == 0
    assert obs["items"][-1]["values"]["value"] > 0
    assert obs["integrity"] == "valid"
    assert obs["clockDomain"] == "simulation-time"


def test_capabilities_stale_state_cancel_and_evidence_tamper(client):
    p, pf = prepared(client, 2.0)
    r = start(client, pf)
    running = wait(client, r["runId"], "running")
    unsupported = client.post(
        f"/api/v1/runs/{r['runId']}/commands",
        headers={"Idempotency-Key": "unsupported-step"},
        json={"kind": "step", "expectedStateVersion": running["stateVersion"]},
    )
    assert unsupported.status_code == 422
    stale = client.post(
        f"/api/v1/runs/{r['runId']}/commands",
        headers={"Idempotency-Key": "stale"},
        json={"kind": "cancel", "expectedStateVersion": 0},
    )
    assert stale.status_code == 409
    command = {"kind": "cancel", "expectedStateVersion": running["stateVersion"]}
    first = client.post(
        f"/api/v1/runs/{r['runId']}/commands",
        headers={"Idempotency-Key": "cancel"},
        json=command,
    )
    assert first.status_code == 202, first.text
    assert (
        client.post(
            f"/api/v1/runs/{r['runId']}/commands",
            headers={"Idempotency-Key": "cancel"},
            json=command,
        ).json()
        == first.json()
    )
    ended = wait(client, r["runId"])
    assert ended["cleanup"] == "complete"
    path = client.app.state.studio.runs.directory(r["runId"]) / "evidence.jsonl"
    path.write_bytes(
        path.read_bytes().replace(b"duration_complete", b"forged_completion")
    )
    # Ensure tampering even when a cancel reason differs.
    with path.open("ab") as f:
        f.write(b'{"fake":true}\n')
    assert client.get("/api/v1/runs/" + r["runId"]).json()["evidence"] == "invalid"


def test_preflight_change_and_unsupported_provider(client):
    p, pf = prepared(client)
    r = client.post(
        f"/api/v1/projects/{p['projectId']}/edits",
        headers={"If-Match": str(p["revision"])},
        json={
            "baseRevision": p["revision"],
            "edits": [{"kind": "set_parameter", "parameterId": "target", "value": 2.0}],
        },
    )
    assert r.status_code == 200, r.text
    response = client.post(
        "/api/v1/runs",
        headers={"Idempotency-Key": "stale"},
        json={"snapshotId": pf["snapshotId"], "preflightId": pf["preflightId"]},
    )
    assert response.status_code == 409, response.text
    response = client.post(
        f"/api/v1/projects/{p['projectId']}/preflights",
        json={"revision": r.json()["revision"], "providerId": "xverse.lite"},
    )
    assert response.json()["status"] == "blocked"
