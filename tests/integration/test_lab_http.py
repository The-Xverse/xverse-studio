"""Actual installed HTTP routes with explicit host configuration and owned fixtures.

No route replacement, hardware admission or physical action; actual middleware
and server-owned grants enforce independent reservation scopes.
"""

import importlib
import importlib.util
from pathlib import Path
from types import SimpleNamespace
import pytest
from fastapi.testclient import TestClient

from xverse_studio.api.app import create_app

from xverse_studio.lab.authority import LabAuthority

spec = importlib.util.spec_from_file_location(
    "owned_lab_http_fixture",
    Path(__file__).resolve().parents[1] / "fixtures/providers/physical/provider.py",
)
fixtures = importlib.util.module_from_spec(spec)
spec.loader.exec_module(fixtures)


def prepare(root, provider, policy, now, *, timeout=1.0, version="1.0.0"):
    import platform
    from xverse_studio.lab.configuration import (
        LabHostConfiguration,
        LeaseProviderInstallation,
    )

    installation = LeaseProviderInstallation(
        provider,
        provider.provider_id,
        version,
        "sha256:" + "a" * 64,
        (platform.system(),),
        (platform.machine(),),
        "fixture",
        "fixture-conformance",
        "fixture-no-equipment",
    )
    host = LabHostConfiguration(
        (installation,), policy, clock=lambda: now[0], call_timeout=timeout
    )
    app = create_app(
        root,
        allowed_hosts=["testserver"],
        bootstrap_token="owned-http-fixture-bootstrap",
        lab_host=host,
    )
    return app, app.state.studio.lab_reservations


def login(client):
    client.headers["Origin"] = "http://testserver"
    result = client.post(
        "/api/v1/session", json={"bootstrapToken": "owned-http-fixture-bootstrap"}
    )
    assert result.status_code == 200
    client.headers["X-CSRF-Token"] = result.json()["csrfToken"]


@pytest.fixture
def bench(tmp_path):
    now = [100]
    provider = fixtures.PhysicalContractFixture(lambda: now[0])
    policy = LabAuthority({("local-operator", provider.asset_id): {"observe"}})
    app, service = prepare(tmp_path / "owned proposed HTTP Ω", provider, policy, now)
    with TestClient(app, base_url="http://testserver") as client:
        login(client)
        yield SimpleNamespace(
            client=client, service=service, provider=provider, policy=policy, now=now
        )


def acquire(bench, *, key="acquire", body=None):
    return bench.client.post(
        "/api/v1/assets/" + bench.provider.asset_id + "/reservations",
        headers={"Idempotency-Key": key},
        json={} if body is None else body,
    )


def test_real_session_positive_observe_same_key_conflict_and_release(bench):
    first = acquire(bench)
    assert first.status_code == 202 and first.json()["status"] == "completed"
    assert acquire(bench).json() == first.json()
    rid = first.json()["reservationId"]
    record = bench.client.get("/api/v1/reservations/" + rid)
    assert (
        record.status_code == 200
        and record.json()["scope"] == "observe"
        and record.json()["evidenceScope"] == "fixture"
    )
    op = bench.client.get("/api/v1/operations/" + first.json()["operationId"])
    assert op.status_code == 200 and op.json() == first.json()
    conflict = acquire(bench, body={"durationSeconds": 31})
    assert (
        conflict.status_code == 409
        and conflict.json()["code"] == "IDEMPOTENCY_CONFLICT"
    )
    released = bench.client.delete(
        "/api/v1/reservations/" + rid, headers={"Idempotency-Key": "release"}
    )
    assert (
        released.status_code == 202
        and released.json()["result"]["status"] == "released"
    )
    assert (
        bench.provider.calls.count("reserve")
        == bench.provider.calls.count("release")
        == 1
    )


