"""Independent regressions for recorded M0/M1 findings; isolated owned assets only."""

import base64
import io
import json
import sqlite3
import time
import zipfile

import psutil
import pytest

from xverse_studio.security.files import safe_name
from xverse_studio.storage.core import Problem, Store, atomic, canonical
from xverse_studio.projects.service import Projects
from xverse_studio.runs.service import Runs
from xverse_studio.xdl import XDLAdapter


def new_project(client):
    response = client.post("/api/v1/projects", json={"name": "Independent review regression"})
    assert response.status_code == 201, response.text
    return response.json()


def test_uri_credentials_reject_source_import_and_export_without_echo(client):
    project = new_project(client)
    project_id = project["projectId"]
    document_id = next(iter(project["documents"]))
    credential = "https://synthetic-user:review-secret-marker@example.invalid"
    source = project["documents"][document_id]["content"] + "\n# " + credential + "\n"
    response = client.put(f"/api/v1/projects/{project_id}/documents/{document_id}",
                          json={"content": source, "format": "yaml"}, headers={"If-Match": str(project["revision"])})
    assert response.status_code == 422
    assert response.json()["code"] == "CREDENTIAL_REJECTED"
    assert "review-secret-marker" not in response.text
    target = io.BytesIO()
    with zipfile.ZipFile(target, "w") as archive:
        archive.writestr("README.md", credential)
    response = client.post("/api/v1/projects/imports", json={"archiveBase64": base64.b64encode(target.getvalue()).decode()})
    assert response.status_code == 422
    assert response.json()["code"] == "CREDENTIAL_REJECTED"
    assert "review-secret-marker" not in response.text
    # An older persisted input may predate the new admission rule. Export must recheck it.
    store = client.app.state.studio.store
    record = store.get("project", project_id)
    record["supportingFiles"]["README.md"] = credential
    store.put("project", project_id, record)
    response = client.post(f"/api/v1/projects/{project_id}/exports", json={"revision": project["revision"]},
                           headers={"Idempotency-Key": "review-export-credential"})
    assert response.status_code == 422
    assert "review-secret-marker" not in response.text


def test_portable_paths_reject_all_windows_forbidden_filename_characters():
    for character in '<>"|?*':
        with pytest.raises(Problem) as error:
            safe_name("xdl/bad" + character + ".yaml")
        assert error.value.code == "UNSAFE_PATH"


def test_nonempty_artifact_lock_survives_export_exactly(client):
    project = new_project(client)
    store = client.app.state.studio.store
    record = store.get("project", project["projectId"])
    original = json.dumps({"formatVersion": "1.0", "entries": [{
        "artifactId": "restricted-reference", "digest": "sha256:" + "b" * 64,
        "availability": "missing", "distribution": "restricted"}]}, indent=3) + "\n"
    record["supportingFiles"]["artifacts.lock.json"] = original
    store.put("project", project["projectId"], record)
    response = client.post(f"/api/v1/projects/{project['projectId']}/exports", json={"revision": project["revision"]},
                           headers={"Idempotency-Key": "review-lock-export"})
    assert response.status_code == 202, response.text
    bundle = client.get(response.json()["result"]["downloadUrl"])
    with zipfile.ZipFile(io.BytesIO(bundle.content)) as archive:
        assert archive.read("artifacts.lock.json").decode() == original


def test_metadata_write_failure_preserves_prior_revision_and_allows_retry(tmp_path, monkeypatch):
    store = Store(tmp_path)
    projects = Projects(store, XDLAdapter())
    project = projects.create("Metadata write failure")
    document_id = next(iter(project["documents"]))
    source = project["documents"][document_id]["content"]
    put = store.put

    def fail(kind, identifier, body, db=None):
        result = put(kind, identifier, body, db)
        if kind == "project" and body["revision"] == 2:
            raise OSError("synthetic metadata write error")
        return result

    with monkeypatch.context() as patch:
        patch.setattr(store, "put", fail)
        with pytest.raises(OSError):
            projects.save(project["projectId"], document_id, 1, source + "\n# changed\n", "yaml")
    assert projects.read(project["projectId"])["revision"] == 1
    assert not projects._dir(project["projectId"], 2).exists()
    assert projects.save(project["projectId"], document_id, 1, source + "\n# retry\n", "yaml")["revision"] == 2


