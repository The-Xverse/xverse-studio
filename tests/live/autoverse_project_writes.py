"""Actual Autoverse project publication under native owned-directory faults."""

from contextlib import contextmanager
import json

from fastapi.testclient import TestClient
import pytest

import autoverse_provider_admission as enrollment
from autoverse_provider_admission import application, project
from xverse_studio.projects import service
from xverse_studio.security import managed_io

target = enrollment.target


@contextmanager
def signed_in(app):
    with TestClient(app, raise_server_exceptions=False) as api:
        api.headers["Origin"] = "http://testserver"
        response = api.post(
            "/api/v1/session",
            json={"bootstrapToken": "owned-autoverse-contract-check"},
        )
        assert response.status_code == 200
        api.headers["X-CSRF-Token"] = response.json()["csrfToken"]
        yield api


@pytest.mark.parametrize("foreign_revision", [False, True])
def test_autoverse_parent_swap_refuses_publication_and_preserves_foreign_directory(
    target, tmp_path, monkeypatch, foreign_revision
):
    provider, blueprint = target
    app = application(tmp_path / "Native Autoverse writes Ω", provider)
    with signed_in(app) as api:
        original = project(api, blueprint)
        pid = original["projectId"]
        docid, document = next(iter(original["documents"].items()))
        revisions = app.state.studio.store.root / "projects" / pid / "revisions"
        retained = revisions.with_name("retained-original-revisions")
        outside = tmp_path / "Foreign owned directory Ω"
        outside.mkdir()
        sentinel = outside / "keep.txt"
        sentinel.write_text("Original foreign bytes must survive")
        foreign = outside / "2"
        if foreign_revision:
            foreign.mkdir()
        original_foreign_inode = foreign.stat().st_ino if foreign_revision else None
        original_atomic = service.atomic
        observed = {"faultDelivered": False, "foreignWriteObserved": False}

        def swap_before_write(path, data):
            if not observed["faultDelivered"] and path.is_relative_to(revisions):
                revisions.rename(retained)
                revisions.symlink_to(outside, target_is_directory=True)
                observed["faultDelivered"] = True
            result = original_atomic(path, data)
            if any(p.is_file() and p != sentinel for p in outside.rglob("*")):
                observed["foreignWriteObserved"] = True
            return result

        monkeypatch.setattr(service, "atomic", swap_before_write)
        try:
            response = api.put(
                f"/api/v1/projects/{pid}/documents/{docid}",
                headers={"If-Match": str(original["revision"])},
                json={
                    "content": document["content"] + "\n# inert owned edit\n",
                    "format": document["format"],
                },
            )
        finally:
            if observed["faultDelivered"]:
                assert revisions.is_symlink()
                revisions.unlink()
                retained.rename(revisions)
        observed.update(
            status=response.status_code,
            code=response.json().get("code"),
            foreignRevisionPreserved=(
                foreign.exists() and foreign.stat().st_ino == original_foreign_inode
                if foreign_revision
                else not foreign.exists()
            ),
        )
        (tmp_path / "write-fault-observation.json").write_text(
            json.dumps(observed, indent=2) + "\n"
        )
        assert observed["faultDelivered"]
        assert response.status_code in (409, 412), observed
        assert not observed["foreignWriteObserved"], observed
        assert observed["foreignRevisionPreserved"], observed
        assert sentinel.read_text() == "Original foreign bytes must survive"
        current = api.get(f"/api/v1/projects/{pid}")
        assert current.status_code == 200 and current.json() == original
        assert app.state.studio.store.all("run") == []


@pytest.mark.parametrize("failure", ["before-write", "after-write", "metadata"])
def test_autoverse_failed_publication_retains_prior_revision(
    target, tmp_path, monkeypatch, failure
):
    provider, blueprint = target
    app = application(tmp_path / "Autoverse failed publication Ω", provider)
    with signed_in(app) as api:
        p = project(api, blueprint)
        pid = p["projectId"]
        docid, document = next(iter(p["documents"].items()))
        root = app.state.studio.store.root / "projects" / pid / "revisions"
        atomic, put = service.atomic, app.state.studio.store.put
        delivered = []

        def failed_write(path, data):
            if path.is_relative_to(root):
                delivered.append(True)
                if failure == "after-write":
                    atomic(path, data)
                raise OSError("owned-private-marker: publication unavailable")
            return atomic(path, data)

        def failed_metadata(kind, identity, body, db=None):
            if kind == "project" and identity == pid and body["revision"] == 2:
                assert (root / "2").is_dir()
                delivered.append(True)
                raise OSError("owned-private-marker: metadata unavailable")
            return put(kind, identity, body, db)

        if failure == "metadata":
            monkeypatch.setattr(app.state.studio.store, "put", failed_metadata)
        else:
            monkeypatch.setattr(service, "atomic", failed_write)
        response = api.put(
            f"/api/v1/projects/{pid}/documents/{docid}",
            headers={"If-Match": str(p["revision"])},
            json={
                "content": document["content"] + "\n# inert edit\n",
                "format": document["format"],
            },
        )
        assert delivered and response.status_code == 500
        assert "owned-private-marker" not in response.text
        assert api.get(f"/api/v1/projects/{pid}").json() == p
        assert [path.name for path in root.iterdir()] == ["1"]
        assert app.state.studio.store.all("run") == []


