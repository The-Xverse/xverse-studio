"""Registry-only T073 fixtures; positive HTTP authorization remains T074 work."""

from concurrent.futures import ThreadPoolExecutor
from copy import deepcopy
import importlib.util
import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from xverse_studio.lab import LabRegistry, LabError

_spec = importlib.util.spec_from_file_location(
    "reservation_physical_fixture",
    Path(__file__).resolve().parents[1] / "fixtures/providers/physical/provider.py",
)
_physical = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_physical)


@pytest.fixture
def persisted_fixture(tmp_path):
    """Serialize fixture lease snapshots; no real provider or permission is installed."""
    now, writes = [100], []
    provider = _physical.PhysicalContractFixture(lambda: now[0])
    path = tmp_path / "fixture-leases.json"

    def persist(records):
        writes.append(deepcopy(records))
        path.write_text(json.dumps(records))

    def restore():
        return LabRegistry(
            {provider.provider_id: provider},
            clock=lambda: now[0],
            records=json.loads(path.read_text()),
            persist=persist,
        )

    registry = LabRegistry(
        {provider.provider_id: provider},
        clock=lambda: now[0],
        persist=persist,
    )
    return SimpleNamespace(
        registry=registry,
        provider=provider,
        now=now,
        writes=writes,
        path=path,
        restore=restore,
    )


class FixtureProvider:
    """Owned in-memory fixture; never registers in the shipped application."""

    def __init__(self):
        self.held = None
        self.fence = 0
        self.release_calls = 0

    def inventory(self):
        return [
            {
                "assetId": "owned-fixture",
                "providerId": "fixture",
                "identity": {"serial": "fixture-1"},
                "physical": False,
                "evidenceScope": "fixture",
                "capabilities": ["observe", "stimulate"],
                "interfaces": {"input": "scalar@1"},
            }
        ]

    def reserve(self, asset, scope, owner, deadline):
        if self.held:
            raise LabError("RESOURCE_BUSY")
        self.fence += 1
        self.held = {
            "fencingIdentity": str(self.fence),
            "expiry": deadline,
            "owner": owner,
            "scope": scope,
            "status": "owned",
        }
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
        registry.require_authority(
            r["reservationId"], owner="principal", action="stimulate"
        )


def test_active_scope_requires_explicit_grant_and_provider_capability():
    registry, provider, now = setup()
    with pytest.raises(LabError, match="FORBIDDEN"):
        registry.reserve("owned-fixture", owner="p", scope="stimulate", duration=10)
    r = registry.reserve(
        "owned-fixture",
        owner="p",
        scope="stimulate",
        duration=10,
        granted_scopes={"stimulate"},
    )
    assert (
        registry.require_authority(
            r["reservationId"],
            owner="p",
            action="stimulate",
            granted_scopes={"stimulate"},
        )["status"]
        == "owned"
    )
    with pytest.raises(LabError, match="CAPABILITY_UNSUPPORTED"):
        registry.require_authority(
            r["reservationId"],
            owner="p",
            action="destructive",
            granted_scopes={"destructive"},
        )


def test_expiry_and_stale_fence_cannot_renew_or_enable_commands():
    registry, provider, now = setup()
    r = registry.reserve("owned-fixture", owner="p", duration=10)
    with pytest.raises(LabError, match="STALE_FENCING_IDENTITY"):
        registry.renew(
            r["reservationId"], owner="p", expected_fencing_identity="old", duration=10
        )
    now[0] = 111
    assert registry.get(r["reservationId"], owner="p")["status"] == "expired"
    with pytest.raises(LabError, match="OWNERSHIP_UNCERTAIN"):
        registry.renew(
            r["reservationId"],
            owner="p",
            expected_fencing_identity=r["fencingIdentity"],
            duration=10,
        )
    assert provider.fence == 1


def test_renew_same_scope_and_idempotent_release_never_affects_new_owner():
    registry, provider, now = setup()
    r = registry.reserve("owned-fixture", owner="p", duration=10)
    updated = registry.renew(
        r["reservationId"],
        owner="p",
        expected_fencing_identity=r["fencingIdentity"],
        duration=15,
    )
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
    provider.held = {
        "fencingIdentity": "new-owner",
        "expiry": 200,
        "scope": "observe",
        "owner": "q",
        "status": "owned",
    }
    out = registry.release(r["reservationId"], owner="p")
    assert out["status"] == "expired"
    assert provider.release_calls == 0


def test_concurrent_claims_allow_only_one():
    registry, provider, now = setup()

    def reserve(i):
        try:
            return registry.reserve("owned-fixture", owner=str(i), duration=10)[
                "reservationId"
            ]
        except LabError:
            return None

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


def test_another_owner_cannot_release_an_existing_reservation():
    registry, provider, now = setup()
    r = registry.reserve("owned-fixture", owner="p", duration=10)
    with pytest.raises(LabError, match="FORBIDDEN"):
        registry.release(r["reservationId"], owner="q")


