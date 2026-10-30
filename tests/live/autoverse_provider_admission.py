"""Explicit enrolled Autoverse targets; no reference workload substitutes.

Select this file explicitly with STUDIO_AUTOVERSE_TEST_INSTALLATION pointing to a
private receipt produced by read-only native enrollment. A missing environment is
a failed prerequisite, never a skipped or simulated live acceptance result.
"""

from copy import deepcopy
from contextlib import contextmanager
import json
import os
from pathlib import Path
import subprocess

from fastapi.testclient import TestClient
import pytest

from xverse_studio.api.app import create_app
from xverse_studio.providers.autoverse.adapter import AutoverseProvider
from xverse_studio.providers.autoverse.platform_adapter import PlatformProvider
from xverse_studio.providers.registry import admit_descriptor
from xverse_studio.storage.core import Problem


@pytest.fixture(params=["classic", "platform"])
def target(request):
    receipt = os.environ.get("STUDIO_AUTOVERSE_TEST_INSTALLATION")
    if not receipt:
        pytest.fail("An explicitly enrolled private Autoverse installation is required")
    installation = json.loads(Path(receipt).read_bytes())[request.param]
    provider = (AutoverseProvider if request.param == "classic" else PlatformProvider)(
        installation
    )
    return (
        provider,
        "autoverse-classic" if request.param == "classic" else "autoverse-platform",
    )


def corrupt(descriptor, case):
    d = deepcopy(descriptor)
    if case == "digest":
        d["implementationDigest"] = "sha256:invalid"
    elif case == "boolean-identity":
        d["providerId"] = True
    elif case == "version":
        d["contractVersion"] = "2.0"
    elif case == "null-capabilities":
        d["capabilityRecords"] = None
    elif case == "text-physical":
        d["capabilityRecords"][0]["physicalEffects"] = "false"
    elif case == "text-hosts":
        d["supportedHostOS"] = "Linux"
    elif case == "empty-hosts":
        d["supportedHostOS"] = []
    elif case == "text-architectures":
        d["architectures"] = "x86_64"
    elif case == "list-limits":
        d["limits"] = []
    elif case == "negative-limit":
        d["limits"]["maxDurationSeconds"] = -1
    elif case == "boolean-limit":
        d["limits"]["maxDurationSeconds"] = True
    elif case == "infinite-limit":
        d["limits"]["maxDurationSeconds"] = float("inf")
    elif case == "text-availability":
        d["available"] = "false"
    elif case == "text-host-compatible":
        d["hostCompatible"] = "false"
    elif case == "text-states":
        d["capabilityRecords"][0]["legalStates"] = "ready"
    elif case == "empty-authority":
        d["capabilityRecords"][0]["authorityRequirements"] = []
    elif case == "duplicate-capability":
        d["capabilityRecords"].append(deepcopy(d["capabilityRecords"][0]))
    elif case == "missing-operation":
        d["operations"].remove("start")
    elif case == "unscoped-operation":
        d["operations"].append("unscoped")
    elif case == "invalid-schema":
        d["capabilityRecords"][0]["parametersSchema"]["minProperties"] = "invalid"
    elif case == "schema-version":
        d["capabilityRecords"][0]["parametersSchema"]["$schema"] = (
            "https://example.invalid/future-schema"
        )
    elif case == "open-schema":
        d["capabilityRecords"][0]["parametersSchema"]["additionalProperties"] = True
    elif case == "non-json-extension":
        d["extension"] = object()
    elif case == "nonfinite-extension":
        d["extension"] = float("nan")
    elif case == "unencodable-extension":
        d["extension"] = "\ud800"
    elif case == "cycle":
        d["extension"] = d
    elif case == "oversize":
        d["extension"] = "x" * 65537
    elif case == "depth":
        d["extension"] = value = {}
        for _ in range(17):
            value["next"] = {}
            value = value["next"]
    elif case == "node-count":
        d["extension"] = [0] * 4097
    elif case == "credential":
        d["extension"] = "password=owned-private-marker"
    else:
        raise AssertionError("Unknown controlled descriptor fault")
    return d