def test_autoverse_publication_never_replaces_a_late_existing_directory(
    target, tmp_path, monkeypatch
):
    provider, blueprint = target
    app = application(tmp_path / "Autoverse publication collision Ω", provider)
    with signed_in(app) as api:
        p = project(api, blueprint)
        pid = p["projectId"]
        docid, document = next(iter(p["documents"].items()))
        publish = service.publish_directory
        observed = {}

        def occupied(root, source, target, **options):
            target.mkdir()
            observed["identity"] = target.stat().st_ino
            observed["path"] = target
            return publish(root, source, target, **options)

        monkeypatch.setattr(service, "publish_directory", occupied)
        response = api.put(
            f"/api/v1/projects/{pid}/documents/{docid}",
            headers={"If-Match": str(p["revision"])},
            json={
                "content": document["content"] + "\n# inert edit\n",
                "format": document["format"],
            },
        )
        assert response.status_code == 409 and observed
        assert observed["path"].stat().st_ino == observed["identity"]
        assert list(observed["path"].iterdir()) == []
        assert api.get(f"/api/v1/projects/{pid}").json() == p


def test_autoverse_short_native_write_cannot_publish_truncated_source(
    target, tmp_path, monkeypatch
):
    provider, blueprint = target
    app = application(tmp_path / "Autoverse short native write Ω", provider)
    with signed_in(app) as api:
        p = project(api, blueprint)
        pid = p["projectId"]
        docid, document = next(iter(p["documents"].items()))
        fileio = managed_io.io.FileIO
        delivered = []

        @contextmanager
        def short_write(*args, **kwargs):
            with fileio(*args, **kwargs) as stream:
                if len(args) > 1 and args[1] == "wb":

                    class Writer:
                        def write(self, data):
                            delivered.append(True)
                            return stream.write(data[: len(data) // 2])

                        def flush(self):
                            stream.flush()

                    yield Writer()
                else:
                    yield stream

        monkeypatch.setattr(managed_io.io, "FileIO", short_write)
        response = api.put(
            f"/api/v1/projects/{pid}/documents/{docid}",
            headers={"If-Match": str(p["revision"])},
            json={
                "content": document["content"] + "\n# inert edit\n",
                "format": document["format"],
            },
        )
        assert delivered and response.status_code == 409
        assert api.get(f"/api/v1/projects/{pid}").json() == p
        directory = app.state.studio.store.root / "projects" / pid / "revisions"
        assert [path.name for path in directory.iterdir()] == ["1"]


def test_autoverse_unavailable_native_publication_refuses_without_overwriting_fallback(
    target, tmp_path, monkeypatch
):
    provider, blueprint = target
    app = application(tmp_path / "Autoverse unavailable native publication Ω", provider)
    with signed_in(app) as api:
        p = project(api, blueprint)
        pid = p["projectId"]
        docid, document = next(iter(p["documents"].items()))
        monkeypatch.setattr(managed_io.ctypes, "CDLL", lambda *a, **k: object())
        response = api.put(
            f"/api/v1/projects/{pid}/documents/{docid}",
            headers={"If-Match": str(p["revision"])},
            json={
                "content": document["content"] + "\n# inert edit\n",
                "format": document["format"],
            },
        )
        assert (
            response.status_code == 503
            and response.json()["code"] == "PLATFORM_IO_UNAVAILABLE"
        )
        assert api.get(f"/api/v1/projects/{pid}").json() == p
        directory = app.state.studio.store.root / "projects" / pid / "revisions"
        assert [path.name for path in directory.iterdir()] == ["1"]


def test_autoverse_native_source_publication_preserves_plan_and_private_modes(
    target, tmp_path
):
    provider, blueprint = target
    app = application(tmp_path / "Private Autoverse publication Ω", provider)
    with signed_in(app) as api:
        original = project(api, blueprint)
        pid = original["projectId"]
        before = api.post(
            f"/api/v1/projects/{pid}/compilations",
            json={"revision": original["revision"]},
        )
        assert before.status_code == 200 and before.json()["valid"]
        docid, document = next(iter(original["documents"].items()))
        content = document["content"] + "\n# command-like content remains inert\n"
        saved = api.put(
            f"/api/v1/projects/{pid}/documents/{docid}",
            headers={"If-Match": str(original["revision"])},
            json={"content": content, "format": document["format"]},
        )
        assert saved.status_code == 200, saved.text
        p = saved.json()
        assert p["documents"][docid]["content"] == content
        compiled = api.post(
            f"/api/v1/projects/{pid}/compilations", json={"revision": p["revision"]}
        )
        assert compiled.status_code == 200 and compiled.json()["valid"]
        assert compiled.json()["planDigest"] == before.json()["planDigest"]
        directory = (
            app.state.studio.store.root
            / "projects"
            / pid
            / "revisions"
            / str(p["revision"])
        )
        assert directory.stat().st_mode & 0o777 == 0o700
        assert all(
            path.stat().st_mode & 0o777 == 0o600
            for path in directory.rglob("*")
            if path.is_file()
        )
        assert api.get(f"/api/v1/projects/{pid}").json() == p
        assert app.state.studio.store.all("run") == []
