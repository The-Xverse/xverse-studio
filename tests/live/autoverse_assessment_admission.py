"""Offline admission over the actually enrolled Autoverse provider; no dispatch."""
from copy import deepcopy
import json
import os
from pathlib import Path

import pytest
from ruamel.yaml import YAML
from autoverse_provider_admission import application, authenticated
from xverse_studio.blueprints.autoverse import assessment_example
from xverse_studio.blueprints.autoverse_assessments import NAMESPACE, OBSERVER
from xverse_studio.providers.autoverse.adapter import AutoverseProvider
from xverse_studio.xdl import XDLAdapter
from xverse_studio.xdl.examples import dump_yaml


@pytest.fixture
def enrolled(tmp_path, monkeypatch):
    receipt = json.loads(Path(os.environ["STUDIO_AUTOVERSE_TEST_INSTALLATION"]).read_bytes())
    provider = AutoverseProvider(receipt["classic"])
    app = application(tmp_path / "Actual assessment admission Ω", provider)
    def forbidden(*args, **kwargs):
        raise AssertionError("Static assessment admission must not dispatch or probe runtime")
    monkeypatch.setattr(provider, "readiness", forbidden)
    monkeypatch.setattr(app.state.studio.runs, "_dispatch", forbidden)
    with authenticated(app) as api:
        yield app, api, provider
        assert app.state.studio.store.all("run") == app.state.studio.store.all("operation") == []


def test_enrolled_assessment_blueprint_is_real_source_and_static_observation_admission(enrolled):
    app, api, provider = enrolled
    response = api.post("/api/v1/projects", json={"name": "Retrospective bridge acknowledgements", "blueprintRef": "autoverse-fault-assessments"})
    assert response.status_code == 201, response.text
    p = response.json()
    assert p["manifest"]["provenance"]["evidenceScope"] == "external_demo"
    documents = {doc["path"]: doc["content"] for doc in p["documents"].values()}
    compiled = app.state.studio.adapter.compile(documents)
    assert compiled["valid"] and provider.configuration(documents, compiled)["assessment"]["observerRef"] == OBSERVER
    report = api.get(f"/api/v1/projects/{p['projectId']}/scenario-admission", params={"revision": p["revision"], "providerId": "autoverse.demo"})
    assert report.status_code == 200, report.text
    value = report.json()
    assert value["status"] == "preflight_required" and value["sourceMapping"] == "supported"
    assert value["observations"]["observerCount"] == 2
    assert value["observations"]["budgets"] == [{"unit": "observer-slot", "maximum": 1, "total": 1, "status": "satisfied"}]


@pytest.mark.parametrize("case", ["unknown-field", "other-observer", "profile-version", "profile-schema", "missing-profile",
                                 "unknown-profile", "duplicate-definition", "unknown-operator", "observer-target", "opaque-runtime-extension"])
def test_actual_provider_preserves_but_refuses_unknown_assessment_semantics(enrolled, case):
    _, _, provider = enrolled
    documents = deepcopy(assessment_example()["documents"])
    yaml = YAML(typ="safe")
    scenario = yaml.load(documents["scenario.xdl.yaml"])
    profile = yaml.load(documents["assessment-profile.xdl.yaml"])
    definitions = scenario["extensions"][NAMESPACE]["definitions"]
    if case == "unknown-field":
        definitions[0]["expression"]["input"]["field"] = "vehicleSafe"
    elif case == "other-observer":
        definitions[0]["expression"]["input"]["observerRef"] = "autoverse-telemetry"
    elif case == "profile-version":
        profile["metadata"]["version"] = "2.0.0"
    elif case == "profile-schema":
        profile["spec"]["schemaRef"] = "https://unsupported.invalid/never-fetch.json"
    elif case == "missing-profile":
        del documents["assessment-profile.xdl.yaml"]
    elif case == "unknown-profile":
        profile["spec"]["extensionNamespace"] = "io.unadmitted.assessments"
    elif case == "duplicate-definition":
        definitions.append(deepcopy(definitions[0]))
    elif case == "unknown-operator":
        definitions[0]["expression"]["operator"] = "execute"
    elif case == "observer-target":
        scenario["spec"]["observers"][-1]["targetRef"]["element"] = "carla"
    else:
        scenario["extensions"]["io.xverse.studio.native-runtime"]["unadmitted"] = "inert data never executed"
    documents["scenario.xdl.yaml"] = dump_yaml(scenario)
    if case != "missing-profile":
        documents["assessment-profile.xdl.yaml"] = dump_yaml(profile)
    before = deepcopy(documents)
    compiled = XDLAdapter().compile(documents)
    assert not compiled["valid"] or provider.configuration(documents, compiled) is None
    assert documents == before
