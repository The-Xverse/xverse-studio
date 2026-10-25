"""Readonly snapshot HTTP acquisition; synthetic metadata grants no runtime evidence."""

from pathlib import Path
import pytest


@pytest.mark.parametrize(
    "mutation", ["none", "missing", "symlink", "oversize", "modified"]
)
def test_snapshot_route_uses_bounded_canonical_acquisition(
    client, monkeypatch, mutation
):
    project = client.post(
        "/api/v1/projects", json={"name": "Snapshot read fixture"}
    ).json()
    pf = client.post(
        f"/api/v1/projects/{project['projectId']}/preflights", json={"revision": 1}
    ).json()
    store = client.app.state.studio.store
    store.put(
        "run",
        "readonly-fixture",
        {
            "runId": "readonly-fixture",
            "snapshotId": pf["snapshotId"],
            "state": "stopped",
        },
    )
    path = store.root / "snapshots" / pf["snapshotId"] / "snapshot.json"
    raw = path.read_bytes()
    if mutation == "missing":
        path.unlink()
    elif mutation == "symlink":
        replacement = store.root / "unadmitted-snapshot.json"
        replacement.write_bytes(raw)
        path.unlink()
        path.symlink_to(replacement)
    elif mutation == "oversize":
        with path.open("wb") as stream:
            stream.truncate(64 * 1024 * 1024 + 1)
    elif mutation == "modified":
        path.write_bytes(b"{}")
    # Any accidental fallback to whole-file Path acquisition fails this test.
    monkeypatch.setattr(
        Path,
        "read_bytes",
        lambda *a, **k: pytest.fail("Snapshot route must use bounded anchored I/O"),
    )
    try:
        response = client.get("/api/v1/runs/readonly-fixture/snapshot")
        if mutation == "none":
            assert response.status_code == 200, response.text
            assert response.json()["snapshot"]["snapshotDigest"] == pf["snapshotDigest"]
            assert response.json()["integrity"] == "valid"
        else:
            assert response.status_code == 422, response.text
            assert response.json()["code"] == "SNAPSHOT_INTEGRITY"
    finally:
        # No runtime exists for this reader-only record; retire it before the
        # application's shutdown reconciles genuine runtime records.
        with store.tx() as db:
            db.execute(
                "DELETE FROM records WHERE kind=? AND id=?", ("run", "readonly-fixture")
            )
