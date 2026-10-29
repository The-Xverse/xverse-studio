"""Real bounded threads over owned in-memory callbacks, never actual equipment."""

import threading
import time
from types import SimpleNamespace
import pytest
from xverse_studio.lab import LabError, LabRegistry

from xverse_studio.lab.bounded import BoundedLeaseProvider


def test_timeout_keeps_capacity_until_real_completion_and_never_reacquires():
    entered, finish, returned = threading.Event(), threading.Event(), threading.Event()
    held = []

    def acquire(asset, scope, owner, deadline):
        entered.set()
        try:
            assert finish.wait(3)
            held.append(owner)
            return {
                "owner": owner,
                "scope": scope,
                "expiry": deadline,
                "status": "owned",
                "fencingIdentity": "late-fixture-fence",
            }
        finally:
            returned.set()

    asset = {
        "assetId": "fixture:asset",
        "providerId": "fixture",
        "capabilities": ["observe"],
    }
    provider = SimpleNamespace(inventory=lambda: [asset], reserve=acquire)
    bounded = BoundedLeaseProvider(provider, timeout=0.03)
    writes = []
    registry = LabRegistry(
        {"fixture": bounded},
        clock=lambda: 100,
        persist=lambda records: writes.append(records),
    )
    start = time.monotonic()
    try:
        with pytest.raises(LabError, match="^OWNERSHIP_UNCERTAIN$"):
            registry.reserve("fixture:asset", owner="fixture-owner")
        assert time.monotonic() - start < 0.5 and entered.is_set()
        rec = next(iter(registry.records.values()))
        assert rec["status"] == "unknown" and rec["fencingIdentity"] is None
        before = len(writes)
        for _ in range(5):
            with pytest.raises(LabError, match="^PROVIDER_CALL_UNSETTLED$"):
                bounded.reserve(asset, "observe", "other-owner", 160)
        assert not held and len(writes) == before
    finally:
        finish.set()
        assert returned.wait(3)
    # The original acquired lease exists, but a late acknowledgement never makes
    # the registry authoritative or invokes a second reservation.
    assert held == ["fixture-owner"]
    assert rec["status"] == "unknown" and rec["fencingIdentity"] is None
    assert bounded.inventory()[0]["assetId"] == asset["assetId"]


def test_inputs_and_results_are_copied_at_the_provider_boundary():
    incoming = {"assetId": "fixture:asset", "nested": {"original": True}}
    observed = {"status": "owned", "fencingIdentity": "fixture-original-fence"}

    def acquire(asset, scope, owner, deadline):
        asset["nested"]["original"] = False
        return observed

    bounded = BoundedLeaseProvider(SimpleNamespace(reserve=acquire))
    result = bounded.reserve(incoming, "observe", "fixture-owner", 160)
    result["fencingIdentity"] = "client-only-fence"
    assert (
        incoming["nested"]["original"] is True
        and observed["fencingIdentity"] == "fixture-original-fence"
    )


@pytest.mark.parametrize(
    "error,code",
    [
        (ConnectionError("private endpoint"), "PROVIDER_OPERATION_UNKNOWN"),
        (LabError("RESOURCE_BUSY"), "RESOURCE_BUSY"),
        (
            LabError({"private": "fixture-only unstructured code"}),
            "PROVIDER_OPERATION_UNKNOWN",
        ),
    ],
)
def test_private_exception_text_never_leaves_provider_boundary_and_slot_recovers(
    error, code
):
    def refusal(*args):
        raise error

    bounded = BoundedLeaseProvider(
        SimpleNamespace(reserve=refusal, inventory=lambda: [])
    )
    with pytest.raises(LabError, match="^" + code + "$") as caught:
        bounded.reserve({}, "observe", "fixture-owner", 160)
    assert "private endpoint" not in str(caught.value)
    assert bounded.inventory() == []


@pytest.mark.parametrize(
    "value", [True, None, 0, -1, 6, float("inf"), float("nan"), "1"]
)
def test_invalid_or_unbounded_timeout_is_refused(value):
    with pytest.raises(LabError, match="^PROVIDER_CONFIG_INVALID$"):
        BoundedLeaseProvider(SimpleNamespace(), timeout=value)


def test_unrecognized_typed_error_text_does_not_escape_the_provider_boundary():
    def refusal(*args):
        raise LabError("private endpoint with credential-shaped text")

    bounded = BoundedLeaseProvider(SimpleNamespace(reserve=refusal))
    with pytest.raises(LabError, match="^PROVIDER_OPERATION_UNKNOWN$"):
        bounded.reserve({}, "observe", "fixture-owner", 160)


def test_response_projection_excludes_private_metadata_and_rejects_unbounded_inventory():
    asset = {
        "assetId": "fixture:asset",
        "providerId": "fixture",
        "capabilities": ["observe"],
        "privateEndpoint": "private fixture endpoint",
    }
    provider = SimpleNamespace(inventory=lambda: [asset])
    bounded = BoundedLeaseProvider(provider)
    observed = bounded.inventory()
    assert (
        observed[0]["assetId"] == asset["assetId"]
        and "privateEndpoint" not in observed[0]
    )
    provider.inventory = lambda: [asset] * 1001
    with pytest.raises(LabError, match="^PROVIDER_RESPONSE_INVALID$"):
        bounded.inventory()


def test_lease_projection_excludes_unknown_fields_and_refuses_boolean_expiry():
    record = {
        "status": "owned",
        "owner": "fixture-owner",
        "scope": "observe",
        "fencingIdentity": "fixture-fence",
        "expiry": 160,
        "privateData": "private fixture data",
    }
    provider = SimpleNamespace(reserve=lambda *args: record)
    bounded = BoundedLeaseProvider(provider)
    observed = bounded.reserve({}, "observe", "fixture-owner", 160)
    assert observed["expiry"] == 160 and "privateData" not in observed
    record["expiry"] = True
    with pytest.raises(LabError, match="^PROVIDER_RESPONSE_INVALID$"):
        bounded.reserve({}, "observe", "fixture-owner", 160)
