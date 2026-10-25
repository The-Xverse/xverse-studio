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