def test_sqlite_commit_failure_preserves_prior_revision_and_allows_retry(tmp_path, monkeypatch):
    store = Store(tmp_path)
    projects = Projects(store, XDLAdapter())
    project = projects.create("SQLite commit failure")
    document_id = next(iter(project["documents"]))
    source = project["documents"][document_id]["content"]
    connect = sqlite3.connect

    class ConnectionProxy:
        def __init__(self, connection):
            self.connection = connection

        def __getattr__(self, name):
            return getattr(self.connection, name)

        def commit(self):
            raise sqlite3.OperationalError("synthetic SQLite commit failure")

    with monkeypatch.context() as patch:
        patch.setattr(sqlite3, "connect", lambda *args, **kwargs: ConnectionProxy(connect(*args, **kwargs)))
        with pytest.raises(sqlite3.OperationalError):
            projects.save(project["projectId"], document_id, 1, source + "\n# changed\n", "yaml")
    assert projects.read(project["projectId"])["revision"] == 1
    assert not projects._dir(project["projectId"], 2).exists()
    assert projects.save(project["projectId"], document_id, 1, source + "\n# retry\n", "yaml")["revision"] == 2


def test_error_after_successful_sqlite_commit_never_deletes_committed_sources(tmp_path, monkeypatch):
    store = Store(tmp_path)
    projects = Projects(store, XDLAdapter())
    project = projects.create("Acknowledgement lost after metadata commit")
    document_id = next(iter(project["documents"]))
    source = project["documents"][document_id]["content"]
    connect = sqlite3.connect

    class ConnectionProxy:
        def __init__(self, connection):
            self.connection = connection

        def __getattr__(self, name):
            return getattr(self.connection, name)

        def commit(self):
            self.connection.commit()
            raise sqlite3.OperationalError("synthetic acknowledgement loss after commit")

    with monkeypatch.context() as patch:
        patch.setattr(sqlite3, "connect", lambda *args, **kwargs: ConnectionProxy(connect(*args, **kwargs)))
        with pytest.raises(sqlite3.OperationalError):
            projects.save(project["projectId"], document_id, 1, source + "\n# committed\n", "yaml")
    recovered = projects.read(project["projectId"])
    assert recovered["revision"] == 2
    assert recovered["documents"][document_id]["content"] == source + "\n# committed\n"
    assert projects._dir(project["projectId"], 1).exists()
    assert projects._dir(project["projectId"], 2).exists()


def test_capability_identity_changes_with_effective_provider_source_without_source_mutation(monkeypatch):
    from pathlib import Path
    from xverse_studio.providers import registry
    before = registry.capability_digest()
    read = Path.read_bytes

    def changed(path):
        data = read(path)
        if path.name == "worker.py" and path.parent.name == "providers":
            return data + b"\n# synthetic implementation identity change\n"
        return data

    with monkeypatch.context() as patch:
        patch.setattr(Path, "read_bytes", changed)
        assert registry.capability_digest() != before
    assert registry.capability_digest() == before


def test_unknown_and_wrong_kind_selection_cannot_preflight_or_compile(client):
    project = new_project(client)
    project_id = project["projectId"]
    for route in ("preflights", "compilations"):
        for fields in ({"scenarioRef": "xdl://org.missing/scenario/missing"},
                       {"deploymentRef": "xdl://org.missing/deployment/missing"},
                       {"scenarioRef": "xdl://org.xverse.studio.process-control/system/reference-loop"}):
            response = client.post(f"/api/v1/projects/{project_id}/{route}", json={"revision": project["revision"], **fields})
            assert response.status_code == 422, response.text
            assert response.json()["code"] == "SELECTION_UNRESOLVED"


def test_external_source_change_blocks_all_authoritative_revision_operations(client):
    project = new_project(client)
    project_id = project["projectId"]
    document_id = next(identifier for identifier, doc in project["documents"].items() if doc["path"].endswith("scenario.xdl.yaml"))
    path = client.app.state.studio.projects.document_path(project_id, document_id)
    original = path.read_text()
    changed = original.replace("value: 0.8", "value: 0.7")
    assert changed != original
    path.write_text(changed)
    for route in ("validations", "compilations", "preflights", "exports"):
        response = client.post(f"/api/v1/projects/{project_id}/{route}", json={"revision": project["revision"]},
                               headers={"Idempotency-Key": "review-external-" + route})
        assert response.status_code == 412, response.text
        assert response.json()["code"] == "REVISION_CONFLICT"
    assert path.read_text() == changed
    assert client.get(f"/api/v1/projects/{project_id}").json()["revision"] == 1


