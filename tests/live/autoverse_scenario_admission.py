"""Scenario inspection/budget enforcement on actual enrolled Autoverse providers."""

from copy import deepcopy

import pytest
from ruamel.yaml import YAML

import autoverse_provider_admission as enrollment
from autoverse_composition import checked, document, sources, forbidden, variants
from autoverse_provider_admission import application, authenticated, project
from xverse_studio.xdl.examples import dump_yaml

target = enrollment.target
SAFE = YAML(typ="safe")


@pytest.fixture
def authored(target, tmp_path, monkeypatch):
    provider, blueprint = target
    app = application(tmp_path / "Autoverse scenario inspection Ω", provider)
    monkeypatch.setattr(app.state.studio.runs, "_dispatch", forbidden)
    monkeypatch.setattr(provider, "readiness", forbidden)
    with authenticated(app) as api:
        p = project(api, blueprint)
        yield app, api, provider, p
        assert (
            app.state.studio.store.all("run")
            == app.state.studio.store.all("operation")
            == []
        )


def inspect(api, p, provider, **extra):
    return api.get(
        f"/api/v1/projects/{p['projectId']}/scenario-admission",
        params={
            "revision": p["revision"],
            "providerId": provider.descriptor()["providerId"],
            **extra,
        },
    )


def test_actual_autoverse_static_scenario_inspection_is_bound_and_never_ready(authored):
    app, api, provider, p = authored
    report = checked(inspect(api, p, provider))
    assert (
        report["scenarioAdmissionVersion"] == "1.0"
        and report["readOnly"]
        and report["status"] == "preflight_required"
    )
    assert (
        report["projectId"] == p["projectId"]
        and report["revision"] == p["revision"]
        and report["providerId"] == provider.descriptor()["providerId"]
    )
    assert report["sourceMapping"] == "supported" and report["sourceValid"]
    assert (
        report["planDigest"]
        == app.state.studio.adapter.compile(sources(p))["planDigest"]
    )
    assert len(report["steps"]) == 1 and report["faults"] == []
    if report["providerId"] == "autoverse.demo":
        assert len(report["observations"]["items"]) == 1
        b = report["observations"]["budgets"][0]
        assert (
            b["unit"] == "observer-slot"
            and b["total"] == b["maximum"] == 1
            and b["status"] == "satisfied"
        )
    else:
        assert (
            len(report["observations"]["items"]) == 4
            and report["observations"]["status"] == "not_declared"
        )
    assert all(
        row["retention"]["status"] == "not_declared"
        for row in report["observations"]["items"]
    )
    assert app.state.studio.store.all("snapshot") == []


@pytest.mark.parametrize(
    "case",
    [
        "exceeded",
        "unknown-cost",
        "duplicate-unit",
        "bad-type",
        "bad-version",
        "count",
        "unit-mismatch",
        "duplicate-observer",
        "fractional-count",
    ],
)
def test_actual_autoverse_declared_budget_refuses_before_readiness_or_dispatch(
    authored, monkeypatch, case
):
    app, api, provider, p = authored
    _, doc = document(p, "Scenario")
    ids = [o["id"] for o in SAFE.load(doc["content"])["spec"]["observers"]]
    original = provider.descriptor
    contract = {
        "contractVersion": "1.0",
        "observers": [
            {"observerId": i, "costs": [{"value": 1, "unit": "review-slot"}]}
            for i in ids
        ],
        "budgets": [{"unit": "review-slot", "maximum": len(ids)}],
    }
    if case == "exceeded":
        contract["budgets"][0]["maximum"] = 0
    elif case == "unknown-cost":
        contract["observers"][0]["costs"] = None
    elif case == "duplicate-unit":
        contract["budgets"].append(deepcopy(contract["budgets"][0]))
    elif case == "bad-type":
        contract["observers"][0]["costs"][0]["value"] = True
    elif case == "bad-version":
        contract["contractVersion"] = "2.0"
    elif case == "unit-mismatch":
        contract["observers"][0]["costs"][0]["unit"] = "other-unit"
    elif case == "duplicate-observer":
        contract["observers"].append(deepcopy(contract["observers"][0]))

    def descriptor():
        d = original()
        d["observationContracts"] = deepcopy(contract)
        if case == "count":
            d["limits"]["maxObservers"] = 0
        elif case == "fractional-count":
            d["limits"]["maxObservers"] = 0.5
        return d

    monkeypatch.setattr(provider, "descriptor", descriptor)
    report = checked(inspect(api, p, provider))
    assert report["status"] == "blocked" and report["observations"]["diagnostics"]
    pf = checked(
        api.post(
            f"/api/v1/projects/{p['projectId']}/preflights",
            json={"revision": p["revision"], "providerId": descriptor()["providerId"]},
        )
    )
    assert pf["status"] == "blocked" and any(
        d["code"].startswith("OBSERVATION_") for d in pf["diagnostics"]
    )
    denied = api.post(
        "/api/v1/runs",
        headers={"Idempotency-Key": "observation-budget-refusal"},
        json={k: pf[k] for k in ["snapshotId", "preflightId"]},
    )
    assert denied.status_code == 422 and denied.json()["code"] == "ADMISSION_REJECTED"


