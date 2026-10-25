"""Evidence-linked diagnostic explanations: facts, consequences, hypotheses and unknowns."""

import importlib.util
from pathlib import Path
import time

import pytest

from xverse_studio.diagnostics import (
    ACTIONS,
    CLASSES,
    MAX_REFS,
    explain_preflight,
    explain_run,
)

_PATH = (
    Path(__file__).resolve().parents[1]
    / "fixtures/evidence/create_recorded_evidence.py"
)
_spec = importlib.util.spec_from_file_location("diagnostics_evidence_fixture", _PATH)
_fixture = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_fixture)


def record(sequence, kind, payload=None, clock="simulation-time", tick="0"):
    return {
        "eventId": f"run-x:{sequence}",
        "sequence": str(sequence),
        "type": kind,
        "sourceTime": None
        if clock is None
        else {"tick": tick, "clockDomain": clock, "resolution": "microsecond"},
        "payload": payload or {},
    }


def observation(sequence, observer="state-observer", clock="simulation-time", **values):
    return record(
        sequence,
        "observation.available",
        {"observerRef": observer, "values": values or {"value": 1.0}},
        clock=clock,
        tick=str(sequence),
    )


RUN = {
    "runId": "run-x",
    "snapshotId": "snap-x",
    "state": "stopped",
    "stateVersion": 3,
    "cleanup": "complete",
    "evidence": "complete",
    "evidenceScope": "owned_reference",
}


def checked(explanation):
    """Shared invariants: every claim is anchored, inference cites only its own facts."""
    assert explanation["explanationVersion"] == "1.0"
    assert explanation["rootCause"] == "not_inferred"
    assert set(explanation["evaluatedClasses"]) <= set(CLASSES)
    for finding in explanation["findings"]:
        assert finding["class"] in CLASSES
        assert finding["class"] in explanation["evaluatedClasses"]
        assert finding["facts"], finding
        ids = {fact["id"] for fact in finding["facts"]}
        for fact in finding["facts"]:
            assert fact["evidence"] and len(fact["evidence"]) <= MAX_REFS
            assert all("kind" in ref for ref in fact["evidence"])
        for consequence in finding["consequences"]:
            assert consequence["basis"] and set(consequence["basis"]) <= ids
        for hypothesis in finding["hypotheses"]:
            assert hypothesis["status"] == "unconfirmed"
            assert set(hypothesis["basis"]) <= ids
        assert all(a["action"] in ACTIONS for a in finding["nextActions"])
    return {f["class"]: f for f in explanation["findings"]}


def test_normal_completed_run_has_no_findings_and_infers_no_health():
    records = [
        record(1, "run.state_changed", {"state": "running"}),
        observation(2),
        record(3, "run.state_changed", {"state": "stopped"}),
    ]
    explanation = explain_run(
        RUN, records, "valid", expected_observers=["state-observer"]
    )
    assert checked(explanation) == {}
    assert explanation["findingCount"] == 0 and explanation["findingsComplete"]


def test_process_exit_identifies_exit_and_affected_elements_but_not_its_cause():
    run = {
        **RUN,
        "state": "failed",
        "reason": "REFERENCE_WORKER_ERROR",
        "cleanup": "unknown",
        "evidence": "partial",
        "elementRefs": ["xdl://org.example/system/s#plant"],
    }
    records = [
        observation(1),
        record(2, "log.appended", {"severity": "error", "message": "failed"}),
    ]
    findings = checked(explain_run(run, records, "verified_prefix"))
    exit_ = findings["process_exit"]
    assert exit_["code"] == "REFERENCE_WORKER_ERROR"
    assert exit_["elementRefs"] == run["elementRefs"]
    cited = [ref.get("eventId") for fact in exit_["facts"] for ref in fact["evidence"]]
    assert "run-x:2" in cited
    assert exit_["hypotheses"] == []
    assert any("root cause is not established" in u for u in exit_["unknowns"])
    assert exit_["nextActions"][0]["action"] == "inspect_events"
    assert findings["failed_cleanup"]["severity"] == "warning"
    assert findings["unavailable_evidence"]["code"] == "EVIDENCE_PARTIAL"


