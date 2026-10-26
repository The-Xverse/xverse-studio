"""Contract fixtures establish no hardware access or admission claim."""

from copy import deepcopy
import importlib.util
from pathlib import Path

import pytest

from xverse_studio.lab import LabError, LabRegistry, handle_disconnect, validate_binding

_spec = importlib.util.spec_from_file_location(
    "physical_contract_fixture",
    Path(__file__).resolve().parents[1] / "fixtures/providers/physical/provider.py",
)
_fixture = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_fixture)


@pytest.fixture
def bench():
    now = [100.0]
    provider = _fixture.PhysicalContractFixture(lambda: now[0])
    persisted = []
    registry = LabRegistry(
        {provider.provider_id: provider},
        clock=lambda: now[0],
        persist=lambda records: persisted.append(deepcopy(records)),
    )
    return registry, provider, now, persisted


def test_unresolved_identity_is_inspectable_but_not_active_ready():
    result = validate_binding(
        "system#device",
        {"assetId": "unresolved", "physical": True, "interfaces": {}},
        {},
    )
    assert result["ready"] is False
    assert "ASSET_IDENTITY_UNRESOLVED" in result["diagnostics"]
    assert LabRegistry().inventory() == []


def test_identity_firmware_and_unknown_metadata_are_preserved_without_admission(bench):
    registry, provider, _, _ = bench
    asset = registry.inventory()[0]
    assert asset["identity"] == {"serial": "SYNTHETIC-001", "model": "Contract sensor"}
    assert asset["providerVersion"] == "1.0.0"
    assert asset["firmware"] == {"status": "observed", "version": "fixture-1.2.3"}
    assert asset["metadata"]["calibration"] == {"status": "unknown", "value": None}
    binding = validate_binding("system#sensor", asset, {"measurement": "scalar@1"})
    assert binding["logicalRef"] == "system#sensor"
    assert binding["assetId"] == provider.asset_id
    assert binding["identity"] == asset["identity"]
    assert binding["physical"] is True and binding["evidenceScope"] == "fixture"
    assert binding["ready"] is False
    assert binding["diagnostics"] == ["PHYSICAL_PROVIDER_NOT_ADMITTED"]
    asset["identity"]["serial"] = "changed"
    binding["identity"]["model"] = "changed"
    assert registry.inventory()[0]["identity"] == provider.assets[0]["identity"]
    assert provider.calls == ["inventory", "inventory"]


def test_unresolved_identity_and_firmware_remain_inspectable_but_not_ready(bench):
    registry, _, _, _ = bench
    asset = registry.inventory()[1]
    result = validate_binding("system#sensor", asset, {"measurement": "scalar@1"})
    assert asset["firmware"] == {"status": "unknown", "version": None}
    assert result["identity"] is None and result["ready"] is False
    assert set(result["diagnostics"]) == {
        "ASSET_IDENTITY_UNRESOLVED",
        "PHYSICAL_PROVIDER_NOT_ADMITTED",
        "ASSET_READINESS_UNPROVEN",
    }


def test_absent_asset_cannot_be_reserved_and_production_inventory_stays_empty(
    bench, client
):
    registry, provider, _, _ = bench
    with pytest.raises(LabError, match="^ASSET_UNAVAILABLE$"):
        registry.reserve("not-registered", owner="run-a")
    assert "reserve" not in provider.calls
    response = client.get("/api/v1/assets")
    assert response.status_code == 200
    assert response.json()["items"] == []
    assert response.json()["physicalProviderStatus"] == "unavailable"


def test_exclusive_lease_conflict_has_no_second_provider_delegation(bench):
    registry, provider, _, persisted = bench
    first = registry.reserve(provider.asset_id, owner="run-a", duration=10)
    with pytest.raises(LabError, match="^RESOURCE_BUSY$"):
        registry.reserve(provider.asset_id, owner="run-b", duration=10)
    assert provider.calls.count("reserve") == 1
    assert first["scope"] == "observe" and first["evidenceScope"] == "fixture"
    assert first["expiry"] == 110 and first["fencingIdentity"]
    assert persisted[0][0]["status"] == "unknown"
    assert persisted[-1][0]["status"] == "owned"


@pytest.mark.parametrize("action", ["stimulate", "destructive"])
def test_observe_only_cannot_gain_active_authority_even_with_a_new_grant(bench, action):
    registry, provider, _, _ = bench
    provider.assets[0]["capabilities"].append("destructive")
    lease = registry.reserve(provider.asset_id, owner="run-a")
    assert (
        registry.require_authority(
            lease["reservationId"], owner="run-a", action="observe"
        )["scope"]
        == "observe"
    )
    with pytest.raises(LabError, match="^FORBIDDEN$"):
        registry.require_authority(
            lease["reservationId"],
            owner="run-a",
            action=action,
            granted_scopes={action},
        )
    assert set(provider.calls) == {"inventory", "reserve"}


