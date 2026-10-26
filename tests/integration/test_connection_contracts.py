"""ADR-0016: the owned provider admits and executes exactly its declared connection contracts."""
import json
import math
import time

import pytest
from ruamel.yaml import YAML

from xverse_studio.connections import admit_connections
from xverse_studio.providers.registry import descriptors
from xverse_studio.xdl import XDLAdapter, examples, reference_configuration
from xverse_studio.xdl.examples import CONNECTIONS_NAMESPACE, dump_yaml

SAFE = YAML(typ="safe")


def _feedback_project(client, change=None, duration=0.5, fault=None):
    project = client.post("/api/v1/projects", json={"name": "Feedback contracts", "blueprintRef": "reference-feedback"}).json()
    pid = project["projectId"]
    project = client.post(f"/api/v1/projects/{pid}/edits", headers={"If-Match": str(project["revision"])},
                          json={"baseRevision": project["revision"], "edits": [
                              {"kind": "set_parameter", "parameterId": "duration", "value": duration},
                              *([{"kind": "set_parameter", "parameterId": "fault", "value": fault}] if fault else [])]}).json()
    if change:
        system_id = next(i for i, d in project["documents"].items() if d["path"].endswith("/system.xdl.yaml"))
        system = SAFE.load(project["documents"][system_id]["content"])
        change(system)
        saved = client.put(f"/api/v1/projects/{pid}/documents/{system_id}", headers={"If-Match": str(project["revision"])},
                           json={"content": dump_yaml(system)})
        assert saved.status_code == 200, saved.text
        project = saved.json()
    return project


def _flow(system, identifier):
    return next(f for f in system["spec"]["flows"] if f["id"] == identifier)


def _run(client, project):
    preflight = client.post(f"/api/v1/projects/{project['projectId']}/preflights", json={"revision": project["revision"]}).json()
    assert preflight["status"] == "ready", preflight
    response = client.post("/api/v1/runs", headers={"Idempotency-Key": "contracts-" + project["projectId"]},
                           json={"snapshotId": preflight["snapshotId"], "preflightId": preflight["preflightId"]})
    assert response.status_code == 202, response.text
    run_id, deadline = response.json()["runId"], time.monotonic() + 15
    while time.monotonic() < deadline:
        run = client.get("/api/v1/runs/" + run_id).json()
        if run["state"] == "stopped":
            return run
        assert run["state"] not in {"failed", "unknown"}, run
        time.sleep(.05)
    raise AssertionError(run)


def test_feedback_blueprint_admits_and_executes_the_declared_loop_and_converter(client):
    def scaled(system):
        _flow(system, "state-flow")["extensions"][CONNECTIONS_NAMESPACE]["converter"].update(scale=50.0, offset=10.0)
    project = _feedback_project(client, scaled)
    report = client.get(f"/api/v1/projects/{project['projectId']}/connections").json()
    assert report["blocking"] == 0 and report["providerId"] == "studio.reference"
    assert [(c["status"], c["delayedFlows"]) for c in report["cycles"]] == [("admitted", ["command-flow"])]
    conversion = next(check for c in report["connections"] if c["ref"].endswith("#state-flow")
                      for check in c["checks"] if check["check"] == "conversion")
    assert conversion["status"] == "pass" and conversion["mapping"] == {
        "kind": "linear", "fromUnit": "1", "toUnit": "%", "scale": 50.0, "offset": 10.0}
    run = _run(client, project)
    journal = client.app.state.studio.runs.directory(run["runId"]) / "evidence.jsonl"
    records = [json.loads(line) for line in journal.read_text().splitlines() if line.strip()]
    samples = [r for r in records if r.get("type") == "observation.available"]
    assert len(samples) == 5
    for item in samples:
        values, units = item["payload"]["values"], item["payload"]["units"]
        # The declared converter maps exactly the plant state its flow carries, in its declared unit.
        assert math.isclose(values["observed"], 50.0 * values["value"] + 10.0) and units["observed"] == "%"
        assert item["payload"]["conversion"]["source"] == "value" and units["value"] == "1"
    # Unit delay on the command flow: the plant applies each step's command only at the next step.
    for before, after in zip(samples, samples[1:]):
        b, a = before["payload"]["values"], after["payload"]["values"]
        assert math.isclose(b["control"], 0.8 * (b["target"] - b["measured"]))
        assert math.isclose(a["value"], b["value"] + b["control"] * 0.1)


