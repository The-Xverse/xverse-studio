"""Read-only readiness facts and admission across every owned execution route."""

from copy import deepcopy
import subprocess

import pytest


def new_project(client):
    response = client.post("/api/v1/projects", json={"name": "Readiness facts"})
    assert response.status_code == 201, response.text
    return response.json()


def test_preflight_preserves_selected_unavailable_provider_without_reference_substitution(
    client, monkeypatch
):
    monkeypatch.setattr(
        subprocess,
        "Popen",
        lambda *a, **k: pytest.fail("Read-only preflight must not dispatch"),
    )
    project = new_project(client)
    response = client.post(
        f"/api/v1/projects/{project['projectId']}/preflights",
        json={"revision": 1, "providerId": "xverse.lite"},
    )
    assert response.status_code == 200, response.text
    result = response.json()
    assert result["status"] == "blocked"
    assert result["providerId"] == "xverse.lite"
    assert result["providerIdentity"]["providerId"] == "xverse.lite"
    assert result["limits"] == {}
    snapshot = client.app.state.studio.store.get("snapshot", result["snapshotId"])
    assert snapshot["providerId"] == "xverse.lite"
    assert snapshot["configuration"] is None
    assert client.get("/api/v1/runs").json()["items"] == []


@pytest.mark.parametrize("route", ["/api/v1/campaigns/preview", "/api/v1/campaigns"])
def test_unavailable_provider_snapshot_cannot_be_promoted_by_campaign_route(
    client, monkeypatch, route
):
    monkeypatch.setattr(
        subprocess,
        "Popen",
        lambda *a, **k: pytest.fail("Unavailable provider must not dispatch"),
    )
    project = new_project(client)
    pf = client.post(
        f"/api/v1/projects/{project['projectId']}/preflights",
        json={"revision": 1, "providerId": "xverse.lite"},
    ).json()
    assert pf["status"] == "blocked"
    response = client.post(
        route,
        headers={"Idempotency-Key": "not-a-reference-campaign"},
        json={
            "snapshotId": pf["snapshotId"],
            "matrix": {"gain": [0.8]},
            "budget": {"maxRuns": 1, "maxTotalSeconds": 5},
            "concurrency": 1,
        },
    )
    assert response.status_code == 422, response.text
    assert response.json()["code"] == "ADMISSION_REJECTED"
    assert client.app.state.studio.store.all("campaign") == []
    assert client.get("/api/v1/runs").json()["items"] == []


def test_ready_preflight_advertises_independent_facts_and_exact_frozen_plan(client):
    project = new_project(client)
    response = client.post(
        f"/api/v1/projects/{project['projectId']}/preflights", json={"revision": 1}
    )
    assert response.status_code == 200, response.text
    result = response.json()
    assert result["status"] == "ready", result
    expected = {
        "backend",
        "provider",
        "model",
        "artifacts",
        "capabilities",
        "target",
        "resources",
        "ownership",
        "clocks",
        "authority",
    }
    assert set(result["readiness"]) == expected
    assert result["readiness"]["model"]["status"] == "valid"
    assert all(
        row["message"] and isinstance(row["elementRefs"], list)
        for row in result["readiness"].values()
    )
    assert "liveness" not in result["readiness"]
    snapshot = client.app.state.studio.store.get("snapshot", result["snapshotId"])
    preview = result["planPreview"]
    assert preview["plan"] == snapshot["plan"]
    assert (
        preview["snapshotDigest"]
        == snapshot["snapshotDigest"]
        == result["snapshotDigest"]
    )
    assert preview["planDigest"] == result["planDigest"]
    assert preview["revision"] == result["revision"] == 1
    assert preview["selection"] == snapshot["selection"]


