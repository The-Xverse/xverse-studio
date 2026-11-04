"""T011 fixture distinctions against actual enrolled Autoverse projects.

Synthetic descriptions can only establish negative admission. The committed
recording is read-only evidence and never a newly executed provider or clock.
"""

import base64
import hashlib
import importlib.util
import io
import json
from pathlib import Path
import subprocess
import sys
import zipfile

import pytest

import autoverse_provider_admission as enrollment
from autoverse_provider_admission import application, authenticated, project
from xverse_studio.storage.core import digest
from xverse_studio.host.ownership import own_root, RootOwnedError

target = enrollment.target
ROOT = Path(__file__).resolve().parents[2]
CATALOG = ROOT / "tests/fixtures/providers/catalog.json"
RECORDING = ROOT / "tests/fixtures/runs/autoverse-classic-recorded.bundle.zip"
PROVENANCE = ROOT / "tests/fixtures/runs/autoverse-classic-recorded.json"
spec = importlib.util.spec_from_file_location("closed_fake_provider_fixture", ROOT / "tests/fixtures/providers/fake_provider.py")
fake = importlib.util.module_from_spec(spec)
spec.loader.exec_module(fake)
host_spec = importlib.util.spec_from_file_location("closed_native_failure_host", ROOT / "tests/fixtures/providers/run_failures/host.py")
host = importlib.util.module_from_spec(host_spec)
host_spec.loader.exec_module(host)


def forbidden(*args, **kwargs):
    raise AssertionError("Inert or fake fixture attempted native process acquisition")


def test_current_autoverse_host_discovery_does_not_advertise_unverified_reference_windows(target, tmp_path):
    provider, blueprint = target
    app = application(tmp_path / "Autoverse fixture discovery Ω", provider)
    with authenticated(app) as api:
        p = project(api, blueprint)
        capabilities = api.get("/api/v1/capabilities")
        assert capabilities.status_code == 200
        value = capabilities.json()
        assert value["studio"]["nativeTargets"] == ["Linux", "Windows"]
        reference = next(d for d in value["providers"] if d["providerId"] == "studio.reference")
        assert reference["supportedHostOS"] == ["Linux"]
        assert reference["architectures"] == ["x86_64"]
        assert reference["maturity"] == "fixture" and reference["evidenceScope"] == "owned_reference"
        assert api.get(f"/api/v1/projects/{p['projectId']}").json()["sourceIntegrity"] == "intact"


@pytest.mark.parametrize("case", list(fake.CASES))
def test_synthetic_fixture_descriptions_cannot_admit_actual_autoverse_execution(
    target, tmp_path, monkeypatch, case
):
    provider, blueprint = target
    original = provider.descriptor()
    synthetic = fake.FakeProvider(original, case)
    synthetic.clock.advance(9007199254740993)
    app = application(tmp_path / "Synthetic Autoverse refusal Ω", synthetic)
    with authenticated(app) as api:
        p = project(api, blueprint)
        monkeypatch.setattr(subprocess, "Popen", forbidden)
        monkeypatch.setattr(app.state.studio.runs, "_dispatch", forbidden)
        discovery = api.get("/api/v1/providers")
        assert discovery.status_code == 200
        described = next(d for d in discovery.json()["items"] if d["providerId"] == original["providerId"])
        assert described["available"] is False and described["operations"] == []
        assert described["blockedReasons"][0]["code"] == synthetic.expected_code
        pf = api.post(
            f"/api/v1/projects/{p['projectId']}/preflights",
            json={"revision": p["revision"], "providerId": original["providerId"]},
        )
        assert pf.status_code == 200 and pf.json()["status"] == "blocked", pf.text
        start = api.post(
            "/api/v1/runs", headers={"Idempotency-Key": "synthetic-fixture-no-execution"},
            json={key: pf.json()[key] for key in ("snapshotId", "preflightId")},
        )
        assert start.status_code == 422 and start.json()["code"] == "ADMISSION_REJECTED"
        assert synthetic.lifecycle_calls == 0
        assert provider.descriptor() == original
        assert app.state.studio.store.all("run") == []
        assert app.state.studio.store.all("operation") == []
        catalogue = json.loads(CATALOG.read_bytes())
        assert catalogue["fakeProvider"]["executionAllowed"] is False
        assert synthetic.descriptor()["fixtureMetadata"]["clock"]["tick"] == "9007199254740993"


