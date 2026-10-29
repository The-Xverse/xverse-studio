"""Owned reference timeline witnesses, never a live-device/provider claim."""

from copy import deepcopy
import base64
from io import StringIO
import json
import time

import pytest
from ruamel.yaml import YAML

from xverse_studio.assertions import definition_digest


@pytest.fixture
def recorded_fault(client):
    response = client.post("/api/v1/projects", json={"name": "Owned timeline source"})
    assert response.status_code == 201, response.text
    project = response.json()
    document_id, document = next(
        (key, value) for key, value in project["documents"].items()
        if value["path"].endswith("/scenario.xdl.yaml")
    )
    yaml = YAML()
    scenario = yaml.load(document["content"])
    parameters = scenario["extensions"]["io.xverse.experiment"]["parameters"]
    next(p for p in parameters if p["id"] == "duration")["value"] = 0.2
    next(p for p in parameters if p["id"] == "fault")["value"] = "stuck-sensor"
    for definition in scenario["extensions"]["io.xverse.studio.experiments"]["definitions"]:
        definition["window"]["endTick"] = "200000"
    original = scenario["extensions"]["io.xverse.studio.experiments"]["definitions"][0]
    metric = {**deepcopy(original), "evaluationId": "timeline-peak", "name": "Timeline peak",
              "kind": "metric", "resultUnit": "1", "expression": deepcopy(original["expression"]["left"])}
    scenario["extensions"]["io.xverse.studio.experiments"]["definitions"].append(metric)
    stream = StringIO()
    yaml.dump(scenario, stream)
    response = client.put(
        f"/api/v1/projects/{project['projectId']}/documents/{document_id}",
        headers={"If-Match": str(project["revision"])},
        json={"content": stream.getvalue(), "format": "yaml"},
    )
    assert response.status_code == 200, response.text
    project = response.json()
    response = client.post(
        f"/api/v1/projects/{project['projectId']}/preflights",
        json={"revision": project["revision"]},
    )
    assert response.status_code == 200, response.text
    preflight = response.json()
    assert preflight["status"] == "ready", preflight
    response = client.post(
        "/api/v1/runs", headers={"Idempotency-Key": "owned-timeline-run"},
        json={"preflightId": preflight["preflightId"], "snapshotId": preflight["snapshotId"]},
    )
    assert response.status_code == 202, response.text
    run_id = response.json()["runId"]
    deadline = time.monotonic() + 20
    while time.monotonic() < deadline:
        run = client.get(f"/api/v1/runs/{run_id}").json()
        if run["state"] in ("stopped", "failed", "unknown"):
            break
        time.sleep(0.05)
    assert run["state"] == "stopped", run
    snapshot = client.get(f"/api/v1/runs/{run_id}/snapshot").json()["snapshot"]
    journal = client.app.state.studio.runs.directory(run_id) / "evidence.jsonl"
    history = client.get(f"/api/v1/runs/{run_id}/history").json()
    assert {"fault.activation_requested", "fault.activation_observed"} <= {
        item["type"] for item in history["items"]
    }
    return project, document_id, scenario, run, snapshot, journal


def test_actual_fault_timeline_uses_frozen_intent_and_preserves_inputs(client, recorded_fault):
    project, document_id, scenario, run, snapshot, journal = recorded_fault
    later = deepcopy(scenario)
    later["spec"]["steps"][0]["id"] = "later-start"
    stream = StringIO()
    YAML().dump(later, stream)
    response = client.put(
        f"/api/v1/projects/{project['projectId']}/documents/{document_id}",
        headers={"If-Match": str(project["revision"])},
        json={"content": stream.getvalue(), "format": "yaml"},
    )
    assert response.status_code == 200, response.text
    current = response.json()
    original_bytes = journal.read_bytes()
    response = client.get(f"/api/v1/runs/{run['runId']}/timeline")
    assert response.status_code == 200, response.text
    report = response.json()
    assert report["timelineVersion"] == "1.0" and report["readOnly"] is True
    assert report["snapshotId"] == snapshot["snapshotId"]
    assert report["snapshotDigest"] == snapshot["snapshotDigest"]
    assert report["projectRevision"] == project["revision"] != current["revision"]
    assert report["selection"] == snapshot["selection"]
    rows = report["items"]
    assert any(row.get("intentId") == "start-reference" for row in rows)
    assert not any(row.get("intentId") == "later-start" for row in rows)
    requested = next(row for row in rows if row["kind"] == "fault.activation_requested")
    observed = next(row for row in rows if row["kind"] == "fault.activation_observed")
    assert requested["layer"] == observed["layer"] == "recorded"
    assert requested["eventId"] != observed["eventId"]
    assert requested["position"]["tick"] == observed["position"]["tick"] == "100000"
    assert requested["position"]["tickUnit"] == "microsecond"
    assert requested["evidenceScope"] == observed["evidenceScope"] == "owned_reference"
    assert requested["source"] == observed["source"] == {"providerId": "studio.reference", "version": "1.0.0"}
    configured = next(row for row in rows if row["id"] == "intent:configuration:fault")
    assert configured["declaredValue"] == "stuck-sensor" and configured["layer"] == "intent"
    assert configured["logicalRef"] == snapshot["selection"]["scenarioRef"]
    assert configured["position"]["status"] == "unplaced" and configured["position"]["tick"] is None
    assert configured["position"]["reason"] == "CONFIGURATION_HAS_NO_AUTHORED_POSITION"
    assert journal.read_bytes() == original_bytes
    assert client.get(f"/api/v1/runs/{run['runId']}/snapshot").json()["snapshot"] == snapshot
    assert client.get(f"/api/v1/projects/{project['projectId']}").json() == current


