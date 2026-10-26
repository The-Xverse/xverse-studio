"""T076 fixture contracts; no hardware, provider admission or clock measurement."""

from copy import deepcopy
import importlib.util
from pathlib import Path

import pytest
from ruamel.yaml import YAML

from xverse_studio.lab import (
    assess_time_quality,
    handle_disconnect,
    validate_binding,
    LabError,
)
from xverse_studio.lab import LabRegistry
from xverse_studio.deployments import Deployments
from xverse_studio.projects.service import Projects
from xverse_studio.storage.core import Store
from xverse_studio.xdl import XDLAdapter
from xverse_studio.xdl.examples import dump_yaml

_fixture_spec = importlib.util.spec_from_file_location(
    "hybrid_physical_fixture",
    Path(__file__).resolve().parents[1] / "fixtures/providers/physical/provider.py",
)
_fixtures = importlib.util.module_from_spec(_fixture_spec)
_fixture_spec.loader.exec_module(_fixtures)


@pytest.fixture
def physical_fixture():
    provider = _fixtures.PhysicalContractFixture(lambda: 100)
    registry = LabRegistry({provider.provider_id: provider}, clock=lambda: 100)
    return provider, registry


def test_clock_uncertainty_never_fakes_simulation_time_or_latency():
    q = assess_time_quality(
        {"clockDomainRef": "device", "sourceTick": "12"},
        target_clock="simulation",
        max_uncertainty_ticks=2,
    )
    assert q["correlation"] == "unknown" and q["sourceTick"] == "12"
    q = assess_time_quality(
        {
            "clockDomainRef": "device",
            "sourceTick": "12",
            "mapping": {
                "admitted": True,
                "mappingId": "map",
                "digest": "sha256:map",
                "targetClockDomainRef": "simulation",
                "uncertaintyTicks": 3,
            },
        },
        target_clock="simulation",
        max_uncertainty_ticks=2,
    )
    assert q["correlation"] == "uncertain" and q["preciseLatencyAvailable"] is False


def test_missing_source_time_remains_missing():
    q = assess_time_quality(
        {"recordedAt": "2026-10-25T00:00:00Z"}, target_clock="simulation"
    )
    assert q["sourceTick"] is None and q["correlation"] == "unknown"


def test_refused_or_failed_stop_leaves_physical_state_unknown():
    out = handle_disconnect(
        "request_stop", stop_permitted=True, stop_action=lambda: {"acknowledged": False}
    )
    assert out["physicalState"] == "unknown" and out["cleanup"] == "unknown"
    out = handle_disconnect(
        "request_stop",
        stop_permitted=True,
        stop_action=lambda: (_ for _ in ()).throw(OSError()),
    )
    assert out["cleanup"] == "failed"


def test_unadvertised_stop_is_never_attempted():
    calls = []
    out = handle_disconnect(
        "request_stop", stop_permitted=False, stop_action=lambda: calls.append(True)
    )
    assert calls == [] and out["physicalState"] == "unknown"


def test_compatible_substitution_preserves_logical_identity():
    out = validate_binding(
        "system#sensor",
        {
            "assetId": "asset",
            "identity": {"serial": "known"},
            "interfaces": {"output": "scalar@1"},
            "physical": True,
            "evidenceScope": "unavailable",
        },
        {"output": "scalar@1"},
    )
    assert out["logicalRef"] == "system#sensor" and out["ready"] is False
    with pytest.raises(LabError, match="INTERFACE_INCOMPATIBLE"):
        validate_binding(
            "system#sensor",
            {"assetId": "asset", "interfaces": {"output": "other@1"}},
            {"output": "scalar@1"},
        )


def test_authored_physical_substitution_retains_topology_but_not_runtime_support(
    tmp_path,
):
    adapter = XDLAdapter()
    projects = Projects(Store(tmp_path), adapter)
    project = projects.create("Hybrid substitution fixture")
    deployments = Deployments(projects, adapter)
    variant = deployments.list(project["projectId"])["items"][0]
    before = projects.sources(project)
    graph = adapter.project(before)
    document_id = variant["documentId"]
    deployment = YAML(typ="safe").load(project["documents"][document_id]["content"])
    binding = next(
        b for b in deployment["spec"]["bindings"] if b["id"] == "plant-binding"
    )
    target = next(
        t for t in deployment["spec"]["targets"] if t["id"] == binding["targetId"]
    )
    target["externalAssetRef"] = "urn:fixture:unresolved:hybrid-bench"
    saved = projects.save(
        project["projectId"],
        document_id,
        project["revision"],
        dump_yaml(deployment),
        "yaml",
    )
    changed = deployments.update_binding(
        project["projectId"],
        saved["revision"],
        document_id,
        {"bindingId": "plant-binding", "realizationClass": "physical"},
    )
    after = projects.sources(changed["project"])
    system_path = next(path for path in before if path.endswith("system.xdl.yaml"))
    assert after[system_path] == before[system_path]
    after_graph = adapter.project(after)
    for collection in ("elements", "connections"):
        assert [item["ref"] for item in after_graph[collection]] == [
            item["ref"] for item in graph[collection]
        ]
    assert changed["compatibility"]["status"] == "blocked"
    assert "XDL1-PLAN-REALIZATION-UNSUPPORTED" in {
        d["code"] for d in changed["compatibility"]["diagnostics"]
    }
    # The selected compiler refuses this realization before provider resolution.
    assert changed["resolution"] is None
    assert any(
        "behavioural equivalence" in text
        for text in changed["variant"]["limitations"]
    )