def test_persistence_failure_before_reserve_prevents_delegation(persisted_fixture):
    bench = persisted_fixture
    attempts = []

    def refuse_write(records):
        attempts.append(deepcopy(records))
        raise OSError("fixture persistence unavailable")

    bench.registry.persist = refuse_write
    with pytest.raises(OSError, match="fixture persistence unavailable"):
        bench.registry.reserve(bench.provider.asset_id, owner="fixture-owner")
    assert len(attempts) == 1 and attempts[0][0]["status"] == "unknown"
    assert not bench.path.exists() and bench.provider.held == {}
    assert "reserve" not in bench.provider.calls
    reservation_id = attempts[0][0]["reservationId"]
    with pytest.raises(LabError, match="^OWNERSHIP_UNCERTAIN$"):
        bench.registry.require_authority(
            reservation_id, owner="fixture-owner", action="observe"
        )


def test_restart_after_lost_reserve_ack_never_reacquires_or_invents_a_fence(
    persisted_fixture,
):
    bench = persisted_fixture
    bench.provider.lose_reserve_ack = True
    with pytest.raises(LabError, match="^OWNERSHIP_UNCERTAIN$"):
        bench.registry.reserve(
            bench.provider.asset_id, owner="fixture-owner", duration=10
        )
    saved = json.loads(bench.path.read_text())[0]
    assert saved["status"] == "unknown" and saved["fencingIdentity"] is None
    assert saved["reason"] == "RESERVATION_ACKNOWLEDGEMENT_LOST"
    recovered = bench.restore()
    assert (
        recovered.reconcile(saved["reservationId"], owner="fixture-owner")["status"]
        == "unknown"
    )
    with pytest.raises(LabError, match="^OWNERSHIP_UNCERTAIN$"):
        recovered.require_authority(
            saved["reservationId"], owner="fixture-owner", action="observe"
        )
    with pytest.raises(LabError, match="^RESOURCE_BUSY$"):
        recovered.reserve(bench.provider.asset_id, owner="other-owner", duration=10)
    assert bench.provider.calls.count("reserve") == 1
    assert bench.provider.held[bench.provider.asset_id]["owner"] == "fixture-owner"


def test_restart_after_lost_renew_ack_keeps_the_last_confirmed_deadline(
    persisted_fixture,
):
    bench = persisted_fixture
    lease = bench.registry.reserve(
        bench.provider.asset_id, owner="fixture-owner", duration=10
    )
    bench.provider.lose_renew_ack = True
    with pytest.raises(LabError, match="^OWNERSHIP_UNCERTAIN$"):
        bench.registry.renew(
            lease["reservationId"],
            owner="fixture-owner",
            expected_fencing_identity=lease["fencingIdentity"],
            duration=20,
        )
    saved = json.loads(bench.path.read_text())[0]
    assert saved["status"] == "unknown" and saved["expiry"] == lease["expiry"] == 110
    assert bench.provider.held[bench.provider.asset_id]["expiry"] == 120
    recovered = bench.restore()
    assert (
        recovered.reconcile(lease["reservationId"], owner="fixture-owner")["status"]
        == "unknown"
    )
    with pytest.raises(LabError, match="^OWNERSHIP_UNCERTAIN$"):
        recovered.require_authority(
            lease["reservationId"], owner="fixture-owner", action="observe"
        )
    assert (
        bench.provider.calls.count("reserve")
        == bench.provider.calls.count("renew")
        == 1
    )


def test_lost_release_ack_and_restart_never_repeat_an_uncertain_release(
    persisted_fixture, monkeypatch
):
    bench = persisted_fixture
    lease = bench.registry.reserve(bench.provider.asset_id, owner="fixture-owner")
    release = bench.provider.release

    def lose_ack(*args, **kwargs):
        release(*args, **kwargs)
        raise ConnectionError("fixture release acknowledgement lost")

    monkeypatch.setattr(bench.provider, "release", lose_ack)
    with pytest.raises(LabError, match="^OWNERSHIP_UNCERTAIN$"):
        bench.registry.release(lease["reservationId"], owner="fixture-owner")
    saved = json.loads(bench.path.read_text())[0]
    assert saved["status"] == "unknown" and saved["reason"] == "RELEASE_UNCERTAIN"
    assert bench.provider.held == {}
    recovered = bench.restore()
    for registry in (bench.registry, recovered):
        with pytest.raises(LabError, match="^OWNERSHIP_UNCERTAIN$"):
            registry.release(lease["reservationId"], owner="fixture-owner")
    assert (
        recovered.reconcile(lease["reservationId"], owner="fixture-owner")["status"]
        == "unknown"
    )
    assert bench.provider.calls.count("release") == 1