def test_timeline_requires_exact_snapshot_selection(client, recorded_fault):
    _, _, _, run, _, _ = recorded_fault
    response = client.get(
        f"/api/v1/runs/{run['runId']}/timeline", params={"snapshotId": "foreign-snapshot"}
    )
    assert response.status_code == 409, response.text
    assert response.json()["code"] == "SNAPSHOT_SELECTION_MISMATCH"


def test_timeline_pages_preserve_all_record_and_intent_identities(client, recorded_fault):
    _, _, _, run, snapshot, journal = recorded_fault
    original = journal.read_bytes()
    url = f"/api/v1/runs/{run['runId']}/timeline"
    first = client.get(url, params={"limit": 1})
    assert first.status_code == 200, first.text
    page = first.json()
    total = page["counts"]["matchedRows"]
    rows = list(page["items"])
    while page["nextCursor"] is not None:
        response = client.get(url, params={"limit": 1, "cursor": page["nextCursor"]})
        assert response.status_code == 200, response.text
        page = response.json()
        assert page["snapshotId"] == snapshot["snapshotId"]
        rows.extend(page["items"])
        assert len(rows) <= total
    assert len(rows) == total and len({row["id"] for row in rows}) == total
    history = client.get(f"/api/v1/runs/{run['runId']}/history").json()["items"]
    assert {row["eventId"] for row in rows if row["layer"] == "recorded"} == {
        item["eventId"] for item in history
    }
    assert journal.read_bytes() == original


def test_timeline_query_bound_is_closed_before_reading_unknown_run(client):
    response = client.get("/api/v1/runs/absent/timeline", params={"limit": 201})
    assert response.status_code == 422, response.text


def test_actual_evaluations_are_windows_with_separate_metric_and_assertion_results(client, recorded_fault):
    _, _, _, run, snapshot, journal = recorded_fault
    journal_before = journal.read_bytes()
    url = f"/api/v1/runs/{run['runId']}/timeline"
    previous = client.get(url, params={"limit": 1}).json()
    definitions = client.get(f"/api/v1/runs/{run['runId']}/definitions").json()["items"]
    evaluations = []
    for definition in definitions:
        response = client.post(
            f"/api/v1/runs/{run['runId']}/evaluations",
            headers={"Idempotency-Key": "timeline:" + definition["definitionRef"]},
            json={"snapshotId": snapshot["snapshotId"], "definitionRef": definition["definitionRef"],
                  "definitionDigest": definition["definitionDigest"], "evidenceRefs": [run["runId"] + ":reference-journal"]},
        )
        assert response.status_code == 202, response.text
        evaluations.append(client.get("/api/v1/evaluations/" + response.json()["evaluationId"]).json())
    refused = client.get(url, params={"cursor": previous["nextCursor"], "limit": 1})
    assert refused.status_code == 409 and refused.json()["code"] == "TIMELINE_CURSOR_STALE"
    response = client.get(url)
    assert response.status_code == 200, response.text
    rows = [r for r in response.json()["items"] if r["layer"] == "evaluation"]
    assert len(rows) == 2
    metric = next(r for r in rows if r["kind"] == "metric")
    assertion = next(r for r in rows if r["kind"] == "assertion")
    assert metric["verdict"] is None and metric["value"] is not None and metric["executionStatus"] == "complete"
    assert assertion["verdict"] == "pass" and assertion["executionStatus"] == "complete"
    for row in rows:
        original = next(r for r in evaluations if r["evaluationId"] == row["evaluationId"])
        assert row["definitionDigest"] == definition_digest(original["definition"])
        assert row["position"]["tick"] == "0" and row["position"]["endTick"] == "200000"
        assert row["window"] == original["definition"]["window"]
        assert row["evidenceDigests"] == original["evidenceDigests"] and row["matchesCurrentEvidence"] is True
        assert row["reasons"] == original["reasons"] and row["reasonsComplete"] is True
        assert row["evaluatorIdentity"] == original["evaluatorIdentity"]
        assert client.get("/api/v1/evaluations/" + row["evaluationId"]).json() == original
    assert journal.read_bytes() == journal_before


