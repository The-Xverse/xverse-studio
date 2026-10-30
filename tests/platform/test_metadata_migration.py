"""Controlled known unversioned schema; no unidentified legacy-release claim."""

from contextlib import closing
import json
import os
import sqlite3
import subprocess
import sys

import pytest

from xverse_studio.projects.service import Projects
from xverse_studio.storage.core import Problem, Store
from xverse_studio.xdl import XDLAdapter


def unversioned_root(root):
    store = Store(root)
    projects = Projects(store, XDLAdapter())
    p = projects.create("Migration System Ω")
    document_id = next(iter(p["documents"]))
    content = "# Preserve authored Ω\r\n" + p["documents"][document_id]["content"].replace("\n", "\r\n")
    projects.save(p["projectId"], document_id, p["revision"], content, "yaml")
    project = projects.read(p["projectId"])
    plan = projects.adapter.compile(projects.sources(project))
    assert plan["valid"], plan
    store.put("session", "old-browser-session", {"private": "never-print-old-session"})
    store.put("operation", "op-original", {"operationId": "op-original", "status": "completed", "opaque": [1, 2]})
    with store.tx() as db:
        db.execute("INSERT INTO idempotency VALUES(?,?,?,?)", ("start", "original-key", "original-fingerprint", '{"operationId":"op-original"}'))
    # This explicitly constructs the prior accepted schema0 shape. It is not
    # evidence that an unspecified previous released package produced this root.
    with closing(sqlite3.connect(store.dbpath)) as db:
        db.execute("PRAGMA journal_mode=DELETE")
        db.execute("PRAGMA user_version=0")
    return project, plan


def inventory(root):
    return {p.relative_to(root).as_posix(): p.read_bytes() for p in root.rglob("*")
            if p.is_file() and p.name != "studio.lock"}


def migrate(source, backup, destination):
    from xverse_studio.host.migration import migrate_full
    return migrate_full(source, backup, destination)


@pytest.mark.parametrize("version", [0, 999])
def test_existing_metadata_requires_explicit_migration_before_any_schema_or_journal_write(tmp_path, version):
    root = tmp_path / "original Ω"
    unversioned_root(root)
    with closing(sqlite3.connect(root / "studio.sqlite")) as db:
        db.execute(f"PRAGMA user_version={version}")
    original = inventory(root)
    with pytest.raises(Problem) as error:
        Store(root)
    assert error.value.code == "MIGRATION_REQUIRED"
    assert inventory(root) == original


def test_copy_migration_retains_project_sources_identity_receipts_and_verified_backup(tmp_path):
    source, backup, target = (tmp_path / n for n in ["original Ω", "backup with spaces", "candidate Ω"])
    project, plan = unversioned_root(source)
    original = inventory(source)
    result = migrate(source, backup, target)
    assert result["status"] == "migrated" and result["sessionsInvalidated"] is True
    assert inventory(source) == original
    with closing(sqlite3.connect(backup / "files/studio.sqlite")) as db:
        assert db.execute("PRAGMA user_version").fetchone()[0] == 0
        assert db.execute("SELECT count(*) FROM records WHERE kind='session'").fetchone()[0] == 1
    store = Store(target)
    projects = Projects(store, XDLAdapter())
    after = projects.read(project["projectId"])
    assert after == project
    assert projects.adapter.compile(projects.sources(after))["planDigest"] == plan["planDigest"]
    assert store.all("session") == []
    assert store.get("operation", "op-original")["opaque"] == [1, 2]
    with store.tx() as db:
        assert db.execute("SELECT * FROM idempotency").fetchall() == [("start", "original-key", "original-fingerprint", '{"operationId":"op-original"}')]
    for name, raw in original.items():
        if name != "studio.sqlite":
            assert (backup / "files" / name).read_bytes() == raw
            assert (target / name).read_bytes() == raw
    report = json.loads((target / "migration-report.json").read_text())
    assert report["format"] == "studio.metadata-migration-report" and report["version"] == 1
    assert report["sourceSchema"] == 0 and report["targetSchema"] == 1
    assert report["semanticDiff"]["before"] == report["semanticDiff"]["after"]
    assert report["semanticDiff"]["unchanged"] is True
    assert "user_version" in report["textualDiff"] and report["sessionsInvalidated"] == 1
    assert "never-print-old-session" not in json.dumps(result) + json.dumps(report)
    assert not (target / ".recovery-incomplete").exists()
    assert not (target / "bootstrap.json").exists()


