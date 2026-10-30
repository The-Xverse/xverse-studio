"""Corrupted revision envelopes: authenticated observation, no process authority."""

import json

import pytest

from xverse_studio.storage.core import canonical


def project(client):
    response = client.post("/api/v1/projects", json={"name": "Envelope integrity Ω"})
    assert response.status_code == 201, response.text
    p = response.json()
    path = client.app.state.studio.projects._dir(p["projectId"], p["revision"]) / "project.studio.json"
    return p, path


@pytest.mark.parametrize("fault", ["changed", "formatted", "malformed", "missing", "symlink", "oversized", "nontext"])
def test_changed_revision_envelope_is_visible_and_blocks_new_work_without_allocation(client, monkeypatch, tmp_path, fault):
    p, path = project(client)
    store = client.app.state.studio.store
    before = {kind: store.all(kind) for kind in ["operation", "run", "snapshot", "revision"]}
    outside = tmp_path / "controlled outside.json"
    outside.write_bytes(b'{"syntheticOutside":"never-follow"}')
    if fault == "changed":
        path.write_text(json.dumps({**p["manifest"], "foreign": {"script": "must-not-execute"}}))
    elif fault == "formatted":
        path.write_bytes(path.read_bytes() + b"\n")
    elif fault == "malformed":
        path.write_text("{invalid envelope")
    elif fault == "missing":
        path.unlink()
    elif fault == "symlink":
        path.unlink()
        path.symlink_to(outside)
    elif fault == "oversized":
        path.write_bytes(b"x" * (16 * 1024 * 1024 + 1))
    elif fault == "nontext":
        path.write_bytes(b"\xff\xfe\x00")
    raw = path.read_bytes() if not path.is_symlink() and path.exists() else None

    def forbidden(*args, **kwargs):
        pytest.fail("An unverified revision envelope cannot authorize any launch")

    monkeypatch.setattr("xverse_studio.runs.service.subprocess.Popen", forbidden)
    response = client.get("/api/v1/projects/" + p["projectId"])
    assert response.status_code == 200, response.text
    observed = response.json()
    assert observed["sourceIntegrity"] == "modified", observed["sourceDiagnostics"]
    assert any(d.get("sidecar") == "project.studio.json" for d in observed["sourceDiagnostics"])
    assert "never-follow" not in response.text and "must-not-execute" not in response.text
    docid = next(iter(p["documents"]))
    routes = [
        ("post", f"/api/v1/projects/{p['projectId']}/compilations", {"revision": p["revision"]}, {}),
        ("post", f"/api/v1/projects/{p['projectId']}/preflights", {"revision": p["revision"]}, {}),
        ("put", f"/api/v1/projects/{p['projectId']}/documents/{docid}", {"content": p["documents"][docid]["content"] + "\n", "format": "yaml"}, {"If-Match": str(p["revision"])}),
        ("post", f"/api/v1/projects/{p['projectId']}/exports", {"revision": p["revision"]}, {"Idempotency-Key": "manifest-refused-export"}),
    ]
    for method, route, body, headers in routes:
        refused = getattr(client, method)(route, json=body, headers=headers)
        assert refused.status_code == 412 and refused.json()["code"] == "REVISION_CONFLICT", refused.text
    assert {kind: store.all(kind) for kind in before} == before
    assert not path.parent.with_name(str(p["revision"] + 1)).exists()
    if raw is not None:
        assert path.read_bytes() == raw
    assert outside.read_bytes() == b'{"syntheticOutside":"never-follow"}'


def test_start_rechecks_envelope_after_an_original_ready_preflight(client, monkeypatch):
    p, path = project(client)
    preflight = client.post(f"/api/v1/projects/{p['projectId']}/preflights", json={"revision": p["revision"]})
    assert preflight.status_code == 200 and preflight.json()["status"] == "ready", preflight.text
    path.write_text('{"foreign": "later external envelope"}')
    launches = []
    def forbidden(*args, **kwargs):
        launches.append(args)
        raise OSError("Controlled forbidden launch; no process was created")
    monkeypatch.setattr("xverse_studio.runs.service.subprocess.Popen", forbidden)
    response = client.post("/api/v1/runs", headers={"Idempotency-Key": "manifest-changed-after-preflight"},
                           json={"preflightId": preflight.json()["preflightId"], "snapshotId": preflight.json()["snapshotId"]})
    assert response.status_code == 412 and response.json()["code"] == "REVISION_CONFLICT", response.text
    store = client.app.state.studio.store
    assert store.all("run") == [] and store.all("operation") == []
    assert len(store.all("snapshot")) == 1 and launches == []


