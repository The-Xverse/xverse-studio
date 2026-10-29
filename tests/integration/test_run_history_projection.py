"""Actual owned runs: bounded history work and exact-input assessment cache isolation."""

from copy import deepcopy

from test_advanced_api import prepared, start, wait_run


def two_runs(client):
    project, left_pf = prepared(client)
    left = start(client, left_pf, key="history-left")
    assert wait_run(client, left)["state"] == "stopped"
    right_pf = client.post(
        f"/api/v1/projects/{project['projectId']}/preflights",
        json={"revision": project["revision"]},
    ).json()
    assert right_pf["status"] == "ready"
    right = start(client, right_pf, key="history-right")
    assert wait_run(client, right)["state"] == "stopped"
    return project, left, right


def test_run_history_only_reconciles_requested_page_without_dropping_assessment(
    client, monkeypatch
):
    project, left, right = two_runs(client)
    manager = client.app.state.studio.runs
    original = manager.read
    calls = []

    def observed(rid):
        calls.append(rid)
        return original(rid)

    monkeypatch.setattr(manager, "read", observed)
    page = client.get("/api/v1/runs", params={"limit": 1})
    assert page.status_code == 200, page.text
    assert [r["runId"] for r in page.json()["items"]] == [right]
    assert page.json()["nextCursor"] == "1"
    assert calls == [right], "Off-page runs must not be reconciled before pagination."
    row = page.json()["items"][0]
    assert row["state"] == "stopped" and row["cleanup"] == "complete"
    assert row["evaluation"] == "not_started" and row["verdict"] is None
    assert row["evaluationSummary"]["requiredAssertions"] == 1
    assert not any(key in row for key in ["pid", "createTime", "ownerDigest"])
    calls.clear()
    page = client.get(
        "/api/v1/runs",
        params={"limit": 1, "cursor": "1", "projectId": project["projectId"]},
    )
    assert page.status_code == 200 and [r["runId"] for r in page.json()["items"]] == [
        left
    ]
    assert page.json()["nextCursor"] is None and calls == [left]
    calls.clear()
    invalid = client.get("/api/v1/runs", params={"limit": 1, "cursor": "not-a-cursor"})
    assert invalid.status_code >= 400 and invalid.json()["code"] == "CURSOR_INVALID"
    assert calls == []


def test_same_frozen_documents_share_admission_but_never_another_runs_verdict(
    client, monkeypatch
):
    import xverse_studio.api.advanced as advanced

    original = advanced.snapshot_definitions
    admissions = []

    def observed(snapshot, adapter):
        admissions.append(snapshot["snapshotId"])
        return original(snapshot, adapter)

    monkeypatch.setattr(advanced, "snapshot_definitions", observed)
    project, left, right = two_runs(client)
    store = client.app.state.studio.store
    left_run = client.get("/api/v1/runs/" + left).json()
    right_run = client.get("/api/v1/runs/" + right).json()
    a = store.get("snapshot", left_run["snapshotId"])
    b = store.get("snapshot", right_run["snapshotId"])
    assert (
        a["snapshotId"] != b["snapshotId"]
        and a["snapshotDigest"] != b["snapshotDigest"]
    )
    assert a["documents"] == b["documents"]
    assert len(admissions) == 1, (
        "Identical immutable definition inputs must not be re-admitted for each snapshot UUID."
    )
    definition = client.get(f"/api/v1/runs/{left}/definitions").json()["items"][0]
    evaluated = client.post(
        f"/api/v1/runs/{left}/evaluations",
        headers={"Idempotency-Key": "history-left-evaluation"},
        json={
            "snapshotId": a["snapshotId"],
            "definitionRef": definition["definitionRef"],
            "definitionDigest": definition["definitionDigest"],
            "evidenceRefs": [left + ":reference-journal"],
        },
    )
    assert evaluated.status_code == 202, evaluated.text
    page = client.get(
        "/api/v1/runs", params={"projectId": project["projectId"]}
    ).json()["items"]
    by_id = {r["runId"]: r for r in page}
    assert by_id[left]["verdict"] == "pass" and by_id[left]["evaluation"] == "complete"
    assert (
        by_id[right]["verdict"] is None and by_id[right]["evaluation"] == "not_started"
    )
    before = len(admissions)
    edited = client.post(
        f"/api/v1/projects/{project['projectId']}/edits",
        headers={"If-Match": str(project["revision"])},
        json={
            "baseRevision": project["revision"],
            "edits": [{"kind": "set_parameter", "parameterId": "gain", "value": 1.2}],
        },
    )
    assert edited.status_code == 200
    project = edited.json()
    pf = client.post(
        f"/api/v1/projects/{project['projectId']}/preflights",
        json={"revision": project["revision"]},
    ).json()
    assert pf["status"] == "ready"
    changed_snapshot = store.get("snapshot", pf["snapshotId"])
    assert changed_snapshot["documents"] != a["documents"]
    assert changed_snapshot["configuration"]["gain"] == 1.2
    third = start(client, pf, key="history-different-documents")
    assert wait_run(client, third)["state"] == "stopped"
    assert len(admissions) == before + 1
    # Labelled SQLite-only integrity fault: no protected snapshot/journal file is changed.
    original_snapshot = deepcopy(b)
    changed = deepcopy(b)
    changed["revision"] += 1
    store.put("snapshot", b["snapshotId"], changed)
    try:
        refused = client.get("/api/v1/runs/" + right).json()
        assert refused["verdict"] == "indeterminate"
        assert (
            "SNAPSHOT_INTEGRITY_INVALID" in refused["evaluationSummary"]["diagnostics"]
        )
    finally:
        store.put("snapshot", original_snapshot["snapshotId"], original_snapshot)