@pytest.mark.parametrize("scope", ["stimulate", "destructive"])
def test_each_active_scope_requires_its_own_server_grant(bench, scope):
    refused = acquire(bench, body={"scope": scope})
    assert refused.status_code == 403 and refused.json()["code"] == "FORBIDDEN"
    assert bench.provider.calls.count("reserve") == 0
    # Explicitly declare this synthetic capability only for the positive fixture
    # lane; neither the stock fixture nor actual equipment gains this operation.
    if scope == "destructive":
        bench.provider.assets[0]["capabilities"].append("destructive")
    bench.policy.set_scopes("local-operator", bench.provider.asset_id, {scope})
    accepted = acquire(bench, body={"scope": scope})
    assert accepted.status_code == 202 and accepted.json()["status"] == "completed"
    record = bench.client.get(
        "/api/v1/reservations/" + accepted.json()["reservationId"]
    ).json()
    assert record["scope"] == scope and record["evidenceScope"] == "fixture"
    other = "destructive" if scope == "stimulate" else "stimulate"
    still_refused = acquire(bench, key="other", body={"scope": other})
    assert (
        still_refused.status_code == 403 and bench.provider.calls.count("reserve") == 1
    )


@pytest.mark.parametrize(
    "body",
    [
        {"owner": "different-owner"},
        {"grantedScopes": ["stimulate"]},
        {"providerId": "unapproved"},
        {"scope": "admin"},
        {"durationSeconds": True},
        {"durationSeconds": 301},
    ],
)
def test_browser_cannot_supply_owner_grants_provider_or_invalid_limits(bench, body):
    result = acquire(bench, body=body)
    assert result.status_code == 422 and result.json()["code"] == "REQUEST_INVALID"
    assert bench.provider.calls == [] and bench.service.store.all("operation") == []


@pytest.mark.parametrize(
    "header,value",
    [("X-CSRF-Token", "bad-fixture-csrf"), ("Origin", "http://foreign.invalid")],
)
def test_actual_boundary_refuses_before_provider_contact(bench, header, value):
    bench.client.headers[header] = value
    result = acquire(bench)
    assert result.status_code == 403 and result.json()["code"] == "FORBIDDEN"
    assert bench.provider.calls == []


def test_unknown_response_is_accepted_without_reacquisition_on_retry(bench):
    bench.provider.lose_reserve_ack = True
    first = acquire(bench)
    assert first.status_code == 202 and first.json()["status"] == "unknown"
    assert (
        acquire(bench).json() == first.json()
        and bench.provider.calls.count("reserve") == 1
    )
    rid = first.json()["reservationId"]
    record = bench.client.get("/api/v1/reservations/" + rid)
    assert (
        record.json()["status"] == "unknown"
        and record.json()["fencingIdentity"] is None
    )
    renewed = bench.client.post(
        "/api/v1/reservations/" + rid + "/renewals",
        headers={"Idempotency-Key": "renew-unknown"},
        json={"fencingIdentity": "invented-fixture-fence"},
    )
    assert (
        renewed.status_code == 422 and renewed.json()["code"] == "OWNERSHIP_UNCERTAIN"
    )
    assert bench.provider.calls.count("renew") == 0


def test_grant_alone_cannot_supply_an_unsupported_destructive_capability(bench):
    bench.policy.set_scopes("local-operator", bench.provider.asset_id, {"destructive"})
    result = acquire(bench, body={"scope": "destructive"})
    assert (
        result.status_code == 422 and result.json()["code"] == "CAPABILITY_UNSUPPORTED"
    )
    assert (
        bench.provider.calls.count("reserve") == 0
        and bench.service.store.all("operation") == []
    )


def test_failed_lease_acknowledgement_commit_cannot_leave_active_memory_authority(
    bench, monkeypatch
):
    from xverse_studio.lab import LabError

    put = bench.service.store.put

    def fail_owned_ledger(kind, identity, body, db=None):
        if kind == "lab_registry" and any(
            row["status"] == "owned" for row in body["records"]
        ):
            raise OSError("owned fixture acknowledgement persistence failure")
        return put(kind, identity, body, db)

    monkeypatch.setattr(bench.service.store, "put", fail_owned_ledger)
    result = acquire(bench)
    assert result.status_code == 202 and result.json()["status"] == "unknown"
    rid = result.json()["reservationId"]
    record = bench.client.get("/api/v1/reservations/" + rid)
    assert record.status_code == 200 and record.json()["status"] == "unknown"
    with pytest.raises(LabError, match="^OWNERSHIP_UNCERTAIN$"):
        bench.service.require_authority(rid, owner="local-operator", action="observe")
    assert bench.provider.calls.count("reserve") == 1
    assert bench.provider.held[bench.provider.asset_id]["owner"] == "local-operator"
    assert (
        bench.service.store.get("lab_registry", "leases")["records"][0]["status"]
        == "unknown"
    )