def test_actual_autoverse_unknown_provider_and_stale_or_extra_query_refuse(authored):
    _, api, provider, p = authored
    assert inspect(api, p, provider, providerId="absent").status_code == 404
    assert inspect(api, p, provider, revision=p["revision"] + 1).status_code == 412
    assert inspect(api, p, provider, budget=999).status_code == 422
    url = f"/api/v1/projects/{p['projectId']}/scenario-admission"
    assert (
        api.get(
            url,
            params=[
                ("revision", p["revision"]),
                ("revision", p["revision"]),
                ("providerId", provider.descriptor()["providerId"]),
            ],
        ).status_code
        == 422
    )
    assert (
        inspect(
            api, p, provider, scenarioRef="xdl://absent/scenario/absent"
        ).status_code
        == 422
    )


def test_actual_autoverse_unadmitted_observer_source_is_retained_and_sanitized(
    authored,
):
    app, api, provider, p = authored
    key, doc = document(p, "Scenario")
    value = SAFE.load(doc["content"])
    value["spec"]["observers"][0]["evidenceSinkRef"] = (
        "https://user:secret@example.invalid/forbidden"
    )
    credentialed = dump_yaml(value)
    rejected = api.put(
        f"/api/v1/projects/{p['projectId']}/documents/{key}",
        headers={"If-Match": str(p["revision"])},
        json={"content": credentialed},
    )
    assert (
        rejected.status_code == 422 and rejected.json()["code"] == "CREDENTIAL_REJECTED"
    )
    assert checked(api.get(f"/api/v1/projects/{p['projectId']}")) == p
    value["spec"]["observers"][0]["evidenceSinkRef"] = (
        "https://example.invalid/capture?scope=unadmitted"
    )
    raw = dump_yaml(value)
    p = checked(
        api.put(
            f"/api/v1/projects/{p['projectId']}/documents/{key}",
            headers={"If-Match": str(p["revision"])},
            json={"content": raw},
        )
    )
    report = checked(inspect(api, p, provider))
    assert (
        report["sourceValid"]
        and report["sourceMapping"] == "unsupported"
        and report["status"] == "blocked"
    )
    assert report["observations"]["items"][0]["evidenceSink"]["status"] == "withheld"
    assert (
        "user:secret" not in str(report)
        and document(p, "Scenario")[1]["content"] == raw
    )
    assert app.state.studio.store.all("snapshot") == []


def test_actual_autoverse_invalid_source_never_becomes_zero_cost_or_complete(
    authored, monkeypatch
):
    _, api, provider, p = authored
    key, doc = document(p, "Scenario")
    value = SAFE.load(doc["content"])
    value["apiVersion"] = "xverse.io/xdl/v99"
    raw = dump_yaml(value)
    p = checked(
        api.put(
            f"/api/v1/projects/{p['projectId']}/documents/{key}",
            headers={"If-Match": str(p["revision"])},
            json={"content": raw},
        )
    )
    monkeypatch.setattr(provider, "configuration", forbidden)
    report = checked(inspect(api, p, provider))
    assert report["status"] == "blocked" and not report["sourceValid"]
    assert report["observations"]["status"] == "unavailable"
    assert (
        report["observations"]["observerCount"] is None
        and report["observations"]["budgets"] == []
    )
    assert (
        not report["stepsComplete"]
        and not report["faultsComplete"]
        and not report["observations"]["itemsComplete"]
    )
    assert document(p, "Scenario")[1]["content"] == raw


def test_actual_autoverse_inspection_captures_one_descriptor(authored, monkeypatch):
    _, api, provider, p = authored
    original = provider.descriptor
    pid = original()["providerId"]
    calls = []

    def changing():
        d = original()
        calls.append(d)
        if len(calls) > 1:
            d["available"] = False
        return d

    monkeypatch.setattr(provider, "descriptor", changing)
    report = checked(
        api.get(
            f"/api/v1/projects/{p['projectId']}/scenario-admission",
            params={"revision": p["revision"], "providerId": pid},
        )
    )
    assert len(calls) == 1 and report["sourceMapping"] == "supported"


def test_actual_autoverse_static_mapping_failure_is_unknown_without_private_exception(
    authored, monkeypatch
):
    _, api, provider, p = authored

    def broken(*args, **kwargs):
        raise RuntimeError("private-marker-not-for-user")

    monkeypatch.setattr(provider, "configuration", broken)
    report = checked(inspect(api, p, provider))
    assert report["status"] == "blocked" and report["sourceMapping"] == "unknown"
    assert any(
        v["code"] == "SCENARIO_INSPECTION_UNAVAILABLE" for v in report["diagnostics"]
    )
    assert "private-marker" not in str(report)


def test_actual_autoverse_multiple_scenarios_require_explicit_compiler_selection(
    authored,
):
    _, api, provider, p = authored
    p, original, alternative = variants(api, p)
    assert inspect(api, p, provider).status_code == 422
    for ref in [original["scenarioRefs"][0], alternative["scenarioRefs"][0]]:
        report = checked(inspect(api, p, provider, scenarioRef=ref))
        assert (
            report["selection"]["scenarioRef"] == ref
            and report["revision"] == p["revision"]
        )
        assert report["status"] in {"preflight_required", "blocked"}
        assert all(v["effectStatus"] == "declared_intent_only" for v in report["steps"])


def test_actual_autoverse_unavailable_descriptor_has_no_static_runtime_admission(
    authored, monkeypatch
):
    _, api, provider, p = authored
    original = provider.descriptor

    def unavailable():
        d = original()
        d["available"] = False
        return d

    monkeypatch.setattr(provider, "descriptor", unavailable)
    report = checked(inspect(api, p, provider))
    assert report["status"] == "blocked" and report["sourceMapping"] == "unsupported"
    assert any(v["code"] == "PROVIDER_UNAVAILABLE" for v in report["diagnostics"])