def test_reported_input_mismatch_is_a_reported_fact_not_an_unknown_cause():
    run = {
        **RUN,
        "state": "failed",
        "reason": "EFFECTIVE_INPUT_MISMATCH",
        "evidence": "unavailable",
    }
    findings = checked(explain_run(run, [], "unavailable"))
    exit_ = findings["process_exit"]
    assert exit_["title"] == "The owned workload did not start."
    assert exit_["unknowns"] == []
    assert any("did not match" in fact["statement"] for fact in exit_["facts"])
    evidence = findings["unavailable_evidence"]
    assert evidence["code"] == "EVIDENCE_NOT_PRODUCED"
    assert evidence["severity"] == "info" and evidence["nextActions"] == []


def test_failed_launch_is_not_described_as_an_ended_execution():
    run = {
        **RUN,
        "state": "failed",
        "reason": "LAUNCH_FAILED",
        "evidence": "unavailable",
    }
    findings = checked(explain_run(run, [], "unavailable"))
    exit_ = findings["process_exit"]
    assert exit_["consequences"][0]["statement"] == (
        "No execution took place, so no results exist."
    )
    assert exit_["unknowns"] == ["Why the launch failed is not established."]
    assert findings["unavailable_evidence"]["code"] == "EVIDENCE_NOT_PRODUCED"


@pytest.mark.parametrize("state", ["preparing", "running"])
def test_unreadable_active_journal_is_information_not_evidence_loss(state):
    run = {**RUN, "state": state, "evidence": "collecting"}
    findings = checked(explain_run(run, [], "unavailable"))
    assert list(findings) == ["unavailable_evidence"]
    assert findings["unavailable_evidence"]["code"] == "EVIDENCE_NOT_YET_READABLE"
    assert findings["unavailable_evidence"]["severity"] == "info"


def test_lost_ownership_keeps_both_outcomes_as_unconfirmed_hypotheses():
    run = {
        **RUN,
        "state": "unknown",
        "reason": "OWNERSHIP_UNKNOWN",
        "cleanup": "unknown",
    }
    findings = checked(explain_run(run, [observation(1)], "verified_prefix"))
    lost = findings["lost_connection"]
    assert len(lost["hypotheses"]) == 2
    assert {"Whether the workload is still executing."} <= set(lost["unknowns"])
    assert [a["action"] for a in lost["nextActions"]][:1] == ["reconcile_ownership"]
    assert findings["failed_cleanup"]["code"] == "CLEANUP_UNKNOWN"


def test_failed_cleanup_cites_cleanup_events():
    run = {**RUN, "cleanup": "failed"}
    records = [record(1, "cleanup.updated", {"status": "failed"})]
    cleanup = checked(explain_run(run, records, "valid"))["failed_cleanup"]
    assert cleanup["severity"] == "error" and cleanup["unknowns"] == []
    assert cleanup["facts"][0]["evidence"][1]["eventId"] == "run-x:1"


@pytest.mark.parametrize(
    "integrity,evidence,code",
    [
        ("unavailable", "complete", "EVIDENCE_UNAVAILABLE"),
        ("invalid", "invalid", "EVIDENCE_INVALID"),
        ("valid", "partial", "EVIDENCE_PARTIAL"),
    ],
)
def test_unavailable_evidence_is_independent_of_lifecycle(integrity, evidence, code):
    findings = checked(explain_run({**RUN, "evidence": evidence}, [], integrity))
    assert list(findings) == ["unavailable_evidence"]
    assert findings["unavailable_evidence"]["code"] == code
    actions = [a["action"] for a in findings["unavailable_evidence"]["nextActions"]]
    assert ("refresh_evidence" in actions) == (integrity == "unavailable")


