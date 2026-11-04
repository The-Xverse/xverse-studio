"""Actual Autoverse evidence exchange; independent stores, no new execution.

Original complete 0.3/0.4 recordings supply protected snapshots, original journals
and derived assessments. Faults affect only separate owned copies. Imports never
admit a provider reader, start a workload, or change original evidence.
"""

import base64
from contextlib import closing
from copy import deepcopy
import io
import hashlib
import json
import os
from pathlib import Path
import shutil
import sqlite3
import zipfile

import pytest

from autoverse_frozen_rerun import original as original
from autoverse_provider_admission import application, authenticated
from xverse_studio.providers.autoverse.adapter import AutoverseProvider
from xverse_studio.storage.core import canonical, digest


def unpack(raw):
    with zipfile.ZipFile(io.BytesIO(raw)) as archive:
        return {name: archive.read(name) for name in archive.namelist()}


def encode(files):
    manifest = json.loads(files["manifest.json"])
    manifest["files"] = {
        name: digest(raw) for name, raw in files.items() if name != "manifest.json"
    }
    files = {**files, "manifest.json": canonical(manifest).encode()}
    stream = io.BytesIO()
    with zipfile.ZipFile(stream, "w", compression=zipfile.ZIP_STORED) as archive:
        for name, raw in files.items():
            archive.writestr(name, raw)
    return base64.b64encode(stream.getvalue()).decode()


@pytest.fixture
def recorded(original, tmp_path, monkeypatch):  # noqa: F811 — imported pytest fixture
    run, snapshot, raw = deepcopy(original)
    source = Path(
        os.environ[
            "STUDIO_AUTOVERSE_CAMPAIGN_RECORDING"
            if snapshot["providerIdentity"]["providerVersion"] == "0.4.0"
            else "STUDIO_AUTOVERSE_ASSESSMENT_RECORDING"
        ]
    )
    root = Path(
        json.loads((source / "data-root.private.json").read_bytes())["dataRoot"]
    )
    provider = AutoverseProvider(
        json.loads(Path(os.environ["STUDIO_AUTOVERSE_TEST_INSTALLATION"]).read_bytes())[
            "classic"
        ]
    )
    app = application(tmp_path / "Actual recorded exchange Ω", provider)
    store = app.state.studio.store
    store.put("run", run["runId"], run)
    store.put("snapshot", snapshot["snapshotId"], snapshot)
    with closing(
        sqlite3.connect((root / "studio.sqlite").as_uri() + "?mode=ro", uri=True)
    ) as db:
        rows = db.execute(
            "SELECT kind,id,body FROM records WHERE kind IN ('operation','evaluation','annotation')"
        ).fetchall()
    for kind, key, body in rows:
        row = json.loads(body)
        if kind == "operation" or row.get("runId") == run["runId"]:
            store.put(kind, key, row)
    for name in ("state.json", "evidence.jsonl"):
        dest = store.root / "runs" / run["runId"] / name
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(root / "runs" / run["runId"] / name, dest)
    path = store.root / "snapshots" / snapshot["snapshotId"] / "snapshot.json"
    path.parent.mkdir(parents=True)
    path.write_bytes(raw)

    def forbidden(*args, **kwargs):
        pytest.fail("Recorded exchange attempted provider readiness or execution")

    monkeypatch.setattr(provider, "readiness", forbidden)
    monkeypatch.setattr(app.state.studio.runs, "_dispatch", forbidden)
    with authenticated(app) as api:
        yield api, store, run, snapshot, path


def export(recorded):
    api, _, run, _, _ = recorded
    return api.post(
        f"/api/v1/runs/{run['runId']}/exports",
        headers={"Idempotency-Key": "actual-evidence-export"},
        json={},
    )


def test_exact_actual_snapshot_journal_and_derived_records_export_without_execution(
    recorded,
):
    api, store, run, _, path = recorded
    before_runs = store.all("run")
    result = export(recorded)
    assert result.status_code == 202, result.text[:500]
    assert export(recorded).json() == result.json()
    files = unpack(api.get(result.json()["result"]["downloadUrl"]).content)
    assert files["snapshot.json"] == path.read_bytes()
    assert (
        files["evidence/reference.jsonl"]
        == (store.root / "runs" / run["runId"] / "evidence.jsonl").read_bytes()
    )
    assert json.loads(files["evaluations.json"]) == [
        r for r in store.all("evaluation") if r.get("runId") == run["runId"]
    ]
    report = json.loads(files["report.json"])
    assert (
        report["evidenceScope"] == "external_demo"
        and report["evidenceStatus"] == "available"
    )
    assert report["integrity"] == "valid"
    imported = api.post(
        "/api/v1/evidence/imports", json={"archiveBase64": encode(files)}
    )
    assert imported.status_code == 201, imported.text
    inspection = imported.json()["inspection"]
    assert inspection["executionAllowed"] is False
    assert inspection["journalIntegrity"] == "unavailable"
    assert "SOURCE_PROVIDER_READER_UNSUPPORTED" in inspection["diagnostics"]
    assert len(store.all("run")) == len(before_runs)
    assert store.all("preflight") == store.all("rerunDispatch") == []


