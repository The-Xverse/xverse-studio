"""Draft envelope conflicts do not rewrite completed receipts or frozen inputs."""

from test_project_manifest_integrity import project
from test_recorded_replay_and_rerun import original_run, rerun


def test_completed_export_receipt_survives_a_later_envelope_conflict(client):
    p, path = project(client)
    route = f"/api/v1/projects/{p['projectId']}/exports"
    body, headers = {"revision": p["revision"]}, {"Idempotency-Key": "original-envelope-export"}
    original = client.post(route, json=body, headers=headers)
    assert original.status_code == 202, original.text
    receipt = original.json()
    data = client.get(receipt["result"]["downloadUrl"]).content
    path.write_bytes(b'{"foreign":"changed after completed export"}')
    again = client.post(route, json=body, headers=headers)
    assert again.status_code == 202 and again.json() == receipt
    refused = client.post(route, json=body, headers={"Idempotency-Key": "new-conflicted-export"})
    assert refused.status_code == 412 and refused.json()["code"] == "REVISION_CONFLICT"
    assert client.get(receipt["result"]["downloadUrl"]).content == data
    assert len(client.app.state.studio.store.all("operation")) == 1


def test_explicit_frozen_rerun_remains_separate_from_a_conflicted_current_envelope(client):
    p, original = original_run(client)
    studio = client.app.state.studio
    path = studio.projects._dir(p["projectId"], p["revision"]) / "project.studio.json"
    snapshot_path = studio.store.root / "snapshots" / original["snapshotId"] / "snapshot.json"
    frozen_bytes = snapshot_path.read_bytes()
    original_snapshot = studio.store.get("snapshot", original["snapshotId"])
    raw = b'{"foreign":"current draft envelope is not a rerun input"}'
    path.write_bytes(raw)
    observed = client.get("/api/v1/projects/" + p["projectId"])
    assert observed.status_code == 200 and observed.json()["sourceIntegrity"] == "modified"
    assert client.post(f"/api/v1/projects/{p['projectId']}/preflights", json={"revision": p["revision"]}).status_code == 412
    _, operation = rerun(client, original["runId"])
    assert operation["status"] == "completed", operation
    child = studio.store.get("run", operation["result"]["runId"])
    copied = studio.store.get("snapshot", child["snapshotId"])
    assert copied["documents"] == original_snapshot["documents"] and copied["planDigest"] == original_snapshot["planDigest"]
    assert snapshot_path.read_bytes() == frozen_bytes and path.read_bytes() == raw
    assert len(studio.store.all("run")) == 2
