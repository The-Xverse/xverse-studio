"""Linux HTTP boundary with owned inert callbacks; no equipment or model execution."""

from copy import deepcopy

from fastapi.testclient import TestClient
import pytest

from test_lab_probe_http import OwnedProbe, configured, login, request


OVERSIZED = pytest.mark.parametrize(
    "value", [10**400, -(10**400)], ids=["positive-overflow", "negative-overflow"]
)


@pytest.fixture
def bench(tmp_path):
    owned = configured(tmp_path / "Owned clock contract Ω")
    with TestClient(
        owned.app, base_url="http://testserver", raise_server_exceptions=False
    ) as client:
        login(client)
        owned.client = client
        yield owned


def assert_inert(bench):
    discovery = bench.client.get("/api/v1/capabilities").json()["labProbes"]
    assert discovery["runtimeAdmission"] == "unavailable"
    assert discovery["physicalCommands"] == []
    assert bench.app.state.studio.lab.records == {}
    assert bench.client.get("/api/v1/runs").json()["items"] == []


@OVERSIZED
@pytest.mark.parametrize("route", ["options", "request"])
def test_oversized_backend_clock_refuses_before_receipt_or_provider_contact(
    bench, value, route
):
    bench.now[0] = value
    with bench.service.store.tx() as db:
        before = db.execute(
            "SELECT scope,key,fingerprint,result FROM idempotency"
        ).fetchall()
    response = (
        bench.client.get("/api/v1/assets/fixture-asset/probe-options")
        if route == "options"
        else request(bench)
    )
    assert response.status_code == 422, response.text
    assert response.json()["code"] == "PROBE_CLOCK_UNAVAILABLE"
    assert bench.provider.calls == []
    assert bench.service.store.find("operation", "kind", "lab_probe") == []
    with bench.service.store.tx() as db:
        assert (
            db.execute(
                "SELECT scope,key,fingerprint,result FROM idempotency"
            ).fetchall()
            == before
        )
    assert_inert(bench)


@OVERSIZED
@pytest.mark.parametrize(
    "field", ["createdAt", "deadline", "receivedAt", "uncertaintySeconds"]
)
def test_oversized_stored_clock_remains_typed_unavailable_without_redelegation(
    bench, value, field
):
    operation = request(bench).json()
    record = bench.service.store.get("operation", operation["operationId"])
    if field in {"createdAt", "deadline"}:
        record[field] = value
    elif field == "receivedAt":
        record["result"][field] = value
    else:
        record["result"]["sourceTime"][field] = value
    bench.service.store.put("operation", record["operationId"], record)
    original = deepcopy(record)
    response = bench.client.get("/api/v1/operations/" + record["operationId"])
    assert response.status_code == 422, response.text
    assert response.json()["code"] == "PROBE_STATE_UNAVAILABLE"
    retry = request(bench)
    assert (
        retry.status_code == 422 and retry.json()["code"] == "PROBE_STATE_UNAVAILABLE"
    )
    assert len(bench.provider.calls) == 1
    assert bench.service.store.get("operation", record["operationId"]) == original
    assert_inert(bench)


@OVERSIZED
def test_oversized_provider_uncertainty_is_invalid_response_not_unknown_io(
    bench, value
):
    def malformed(binding):
        response = OwnedProbe.result(binding)
        response["sourceTime"]["uncertaintySeconds"] = value
        return response

    bench.provider.callback = malformed
    response = request(bench)
    assert response.status_code == 202
    operation = response.json()
    assert operation["status"] == "unknown" and operation["result"] is None
    assert operation["code"] == "PROBE_RESPONSE_INVALID"
    assert request(bench).json() == operation
    assert (
        bench.client.get("/api/v1/operations/" + operation["operationId"]).json()
        == operation
    )
    assert len(bench.provider.calls) == 1
    assert_inert(bench)


@OVERSIZED
@pytest.mark.parametrize("phase", ["before-provider", "after-provider"])
def test_clock_failure_during_delegation_retains_explicit_diagnostic(
    bench, value, phase, monkeypatch
):
    if phase == "before-provider":
        call = bench.service._call

        def invalid_before_guard(record, item, generation):
            bench.now[0] = value
            return call(record, item, generation)

        monkeypatch.setattr(bench.service, "_call", invalid_before_guard)
    else:

        def invalid_after_observation(binding):
            bench.now[0] = value
            return OwnedProbe.result(binding)

        bench.provider.callback = invalid_after_observation
    response = request(bench)
    assert response.status_code == 202
    operation = response.json()
    assert operation["status"] == "unknown" and operation["result"] is None
    assert operation["code"] == "PROBE_CLOCK_UNAVAILABLE"
    assert len(bench.provider.calls) == (0 if phase == "before-provider" else 1)
    assert request(bench).json() == operation
    assert (
        bench.client.get("/api/v1/operations/" + operation["operationId"]).json()
        == operation
    )
    assert len(bench.provider.calls) == (0 if phase == "before-provider" else 1)
    assert_inert(bench)
