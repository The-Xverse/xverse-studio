"""T082 contract matrix over actual enrolled Autoverse and its recorded evidence.

Select explicitly with the private enrollment receipt. No reference workload and
no invented scheduled-fault capability. Native positive evidence is read from an
explicit completed Autoverse session; original journal/snapshot bytes stay intact.
"""

from copy import deepcopy
import json
import os
from pathlib import Path
import sqlite3

import pytest
from ruamel.yaml import YAML

import autoverse_provider_admission as enrollment
from autoverse_provider_admission import application, authenticated, project
from autoverse_composition import checked, document, sources, forbidden
from xverse_studio.blueprints.autoverse import NAMESPACE
from xverse_studio.evidence.reader import read_journal
from xverse_studio.experiments import scenario_timeline
from xverse_studio.timeline import project_timeline, TimelineQuery
from xverse_studio.xdl import XDLAdapter, XDLRejected
from xverse_studio.xdl.edits import semantic_edits
from xverse_studio.xdl.examples import dump_yaml

ROOT = Path(__file__).resolve().parents[2]
CASES = json.loads(
    (ROOT / "tests/fixtures/scenarios/autoverse-contract-cases.json").read_bytes()
)
SAFE = YAML(typ="safe")
target = enrollment.target
COLLECTIONS = {
    "step": "steps",
    "observer": "observers",
    "metric": "metrics",
    "fault": "faults",
}


@pytest.fixture
def authored(target, tmp_path, monkeypatch):
    provider, blueprint = target
    app = application(tmp_path / "Autoverse scenario contracts Ω", provider)
    monkeypatch.setattr(app.state.studio.runs, "_dispatch", forbidden)
    with authenticated(app) as api:
        p = project(api, blueprint)
        yield app, api, provider, p
        assert app.state.studio.store.all("run") == []
        assert app.state.studio.store.all("operation") == []


def edit_for(p, case):
    key, doc = document(p, "Scenario")
    item = SAFE.load(doc["content"])["spec"][COLLECTIONS[case["itemKind"]]][0]
    properties = deepcopy(case["properties"])
    if case.get("mergeReference"):
        properties["targetRef"] = {**item["targetRef"], **properties["targetRef"]}
    return {
        "kind": "update_scenario_item",
        "documentId": key,
        "itemKind": case["itemKind"],
        "itemId": item["id"],
        "properties": properties,
    }


def author(api, p, edits):
    return api.post(
        f"/api/v1/projects/{p['projectId']}/edits",
        headers={"If-Match": str(p["revision"])},
        json={"baseRevision": p["revision"], "edits": edits},
    )


def assert_blocked(app, api, provider, p):
    pf = checked(
        api.post(
            f"/api/v1/projects/{p['projectId']}/preflights",
            json={
                "revision": p["revision"],
                "providerId": provider.descriptor()["providerId"],
            },
        )
    )
    assert pf["status"] == "blocked"
    result = api.post(
        "/api/v1/runs",
        headers={"Idempotency-Key": "unsupported-scenario-review"},
        json={k: pf[k] for k in ["snapshotId", "preflightId"]},
    )
    assert result.status_code == 422 and result.json()["code"] == "ADMISSION_REJECTED"
    assert (
        app.state.studio.store.all("run")
        == app.state.studio.store.all("operation")
        == []
    )
    return pf


@pytest.mark.parametrize("case", CASES["invalidEdits"], ids=lambda c: c["id"])
def test_actual_autoverse_invalid_scenario_edit_is_atomic(authored, case):
    _, api, _, p = authored
    response = author(api, p, [edit_for(p, case)])
    assert response.status_code == 422, response.text
    assert checked(api.get(f"/api/v1/projects/{p['projectId']}")) == p


@pytest.mark.parametrize("case", CASES["unsupportedIntent"], ids=lambda c: c["id"])
def test_actual_autoverse_valid_unadmitted_intent_is_inspectable_and_blocked(
    authored, case
):
    app, api, provider, p = authored
    original = deepcopy(p)
    edit = edit_for(p, case)
    p = checked(author(api, p, [edit]))
    assert p["revision"] == original["revision"] + 1
    assert app.state.studio.adapter.validate(sources(p))["valid"]
    key, doc = document(p, "Scenario")
    assert all(
        v == original["documents"][k] for k, v in p["documents"].items() if k != key
    )
    item = SAFE.load(doc["content"])["spec"][COLLECTIONS[case["itemKind"]]][0]
    assert all(item[k] == v for k, v in edit["properties"].items())
    assert (
        provider.configuration(sources(p), app.state.studio.adapter.compile(sources(p)))
        is None
    )
    assert_blocked(app, api, provider, p)
    assert checked(api.get(f"/api/v1/projects/{p['projectId']}")) == p