def test_unknown_limits_block_admission_without_inventing_reference_defaults(
    client, monkeypatch
):
    from xverse_studio.runs import service

    descriptors = service.descriptors

    def incomplete():
        rows = deepcopy(descriptors())
        next(row for row in rows if row["providerId"] == "studio.reference")[
            "limits"
        ].pop("maxDurationSeconds")
        return rows

    monkeypatch.setattr(service, "descriptors", incomplete)
    project = new_project(client)
    result = client.post(
        f"/api/v1/projects/{project['projectId']}/preflights", json={"revision": 1}
    ).json()
    assert result["status"] == "blocked", result
    assert result["readiness"]["resources"]["status"] == "unknown"
    assert any(d["code"] == "LIMITS_UNKNOWN" for d in result["diagnostics"])
    assert "maxDurationSeconds" not in result["limits"]


@pytest.mark.parametrize(
    "mutation,dimension", [("clock", "clocks"), ("artifact", "artifacts")]
)
def test_valid_but_unsupported_inputs_do_not_claim_clock_or_artifact_availability(
    client, mutation, dimension
):
    from io import StringIO
    from ruamel.yaml import YAML

    project = new_project(client)
    parser = YAML()
    for docid, document in project["documents"].items():
        resource = parser.load(document["content"])
        if mutation == "clock" and resource["kind"] == "System":
            resource["spec"]["timeDomains"][0]["rate"] = "2"
        elif (
            mutation == "artifact"
            and resource["kind"] == "Component"
            and resource["spec"].get("models")
        ):
            resource["spec"]["models"][0]["externalRef"] = (
                "urn:example:unavailable-model"
            )
        else:
            continue
        stream = StringIO()
        parser.dump(resource, stream)
        saved = client.put(
            f"/api/v1/projects/{project['projectId']}/documents/{docid}",
            headers={"If-Match": "1"},
            json={"content": stream.getvalue(), "format": "yaml"},
        )
        assert saved.status_code == 200, saved.text
        project = saved.json()
        break
    pf = client.post(
        f"/api/v1/projects/{project['projectId']}/preflights",
        json={"revision": project["revision"]},
    ).json()
    assert pf["readiness"]["model"]["status"] == "valid", pf
    assert pf["status"] == "blocked"
    assert pf["readiness"][dimension]["status"] in {
        "unknown",
        "unsupported",
        "unavailable",
    }


def test_legacy_blocked_snapshot_with_reference_configuration_cannot_create_campaign(
    client,
):
    project = new_project(client)
    pf = client.post(
        f"/api/v1/projects/{project['projectId']}/preflights", json={"revision": 1}
    ).json()
    store = client.app.state.studio.store
    historical = store.get("preflight", pf["preflightId"])
    historical["status"] = "blocked"
    store.put("preflight", pf["preflightId"], historical)
    response = client.post(
        "/api/v1/campaigns",
        headers={"Idempotency-Key": "legacy-blocked"},
        json={
            "snapshotId": pf["snapshotId"],
            "matrix": {"gain": [0.8]},
            "budget": {"maxRuns": 1, "maxTotalSeconds": 5},
        },
    )
    assert response.status_code == 422, response.text
    assert response.json()["code"] == "ADMISSION_REJECTED"
    assert store.all("campaign") == []


def test_campaign_retry_identity_precedes_mutable_snapshot_admission(client):
    client.app.state.studio.campaign_tick = lambda: None
    project = new_project(client)
    pf = client.post(
        f"/api/v1/projects/{project['projectId']}/preflights", json={"revision": 1}
    ).json()
    payload = {
        "snapshotId": pf["snapshotId"],
        "matrix": {"gain": [0.8]},
        "budget": {"maxRuns": 1, "maxTotalSeconds": 5},
    }
    headers = {"Idempotency-Key": "same-campaign-intent"}
    original = client.post("/api/v1/campaigns", headers=headers, json=payload)
    assert original.status_code == 202, original.text
    store = client.app.state.studio.store
    file = store.root / "snapshots" / pf["snapshotId"] / "snapshot.json"
    moved = file.with_suffix(".held")
    file.rename(moved)
    try:
        retry = client.post("/api/v1/campaigns", headers=headers, json=payload)
        assert retry.status_code == 202 and retry.json() == original.json(), retry.text
        conflict = client.post(
            "/api/v1/campaigns",
            headers=headers,
            json={**payload, "matrix": {"gain": [1.2]}},
        )
        assert (
            conflict.status_code == 409
            and conflict.json()["code"] == "IDEMPOTENCY_CONFLICT"
        ), conflict.text
        new = client.post(
            "/api/v1/campaigns",
            headers={"Idempotency-Key": "new-campaign-intent"},
            json=payload,
        )
        assert new.status_code == 422 and new.json()["code"] == "SNAPSHOT_INTEGRITY", (
            new.text
        )
        assert len(store.all("campaign")) == 1
        assert store.all("run") == []
    finally:
        moved.rename(file)