CASES = [
    "digest",
    "boolean-identity",
    "version",
    "null-capabilities",
    "text-physical",
    "text-hosts",
    "empty-hosts",
    "text-architectures",
    "list-limits",
    "negative-limit",
    "boolean-limit",
    "infinite-limit",
    "text-availability",
    "text-host-compatible",
    "text-states",
    "empty-authority",
    "duplicate-capability",
    "missing-operation",
    "unscoped-operation",
    "invalid-schema",
    "schema-version",
    "open-schema",
    "non-json-extension",
    "nonfinite-extension",
    "unencodable-extension",
    "cycle",
    "oversize",
    "depth",
    "node-count",
    "credential",
]


@pytest.mark.parametrize("case", CASES)
def test_enrolled_autoverse_descriptors_reject_invalid_contracts_with_typed_problems(
    target, case
):
    provider, _ = target
    with pytest.raises(Problem) as error:
        admit_descriptor(corrupt(provider.descriptor(), case))
    assert error.value.code == (
        "PROVIDER_VERSION_INCOMPATIBLE"
        if case == "version"
        else "PROVIDER_DESCRIPTOR_INVALID"
    )
    assert "owned-private-marker" not in str(error.value)


def test_enrolled_autoverse_descriptors_preserve_exact_inert_extensions(target):
    provider, _ = target
    value = provider.descriptor()
    value["extension"] = {
        "note": "inert; no provider command",
        "unknown": [1, False, None],
    }
    original = deepcopy(value)
    observed = admit_descriptor(value)
    assert observed == original and value == original
    observed["extension"]["unknown"].append("separate observation")
    assert value == original


def test_autoverse_parameter_schema_references_are_inspected_without_remote_resolution(
    target, monkeypatch
):
    import socket

    provider, _ = target
    value = provider.descriptor()
    value["capabilityRecords"][0]["parametersSchema"]["properties"] = {
        "value": {"$ref": "https://never-contact.invalid/target"}
    }
    monkeypatch.setattr(socket, "create_connection", forbidden_contact)
    assert admit_descriptor(value) == value


@contextmanager
def authenticated(app):
    with TestClient(app) as api:
        api.headers["Origin"] = "http://testserver"
        login = api.post(
            "/api/v1/session", json={"bootstrapToken": "owned-autoverse-contract-check"}
        )
        assert login.status_code == 200, login.text
        api.headers["X-CSRF-Token"] = login.json()["csrfToken"]
        yield api


def forbidden_contact(*args, **kwargs):
    raise AssertionError(
        "Unverified Autoverse admission reached a provider or worker operation"
    )


def application(root, provider):
    pid = provider.descriptor()["providerId"]
    return create_app(
        root,
        allowed_hosts=["testserver"],
        bootstrap_token="owned-autoverse-contract-check",
        installed_providers={pid: provider},
    )


def project(api, blueprint):
    result = api.post(
        "/api/v1/projects",
        json={"name": "Actual Autoverse admission target", "blueprintRef": blueprint},
    )
    assert result.status_code == 201, result.text
    return result.json()


def preflight(api, p, provider_id):
    return api.post(
        f"/api/v1/projects/{p['projectId']}/preflights",
        json={"revision": p["revision"], "providerId": provider_id},
    )


@pytest.mark.parametrize(
    "case",
    [
        "digest",
        "null-capabilities",
        "text-physical",
        "text-hosts",
        "list-limits",
        "version",
    ],
)
def test_bad_enrolled_autoverse_description_keeps_authoring_but_never_calls_provider(
    target, tmp_path, monkeypatch, case
):
    provider, blueprint = target
    original = provider.descriptor()
    provider_id = original["providerId"]
    bad = corrupt(original, case)
    monkeypatch.setattr(provider, "descriptor", lambda: bad)
    monkeypatch.setattr(provider, "readiness", forbidden_contact)
    # Use the server-configured identity even if descriptor contents are invalid.
    app = create_app(
        tmp_path,
        allowed_hosts=["testserver"],
        bootstrap_token="owned-autoverse-contract-check",
        installed_providers={provider_id: provider},
    )
    with authenticated(app) as api:
        p = project(api, blueprint)
        listed = api.get("/api/v1/providers")
        assert listed.status_code == 200, listed.text
        unavailable = next(
            d for d in listed.json()["items"] if d["providerId"] == provider_id
        )
        assert unavailable["available"] is False and unavailable["operations"] == []
        assert unavailable["blockedReasons"][0]["code"] == (
            "PROVIDER_VERSION_INCOMPATIBLE"
            if case == "version"
            else "PROVIDER_DESCRIPTOR_INVALID"
        )
        result = preflight(api, p, provider_id)
        assert result.status_code == 200 and result.json()["status"] == "blocked", (
            result.text
        )
        assert result.json()["providerId"] == provider_id
        assert api.get("/api/v1/runs").json()["items"] == []


