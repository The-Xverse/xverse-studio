"""External writes, interrupted saves, undo/redo transactions and draft/run isolation."""

import time

import pytest

from xverse_studio.storage.core import digest


def project(client, name="edit conflicts"):
    response = client.post("/api/v1/projects", json={"name": name})
    assert response.status_code == 201, response.text
    return response.json()


def edit(client, p, *edits):
    response = client.post(
        f"/api/v1/projects/{p['projectId']}/edits",
        headers={"If-Match": str(p["revision"])},
        json={"baseRevision": p["revision"], "edits": list(edits)},
    )
    assert response.status_code == 200, response.text
    return response.json()


def restore(client, p, target, expected=None):
    return client.post(
        f"/api/v1/projects/{p['projectId']}/revisions/{target}/restore",
        headers={"If-Match": str(p["revision"] if expected is None else expected)},
    )


def contents(p):
    return {d["path"].rsplit("/", 1)[-1]: d["content"] for d in p["documents"].values()}


def valid(client, p):
    response = client.post(
        f"/api/v1/projects/{p['projectId']}/validations",
        json={"revision": p["revision"]},
    )
    assert response.status_code == 200, response.text
    return response.json()["valid"]


def preserved_source(client, p, recovery, key):
    response = client.get(
        f"/api/v1/projects/{p['projectId']}/recoveries/{recovery['recoveryId']}/preserved",
        params={"key": key},
    )
    assert response.status_code == 200, response.text
    return response.json()


def recover(client, p, action, revision=None):
    return client.post(
        f"/api/v1/projects/{p['projectId']}/recoveries",
        headers={"If-Match": str(p["revision"])},
        json={"expectedRevision": p["revision"], "action": action}
        | ({"revision": revision} if revision is not None else {}),
    )


def revision_dir(client, p, revision=None):
    root = client.app.state.studio.store.root
    return (
        root
        / "projects"
        / p["projectId"]
        / "revisions"
        / str(revision or p["revision"])
    )


ADD = {
    "kind": "add_element",
    "templateId": "reference-plant",
    "elementId": "second-plant",
    "nodeId": "plant-node",
}
CONNECT = {
    "kind": "connect_endpoints",
    "flowId": "extra-state-flow",
    "sourceEndpointId": "plant-out",
    "destinationEndpointIds": ["observer-in"],
    "interfaceId": "state",
}
DISCONNECT = {"kind": "disconnect_flow", "flowId": "extra-state-flow"}
REMOVE = {"kind": "remove_element", "elementId": "second-plant"}


def test_history_records_origin_and_digests_of_every_revision(client):
    p = project(client)
    p = edit(client, p, ADD)
    history = client.get(f"/api/v1/projects/{p['projectId']}/revisions").json()
    assert [r["revision"] for r in history["items"]] == [2, 1]
    assert history["items"][1]["origin"] == {"kind": "create"}
    assert history["items"][0]["origin"] == {
        "kind": "semantic_edit",
        "edits": ["add_element"],
    }
    recorded = {
        d["path"]: d["digest"] for d in history["items"][0]["documents"].values()
    }
    assert recorded == {
        d["path"]: digest(d["content"].encode()) for d in p["documents"].values()
    }
    assert history["nextBefore"] is None and history["unrecordedBefore"] is None
    assert "manifest" not in history["items"][0]


def test_undo_redo_add_connect_delete_preserves_exact_bytes_and_references(client):
    p1 = project(client)
    p2 = edit(client, p1, ADD)
    p3 = edit(client, p2, CONNECT)
    p4 = edit(client, p3, DISCONNECT)
    p5 = edit(client, p4, REMOVE)
    assert contents(p5) == contents(p1)  # the transaction chain itself is reversible
    states = [p1, p2, p3, p4, p5]
    current = p5
    # Undo four steps: each new forward revision equals its target's bytes exactly.
    for target in (p4, p3, p2, p1):
        response = restore(client, current, target["revision"])
        assert response.status_code == 200, response.text
        current = response.json()
        assert contents(current) == contents(target)
        assert valid(client, current)
    # Redo back to the connected state.
    for target in (p2, p3):
        current = restore(client, current, target["revision"]).json()
        assert contents(current) == contents(target)
        assert valid(client, current)
    assert "extra-state-flow" in contents(current)["system.xdl.yaml"]
    history = client.get(f"/api/v1/projects/{p1['projectId']}/revisions").json()
    origins = [r["origin"] for r in history["items"][:6]]
    assert origins[0] == {"kind": "restore", "fromRevision": 3}
    assert len(history["items"]) == len(states) + 6
    # History is append-only: earlier revisions are unchanged.
    for state in states:
        recorded = next(
            r for r in history["items"] if r["revision"] == state["revision"]
        )
        assert {d["path"]: d["digest"] for d in recorded["documents"].values()} == {
            d["path"]: digest(d["content"].encode())
            for d in state["documents"].values()
        }


