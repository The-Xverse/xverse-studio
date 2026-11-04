"""Frozen rerun admission using original complete Autoverse campaign records.

These cases copy protected records into separate stores and suppress dispatch.
Positive checks exercise the actual installed provider's read-only readiness in
the prepared environment; they do not claim a newly executed demo or rerun.
"""

from contextlib import closing
from copy import deepcopy
import hashlib
import json
import os
from pathlib import Path
import sqlite3

import pytest

from autoverse_provider_admission import application, authenticated
from xverse_studio.evidence.reader import read_journal
from xverse_studio.providers.autoverse.adapter import AutoverseProvider
from xverse_studio.storage.core import canonical, digest


@pytest.fixture(scope="module", params=["campaign", "assessment"])
def original(request):
    source = Path(
        os.environ[
            "STUDIO_AUTOVERSE_CAMPAIGN_RECORDING"
            if request.param == "campaign"
            else "STUDIO_AUTOVERSE_ASSESSMENT_RECORDING"
        ]
    )
    result = json.loads((source / "native-result.json").read_bytes())
    assert result["outcome"] == "passed"
    child = result["children"][0] if request.param == "campaign" else result
    assert child[
        "fullAndroidAndVehicleSpeedObserved"
        if request.param == "campaign"
        else "fullAndroidAndSpeedObserved"
    ]
    root = Path(
        json.loads((source / "data-root.private.json").read_bytes())["dataRoot"]
    )
    path = root / "snapshots" / child["snapshotId"] / "snapshot.json"
    journal = root / "runs" / child["runId"] / "evidence.jsonl"
    files = [path, journal, root / "studio.sqlite"]

    def hashes():
        return {str(p): hashlib.sha256(p.read_bytes()).hexdigest() for p in files}

    before = hashes()
    with closing(
        sqlite3.connect((root / "studio.sqlite").as_uri() + "?mode=ro", uri=True)
    ) as db:
        run = json.loads(
            db.execute(
                "SELECT body FROM records WHERE kind='run' AND id=?", (child["runId"],)
            ).fetchone()[0]
        )
    snapshot = json.loads(path.read_bytes())
    assert snapshot["snapshotDigest"] == digest(
        {k: v for k, v in snapshot.items() if k != "snapshotDigest"}
    )
    assert read_journal(journal.parent, run)[1] == "valid"
    assert run["state"] == "stopped" and run["cleanup"] == "complete"
    yield run, snapshot, path.read_bytes()
    assert hashes() == before


@pytest.fixture
def target(original, tmp_path, monkeypatch):
    receipt = json.loads(
        Path(os.environ["STUDIO_AUTOVERSE_TEST_INSTALLATION"]).read_bytes()
    )
    provider = AutoverseProvider(receipt["classic"])
    app = application(tmp_path / "Frozen historical admission Ω", provider)
    store = app.state.studio.store
    run, snapshot, raw = deepcopy(original)
    store.put("run", run["runId"], run)
    store.put("snapshot", snapshot["snapshotId"], snapshot)
    directory = store.root / "snapshots" / snapshot["snapshotId"]
    directory.mkdir(parents=True)
    (directory / "snapshot.json").write_bytes(raw)
    dispatched = []
    monkeypatch.setattr(app.state.studio.reruns, "dispatch", dispatched.append)

    def forbidden(*args, **kwargs):
        pytest.fail("Admission-only check dispatched a workload")

    monkeypatch.setattr(app.state.studio.runs, "_dispatch", forbidden)
    with authenticated(app) as api:
        yield api, app.state.studio, provider, run, snapshot, dispatched
    assert (directory / "snapshot.json").read_bytes() == raw


def request(target, key="exact-historical-inputs"):
    api, _, _, run, _, _ = target
    return api.post(
        f"/api/v1/runs/{run['runId']}/reruns", headers={"Idempotency-Key": key}, json={}
    )


def test_historical_installed_inputs_receive_a_new_full_readonly_preflight(target):
    _, state, _, run, frozen, dispatched = target
    response = request(target)
    assert response.status_code == 202, response.text
    operation = state.store.get("operation", response.json()["operationId"])
    assert (
        operation["status"] == "accepted" and operation["sourceRunId"] == run["runId"]
    )
    snapshot = state.store.get("snapshot", operation["snapshotId"])
    assert snapshot["snapshotId"] != frozen["snapshotId"]
    for key in (
        "documents",
        "projectDocuments",
        "selection",
        "profileLocks",
        "configuration",
        "planDigest",
        "semanticDigest",
        "revision",
    ):
        assert snapshot[key] == frozen[key], key
    assert snapshot["parentSnapshotId"] == frozen["snapshotId"]
    assert snapshot["sourceRunId"] == run["runId"]
    assert snapshot["sourceSnapshotDigest"] == frozen["snapshotDigest"]
    assert "campaignId" not in snapshot and "campaignChildKey" not in snapshot
    (pf,) = state.store.all("preflight")
    assert pf["status"] == "ready" and pf["snapshotId"] == snapshot["snapshotId"]
    assert pf["snapshotDigest"] == snapshot["snapshotDigest"]
    assert pf["readiness"]["observations"]["status"] == "compatible"
    assert pf["readiness"]["ownership"]["facts"]["reserved"] is False
    assert pf["dimensions"]["evidenceScope"] == "external_demo"
    assert operation["evidenceScope"] == "external_demo"
    assert (
        snapshot["configuration"]["randomness"]
        == "external_uncontrolled_no_applied_seed"
    )
    assert len(state.store.all("run")) == 1 and len(dispatched) == 1


