"""Owned Linux failure fixtures for explicit managed-data retention; no provider start."""

from pathlib import Path
import shutil
import sqlite3

import pytest

from xverse_studio.retention.service import RetentionService
from xverse_studio.storage.core import Problem


def project(client, name="Retirement fixture"):
    response = client.post("/api/v1/projects", json={"name": name})
    assert response.status_code == 201, response.text
    return response.json()


def plan(client, pid):
    response = client.post("/api/v1/retention/plans", json={"projectIds": [pid]})
    assert response.status_code == 200, response.text
    return response.json()


def apply(client, preview, key="retention-failure"):
    return client.post(
        "/api/v1/retention/plans/" + preview["planId"] + "/apply",
        headers={"Idempotency-Key": key},
        json={"fingerprint": preview["fingerprint"]},
    )


def test_project_metadata_write_failure_restores_original_and_allows_explicit_retry(
    client, monkeypatch
):
    original = project(client)
    pid = original["projectId"]
    preview = plan(client, pid)
    store = client.app.state.studio.store
    put = store.put

    def fail(kind, identifier, body, db=None):
        result = put(kind, identifier, body, db)
        if kind == "retentionTombstone" and identifier == "project:" + pid:
            raise OSError("owned injected metadata write refusal")
        return result

    with monkeypatch.context() as patch:
        patch.setattr(store, "put", fail)
        response = apply(client, preview)
    assert response.status_code == 202, response.text
    assert response.json()["status"] == "partial"
    current = client.get("/api/v1/projects/" + pid)
    assert current.status_code == 200, current.text
    assert current.json()["documents"] == original["documents"]
    assert (store.root / "projects" / pid).exists()
    with pytest.raises(Problem):
        store.get("retentionTombstone", "project:" + pid)
    retry = apply(client, plan(client, pid), "retire-after-restored-rollback")
    assert retry.status_code == 202 and retry.json()["status"] == "complete", retry.text


@pytest.mark.parametrize("after_commit", [False, True])
def test_real_sqlite_retirement_commit_outcomes_do_not_reverse_committed_metadata(
    client, monkeypatch, after_commit
):
    original = project(client)
    pid = original["projectId"]
    preview = plan(client, pid)
    connect = sqlite3.connect
    fired = [False]

    class Proxy:
        def __init__(self, connection):
            self.connection = connection
            self.retirement = False

        def __getattr__(self, key):
            return getattr(self.connection, key)

        def execute(self, statement, parameters=()):
            if statement.startswith("DELETE FROM records") and parameters == (
                "project",
                pid,
            ):
                self.retirement = True
            return self.connection.execute(statement, parameters)

        def commit(self):
            if self.retirement and not fired[0]:
                fired[0] = True
                if after_commit:
                    self.connection.commit()
                raise sqlite3.OperationalError(
                    "owned injected commit acknowledgement failure"
                )
            return self.connection.commit()

    with monkeypatch.context() as patch:
        patch.setattr(
            sqlite3, "connect", lambda *args, **kwargs: Proxy(connect(*args, **kwargs))
        )
        response = apply(client, preview)
    assert fired[0] and response.status_code == 202, response.text
    if after_commit:
        assert response.json()["status"] == "complete", response.text
        assert client.get("/api/v1/projects/" + pid).status_code == 404
        assert not (client.app.state.studio.store.root / "projects" / pid).exists()
    else:
        assert response.json()["status"] == "partial", response.text
        current = client.get("/api/v1/projects/" + pid)
        assert current.status_code == 200, current.text
        assert current.json()["documents"] == original["documents"]


def test_project_purge_failure_is_visible_and_residue_requires_new_explicit_plan(
    client, monkeypatch
):
    original = project(client)
    pid = original["projectId"]
    preview = plan(client, pid)
    import xverse_studio.retention.service as service

    remove = shutil.rmtree

    def refuse(path, *args, **kwargs):
        if "retention-staging" in Path(path).parts:
            raise OSError("owned injected purge refusal")
        return remove(path, *args, **kwargs)

    with monkeypatch.context() as patch:
        patch.setattr(service.shutil, "rmtree", refuse)
        response = apply(client, preview)
    assert response.status_code == 202 and response.json()["status"] == "partial", (
        response.text
    )
    outcome = response.json()["outcomes"][0]
    assert (
        outcome["metadataRemoved"] is True and outcome["remainingManagedFiles"] is True
    )
    assert client.get("/api/v1/projects/" + pid).status_code == 404
    tombstone = client.app.state.studio.store.get(
        "retentionTombstone", "project:" + pid
    )
    assert (client.app.state.studio.store.root / tombstone["quarantineRef"]).exists()
    residue = plan(client, pid)
    assert residue["removals"] == [
        {"projectId": pid, "scope": "owned_project_retention_residue"}
    ]
    result = apply(client, residue, "explicit-residue-cleanup")
    assert result.status_code == 202 and result.json()["status"] == "complete", (
        result.text
    )
    assert not (
        client.app.state.studio.store.root / tombstone["quarantineRef"]
    ).exists()


