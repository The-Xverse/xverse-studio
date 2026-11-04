"""Native exchange refusals against enrolled and recorded actual Autoverse.

The recorded fixture is an exact stopped complete-demo capture, never a running
provider or Argus admission. Every fault modifies only a fresh owned test copy.
"""

import base64
import io
import inspect
import json
import os
from pathlib import Path
import shutil
import sqlite3
import zipfile

import pytest

import autoverse_provider_admission as enrollment
from autoverse_provider_admission import application, authenticated, project
from xverse_studio.storage.core import canonical, digest

target = enrollment.target
MAXIMUM = 16 * 1024 * 1024


def unpack(raw):
    with zipfile.ZipFile(io.BytesIO(raw)) as archive:
        return {name: archive.read(name) for name in archive.namelist()}


@pytest.mark.parametrize("fault", ["none", "file-link", "parent-link", "hardlink", "oversized"])
def test_autoverse_project_download_acquires_bounded_original_regular_bytes(
    target, tmp_path, fault
):
    provider, blueprint = target
    app = application(tmp_path / "Autoverse download Ω", provider)
    with authenticated(app) as api:
        p = project(api, blueprint)
        operation = api.post(
            f"/api/v1/projects/{p['projectId']}/exports",
            headers={"Idempotency-Key": "owned-autoverse-export"},
            json={"revision": p["revision"]},
        )
        assert operation.status_code == 202, operation.text
        op = operation.json()
        store = app.state.studio.store
        path = store.root / "exports" / (op["operationId"] + ".zip")
        original = path.read_bytes()
        if fault == "file-link":
            alternate = store.root / "original-export.zip"
            path.rename(alternate)
            path.symlink_to(alternate)
        elif fault == "parent-link":
            alternate = store.root / "original-exports"
            path.parent.rename(alternate)
            path.parent.symlink_to(alternate, target_is_directory=True)
        elif fault == "hardlink":
            os.link(path, store.root / "second-export.zip")
        elif fault == "oversized":
            with path.open("wb") as stream:
                stream.truncate(MAXIMUM + 1)
        response = api.get(op["result"]["downloadUrl"])
        if fault == "none":
            assert response.status_code == 200, response.text
            assert response.content == original
            assert digest(original) == op["result"]["digest"]
            files = unpack(original)
            for document in p["documents"].values():
                assert files[document["path"]] == document["content"].encode()
        else:
            assert response.status_code == (413 if fault == "oversized" else 422)
            assert response.json()["code"] == (
                "LIMIT_EXCEEDED" if fault == "oversized" else "EVIDENCE_INVALID"
            )
        assert store.all("run") == []
        assert store.get("operation", op["operationId"]) == op


@pytest.fixture
def recorded_demo(tmp_path):
    """Read only the explicitly nominated actual complete-demo recording."""
    receipt = os.environ.get("STUDIO_AUTOVERSE_TEST_INSTALLATION")
    source = os.environ.get("STUDIO_AUTOVERSE_RECORDED_ROOT")
    if not receipt or not source:
        pytest.fail("Explicit native enrollment and complete Autoverse recording are required")
    source = Path(source)
    provider = enrollment.AutoverseProvider(json.loads(Path(receipt).read_bytes())["classic"])
    app = application(tmp_path / "Recorded Autoverse exchange Ω", provider)
    store = app.state.studio.store
    with sqlite3.connect((source / "studio.sqlite").as_uri() + "?mode=ro", uri=True) as db:
        rows = db.execute(
            "SELECT kind,id,body FROM records WHERE kind IN ('run','snapshot','command','operation')"
        ).fetchall()
    runs = [json.loads(body) for kind, _, body in rows if kind == "run"]
    assert len(runs) == 1
    run = runs[0]
    assert run["providerId"] == "autoverse.demo"
    assert run["state"] == "stopped" and run["cleanup"] == "complete"
    assert run["evidenceScope"] == "external_demo" and run["journalDigest"]
    root = store.root / "runs" / run["runId"]
    root.mkdir(parents=True)
    for name in ("state.json", "evidence.jsonl"):
        shutil.copyfile(source / "runs" / run["runId"] / name, root / name)
    snapshot_root = store.root / "snapshots" / run["snapshotId"]
    snapshot_root.mkdir(parents=True)
    shutil.copyfile(source / "snapshots" / run["snapshotId"] / "snapshot.json", snapshot_root / "snapshot.json")
    assert digest((root / "evidence.jsonl").read_bytes()) == run["journalDigest"]
    for kind, key, body in rows:
        store.put(kind, key, json.loads(body))
    return app, run, root


def export(api, run):
    return api.post(
        f"/api/v1/runs/{run['runId']}/exports",
        headers={"Idempotency-Key": "owned-recorded-autoverse-export"},
        json={},
    )


def test_actual_autoverse_export_preserves_source_scope(recorded_demo):
    app, run, root = recorded_demo
    with authenticated(app) as api:
        response = export(api, run)
        assert response.status_code == 202, response.text
        download = api.get(response.json()["result"]["downloadUrl"])
        assert download.status_code == 200
        files = unpack(download.content)
        assert files["evidence/reference.jsonl"] == (root / "evidence.jsonl").read_bytes()
        report = json.loads(files["report.json"])
        assert report["evidenceScope"] == run["evidenceScope"]
        assert report["integrity"] == "valid"
        assert "Owned executable reference" not in " ".join(report["limitations"])