def test_committed_actual_autoverse_recording_has_original_bytes_and_no_current_authority(
    target, tmp_path, monkeypatch
):
    provider, blueprint = target
    app = application(tmp_path / "Recorded Autoverse inspection Ω", provider)
    original = RECORDING.read_bytes()
    provenance = json.loads(PROVENANCE.read_bytes())
    assert digest(original) == provenance["archiveDigest"]
    assert len(original) == provenance["compressedBytes"]
    with zipfile.ZipFile(io.BytesIO(original)) as archive:
        files = {name: archive.read(name) for name in archive.namelist()}
    assert sum(map(len, files.values())) == provenance["expandedBytes"]
    assert digest(files["evidence/reference.jsonl"]) == provenance["journalDigest"]
    rows = [json.loads(line) for line in files["evidence/reference.jsonl"].splitlines()]
    assert len(rows) == provenance["recordCount"] == 71
    assert all(row["sourceTime"] is None for row in rows)
    assert {row["runId"] for row in rows} == {provenance["sourceRunId"]}
    with authenticated(app) as api:
        project(api, blueprint)
        monkeypatch.setattr(subprocess, "Popen", forbidden)
        monkeypatch.setattr(app.state.studio.runs, "_dispatch", forbidden)
        imported = api.post(
            "/api/v1/evidence/imports",
            json={"archiveBase64": base64.b64encode(original).decode()},
        )
        assert imported.status_code == 201, imported.text
        value = imported.json()
        inspection = value["inspection"]
        assert inspection["sourceRunId"] == provenance["sourceRunId"]
        assert inspection["declaredEvidenceScope"] == "external_demo"
        assert inspection["evidenceScope"] == "imported_recorded_evidence"
        assert inspection["executionAllowed"] is False
        assert inspection["providerAdmission"] == "not_conferred_by_import"
        assert inspection["coverageComplete"] is False
        assert "SOURCE_PROVIDER_READER_UNSUPPORTED" in inspection["diagnostics"]
        assert api.get("/api/v1/evidence/imports/" + value["bundleId"]).json()["inspection"] == inspection
        start = api.post(
            "/api/v1/runs", headers={"Idempotency-Key": "recording-is-not-a-preflight"},
            json={"snapshotId": provenance["sourceSnapshotId"], "preflightId": "recorded-no-live-preflight"},
        )
        assert start.status_code == 404 and start.json()["code"] == "NOT_FOUND"
        assert app.state.studio.store.all("run") == []
        assert app.state.studio.store.all("snapshot") == []
        assert app.state.studio.store.all("operation") == []
    assert RECORDING.read_bytes() == original
    assert "sha256:" + hashlib.sha256(original).hexdigest() == provenance["archiveDigest"]


@pytest.mark.parametrize("alias", [False, True])
def test_failure_host_refuses_an_existing_autoverse_workspace_before_application_init(
    target, tmp_path, monkeypatch, alias
):
    provider, blueprint = target
    app = application(tmp_path / "Preserved Autoverse workspace Ω", provider)
    with authenticated(app) as api:
        p = project(api, blueprint)
        before = app.state.studio.store.get("project", p["projectId"])
        root = app.state.studio.store.root
        if alias:
            selected = tmp_path / "Autoverse workspace alias"
            selected.symlink_to(root, target_is_directory=True)
        else:
            selected = root
        monkeypatch.setattr(host, "create_app", forbidden)
        monkeypatch.setattr(sys, "argv", ["closed-failure-host", "--data", str(selected), "--scenario", "normal"])
        with pytest.raises(SystemExit) as refused:
            host.main()
        assert refused.value.code == 2
        assert app.state.studio.store.get("project", p["projectId"]) == before
        assert app.state.studio.store.all("run") == []


def test_failure_root_claim_is_exclusive_for_a_fresh_autoverse_workspace(target, tmp_path):
    provider, blueprint = target
    selected = tmp_path / "Fresh owned Autoverse fixture Ω"
    with host.claim_root(selected) as acquired:
        assert acquired == selected
        app = application(acquired, provider)
        with authenticated(app) as api:
            p = project(api, blueprint)
            with pytest.raises(RootOwnedError):
                with own_root(acquired):
                    raise AssertionError("A second native owner acquired the fixture root")
            assert api.get(f"/api/v1/projects/{p['projectId']}").status_code == 200
            assert app.state.studio.store.all("run") == []
    with own_root(selected):
        pass
    with pytest.raises(OSError):
        with host.claim_root(selected):
            raise AssertionError("An existing root was adopted as a new fixture")