def test_post_spawn_lost_birth_is_unknown_then_recovers_one_exact_owned_worker(tmp_path, monkeypatch):
    from xverse_studio.runs import service as run_module
    store = Store(tmp_path)
    adapter = XDLAdapter()
    projects = Projects(store, adapter)
    project = projects.create("Owned lost acknowledgement")
    runs = Runs(store, projects, adapter)
    preflight = runs.preflight(project["projectId"], {"revision": 1})
    payload = {"snapshotId": preflight["snapshotId"], "preflightId": preflight["preflightId"]}
    process_type = psutil.Process
    popen = run_module.subprocess.Popen
    children = []
    births = []

    def spawn(*args, **kwargs):
        # Durable launch authority must precede effects.
        records = store.all("run")
        assert records[0].get("ownerDigest")
        child = popen(*args, **kwargs)
        children.append(child)
        return child

    def lose_first_birth(pid):
        births.append(pid)
        if len(births) == 1:
            raise psutil.AccessDenied(pid)
        return process_type(pid)

    try:
        with monkeypatch.context() as patch:
            patch.setattr(run_module.subprocess, "Popen", spawn)
            patch.setattr(run_module.psutil, "Process", lose_first_birth)
            result = runs.start("review-owner", "review-once", payload)
            record = store.get("run", result["runId"])
            assert record["state"] == "unknown"
            assert store.get("operation", result["operationId"])["status"] == "unknown"
            assert record["ownerDigest"]
            assert runs.start("review-owner", "review-once", payload) == result
        deadline = time.monotonic() + 8
        while time.monotonic() < deadline:
            recovered = runs.read(result["runId"])
            if recovered["state"] == "running":
                break
            time.sleep(.05)
        assert recovered["state"] == "running", recovered
        assert recovered["pid"] == children[0].pid
        assert len(children) == 1
        assert runs.start("review-owner", "review-once", payload) == result
    finally:
        runs.shutdown()
        for child in children:
            # Original Popen handle identifies only this test's child. No PID/name-based killing.
            child.wait(timeout=8)


@pytest.mark.parametrize("extra_argument", [False, True])
def test_reconciliation_does_not_adopt_a_matching_pid_with_wrong_argv(tmp_path, monkeypatch, extra_argument):
    from xverse_studio.runs import service as run_module
    store = Store(tmp_path)
    projects = Projects(store, XDLAdapter())
    runs = Runs(store, projects, XDLAdapter())
    run_id, operation_id = "run-review", "operation-review"
    record = {"runId": run_id, "operationId": operation_id, "state": "unknown", "ownerDigest": "expected-digest", "createdAt": 0}
    store.put("run", run_id, record)
    store.put("operation", operation_id, {"operationId": operation_id, "status": "unknown"})
    state = {"state": "running", "ownerDigest": "expected-digest", "pid": 12345, "createTime": 123.0}
    atomic(runs.directory(run_id) / "state.json", canonical(state).encode())

    class UnrelatedProcess:
        def create_time(self):
            return 123.0

        def cmdline(self):
            argv = ["python", "-m", "unrelated_workload", str(runs.directory(run_id))]
            if extra_argument:
                argv.append("xverse_studio.providers.worker")
            return argv

        def is_running(self):
            return True

        def status(self):
            return psutil.STATUS_RUNNING

    monkeypatch.setattr(run_module.psutil, "Process", lambda pid: UnrelatedProcess())
    result = runs.read(run_id)
    assert result["state"] == "unknown"
    assert "pid" not in result


def test_stop_parameters_reject_before_delegation_even_on_direct_api(client):
    store = client.app.state.studio.store
    run_id, operation_id = "run-parameters", "operation-parameters"
    # An unresolved owned fixture suffices: the parameter gate runs before an active effect.
    store.put("run", run_id, {"runId": run_id, "operationId": operation_id, "state": "unknown", "stateVersion": 0,
                              "cleanup": "unknown", "evidence": "partial", "createdAt": 0, "capabilities": ["stop", "cancel"]})
    store.put("operation", operation_id, {"operationId": operation_id, "kind": "start", "runId": run_id, "status": "unknown"})
    before = len(store.all("operation"))
    response = client.post(f"/api/v1/runs/{run_id}/commands", headers={"Idempotency-Key": "review-unsupported-command"},
                           json={"kind": "cancel", "expectedStateVersion": 0, "parameters": {"forceKill": True}})
    assert response.status_code == 422
    assert response.json()["code"] == "COMMAND_PARAMETERS_UNSUPPORTED"
    assert len(store.all("operation")) == before
    assert not (client.app.state.studio.runs.directory(run_id) / "command.json").exists()