def test_stale_restore_and_concurrent_session_saves_conflict_without_changes(client):
    p1 = project(client)
    p2 = edit(client, p1, ADD)
    # Another session already advanced the project from revision 1.
    stale = restore(client, p2, 1, expected=1)
    assert stale.status_code == 412
    assert stale.json()["code"] == "REVISION_CONFLICT"
    assert stale.json()["currentRevision"] == 2
    did = next(iter(p2["documents"]))
    document = p2["documents"][did]
    first = client.put(
        f"/api/v1/projects/{p2['projectId']}/documents/{did}",
        headers={"If-Match": "2"},
        json={"content": document["content"] + "\n", "format": document["format"]},
    )
    second = client.put(
        f"/api/v1/projects/{p2['projectId']}/documents/{did}",
        headers={"If-Match": "2"},
        json={"content": document["content"] + "\n\n", "format": document["format"]},
    )
    assert first.status_code == 200 and second.status_code == 412
    current = client.get(f"/api/v1/projects/{p2['projectId']}").json()
    assert current["revision"] == 3
    assert current["documents"][did]["content"] == document["content"] + "\n"


def test_restore_ignores_a_tampered_sealed_copy_and_refuses_missing_history(client):
    p1 = project(client)
    p2 = edit(client, p1, ADD)
    store = client.app.state.studio.store
    objects = store.root / "projects" / p1["projectId"] / "objects"
    system = next(
        d for d in p1["documents"].values() if d["path"].endswith("/system.xdl.yaml")
    )
    blob = objects / digest(system["content"].encode()).split(":", 1)[1]
    blob.write_text(system["content"] + "# tampered\n")
    # The tampered copy is never served; the matching revision file is.
    restored = restore(client, p2, 1)
    assert restored.status_code == 200, restored.text
    assert contents(restored.json()) == contents(p1)
    missing = restore(client, restored.json(), 99)
    assert missing.status_code == 409
    assert missing.json()["code"] == "REVISION_UNRECOVERABLE"


def test_external_write_is_preserved_and_both_versions_stay_recoverable(client):
    p1 = project(client)
    p2 = edit(client, p1, ADD)
    did, doc = next(
        (k, v)
        for k, v in p2["documents"].items()
        if v["path"].endswith("/system.xdl.yaml")
    )
    path = revision_dir(client, p2) / doc["path"]
    external = doc["content"].replace("reference-loop", "externally-renamed-loop", 1)
    path.write_text(external)
    read = client.get(f"/api/v1/projects/{p2['projectId']}").json()
    assert read["sourceIntegrity"] == "modified"
    # A save against the externally modified revision conflicts and changes nothing.
    save = client.put(
        f"/api/v1/projects/{p2['projectId']}/documents/{did}",
        headers={"If-Match": "2"},
        json={"content": doc["content"], "format": doc["format"]},
    )
    assert save.status_code == 412 and save.json()["code"] == "REVISION_CONFLICT"
    assert path.read_text() == external
    blocked = restore(client, read, 1)
    assert blocked.status_code == 412
    adopted = client.post(
        f"/api/v1/projects/{p2['projectId']}/recoveries",
        headers={"If-Match": "2"},
        json={"expectedRevision": 2, "action": "adopt_external"},
    )
    assert adopted.status_code == 200, adopted.text
    result = adopted.json()
    assert result["project"]["revision"] == 3
    assert result["project"]["sourceIntegrity"] == "intact"
    assert contents(result["project"])["system.xdl.yaml"] == external
    recovery = result["recovery"]
    assert list(recovery["preserved"]) == ["document:" + did]
    assert recovery["preserved"]["document:" + did]["committedDigest"] == doc["digest"]
    preserved = preserved_source(client, p2, recovery, "document:" + did)
    assert preserved["content"] == external
    # The committed bytes of revision 2 remain recoverable from verified history.
    back = restore(client, result["project"], 2)
    assert back.status_code == 200, back.text
    assert contents(back.json()) == contents(p2)
    listed = client.get(f"/api/v1/projects/{p2['projectId']}/recoveries").json()
    assert [r["recoveryId"] for r in listed["items"]] == [recovery["recoveryId"]]


