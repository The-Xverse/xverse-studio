import pytest

from xverse_studio.lab import assess_time_quality, handle_disconnect, validate_binding, LabError


def test_clock_uncertainty_never_fakes_simulation_time_or_latency():
    q = assess_time_quality({"clockDomainRef": "device", "sourceTick": "12"}, target_clock="simulation", max_uncertainty_ticks=2)
    assert q["correlation"] == "unknown" and q["sourceTick"] == "12"
    q = assess_time_quality({"clockDomainRef": "device", "sourceTick": "12", "mapping": {"admitted": True, "mappingId": "map", "digest": "sha256:map", "targetClockDomainRef": "simulation", "uncertaintyTicks": 3}}, target_clock="simulation", max_uncertainty_ticks=2)
    assert q["correlation"] == "uncertain" and q["preciseLatencyAvailable"] is False


def test_missing_source_time_remains_missing():
    q = assess_time_quality({"recordedAt": "2026-10-25T00:00:00Z"}, target_clock="simulation")
    assert q["sourceTick"] is None and q["correlation"] == "unknown"


def test_refused_or_failed_stop_leaves_physical_state_unknown():
    out = handle_disconnect("request_stop", stop_permitted=True, stop_action=lambda: {"acknowledged": False})
    assert out["physicalState"] == "unknown" and out["cleanup"] == "unknown"
    out = handle_disconnect("request_stop", stop_permitted=True, stop_action=lambda: (_ for _ in ()).throw(OSError()))
    assert out["cleanup"] == "failed"


def test_unadvertised_stop_is_never_attempted():
    calls = []
    out = handle_disconnect("request_stop", stop_permitted=False, stop_action=lambda: calls.append(True))
    assert calls == [] and out["physicalState"] == "unknown"


def test_compatible_substitution_preserves_logical_identity():
    out = validate_binding("system#sensor", {"assetId": "asset", "identity": {"serial": "known"}, "interfaces": {"output": "scalar@1"}, "physical": True, "evidenceScope": "unavailable"}, {"output": "scalar@1"})
    assert out["logicalRef"] == "system#sensor" and out["ready"] is False
    with pytest.raises(LabError, match="INTERFACE_INCOMPATIBLE"):
        validate_binding("system#sensor", {"assetId": "asset", "interfaces": {"output": "other@1"}}, {"output": "scalar@1"})