@pytest.mark.parametrize(
    "case",
    [
        "start_target",
        "xdl_version",
        "availability",
        "host_fact",
        "host_os",
        "host_arch",
    ],
)
def test_unknown_or_incompatible_provider_facts_never_admit_execution(
    client, monkeypatch, case
):
    from xverse_studio.runs import service

    descriptors = service.descriptors
    rows = deepcopy(descriptors())
    provider = next(row for row in rows if row["providerId"] == "studio.reference")
    if case == "start_target":
        next(c for c in provider["capabilityRecords"] if c["kind"] == "start")[
            "targetClass"
        ] = "unadmitted-target"
    elif case == "xdl_version":
        provider["supportedXdlVersions"] = ["xverse.io/xdl/unsupported"]
    elif case == "availability":
        provider["available"] = "unknown"
    elif case == "host_fact":
        provider["hostCompatible"] = "unknown"
    elif case == "host_os":
        provider["supportedHostOS"] = ["unavailable-os"]
    else:
        provider["architectures"] = ["unavailable-architecture"]
    monkeypatch.setattr(service, "descriptors", lambda: rows)
    monkeypatch.setattr(
        subprocess, "Popen", lambda *a, **k: pytest.fail("No process may dispatch")
    )
    project = new_project(client)
    result = client.post(
        f"/api/v1/projects/{project['projectId']}/preflights", json={"revision": 1}
    ).json()
    assert result["status"] == "blocked", result
    snapshot = client.app.state.studio.store.get("snapshot", result["snapshotId"])
    assert snapshot["configuration"] is None
    assert client.app.state.studio.store.all("run") == []


@pytest.mark.parametrize(
    "change,code,status",
    [
        ("expiry", "PREFLIGHT_STALE", 409),
        ("provider", "PREFLIGHT_STALE", 409),
        ("resources", "RESOURCE_BUSY", 409),
        ("canonical_snapshot", "SNAPSHOT_INTEGRITY", 422),
    ],
)
def test_start_rechecks_admission_before_any_dispatch(
    client, monkeypatch, change, code, status
):
    from xverse_studio.runs import service

    project = new_project(client)
    pf = client.post(
        f"/api/v1/projects/{project['projectId']}/preflights", json={"revision": 1}
    ).json()
    assert pf["status"] == "ready"
    store = client.app.state.studio.store
    if change == "expiry":
        pf["expiresAt"] = 0
        store.put("preflight", pf["preflightId"], pf)
    elif change == "provider":
        rows = deepcopy(service.descriptors())
        next(r for r in rows if r["providerId"] == "studio.reference")[
            "providerVersion"
        ] = "changed"
        monkeypatch.setattr(service, "descriptors", lambda: rows)
    elif change == "resources":
        # Fake metadata occupies capacity; this is a failure fixture, not runtime evidence.
        # Keep this admission-only fixture out of runtime reconciliation: there are
        # no corresponding owned processes or operations to inspect.
        monkeypatch.setattr(
            client.app.state.studio.runs, "read", lambda rid: store.get("run", rid)
        )
        for index in range(4):
            store.put(
                "run",
                f"occupied-{index}",
                {"runId": f"occupied-{index}", "state": "running"},
            )
    else:
        (store.root / "snapshots" / pf["snapshotId"] / "snapshot.json").write_bytes(
            b"{}"
        )
    monkeypatch.setattr(
        subprocess,
        "Popen",
        lambda *a, **k: pytest.fail("No dispatch after changed admission"),
    )
    before = store.all("run")
    response = client.post(
        "/api/v1/runs",
        headers={"Idempotency-Key": "changed-admission"},
        json={"preflightId": pf["preflightId"], "snapshotId": pf["snapshotId"]},
    )
    assert response.status_code == status and response.json()["code"] == code, (
        response.text
    )
    assert store.all("run") == before
    if change == "resources":
        # Retire synthetic rows before monkeypatch teardown restores real reconciliation.
        with store.tx() as db:
            for index in range(4):
                db.execute(
                    "DELETE FROM records WHERE kind=? AND id=?",
                    ("run", f"occupied-{index}"),
                )


