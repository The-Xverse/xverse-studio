"""Malformed sealed metadata is uncertainty, never a usable envelope baseline."""

import json

import pytest

from test_project_manifest_integrity import project


@pytest.mark.parametrize("fault", ["malformed-json", "nonfinite", "unencodable"])
def test_corrupt_sealed_history_is_inspectable_and_cannot_be_restored(client, fault):
    p, path = project(client)
    store = client.app.state.studio.store
    identity = f"{p['projectId']}:{p['revision']}"
    record = store.get("revision", identity)
    if fault == "malformed-json":
        raw = "{invalid recorded metadata"
    else:
        record["manifest"]["foreign"] = float("nan") if fault == "nonfinite" else "\ud800"
        raw = json.dumps(record)
    with store.tx() as db:
        db.execute("UPDATE records SET body=? WHERE kind='revision' AND id=?", (raw, identity))
    original = path.read_bytes()
    response = client.get("/api/v1/projects/" + p["projectId"])
    assert response.status_code == 200 and response.json()["sourceIntegrity"] == "modified", response.text
    assert any(d.get("observed") == "unverified" for d in response.json()["sourceDiagnostics"])
    refused = client.post(f"/api/v1/projects/{p['projectId']}/recoveries", headers={"If-Match": str(p["revision"])},
                          json={"expectedRevision": p["revision"], "action": "restore_revision", "revision": p["revision"]})
    assert refused.status_code == 409 and refused.json()["code"] == "REVISION_UNRECOVERABLE", refused.text
    assert store.all("recovery") == [] and path.read_bytes() == original
    with store.tx() as db:
        assert db.execute("SELECT body FROM records WHERE kind='revision' AND id=?", (identity,)).fetchone()[0] == raw