def test_incompatible_clocks_and_missing_source_time_are_not_aligned():
    records = [
        observation(1, clock="alpha"),
        observation(2, clock="beta"),
        observation(3, clock=None),
        {**observation(4), "sourceTime": {"clockDomain": 5}},
    ]
    mapping = checked(explain_run(RUN, records, "valid"))["incompatible_time_mapping"]
    statements = " ".join(f["statement"] for f in mapping["facts"])
    assert "2 clock domains: alpha, beta" in statements
    assert "1 observation(s) carry no source time" in statements
    assert "1 observation(s) carry malformed source time" in statements
    assert (
        "not ordered, aligned or compared by latency"
        in mapping["consequences"][0]["statement"]
    )
    assert "The mapping between these clock domains." in mapping["unknowns"]


def test_declared_gaps_bound_their_references_and_report_omissions():
    records = [observation(1)] + [
        record(i, "observation.gap", {"reason": "collector paused"})
        for i in range(2, 22)
    ]
    gap = checked(explain_run(RUN, records, "valid"))["telemetry_gap"]
    assert "20 declared collection gap(s)" in gap["facts"][0]["statement"]
    assert len(gap["facts"][0]["evidence"]) == MAX_REFS
    assert gap["facts"][0]["evidenceOmitted"] == 20 - MAX_REFS


def test_observed_fault_and_diverging_measurements_are_stale_observations():
    records = [
        observation(1, value=0.0, measured=0.0),
        record(2, "fault.activation_requested", {"kind": "stuck-sensor"}),
        record(3, "fault.activation_observed", {"kind": "stuck-sensor"}),
        observation(4, value=0.5, measured=0.0),
        observation(5, value=0.6, measured=0.6),
    ]
    conflict = checked(explain_run(RUN, records, "valid"))["observation_conflict"]
    assert [f["statement"] for f in conflict["facts"]][-1].startswith(
        "1 later observation(s)"
    )
    assert conflict["facts"][-1]["evidence"][0]["eventId"] == "run-x:4"
    # The request is context only; the consequence rests on observation and divergence.
    requested = conflict["facts"][0]
    assert requested["statement"] == "A fault activation was requested."
    assert requested["id"] not in conflict["consequences"][0]["basis"]


def test_requested_fault_alone_is_not_evidence_of_a_fault():
    records = [observation(1), record(2, "fault.activation_requested", {})]
    assert "observation_conflict" not in checked(explain_run(RUN, records, "valid"))


def test_observed_fault_without_diverging_measurement_claims_no_stale_values():
    records = [
        observation(1, value=0.0, measured=0.0),
        record(2, "fault.activation_requested", {"kind": "stuck-sensor"}),
        record(3, "fault.activation_observed", {"kind": "stuck-sensor"}),
    ]
    fault = checked(explain_run(RUN, records, "valid"))["observation_conflict"]
    assert fault["consequences"] == []
    assert fault["unknowns"] == [
        "Whether any measurement was affected; no later observation diverges."
    ]


def test_accepted_command_failure_and_unknown_outcome_are_separate_from_lifecycle():
    records = [
        observation(1),
        record(2, "command.failed", {"operationId": "op-1", "code": "X"}),
    ]
    operations = [
        {"operationId": "op-1", "kind": "stop", "status": "failed"},
        {"operationId": "op-2", "kind": "cancel", "status": "unknown"},
        {"operationId": "op-3", "kind": "stop", "status": "completed"},
    ]
    command = checked(explain_run(RUN, records, "valid", operations=operations))[
        "command_failure"
    ]
    statements = [f["statement"] for f in command["facts"]]
    assert statements[0] == "The workload recorded command.failed."
    assert statements[1] == "Operation op-2 (cancel) is unknown."
    assert len(statements) == 2
    assert command["unknowns"] == ["Whether operation op-2 took effect."]


def test_absent_traffic_is_unobserved_information_never_failure():
    explanation = explain_run(
        RUN,
        [observation(1, observer="other-observer")],
        "valid",
        expected_observers=["state-observer"],
    )
    quiet = checked(explanation)["no_traffic"]
    assert quiet["severity"] == "info" and quiet["consequences"] == []
    assert len(quiet["hypotheses"]) == 2
    assert any("not a failure" in u for u in quiet["unknowns"])
    # Unreadable evidence cannot establish absence.
    assert "no_traffic" not in checked(
        explain_run(RUN, [], "unavailable", expected_observers=["state-observer"])
    )