def test_failed_final_receipt_commit_reports_unknown_without_replaying_acquisition(
    bench, monkeypatch
):
    put = bench.service.store.put

    def fail_completed_receipt(kind, identity, body, db=None):
        if (
            kind == "operation"
            and body.get("kind") == "lab_reserve"
            and body.get("status") == "completed"
        ):
            raise OSError("owned fixture final receipt persistence failure")
        return put(kind, identity, body, db)

    monkeypatch.setattr(bench.service.store, "put", fail_completed_receipt)
    result = acquire(bench)
    assert result.status_code == 202 and result.json()["status"] == "unknown"
    assert result.json()["code"] == "LAB_OPERATION_RECORD_UNCERTAIN"
    retry = acquire(bench)
    assert retry.json() == result.json() and bench.provider.calls.count("reserve") == 1


@pytest.mark.parametrize("same_key", [True, False])
def test_two_actual_http_clients_share_durable_scope_and_exclusive_lease(
    bench, monkeypatch, same_key
):
    from concurrent.futures import ThreadPoolExecutor
    import threading

    entered, finish, second_started = (
        threading.Event(),
        threading.Event(),
        threading.Event(),
    )
    original = bench.provider.reserve

    def hold_first(*args):
        entered.set()
        assert finish.wait(3), "bounded owned fixture wait"
        return original(*args)

    monkeypatch.setattr(bench.provider, "reserve", hold_first)
    bench.service.registry.providers[bench.provider.provider_id]._timeout = 5.0
    second = TestClient(bench.client.app, base_url="http://testserver")
    second.cookies.update(bench.client.cookies)
    second.headers.update(
        {
            "Origin": "http://testserver",
            "X-CSRF-Token": bench.client.headers["X-CSRF-Token"],
        }
    )

    def other():
        second_started.set()
        return second.post(
            "/api/v1/assets/" + bench.provider.asset_id + "/reservations",
            headers={"Idempotency-Key": "acquire" if same_key else "competing"},
            json={},
        )

    try:
        with ThreadPoolExecutor(max_workers=2) as pool:
            first = pool.submit(acquire, bench)
            try:
                assert entered.wait(3)
                later = pool.submit(other)
                assert second_started.wait(3)
            finally:
                finish.set()
            left, right = first.result(timeout=10), later.result(timeout=10)
        assert left.status_code == right.status_code == 202
        assert left.json()["status"] == "completed"
        if same_key:
            assert right.json() == left.json()
        else:
            assert (
                right.json()["status"] == "rejected"
                and right.json()["code"] == "RESOURCE_BUSY"
            )
        assert bench.provider.calls.count("reserve") == 1
        assert len(bench.service.store.get("lab_registry", "leases")["records"]) == 1
    finally:
        finish.set()
        second.close()


