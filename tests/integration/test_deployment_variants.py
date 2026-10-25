import pytest
import time

from xverse_studio.deployments import Deployments, compile_selection
from xverse_studio.projects.service import Projects
from xverse_studio.storage.core import Problem, Store
from xverse_studio.xdl import XDLAdapter, reference_configuration


def test_authored_variants_keep_logical_identity_and_compile_explicit_contributors(tmp_path):
    adapter = XDLAdapter()
    projects = Projects(Store(tmp_path), adapter)
    project = projects.create("Deployment variants")
    deployments = Deployments(projects, adapter)
    before = projects.sources(project)
    result = deployments.create(project["projectId"], 1, {"name": "Alternative"})
    updated = result["project"]
    assert updated["revision"] == 2
    assert adapter.validate(projects.sources(updated))["valid"]
    assert len(deployments.list(project["projectId"])["items"]) == 2
    assert next(value for path, value in before.items() if path.endswith("system.xdl.yaml")) == next(
        value for path, value in projects.sources(updated).items() if path.endswith("system.xdl.yaml"))
    selected = compile_selection(projects.sources(updated), {"deploymentRef": result["variant"]["ref"]}, adapter)
    assert selected["valid"], selected["diagnostics"]
    assert selected["selection"]["deploymentRef"] == result["variant"]["ref"]
    assert len(selected["contributingDocuments"]) == len(before)
    assert len(projects.sources(updated)) == len(before) + 2
    config = reference_configuration(selected["contributingDocuments"], selected)
    assert config["target"] == 1
    assert config["planDigest"] == selected["planDigest"]


def test_ambiguous_or_mismatched_variant_selection_does_not_fall_back(tmp_path):
    adapter = XDLAdapter()
    projects = Projects(Store(tmp_path), adapter)
    project = projects.create("Ambiguous selection")
    deployments = Deployments(projects, adapter)
    original = deployments.list(project["projectId"])["items"][0]
    result = deployments.create(project["projectId"], 1, {"name": "Other"})
    documents = projects.sources(result["project"])
    with pytest.raises(Problem) as error:
        compile_selection(documents, {}, adapter)
    assert error.value.code == "SELECTION_AMBIGUOUS"
    with pytest.raises(Problem) as mismatch:
        compile_selection(documents, {"deploymentRef": result["variant"]["ref"], "scenarioRef": original["scenarioRefs"][0]}, adapter)
    assert mismatch.value.code == "SELECTION_INCOMPATIBLE"


def test_invalid_rebinding_preserves_prior_revision(tmp_path):
    adapter = XDLAdapter()
    projects = Projects(Store(tmp_path), adapter)
    project = projects.create("Binding validation")
    deployments = Deployments(projects, adapter)
    variant = deployments.list(project["projectId"])["items"][0]
    with pytest.raises(Problem):
        deployments.update_binding(project["projectId"], 1, variant["documentId"], {"bindingId": "plant-binding", "targetId": "not-declared"})
    assert projects.read(project["projectId"])["revision"] == 1