def staged_project(client):
    original = project(client)
    pid = original["projectId"]
    preview = plan(client, pid)
    store = client.app.state.studio.store
    stage = {
        "kind": "project",
        "resourceId": pid,
        "planId": preview["planId"],
        "quarantineRef": f"retention-staging/{preview['planId']}/{pid}",
        "phase": "quarantined",
        "originalFingerprint": preview["filesystem"]["project:" + pid]["fingerprint"],
    }
    source = store.root / "projects" / pid
    quarantine = store.root / stage["quarantineRef"]
    quarantine.parent.mkdir(parents=True)
    source.rename(quarantine)
    store.put("retentionProjectStage", preview["planId"] + ":" + pid, stage)
    return original, stage, source, quarantine


def test_interrupted_uncommitted_project_retirement_restores_bytes_without_replaying_delete(
    client,
):
    original, stage, source, quarantine = staged_project(client)
    studio = client.app.state.studio
    RetentionService(studio.store, studio.projects, studio.runs)
    assert source.exists() and not quarantine.exists()
    assert (
        studio.projects.read(original["projectId"])["documents"]
        == original["documents"]
    )
    assert (
        studio.store.get(
            "retentionProjectStage", stage["planId"] + ":" + original["projectId"]
        )["phase"]
        == "aborted"
    )


def test_recovery_never_overwrites_an_existing_project_or_reverses_retirement(client):
    original, stage, source, quarantine = staged_project(client)
    source.mkdir()
    marker = source / "unrelated.txt"
    marker.write_text("preserve independent existing bytes")
    studio = client.app.state.studio
    RetentionService(studio.store, studio.projects, studio.runs)
    assert (
        marker.read_text() == "preserve independent existing bytes"
        and quarantine.exists()
    )
    assert (
        studio.store.get(
            "retentionProjectStage", stage["planId"] + ":" + original["projectId"]
        )["phase"]
        == "unknown"
    )
    # No overwrite or automatic purge is authorized by an uncertain recovery state.
    preview = plan(client, original["projectId"])
    assert preview["removals"] == []
    assert "RETENTION_RECOVERY_REQUIRED" in preview["protected"][0]["reasons"]


def test_symlinked_project_path_cannot_remove_external_fixture(client, tmp_path):
    original = project(client)
    pid = original["projectId"]
    store = client.app.state.studio.store
    source = store.root / "projects" / pid
    held = store.root / "held-project"
    source.rename(held)
    external = tmp_path / "external"
    external.mkdir()
    marker = external / "keep.txt"
    marker.write_text("keep external bytes")
    source.symlink_to(external, target_is_directory=True)
    response = client.post("/api/v1/retention/plans", json={"projectIds": [pid]})
    assert response.status_code == 422, response.text
    assert marker.read_text() == "keep external bytes"
    source.unlink()
    held.rename(source)


def test_retention_uses_bounded_descriptors_and_refuses_oversized_external_source(
    client, monkeypatch
):
    original = project(client)
    studio = client.app.state.studio
    registered = client.post(
        "/api/v1/catalog/artifacts",
        headers={"Idempotency-Key": "bounds-artifact"},
        json={
            "name": "Unreferenced metadata",
            "version": "1.0.0",
            "artifactKind": "model",
            "digest": "sha256:" + "a" * 64,
            "originRef": "urn:owned:bounded-source",
        },
    ).json()
    read_bytes = Path.read_bytes

    def forbidden_read_bytes(path):
        if path.is_relative_to(studio.store.root):
            raise AssertionError(
                "Retention must not perform unbounded managed Path.read_bytes"
            )
        return read_bytes(
            path
        )  # Trusted installed validator identity, outside managed input roots.

    with monkeypatch.context() as patch:
        patch.setattr(Path, "read_bytes", forbidden_read_bytes)
        response = client.post(
            "/api/v1/retention/plans", json={"artifactIds": [registered["entryId"]]}
        )
    assert response.status_code == 200, response.text
    did = next(iter(original["documents"]))
    path = studio.projects.document_path(original["projectId"], did)
    with path.open("wb") as stream:
        stream.truncate(128 * 1024 * 1024)
    response = client.post(
        "/api/v1/retention/plans", json={"artifactIds": [registered["entryId"]]}
    )
    assert response.status_code == 413, response.text
    assert path.stat().st_size == 128 * 1024 * 1024


def test_proof_limit_refuses_before_project_deletion(client, monkeypatch):
    original = project(client)
    import xverse_studio.retention.files as files

    with monkeypatch.context() as patch:
        patch.setattr(files, "MAX_PROOF_BYTES", 16)
        response = client.post(
            "/api/v1/retention/plans", json={"projectIds": [original["projectId"]]}
        )
    assert response.status_code == 413, response.text
    assert client.get("/api/v1/projects/" + original["projectId"]).status_code == 200