@pytest.mark.parametrize("malformation", ["source-time", "observation-values", "large-value", "gap-private-payload"])
def test_labelled_reader_metadata_failures_stay_unknown_and_omit_private_extras(client, recorded_fault, monkeypatch, malformation):
    _, _, _, run, _, journal = recorded_fault
    original = journal.read_bytes()
    # Deliberately malformed DTOs from a synthetic reader, not a canonical/live evidence claim.
    records = deepcopy(client.get(f"/api/v1/runs/{run['runId']}/history").json()["items"])
    sample = next(r for r in records if r["type"] == "observation.available")
    sample["payload"]["privateUnsupported"] = "OMIT-PRIVATE-SENTINEL"
    if malformation == "source-time":
        sample["sourceTime"] = "unsupported-clock-encoding"
    if malformation == "observation-values":
        sample["payload"]["values"] = ["unsupported-metadata"]
    if malformation == "large-value":
        sample["payload"]["values"]["value"] = 10 ** 500
    if malformation == "gap-private-payload":
        sample["type"] = "observation.gap"
        sample["payload"] = {"reason": "Synthetic fixture gap", "privateEndpoint": "OMIT-PRIVATE-SENTINEL"}
    monkeypatch.setattr("xverse_studio.api.app.read_journal", lambda *args: (records, "valid"))
    response = client.get(f"/api/v1/runs/{run['runId']}/timeline")
    assert response.status_code == 200, response.text
    assert "OMIT-PRIVATE-SENTINEL" not in response.text
    assert len(response.json()["items"]) > 0
    row = next(r for r in response.json()["items"] if r.get("eventId") == sample["eventId"])
    if malformation == "source-time":
        assert row["position"]["status"] == "unplaced" and row["position"]["tick"] is None
    if malformation in ["observation-values", "large-value"]:
        assert row["unsupportedValueCount"] >= 1
    assert journal.read_bytes() == original


@pytest.mark.parametrize("resolution", ["nanosecond", "unknown"])
def test_labelled_unadmitted_resolution_never_becomes_microseconds(client, recorded_fault, monkeypatch, resolution):
    _, _, _, run, _, _ = recorded_fault
    records = deepcopy(client.get(f"/api/v1/runs/{run['runId']}/history").json()["items"])
    sample = next(r for r in records if r["type"] == "observation.available")
    sample["sourceTime"].update(tick="9007199254740993", resolution=resolution)
    monkeypatch.setattr("xverse_studio.api.app.read_journal", lambda *args: (records, "valid"))
    report = client.get(f"/api/v1/runs/{run['runId']}/timeline").json()
    row = next(r for r in report["items"] if r.get("eventId") == sample["eventId"])
    assert row["position"]["tick"] == "9007199254740993"
    assert row["position"]["tickUnit"] is None and row["position"]["status"] == "unplaced"


def test_actual_corrupt_journal_is_not_observed_absence_and_bytes_are_preserved(client, recorded_fault):
    _, _, _, run, _, journal = recorded_fault
    original = journal.read_bytes()
    try:
        changed = original + b"invalid journal\n"
        journal.write_bytes(changed)
        response = client.get(f"/api/v1/runs/{run['runId']}/timeline")
        assert response.status_code == 200, response.text
        assert response.json()["recorded"]["integrity"] == "invalid"
        assert response.json()["recorded"]["coverage"] == "not_attested_by_timeline"
        assert response.json()["inputsComplete"]["recorded"] is False
        assert response.json()["clockDomainsComplete"] is False
        # The reader preserves a verified prefix after a corrupt tail. Keep it
        # inspectable, but never align it as trustworthy current evidence.
        recorded = [r for r in response.json()["items"] if r["layer"] == "recorded"]
        assert recorded and all(r["position"]["status"] == "unplaced" and r["evidenceIntegrity"] == "invalid" for r in recorded)
        assert journal.read_bytes() == changed
    finally:
        journal.write_bytes(original)


@pytest.mark.parametrize("query", [{"unknown": "value"}, [("limit", "1"), ("limit", "2")], {"cursor": "%%%"}])
def test_timeline_rejects_unsupported_duplicate_and_malformed_selectors(client, recorded_fault, query):
    run = recorded_fault[3]
    response = client.get(f"/api/v1/runs/{run['runId']}/timeline", params=query)
    assert response.status_code in (400, 422), response.text