@pytest.mark.parametrize(
    "patch",
    [
        {"owner": "other-owner"},
        {"scope": "stimulate"},
        {"status": "released"},
        {"fencingIdentity": ""},
        {"fencingIdentity": None},
        {"expiry": "110"},
        {"expiry": float("inf")},
        {"expiry": 100},
        {"expiry": 111},
    ],
)
def test_malformed_reservation_ack_is_unknown_and_cannot_enable_authority(
    persisted_fixture, monkeypatch, patch
):
    bench = persisted_fixture
    reserve = bench.provider.reserve

    def invalid_ack(*args, **kwargs):
        return {**reserve(*args, **kwargs), **patch}

    monkeypatch.setattr(bench.provider, "reserve", invalid_ack)
    with pytest.raises(LabError, match="^OWNERSHIP_UNCERTAIN$"):
        bench.registry.reserve(
            bench.provider.asset_id, owner="fixture-owner", duration=10
        )
    saved = json.loads(bench.path.read_text())[0]
    assert (
        saved["status"] == "unknown"
        and saved["reason"] == "PROVIDER_RESERVATION_INVALID"
    )
    assert saved["owner"] == "fixture-owner" and saved["scope"] == "observe"
    assert saved["expiry"] == 110 and saved["fencingIdentity"] is None
    with pytest.raises(LabError, match="^OWNERSHIP_UNCERTAIN$"):
        bench.registry.require_authority(
            saved["reservationId"], owner="fixture-owner", action="observe"
        )
    assert bench.provider.calls.count("reserve") == 1


@pytest.mark.parametrize(
    "patch",
    [
        {"owner": "other-owner"},
        {"scope": "stimulate"},
        {"fencingIdentity": "replacement-fence"},
        {"status": "unknown"},
        {"expiry": 121},
    ],
)
def test_renewal_cannot_change_owner_scope_fence_or_exceed_requested_deadline(
    persisted_fixture, monkeypatch, patch
):
    bench = persisted_fixture
    lease = bench.registry.reserve(
        bench.provider.asset_id, owner="fixture-owner", duration=10
    )
    renew = bench.provider.renew

    def invalid_ack(*args, **kwargs):
        return {**renew(*args, **kwargs), **patch}

    monkeypatch.setattr(bench.provider, "renew", invalid_ack)
    with pytest.raises(LabError, match="^OWNERSHIP_UNCERTAIN$"):
        bench.registry.renew(
            lease["reservationId"],
            owner="fixture-owner",
            expected_fencing_identity=lease["fencingIdentity"],
            duration=20,
        )
    saved = json.loads(bench.path.read_text())[0]
    assert saved["status"] == "unknown" and saved["reason"] == "RENEWAL_UNCERTAIN"
    assert saved["owner"] == lease["owner"] and saved["scope"] == lease["scope"]
    assert (
        saved["fencingIdentity"] == lease["fencingIdentity"]
        and saved["expiry"] == lease["expiry"]
    )
    with pytest.raises(LabError, match="^OWNERSHIP_UNCERTAIN$"):
        bench.registry.require_authority(
            lease["reservationId"], owner="fixture-owner", action="observe"
        )


def test_revoked_active_grant_prevents_renewal_before_provider_delegation(
    persisted_fixture,
):
    bench = persisted_fixture
    lease = bench.registry.reserve(
        bench.provider.asset_id,
        owner="fixture-owner",
        scope="stimulate",
        duration=10,
        granted_scopes={"stimulate"},
    )
    with pytest.raises(LabError, match="^FORBIDDEN$"):
        bench.registry.renew(
            lease["reservationId"],
            owner="fixture-owner",
            expected_fencing_identity=lease["fencingIdentity"],
            duration=20,
            granted_scopes=(),
        )
    assert "renew" not in bench.provider.calls
    assert (
        bench.registry.get(lease["reservationId"], owner="fixture-owner")["expiry"]
        == 110
    )
    with pytest.raises(LabError, match="^FORBIDDEN$"):
        bench.registry.require_authority(
            lease["reservationId"], owner="fixture-owner", action="stimulate"
        )


@pytest.mark.parametrize("duration", [5, 10])
def test_requested_non_extension_is_rejected_without_provider_renewal(
    persisted_fixture, duration
):
    bench = persisted_fixture
    lease = bench.registry.reserve(
        bench.provider.asset_id, owner="fixture-owner", duration=10
    )
    with pytest.raises(LabError, match="^LEASE_NOT_EXTENSION$"):
        bench.registry.renew(
            lease["reservationId"],
            owner="fixture-owner",
            expected_fencing_identity=lease["fencingIdentity"],
            duration=duration,
        )
    assert "renew" not in bench.provider.calls
    assert (
        bench.registry.get(lease["reservationId"], owner="fixture-owner")["status"]
        == "owned"
    )