def test_compatible_fixture_binding_changes_identity_and_controls_without_equivalence(
    physical_fixture,
):
    provider, _ = physical_fixture
    physical = provider.inventory()[0]
    virtual = {
        **deepcopy(physical),
        "assetId": "fixture:virtual-sensor",
        "physical": False,
        "identity": {"model": "Synthetic virtual sensor"},
        "capabilities": ["observe", "pause", "rewind"],
    }
    required = {"measurement": "scalar@1"}
    before = validate_binding("system#sensor", virtual, required)
    after = validate_binding("system#sensor", physical, required)
    assert before["logicalRef"] == after["logicalRef"] == "system#sensor"
    assert (
        before["assetId"] != after["assetId"]
        and before["identity"] != after["identity"]
    )
    assert before["physical"] is False and after["physical"] is True
    assert set(before["capabilities"]) == {"observe", "pause", "rewind"}
    assert set(after["capabilities"]) == {"observe", "stimulate"}
    assert before["ready"] is False and after["ready"] is False
    assert before["diagnostics"] == ["FIXTURE_SCOPE_ONLY"]
    assert after["diagnostics"] == ["PHYSICAL_PROVIDER_NOT_ADMITTED"]
    assert "equivalent" not in after and "fidelity" not in after


@pytest.mark.parametrize(
    "interfaces", [{}, {"measurement": "other@1"}, {"other": "scalar@1"}]
)
def test_incompatible_physical_binding_rejects_without_mutating_source(
    physical_fixture, interfaces
):
    provider, _ = physical_fixture
    asset = provider.inventory()[0]
    asset["interfaces"] = interfaces
    before = deepcopy(asset)
    with pytest.raises(LabError, match="^INTERFACE_INCOMPATIBLE$"):
        validate_binding("system#sensor", asset, {"measurement": "scalar@1"})
    assert asset == before
    assert provider.calls == ["inventory"]


@pytest.mark.parametrize(
    "observation",
    [
        {"recordedAt": "2026-10-26T00:00:00Z"},
        {
            "clockDomainRef": "bench",
            "sourceTick": None,
            "recordedAt": "2026-10-26T00:00:00Z",
        },
        {"sourceTick": "12345678901234567890", "recordedAt": "2026-10-26T00:00:00Z"},
    ],
)
def test_missing_clock_evidence_never_uses_receipt_time_for_source_time(observation):
    before = deepcopy(observation)
    result = assess_time_quality(observation, target_clock="simulation")
    assert result["sourceTick"] == observation.get("sourceTick")
    assert result["recordedAt"] == observation["recordedAt"]
    assert (
        result["correlation"] == "unknown"
        and result["preciseLatencyAvailable"] is False
    )
    assert result["reasons"] == ["SOURCE_TIME_UNAVAILABLE"]
    assert observation == before


@pytest.mark.parametrize(
    "change",
    [
        {"admitted": False},
        {"mappingId": None},
        {"digest": None},
        {"targetClockDomainRef": "another-clock"},
    ],
)
def test_incomplete_cross_clock_proof_remains_unknown(change):
    mapping = {
        "admitted": True,
        "mappingId": "fixture-map",
        "digest": "sha256:fixture-only",
        "targetClockDomainRef": "simulation",
        "uncertaintyTicks": 0,
        **change,
    }
    result = assess_time_quality(
        {"clockDomainRef": "bench", "sourceTick": "12", "mapping": mapping},
        target_clock="simulation",
    )
    assert (
        result["correlation"] == "unknown"
        and result["preciseLatencyAvailable"] is False
    )
    assert result["reasons"] == ["CLOCK_MAPPING_UNAVAILABLE"]
    assert result["mapping"] == mapping


