"""Failure and corruption boundaries for private declaration head publication."""

from contextlib import contextmanager
import json
import sqlite3

import pytest

from test_local_bindings import entries, project, put
from xverse_studio.storage.core import digest


def initialized(client, tmp_path):
    p = project(client)
    result = put(client, p["projectId"], entries(tmp_path))
    assert result.status_code == 200, result.text
    store = client.app.state.studio.store
    head = store.get("project_local_bindings", p["projectId"])
    return p, head, store.root / head["sidecar"]


@pytest.mark.parametrize("fault", ["bytes", "missing", "symlink", "oversize", "bad-json", "future-file", "foreign-document", "wrong-revision", "future-head", "foreign-head", "unsafe-head", "malformed-head"])
def test_unverifiable_private_state_never_becomes_empty_or_overwritten(client, tmp_path, fault):
    p, head, sidecar = initialized(client, tmp_path)
    store = client.app.state.studio.store
    outside = tmp_path / "outside-owned.json"
    outside.write_bytes(b"never-follow-declared-or-foreign-files")
    if fault == "bytes":
        sidecar.write_bytes(sidecar.read_bytes() + b"\n")
    elif fault == "missing":
        sidecar.unlink()
    elif fault == "symlink":
        sidecar.unlink()
        sidecar.symlink_to(outside)
    elif fault == "oversize":
        sidecar.write_bytes(b"x" * (65536 + 1))
    elif fault in ("bad-json", "future-file", "foreign-document", "wrong-revision"):
        data = json.loads(sidecar.read_text())
        if fault == "future-file":
            data["formatVersion"] = "99.0"
        elif fault == "foreign-document":
            data["projectId"] = "prj-another-project"
        elif fault == "wrong-revision":
            data["bindingRevision"] = True
        sidecar.write_text("{invalid" if fault == "bad-json" else json.dumps(data))
        head["digest"] = digest(sidecar.read_bytes())
        store.put("project_local_bindings", p["projectId"], head)
    elif fault == "future-head":
        head["formatVersion"] = "99.0"
        store.put("project_local_bindings", p["projectId"], head)
    elif fault == "foreign-head":
        head["projectId"] = "prj-another-project"
        store.put("project_local_bindings", p["projectId"], head)
    elif fault == "unsafe-head":
        head["sidecar"] = "../outside-owned.json"
        store.put("project_local_bindings", p["projectId"], head)
    else:
        with store.tx() as db:
            db.execute("UPDATE records SET body=? WHERE kind='project_local_bindings' AND id=?", ("{unreadable head", p["projectId"]))
    path = f"/api/v1/projects/{p['projectId']}/local-bindings"
    before = sidecar.read_bytes() if sidecar.exists() and not sidecar.is_symlink() else None
    observed = client.get(path)
    assert observed.status_code == 409 and observed.json()["code"].startswith("LOCAL_BINDINGS_"), observed.text
    assert "never-follow" not in observed.text
    refused = put(client, p["projectId"], [], revision=1)
    assert refused.status_code == 409 and refused.json()["code"].startswith("LOCAL_BINDINGS_"), refused.text
    assert client.get("/api/v1/projects/" + p["projectId"]).json()["sourceIntegrity"] == "intact"
    assert outside.read_bytes() == b"never-follow-declared-or-foreign-files"
    if before is not None:
        assert sidecar.read_bytes() == before