def _admission_save_resource(client, project, kind, change):
    from io import StringIO
    from ruamel.yaml import YAML

    parser = YAML()
    document_id, document = next(
        (key, value)
        for key, value in project["documents"].items()
        if parser.load(value["content"])["kind"] == kind
    )
    resource = parser.load(document["content"])
    change(resource)
    output = StringIO()
    parser.dump(resource, output)
    response = client.put(
        f"/api/v1/projects/{project['projectId']}/documents/{document_id}",
        headers={"If-Match": str(project["revision"])},
        json={"content": output.getvalue(), "format": "yaml"},
    )
    assert response.status_code == 200, response.text
    return response.json()


def _admission_assert_publicly_valid(client, project):
    for operation in ("validations", "compilations"):
        response = client.post(
            f"/api/v1/projects/{project['projectId']}/{operation}",
            json={"revision": project["revision"]},
        )
        assert response.status_code == 200, response.text
        assert response.json()["valid"] is True, response.text


def _admission_check(client, project):
    response = client.post(
        f"/api/v1/projects/{project['projectId']}/preflights",
        json={"revision": project["revision"]},
    )
    assert response.status_code == 200, response.text
    return response.json()


def _admission_refuses_start(client, preflight, key):
    store = client.app.state.studio.store
    before_runs, before_operations = store.all("run"), store.all("operation")
    response = client.post(
        "/api/v1/runs",
        headers={"Idempotency-Key": key},
        json={
            "snapshotId": preflight["snapshotId"],
            "preflightId": preflight["preflightId"],
        },
    )
    assert response.status_code == 422, response.text
    assert response.json()["code"] == "ADMISSION_REJECTED", response.text
    assert store.all("run") == before_runs
    assert store.all("operation") == before_operations


@pytest.mark.parametrize("limit,value", [("maxDurationSeconds", 4), ("maxSamples", 1)])
def test_exceeded_advertised_duration_and_sample_budgets_block_valid_inputs(
    client, monkeypatch, limit, value
):
    from xverse_studio.runs import service
    from xverse_studio.storage.core import digest

    project = new_project(client)
    _admission_assert_publicly_valid(client, project)
    source_before = digest(client.app.state.studio.projects.sources(project))
    rows = deepcopy(service.descriptors())
    provider = next(row for row in rows if row["providerId"] == "studio.reference")
    provider["limits"][limit] = value
    monkeypatch.setattr(service, "descriptors", lambda: rows)
    monkeypatch.setattr(
        subprocess,
        "Popen",
        lambda *args, **kwargs: pytest.fail("No budget overrun may dispatch"),
    )
    preflight = _admission_check(client, project)
    parameters = {
        item["id"]: item["value"]
        for item in preflight["planPreview"]["plan"]["parameters"]
    }
    required = (
        parameters["duration"]
        if limit == "maxDurationSeconds"
        else parameters["duration"] / parameters["timestep"]
    )
    assert required > preflight["limits"][limit] == value
    assert preflight["status"] == "blocked", preflight
    assert preflight["readiness"]["model"]["status"] == "valid"
    assert preflight["readiness"]["capabilities"]["status"] == "compatible"
    assert preflight["readiness"]["resources"]["status"] == "blocked"
    assert "LIMIT_EXCEEDED" in preflight["readiness"]["resources"]["diagnosticCodes"]
    assert (
        client.app.state.studio.store.get("snapshot", preflight["snapshotId"])[
            "configuration"
        ]
        is None
    )
    _admission_refuses_start(client, preflight, "exceeded-advertised-" + limit)
    reopened = client.get(f"/api/v1/projects/{project['projectId']}")
    assert reopened.status_code == 200, reopened.text
    assert (
        digest(client.app.state.studio.projects.sources(reopened.json()))
        == source_before
    )