@pytest.mark.parametrize("uncertainty", [None, True, -1, float("inf"), float("nan")])
def test_unknown_clock_uncertainty_cannot_become_precise_latency(uncertainty):
    result = assess_time_quality(
        {
            "clockDomainRef": "bench",
            "sourceTick": "12",
            "mapping": {
                "admitted": True,
                "mappingId": "fixture-map",
                "digest": "sha256:fixture-only",
                "targetClockDomainRef": "simulation",
                "uncertaintyTicks": uncertainty,
            },
        },
        target_clock="simulation",
    )
    assert (
        result["correlation"] == "unknown"
        and result["preciseLatencyAvailable"] is False
    )
    assert result["reasons"] == ["CLOCK_UNCERTAINTY_UNKNOWN"]


def test_bounded_mapping_retains_original_clock_tick_and_uncertainty():
    observation = {
        "clockDomainRef": "bench",
        "sourceTick": "12345678901234567890",
        "recordedAt": "2026-10-26T00:00:00Z",
        "mapping": {
            "admitted": True,
            "mappingId": "fixture-map",
            "digest": "sha256:fixture-only",
            "targetClockDomainRef": "simulation",
            "uncertaintyTicks": 2,
        },
    }
    result = assess_time_quality(
        observation, target_clock="simulation", max_uncertainty_ticks=2
    )
    assert (
        result["correlation"] == "mapped" and result["preciseLatencyAvailable"] is False
    )
    assert (
        result["clockDomainRef"] == "bench"
        and result["sourceTick"] == observation["sourceTick"]
    )
    assert result["mapping"] == observation["mapping"]
    result["mapping"]["uncertaintyTicks"] = 0
    assert observation["mapping"]["uncertaintyTicks"] == 2


def test_fixture_unplug_disables_access_and_keeps_ownership_and_stop_unconfirmed(
    physical_fixture,
):
    provider, registry = physical_fixture
    lease = registry.reserve(provider.asset_id, owner="fixture-run")
    provider.online = False
    with pytest.raises(LabError, match="^ASSET_UNAVAILABLE$"):
        registry.require_authority(
            lease["reservationId"], owner="fixture-run", action="observe"
        )
    assert (
        registry.reconcile(lease["reservationId"], owner="fixture-run")["status"]
        == "unknown"
    )
    result = handle_disconnect(
        "request_stop", stop_permitted=True, stop_action=provider.stop
    )
    assert result["connection"] == "lost" and result["physicalState"] == "unknown"
    assert result["cleanup"] == "failed" and result["reasons"] == [
        "STOP_REQUEST_FAILED"
    ]
    assert provider.held[provider.asset_id]["owner"] == "fixture-run"
    assert provider.calls.count("reserve") == 1 and provider.calls.count("stop") == 1


def test_refused_stop_is_retained_without_retry_or_inferred_safe_state(
    physical_fixture,
):
    provider, _ = physical_fixture
    provider.stop_observation = {
        "acknowledged": False,
        "reason": "FIXTURE_STOP_REFUSED",
    }
    result = handle_disconnect(
        "request_stop", stop_permitted=True, stop_action=provider.stop
    )
    assert result["physicalState"] == "unknown" and result["cleanup"] == "unknown"
    assert result["observations"] == [provider.stop_observation]
    assert result["reasons"] == ["STOP_UNCONFIRMED"] and provider.calls == ["stop"]


def test_provider_reported_restore_failure_does_not_erase_observed_stop(
    physical_fixture,
):
    provider, _ = physical_fixture
    # Synthetic stop/cleanup evidence: no restore operation or capability is invented.
    provider.stop_observation = {
        "stoppedObserved": True,
        "cleanupObserved": "failed",
        "restoreObserved": "failed",
        "reason": "FIXTURE_RESTORE_FAILED",
    }
    result = handle_disconnect(
        "request_stop", stop_permitted=True, stop_action=provider.stop
    )
    assert (
        result["physicalState"] == "stopped_observed" and result["cleanup"] == "failed"
    )
    assert result["observations"] == [provider.stop_observation] and provider.calls == [
        "stop"
    ]


@pytest.mark.parametrize("policy", ["restore", "rewind", "pause", "reset"])
def test_unadvertised_physical_recovery_never_calls_the_provider(
    physical_fixture, policy
):
    provider, _ = physical_fixture
    result = handle_disconnect(policy, stop_permitted=True, stop_action=provider.stop)
    assert result["action"] == "none" and result["physicalState"] == "unknown"
    assert result["cleanup"] == "unknown" and result["reasons"] == [
        "RECOVERY_POLICY_UNSUPPORTED"
    ]
    assert provider.calls == []