@pytest.mark.parametrize("fault", ["write", "partial-write", "metadata", "commit", "after-commit"])
def test_binding_publication_failures_preserve_durable_head_and_allow_explicit_retry(client, tmp_path, monkeypatch, fault):
    from xverse_studio.projects import local_bindings as module
    p, head, sidecar = initialized(client, tmp_path)
    store = client.app.state.studio.store
    old = client.get(f"/api/v1/projects/{p['projectId']}/local-bindings").json()
    original = sidecar.read_bytes()
    new = entries(tmp_path)
    new[0]["path"] += ".new"
    real_open, real_put, connect = module.open_write, store.put, sqlite3.connect
    fired = []

    @contextmanager
    def failed_write(*args, **kwargs):
        if fault == "write":
            fired.append(True)
            raise OSError("controlled private write failure")
        with real_open(*args, **kwargs) as stream:
            if fault == "partial-write":
                stream.write(b"incomplete private prepared bytes")
                fired.append(True)
                raise OSError("controlled partial write failure")
            yield stream

    def failed_put(kind, identity, body, db=None):
        result = real_put(kind, identity, body, db)
        if fault == "metadata" and kind == "project_local_bindings":
            fired.append(True)
            raise OSError("controlled head persistence failure")
        return result

    class FailedCommit(sqlite3.Connection):
        touched = False
        def execute(self, sql, parameters=(), /):
            if sql.startswith("INSERT INTO records") and parameters and parameters[0] == "project_local_bindings":
                self.touched = True
            return super().execute(sql, parameters)
        def commit(self):
            if self.touched and fault in ("commit", "after-commit"):
                fired.append(True)
                if fault == "after-commit":
                    super().commit()
                raise OSError("controlled actual commit acknowledgement failure")
            return super().commit()

    with monkeypatch.context() as patch:
        patch.setattr(module, "open_write", failed_write)
        patch.setattr(store, "put", failed_put)
        patch.setattr(sqlite3, "connect", lambda *a, **kw: connect(*a, factory=FailedCommit, **kw))
        response = put(client, p["projectId"], new, revision=1)
        assert response.status_code == 503, response.text
    assert fired and sidecar.read_bytes() == original
    current = client.get(f"/api/v1/projects/{p['projectId']}/local-bindings")
    assert current.status_code == 200
    if fault == "after-commit":
        assert current.json()["bindingRevision"] == 2 and current.json()["bindings"] == new
        assert put(client, p["projectId"], new, revision=1).status_code == 412
    else:
        assert current.json() == old
        assert store.get("project_local_bindings", p["projectId"]) == head
        retry = put(client, p["projectId"], new, revision=1)
        assert retry.status_code == 200 and retry.json()["bindingRevision"] == 2, retry.text
    assert sidecar.read_bytes() == original


def test_pending_project_retirement_blocks_new_private_publication(client, tmp_path):
    p = project(client)
    store = client.app.state.studio.store
    store.put("retentionProjectStage", "controlled-stage", {"resourceId": p["projectId"], "phase": "quarantined"})
    response = put(client, p["projectId"], entries(tmp_path))
    assert response.status_code == 409 and response.json()["code"] == "LOCAL_BINDINGS_BUSY", response.text
    assert store.all("project_local_bindings") == []


def test_project_retirement_removes_its_private_head_with_the_project(client, tmp_path):
    from test_retention_failures import plan, apply
    p, _, _ = initialized(client, tmp_path)
    response = apply(client, plan(client, p["projectId"]), "retire-owned-bindings")
    assert response.status_code == 202 and response.json()["status"] == "complete", response.text
    assert client.app.state.studio.store.all("project_local_bindings") == []
    assert client.get(f"/api/v1/projects/{p['projectId']}/local-bindings").status_code == 404


def test_binding_save_invalidates_an_older_project_retirement_plan(client, tmp_path):
    from test_retention_failures import plan, apply
    p = project(client)
    before = plan(client, p["projectId"])
    assert put(client, p["projectId"], entries(tmp_path)).status_code == 200
    response = apply(client, before, "stale-before-private-save")
    assert response.status_code == 409, response.text
    assert client.get(f"/api/v1/projects/{p['projectId']}/local-bindings").json()["bindingRevision"] == 1


@pytest.mark.parametrize("operation", ["read", "write"])
def test_missing_native_secure_io_is_explicit_and_never_advances_head(client, tmp_path, monkeypatch, operation):
    from xverse_studio.projects import local_bindings as module
    from xverse_studio.security.managed_io import SafeIOError
    p, head, sidecar = initialized(client, tmp_path)
    original = sidecar.read_bytes()

    def unavailable(*args, **kwargs):
        raise SafeIOError("SECURE_IO_UNAVAILABLE")

    with monkeypatch.context() as patch:
        patch.setattr(module, "open_" + operation, unavailable)
        response = client.get(f"/api/v1/projects/{p['projectId']}/local-bindings") if operation == "read" else put(client, p["projectId"], [], revision=1)
        assert response.status_code == 503 and response.json()["code"] == "PLATFORM_IO_UNAVAILABLE", response.text
    assert sidecar.read_bytes() == original
    assert client.app.state.studio.store.get("project_local_bindings", p["projectId"]) == head