def test_configured_restart_reconciles_same_fence_and_unconfigured_restart_retains_unknown(
    tmp_path,
):
    from xverse_studio.lab import LabError

    now = [100]
    provider = fixtures.PhysicalContractFixture(lambda: now[0])
    policy = LabAuthority({("local-operator", provider.asset_id): {"observe"}})
    root = tmp_path / "owned restart Ω"
    app, service = prepare(root, provider, policy, now)
    with TestClient(app, base_url="http://testserver") as first:
        login(first)
        accepted = first.post(
            "/api/v1/assets/" + provider.asset_id + "/reservations",
            headers={"Idempotency-Key": "first"},
            json={},
        )
        assert accepted.status_code == 202 and accepted.json()["status"] == "completed"
        rid = accepted.json()["reservationId"]
        fence = first.get("/api/v1/reservations/" + rid).json()["fencingIdentity"]
    app, restored = prepare(root, provider, policy, now)
    with TestClient(app, base_url="http://testserver") as second:
        login(second)
        assert second.get("/api/v1/reservations/" + rid).json()["status"] == "unknown"
        with pytest.raises(LabError, match="^OWNERSHIP_UNCERTAIN$"):
            restored.require_authority(rid, owner="local-operator", action="observe")
        retry = second.post(
            "/api/v1/assets/" + provider.asset_id + "/reservations",
            headers={"Idempotency-Key": "first"},
            json={},
        )
        assert retry.json() == accepted.json()
        checked = second.post(
            "/api/v1/reservations/" + rid + "/reconciliations",
            headers={"Idempotency-Key": "inspect"},
            json={},
        )
        assert checked.status_code == 202 and checked.json()["status"] == "completed"
        observed = second.get("/api/v1/reservations/" + rid).json()
        assert observed["status"] == "owned" and observed["fencingIdentity"] == fence
        assert provider.calls.count("reserve") == 1
    app = create_app(
        root,
        allowed_hosts=["testserver"],
        bootstrap_token="owned-http-fixture-bootstrap",
    )
    calls = list(provider.calls)
    with TestClient(app, base_url="http://testserver") as third:
        login(third)
        observed = third.get("/api/v1/reservations/" + rid)
        assert observed.status_code == 200 and observed.json()["status"] == "unknown"
        assert (
            third.get("/api/v1/capabilities").json()["labReservations"]["status"]
            == "unavailable"
        )
        denied = third.post(
            "/api/v1/reservations/" + rid + "/renewals",
            headers={"Idempotency-Key": "not-installed"},
            json={"fencingIdentity": fence, "durationSeconds": 60},
        )
        assert (
            denied.status_code == 422
            and denied.json()["code"] == "PROVIDER_RESERVATION_NOT_ADMITTED"
        )
    assert provider.calls == calls


def test_configured_discovery_preserves_separate_runtime_and_fixture_scope(bench):
    caps = bench.client.get("/api/v1/capabilities")
    assert caps.status_code == 200
    lease = caps.json()["labReservations"]
    assert (
        lease["status"] == "configured" and lease["runtimeAdmission"] == "unavailable"
    )
    assert lease["physicalCommands"] == [] and lease["automaticRunRenewal"] is False
    assert lease["providers"][0]["evidenceScope"] == "fixture"
    assert lease["providers"][0]["authorizationRef"] == "fixture-no-equipment"
    inventory = bench.client.get("/api/v1/assets").json()
    assert (
        inventory["physicalProviderStatus"] == "unavailable"
        and inventory["activeReady"] is False
    )
    assert all(
        item["providerAdmission"] == "unavailable" and item["activeReady"] is False
        for item in inventory["items"]
    )


def test_changed_installed_descriptor_cannot_inherit_original_lease_even_with_same_implementation(
    tmp_path,
):
    now = [100]
    provider = fixtures.PhysicalContractFixture(lambda: now[0])
    policy = LabAuthority({("local-operator", provider.asset_id): {"observe"}})
    root = tmp_path / "descriptor binding Ω"
    app, service = prepare(root, provider, policy, now)
    with TestClient(app, base_url="http://testserver") as first:
        login(first)
        accepted = first.post(
            "/api/v1/assets/" + provider.asset_id + "/reservations",
            headers={"Idempotency-Key": "original"},
            json={},
        )
        assert accepted.status_code == 202 and accepted.json()["status"] == "completed"
    app, restored = prepare(root, provider, policy, now, version="1.1.0")
    calls = list(provider.calls)
    with TestClient(app, base_url="http://testserver") as second:
        login(second)
        result = second.post(
            "/api/v1/reservations/"
            + accepted.json()["reservationId"]
            + "/reconciliations",
            headers={"Idempotency-Key": "inspect"},
            json={},
        )
        assert (
            result.status_code == 422
            and result.json()["code"] == "PROVIDER_IDENTITY_CHANGED"
        )
    assert provider.calls == calls