@pytest.mark.parametrize("failure", ["identity", "describe-error"])
def test_unverified_autoverse_registration_never_echoes_payload_or_exception(
    target, tmp_path, monkeypatch, failure
):
    provider, blueprint = target
    original = provider.descriptor()
    provider_id = original["providerId"]
    app = application(tmp_path, provider)

    def describe():
        if failure == "describe-error":
            raise RuntimeError("owned-private-marker: never expose native exceptions")
        return {
            **original,
            "providerId": "foreign-identity",
            "note": "owned-private-marker",
        }

    monkeypatch.setattr(provider, "descriptor", describe)
    monkeypatch.setattr(provider, "readiness", forbidden_contact)
    with authenticated(app) as api:
        p = project(api, blueprint)
        for route in ["/api/v1/providers", "/api/v1/capabilities"]:
            result = api.get(route)
            assert (
                result.status_code == 200 and "owned-private-marker" not in result.text
            ), result.text
        blocked = preflight(api, p, provider_id)
        assert blocked.status_code == 200 and blocked.json()["status"] == "blocked", (
            blocked.text
        )
        assert "owned-private-marker" not in blocked.text
        assert api.get("/api/v1/runs").json()["items"] == []


def test_autoverse_discovery_and_generated_contract_match_without_coercing_values(
    target, tmp_path
):
    provider, _ = target
    app = application(tmp_path, provider)
    with authenticated(app) as api:
        response = api.get("/api/v1/providers")
        assert response.status_code == 200, response.text
        actual = next(
            p
            for p in response.json()["items"]
            if p["providerId"] == provider.descriptor()["providerId"]
        )
        assert actual == provider.descriptor()
        generated = json.loads(
            Path(__file__)
            .resolve()
            .parents[2]
            .joinpath("packages/contracts/openapi.json")
            .read_bytes()
        )
        assert api.get("/api/v1/openapi.json").json() == generated
        assert "ProviderDescriptor" in generated["components"]["schemas"]


def test_autoverse_gate_validates_the_same_immutable_bytes_it_returns(
    target, monkeypatch
):
    from xverse_studio.providers import descriptors as module

    provider, _ = target
    original = provider.descriptor()
    value = corrupt(original, "digest")
    capture = module.bounded_json

    def changed_after_capture(item):
        raw = capture(item)
        item["implementationDigest"] = original["implementationDigest"]
        return raw

    monkeypatch.setattr(module, "bounded_json", changed_after_capture)
    with pytest.raises(Problem) as error:
        admit_descriptor(value)
    assert error.value.code == "PROVIDER_DESCRIPTOR_INVALID"


@pytest.mark.parametrize(
    "name,value",
    [("maxDurationSeconds", 0), ("maxConcurrentRuns", 0), ("maxConcurrentRuns", 1.5)],
)
def test_autoverse_execution_bounds_are_positive_and_concurrency_is_integral(
    target, name, value
):
    provider, _ = target
    descriptor = provider.descriptor()
    descriptor["limits"][name] = value
    with pytest.raises(Problem) as error:
        admit_descriptor(descriptor)
    assert error.value.code == "PROVIDER_DESCRIPTOR_INVALID"


def test_autoverse_authoring_negotiates_versions_and_closed_requests_before_allocation(
    target, tmp_path
):
    provider, blueprint = target
    app = application(tmp_path, provider)
    with authenticated(app) as api:
        request = {"name": "Unallocated Autoverse target", "blueprintRef": blueprint}
        version = api.post(
            "/api/v1/projects",
            headers={"X-Studio-Contract-Version": "2.0"},
            json=request,
        )
        assert (
            version.status_code == 426
            and version.json()["code"] == "API_VERSION_INCOMPATIBLE"
        )
        unknown = api.post(
            "/api/v1/projects", json={**request, "unknown": "owned-private-marker"}
        )
        assert unknown.status_code == 422 and "owned-private-marker" not in unknown.text
        assert {"code", "message", "requestId", "retryable"} <= set(unknown.json())
        assert api.get("/api/v2/providers").status_code == 404
        assert api.get("/api/v1/projects").json()["items"] == []


