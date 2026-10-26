"""Connection admission over declared semantics, against fixtures with expected outcomes."""

import importlib.util
from pathlib import Path

import pytest
from ruamel.yaml import YAML

from xverse_studio.connections import admission_diagnostics, admit_connections
from xverse_studio.xdl import XDLAdapter

_PATH = Path(__file__).resolve().parents[1] / "fixtures/connections/connection_fixtures.py"
_spec = importlib.util.spec_from_file_location("connection_fixtures", _PATH)
fixtures = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(fixtures)


def report(name):
    documents, expected = fixtures.fixture(name)
    validation = XDLAdapter().validate(documents)
    return documents, expected, validation, admit_connections(documents, validation)


@pytest.mark.parametrize("name", sorted(fixtures.FIXTURES))
def test_fixture_declared_semantics(name):
    _, expected, validation, result = report(name)
    assert validation["valid"] is expected["valid"]
    admission = {c["ref"].rsplit("#", 1)[1]: c["admission"] for c in result["connections"]}
    for flow, status in expected["admission"].items():
        assert admission[flow] == status, (flow, admission)
    assert {d["code"] for d in admission_diagnostics(result)} == expected["codes"]
    assert len(result["cycles"]) == expected["cycles"]
    assert len(result["links"]) == expected.get("links", 0)
    assert len(result["couplings"]) == expected.get("couplings", 0)
    if "blocking" in expected:
        assert result["blocking"] == expected["blocking"]
    for connection in result["connections"]:
        assert connection["kind"] == "data_flow"
        assert all(c["pointer"] for c in connection["checks"])
        # Admission is never better than its worst check; unevaluated intents are not passes.
        statuses = {c["status"] for c in connection["checks"]}
        assert statuses <= {"pass", "declared", "unknown", "unsupported", "fail"}
        if connection["admission"] == "admitted":
            assert statuses <= {"pass", "declared"}


def test_no_contract_is_admitted_and_physical_coupling_is_unsupported():
    _, _, _, result = report("compatible")
    assert result["admittedContracts"] == {
        "converter": False, "versionCompatibility": False, "quality": False,
        "causality": False, "modelCoupling": False}
    assert result["couplings"] == [] and result["sourceValid"]
    assert result["blocking"] == 0 and result["complete"]
    clock = next(c for c in result["connections"][0]["checks"] if c["check"] == "clock")
    assert clock["status"] == "declared" and "not evaluated" in clock["message"]


def test_feedback_cycle_lists_members_and_does_not_claim_correctness():
    _, _, _, result = report("feedback-cycle")
    cycle = result["cycles"][0]
    assert cycle["members"] == [
        "xdl://org.xverse.studio.process-control/system/reference-loop#controller",
        "xdl://org.xverse.studio.process-control/system/reference-loop#plant",
    ]
    assert "not proof of executable correctness" in cycle["message"]


def test_conversion_is_never_performed():
    documents, _ = fixtures.fixture("explicit-converter")
    before = dict(documents)
    result = admit_connections(documents, XDLAdapter().validate(documents))
    admission_diagnostics(result)
    assert documents == before
    check = next(c for c in result["connections"][0]["checks"] if c["check"] == "conversion")
    assert check["status"] == "unsupported" and "nothing is converted" in check["message"]


def test_rejected_flows_are_not_cycle_edges():
    _, _, _, result = report("direction-mismatch")
    assert result["cycles"] == []


def _put_system(client, project, documents):
    did = next(k for k, d in project["documents"].items() if d["path"].endswith("/system.xdl.yaml"))
    response = client.put(
        f"/api/v1/projects/{project['projectId']}/documents/{did}",
        headers={"If-Match": str(project["revision"])},
        json={"content": documents["system.xdl.yaml"], "format": "yaml"},
    )
    assert response.status_code == 200, response.text
    return response.json()


def test_api_reports_connections_and_preflight_blocks_unsupported_semantics(client):
    project = client.post("/api/v1/projects", json={"name": "connections"}).json()
    baseline = client.get(f"/api/v1/projects/{project['projectId']}/connections").json()
    assert baseline["blocking"] == 0 and baseline["revision"] == project["revision"]
    assert {c["admission"] for c in baseline["connections"]} == {"admitted"}
    documents, _ = fixtures.fixture("explicit-converter")
    project = _put_system(client, project, documents)
    report = client.get(f"/api/v1/projects/{project['projectId']}/connections").json()
    assert report["blocking"] == 1
    preflight = client.post(
        f"/api/v1/projects/{project['projectId']}/preflights",
        json={"revision": project["revision"]},
    ).json()
    assert preflight["status"] == "blocked"
    # The reference provider admits a linear converter, but this flow declares none (ADR-0016).
    assert "CONVERSION_INVALID" in {d["code"] for d in preflight["diagnostics"]}
    # A provider without converter contracts leaves the same declaration unsupported.
    lite = client.get(f"/api/v1/projects/{project['projectId']}/connections?providerId=xverse.lite").json()
    assert {c["code"] for c in lite["connections"][0]["checks"] if c["check"] == "conversion"} == {"CONVERSION_UNSUPPORTED"}
    # Source bytes are preserved exactly; admission never rewrites them.
    current = client.get(f"/api/v1/projects/{project['projectId']}").json()
    system = next(d for d in current["documents"].values() if d["path"].endswith("/system.xdl.yaml"))
    assert YAML(typ="safe").load(system["content"])["spec"]["interfaces"][0]["compatibility"] == "explicit-converter"


def test_invalid_sources_leave_unaddressed_flows_unknown_not_admitted():
    documents, _ = fixtures.fixture("compatible")
    result = admit_connections(documents, {"valid": False, "diagnostics": []})
    assert not result["sourceValid"]
    assert {c["admission"] for c in result["connections"]} == {"unknown"}


def test_flows_beyond_the_bound_block_execution():
    def many(spec):
        spec["flows"] += [
            {**spec["flows"][0], "id": f"extra-{i}"} for i in range(fixtures_bound())
        ]

    documents = fixtures._variant(many)
    result = admit_connections(documents, {"valid": True, "diagnostics": []})
    assert not result["complete"] and result["blocking"] >= 1
    assert "CONNECTION_LIMIT_EXCEEDED" in {d["code"] for d in admission_diagnostics(result)}


def fixtures_bound():
    from xverse_studio.connections import MAX_CONNECTIONS

    return MAX_CONNECTIONS


def test_one_flow_is_counted_once_per_endpoint():
    def loop(spec):
        spec["endpoints"].append(
            {"id": "plant-io", "ownerId": "plant", "interfaceId": "state",
             "direction": "bidirectional", "multiplicity": "1"})
        spec["flows"].append({"id": "self", "sourceEndpointId": "plant-io",
                              "destinationEndpointIds": ["plant-io"], "interfaceId": "state",
                              "deliveryIntent": "ordered"})

    documents = fixtures._variant(loop)
    result = admit_connections(documents, XDLAdapter().validate(documents))
    endpoint = next(e for e in result["endpoints"] if e["ref"].endswith("#plant-io"))
    assert endpoint["status"] == "pass"