def test_recovery_can_restore_the_committed_revision_and_requires_a_conflict(client):
    p1 = project(client)
    not_needed = client.post(
        f"/api/v1/projects/{p1['projectId']}/recoveries",
        headers={"If-Match": "1"},
        json={"expectedRevision": 1, "action": "adopt_external"},
    )
    assert not_needed.status_code == 409
    assert not_needed.json()["code"] == "RECOVERY_NOT_REQUIRED"
    doc = next(
        d for d in p1["documents"].values() if d["path"].endswith("/plant.xdl.yaml")
    )
    (revision_dir(client, p1) / doc["path"]).write_text("external: true\n")
    stale = client.post(
        f"/api/v1/projects/{p1['projectId']}/recoveries",
        headers={"If-Match": "1"},
        json={"expectedRevision": 0, "action": "adopt_external"},
    )
    assert stale.status_code == 412
    restored = client.post(
        f"/api/v1/projects/{p1['projectId']}/recoveries",
        headers={"If-Match": "1"},
        json={"expectedRevision": 1, "action": "restore_revision", "revision": 1},
    )
    assert restored.status_code == 200, restored.text
    project_after = restored.json()["project"]
    assert project_after["revision"] == 2 and contents(project_after) == contents(p1)
    recovery = restored.json()["recovery"]
    preserved = preserved_source(
        client, p1, recovery, next(iter(recovery["preserved"]))
    )
    assert preserved["content"] == "external: true\n"


def test_interrupted_save_keeps_the_last_saved_revision(client, monkeypatch):
    from xverse_studio.projects import service

    p1 = project(client)
    did = next(iter(p1["documents"]))
    real_atomic, writes = service.atomic, []

    def failing(path, data):
        writes.append(path)
        if len(writes) == 3:
            raise OSError("injected interruption during staging")
        return real_atomic(path, data)

    monkeypatch.setattr(service, "atomic", failing)
    with pytest.raises(OSError):
        client.put(
            f"/api/v1/projects/{p1['projectId']}/documents/{did}",
            headers={"If-Match": "1"},
            json={"content": p1["documents"][did]["content"] + "\n", "format": "yaml"},
        )
    monkeypatch.setattr(service, "atomic", real_atomic)
    current = client.get(f"/api/v1/projects/{p1['projectId']}").json()
    assert current["revision"] == 1 and current["sourceIntegrity"] == "intact"
    assert contents(current) == contents(p1)
    revisions = revision_dir(client, p1).parent
    assert sorted(child.name for child in revisions.iterdir()) == ["1"]
    history = client.get(f"/api/v1/projects/{p1['projectId']}/revisions").json()
    assert [r["revision"] for r in history["items"]] == [1]
    retried = client.put(
        f"/api/v1/projects/{p1['projectId']}/documents/{did}",
        headers={"If-Match": "1"},
        json={"content": p1["documents"][did]["content"] + "\n", "format": "yaml"},
    )
    assert retried.status_code == 200 and retried.json()["revision"] == 2


def test_leftover_staged_revision_blocks_until_explicit_recovery(client):
    p1 = project(client)
    revision_dir(client, p1, 2).mkdir()
    did = next(iter(p1["documents"]))
    response = client.put(
        f"/api/v1/projects/{p1['projectId']}/documents/{did}",
        headers={"If-Match": "1"},
        json={"content": p1["documents"][did]["content"] + "\n", "format": "yaml"},
    )
    assert (
        response.status_code == 412 and response.json()["code"] == "REVISION_CONFLICT"
    )
    assert client.get(f"/api/v1/projects/{p1['projectId']}").json()["revision"] == 1


