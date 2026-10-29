"""Owned SQLite and in-memory lease fixtures; no equipment or live-provider claim."""

from copy import deepcopy
import importlib.util
from pathlib import Path
import pytest
from xverse_studio.lab import LabError
from xverse_studio.storage.core import Store


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


from xverse_studio.lab import persistence as proposal

cases = load(
    "owned_lease_backing_fixture", Path(__file__).with_name("test_lab_reservations.py")
)


@pytest.fixture
def bench(tmp_path):
    store = Store(tmp_path / "owned lease ledger Ω")
    provider = cases.FixtureProvider()
    now = [100]
    backing = proposal.LabLeaseBacking(store)
    registry = backing.registry({"fixture": provider}, clock=lambda: now[0])
    return store, provider, now, backing, registry


def test_intent_is_committed_before_provider_and_restart_requires_reconciliation(
    bench, monkeypatch
):
    store, provider, now, backing, registry = bench
    reserve = provider.reserve
    observed = []

    def delegate(*args, **kwargs):
        intent = store.get(backing.KIND, backing.KEY)["records"]
        assert (
            len(intent) == 1
            and intent[0]["status"] == "unknown"
            and intent[0]["fencingIdentity"] is None
        )
        observed.append(intent)
        return reserve(*args, **kwargs)

    monkeypatch.setattr(provider, "reserve", delegate)
    lease = registry.reserve("owned-fixture", owner="fixture-owner", duration=10)
    assert (
        len(observed) == 1
        and store.get(backing.KIND, backing.KEY)["records"][0]["status"] == "owned"
    )
    restored = proposal.LabLeaseBacking(store).registry(
        {"fixture": provider}, clock=lambda: now[0]
    )
    assert (
        restored.get(lease["reservationId"], owner="fixture-owner")["status"]
        == "unknown"
    )
    with pytest.raises(LabError, match="^OWNERSHIP_UNCERTAIN$"):
        restored.require_authority(
            lease["reservationId"], owner="fixture-owner", action="observe"
        )
    assert (
        restored.reconcile(lease["reservationId"], owner="fixture-owner")["status"]
        == "owned"
    )
    assert len(observed) == 1


def test_stale_snapshot_cannot_overwrite_newer_lease_or_delegate(bench, monkeypatch):
    store, provider, now, first, registry = bench
    second = proposal.LabLeaseBacking(store)
    stale = second.registry({"fixture": provider}, clock=lambda: now[0])
    reserve = provider.reserve
    calls = []

    def delegate(*args, **kwargs):
        calls.append(1)
        return reserve(*args, **kwargs)

    monkeypatch.setattr(provider, "reserve", delegate)
    lease = registry.reserve("owned-fixture", owner="first-owner")
    saved = store.get(first.KIND, first.KEY)
    with pytest.raises(LabError, match="^LAB_STATE_STALE$"):
        stale.reserve("owned-fixture", owner="stale-owner")
    assert store.get(first.KIND, first.KEY) == saved and len(calls) == 1
    assert (
        provider.held["owner"] == "first-owner"
        and provider.held["fencingIdentity"] == lease["fencingIdentity"]
    )
    first.assert_current()
    with pytest.raises(LabError, match="^LAB_STATE_STALE$"):
        second.assert_current()


def test_transaction_failure_before_intent_prevents_provider_delegation(
    bench, monkeypatch
):
    store, provider, now, backing, registry = bench
    put = store.put

    def fail_after_insert(kind, identity, value, db=None):
        put(kind, identity, value, db)
        if kind == backing.KIND:
            raise OSError("owned ledger transaction refusal")

    monkeypatch.setattr(store, "put", fail_after_insert)
    with pytest.raises(OSError, match="owned ledger transaction refusal"):
        registry.reserve("owned-fixture", owner="fixture-owner")
    assert store.all(backing.KIND) == [] and provider.held is None
    assert backing.load() == []


def test_released_history_stays_terminal_after_real_sqlite_reload(bench):
    store, provider, now, backing, registry = bench
    old = registry.reserve("owned-fixture", owner="old-owner")
    registry.release(old["reservationId"], owner="old-owner")
    new = registry.reserve("owned-fixture", owner="new-owner")
    held = deepcopy(provider.held)
    restored = proposal.LabLeaseBacking(store).registry(
        {"fixture": provider}, clock=lambda: now[0]
    )
    assert (
        restored.release(old["reservationId"], owner="old-owner")["status"]
        == "released"
    )
    assert (
        restored.reconcile(old["reservationId"], owner="old-owner")["status"]
        == "released"
    )
    assert (
        provider.release_calls == 1
        and provider.held == held
        and held["fencingIdentity"] == new["fencingIdentity"]
    )


@pytest.mark.parametrize(
    "value",
    [
        {"contractVersion": "2.0", "revision": 1, "records": []},
        {"contractVersion": "1.0", "revision": True, "records": []},
        {"contractVersion": "1.0", "revision": 1, "records": {}},
    ],
)
def test_invalid_version_or_shape_is_preserved_and_never_loaded_as_authority(
    bench, value
):
    store, provider, now, backing, registry = bench
    store.put(backing.KIND, backing.KEY, value)
    with pytest.raises(LabError, match="^LAB_STATE_UNAVAILABLE$"):
        proposal.LabLeaseBacking(store).load()
    assert store.get(backing.KIND, backing.KEY) == value and provider.held is None


def test_oversized_snapshot_is_refused_without_replacing_existing_state(bench):
    store, provider, now, backing, registry = bench
    lease = registry.reserve("owned-fixture", owner="fixture-owner")
    saved = store.get(backing.KIND, backing.KEY)
    small = proposal.LabLeaseBacking(store, max_bytes=1024)
    records = small.load()
    records[0]["opaqueExtension"] = "x" * 2048
    with pytest.raises(LabError, match="^LIMIT_EXCEEDED$"):
        small.save(records)
    assert (
        store.get(backing.KIND, backing.KEY) == saved
        and provider.held["fencingIdentity"] == lease["fencingIdentity"]
    )


@pytest.mark.parametrize("also_expected", [False, True])
def test_unknown_ledger_identity_is_preserved_and_cannot_be_treated_as_empty(
    bench, also_expected
):
    store, provider, now, backing, registry = bench
    value = {"contractVersion": "1.0", "revision": 1, "records": []}
    store.put(backing.KIND, "unrecognized-ledger", value)
    if also_expected:
        store.put(backing.KIND, backing.KEY, value)
    with pytest.raises(LabError, match="^LAB_STATE_UNAVAILABLE$"):
        proposal.LabLeaseBacking(store).load()
    assert (
        store.get(backing.KIND, "unrecognized-ledger") == value
        and provider.held is None
    )
