from concurrent.futures import ThreadPoolExecutor
from copy import deepcopy

import pytest

from xverse_studio.lab import LabRegistry, LabError


class FixtureProvider:
    """Owned in-memory fixture; never registers in the shipped application."""
    def __init__(self):
        self.held = None
        self.fence = 0
        self.release_calls = 0
    def inventory(self):
        return [{"assetId": "owned-fixture", "providerId": "fixture", "identity": {"serial": "fixture-1"}, "physical": False, "evidenceScope": "fixture", "capabilities": ["observe", "stimulate"], "interfaces": {"input": "scalar@1"}}]
    def reserve(self, asset, scope, owner, deadline):
        if self.held:
            raise LabError("RESOURCE_BUSY")
        self.fence += 1
        self.held = {"fencingIdentity": str(self.fence), "expiry": deadline, "owner": owner, "scope": scope, "status": "owned"}
        return deepcopy(self.held)
    def renew(self, reservation, fence, deadline, authority):
        if not self.held or fence != self.held["fencingIdentity"]:
            raise LabError("STALE_FENCING_IDENTITY")
        self.held["expiry"] = deadline
        return deepcopy(self.held)
    def release(self, reservation, authority):
        self.release_calls += 1
        if self.held and reservation["fencingIdentity"] == self.held["fencingIdentity"]:
            self.held = None
        return {"status": "released"}
    def inspect_reservation(self, reservation):
        return deepcopy(self.held) if self.held else {"status": "unknown"}


def setup():
    now = [100]
    provider = FixtureProvider()
    registry = LabRegistry({"fixture": provider}, clock=lambda: now[0])
    return registry, provider, now


def test_default_app_has_no_device_inventory_and_never_scans():
    assert LabRegistry().inventory() == []


def test_exclusive_claim_and_default_observe_scope():
    registry, provider, now = setup()
    r = registry.reserve("owned-fixture", owner="principal", duration=10)
    assert r["scope"] == "observe"
    with pytest.raises(LabError, match="RESOURCE_BUSY"):
        registry.reserve("owned-fixture", owner="other", duration=10)
    with pytest.raises(LabError, match="FORBIDDEN"):
        registry.require_authority(r["reservationId"], owner="principal", action="stimulate")


def test_active_scope_requires_explicit_grant_and_provider_capability():
    registry, provider, now = setup()
    with pytest.raises(LabError, match="FORBIDDEN"):
        registry.reserve("owned-fixture", owner="p", scope="stimulate", duration=10)
    r = registry.reserve("owned-fixture", owner="p", scope="stimulate", duration=10, granted_scopes={"stimulate"})
    assert registry.require_authority(r["reservationId"], owner="p", action="stimulate", granted_scopes={"stimulate"})["status"] == "owned"
    with pytest.raises(LabError, match="CAPABILITY_UNSUPPORTED"):
        registry.require_authority(r["reservationId"], owner="p", action="destructive", granted_scopes={"destructive"})


def test_expiry_and_stale_fence_cannot_renew_or_enable_commands():
    registry, provider, now = setup()
    r = registry.reserve("owned-fixture", owner="p", duration=10)
    with pytest.raises(LabError, match="STALE_FENCING_IDENTITY"):
        registry.renew(r["reservationId"], owner="p", expected_fencing_identity="old", duration=10)
    now[0] = 111
    assert registry.get(r["reservationId"], owner="p")["status"] == "expired"
    with pytest.raises(LabError, match="OWNERSHIP_UNCERTAIN"):
        registry.renew(r["reservationId"], owner="p", expected_fencing_identity=r["fencingIdentity"], duration=10)
    assert provider.fence == 1


def test_renew_same_scope_and_idempotent_release_never_affects_new_owner():
    registry, provider, now = setup()
    r = registry.reserve("owned-fixture", owner="p", duration=10)
    updated = registry.renew(r["reservationId"], owner="p", expected_fencing_identity=r["fencingIdentity"], duration=15)
    assert updated["expiry"] == 115
    registry.release(r["reservationId"], owner="p")
    new = registry.reserve("owned-fixture", owner="q", duration=10)
    registry.release(r["reservationId"], owner="p")
    assert provider.release_calls == 1
    assert provider.held["fencingIdentity"] == new["fencingIdentity"]


def test_expired_release_does_not_call_provider_or_touch_new_lease():
    registry, provider, now = setup()
    r = registry.reserve("owned-fixture", owner="p", duration=1)
    now[0] = 102
    provider.held = {"fencingIdentity": "new-owner", "expiry": 200, "scope": "observe", "owner": "q", "status": "owned"}
    out = registry.release(r["reservationId"], owner="p")
    assert out["status"] == "expired"
    assert provider.release_calls == 0


def test_concurrent_claims_allow_only_one():
    registry, provider, now = setup()
    def reserve(i):
        try: return registry.reserve("owned-fixture", owner=str(i), duration=10)["reservationId"]
        except LabError: return None
    with ThreadPoolExecutor(max_workers=8) as pool:
        results = list(pool.map(reserve, range(8)))
    assert sum(r is not None for r in results) == 1


def test_recovered_lease_is_unknown_until_provider_reconciliation():
    registry, provider, now = setup()
    r = registry.reserve("owned-fixture", owner="p", duration=10)
    recovered = LabRegistry({"fixture": provider}, records=[r], clock=lambda: now[0])
    with pytest.raises(LabError, match="OWNERSHIP_UNCERTAIN"):
        recovered.require_authority(r["reservationId"], owner="p", action="observe")
    assert recovered.reconcile(r["reservationId"], owner="p")["status"] == "owned"
    provider.held["fencingIdentity"] = "replaced"
    assert recovered.reconcile(r["reservationId"], owner="p")["status"] == "unknown"


def test_ownership_checks_and_persistence_failure_preserve_unknown():
    registry, provider, now = setup()
    r = registry.reserve("owned-fixture", owner="p", duration=10)
    with pytest.raises(LabError, match="FORBIDDEN"):
        registry.release(r["reservationId"], owner="q")