def test_draft_edits_and_undo_never_change_an_active_run_snapshot(client):
    p1 = project(client, "draft run isolation")
    p1 = edit(
        client, p1, {"kind": "set_parameter", "parameterId": "duration", "value": 3}
    )
    pf = client.post(
        f"/api/v1/projects/{p1['projectId']}/preflights",
        json={"revision": p1["revision"]},
    ).json()
    run = client.post(
        "/api/v1/runs",
        headers={"Idempotency-Key": "draft-isolation"},
        json={"snapshotId": pf["snapshotId"], "preflightId": pf["preflightId"]},
    ).json()
    store = client.app.state.studio.store
    snapshot_file = store.root / "snapshots" / pf["snapshotId"] / "snapshot.json"
    before = snapshot_file.read_bytes()
    record_before = store.get("snapshot", pf["snapshotId"])
    p2 = edit(client, p1, ADD)
    p3 = edit(
        client, p2, {"kind": "set_parameter", "parameterId": "gain", "value": 0.5}
    )
    undone = restore(client, p3, p1["revision"])
    assert undone.status_code == 200, undone.text
    assert contents(undone.json()) == contents(p1)
    assert snapshot_file.read_bytes() == before
    assert store.get("snapshot", pf["snapshotId"]) == record_before
    frozen = client.get(f"/api/v1/runs/{run['runId']}/snapshot").json()
    assert (
        frozen["integrity"] == "valid"
        and frozen["snapshot"]["revision"] == p1["revision"]
    )
    deadline = time.monotonic() + 15
    while client.get("/api/v1/runs/" + run["runId"]).json()["state"] != "stopped":
        assert time.monotonic() < deadline
        time.sleep(0.1)
    ended = client.get("/api/v1/runs/" + run["runId"]).json()
    assert ended["effectivePlanDigest"] == pf["planDigest"]
    assert snapshot_file.read_bytes() == before


def test_restore_uses_a_verified_revision_copy_when_the_sealed_copy_is_lost(client):
    p1 = project(client)
    p2 = edit(client, p1, ADD)
    objects = (
        client.app.state.studio.store.root / "projects" / p1["projectId"] / "objects"
    )
    system = next(
        d for d in p1["documents"].values() if d["path"].endswith("/system.xdl.yaml")
    )
    (objects / digest(system["content"].encode()).split(":", 1)[1]).unlink()
    restored = restore(client, p2, 1)
    assert restored.status_code == 200, restored.text
    assert contents(restored.json()) == contents(p1)
    # With both copies gone or altered, nothing is restored.
    (objects / digest(system["content"].encode()).split(":", 1)[1]).unlink()
    (revision_dir(client, p1) / system["path"]).write_text("altered: true\n")
    current = restored.json()
    refused = restore(client, current, 1)
    assert (
        refused.status_code == 409
        and refused.json()["code"] == "REVISION_UNRECOVERABLE"
    )
    assert (
        client.get(f"/api/v1/projects/{p1['projectId']}").json()["revision"]
        == current["revision"]
    )


def test_restore_of_an_unknown_project_is_not_found(client):
    response = client.post(
        "/api/v1/projects/prj-missing/revisions/1/restore", headers={"If-Match": "1"}
    )
    assert response.status_code == 404


def test_failure_while_sealing_history_rolls_back_the_whole_revision(
    client, monkeypatch
):
    from xverse_studio.projects import revisions

    p1 = project(client)
    real = revisions.atomic

    def failing(path, data):
        raise OSError("injected failure while sealing history")

    monkeypatch.setattr(revisions, "atomic", failing)
    with pytest.raises(OSError):
        client.post(
            f"/api/v1/projects/{p1['projectId']}/edits",
            headers={"If-Match": "1"},
            json={"baseRevision": 1, "edits": [ADD]},
        )
    monkeypatch.setattr(revisions, "atomic", real)
    current = client.get(f"/api/v1/projects/{p1['projectId']}").json()
    assert current["revision"] == 1 and contents(current) == contents(p1)
    assert sorted(c.name for c in revision_dir(client, p1).parent.iterdir()) == ["1"]
    history = client.get(f"/api/v1/projects/{p1['projectId']}/revisions").json()
    assert [r["revision"] for r in history["items"]] == [1]


def test_tampered_sidecar_blocks_undo_and_is_preserved_by_recovery(client):
    studio = client.app.state.studio
    base = project(client)
    # Imported projects carry sidecars; create one through the same service path.
    p1 = studio.projects.create(
        "sidecar project",
        documents={d["path"]: d["content"] for d in base["documents"].values()},
        supporting={"artifacts.lock.json": '{"artifacts": []}'},
    )
    p2 = edit(client, p1, ADD)
    sidecar = revision_dir(client, p2) / "artifacts.lock.json"
    committed = sidecar.read_bytes()
    sidecar.write_text('{"tampered": true}')
    read = client.get(f"/api/v1/projects/{p2['projectId']}").json()
    assert read["sourceIntegrity"] == "modified"
    assert read["sourceDiagnostics"][0]["sidecar"] == "artifacts.lock.json"
    blocked = restore(client, p2, 1)
    assert blocked.status_code == 412  # undo never silently replaces the tampered file
    assert sidecar.read_text() == '{"tampered": true}'
    adopted = recover(client, p2, "adopt_external")
    assert adopted.status_code == 200, adopted.text
    result = adopted.json()
    entry = result["recovery"]["preserved"]["sidecar:artifacts.lock.json"]
    assert (
        entry["kind"] == "sidecar"
        and result["recovery"]["sidecarPolicy"] == "recorded_content"
    )
    assert (
        preserved_source(client, p2, result["recovery"], "sidecar:artifacts.lock.json")[
            "content"
        ]
        == '{"tampered": true}'
    )
    # Sidecars keep their recorded content; adopted documents are unchanged here.
    assert (
        revision_dir(client, result["project"]) / "artifacts.lock.json"
    ).read_bytes() == committed
    assert result["project"]["sourceIntegrity"] == "intact"


