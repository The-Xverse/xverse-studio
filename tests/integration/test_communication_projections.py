"""T056: declared, resolved and observed communication stay distinct, with scope and freshness."""
import time

import pytest
from ruamel.yaml import YAML

from xverse_studio.connections.projections import ProjectionUnavailable, project_communication
from xverse_studio.xdl import examples
from xverse_studio.xdl.examples import dump_yaml


def _run(client, project):
    preflight = client.post(f"/api/v1/projects/{project['projectId']}/preflights", json={"revision": project["revision"]}).json()
    assert preflight["status"] == "ready", preflight
    response = client.post("/api/v1/runs", headers={"Idempotency-Key": "communication-" + project["projectId"]},
                           json={"snapshotId": preflight["snapshotId"], "preflightId": preflight["preflightId"]})
    run_id, deadline = response.json()["runId"], time.monotonic() + 15
    while time.monotonic() < deadline:
        run = client.get("/api/v1/runs/" + run_id).json()
        if run["state"] == "stopped":
            return run
        assert run["state"] not in {"failed", "unknown"}, run
        time.sleep(.05)
    raise AssertionError(run)


def _feedback(client):
    project = client.post("/api/v1/projects", json={"name": "Communication", "blueprintRef": "reference-feedback"}).json()
    return client.post(f"/api/v1/projects/{project['projectId']}/edits", headers={"If-Match": str(project["revision"])},
                       json={"baseRevision": project["revision"], "edits": [
                           {"kind": "set_parameter", "parameterId": "duration", "value": 0.5}]}).json()


def test_a_draft_is_declared_only(client):
    project = _feedback(client)
    report = client.get(f"/api/v1/projects/{project['projectId']}/communication").json()
    assert {f["flowId"] for f in report["flows"]} == {"command-flow", "state-flow", "measurement-flow", "feedback-flow"}
    for flow in report["flows"]:
        assert flow["declared"]["status"] == "declared"
        assert flow["resolved"]["status"] == "pending" and flow["observed"]["status"] == "no_run"
    command = next(f for f in report["flows"] if f["flowId"] == "command-flow")
    assert command["contract"] == {"causality": {"kind": "unit-delay"}}


def test_a_run_resolves_and_observes_flows_distinctly_with_scope_and_freshness(client):
    project = _feedback(client)
    run = _run(client, project)
    report = client.get(f"/api/v1/projects/{project['projectId']}/communication", params={"runId": run["runId"]}).json()
    flows = {f["flowId"]: f for f in report["flows"]}
    assert report["transport"] == "in-process (owned reference worker)" and report["runState"] == "stopped"
    for flow in flows.values():
        assert flow["resolved"]["status"] == "resolved" and flow["resolved"]["providerId"] == "studio.reference"
    observed = flows["state-flow"]["observed"]
    assert observed["status"] == "observed" and observed["samples"] == 5 and observed["freshness"] == "final"
    assert observed["source"] == {"providerId": "studio.reference", "evidenceClass": "observed"}
    assert observed["evidenceScope"] == "owned_reference" and observed["integrity"] == "valid"
    assert any("no network transport" in text and "native X-COM" in text for text in observed["limitations"])
    # A bound flow no observer targets is not collected; that is not a fault and not traffic.
    assert flows["command-flow"]["observed"]["status"] == "not_collected"
    assert flows["feedback-flow"]["observed"]["status"] == "not_collected"
    other = client.post("/api/v1/projects", json={"name": "Other"}).json()
    assert client.get(f"/api/v1/projects/{other['projectId']}/communication", params={"runId": run["runId"]}).status_code == 404


def _documents():
    entry = next(e for e in examples() if e["id"] == "reference-feedback")
    return {"xdl/" + name: content for name, content in entry["documents"].items()}


SYSTEM = "xdl://org.xverse.studio.feedback/system/reference-loop"
SCENARIO = "xdl://org.xverse.studio.feedback/scenario/reference-response"


def _record(seconds_ago, now, observer="state-observer", recorded=None):
    return {"type": "observation.available", "schemaVersion": "1.0",
            "recordedAt": now - seconds_ago if recorded is None else recorded,
            "sourceTime": {"tick": "0", "clockDomain": "simulation-time"},
            "source": {"providerId": "studio.reference", "version": "1.0.0"}, "evidenceClass": "observed",
            "payload": {"observerRef": observer, "evidenceScope": "owned_reference"}}


def _project(records, state="running", integrity="valid", now=1_000_000.0, scenario=SCENARIO):
    documents = _documents()
    snapshot = {"documents": documents, "selection": {"scenarioRef": scenario},
                "configuration": {"resolvedFlows": [SYSTEM + "#state-flow"]}}
    run = {"runId": "r", "state": state, "providerId": "studio.reference", "evidenceScope": "owned_reference"}
    report = project_communication(documents, run=run, snapshot=snapshot, records=records, integrity=integrity, now=now)
    return {f["flowId"]: f for f in report["flows"]}