@pytest.mark.parametrize("kind", ["duplicate-start", "opaque-fault"])
def test_actual_autoverse_conflicting_schedule_and_fault_intent_do_not_imply_effects(
    authored, kind
):
    app, api, provider, p = authored
    key, doc = document(p, "Scenario")
    scenario = SAFE.load(doc["content"])
    step = scenario["spec"]["steps"][0]
    if kind == "duplicate-start":
        edit = {
            "kind": "add_scenario_item",
            "documentId": key,
            "itemKind": "step",
            "itemId": "conflicting-start",
            "properties": {k: v for k, v in step.items() if k != "id"},
        }
    else:
        # Use the selected public experiment-lite grammar, never parse opaque text.
        target = deepcopy(step["targetRef"])
        fault_id = "unadmitted-fault"
        scenario_ref = {
            "apiVersion": scenario["apiVersion"],
            "kind": "Scenario",
            **{k: scenario["metadata"][k] for k in ["namespace", "name"]},
            "element": fault_id,
        }
        edit = {
            "kind": "add_scenario_item",
            "documentId": key,
            "itemKind": "fault",
            "itemId": fault_id,
            "properties": {
                "targetRef": target,
                "faultKind": "unadmitted-review-fault",
                "activation": "inert activation text",
                "recovery": "inert recovery text",
                "maturity": "prototype",
                "extensions": {
                    "io.xverse.experiment": {
                        "schemaVersion": "0.1",
                        "kind": "fault-intent",
                        "target": scenario_ref,
                        "trigger": {"kind": "time", "at": 1, "unit": "s"},
                        "duration": {"value": 1, "unit": "s"},
                        "timeDomainId": step["timeDomainId"],
                    }
                },
            },
        }
    p = checked(author(api, p, [edit]))
    assert app.state.studio.adapter.compile(sources(p))["valid"]
    scenario = SAFE.load(document(p, "Scenario")[1]["content"])
    markers = scenario_timeline(scenario)
    assert all(v["state"] == "requested" for v in markers)
    if kind == "opaque-fault":
        marker = next(v for v in markers if v["kind"] == "fault")
        assert (
            marker["observed"] is False
            and marker["activationIntent"] == "inert activation text"
            and marker["recoveryIntent"] == "inert recovery text"
        )
    assert_blocked(app, api, provider, p)


@pytest.mark.parametrize("item_kind,limit", CASES["typedAuthoringBounds"].items())
def test_actual_autoverse_authoring_count_limit_is_distinct_from_execution_admission(
    authored, item_kind, limit
):
    app, api, provider, p = authored
    key, doc = document(p, "Scenario")
    scenario = SAFE.load(doc["content"])
    collection = COLLECTIONS[item_kind]
    if item_kind == "fault":
        template = {
            "targetRef": scenario["spec"]["steps"][0]["targetRef"],
            "faultKind": "unadmitted-review",
            "activation": "intent",
            "recovery": "intent",
            "maturity": "prototype",
        }
    else:
        template = {
            k: v for k, v in scenario["spec"][collection][0].items() if k != "id"
        }
    # Retain the original observer ID required by metrics when filling the budget.
    items = scenario["spec"].setdefault(collection, [])
    while len(items) < limit:
        items.append({"id": f"review-{item_kind}-{len(items)}", **deepcopy(template)})
    p = checked(
        api.put(
            f"/api/v1/projects/{p['projectId']}/documents/{key}",
            headers={"If-Match": str(p["revision"])},
            json={"content": dump_yaml(scenario)},
        )
    )
    before = deepcopy(p)
    response = author(
        api,
        p,
        [
            {
                "kind": "add_scenario_item",
                "documentId": key,
                "itemKind": item_kind,
                "itemId": "beyond-limit",
                "properties": template,
            }
        ],
    )
    assert response.status_code == 422 and response.json()["code"] == "LIMIT_EXCEEDED"
    assert checked(api.get(f"/api/v1/projects/{p['projectId']}")) == before


@pytest.mark.parametrize("seconds", CASES["admittedDurationSeconds"])
def test_actual_autoverse_supported_duration_boundary_is_static_only(authored, seconds):
    app, api, provider, p = authored
    key, doc = document(p, "Scenario")
    scenario = SAFE.load(doc["content"])
    scenario["extensions"][NAMESPACE]["durationSeconds"] = seconds
    p = checked(
        api.put(
            f"/api/v1/projects/{p['projectId']}/documents/{key}",
            headers={"If-Match": str(p["revision"])},
            json={"content": dump_yaml(scenario)},
        )
    )
    compiled = app.state.studio.adapter.compile(sources(p))
    assert compiled["valid"]
    configuration = provider.configuration(sources(p), compiled)
    assert configuration is not None and configuration["durationSeconds"] == seconds
    assert app.state.studio.store.all("snapshot") == []


@pytest.mark.parametrize("seconds", CASES["refusedDurationSeconds"])
def test_actual_autoverse_outside_duration_or_boolean_stays_blocked(authored, seconds):
    app, api, provider, p = authored
    key, doc = document(p, "Scenario")
    scenario = SAFE.load(doc["content"])
    scenario["extensions"][NAMESPACE]["durationSeconds"] = seconds
    raw = dump_yaml(scenario)
    p = checked(
        api.put(
            f"/api/v1/projects/{p['projectId']}/documents/{key}",
            headers={"If-Match": str(p["revision"])},
            json={"content": raw},
        )
    )
    assert document(p, "Scenario")[1]["content"] == raw
    assert_blocked(app, api, provider, p)