def test_liveness_without_observation_is_not_functional_health():
    running = {**RUN, "state": "running", "evidence": "collecting"}
    # An unverified preparing process or unreadable evidence establishes no liveness fact.
    assert "liveness_only" not in checked(
        explain_run({**running, "state": "preparing"}, [], "verified_prefix")
    )
    assert "liveness_only" not in checked(explain_run(running, [], "unavailable"))
    live = checked(
        explain_run(running, [record(1, "run.state_changed")], "verified_prefix")
    )
    assert live["liveness_only"]["consequences"][0]["statement"] == (
        "Only liveness is established; functional health is not observed."
    )
    assert "liveness_only" not in checked(
        explain_run(running, [observation(1)], "verified_prefix")
    )


PREFLIGHT = {
    "preflightId": "pf-x",
    "snapshotId": "snap-x",
    "status": "blocked",
    "revision": 4,
    "capabilityDigest": "sha256:a",
    "expiresAt": 2000.0,
    "diagnostics": [],
}


def test_unavailable_provider_does_not_misattribute_unestablished_dimensions():
    readiness = {
        "backend": {"status": "available"},
        "model": {"status": "valid"},
        "provider": {
            "status": "unavailable",
            "message": "No admitted provider.",
            "diagnosticCodes": ["PROVIDER_UNAVAILABLE"],
            "elementRefs": ["xdl://org.example/system/s"],
        },
        **{
            name: {"status": "unknown", "diagnosticCodes": []}
            for name in ("artifacts", "capabilities", "clocks", "authority")
        },
        "target": {"status": "blocked", "diagnosticCodes": []},
    }
    findings = checked(
        explain_preflight(
            {**PREFLIGHT, "readiness": readiness},
            current_revision=4,
            capability_digest="sha256:a",
            now=1000.0,
        )
    )
    assert set(findings) == {"unsupported_capability", "readiness_unknown"}
    assert findings["unsupported_capability"]["code"] == "PROVIDER_UNAVAILABLE"
    grouped = findings["readiness_unknown"]
    # Target readiness is derived from the others and is not a separate finding.
    assert [f["evidence"][0]["dimension"] for f in grouped["facts"]] == [
        "artifacts",
        "capabilities",
        "clocks",
        "authority",
    ]


@pytest.mark.parametrize(
    "dimension,status,code,cls",
    [
        (
            "capabilities",
            "unsupported",
            "CAPABILITY_UNSUPPORTED",
            "unsupported_capability",
        ),
        ("artifacts", "unknown", "ARTIFACT_UNAVAILABLE", "missing_artifact"),
        ("clocks", "unknown", "CLOCK_MAPPING_UNAVAILABLE", "incompatible_time_mapping"),
        ("resources", "unavailable", "RESOURCE_BUSY", "resource_limit"),
        ("authority", "unknown", "AUTHORITY_UNAVAILABLE", "authority_unavailable"),
    ],
)
def test_coded_readiness_dimensions_map_to_their_class(dimension, status, code, cls):
    preflight = {
        **PREFLIGHT,
        "readiness": {dimension: {"status": status, "diagnosticCodes": [code]}},
    }
    findings = checked(
        explain_preflight(
            preflight, current_revision=4, capability_digest="sha256:a", now=1000.0
        )
    )
    assert list(findings) == [cls] and findings[cls]["code"] == code
    assert findings[cls]["severity"] == ("warning" if status == "unknown" else "error")