def _samples(client, run):
    journal = client.app.state.studio.runs.directory(run["runId"]) / "evidence.jsonl"
    return [r for r in (json.loads(line) for line in journal.read_text().splitlines() if line.strip())
            if r.get("type") == "observation.available"]


def test_converter_follows_the_plant_state_while_a_stuck_sensor_freezes_the_measurement(client):
    project = _feedback_project(client, duration=0.6, fault="stuck-sensor")
    samples = [r["payload"]["values"] for r in _samples(client, _run(client, project))]
    assert any(not math.isclose(v["measured"], v["value"]) for v in samples)  # the fault really diverges them
    assert all(math.isclose(v["observed"], 100.0 * v["value"]) for v in samples)


@pytest.mark.parametrize("change,code", [
    # Without the declared delay the loop is algebraic; no algebraic-loop solver is admitted.
    (lambda s: _flow(s, "command-flow").pop("extensions"), "CAUSALITY_CONTRACT_UNSUPPORTED"),
    # The converter must map from the interface unit, with a finite non-zero scale.
    (lambda s: _flow(s, "state-flow")["extensions"][CONNECTIONS_NAMESPACE]["converter"].update(fromUnit="s"), "CONVERSION_INVALID"),
    (lambda s: _flow(s, "state-flow")["extensions"][CONNECTIONS_NAMESPACE]["converter"].update(scale=0), "CONVERSION_INVALID"),
    # Coefficients are bounded so converted samples stay finite.
    (lambda s: _flow(s, "state-flow")["extensions"][CONNECTIONS_NAMESPACE]["converter"].update(scale=1e7), "CONVERSION_INVALID"),
    # A declared converter the provider does not execute in this topology is refused at preflight.
    (lambda s: _flow(s, "state-flow")["extensions"][CONNECTIONS_NAMESPACE]["converter"].update(toUnit="K"), "CAPABILITY_UNSUPPORTED"),
    # A converter may not be attached to an exact interface.
    (lambda s: _flow(s, "command-flow").update(extensions={CONNECTIONS_NAMESPACE: {"converter": {
        "kind": "linear", "fromUnit": "1", "toUnit": "%", "scale": 2.0, "offset": 0.0}}}), "CONVERSION_INVALID"),
])
def test_undeclared_or_invalid_contracts_block_admission(client, change, code):
    project = _feedback_project(client, change)
    preflight = client.post(f"/api/v1/projects/{project['projectId']}/preflights", json={"revision": project["revision"]}).json()
    assert preflight["status"] == "blocked"
    assert code in {d["code"] for d in preflight["diagnostics"]}
    assert client.get("/api/v1/runs").json()["items"] == []


def test_connection_level_verdicts_for_zero_scale_and_unknown_providers(client):
    project = _feedback_project(client, lambda s: _flow(s, "state-flow")["extensions"][CONNECTIONS_NAMESPACE]["converter"].update(scale=0))
    report = client.get(f"/api/v1/projects/{project['projectId']}/connections").json()
    state = next(c for c in report["connections"] if c["ref"].endswith("#state-flow"))
    assert {(k["status"], k["code"]) for k in state["checks"] if k["check"] == "conversion"} == {("fail", "CONVERSION_INVALID")}
    assert client.get(f"/api/v1/projects/{project['projectId']}/connections?providerId=nope").status_code == 404