def test_required_clock_admission_absence_blocks_publicly_valid_inputs(
    client, monkeypatch
):
    from xverse_studio.runs import service

    project = new_project(client)
    _admission_assert_publicly_valid(client, project)
    rows = deepcopy(service.descriptors())
    next(row for row in rows if row["providerId"] == "studio.reference")[
        "clockDomains"
    ] = []
    monkeypatch.setattr(service, "descriptors", lambda: rows)
    monkeypatch.setattr(
        subprocess,
        "Popen",
        lambda *args, **kwargs: pytest.fail("No unadmitted clock may dispatch"),
    )
    preflight = _admission_check(client, project)
    assert preflight["status"] == "blocked", preflight
    assert preflight["readiness"]["model"]["status"] == "valid"
    assert preflight["readiness"]["capabilities"]["status"] == "compatible"
    assert preflight["readiness"]["clocks"]["status"] == "unknown"
    assert preflight["readiness"]["clocks"]["facts"]["domains"] == ["simulation-time"]
    assert (
        "CLOCK_MAPPING_UNAVAILABLE"
        in preflight["readiness"]["clocks"]["diagnosticCodes"]
    )
    assert (
        client.app.state.studio.store.get("snapshot", preflight["snapshotId"])[
            "configuration"
        ]
        is None
    )
    _admission_refuses_start(client, preflight, "missing-clock-admission")


@pytest.mark.parametrize("phase", ["preflight", "before_start"])
def test_conflicting_authority_scope_blocks_before_dispatch(client, monkeypatch, phase):
    from xverse_studio.runs import service

    project = new_project(client)
    _admission_assert_publicly_valid(client, project)
    original = _admission_check(client, project)
    assert original["status"] == "ready"
    rows = deepcopy(service.descriptors())
    provider = next(row for row in rows if row["providerId"] == "studio.reference")
    capability = next(
        row for row in provider["capabilityRecords"] if row["kind"] == "start"
    )
    # An administrative failure fixture, not a physical permit or observed asset owner.
    capability["authorityRequirements"] = [
        "native-backend-owned",
        "reserved-by-another-owner",
    ]
    monkeypatch.setattr(service, "descriptors", lambda: rows)
    monkeypatch.setattr(
        subprocess,
        "Popen",
        lambda *args, **kwargs: pytest.fail("Conflicting authority must not dispatch"),
    )
    store = client.app.state.studio.store
    if phase == "preflight":
        blocked = _admission_check(client, project)
        assert blocked["status"] == "blocked", blocked
        assert blocked["readiness"]["model"]["status"] == "valid"
        assert blocked["readiness"]["authority"]["status"] == "unknown"
        assert (
            "AUTHORITY_UNAVAILABLE"
            in blocked["readiness"]["authority"]["diagnosticCodes"]
        )
        assert store.get("snapshot", blocked["snapshotId"])["configuration"] is None
        _admission_refuses_start(client, blocked, "conflicting-authority-preflight")
    else:
        response = client.post(
            "/api/v1/runs",
            headers={"Idempotency-Key": "authority-changed-after-preflight"},
            json={
                "snapshotId": original["snapshotId"],
                "preflightId": original["preflightId"],
            },
        )
        assert (
            response.status_code == 409 and response.json()["code"] == "PREFLIGHT_STALE"
        ), response.text
        assert store.all("run") == [] and store.all("operation") == []