def test_known_bad_actual_journal_remains_invalid_when_provider_reader_is_unsupported(
    recorded,
):
    api, store, run, _, _ = recorded
    result = export(recorded)
    assert result.status_code == 202, result.text[:500]
    files = unpack(api.get(result.json()["result"]["downloadUrl"]).content)
    files["evidence/reference.jsonl"] += (
        b"Damaged imported journal; original producer digest is unchanged.\n"
    )
    response = api.post(
        "/api/v1/evidence/imports", json={"archiveBase64": encode(files)}
    )
    assert response.status_code == 201, response.text[:500]
    inspection = response.json()["inspection"]
    assert inspection["integrity"] == inspection["journalIntegrity"] == "invalid"
    assert "ORIGINAL_JOURNAL_INVALID" in inspection["diagnostics"]
    assert "SOURCE_PROVIDER_READER_UNSUPPORTED" in inspection["diagnostics"]
    assert (
        inspection["coverageComplete"] is False
        and inspection["executionAllowed"] is False
    )
    assert len(store.all("run")) == 1 and store.all("preflight") == []
    assert (
        api.get("/api/v1/evidence/imports/" + response.json()["bundleId"]).json()[
            "inspection"
        ]
        == inspection
    )


def test_report_names_exact_external_dependencies_without_claiming_their_availability(
    recorded,
):
    api, _, _, snapshot, _ = recorded
    result = export(recorded)
    assert result.status_code == 202, result.text[:500]
    files = unpack(api.get(result.json()["result"]["downloadUrl"]).content)
    dependencies = json.loads(files["report.json"]).get("dependencies")
    assert isinstance(dependencies, dict), (
        "The exchange report must name its unavailable runtime dependencies."
    )
    assert dependencies["dependenciesVersion"] == "1.0"
    assert dependencies["snapshotDigest"] == snapshot["snapshotDigest"]
    assert dependencies["resolution"] == "not_attempted"
    (provider,) = [r for r in dependencies["items"] if r["kind"] == "provider"]
    assert provider["identity"]["providerId"] == "autoverse.demo"
    assert (
        provider["identity"]["installationDigest"]
        == snapshot["providerIdentity"]["installationDigest"]
    )
    assert provider["availability"] == "not_included"
    assert all(r["contentIncluded"] is False for r in dependencies["items"])
    imported = api.post(
        "/api/v1/evidence/imports", json={"archiveBase64": encode(files)}
    )
    assert imported.status_code == 201, imported.text
    assert imported.json()["inspection"]["dependencies"] == dependencies
    assert imported.json()["inspection"]["executionAllowed"] is False


def test_rehashed_dependency_availability_cannot_replace_original_frozen_references(
    recorded,
):
    api, store, _, _, _ = recorded
    result = export(recorded)
    assert result.status_code == 202, result.text[:500]
    files = unpack(api.get(result.json()["result"]["downloadUrl"]).content)
    report = json.loads(files["report.json"])
    report["dependencies"] = {
        "dependenciesVersion": "1.0",
        "resolution": "downloaded_and_installed",
        "items": [],
    }
    files["report.json"] = canonical(report).encode()
    response = api.post(
        "/api/v1/evidence/imports", json={"archiveBase64": encode(files)}
    )
    assert (
        response.status_code == 422
        and response.json()["code"] == "EVIDENCE_BUNDLE_INVALID"
    ), response.text[:500]
    assert store.all("importedEvidence") == []


def test_dependency_booleans_cannot_be_replaced_by_equal_numeric_encodings(recorded):
    api, store, _, _, _ = recorded
    result = export(recorded)
    files = unpack(api.get(result.json()["result"]["downloadUrl"]).content)
    report = json.loads(files["report.json"])
    report["dependencies"]["items"][0]["contentIncluded"] = 0
    files["report.json"] = canonical(report).encode()
    response = api.post(
        "/api/v1/evidence/imports", json={"archiveBase64": encode(files)}
    )
    assert (
        response.status_code == 422
        and response.json()["code"] == "EVIDENCE_BUNDLE_INVALID"
    ), response.text[:500]
    assert store.all("importedEvidence") == []