@pytest.mark.parametrize("condition", ["unavailable", "host", "architecture"])
def test_incompatible_enrolled_autoverse_host_is_blocked_before_readiness_contact(
    target, tmp_path, monkeypatch, condition
):
    provider, blueprint = target
    descriptor = provider.descriptor()
    if condition == "unavailable":
        descriptor["available"] = False
    elif condition == "host":
        descriptor["supportedHostOS"] = ["unavailable-os"]
    else:
        descriptor["architectures"] = ["unavailable-architecture"]
    monkeypatch.setattr(provider, "descriptor", lambda: descriptor)
    app = application(tmp_path, provider)
    monkeypatch.setattr(provider, "readiness", forbidden_contact)
    with authenticated(app) as api:
        p = project(api, blueprint)
        result = preflight(api, p, descriptor["providerId"])
        assert result.status_code == 200 and result.json()["status"] == "blocked", (
            result.text
        )
        assert api.get("/api/v1/runs").json()["items"] == []


@pytest.mark.parametrize("target", ["classic"], indirect=True)
def test_changed_autoverse_description_invalidates_ready_snapshot_before_any_new_run(
    target, tmp_path, monkeypatch
):
    provider, blueprint = target
    descriptor = provider.descriptor()
    app = application(tmp_path, provider)
    with authenticated(app) as api:
        p = project(api, blueprint)
        ready = preflight(api, p, descriptor["providerId"])
        assert ready.status_code == 200 and ready.json()["status"] == "ready", (
            ready.text
        )
        monkeypatch.setattr(
            provider, "descriptor", lambda: corrupt(descriptor, "digest")
        )
        monkeypatch.setattr(subprocess, "Popen", forbidden_contact)
        start = api.post(
            "/api/v1/runs",
            headers={"Idempotency-Key": "changed-autoverse-descriptor"},
            json={k: ready.json()[k] for k in ("snapshotId", "preflightId")},
        )
        assert start.status_code == 409 and start.json()["code"] == "PREFLIGHT_STALE", (
            start.text
        )
        assert api.get("/api/v1/runs").json()["items"] == []
        assert app.state.studio.store.all("operation") == []


@pytest.mark.parametrize("target", ["classic"], indirect=True)
def test_post_accept_autoverse_descriptor_change_refuses_dispatch_before_acquisition(
    target, tmp_path, monkeypatch
):
    provider, blueprint = target
    descriptor = provider.descriptor()
    app = application(tmp_path, provider)
    with authenticated(app) as api:
        p = project(api, blueprint)
        ready = preflight(api, p, descriptor["providerId"])
        assert ready.status_code == 200 and ready.json()["status"] == "ready", (
            ready.text
        )
        runs = app.state.studio.runs
        dispatch = runs._dispatch

        def changed(rid):
            monkeypatch.setattr(
                provider, "descriptor", lambda: corrupt(descriptor, "digest")
            )
            monkeypatch.setattr(subprocess, "Popen", forbidden_contact)
            dispatch(rid)

        monkeypatch.setattr(runs, "_dispatch", changed)
        if hasattr(provider, "prepare_backend_task"):
            monkeypatch.setattr(provider, "prepare_backend_task", forbidden_contact)
        start = api.post(
            "/api/v1/runs",
            headers={"Idempotency-Key": "post-accept-autoverse-change"},
            json={k: ready.json()[k] for k in ("snapshotId", "preflightId")},
        )
        assert start.status_code == 202, start.text
        current = api.get("/api/v1/runs/" + start.json()["runId"])
        assert current.status_code == 200, current.text
        assert (
            current.json()["state"] == "failed"
            and current.json()["cleanup"] == "complete"
        )
        assert current.json()["reason"] == "PROVIDER_ADMISSION_CHANGED"
        assert not (runs.directory(start.json()["runId"]) / "owner.key").exists()