def test_same_key_never_rechecks_readiness_or_creates_another_snapshot(
    target, monkeypatch
):
    _, state, provider, _, _, dispatched = target
    accepted = request(target)
    assert accepted.status_code == 202, accepted.text
    before = (
        state.store.all("preflight"),
        state.store.all("snapshot"),
        state.store.all("operation"),
    )

    def forbidden(*args, **kwargs):
        pytest.fail("An accepted request was admitted again")

    monkeypatch.setattr(provider, "readiness", forbidden)
    assert request(target).json() == accepted.json()
    assert (
        state.store.all("preflight"),
        state.store.all("snapshot"),
        state.store.all("operation"),
    ) == before
    assert dispatched == [accepted.json()["operationId"]]


def test_existing_snapshot_identity_is_preserved(target, monkeypatch):
    _, state, _, _, frozen, dispatched = target
    from xverse_studio.runs import service

    uid = service.uid
    monkeypatch.setattr(
        service,
        "uid",
        lambda prefix: frozen["snapshotId"] if prefix == "snap-" else uid(prefix),
    )
    response = request(target)
    assert (
        response.status_code == 409 and response.json()["code"] == "IDENTITY_CONFLICT"
    ), response.text
    assert (
        state.store.all("operation") == state.store.all("preflight") == dispatched == []
    )
    assert state.store.all("snapshot") == [frozen]


@pytest.mark.parametrize("replace_directory", [False, True])
def test_failed_publication_rolls_back_only_its_acquired_directory(
    target, monkeypatch, replace_directory
):
    _, state, _, run, frozen, dispatched = target
    from xverse_studio.api import reruns as module

    atomic = module.atomic
    paths = {}

    def fail(path, data):
        atomic(path, data)
        assert path.name == "snapshot.json" and path.parent.name != frozen["snapshotId"]
        paths["target"] = path.parent
        if replace_directory:
            retired = path.parent.with_name("retained-original-owned-directory")
            path.parent.rename(retired)
            path.parent.mkdir()
            (path.parent / "foreign-marker").write_bytes(b"Preserve this replacement")
            paths["retired"] = retired
        raise OSError("Controlled failure after protected snapshot publication")

    monkeypatch.setattr(module, "atomic", fail)
    with pytest.raises(OSError, match="Controlled failure"):
        state.reruns.create(run["runId"], "local-operator", "publication-rollback")
    if replace_directory:
        assert (
            paths["target"] / "foreign-marker"
        ).read_bytes() == b"Preserve this replacement"
        assert (paths["retired"] / "snapshot.json").is_file()
    else:
        assert not paths["target"].exists()
    assert state.store.all("snapshot") == [frozen]
    assert (
        state.store.all("operation") == state.store.all("preflight") == dispatched == []
    )
    with state.store.tx() as db:
        assert db.execute("SELECT count(*) FROM idempotency").fetchone()[0] == 0


@pytest.mark.parametrize(
    "change",
    [
        "missing",
        "future",
        "numeric-false",
        "physical",
        "extra",
        "empty-versions",
        "duplicate-versions",
        "unknown-policy",
    ],
)
def test_provider_must_explicitly_admit_the_closed_frozen_rerun_contract(
    target, monkeypatch, change
):
    _, state, provider, _, _, dispatched = target
    descriptor = provider.descriptor()
    if change == "missing":
        descriptor.pop("rerunContract", None)
    else:
        contract = descriptor.setdefault("rerunContract", {})
        if change == "future":
            contract["contractVersion"] = "2.0"
        elif change == "numeric-false":
            contract["physicalEffects"] = 0
        elif change == "physical":
            contract["physicalEffects"] = True
        elif change == "extra":
            contract["runCommand"] = "never execute metadata"
        elif change == "empty-versions":
            contract["sourceVersions"] = []
        elif change == "duplicate-versions":
            contract["sourceVersions"] = ["0.4.0", "0.4.0"]
        else:
            contract["inputPolicy"] = "current-draft"
    monkeypatch.setattr(provider, "descriptor", lambda: descriptor)

    def forbidden(*args, **kwargs):
        pytest.fail("Unsupported rerun contract reached readiness")

    monkeypatch.setattr(provider, "readiness", forbidden)
    response = request(target)
    assert (
        response.status_code == 422 and response.json()["code"] == "RERUN_UNSUPPORTED"
    ), response.text
    assert (
        state.store.all("operation") == state.store.all("preflight") == dispatched == []
    )