def test_http_selected_variant_runs_exact_authored_pair_and_rejects_original_pair(client):
    created = client.post("/api/v1/projects", json={"name": "HTTP authored variant"})
    assert created.status_code == 201
    project = created.json()
    project_id = project["projectId"]
    original = client.get(f"/api/v1/projects/{project_id}/deployment-variants").json()["items"][0]
    response = client.post(f"/api/v1/projects/{project_id}/deployment-variants", headers={"If-Match": "1"},
                           json={"baseRevision": 1, "name": "HTTP alternative"})
    assert response.status_code == 201, response.text
    changed = response.json()
    variant = changed["variant"]
    mismatch = client.post(f"/api/v1/projects/{project_id}/preflights", json={"revision": 2, "deploymentRef": variant["ref"], "scenarioRef": original["scenarioRefs"][0]})
    assert mismatch.status_code == 422
    assert mismatch.json()["code"] == "SELECTION_INCOMPATIBLE"
    compilation = client.post(f"/api/v1/projects/{project_id}/compilations", json={"revision": 2, "deploymentRef": variant["ref"], "scenarioRef": variant["scenarioRefs"][0]})
    assert compilation.status_code == 200, compilation.text
    assert compilation.json()["valid"]
    pf = client.post(f"/api/v1/projects/{project_id}/preflights", json={"revision": 2, "deploymentRef": variant["ref"], "scenarioRef": variant["scenarioRefs"][0]})
    assert pf.status_code == 200, pf.text
    pf = pf.json()
    assert pf["status"] == "ready", pf
    snapshot = client.app.state.studio.store.get("snapshot", pf["snapshotId"])
    assert len(snapshot["projectDocuments"]) == len(snapshot["documents"]) + 2
    assert snapshot["selection"]["deploymentRef"] == variant["ref"]
    response = client.post("/api/v1/runs", headers={"Idempotency-Key": "http-variant-once"},
                           json={"snapshotId": pf["snapshotId"], "preflightId": pf["preflightId"]})
    assert response.status_code == 202, response.text
    run_id = response.json()["runId"]
    deadline = time.monotonic() + 12
    while time.monotonic() < deadline:
        run = client.get("/api/v1/runs/" + run_id).json()
        if run["state"] in {"running", "stopped", "failed", "unknown"}:
            break
        time.sleep(.05)
    assert run["state"] in {"running", "stopped"}, run
    assert run["effectivePlanDigest"] == compilation.json()["planDigest"]
    if run["state"] == "running":
        cancellation = client.post(f"/api/v1/runs/{run_id}/commands", headers={"Idempotency-Key": "http-variant-cancel"},
                                   json={"kind": "cancel", "expectedStateVersion": run["stateVersion"]})
        assert cancellation.status_code == 202, cancellation.text


def test_http_profile_locks_and_catalog_are_revisioned_and_inert(client):
    project = client.post("/api/v1/projects", json={"name": "HTTP profile locks"}).json()
    profiles = client.get("/api/v1/profiles").json()["items"]
    locks = [{key: profile[key] for key in ("profileId", "version", "schemaDigest", "presentationDigest")} for profile in profiles]
    missing = client.post(f"/api/v1/projects/{project['projectId']}/profile-bindings", json={"baseRevision": 1, "profiles": locks})
    assert missing.status_code == 428
    response = client.post(f"/api/v1/projects/{project['projectId']}/profile-bindings", headers={"If-Match": "1"}, json={"baseRevision": 1, "profiles": locks})
    assert response.status_code == 200, response.text
    assert response.headers["ETag"] == '"2"'
    assert len(response.json()["manifest"]["profiles"]) == 2
    catalog = client.get("/api/v1/catalog", params={"kind": "component", "role": "controller"}).json()["items"]
    assert len(catalog) == 1
    artifact = client.post("/api/v1/catalog/artifacts", headers={"Idempotency-Key": "http-inert-artifact"}, json={
        "name": "Portable model metadata", "version": "1.0.0", "artifactKind": "model", "digest": "sha256:" + "c" * 64,
        "originRef": "urn:example:uninstalled-model", "providerIds": ["studio.reference"], "apiVersions": ["xverse.io/xdl/v1alpha1"]})
    assert artifact.status_code == 201, artifact.text
    assert artifact.json()["executionAllowed"] is False
    assert client.get("/api/v1/runs").json()["items"] == []