@pytest.mark.parametrize("scope", ["stimulate", "destructive"])
def test_active_reservation_requires_both_current_grant_and_capability(bench, scope):
    registry, provider, _, _ = bench
    provider.assets[0]["capabilities"].append("destructive")
    with pytest.raises(LabError, match="^FORBIDDEN$"):
        registry.reserve(provider.asset_id, owner="run-a", scope=scope)
    assert "reserve" not in provider.calls
    provider.assets[0]["capabilities"].remove(scope)
    with pytest.raises(LabError, match="^CAPABILITY_UNSUPPORTED$"):
        registry.reserve(
            provider.asset_id, owner="run-a", scope=scope, granted_scopes={scope}
        )
    assert "reserve" not in provider.calls


def test_stimulation_grant_is_rechecked_and_never_implies_destructive_control(bench):
    registry, provider, _, _ = bench
    lease = registry.reserve(
        provider.asset_id,
        owner="run-a",
        scope="stimulate",
        granted_scopes={"stimulate"},
    )
    assert (
        registry.require_authority(
            lease["reservationId"],
            owner="run-a",
            action="stimulate",
            granted_scopes={"stimulate"},
        )["status"]
        == "owned"
    )
    with pytest.raises(LabError, match="^FORBIDDEN$"):
        registry.require_authority(
            lease["reservationId"], owner="run-a", action="stimulate"
        )
    with pytest.raises(LabError, match="^CAPABILITY_UNSUPPORTED$"):
        registry.require_authority(
            lease["reservationId"],
            owner="run-a",
            action="destructive",
            granted_scopes={"destructive"},
        )
    provider.assets[0]["capabilities"].remove("stimulate")
    with pytest.raises(LabError, match="^CAPABILITY_UNSUPPORTED$"):
        registry.require_authority(
            lease["reservationId"],
            owner="run-a",
            action="stimulate",
            granted_scopes={"stimulate"},
        )


@pytest.mark.parametrize("duration", [0, -1, 301, True, float("inf"), float("nan")])
def test_lease_bounds_reject_before_provider_contact(bench, duration):
    registry, provider, _, _ = bench
    with pytest.raises(LabError, match="^LEASE_LIMIT$"):
        registry.reserve(provider.asset_id, owner="run-a", duration=duration)
    assert provider.calls == []


def test_renewal_preserves_fence_scope_and_expiry_blocks_authority(bench):
    registry, provider, now, _ = bench
    lease = registry.reserve(provider.asset_id, owner="run-a", duration=10)
    now[0] = 105
    renewed = registry.renew(
        lease["reservationId"],
        owner="run-a",
        expected_fencing_identity=lease["fencingIdentity"],
        duration=20,
    )
    assert renewed["expiry"] == 125 and renewed["lastRenewal"] == 105
    assert renewed["fencingIdentity"] == lease["fencingIdentity"]
    assert renewed["scope"] == "observe"
    now[0] = 125
    with pytest.raises(LabError, match="^OWNERSHIP_UNCERTAIN$"):
        registry.require_authority(
            lease["reservationId"], owner="run-a", action="observe"
        )
    assert registry.get(lease["reservationId"], owner="run-a")["status"] == "expired"
    assert provider.calls.count("reserve") == 1


def test_lost_reservation_ack_preserves_unknown_intent_and_blocks_retry(bench):
    registry, provider, _, persisted = bench
    provider.lose_reserve_ack = True
    with pytest.raises(LabError, match="^OWNERSHIP_UNCERTAIN$"):
        registry.reserve(provider.asset_id, owner="run-a", duration=10)
    rec = persisted[-1][0]
    assert (
        rec["status"] == "unknown"
        and rec["reason"] == "RESERVATION_ACKNOWLEDGEMENT_LOST"
    )
    assert provider.held[provider.asset_id]["owner"] == "run-a"
    with pytest.raises(LabError, match="^OWNERSHIP_UNCERTAIN$"):
        registry.require_authority(
            rec["reservationId"], owner="run-a", action="observe"
        )
    with pytest.raises(LabError, match="^RESOURCE_BUSY$"):
        registry.reserve(provider.asset_id, owner="run-b", duration=10)
    assert (
        registry.reconcile(rec["reservationId"], owner="run-a")["status"] == "unknown"
    )
    assert provider.calls.count("reserve") == 1