def test_legacy_report_without_dependency_summary_remains_inert_and_explicitly_unresolved(
    recorded,
):
    api, _, _, _, _ = recorded
    result = export(recorded)
    files = unpack(api.get(result.json()["result"]["downloadUrl"]).content)
    report = json.loads(files["report.json"])
    report.pop("dependencies")
    files["report.json"] = canonical(report).encode()
    response = api.post(
        "/api/v1/evidence/imports", json={"archiveBase64": encode(files)}
    )
    assert response.status_code == 201, response.text[:500]
    inspection = response.json()["inspection"]
    assert inspection["dependencies"] is None
    assert "DEPENDENCY_SUMMARY_UNAVAILABLE" in inspection["diagnostics"]
    assert inspection["executionAllowed"] is False


@pytest.mark.parametrize(
    "fault",
    ["boolean-sequence", "numeric-sequence", "leading-zero", "duplicate-event-id"],
)
def test_rehashed_noncanonical_envelopes_remain_invalid_for_an_unsupported_reader(
    recorded, fault
):
    api, _, _, _, _ = recorded
    result = export(recorded)
    files = unpack(api.get(result.json()["result"]["downloadUrl"]).content)
    records = [
        json.loads(line) for line in files["evidence/reference.jsonl"].splitlines()
    ]
    if fault == "duplicate-event-id":
        records[1]["eventId"] = records[0]["eventId"]
    else:
        records[0]["sequence"] = {
            "boolean-sequence": True,
            "numeric-sequence": 1,
            "leading-zero": "01",
        }[fault]
    # A hostile archive can rehash itself. Internal hashes cannot legitimize a
    # noncanonical envelope or authenticate the original external producer.
    previous = "0" * 64
    lines = []
    for record in records:
        record.pop("digest")
        record["previousDigest"] = previous
        previous = hashlib.sha256(canonical(record).encode()).hexdigest()
        lines.append(canonical({**record, "digest": previous}).encode() + b"\n")
    files["evidence/reference.jsonl"] = b"".join(lines)
    run = json.loads(files["run.json"])
    run["journalDigest"] = digest(files["evidence/reference.jsonl"])
    files["run.json"] = canonical(run).encode()
    response = api.post(
        "/api/v1/evidence/imports", json={"archiveBase64": encode(files)}
    )
    assert response.status_code == 201, response.text[:500]
    assert response.json()["inspection"]["integrity"] == "invalid"
    assert response.json()["inspection"]["executionAllowed"] is False


@pytest.mark.parametrize(
    "fault", ["database", "file", "missing", "symlink", "hardlink"]
)
def test_export_requires_the_original_protected_snapshot_before_creating_an_operation(
    recorded, fault
):
    _, store, _, snapshot, path = recorded
    if fault == "database":
        changed = deepcopy(snapshot)
        changed["configuration"]["durationSeconds"] += 1
        store.put("snapshot", snapshot["snapshotId"], changed)
    elif fault == "file":
        path.write_bytes(path.read_bytes() + b"\n")
    elif fault == "missing":
        path.unlink()
    elif fault == "symlink":
        alternate = path.with_name("retained-original.json")
        path.rename(alternate)
        path.symlink_to(alternate)
    else:
        os.link(path, path.with_name("shared-copy.json"))
    before = store.all("operation")
    response = export(recorded)
    assert (
        response.status_code == 422 and response.json()["code"] == "SNAPSHOT_INTEGRITY"
    ), response.text[:500]
    assert store.all("operation") == before
    assert not list((store.root / "exports").glob("*.zip"))


@pytest.mark.parametrize(
    "field,value",
    [
        ("projectId", "foreign-project"),
        ("revision", 999),
        ("providerId", "unadmitted-provider"),
        ("semanticDigest", "sha256:" + "0" * 64),
        ("planDigest", "sha256:" + "0" * 64),
    ],
)
def test_export_rejects_changed_run_to_snapshot_binding(recorded, field, value):
    _, store, run, _, _ = recorded
    store.put("run", run["runId"], {**run, field: value})
    before = store.all("operation")
    response = export(recorded)
    assert (
        response.status_code == 422 and response.json()["code"] == "SNAPSHOT_INTEGRITY"
    ), response.text[:500]
    assert store.all("operation") == before