def test_unreadable_sources_can_only_be_restored_and_are_reported_as_such(client):
    p1 = project(client)
    p2 = edit(client, p1, ADD)
    system = next(
        d for d in p2["documents"].values() if d["path"].endswith("/system.xdl.yaml")
    )
    plant = next(
        d for d in p2["documents"].values() if d["path"].endswith("/plant.xdl.yaml")
    )
    (revision_dir(client, p2) / system["path"]).unlink()
    (revision_dir(client, p2) / plant["path"]).write_bytes(b"\xff\xfe not utf-8")
    unreadable = client.get(f"/api/v1/projects/{p2['projectId']}")
    assert unreadable.status_code == 409
    assert unreadable.json()["code"] == "PROJECT_UNAVAILABLE"
    adopt = recover(client, p2, "adopt_external")
    assert (
        adopt.status_code == 409
        and adopt.json()["code"] == "RECOVERY_ADOPT_UNAVAILABLE"
    )
    restored = recover(client, p2, "restore_revision", 2)
    assert restored.status_code == 200, restored.text
    result = restored.json()
    assert contents(result["project"]) == contents(p2)
    preserved = result["recovery"]["preserved"]
    missing = next(v for v in preserved.values() if v["path"] == system["path"])
    assert missing["status"] == "missing" and "backupFile" not in missing
    binary = next(v for v in preserved.values() if v["path"] == plant["path"])
    assert binary["backupFile"].startswith("files/")
    read_back = preserved_source(
        client,
        p2,
        result["recovery"],
        "document:"
        + next(k for k, d in p2["documents"].items() if d["path"] == plant["path"]),
    )
    assert read_back["content"] is None and read_back["encoding"] == "binary"


def test_history_listing_is_paged_and_bounded(client):
    p = project(client)
    for value in (1, 2, 3, 4):
        p = edit(
            client,
            p,
            {"kind": "set_parameter", "parameterId": "duration", "value": value},
        )
    first = client.get(
        f"/api/v1/projects/{p['projectId']}/revisions", params={"limit": 2}
    ).json()
    assert [r["revision"] for r in first["items"]] == [5, 4]
    second = client.get(
        f"/api/v1/projects/{p['projectId']}/revisions",
        params={"limit": 2, "before": first["nextBefore"]},
    ).json()
    assert [r["revision"] for r in second["items"]] == [3, 2]
    assert (
        client.get(
            f"/api/v1/projects/{p['projectId']}/revisions", params={"limit": 201}
        ).status_code
        == 422
    )


def test_private_full_backup_restores_history_copies_and_recovery_backups(tmp_path):
    from xverse_studio.host.recovery import backup_full, restore_full, verify_backup
    from xverse_studio.projects.service import Projects
    from xverse_studio.storage.core import Store
    from xverse_studio.xdl import XDLAdapter

    root = tmp_path / "data"
    store = Store(root)
    projects = Projects(store, XDLAdapter())
    p1 = projects.create("Backup history")
    did = next(iter(p1["documents"]))
    path = (
        root
        / "projects"
        / p1["projectId"]
        / "revisions"
        / "1"
        / p1["documents"][did]["path"]
    )
    path.write_text(p1["documents"][did]["content"] + "# external\n")
    recovered = projects.history.recover(p1["projectId"], 1, "adopt_external")
    backup = tmp_path / "backup"
    backup_full(root, backup)
    assert verify_backup(backup)["integrity"] == "valid"
    target = tmp_path / "restored"
    restore_full(backup, target)
    restored = Projects(Store(target), XDLAdapter())
    rid = recovered["recovery"]["recoveryId"]
    assert restored.history.recovered(p1["projectId"], rid, "document:" + did)[
        "content"
    ] == (p1["documents"][did]["content"] + "# external\n")
    documents, _, _ = restored.history.contents(p1["projectId"], 1)
    assert documents[did]["content"] == p1["documents"][did]["content"]