@pytest.mark.parametrize("fault", ["version", "extra-table", "trigger", "wrong-column", "active-run", "unknown-operation", "incomplete", "source-link", "nested", "existing-target"])
def test_unsafe_or_unsettled_migration_does_not_promote_a_target(tmp_path, fault):
    from xverse_studio.host.recovery import RecoveryError
    source, backup, target = (tmp_path / n for n in ["source", "backup", "target"])
    unversioned_root(source)
    with closing(sqlite3.connect(source / "studio.sqlite")) as db:
        with db:
            if fault == "version":
                db.execute("PRAGMA user_version=999")
            elif fault == "extra-table":
                db.execute("CREATE TABLE foreign_data (body TEXT)")
            elif fault == "trigger":
                db.execute("CREATE TRIGGER foreign_hook AFTER DELETE ON records BEGIN DELETE FROM idempotency; END")
            elif fault == "wrong-column":
                db.execute("ALTER TABLE records ADD COLUMN foreign_field TEXT")
            elif fault == "active-run":
                db.execute("INSERT INTO records VALUES('run','run-active',?)", (json.dumps({"state": "running", "cleanup": "not_started"}),))
            elif fault == "unknown-operation":
                db.execute("INSERT INTO records VALUES('operation','op-unknown',?)", (json.dumps({"status": "unknown"}),))
    if fault == "incomplete":
        (source / ".recovery-incomplete").write_text("preserve interrupted state")
    if fault == "source-link":
        alias = tmp_path / "alias"
        alias.symlink_to(source, target_is_directory=True)
        source = alias
    if fault == "nested":
        target = source / "nested"
    if fault == "existing-target":
        target.mkdir()
        (target / "keep").write_bytes(b"original")
    before = inventory(source)
    with pytest.raises(RecoveryError):
        migrate(source, backup, target)
    assert inventory(source) == before
    if fault == "existing-target":
        assert (target / "keep").read_bytes() == b"original"
    else:
        assert not target.exists()


def test_cli_copy_migration_returns_without_starting_a_backend_or_worker(tmp_path):
    source, backup, target = (tmp_path / n for n in ["source Ω", "backup Ω", "candidate Ω"])
    project, _ = unversioned_root(source)
    original = inventory(source)
    result = subprocess.run([sys.executable, "-I", "-m", "xverse_studio.host.launcher",
                             "--data-dir", str(target), "--migrate-from", str(source), "--migration-backup", str(backup)],
                            capture_output=True, text=True, timeout=20)
    assert result.returncode == 0, result.stderr
    assert json.loads(result.stdout)["status"] == "migrated"
    assert "never-print-old-session" not in result.stdout + result.stderr
    assert Store(target).get("project", project["projectId"])["revision"] == project["revision"]
    assert inventory(source) == original
    assert not (target / "bootstrap.json").exists()
    assert not (target / "runs").exists()


def test_migration_refuses_an_original_root_with_a_live_owner(tmp_path):
    from xverse_studio.host.ownership import own_root
    from xverse_studio.host.recovery import RecoveryError
    source, backup, target = (tmp_path / n for n in ["source", "backup", "candidate"])
    unversioned_root(source)
    original = inventory(source)
    with own_root(source), pytest.raises(RecoveryError, match="RECOVERY_ROOT_OWNED"):
        migrate(source, backup, target)
    assert inventory(source) == original and not backup.exists() and not target.exists()