def test_freshness_is_live_stale_final_partial_or_unknown_never_guessed():
    now = 1_000_000.0
    observed = lambda **kw: _project(**kw)["state-flow"]["observed"]
    assert observed(records=[_record(1, now)])["freshness"] == "live"
    stale = observed(records=[_record(60, now)])
    assert stale["freshness"] == "stale" and stale["ageSeconds"] == 60
    assert observed(records=[_record(1, now)], state="stopped")["freshness"] == "final"
    assert observed(records=[_record(1, now)], state="stopped", integrity="verified_prefix")["freshness"] == "partial"
    assert observed(records=[_record(1, now)], state="unknown")["freshness"] == "unknown"
    # Missing or future receipt times are unknown, never "live"; RFC3339 text is decoded, never a crash.
    missing = _record(1, now)
    missing.pop("recordedAt")
    assert observed(records=[missing])["freshness"] == "unknown"
    assert observed(records=[_record(-30, now)])["freshness"] == "unknown"
    text = observed(records=[_record(0, now, recorded="1970-01-12T13:46:39Z")])
    assert text["status"] == "observed" and text["freshness"] == "live"


def test_collection_states_distinguish_not_collected_not_yet_and_not_observed():
    flows = _project([])
    assert flows["state-flow"]["observed"]["status"] == "collected_none"
    assert flows["command-flow"]["observed"]["status"] == "not_collected"
    assert flows["command-flow"]["resolved"]["status"] == "not_resolved"  # not in the frozen resolved flows
    # An ended run whose observer recorded nothing is an unmet expectation, not silence.
    assert _project([], state="stopped")["state-flow"]["observed"]["status"] == "not_observed"


def test_unverified_evidence_and_foreign_scenarios_are_never_presented_as_observed():
    now = 1_000_000.0
    invalid = _project([_record(1, now)], integrity="invalid")["state-flow"]["observed"]
    assert invalid["status"] == "unverified" and "invalid" in invalid["reason"]
    # Observers of another Scenario do not attribute samples to this run's flows.
    foreign = _project([_record(1, now)], scenario="xdl://org.xverse.studio.feedback/scenario/other")
    assert foreign["state-flow"]["observed"]["status"] == "not_collected"


def test_a_run_without_frozen_inputs_or_scenario_is_refused_not_projected_from_the_draft():
    with pytest.raises(ProjectionUnavailable):
        project_communication(_documents(), run={"runId": "r", "state": "stopped"}, snapshot={}, records=[], integrity="valid")
    with pytest.raises(ProjectionUnavailable):
        project_communication(_documents(), run={"runId": "r", "state": "stopped"}, snapshot={"documents": _documents()},
                              records=[], integrity="valid")


def test_samples_are_attributed_to_the_observed_systems_flow_only():
    documents = _documents()
    other = YAML(typ="safe").load(documents["xdl/system.xdl.yaml"])
    other["metadata"]["name"] = "other-loop"  # a second System with the same flow ids
    documents["xdl/other-system.xdl.yaml"] = dump_yaml(other)
    snapshot = {"documents": documents, "selection": {"scenarioRef": SCENARIO}, "configuration": {"resolvedFlows": []}}
    run = {"runId": "r", "state": "stopped", "providerId": "studio.reference"}
    report = project_communication(documents, run=run, snapshot=snapshot, records=[_record(1, 1e6)], integrity="valid", now=1e6)
    states = {f["ref"]: f["observed"]["status"] for f in report["flows"] if f["flowId"] == "state-flow"}
    assert states == {SYSTEM + "#state-flow": "observed",
                      "xdl://org.xverse.studio.feedback/system/other-loop#state-flow": "not_collected"}


def test_malformed_record_fields_never_crash_the_projection():
    broken = _record(1, 1e6)
    broken["sourceTime"], broken["source"] = ["not", "a", "mapping"], "text"
    observed = _project([broken, {"type": "observation.available", "payload": ["x"]}])["state-flow"]["observed"]
    assert observed["status"] == "observed" and observed["firstTick"] is None


def test_resolution_uses_its_own_flow_list_and_evidence_refs_stay_unchanged():
    from xverse_studio.xdl import XDLAdapter, reference_configuration

    for entry in examples():
        documents = {"xdl/" + name: content for name, content in entry["documents"].items()}
        config = reference_configuration(documents, XDLAdapter().compile(documents))
        assert not any(ref.endswith("#command-flow") for ref in config["elementRefs"])
        assert any(ref.endswith("#command-flow") for ref in config["resolvedFlows"])


def test_http_refuses_a_run_whose_frozen_inputs_are_gone(client, monkeypatch):
    project = _feedback(client)
    run = _run(client, project)
    store = client.app.state.studio.store
    original = store.get
    monkeypatch.setattr(store, "get", lambda kind, key, *a, **k: {} if kind == "snapshot" else original(kind, key, *a, **k))
    response = client.get(f"/api/v1/projects/{project['projectId']}/communication", params={"runId": run["runId"]})
    assert response.status_code == 409 and response.json()["code"] == "SNAPSHOT_UNAVAILABLE"


def test_lite_evidence_is_labelled_lite_never_native_xcom():
    documents = _documents()
    report = project_communication(documents, run={"runId": "r", "state": "stopped", "providerId": "xverse.lite"},
                                   snapshot={"documents": documents, "selection": {"scenarioRef": SCENARIO},
                                             "configuration": {"resolvedFlows": []}})
    assert report["transport"] == "Lite X-COM bridge"
    assert all(f["resolved"]["status"] == "not_resolved" for f in report["flows"])
    assert any("Native X-COM is not integrated" in text for text in report["limitations"])