@pytest.mark.parametrize(
    "change", ["one_binding_missing", "all_bindings_missing", "digest_mismatch"]
)
def test_missing_binding_or_mismatched_artifact_is_distinct_from_model_uri(
    client, monkeypatch, change
):
    from ruamel.yaml import YAML

    parser = YAML()
    project = new_project(client)
    component_sources = {
        key: value["content"]
        for key, value in project["documents"].items()
        if parser.load(value["content"])["kind"] == "Component"
    }

    def mutate(resource):
        if change == "one_binding_missing":
            resource["spec"]["bindings"][0]["artifactIds"] = []
        elif change == "all_bindings_missing":
            for binding in resource["spec"]["bindings"]:
                binding["artifactIds"] = []
        else:
            resource["spec"]["artifacts"][0]["digest"] = "sha256:" + "0" * 64

    project = _admission_save_resource(client, project, "Deployment", mutate)
    assert component_sources == {
        key: project["documents"][key]["content"] for key in component_sources
    }
    _admission_assert_publicly_valid(client, project)
    monkeypatch.setattr(
        subprocess,
        "Popen",
        lambda *args, **kwargs: pytest.fail(
            "Missing or mismatched artifacts must not dispatch"
        ),
    )
    preflight = _admission_check(client, project)
    assert preflight["readiness"]["model"]["status"] == "valid"
    assert preflight["status"] == "blocked", preflight
    if change == "one_binding_missing":
        counts = [
            len(binding.get("artifactRefs", []))
            for binding in preflight["planPreview"]["plan"]["bindings"]
        ]
        assert sorted(counts) == [0, 1]
    assert preflight["readiness"]["artifacts"]["status"] in {
        "unknown",
        "unavailable",
        "unsupported",
    }, preflight
    assert (
        "ARTIFACT_UNAVAILABLE" in preflight["readiness"]["artifacts"]["diagnosticCodes"]
    )
    assert (
        client.app.state.studio.store.get("snapshot", preflight["snapshotId"])[
            "configuration"
        ]
        is None
    )
    _admission_refuses_start(client, preflight, "artifact-admission-" + change)


def test_removed_required_cross_clock_mapping_is_publicly_rejected_before_start(
    client, monkeypatch
):
    project = new_project(client)
    project = _admission_save_resource(
        client,
        project,
        "System",
        lambda resource: resource["spec"]["timeDomains"].append(
            {
                "id": "other-time",
                "clockClass": "simulation",
                "epoch": "0",
                "rate": "1",
                "monotonic": True,
            }
        ),
    )

    def add_mapping(resource):
        resource["spec"]["observers"][0]["timeDomainId"] = "other-time"
        resource["spec"]["timeMappings"] = [
            {
                "sourceTimeDomainId": "simulation-time",
                "targetTimeDomainId": "other-time",
                "mapping": "declared-fixture-identity",
                "tolerance": {"value": 0, "unit": "s"},
            }
        ]

    project = _admission_save_resource(client, project, "Scenario", add_mapping)
    _admission_assert_publicly_valid(client, project)
    project = _admission_save_resource(
        client,
        project,
        "Scenario",
        lambda resource: resource["spec"].pop("timeMappings"),
    )
    # This is intentionally a public semantic-validation failure. It is not
    # claimed as valid-model runtime mapping admission or a mapping implementation.
    public = client.post(
        f"/api/v1/projects/{project['projectId']}/validations",
        json={"revision": project["revision"]},
    )
    assert public.status_code == 200 and public.json()["valid"] is False, public.text
    assert any(
        row["code"] == "XDL-SEMANTIC-TIME-MAPPING"
        for row in public.json()["diagnostics"]
    )
    monkeypatch.setattr(
        subprocess,
        "Popen",
        lambda *args, **kwargs: pytest.fail(
            "Missing required clock mapping must not dispatch"
        ),
    )
    preflight = _admission_check(client, project)
    assert (
        preflight["status"] == "blocked"
        and preflight["readiness"]["model"]["status"] == "invalid"
    ), preflight
    assert any(
        row["code"] == "XDL-SEMANTIC-TIME-MAPPING" for row in preflight["diagnostics"]
    )
    _admission_refuses_start(client, preflight, "absent-required-clock-mapping")