@pytest.mark.parametrize("fault", ["copy", "upgrade", "report", "metadata-mismatch", "file-mismatch"])
def test_interrupted_migration_keeps_original_backup_and_ineligible_candidate(tmp_path, monkeypatch, fault):
    from xverse_studio.host import recovery as r
    source, backup, target = (tmp_path / n for n in ["source", "backup", "candidate"])
    unversioned_root(source)
    original = inventory(source)
    copy, opening, connect = r._copy, r.open_write, sqlite3.connect

    def interrupted_copy(origin, destination):
        if destination.is_relative_to(target) and fault == "copy":
            raise OSError("controlled target copy interruption")
        value = copy(origin, destination)
        if destination == target / "studio.sqlite" and fault == "metadata-mismatch":
            with closing(connect(destination)) as db:
                with db:
                    db.execute("UPDATE records SET body=? WHERE kind='operation' AND id='op-original'",
                               ('{"operationId":"op-original","status":"completed","opaque":"changed"}',))
        if destination.is_relative_to(target / "projects") and fault == "file-mismatch":
            destination.write_bytes(b"controlled changed file")
        return value

    def interrupted_open(anchor, destination, *args, **kwargs):
        if destination == target / "migration-report.json" and fault == "report":
            raise OSError("controlled report persistence interruption")
        return opening(anchor, destination, *args, **kwargs)

    class InterruptedUpgrade(sqlite3.Connection):
        def execute(self, sql, *args, **kwargs):
            if sql == "PRAGMA user_version=1" and fault == "upgrade":
                raise sqlite3.OperationalError("controlled upgrade commit failure")
            return super().execute(sql, *args, **kwargs)

    def interrupted_connect(*args, **kwargs):
        return connect(*args, factory=InterruptedUpgrade, **kwargs)

    monkeypatch.setattr(r, "_copy", interrupted_copy)
    monkeypatch.setattr(r, "open_write", interrupted_open)
    monkeypatch.setattr(sqlite3, "connect", interrupted_connect)
    expected = r.RecoveryError if fault in ("upgrade", "metadata-mismatch", "file-mismatch") else OSError
    with pytest.raises(expected):
        migrate(source, backup, target)
    assert inventory(source) == original
    with r._bound(backup):
        assert r._verified_manifest(backup, schema=0)[1]["integrity"] == "valid"
    assert (target / ".recovery-incomplete").is_file()
    refused = subprocess.run([sys.executable, "-I", "-m", "xverse_studio.host.launcher", "--data-dir", str(target)],
                             capture_output=True, text=True, timeout=10)
    assert refused.returncode != 0 and "RECOVERY_INCOMPLETE" in refused.stderr
    assert inventory(source) == original
    if fault == "copy":
        monkeypatch.undo()
        retried = migrate(source, tmp_path / "retry backup", tmp_path / "retry candidate")
        assert retried["status"] == "migrated"
        assert (target / ".recovery-incomplete").is_file() and inventory(source) == original


def test_cli_migration_requires_an_explicit_candidate_root(tmp_path):
    source, backup = tmp_path / "source", tmp_path / "backup"
    unversioned_root(source)
    original = inventory(source)
    result = subprocess.run([sys.executable, "-I", "-m", "xverse_studio.host.launcher",
                             "--migrate-from", str(source), "--migration-backup", str(backup)],
                            capture_output=True, text=True, timeout=20,
                            env=dict(os.environ, XDG_DATA_HOME=str(tmp_path / "isolated-default")))
    assert result.returncode != 0 and "--data-dir" in result.stderr
    assert not backup.exists() and inventory(source) == original


@pytest.mark.parametrize("status", ["owned", "unknown"])
def test_migration_cannot_turn_an_unsettled_lease_into_authority(tmp_path, status):
    from test_lab_lease_recovery import ledger
    from xverse_studio.host.recovery import RecoveryError
    source, backup, target = (tmp_path / n for n in ["source", "backup", "candidate"])
    unversioned_root(source)
    with closing(sqlite3.connect(source / "studio.sqlite")) as db:
        with db:
            db.execute("INSERT INTO records VALUES('lab_registry','leases',?)", (json.dumps(ledger(status)),))
    original = inventory(source)
    with pytest.raises(RecoveryError, match="RECOVERY_EXECUTION_UNSETTLED"):
        migrate(source, backup, target)
    assert inventory(source) == original and not backup.exists() and not target.exists()


def test_migration_uses_committed_wal_without_opening_original_sqlite_paths(tmp_path, monkeypatch):
    source, backup, target = (tmp_path / n for n in ["source", "backup", "candidate"])
    project, _ = unversioned_root(source)
    with closing(sqlite3.connect(source / "studio.sqlite")) as writer:
        writer.execute("PRAGMA journal_mode=WAL")
        with writer:
            writer.execute("INSERT INTO records VALUES('opaque','committed-wal',?)", ('{"exact":"preserve"}',))
        assert (source / "studio.sqlite-wal").stat().st_size > 0
        original = inventory(source)
        connect = sqlite3.connect

        def refuse_original_path(path, *args, **kwargs):
            assert str(source) not in str(path), "SQLite must open only held-descriptor private staging"
            return connect(path, *args, **kwargs)

        with monkeypatch.context() as patch:
            patch.setattr(sqlite3, "connect", refuse_original_path)
            migrate(source, backup, target)
        assert inventory(source) == original
    store = Store(target)
    assert store.get("opaque", "committed-wal") == {"exact": "preserve"}
    assert store.get("project", project["projectId"])["projectId"] == project["projectId"]


def test_migration_refuses_nontext_stored_values_with_a_typed_error(tmp_path):
    from xverse_studio.host.recovery import RecoveryError
    source, backup, target = (tmp_path / n for n in ["source", "backup", "candidate"])
    unversioned_root(source)
    with closing(sqlite3.connect(source / "studio.sqlite")) as db:
        with db:
            db.execute("INSERT INTO records VALUES('opaque','blob',?)", (sqlite3.Binary(b"not JSON text"),))
    original = inventory(source)
    with pytest.raises(RecoveryError, match="RECOVERY_DATABASE_INVALID"):
        migrate(source, backup, target)
    assert inventory(source) == original
    assert not target.exists() or (target / ".recovery-incomplete").is_file()