def test_invalid_model_is_established_and_downstream_facts_are_unestablished():
    preflight = {
        **PREFLIGHT,
        "readiness": {
            # Real readiness records the model status without a diagnostic code.
            "model": {"status": "invalid", "diagnosticCodes": []},
            "artifacts": {
                "status": "unknown",
                "diagnosticCodes": ["ARTIFACT_UNAVAILABLE"],
            },
            "resources": {"status": "unknown", "diagnosticCodes": ["LIMITS_UNKNOWN"]},
            "target": {"status": "blocked", "diagnosticCodes": []},
        },
        "diagnostics": [
            {
                "code": "XDL-SEMANTIC-TIME-MAPPING",
                "severity": "error",
                "pointer": "/spec/observers/0",
                "elementRef": "xdl://org.example/scenario/s",
                "location": {"documentId": "doc-1", "line": 12, "column": 3},
            },
            {"code": "ARTIFACT_UNAVAILABLE", "severity": "error"},
        ],
    }
    findings = checked(
        explain_preflight(
            preflight, current_revision=4, capability_digest="sha256:a", now=1000.0
        )
    )
    assert set(findings) == {"invalid_model", "readiness_unknown"}
    model = findings["invalid_model"]
    assert model["code"] == "MODEL_INVALID" and model["severity"] == "error"
    assert model["facts"][1]["evidence"] == [
        {
            "kind": "source_diagnostic",
            "code": "XDL-SEMANTIC-TIME-MAPPING",
            "documentId": "doc-1",
            "line": 12,
            "column": 3,
            "pointer": "/spec/observers/0",
            "elementRef": "xdl://org.example/scenario/s",
        }
    ]
    grouped = findings["readiness_unknown"]
    assert [f["evidence"][0]["dimension"] for f in grouped["facts"]] == [
        "artifacts",
        "resources",
    ]
    assert any("invalid model did not produce" in u for u in grouped["unknowns"])


def test_stale_plan_reports_each_changed_assumption():
    stale = checked(
        explain_preflight(
            {**PREFLIGHT, "status": "ready", "readiness": {}},
            current_revision=5,
            capability_digest="sha256:b",
            now=3000.0,
        )
    )["stale_plan"]
    assert [f["evidence"][0]["field"] for f in stale["facts"]] == [
        "expiresAt",
        "revision",
        "capabilityDigest",
    ]
    assert stale["nextActions"] == [
        {"action": "recheck_preflight", "label": ACTIONS["recheck_preflight"]}
    ]
    fresh = explain_preflight(
        {**PREFLIGHT, "status": "ready", "readiness": {}},
        current_revision=4,
        capability_digest="sha256:a",
        now=1000.0,
    )
    assert fresh["findings"] == []


def _owned_run(client, duration=0.5):
    p = client.post("/api/v1/projects", json={"name": "diagnostics"}).json()
    p = client.post(
        f"/api/v1/projects/{p['projectId']}/edits",
        headers={"If-Match": str(p["revision"])},
        json={
            "baseRevision": p["revision"],
            "edits": [
                {"kind": "set_parameter", "parameterId": "duration", "value": duration}
            ],
        },
    ).json()
    pf = client.post(
        f"/api/v1/projects/{p['projectId']}/preflights",
        json={"revision": p["revision"]},
    ).json()
    return p, pf


def test_api_owned_completed_run_and_stale_preflight(client):
    p, pf = _owned_run(client)
    started = client.post(
        "/api/v1/runs",
        headers={"Idempotency-Key": "diagnostics-start"},
        json={"snapshotId": pf["snapshotId"], "preflightId": pf["preflightId"]},
    ).json()
    deadline = time.monotonic() + 10
    while client.get("/api/v1/runs/" + started["runId"]).json()["state"] != "stopped":
        assert time.monotonic() < deadline
        time.sleep(0.05)
    explanation = client.get(f"/api/v1/runs/{started['runId']}/diagnostics").json()
    assert checked(explanation) == {}
    assert explanation["recordsExamined"] > 2
    assert explanation["integrity"] == "valid"
    assert explanation["evidenceScope"] == "owned_reference"
    route = (
        f"/api/v1/projects/{p['projectId']}/preflights/{pf['preflightId']}/diagnostics"
    )
    assert checked(client.get(route).json()) == {}
    client.post(
        f"/api/v1/projects/{p['projectId']}/edits",
        headers={"If-Match": str(p["revision"])},
        json={
            "baseRevision": p["revision"],
            "edits": [
                {"kind": "set_parameter", "parameterId": "duration", "value": 0.4}
            ],
        },
    )
    stale = checked(client.get(route).json())["stale_plan"]
    assert stale["facts"][0]["evidence"][0]["value"] == {
        "frozen": p["revision"],
        "current": p["revision"] + 1,
    }
    other = client.post("/api/v1/projects", json={"name": "other"}).json()
    wrong = client.get(
        f"/api/v1/projects/{other['projectId']}/preflights/{pf['preflightId']}/diagnostics"
    )
    assert wrong.status_code == 404