@pytest.mark.parametrize("change", ["configuration", "compiled-plan", "full-preflight"])
def test_current_mapping_cannot_change_original_effective_inputs(
    target, monkeypatch, change
):
    _, state, provider, _, _, dispatched = target
    if change == "configuration":
        original_configuration = provider.configuration

        def changed(documents, compiled):
            result = original_configuration(documents, compiled)
            return {**result, "durationSeconds": result["durationSeconds"] + 1}

        monkeypatch.setattr(provider, "configuration", changed)
    elif change == "compiled-plan":
        compile_original = state.runs.compilation

        def changed(*args):
            result = compile_original(*args)
            return {**result, "planDigest": "sha256:" + "0" * 64}

        monkeypatch.setattr(state.runs, "compilation", changed)
    else:
        build_original = state.runs._build_preflight_sources

        def changed(*args, **kwargs):
            snapshot, pf = build_original(*args, **kwargs)
            snapshot["configuration"]["durationSeconds"] += 1
            return snapshot, pf

        monkeypatch.setattr(state.runs, "_build_preflight_sources", changed)
    response = request(target)
    assert (
        response.status_code == 422
        and response.json()["code"] == "RERUN_INPUT_INCOMPATIBLE"
    ), response.text
    assert (
        state.store.all("operation") == state.store.all("preflight") == dispatched == []
    )
    assert len(state.store.all("snapshot")) == 1


def test_current_readiness_refusal_has_no_operation_snapshot_or_dispatch(
    target, monkeypatch
):
    _, state, provider, _, _, dispatched = target
    # Exercise actual provider RESOURCE_BUSY logic, which refuses before native
    # installation probes. This is a controlled metadata state, not a live run.
    occupied = deepcopy(state.store.all("run")[0])
    occupied.update(runId="controlled-unknown-occupancy", state="unknown")
    state.store.put("run", occupied["runId"], occupied)

    def forbidden(*args, **kwargs):
        pytest.fail("Occupied installation should not be probed")

    monkeypatch.setattr(provider, "verify_installation", forbidden)
    try:
        response = request(target)
        assert response.status_code == 422, response.text
        assert response.json()["code"] == "ADMISSION_REJECTED"
        assert any(d["code"] == "RESOURCE_BUSY" for d in response.json()["diagnostics"])
        assert (
            state.store.all("preflight")
            == state.store.all("operation")
            == dispatched
            == []
        )
        assert len(state.store.all("snapshot")) == 1
        with state.store.tx() as db:
            assert db.execute("SELECT count(*) FROM idempotency").fetchone()[0] == 0
    finally:
        with state.store.tx() as db:
            db.execute(
                "DELETE FROM records WHERE kind='run' AND id=?", (occupied["runId"],)
            )


@pytest.mark.parametrize(
    "change", ["binding", "version", "physical", "source-integrity"]
)
def test_changed_historical_binding_never_reaches_readiness(
    target, monkeypatch, change
):
    _, state, provider, run, frozen, dispatched = target
    changed = deepcopy(frozen)
    if change == "binding":
        changed["providerIdentity"]["installationDigest"] = "sha256:" + "0" * 64
    elif change == "version":
        changed["providerIdentity"]["providerVersion"] = "unadmitted"
    elif change == "physical":
        changed["configuration"]["physicalEffects"] = True
    else:
        # A database-only mutation is caught by the existing protected reader.
        changed["configuration"]["durationSeconds"] = 60
    if change != "source-integrity":
        changed["snapshotDigest"] = digest(
            {k: v for k, v in changed.items() if k != "snapshotDigest"}
        )
        path = state.store.root / "snapshots" / frozen["snapshotId"] / "snapshot.json"
        original_bytes = path.read_bytes()
        path.write_text(canonical(changed))
    state.store.put("snapshot", frozen["snapshotId"], changed)

    def forbidden(*args, **kwargs):
        pytest.fail("Changed historical authority reached readiness")

    monkeypatch.setattr(provider, "readiness", forbidden)
    try:
        response = request(target)
        assert response.status_code == 422, response.text
        assert response.json()["code"] in {
            "RERUN_UNSUPPORTED",
            "SNAPSHOT_INTEGRITY",
            "RERUN_INPUT_INCOMPATIBLE",
        }
        assert (
            state.store.all("operation")
            == state.store.all("preflight")
            == dispatched
            == []
        )
        assert len(state.store.all("run")) == 1
    finally:
        if change != "source-integrity":
            path.write_bytes(original_bytes)