def test_lost_renewal_ack_disables_authority_without_reacquisition(bench):
    registry, provider, _, persisted = bench
    lease = registry.reserve(provider.asset_id, owner="run-a", duration=10)
    provider.lose_renew_ack = True
    with pytest.raises(LabError, match="^OWNERSHIP_UNCERTAIN$"):
        registry.renew(
            lease["reservationId"],
            owner="run-a",
            expected_fencing_identity=lease["fencingIdentity"],
            duration=20,
        )
    assert persisted[-1][0]["status"] == "unknown"
    assert persisted[-1][0]["reason"] == "RENEWAL_UNCERTAIN"
    with pytest.raises(LabError, match="^OWNERSHIP_UNCERTAIN$"):
        registry.require_authority(
            lease["reservationId"], owner="run-a", action="observe"
        )
    assert provider.calls.count("reserve") == 1


def test_disconnection_preserves_unknown_ownership_and_cleanup(bench):
    registry, provider, _, persisted = bench
    lease = registry.reserve(provider.asset_id, owner="run-a")
    provider.online = False
    with pytest.raises(LabError, match="^OWNERSHIP_UNCERTAIN$"):
        registry.release(lease["reservationId"], owner="run-a")
    assert persisted[-1][0]["reason"] == "RELEASE_UNCERTAIN"
    assert (
        registry.reconcile(lease["reservationId"], owner="run-a")["status"] == "unknown"
    )
    outcome = handle_disconnect(
        "request_stop", stop_permitted=True, stop_action=provider.stop
    )
    assert outcome["action"] == "stop_requested"
    assert outcome["physicalState"] == "unknown" and outcome["cleanup"] == "failed"
    assert outcome["reasons"] == ["STOP_REQUEST_FAILED"]
    assert provider.held[provider.asset_id]["owner"] == "run-a"


def test_unconfirmed_release_cannot_be_reported_as_released(bench):
    registry, provider, _, _ = bench
    lease = registry.reserve(provider.asset_id, owner="run-a")
    provider.release_observation = {"status": "unknown"}
    assert (
        registry.release(lease["reservationId"], owner="run-a")["status"] == "unknown"
    )
    with pytest.raises(LabError, match="^OWNERSHIP_UNCERTAIN$"):
        registry.require_authority(
            lease["reservationId"], owner="run-a", action="observe"
        )
    assert provider.held[provider.asset_id]["owner"] == "run-a"


@pytest.mark.parametrize(
    "policy,permitted,reason",
    [
        ("observe_only", True, "PHYSICAL_STATE_UNOBSERVED"),
        ("request_stop", False, "STOP_AUTHORITY_UNAVAILABLE"),
        ("rewind", True, "RECOVERY_POLICY_UNSUPPORTED"),
    ],
)
def test_disconnect_policy_never_calls_unpermitted_or_unsupported_stop(
    bench, policy, permitted, reason
):
    _, provider, _, _ = bench
    outcome = handle_disconnect(
        policy, stop_permitted=permitted, stop_action=provider.stop
    )
    assert outcome["physicalState"] == "unknown" and outcome["cleanup"] == "unknown"
    assert outcome["action"] == "none" and outcome["reasons"] == [reason]
    assert provider.calls == []


@pytest.mark.parametrize(
    "observation,state,cleanup",
    [
        ({"acknowledged": True}, "unknown", "unknown"),
        ({"acknowledged": False}, "unknown", "unknown"),
        ({"stoppedObserved": True}, "stopped_observed", "unknown"),
        ({"cleanupObserved": "complete"}, "unknown", "complete"),
        (
            {"stoppedObserved": True, "cleanupObserved": "failed"},
            "stopped_observed",
            "failed",
        ),
        (
            {"stoppedObserved": True, "cleanupObserved": "complete"},
            "stopped_observed",
            "complete",
        ),
    ],
)
def test_stop_ack_is_separate_from_observed_physical_state_and_cleanup(
    bench, observation, state, cleanup
):
    _, provider, _, _ = bench
    provider.stop_observation = observation
    outcome = handle_disconnect(
        "request_stop", stop_permitted=True, stop_action=provider.stop
    )
    assert outcome["physicalState"] == state and outcome["cleanup"] == cleanup
    assert outcome["observations"] == [observation]
    assert provider.calls == ["stop"]
    assert outcome["reasons"] == (["STOP_UNCONFIRMED"] if state == "unknown" else [])