def test_export_integrity_describes_exact_captured_autoverse_bytes(recorded_demo, monkeypatch):
    from xverse_studio.evidence import reader

    app, run, root = recorded_demo
    path = root / "evidence.jsonl"
    original = path.read_bytes()
    first = original.splitlines()[0]
    loads = json.loads
    changed = []

    def concurrent_change(value, *args, **kwargs):
        result = loads(value, *args, **kwargs)
        if (
            not changed and isinstance(value, bytes) and value.rstrip(b"\n") == first
            and any(frame.function == "accepted" and frame.filename.endswith("/api/exchange.py")
                    for frame in inspect.stack())
        ):
            path.write_bytes(b"controlled replacement after captured journal verification\n")
            changed.append(True)
        return result

    with authenticated(app) as api:
        # The export must perform a fresh verification, even if the initial
        # lifecycle projection has already cached the same recorded journal.
        read_run = app.state.studio.runs.read

        def fresh_export_capture(rid):
            value = read_run(rid)
            with reader._CACHE_LOCK:
                reader._CACHE.clear()
            return value

        monkeypatch.setattr(app.state.studio.runs, "read", fresh_export_capture)
        monkeypatch.setattr(json, "loads", concurrent_change)
        response = export(api, run)
        assert response.status_code == 202, response.text
        files = unpack(api.get(response.json()["result"]["downloadUrl"]).content)
        assert changed == [True], "The real verification boundary was not exercised"
        assert files["evidence/reference.jsonl"] == original
        assert json.loads(files["report.json"])["integrity"] == "valid"
        manifest = json.loads(files["manifest.json"])
        assert manifest["files"]["evidence/reference.jsonl"] == digest(original)
        assert path.read_bytes() != original


@pytest.mark.parametrize("fault", ["hardlink", "parent-link"])
def test_export_refuses_rebound_or_shared_actual_journal(recorded_demo, fault):
    app, run, root = recorded_demo
    original_operations = app.state.studio.store.all("operation")
    if fault == "hardlink":
        os.link(root / "evidence.jsonl", app.state.studio.store.root / "second-journal.jsonl")
    else:
        alternate = root.with_name("original-" + root.name)
        root.rename(alternate)
        root.symlink_to(alternate, target_is_directory=True)
    with authenticated(app) as api:
        response = export(api, run)
        assert response.status_code == 422, response.text
        assert response.json()["code"] == "EVIDENCE_INVALID"
        assert app.state.studio.store.all("operation") == original_operations


@pytest.mark.parametrize("fault", ["none", "file-link", "parent-link", "hardlink", "oversized", "rehashed-report"])
def test_imported_actual_autoverse_files_are_anchored_and_inert(recorded_demo, fault):
    app, run, _ = recorded_demo
    with authenticated(app) as api:
        operation = export(api, run)
        assert operation.status_code == 202, operation.text
        bundle = api.get(operation.json()["result"]["downloadUrl"])
        response = api.post(
            "/api/v1/evidence/imports",
            json={"archiveBase64": base64.b64encode(bundle.content).decode()},
        )
        assert response.status_code == 201, response.text
        record = response.json()
        store = app.state.studio.store
        original = store.get("importedEvidence", record["bundleId"])
        root = store.root / "evidence-imports" / record["bundleId"]
        path = root / "report.json"
        if fault == "file-link":
            path.rename(root / "original-report.json")
            path.symlink_to(root / "original-report.json")
        elif fault == "parent-link":
            alternate = root.with_name("original-" + root.name)
            root.rename(alternate)
            root.symlink_to(alternate, target_is_directory=True)
        elif fault == "hardlink":
            os.link(path, store.root / "second-report.json")
        elif fault == "oversized":
            with path.open("wb") as stream:
                stream.truncate(1024 * 1024 + 1)
        elif fault == "rehashed-report":
            report = json.loads(path.read_bytes())
            report["evidenceScope"] = "controlled-replacement-report"
            path.write_text(canonical(report))
            manifest_path = root / "manifest.json"
            manifest = json.loads(manifest_path.read_bytes())
            manifest["files"]["report.json"] = digest(path.read_bytes())
            manifest_path.write_text(canonical(manifest))
        detail = api.get("/api/v1/evidence/imports/" + record["bundleId"])
        assert detail.status_code == 200, detail.text
        inspection = detail.json()["inspection"]
        if fault == "none":
            assert inspection == record["inspection"]
            # Preserve the unsupported imported-reader limitation rather than
            # promoting a recording to a newly admitted runtime/Argus source.
            assert "SOURCE_PROVIDER_READER_UNSUPPORTED" in inspection["diagnostics"]
        else:
            assert inspection["integrity"] == "invalid"
            assert "IMPORTED_FILES_CHANGED_OR_UNAVAILABLE" in inspection["diagnostics"]
        assert inspection["executionAllowed"] is False
        assert store.get("importedEvidence", record["bundleId"]) == original
        assert len(store.all("run")) == 1  # no new execution ownership from import