def test_unknown_execution_owner_keeps_capacity_reserved_before_start(
    client, monkeypatch
):
    from xverse_studio.runs import service

    project = new_project(client)
    _admission_assert_publicly_valid(client, project)
    rows = deepcopy(service.descriptors())
    next(row for row in rows if row["providerId"] == "studio.reference")["limits"][
        "maxConcurrentRuns"
    ] = 1
    monkeypatch.setattr(service, "descriptors", lambda: rows)
    monkeypatch.setattr(
        subprocess,
        "Popen",
        lambda *args, **kwargs: pytest.fail(
            "An unknown owner must not lose its reserved capacity"
        ),
    )
    ready = _admission_check(client, project)
    assert ready["status"] == "ready"
    store = client.app.state.studio.store
    # Explicit ownership-uncertainty metadata fixture: no provider process exists,
    # no physical asset is reserved, and no live-provider result is claimed.
    store.put(
        "operation",
        "fixture-owner-op",
        {"operationId": "fixture-owner-op", "kind": "start", "status": "unknown"},
    )
    store.put(
        "run",
        "fixture-owner-run",
        {
            "runId": "fixture-owner-run",
            "operationId": "fixture-owner-op",
            "snapshotId": ready["snapshotId"],
            "projectId": project["projectId"],
            "state": "unknown",
            "stateVersion": 1,
            "cleanup": "unknown",
            "evidence": "partial",
            "evaluation": "not_started",
            "verdict": None,
            "createdAt": 0,
            "evidenceScope": "synthetic_ownership_failure_fixture",
            "providerId": "studio.reference",
        },
    )
    try:
        blocked = _admission_check(client, project)
        assert blocked["status"] == "blocked", blocked
        assert blocked["readiness"]["model"]["status"] == "valid"
        assert "RESOURCE_BUSY" in blocked["readiness"]["resources"]["diagnosticCodes"]
        response = client.post(
            "/api/v1/runs",
            headers={"Idempotency-Key": "unknown-owner-capacity"},
            json={
                "snapshotId": ready["snapshotId"],
                "preflightId": ready["preflightId"],
            },
        )
        assert (
            response.status_code == 409 and response.json()["code"] == "RESOURCE_BUSY"
        ), response.text
        assert store.get("run", "fixture-owner-run")["state"] == "unknown"
        assert len(store.all("run")) == 1
        assert store.get("operation", "fixture-owner-op")["status"] == "unknown"
    finally:
        with store.tx() as db:
            db.execute(
                "DELETE FROM records WHERE kind=? AND id=?",
                ("run", "fixture-owner-run"),
            )
            db.execute(
                "DELETE FROM records WHERE kind=? AND id=?",
                ("operation", "fixture-owner-op"),
            )


def test_unsupported_parameter_unit_cannot_be_silently_converted_or_run_as_preset(
    client, monkeypatch
):
    from xverse_studio.xdl.examples import PROFILE_NAMESPACE

    project = new_project(client)

    def change_unit(resource):
        parameter = next(
            row
            for row in resource["extensions"][PROFILE_NAMESPACE]["parameters"]
            if row["id"] == "duration"
        )
        parameter["unitSemantics"] = "ms"

    project = _admission_save_resource(client, project, "Scenario", change_unit)
    # The public declared-intent contract admits a unit string; the selected
    # executable must separately refuse this unsupported input interpretation.
    _admission_assert_publicly_valid(client, project)
    monkeypatch.setattr(
        subprocess,
        "Popen",
        lambda *args, **kwargs: pytest.fail(
            "Unsupported units must not execute a fixed preset"
        ),
    )
    preflight = _admission_check(client, project)
    assert preflight["readiness"]["model"]["status"] == "valid"
    assert preflight["status"] == "blocked", preflight
    assert preflight["readiness"]["capabilities"]["status"] == "unsupported"
    requested = next(
        row
        for row in preflight["planPreview"]["plan"]["parameters"]
        if row["id"] == "duration"
    )
    assert requested["unitSemantics"] == "ms"
    assert (
        "CAPABILITY_UNSUPPORTED"
        in preflight["readiness"]["capabilities"]["diagnosticCodes"]
    )
    assert preflight["readiness"]["capabilities"]["remediation"]
    assert (
        client.app.state.studio.store.get("snapshot", preflight["snapshotId"])[
            "configuration"
        ]
        is None
    )
    _admission_refuses_start(client, preflight, "unsupported-duration-unit")