def test_connections_profile_identity_is_pinned(client):
    project = _feedback_project(client)
    profile_id = next(i for i, d in project["documents"].items() if d["path"].endswith("/connections-profile.xdl.yaml"))
    profile = SAFE.load(project["documents"][profile_id]["content"])
    profile["metadata"]["version"] = "9.9.9"
    saved = client.put(f"/api/v1/projects/{project['projectId']}/documents/{profile_id}", headers={"If-Match": str(project["revision"])},
                       json={"content": dump_yaml(profile)}).json()
    preflight = client.post(f"/api/v1/projects/{project['projectId']}/preflights", json={"revision": saved["revision"]}).json()
    assert preflight["status"] == "blocked"
    assert {"PROFILE_UNRESOLVED", "PROFILE_CONFLICT"} & {d["code"] for d in preflight["diagnostics"]}


def _documents(change):
    entry = next(e for e in examples() if e["id"] == "reference-feedback")
    documents = {"xdl/" + name: content for name, content in entry["documents"].items()}
    system = SAFE.load(documents["xdl/system.xdl.yaml"])
    change(system)
    documents["xdl/system.xdl.yaml"] = dump_yaml(system)
    return documents


REFERENCE = next(d for d in descriptors() if d["providerId"] == "studio.reference")


def test_every_loop_needs_a_delay_and_default_clocks_resolve():
    def hidden_algebraic_loop(system):
        _flow(system, "command-flow").pop("extensions")
        _flow(system, "feedback-flow")["extensions"] = {CONNECTIONS_NAMESPACE: {"causality": {"kind": "unit-delay"}}}
        system["spec"]["flows"].append({"id": "direct-flow", "sourceEndpointId": "plant-out", "destinationEndpointIds": ["controller-in"],
                                        "interfaceId": "state", "deliveryIntent": "ordered", "timeDomainId": "simulation-time"})
    documents = _documents(hidden_algebraic_loop)
    report = admit_connections(documents, XDLAdapter().validate(documents), REFERENCE)
    assert [c["status"] for c in report["cycles"]] == ["unsupported"] and "algebraic" in report["cycles"][0]["message"]

    def default_clock(system):
        for flow in system["spec"]["flows"]:
            flow.pop("timeDomainId")
    documents = _documents(default_clock)
    assert XDLAdapter().validate(documents)["valid"]
    report = admit_connections(documents, XDLAdapter().validate(documents), REFERENCE)
    assert [c["status"] for c in report["cycles"]] == ["admitted"] and report["blocking"] == 0

    def stray_delay(system):
        _flow(system, "state-flow")["extensions"][CONNECTIONS_NAMESPACE]["causality"] = {"kind": "unit-delay"}
    documents = _documents(stray_delay)
    report = admit_connections(documents, XDLAdapter().validate(documents), REFERENCE)
    state = next(c for c in report["connections"] if c["ref"].endswith("#state-flow"))
    assert ("causality", "declared") in {(k["check"], k["status"]) for k in state["checks"]}


def test_a_provider_without_contracts_admits_neither_the_loop_nor_the_converter(client):
    project = _feedback_project(client)
    report = client.get(f"/api/v1/projects/{project['projectId']}/connections?providerId=xverse.lite").json()
    assert report["admittedContracts"]["converter"] is False and report["admittedContracts"]["causality"] is False
    assert {c["status"] for c in report["cycles"]} == {"unsupported"}
    codes = {check.get("code") for c in report["connections"] for check in c["checks"]}
    assert {"CONVERSION_UNSUPPORTED", "CAUSALITY_CONTRACT_UNSUPPORTED"} <= codes


def test_existing_examples_carry_no_connection_contract_configuration():
    for entry in examples()[:2]:
        documents = {"xdl/" + name: content for name, content in entry["documents"].items()}
        config = reference_configuration(documents, XDLAdapter().compile(documents))
        assert "converter" not in config and "causality" not in config