@pytest.fixture
def actual_recording():
    report_dir = os.environ.get("STUDIO_AUTOVERSE_SCENARIO_RECORDED_REPORT")
    if not report_dir:
        pytest.fail(
            "Explicit completed actual Autoverse report required; no generated journal substitutes"
        )
    report_dir = Path(report_dir)
    native = json.loads((report_dir / "native-result.json").read_bytes())
    assert (
        native["outcome"] == "passed"
        and native["originalWorkerExited"]
        and native["originalRootLockReleased"]
    )
    data = Path(
        json.loads((report_dir / "browser-command.private.json").read_bytes())[
            "dataRoot"
        ]
    )
    directory = data / "runs" / native["runId"]
    journal = directory / "evidence.jsonl"
    snapshot_path = data / "snapshots" / native["snapshotId"] / "snapshot.json"
    before = (journal.read_bytes(), snapshot_path.read_bytes())
    with sqlite3.connect(
        (data / "studio.sqlite").as_uri() + "?mode=ro", uri=True
    ) as db:

        def get(kind, key):
            return json.loads(
                db.execute(
                    "SELECT body FROM records WHERE kind=? AND id=?", (kind, key)
                ).fetchone()[0]
            )

        run = get("run", native["runId"])
        snapshot = get("snapshot", native["snapshotId"])
    assert (
        run["providerId"] == snapshot["providerId"] == "autoverse.demo"
        and run["state"] == "stopped"
        and run["cleanup"] == "complete"
    )
    records, integrity = read_journal(directory, run)
    assert integrity == "valid" and records
    yield run, snapshot, records
    assert (journal.read_bytes(), snapshot_path.read_bytes()) == before


def test_actual_autoverse_recorded_timeline_keeps_intent_observations_and_unmapped_clocks_separate(
    actual_recording,
):
    run, snapshot, records = actual_recording
    report = project_timeline(
        run, snapshot, records, "valid", [], XDLAdapter(), TimelineQuery(limit=200)
    )
    rows = report["items"]
    intent = [v for v in rows if v["layer"] == "intent"]
    observed = [v for v in rows if v["layer"] == "recorded"]
    assert report["readOnly"] and report["snapshotDigest"] == snapshot["snapshotDigest"]
    assert {v["intentId"] for v in intent} == {
        "start-autoverse",
        "autoverse-telemetry",
        "reported-speed",
    }
    assert all(v["evidenceScope"] == "declared_intent_only" for v in intent)
    assert {v["eventId"] for v in observed} == {v["eventId"] for v in records}
    assert any(v["kind"] == "observation.available" for v in observed)
    assert all(v["position"]["status"] == "unplaced" for v in rows)
    assert not any(
        "fault.activation_observed" == v["kind"]
        or "fault.recovery_observed" == v["kind"]
        for v in rows
    )
    assert all(
        v.get("evaluationStatus") == "not_evaluated_by_intent"
        for v in intent
        if v["kind"] == "intent.metric"
    )
    assert run["verdict"] is None


@pytest.mark.parametrize(
    "payload_kind", ["nan", "infinity", "negative-infinity", "depth", "nodes", "bytes"]
)
def test_actual_autoverse_edit_envelope_limits_precede_copy_or_effects(
    authored, payload_kind
):
    _, api, _, p = authored
    original = sources(p)
    key, _ = document(p, "Scenario")
    if payload_kind in {"nan", "infinity", "negative-infinity"}:
        at = {
            "nan": float("nan"),
            "infinity": float("inf"),
            "negative-infinity": float("-inf"),
        }[payload_kind]
        edit = edit_for(
            p, {"itemKind": "step", "properties": {"schedule": {"at": at, "unit": "s"}}}
        )
        code = "INVALID_EDIT"
    else:
        if payload_kind == "depth":
            value = {"leaf": "inert"}
            for _ in range(600):
                value = {"nested": value}
        elif payload_kind == "nodes":
            value = [None] * 10001
        else:
            value = "x" * (64 * 1024)
        edit = {
            "kind": "set_scenario_conditions",
            "documentId": key,
            "properties": {"initialConditions": {"boundedReview": value}},
        }
        code = "LIMIT_EXCEEDED"
    with pytest.raises(XDLRejected) as rejected:
        semantic_edits(original, [edit])
    assert rejected.value.code == code and sources(p) == original
    assert checked(api.get(f"/api/v1/projects/{p['projectId']}")) == p


def test_actual_autoverse_multi_edit_failure_keeps_original_complete_source_set(
    authored,
):
    _, api, _, p = authored
    key, _ = document(p, "Scenario")
    valid = {
        "kind": "set_scenario_conditions",
        "documentId": key,
        "properties": {
            "acceptanceIntent": "First edit must roll back when later reference fails"
        },
    }
    invalid = edit_for(
        p, {"itemKind": "step", "properties": {"timeDomainId": "absent"}}
    )
    refused = author(api, p, [valid, invalid])
    assert refused.status_code == 422
    assert checked(api.get(f"/api/v1/projects/{p['projectId']}")) == p