@pytest.mark.parametrize("body", [{"offset": True, "identity": "wrong"}, {"offset": -1, "identity": "wrong"}, [], {"offset": 0, "identity": "wrong", "extra": True}])
def test_timeline_opaque_cursor_structure_cannot_bypass_bounds(client, recorded_fault, body):
    run = recorded_fault[3]
    cursor = base64.urlsafe_b64encode(json.dumps(body).encode()).decode().rstrip("=")
    response = client.get(f"/api/v1/runs/{run['runId']}/timeline", params={"cursor": cursor})
    assert response.status_code == 422 and response.json()["code"] == "TIMELINE_CURSOR_INVALID"


def test_timeline_large_source_ticks_are_exact_and_clocks_not_converted(client, recorded_fault, monkeypatch):
    run = recorded_fault[3]
    records = deepcopy(client.get(f"/api/v1/runs/{run['runId']}/history").json()["items"])
    samples = [r for r in records if r["type"] == "observation.available"]
    samples[0]["sourceTime"]["tick"] = "9007199254740993"
    samples[1]["sourceTime"].update(tick="9007199254740994", clockDomain="unmapped-device-time")
    monkeypatch.setattr("xverse_studio.api.app.read_journal", lambda *args: (records, "valid"))
    response = client.get(f"/api/v1/runs/{run['runId']}/timeline")
    assert response.status_code == 200, response.text
    report = response.json()
    first = next(r for r in report["items"] if r.get("eventId") == samples[0]["eventId"])
    second = next(r for r in report["items"] if r.get("eventId") == samples[1]["eventId"])
    assert first["position"]["tick"] == "9007199254740993" and first["position"]["status"] == "aligned"
    assert second["position"]["tick"] == "9007199254740994" and second["position"]["status"] == "unplaced"
    assert second["position"]["reason"] == "CLOCK_NOT_SELECTED" and second["position"]["tickUnit"] is None
    response = client.get(f"/api/v1/runs/{run['runId']}/timeline", params={"clockDomain": "unmapped-device-time"})
    assert response.status_code == 200, response.text
    selected = next(r for r in response.json()["items"] if r.get("eventId") == samples[1]["eventId"])
    assert selected["position"]["status"] == "unplaced" and selected["position"]["reason"] == "TICK_ENCODING_UNADMITTED"
    assert response.json()["intentClockCodec"] is None


def test_timeline_processing_caps_remain_visible_and_do_not_claim_clock_completeness(client, recorded_fault, monkeypatch):
    run = recorded_fault[3]
    original = recorded_fault[-1].read_bytes()
    monkeypatch.setattr("xverse_studio.timeline.MAX_RECORDS", 2)
    monkeypatch.setattr("xverse_studio.timeline.MAX_INTENTS", 1)
    report = client.get(f"/api/v1/runs/{run['runId']}/timeline").json()
    assert report["counts"]["recordedInputs"] > report["counts"]["recordedInputsConsidered"] == 2
    assert report["counts"]["intentInputs"] > report["counts"]["intentInputsConsidered"] == 1
    assert report["inputsComplete"]["recorded"] is False and report["inputsComplete"]["intents"] is False
    assert report["clockDomainsComplete"] is False
    assert report["reduction"] == {"method": "page", "canonical": False, "pageStart": 0, "pageSize": 100}
    assert any(d["code"] == "TIMELINE_INPUT_LIMIT" for d in report["diagnostics"])
    assert recorded_fault[-1].read_bytes() == original


def test_timeline_refuses_managed_snapshot_tamper_without_using_current_project(client, recorded_fault):
    run, snapshot = recorded_fault[3:5]
    file = client.app.state.studio.store.root / "snapshots" / snapshot["snapshotId"] / "snapshot.json"
    original = file.read_bytes()
    try:
        file.write_bytes(original + b"tampered")
        response = client.get(f"/api/v1/runs/{run['runId']}/timeline")
        assert response.status_code == 422, response.text
        assert response.json()["code"] == "SNAPSHOT_INTEGRITY"
        assert file.read_bytes().endswith(b"tampered")
    finally:
        file.write_bytes(original)


def test_recorded_clock_codec_remains_separate_from_unproven_frozen_intent_codec(client, recorded_fault, monkeypatch):
    run = recorded_fault[3]
    runs = client.app.state.studio.runs
    read = runs.read
    def changed(run_id):
        result = deepcopy(read(run_id))
        result["effectivePlanDigest"] = "sha256:" + "f" * 64
        return result
    monkeypatch.setattr(runs, "read", changed)
    response = client.get(f"/api/v1/runs/{run['runId']}/timeline")
    assert response.status_code == 200, response.text
    report = response.json()
    assert report["intentClockCodec"] is None and report["tickUnit"] == "microsecond"
    assert any(r["layer"] == "recorded" and r["position"]["status"] == "aligned" for r in report["items"])
    assert all(r["position"]["status"] == "unplaced" for r in report["items"] if r["layer"] == "intent")
    assert not any(r["kind"] == "intent.provider_configuration" for r in report["items"])