def test_cloned_scenario_preserves_explicit_named_metric_dependency_pins(tmp_path):
    from ruamel.yaml import YAML
    from xverse_studio.assertions.snapshot import definition_digest, snapshot_definitions
    from xverse_studio.storage.core import digest
    from xverse_studio.xdl.examples import dump_yaml
    adapter = XDLAdapter()
    projects = Projects(Store(tmp_path), adapter)
    project = projects.create("Metric-aware scenario clone")
    identifier, document = next((key, value) for key, value in project["documents"].items() if value["path"].endswith("scenario.xdl.yaml"))
    scenario = YAML(typ="safe").load(document["content"])
    definitions = scenario["extensions"]["io.xverse.studio.experiments"]["definitions"]
    assertion = definitions[0]
    metric = {"evaluationId": "peak-value", "version": "1.0", "kind": "metric", "name": "Peak value", "systemRef": assertion["systemRef"],
              "scenarioRef": assertion["scenarioRef"], "window": assertion["window"].copy(), "coveragePolicy": "complete", "resultUnit": "1",
              "expression": {"kind": "aggregate", "operator": "max", "input": {"kind": "signal", "observerRef": "state-observer", "field": "value"}}}
    assertion["expression"]["left"] = {"kind": "metric", "evaluationRef": {"evaluationId": "peak-value", "version": "1.0", "definitionDigest": definition_digest(metric)}}
    definitions.append(metric)
    project = projects.save(project["projectId"], identifier, 1, dump_yaml(scenario), "yaml")
    result = Deployments(projects, adapter).create(project["projectId"], 2, {"name": "Metric variant"})
    compiled = compile_selection(projects.sources(result["project"]), {"deploymentRef": result["variant"]["ref"]}, adapter)
    assert compiled["valid"]
    snapshot = {"documents": compiled["contributingDocuments"]}
    snapshot["snapshotDigest"] = digest(snapshot)
    copied = snapshot_definitions(snapshot, adapter)
    assert {entry["definitionRef"] for entry in copied} == {"peak-value", "state-within-bound"}
    assert all(entry["definition"]["scenarioRef"] == result["variant"]["scenarioRefs"][0] for entry in copied)


def test_ambiguous_binding_admission_refuses_before_committing_and_explicit_scenario_works(tmp_path):
    from copy import deepcopy
    from ruamel.yaml import YAML
    from xverse_studio.xdl import examples
    from xverse_studio.xdl.examples import dump_yaml
    adapter = XDLAdapter()
    projects = Projects(Store(tmp_path), adapter)
    documents = examples()[0]["documents"]
    extra = deepcopy(YAML(typ="safe").load(documents["scenario.xdl.yaml"]))
    extra["metadata"]["name"] = "another-scenario"
    extra["extensions"]["io.xverse.experiment"]["target"]["name"] = "another-scenario"
    for definition in extra["extensions"]["io.xverse.studio.experiments"]["definitions"]:
        definition["scenarioRef"] = "xdl://" + extra["metadata"]["namespace"] + "/scenario/another-scenario"
    documents["another-scenario.xdl.yaml"] = dump_yaml(extra)
    project = projects.create("Two source scenarios", documents=documents)
    deployments = Deployments(projects, adapter)
    variant = deployments.list(project["projectId"])["items"][0]
    before = projects.sources(project)
    with pytest.raises(Problem) as error:
        deployments.update_binding(project["projectId"], 1, variant["documentId"], {"bindingId": "plant-binding", "targetId": "reference-target"})
    assert error.value.code == "SELECTION_AMBIGUOUS"
    assert projects.read(project["projectId"])["revision"] == 1
    assert projects.sources(projects.read(project["projectId"])) == before
    result = deployments.update_binding(project["projectId"], 1, variant["documentId"], {
        "bindingId": "plant-binding", "targetId": "reference-target", "scenarioRef": variant["scenarioRefs"][0]})
    assert result["project"]["revision"] == 2


def test_variant_path_collision_never_replaces_existing_component_or_advances_revision(tmp_path):
    from copy import deepcopy
    from ruamel.yaml import YAML
    from xverse_studio.xdl import examples
    from xverse_studio.xdl.examples import dump_yaml
    adapter = XDLAdapter()
    projects = Projects(Store(tmp_path), adapter)
    documents = examples()[0]["documents"]
    extra = deepcopy(YAML(typ="safe").load(documents["plant.xdl.yaml"]))
    extra["metadata"]["name"] = "unused-component"
    for endpoint in extra["spec"]["endpoints"]:
        endpoint["ownerId"] = "unused-component"
    documents["deployment-review-collision.xdl.yaml"] = dump_yaml(extra)
    project = projects.create("Path identity collision", documents=documents)
    before = projects.sources(project)
    with pytest.raises(Problem):
        Deployments(projects, adapter).create(project["projectId"], 1, {"name": "Review collision"})
    recovered = projects.read(project["projectId"])
    assert recovered["revision"] == 1
    projects.assert_intact(recovered)
    assert projects.sources(recovered) == before
