"""Versioned positive/negative input-loss intent on actual enrolled Autoverse."""


import pytest
from ruamel.yaml import YAML

import autoverse_provider_admission as enrollment
from autoverse_composition import checked, document, sources, forbidden
from autoverse_provider_admission import application, authenticated, project
from xverse_studio.blueprints.autoverse import documents, NAMESPACE
from xverse_studio.xdl.examples import dump_yaml

ACTIVATION = "urn:xverse:studio:autoverse:input-loss:1.0:activation"
RECOVERY = "urn:xverse:studio:autoverse:input-loss:1.0:recovery"
PROFILE = "io.xverse.experiment"
SAFE = YAML(typ="safe")
target = enrollment.target


def fault(scenario, identifier="input-loss", at=5, duration=3, unit="s"):
    target = {**scenario["spec"]["systemRef"], "element": "driver"}
    owner = {
        "apiVersion": scenario["apiVersion"],
        "kind": "Scenario",
        **{k: scenario["metadata"][k] for k in ["namespace", "name"]},
        "element": identifier,
    }
    return {
        "id": identifier,
        "targetRef": target,
        "faultKind": "driver-input-loss",
        "activation": ACTIVATION,
        "recovery": RECOVERY,
        "maturity": "prototype",
        "extensions": {
            PROFILE: {
                "schemaVersion": "0.1",
                "kind": "fault-intent",
                "target": owner,
                "trigger": {"kind": "time", "at": at, "unit": unit},
                "duration": {"value": duration, "unit": unit},
                "timeDomainId": "host-runtime",
            }
        },
    }


@pytest.fixture
def authored(target, tmp_path, monkeypatch):
    provider, blueprint = target
    app = application(tmp_path / "Autoverse scheduled input loss Ω", provider)
    monkeypatch.setattr(app.state.studio.runs, "_dispatch", forbidden)
    with authenticated(app) as api:
        p = project(api, blueprint)
        if blueprint == "autoverse-classic":
            variant = documents("studio-browser")
            for key, doc in list(p["documents"].items()):
                raw = variant[doc["path"].split("/")[-1]]
                if raw != doc["content"]:
                    p = checked(
                        api.put(
                            f"/api/v1/projects/{p['projectId']}/documents/{key}",
                            headers={"If-Match": str(p["revision"])},
                            json={"content": raw},
                        )
                    )
        yield app, api, provider, p
        assert (
            app.state.studio.store.all("run")
            == app.state.studio.store.all("operation")
            == []
        )


def authored_sources(p):
    result = sources(p)
    key, doc = document(p, "Scenario")
    scenario = SAFE.load(doc["content"])
    scenario["spec"]["faults"] = [fault(scenario)]
    result[doc["path"]] = dump_yaml(scenario)
    return result, scenario, doc["path"]


def test_actual_classic_admits_public_plan_bound_input_loss_and_other_mode_refuses(
    authored,
):
    app, _, provider, p = authored
    source, _, _ = authored_sources(p)
    compiled = app.state.studio.adapter.compile(source)
    assert compiled["valid"], compiled["diagnostics"]
    configuration = provider.configuration(source, compiled)
    if provider.descriptor()["providerId"] == "autoverse.platform":
        assert configuration is None
        assert not provider.descriptor().get("scenarioContracts", {}).get("faults")
    else:
        assert configuration is not None, (
            "Positive scheduled input-loss mapping is not implemented"
        )
        schedule = configuration["inputLoss"]["schedules"][0]
        planned = compiled["plan"]["faultSchedule"][0]
        assert (
            schedule["activationTick"] == "5000000"
            and schedule["recoveryTick"] == "8000000"
        )
        assert (
            schedule["planActivationTick"]
            == str(planned["trigger"]["atTicks"])
            == "5000000000"
        )
        assert (
            schedule["planDurationTick"]
            == str(planned["duration"]["ticks"])
            == "3000000000"
        )
        assert schedule["trigger"] == {"kind": "time", "at": 5, "unit": "s"}
        assert (
            provider.descriptor()["scenarioContracts"]["faults"][0]["kind"]
            == "driver-input-loss"
        )


@pytest.mark.parametrize(
    "case",
    [
        "target",
        "clock",
        "marker",
        "field",
        "early",
        "short",
        "long",
        "horizon",
        "submicrosecond",
        "overlap",
        "adjacent",
        "count",
        "pygame",
    ],
)
def test_actual_autoverse_input_loss_contract_refuses_unadmitted_semantics_before_start(
    authored, case
):
    app, api, provider, p = authored
    source, scenario, path = authored_sources(p)
    f = scenario["spec"]["faults"][0]
    intent = f["extensions"][PROFILE]
    if case == "target":
        f["targetRef"]["element"] = "carla"
    elif case == "clock":
        intent["timeDomainId"] = "unknown"
    elif case == "marker":
        f["activation"] = "opaque custom text"
    elif case == "field":
        intent["extra"] = "unknown intent"
    elif case == "early":
        intent["trigger"]["at"] = 1
    elif case == "short":
        intent["duration"]["value"] = 1
    elif case == "long":
        intent["duration"]["value"] = 31
    elif case == "horizon":
        intent["trigger"]["at"] = 599
    elif case == "submicrosecond":
        intent["trigger"].update(at=5000000001, unit="ns")
    elif case in {"overlap", "adjacent"}:
        scenario["spec"]["faults"].append(
            fault(scenario, "second-loss", 7 if case == "overlap" else 8, 3)
        )
    elif case == "count":
        scenario["spec"]["faults"] = [
            fault(scenario, f"loss-{i}", 5 + i * 5, 2) for i in range(9)
        ]
    elif case == "pygame":
        scenario["extensions"][NAMESPACE]["inputSurface"] = "native-pygame"
    source[path] = dump_yaml(scenario)
    compiled = app.state.studio.adapter.compile(source)
    assert provider.configuration(source, compiled) is None
    key, _ = document(p, "Scenario")
    p = checked(
        api.put(
            f"/api/v1/projects/{p['projectId']}/documents/{key}",
            headers={"If-Match": str(p["revision"])},
            json={"content": source[path]},
        )
    )
    pf = checked(
        api.post(
            f"/api/v1/projects/{p['projectId']}/preflights",
            json={
                "revision": p["revision"],
                "providerId": provider.descriptor()["providerId"],
            },
        )
    )
    assert pf["status"] == "blocked"
    refused = api.post(
        "/api/v1/runs",
        headers={"Idempotency-Key": "unadmitted-input-loss"},
        json={k: pf[k] for k in ["snapshotId", "preflightId"]},
    )
    assert refused.status_code == 422 and refused.json()["code"] == "ADMISSION_REJECTED"
    assert document(p, "Scenario")[1]["content"] == source[path]