@pytest.mark.parametrize("action", ["adopt_external", "restore_revision"])
def test_envelope_recovery_preserves_external_bytes_and_uses_recorded_metadata(client, action):
    p, path = project(client)
    raw = b'{"foreign":"preserve exact bytes","resources":[],"profiles":[]}'
    path.write_bytes(raw)
    body = {"expectedRevision": p["revision"], "action": action}
    if action == "restore_revision":
        body["revision"] = p["revision"]
    response = client.post(f"/api/v1/projects/{p['projectId']}/recoveries", headers={"If-Match": str(p["revision"])}, json=body)
    assert response.status_code == 200, response.text
    result = response.json()
    after, recovery = result["project"], result["recovery"]
    assert after["revision"] == p["revision"] + 1 and after["sourceIntegrity"] == "intact"
    assert after["manifest"] == p["manifest"] and "foreign" not in after["manifest"]
    assert path.read_bytes() == raw
    preserved = client.get(f"/api/v1/projects/{p['projectId']}/recoveries/{recovery['recoveryId']}/preserved",
                           params={"key": "sidecar:project.studio.json"})
    assert preserved.status_code == 200 and preserved.json()["content"].encode() == raw, preserved.text
    new_path = client.app.state.studio.projects._dir(after["projectId"], after["revision"]) / "project.studio.json"
    assert new_path.read_bytes() == canonical(p["manifest"]).encode()


def test_layout_only_update_uses_the_sealed_source_envelope_baseline(client):
    p, path = project(client)
    original = path.read_bytes()
    before = client.post(f"/api/v1/projects/{p['projectId']}/compilations", json={"revision": p["revision"]}).json()
    changed = client.put(f"/api/v1/projects/{p['projectId']}/layout", headers={"If-Match": str(p["presentationRevision"])},
                         json={"positions": {"plant": {"x": 10, "y": 20}}})
    assert changed.status_code == 200 and changed.json()["sourceIntegrity"] == "intact", changed.text
    assert changed.json()["revision"] == p["revision"] and path.read_bytes() == original
    after = client.post(f"/api/v1/projects/{p['projectId']}/compilations", json={"revision": p["revision"]})
    assert after.status_code == 200 and after.json()["planDigest"] == before["planDigest"]


def test_prior_metadata_without_history_compares_known_envelope_fields_and_keeps_layout_separate(client):
    p, path = project(client)
    store = client.app.state.studio.store
    with store.tx() as db:
        db.execute("DELETE FROM records WHERE kind='revision' AND id=?", (f"{p['projectId']}:{p['revision']}",))
    path.write_bytes(path.read_bytes() + b"\n")  # No older textual seal is invented.
    changed = client.put(f"/api/v1/projects/{p['projectId']}/layout", headers={"If-Match": str(p["presentationRevision"])},
                         json={"positions": {"plant": {"x": 20, "y": 30}}})
    assert changed.status_code == 200 and changed.json()["sourceIntegrity"] == "intact", changed.text
    assert client.post(f"/api/v1/projects/{p['projectId']}/compilations", json={"revision": p["revision"]}).status_code == 200
    path.write_text(json.dumps({**p["manifest"], "foreign": "unrecorded external metadata"}))
    observed = client.get("/api/v1/projects/" + p["projectId"])
    assert observed.status_code == 200 and observed.json()["sourceIntegrity"] == "modified"
    recovered = client.post(f"/api/v1/projects/{p['projectId']}/recoveries", headers={"If-Match": str(p["revision"])},
                            json={"expectedRevision": p["revision"], "action": "adopt_external"})
    assert recovered.status_code == 200, recovered.text
    after = recovered.json()["project"]
    assert after["revision"] == 2 and after["sourceIntegrity"] == "intact"
    assert "foreign" not in after["manifest"]
    assert store.get("revision", f"{p['projectId']}:2")["manifest"] == after["manifest"]


@pytest.mark.parametrize("fault", ["foreign-project", "foreign-revision", "missing-manifest", "malformed-manifest"])
def test_invalid_history_identity_cannot_supply_a_manifest_or_restore_authority(client, fault):
    p, path = project(client)
    store = client.app.state.studio.store
    identity = f"{p['projectId']}:{p['revision']}"
    record = store.get("revision", identity)
    if fault == "foreign-project":
        record["projectId"] = "prj-another-owner"
    elif fault == "foreign-revision":
        record["revision"] = True
    elif fault == "missing-manifest":
        record.pop("manifest")
    else:
        record["manifest"] = []
    store.put("revision", identity, record)
    original = path.read_bytes()
    observed = client.get("/api/v1/projects/" + p["projectId"])
    assert observed.status_code == 200 and observed.json()["sourceIntegrity"] == "modified", observed.text
    assert any(d.get("observed") == "unverified" for d in observed.json()["sourceDiagnostics"])
    refused = client.post(f"/api/v1/projects/{p['projectId']}/recoveries", headers={"If-Match": str(p["revision"])},
                          json={"expectedRevision": p["revision"], "action": "restore_revision", "revision": p["revision"]})
    assert refused.status_code == 409 and refused.json()["code"] == "REVISION_UNRECOVERABLE", refused.text
    assert store.get("revision", identity) == record and store.all("recovery") == []
    assert path.read_bytes() == original and store.get("project", p["projectId"])["revision"] == p["revision"]