def test_native_completed_reference_can_be_migrated_and_explicitly_reopened_without_replay(tmp_path):
    from test_linux_project_exchange import native_workspace
    from test_native_recovery import eventually

    source, backup, target = (tmp_path / n for n in ["native source Ω", "private backup Ω", "native candidate Ω"])
    with native_workspace(source) as api:
        created = api.post("/api/v1/projects", json={"name": "Actual native migration Ω"})
        assert created.status_code == 201, created.text
        project = created.json()
        changed = api.post(f"/api/v1/projects/{project['projectId']}/edits",
                           headers={"If-Match": str(project["revision"])},
                           json={"baseRevision": project["revision"], "edits": [{"kind": "set_parameter", "parameterId": "duration", "value": 0.5}]})
        assert changed.status_code == 200, changed.text
        project = changed.json()
        compiled = api.post(f"/api/v1/projects/{project['projectId']}/compilations", json={"revision": project["revision"]}).json()
        assert compiled["valid"] is True
        preflight = api.post(f"/api/v1/projects/{project['projectId']}/preflights", json={"revision": project["revision"]}).json()
        assert preflight["status"] == "ready", preflight
        response = api.post("/api/v1/runs", headers={"Idempotency-Key": "native-before-migration"},
                            json={"snapshotId": preflight["snapshotId"], "preflightId": preflight["preflightId"]})
        assert response.status_code == 202, response.text
        run_id = response.json()["runId"]
        eventually(lambda: api.get("/api/v1/runs/" + run_id).json()["state"] == "stopped")
        run = api.get("/api/v1/runs/" + run_id).json()
        assert run["cleanup"] == "complete" and run["evidence"] == "complete", run
        original_cookie = api.cookies.get("studio_session")
        assert original_cookie
    # Controlled version conversion of an actually completed native root. No
    # historical release identity or unknown-version compatibility is invented.
    with closing(sqlite3.connect(source / "studio.sqlite")) as db:
        db.execute("PRAGMA journal_mode=DELETE")
        db.execute("PRAGMA user_version=0")
    original = inventory(source)
    result = subprocess.run([sys.executable, "-I", "-m", "xverse_studio.host.launcher",
                             "--data-dir", str(target), "--migrate-from", str(source), "--migration-backup", str(backup)],
                            capture_output=True, text=True, timeout=20)
    assert result.returncode == 0, result.stderr
    assert inventory(source) == original and not (target / "bootstrap.json").exists()
    with native_workspace(target) as reopened:
        after = reopened.get("/api/v1/projects/" + project["projectId"]).json()
        assert {k: v["content"] for k, v in after["documents"].items()} == {k: v["content"] for k, v in project["documents"].items()}
        assert reopened.post(f"/api/v1/projects/{after['projectId']}/compilations", json={"revision": after["revision"]}).json()["plan"] == compiled["plan"]
        rows = reopened.get("/api/v1/runs").json()["items"]
        assert len(rows) == 1 and rows[0]["runId"] == run_id and rows[0]["state"] == "stopped"
        assert reopened.get("/api/v1/session", headers={"Cookie": "studio_session=" + original_cookie}).status_code == 401
        for folder in ["snapshots", "runs"]:
            for name, raw in original.items():
                if name.startswith(folder + "/"):
                    assert (target / name).read_bytes() == raw
    assert inventory(source) == original


@pytest.mark.parametrize("field,value", [("version", True), ("databaseSchema", False)])
def test_migration_backup_rejects_boolean_version_fields_before_target_allocation(tmp_path, monkeypatch, field, value):
    from xverse_studio.host import recovery as r
    source, backup, target = (tmp_path / n for n in ["source", "backup", "candidate"])
    unversioned_root(source)
    original = inventory(source)
    backup_full = r._backup_full

    def forged_version(*args, **kwargs):
        result = backup_full(*args, **kwargs)
        file = backup / "manifest.json"
        manifest = json.loads(file.read_text())
        manifest[field] = value
        file.write_text(json.dumps(manifest))
        return result

    monkeypatch.setattr(r, "_backup_full", forged_version)
    with pytest.raises(r.RecoveryError, match="RECOVERY_SCHEMA_UNSUPPORTED"):
        migrate(source, backup, target)
    assert inventory(source) == original and not target.exists()