def test_http_renewal_stale_fence_expiry_and_repeated_terminal_release_preserve_newer_lease(
    bench,
):
    first = acquire(bench)
    assert first.status_code == 202 and first.json()["status"] == "completed"
    rid = first.json()["reservationId"]
    record = bench.client.get("/api/v1/reservations/" + rid).json()
    fence = record["fencingIdentity"]
    bench.now[0] = 101
    renewed = bench.client.post(
        "/api/v1/reservations/" + rid + "/renewals",
        headers={"Idempotency-Key": "extend"},
        json={"fencingIdentity": fence, "durationSeconds": 60},
    )
    assert renewed.status_code == 202 and renewed.json()["status"] == "completed"
    record = bench.client.get("/api/v1/reservations/" + rid).json()
    assert (
        record["expiry"] == 161
        and record["lastRenewal"] == 101
        and record["fencingIdentity"] == fence
    )
    stale = bench.client.post(
        "/api/v1/reservations/" + rid + "/renewals",
        headers={"Idempotency-Key": "stale"},
        json={"fencingIdentity": "fixture-stale", "durationSeconds": 90},
    )
    assert stale.status_code == 422 and stale.json()["code"] == "STALE_FENCING_IDENTITY"
    assert bench.provider.calls.count("renew") == 1
    bench.now[0] = 162
    assert bench.client.get("/api/v1/reservations/" + rid).json()["status"] == "expired"
    expired = bench.client.post(
        "/api/v1/reservations/" + rid + "/renewals",
        headers={"Idempotency-Key": "too-late"},
        json={"fencingIdentity": fence, "durationSeconds": 90},
    )
    assert (
        expired.status_code == 422 and expired.json()["code"] == "OWNERSHIP_UNCERTAIN"
    )
    newer = acquire(bench, key="newer")
    assert newer.status_code == 202 and newer.json()["status"] == "completed"
    held = dict(bench.provider.held[bench.provider.asset_id])
    calls = list(bench.provider.calls)
    for key in ["old-cleanup", "old-again"]:
        terminal = bench.client.delete(
            "/api/v1/reservations/" + rid, headers={"Idempotency-Key": key}
        )
        assert (
            terminal.status_code == 202
            and terminal.json()["result"]["status"] == "expired"
        )
    assert (
        bench.provider.held[bench.provider.asset_id] == held
        and held["fencingIdentity"] != fence
    )
    assert bench.provider.calls == calls and bench.provider.calls.count("reserve") == 2


def test_error_after_final_receipt_commit_reads_back_exact_result_without_redelegation(
    bench, monkeypatch
):
    put = bench.service.store.put

    def lose_commit_ack(kind, identity, body, db=None):
        result = put(kind, identity, body, db)
        if (
            db is None
            and kind == "operation"
            and body.get("kind") == "lab_reserve"
            and body.get("status") == "completed"
        ):
            assert (
                bench.service.store.get("operation", identity)["status"] == "completed"
            )
            raise OSError("owned fixture lost post-commit acknowledgement")
        return result

    monkeypatch.setattr(bench.service.store, "put", lose_commit_ack)
    result = acquire(bench)
    assert result.status_code == 202 and result.json()["status"] == "completed"
    assert acquire(bench).json() == result.json()
    assert bench.provider.calls.count("reserve") == 1
    assert (
        bench.service.store.get("operation", result.json()["operationId"])["status"]
        == "completed"
    )


def test_unavailable_final_receipt_storage_keeps_unknown_reads_and_same_identity(
    bench, monkeypatch
):
    put = bench.service.store.put

    def lose_final_storage(kind, identity, body, db=None):
        if (
            kind == "operation"
            and body.get("kind") == "lab_reserve"
            and body.get("status") in {"completed", "unknown"}
        ):
            raise OSError("owned fixture final storage unavailable")
        return put(kind, identity, body, db)

    monkeypatch.setattr(bench.service.store, "put", lose_final_storage)
    result = acquire(bench)
    assert result.status_code == 202 and result.json()["status"] == "unknown"
    operation_id = result.json()["operationId"]
    for reply in [
        acquire(bench),
        bench.client.get("/api/v1/operations/" + operation_id),
    ]:
        assert (
            reply.json()["operationId"] == operation_id
            and reply.json()["status"] == "unknown"
        )
        assert reply.json()["code"] == "LAB_OPERATION_RECORD_UNCERTAIN"
    assert bench.provider.calls.count("reserve") == 1
    assert bench.service.store.get("operation", operation_id)["status"] == "delegated"