def test_api_invalid_model_cites_the_authoritative_source_diagnostic(client):
    from io import StringIO
    from ruamel.yaml import YAML

    p = client.post("/api/v1/projects", json={"name": "invalid model"}).json()
    parser = YAML()
    did, doc = next(
        (k, v)
        for k, v in p["documents"].items()
        if parser.load(v["content"])["kind"] == "Scenario"
    )
    resource = parser.load(doc["content"])
    resource["spec"]["observers"][0]["timeDomainId"] = "undeclared-time"
    out = StringIO()
    parser.dump(resource, out)
    p = client.put(
        f"/api/v1/projects/{p['projectId']}/documents/{did}",
        headers={"If-Match": str(p["revision"])},
        json={"content": out.getvalue(), "format": "yaml"},
    ).json()
    pf = client.post(
        f"/api/v1/projects/{p['projectId']}/preflights",
        json={"revision": p["revision"]},
    ).json()
    assert pf["readiness"]["model"]["status"] == "invalid", pf["readiness"]["model"]
    explanation = client.get(
        f"/api/v1/projects/{p['projectId']}/preflights/{pf['preflightId']}/diagnostics"
    ).json()
    model = checked(explanation)["invalid_model"]
    sources = model["facts"][1]["evidence"]
    assert {ref["code"] for ref in sources} <= {
        d["code"] for d in pf["diagnostics"] if d["severity"] == "error"
    }
    assert any(ref["documentId"] == did or ref["pointer"] for ref in sources)


def test_api_unavailable_provider_preflight_explanation(client):
    p = client.post("/api/v1/projects", json={"name": "unavailable"}).json()
    pf = client.post(
        f"/api/v1/projects/{p['projectId']}/preflights",
        json={"revision": p["revision"], "providerId": "provider.not-installed"},
    ).json()
    explanation = client.get(
        f"/api/v1/projects/{p['projectId']}/preflights/{pf['preflightId']}/diagnostics"
    ).json()
    findings = checked(explanation)
    assert findings["unsupported_capability"]["code"] == "PROVIDER_UNAVAILABLE"
    assert "missing_artifact" not in findings
    assert explanation["subject"]["status"] == "blocked"


def test_api_recorded_fixture_explains_clocks_gap_and_partial_evidence(client):
    project = client.post("/api/v1/projects", json={"name": "recorded"}).json()
    studio = client.app.state.studio
    fixture = _fixture.create_recorded_evidence(
        studio.store, studio.projects, studio.runs, project["projectId"]
    )
    journal = studio.runs.directory(fixture["runId"]) / "evidence.jsonl"
    before = journal.read_bytes()
    explanation = client.get(f"/api/v1/runs/{fixture['runId']}/diagnostics").json()
    findings = checked(explanation)
    assert {
        "incompatible_time_mapping",
        "telemetry_gap",
        "unavailable_evidence",
    } <= set(findings)
    assert findings["unavailable_evidence"]["code"] == "EVIDENCE_PARTIAL"
    assert "no_traffic" not in findings  # state-observer is present in the fixture
    assert explanation["evidenceScope"] == "recorded_fixture"
    gap_ids = [
        ref["eventId"] for ref in findings["telemetry_gap"]["facts"][0]["evidence"]
    ]
    assert fixture["events"]["gap"] in gap_ids
    assert journal.read_bytes() == before


def test_affected_elements_come_from_the_frozen_configuration():
    run = {**RUN, "state": "unknown", "reason": "OWNERSHIP_UNKNOWN"}
    refs = ["xdl://org.example/system/s#controller", "xdl://org.example/system/s#plant"]
    lost = checked(explain_run(run, [], "verified_prefix", element_refs=refs))[
        "lost_connection"
    ]
    assert lost["elementRefs"] == refs
