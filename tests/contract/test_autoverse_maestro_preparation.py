"""Actual public compiler/preparation boundary; no live Autoverse claim."""
from copy import deepcopy
import json
import subprocess

import pytest
from ruamel.yaml import YAML
from xverse.maestro.execution import ExecutionInputError

from xverse_studio.blueprints.autoverse import documents, NAMESPACE, ROLES
from xverse_studio.providers.autoverse.preparation import prepare_snapshot
from xverse_studio.xdl import XDLAdapter
from xverse_studio.xdl.examples import dump_yaml


def snapshot(source=None):
    source = documents() if source is None else source
    compiled = XDLAdapter().compile(source)
    assert compiled["valid"], compiled["diagnostics"]
    return {"documents": source, "plan": compiled["plan"],
            "planDigest": compiled["planDigest"], "semanticDigest": compiled["semanticDigest"]}


def prepare(value):
    # A static enrollment identity only. No executable or endpoint is registered
    # in this test; successful preparation cannot authorize a launch.
    return prepare_snapshot("run-preparation", value, installation={"identityDigest": "sha256:" + "1" * 64},
                            host_id="owned-static-host")


def test_actual_effective_sources_and_six_bindings_survive_pure_preparation(monkeypatch):
    source = {"xdl/" + name: "# Original authored bytes\r\n" + raw.replace("\n", "\r\n")
              for name, raw in documents().items()}
    value = snapshot(source)
    before = deepcopy(value)
    def no_effects(*_args, **_kwargs):
        pytest.fail("Pure public preparation attempted a process")
    monkeypatch.setattr(subprocess, "Popen", no_effects)
    result = prepare(value)
    assert value == before
    assert result.prepared.submission.documents == tuple((name, raw.encode()) for name, raw in source.items())
    effective = result.prepared.providers[0].configuration
    assert effective.documents == result.prepared.submission.documents
    assert json.loads(effective.private_config)["inputSurface"] == "native-pygame"
    receipt = result.prepared.summary()
    assert receipt["executionAllowed"] is False and receipt["runtimeAdmission"] == "not_checked"
    actual = result.prepared.inspection.to_data()
    assert actual["planDigest"] == value["planDigest"]
    assert actual["inputSemanticDigest"] == value["semanticDigest"]
    assert {u["logicalRef"]["element"] for u in actual["units"]} == set(ROLES)
    assert {p.logical_id for p in result.lifecycle.phases} == {u["logicalId"] for u in actual["units"]}


def test_actual_platform_checks_complete_per_binding_graph_and_startup_order():
    result = prepare(snapshot())
    positions = {p.phase_id: i for i, p in enumerate(result.lifecycle.phases)}
    units = result.prepared.inspection.to_data()["units"]
    for unit in units:
        phases = [p for p in result.lifecycle.phases if p.logical_id == unit["logicalId"]]
        assert {p.operation for p in phases} == {"prepare", "start", "ready"}
        for phase in phases:
            assert all(positions[need] < positions[phase.phase_id] for need in phase.needs)
    assert positions["carla-server-prepare"] < positions["vcu-start"]
    assert positions["score-ready"] < positions["carla-vehicle-start"]
    assert positions["driver-observer-prepare"] < positions["carla-ready"]
    assert positions["carla-ready"] < positions["android-vm-start"]
    assert positions["android-boot-start"] < positions["android-apk-start"] < positions["driver-start"]
    assert result.lifecycle.preparation_digest == result.prepared.digest


@pytest.mark.parametrize("field", ["planDigest", "semanticDigest"])
def test_stale_immutable_identities_reject_at_actual_public_boundary(field):
    value = snapshot()
    value[field] = "sha256:" + "f" * 64
    with pytest.raises(ExecutionInputError) as caught:
        prepare(value)
    assert caught.value.code == "MPX-EFFECTIVE-INPUT-MISMATCH"


def test_selected_resource_cannot_be_changed_by_snapshot_metadata():
    value = snapshot()
    value["plan"]["selection"]["system"]["uri"] += "-other"
    with pytest.raises(ExecutionInputError) as caught:
        prepare(value)
    assert caught.value.code == "MPX-SELECTION-MISMATCH"


def test_compilable_unknown_behavior_is_not_admitted_by_echoing_documents():
    source = documents()
    scenario = YAML(typ="safe").load(source["scenario.xdl.yaml"])
    scenario["spec"]["initialConditions"]["unknownBehavior"] = True
    source["scenario.xdl.yaml"] = dump_yaml(scenario)
    value = snapshot(source)  # Valid XDL is still unsupported by this provider.
    with pytest.raises(ExecutionInputError) as caught:
        prepare(value)
    assert caught.value.code == "AUTOVERSE-SOURCE-UNSUPPORTED"


def test_supported_duration_edit_reaches_frozen_configuration_and_original_sources():
    source = documents()
    scenario = YAML(typ="safe").load(source["scenario.xdl.yaml"])
    scenario["extensions"][NAMESPACE]["durationSeconds"] = 30
    source["scenario.xdl.yaml"] = dump_yaml(scenario)
    value = snapshot(source)
    result = prepare(value)
    effective = result.prepared.providers[0].configuration
    assert json.loads(effective.private_config)["durationSeconds"] == 30
    assert dict(effective.documents)["scenario.xdl.yaml"] == source["scenario.xdl.yaml"].encode()
    assert result.prepared.submission.expected_plan_digest == value["planDigest"]
