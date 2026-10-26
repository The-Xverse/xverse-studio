import json
import pytest
import time

from ruamel.yaml import YAML

from xverse_studio.deployments import Deployments, compile_selection
from xverse_studio.deployments.resolution import resolution_diagnostics, resolve_deployment
from xverse_studio.projects.service import Projects
from xverse_studio.storage.core import Problem, Store
from xverse_studio.xdl import XDLAdapter, examples, reference_configuration
from xverse_studio.xdl.examples import dump_yaml


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


# --- T057: rebinding compatibility, constraints, effective values and portable/private bindings ---

DEPLOYMENT_REF = "xdl://org.xverse.studio.process-control/deployment/local-reference"
SYSTEM = {"apiVersion": "xverse.io/xdl/v1alpha1", "kind": "System", "namespace": "org.xverse.studio.process-control", "name": "reference-loop"}
RATE = {"id": "rate", "valueType": "number", "unitSemantics": "1/s", "default": 1.0, "mutability": "configuration"}
STEPS = {"id": "steps", "valueType": "integer", "unitSemantics": "1", "default": 4, "mutability": "configuration"}
MODE = {"id": "mode", "valueType": "string", "unitSemantics": "1", "default": "linear", "mutability": "constant"}
LEVEL = {"id": "level", "valueType": "number", "unitSemantics": "1", "default": 1, "mutability": "constant"}


def _sources(mutate=None):
    """The process-control example as an explicit source set, optionally mutated by resource name."""
    yaml = YAML(typ="safe")
    parsed = {"xdl/" + name: yaml.load(content) for name, content in examples()[0]["documents"].items()}
    if mutate:
        mutate({path.rsplit("/", 1)[-1].split(".")[0]: resource for path, resource in parsed.items()})
    documents = {path: dump_yaml(resource) for path, resource in parsed.items()}
    validation = XDLAdapter().validate(documents)
    assert validation["valid"], validation["diagnostics"]  # every case is structurally valid XDL
    return documents


def _report(mutate=None, **options):
    report = resolve_deployment(_sources(mutate), DEPLOYMENT_REF, **options)
    return report, {d["code"] for d in resolution_diagnostics(report)}


def _binding(resources, binding_id):
    return next(b for b in resources["deployment"]["spec"]["bindings"] if b["id"] == binding_id)


def _plant_instance(resources):
    return next(e for e in resources["system"]["spec"]["componentInstances"] if e["id"] == "plant")


def _checks(report, binding_id):
    row = next(row for row in report["bindings"] if row["bindingId"] == binding_id)
    return row, {(c["check"], c.get("requirementId") or c.get("resourceId")): (c["status"], c.get("code")) for c in row["checks"]}


def test_reference_deployment_resolves_without_blocking_and_reports_its_layers():
    report, codes = _report()
    assert report["resolutionVersion"] == "1.0" and codes == set()
    assert {row["bindingId"]: row["status"] for row in report["bindings"]} == {"controller-binding": "compatible", "plant-binding": "compatible"}
    scenario = {p["parameterId"]: p for p in report["parameters"] if p["elementId"] is None}
    assert [layer["layer"] for layer in scenario["target"]["chain"]] == ["profile-default", "scenario"]
    assert scenario["target"]["effective"] == 1.0 and scenario["target"]["status"] == "default"
    assert report["environment"] == [] and report["portability"] == []


def _requirements(resources):
    resources["plant"]["spec"]["artifactRequirements"] = [
        {"id": "model", "artifactKind": "model", "versionConstraint": "1.0.0"},
        {"id": "any-model", "artifactKind": "model", "versionConstraint": "*"}]
    resources["plant"]["spec"]["resourceRequirements"] = [{"id": "cpu", "resourceClass": "cpu", "minimum": {"value": 2, "unit": "core"}}]


def test_compatible_rebinding_preserves_logical_identity_and_meets_declared_requirements(tmp_path):
    adapter = XDLAdapter()
    projects = Projects(Store(tmp_path), adapter)
    project = projects.create("Rebinding")
    deployments = Deployments(projects, adapter)
    plant_id = next(i for i, d in project["documents"].items() if d["path"].endswith("plant.xdl.yaml"))
    plant = YAML(typ="safe").load(project["documents"][plant_id]["content"])
    _requirements({"plant": plant})
    project = projects.save(project["projectId"], plant_id, project["revision"], dump_yaml(plant), "yaml")
    created = deployments.create(project["projectId"], project["revision"], {"name": "Emulated plant"})
    document_id = created["variant"]["documentId"]
    sources = projects.sources(created["project"])
    deployment = YAML(typ="safe").load(created["project"]["documents"][document_id]["content"])
    deployment["spec"]["targets"].append({**deployment["spec"]["targets"][0], "id": "emulator-target", "targetClass": "emulator",
                                          "offeredResourceIds": ["emulator-cpu", "small-cpu"]})
    deployment["spec"]["resources"] = [
        {"id": "emulator-cpu", "resourceClass": "cpu", "capacity": {"value": 2, "unit": "core"}, "allocationPolicy": "exclusive"},
        {"id": "small-cpu", "resourceClass": "cpu", "capacity": {"value": 1, "unit": "core"}, "allocationPolicy": "shared"}]
    saved = projects.save(project["projectId"], document_id, created["project"]["revision"], dump_yaml(deployment), "yaml")
    result = deployments.update_binding(project["projectId"], saved["revision"], document_id,
                                        {"bindingId": "plant-binding", "targetId": "emulator-target", "realizationClass": "virtual",
                                         "resourceIds": ["emulator-cpu"]})
    updated = projects.sources(result["project"])
    # The System and its logical topology are byte-identical; only the binding and readiness changed.
    system = next(p for p in updated if p.endswith("system.xdl.yaml"))
    assert updated[system] == sources[system]
    before_graph, after_graph = adapter.project(sources), adapter.project(updated)
    for collection in ("elements", "connections"):
        assert [e["ref"] for e in after_graph[collection]] == [e["ref"] for e in before_graph[collection]]
    resolution = result["resolution"]
    row, checks = _checks(resolution, "plant-binding")
    assert row["status"] == "compatible" and row["targetClass"] == "emulator"
    assert checks[("artifact", "model")] == ("pass", None) and checks[("artifact", "any-model")] == ("pass", None)
    assert checks[("resource", "cpu")] == ("pass", None) and checks[("placement", "emulator-cpu")] == ("pass", None)
    assert resolution["diagnostics"] == []
    assert any("behavioural equivalence" in limitation for limitation in resolution["limitations"])
    # Readiness is recomputed: the owned reference provider refuses changed placement on its own.
    assert result["compatibility"]["status"] == "blocked"
    assert {d["code"] for d in result["compatibility"]["diagnostics"]} == {"CAPABILITY_UNSUPPORTED"}
    # An incompatible rebinding commits as a draft and names the unmet contract.
    worse = deployments.update_binding(project["projectId"], result["project"]["revision"], document_id,
                                       {"bindingId": "plant-binding", "resourceIds": ["small-cpu"]})
    assert worse["project"]["revision"] == result["project"]["revision"] + 1
    _, checks = _checks(worse["resolution"], "plant-binding")
    assert checks[("resource", "cpu")] == ("fail", "RESOURCE_REQUIREMENT_UNMET")
    assert "RESOURCE_REQUIREMENT_UNMET" in {d["code"] for d in worse["compatibility"]["diagnostics"]}
    assert updated[system] == projects.sources(worse["project"])[system]


def test_incompatible_requirements_are_identified_and_undecidable_ones_stay_unknown():
    def mutate(resources):
        spec = resources["deployment"]["spec"]
        spec["resources"] = [
            {"id": "small-cpu", "resourceClass": "cpu", "capacity": {"value": 1, "unit": "core"}, "allocationPolicy": "shared"},
            {"id": "memory-gib", "resourceClass": "memory", "capacity": {"value": 1, "unit": "GiB"}, "allocationPolicy": "shared"},
            {"id": "memory-mib", "resourceClass": "memory", "capacity": {"value": 4096, "unit": "MiB"}, "allocationPolicy": "shared"}]
        spec["targets"][0]["offeredResourceIds"] = ["small-cpu", "memory-gib", "memory-mib"]
        resources["plant"]["spec"]["artifactRequirements"] = [
            {"id": "firmware", "artifactKind": "firmware", "versionConstraint": "2.0.0"},
            {"id": "exact", "artifactKind": "model", "versionConstraint": "2.0.0"},
            {"id": "range", "artifactKind": "model", "versionConstraint": ">=1.0.0"}]
        resources["plant"]["spec"]["resourceRequirements"] = [
            {"id": "cpu", "resourceClass": "cpu", "minimum": {"value": 2, "unit": "core"}},
            {"id": "memory", "resourceClass": "memory", "minimum": {"value": 2, "unit": "GiB"}}]
        _binding(resources, "plant-binding").update(realizationClass="physical", resourceIds=["small-cpu", "memory-gib", "memory-mib"])
        spec["targets"][0]["externalAssetRef"] = "urn:lab:asset:plant-rig"  # the platform requires it for physical
    report, codes = _report(mutate)
    row, checks = _checks(report, "plant-binding")
    # Realization and placement are independent dimensions; the provider judges the combination.
    assert checks[("realization", None)] == ("declared", None)
    assert checks[("artifact", "firmware")] == ("fail", "ARTIFACT_REQUIREMENT_UNMET")
    assert checks[("artifact", "exact")] == ("fail", "ARTIFACT_REQUIREMENT_UNMET")
    assert checks[("artifact", "range")] == ("unknown", "COMPATIBILITY_UNKNOWN")
    assert checks[("resource", "cpu")] == ("fail", "RESOURCE_REQUIREMENT_UNMET")
    assert checks[("resource", "memory")] == ("unknown", "COMPATIBILITY_UNKNOWN")  # 4096 MiB is not converted
    assert row["status"] == "fail"
    assert {"ARTIFACT_REQUIREMENT_UNMET", "RESOURCE_REQUIREMENT_UNMET", "COMPATIBILITY_UNKNOWN", "BINDING_UNRESOLVED"} <= codes
    controller, _ = _checks(report, "controller-binding")
    assert controller["status"] == "compatible"  # unaffected contracts are not implicated


def _clock(resources, *, default=True):
    spec, system = resources["deployment"]["spec"], resources["system"]["spec"]
    system["timeDomains"] += [{"id": "wall-time", "clockClass": "wall", "epoch": "unix", "rate": "1", "monotonic": False},
                              {"id": "bench-time", "clockClass": "external", "epoch": "bench", "rate": "1", "monotonic": True}]
    if not default:
        system.pop("defaultTimeDomainId")
    spec["simulators"] = [{"id": "plant-sim", "standardRef": "urn:standard:fmi:3.0", "artifactId": "reference-model", "timeDomainId": "wall-time"}]


def _mapping(identifier, source, target, tolerance=0.001):
    return {"id": identifier, "sourceTimeDomainRef": {**SYSTEM, "element": source}, "targetTimeDomainRef": {**SYSTEM, "element": target},
            "mapping": "offset-at-start", "tolerance": {"value": tolerance, "unit": "s"}}


def test_resource_time_and_network_constraints_are_revalidated():
    def mutate(resources):
        spec, system = resources["deployment"]["spec"], resources["system"]["spec"]
        spec["resources"] = [{"id": "gpu", "resourceClass": "gpu", "capacity": {"value": 1, "unit": "device"}, "allocationPolicy": "exclusive"},
                             {"id": "disk", "resourceClass": "storage", "capacity": {"value": 10, "unit": "GiB"},
                              "hardLimit": {"value": 5, "unit": "GiB"}, "allocationPolicy": "quota"}]
        spec["targets"][0]["offeredResourceIds"] = ["gpu"]
        for binding in spec["bindings"]:
            binding["resourceIds"] = ["gpu"]
        _binding(resources, "plant-binding")["resourceIds"] = ["gpu", "disk"]
        _clock(resources)
        system["networks"] = [{"id": "plant-bus", "scope": "loop", "capabilities": ["ordered"]},
                              {"id": "spare-bus", "scope": "loop", "capabilities": ["ordered"]}]
        profile = {"apiVersion": "xverse.io/xdl/v1alpha1", "kind": "Profile", "namespace": resources["profile"]["metadata"]["namespace"],
                   "name": resources["profile"]["metadata"]["name"]}
        network = {**SYSTEM, "element": "plant-bus"}
        spec["networkBindings"] = [{"id": "bus-a", "logicalNetworkRef": network, "profileRef": profile, "limitations": ["Declared only."]},
                                   {"id": "bus-b", "logicalNetworkRef": network, "profileRef": profile, "limitations": ["Declared only."]}]
    report, codes = _report(mutate)
    assert {"RESOURCE_CONFLICT", "RESOURCE_NOT_OFFERED", "CLOCK_MAPPING_MISSING", "NETWORK_BINDING_CONFLICT"} <= codes
    resources = {c["resourceId"]: c["status"] for c in report["constraints"] if c["check"] == "resource"}
    assert resources == {"gpu": "fail", "disk": "declared"}  # a quota hard limit below capacity is not a violation
    networks = {c["networkId"]: c["status"] for c in report["constraints"] if c["check"] == "network"}
    assert networks == {"plant-bus": "fail", "spare-bus": "declared"}

    # A mapping path through another domain relates the simulator clock; accuracy stays unevaluated.
    def mapped(resources):
        mutate(resources)
        resources["deployment"]["spec"]["timeMappings"] = [_mapping("wall-to-bench", "wall-time", "bench-time"),
                                                           _mapping("bench-to-sim", "bench-time", "simulation-time")]
    report, codes = _report(mapped)
    assert "CLOCK_MAPPING_MISSING" not in codes
    assert {c["mappingId"]: c["status"] for c in report["constraints"] if c["check"] == "time"} == {
        "wall-to-bench": "declared", "bench-to-sim": "declared"}

    def negative(resources):
        _clock(resources)
        resources["deployment"]["spec"]["timeMappings"] = [_mapping("wall-to-sim", "wall-time", "simulation-time", tolerance=-0.5)]
    _, codes = _report(negative)
    assert codes == {"CLOCK_MAPPING_INVALID"}

    # Without a default time domain there is no reference clock to relate an unmapped simulator to.
    _, codes = _report(lambda resources: _clock(resources, default=False))
    assert codes == {"COMPATIBILITY_UNKNOWN"}

    # A target that declares no offered resources cannot establish placement.
    def undeclared(resources):
        resources["deployment"]["spec"]["resources"] = [
            {"id": "cpu", "resourceClass": "cpu", "capacity": {"value": 1, "unit": "core"}, "allocationPolicy": "shared"}]
        _binding(resources, "plant-binding")["resourceIds"] = ["cpu"]
    report, codes = _report(undeclared)
    assert _checks(report, "plant-binding")[1][("placement", None)] == ("unknown", "COMPATIBILITY_UNKNOWN")


@pytest.mark.parametrize("instance,binding,parameters,status,code,effective", [
    (None, None, [RATE], "default", None, 1.0),
    ({"rate": 2.5}, None, [RATE], "overridden", None, 2.5),
    (None, {"rate": 3.0}, [RATE], "overridden", None, 3.0),
    ({"rate": 2.5}, {"rate": 3.0}, [RATE], "ambiguous", "PRECEDENCE_UNDEFINED", None),
    ({"rate": 2.5}, {"rate": 2.5}, [RATE], "ambiguous", "PRECEDENCE_UNDEFINED", None),
    ({"rate": "fast"}, None, [RATE], "fail", "PARAMETER_INVALID", None),
    ({"steps": 6.0}, None, [STEPS], "overridden", None, 6.0),  # JSON Schema: an integral number is an integer
    ({"steps": 6.5}, None, [STEPS], "fail", "PARAMETER_INVALID", None),
    ({"mode": "cubic"}, None, [MODE], "fail", "PARAMETER_IMMUTABLE", None),
    ({"level": 1.0}, None, [LEVEL], "overridden", None, 1.0),  # the same JSON number as its constant default
    ({"gain": 4}, None, [], "unsupported", "PARAMETER_UNDECLARED", None),
])
def test_effective_values_show_their_chain_and_reject_undefined_precedence(instance, binding, parameters, status, code, effective):
    def mutate(resources):
        resources["plant"]["spec"]["parameters"] = list(parameters)
        if instance:
            _plant_instance(resources)["parameterValues"] = instance
        if binding:
            _binding(resources, "plant-binding")["parameterValues"] = binding
    report, codes = _report(mutate)
    entry = next(p for p in report["parameters"] if p["elementId"] == "plant")
    assert (entry["status"], entry.get("code"), entry["effective"]) == (status, code, effective)
    expected = ([("definition-default", "xdl/plant.xdl.yaml", "/spec/parameters/0/default")] if parameters else []) + (
        [("system-instance", "xdl/system.xdl.yaml", f"/spec/componentInstances/1/parameterValues/{entry['parameterId']}")] if instance else []) + (
        [("deployment-binding", "xdl/deployment.xdl.yaml", f"/spec/bindings/1/parameterValues/{entry['parameterId']}")] if binding else [])
    assert [(layer["layer"], layer["documentId"], layer["pointer"]) for layer in entry["chain"]] == expected
    assert (code in codes) if code else not codes


def test_binding_values_on_non_component_elements_are_reported_not_dropped():
    def mutate(resources):
        binding = {**_binding(resources, "plant-binding"), "id": "node-binding", "parameterValues": {"rack": 3}}
        binding["logicalRef"] = {**binding["logicalRef"], "element": "plant-node"}
        resources["deployment"]["spec"]["bindings"].append(binding)
    report, codes = _report(mutate)
    entry = next(p for p in report["parameters"] if p["elementId"] == "plant-node")
    assert (entry["parameterId"], entry["status"]) == ("rack", "unsupported") and "PARAMETER_UNDECLARED" in codes


def test_portable_intent_is_separate_from_environment_addresses_and_secret_handles():
    def mutate(resources):
        spec = resources["deployment"]["spec"]
        spec["targets"][0]["externalAssetRef"] = "https://admin:PW-asset@bench.lab/asset/7"
        plant = _binding(resources, "plant-binding")
        plant["secretRefs"] = ["secret://vault/plant-license", "https://operator:PW-pass@license.example/plant?token=PW-query",
                               "https://PW-user@github.com/org/repo", "vault://kv/plant#token=PW-fragment"]
        plant["parameterValues"] = {"modelPath": "C:\\models\\plant.fmu", "cache": "/var/cache/plant", "topic": "/plant/state",
                                    "fmu": "file:C:/models/plant.fmu", "share": "file://fileserver/share/plant.fmu",
                                    "endpoint": "mqtt://u:PW-value@broker:1883", "dsn": "host=db;password=PW-dsn"}
    report, codes = _report(mutate, host_os="Linux")
    text = json.dumps(report)
    assert "PW-" not in text  # credential material is never echoed, wherever it was authored
    environment = sorted((e["kind"], e["status"], e["code"]) for e in report["environment"])
    assert environment == sorted([("asset", "fail", "SECRET_INLINE"), ("secret", "unresolved", "BINDING_UNRESOLVED")]
                                 + [("secret", "fail", "SECRET_INLINE")] * 3 + [("value", "fail", "SECRET_INLINE")] * 2)
    intent = json.dumps(report["portableIntent"])
    assert "bench.lab" not in intent and "secret://" not in intent and "license.example" not in intent
    paths = {c["pointer"].rsplit("/", 1)[-1]: (c["status"], c.get("code")) for c in report["portability"]}
    assert paths == {"modelPath": ("fail", "HOST_PATH_INCOMPATIBLE"), "fmu": ("fail", "HOST_PATH_INCOMPATIBLE"),
                     "cache": ("declared", None), "share": ("declared", None)}  # the MQTT topic is not a host path
    assert {"SECRET_INLINE", "BINDING_UNRESOLVED", "HOST_PATH_INCOMPATIBLE"} <= codes
    # The same intent resolves against the selected host and provider OS contract.
    for host, provider, expected in (("Windows", None, {"modelPath": "declared", "fmu": "declared", "cache": "fail"}),
                                     ("Darwin", None, {"modelPath": "fail", "fmu": "fail", "cache": "declared"}),
                                     ("Linux", {"supportedHostOS": ["Windows"]}, {"modelPath": "fail", "fmu": "fail", "cache": "fail"})):
        other, _ = _report(mutate, host_os=host, provider=provider)
        statuses = {c["pointer"].rsplit("/", 1)[-1]: c["status"] for c in other["portability"]}
        assert {k: statuses[k] for k in expected} == expected and statuses["share"] == "declared"


def test_http_resolution_rebinding_and_preflight_block_ambiguous_effective_values(client):
    project = client.post("/api/v1/projects", json={"name": "Effective values"}).json()
    pid = project["projectId"]
    variant = client.get(f"/api/v1/projects/{pid}/deployment-variants").json()["items"][0]
    url = f"/api/v1/projects/{pid}/deployment-variants/{variant['documentId']}/resolution"
    resolution = client.get(url)
    assert resolution.status_code == 200, resolution.text
    assert resolution.json()["revision"] == project["revision"] and resolution.json()["diagnostics"] == []
    assert resolution.json()["providerId"] == "studio.reference"
    documents = project["documents"]
    yaml = YAML(typ="safe")
    revision = project["revision"]
    for suffix, change in (("plant.xdl.yaml", lambda r: r["spec"].update(parameters=[RATE])),
                           ("system.xdl.yaml", lambda r: _plant_instance({"system": r}).update(parameterValues={"rate": 2.0})),
                           ("deployment.xdl.yaml", lambda r: next(b for b in r["spec"]["bindings"] if b["id"] == "plant-binding").update(parameterValues={"rate": 3.0}))):
        document_id = next(i for i, d in documents.items() if d["path"].endswith("/" + suffix))
        resource = yaml.load(documents[document_id]["content"])
        change(resource)
        saved = client.put(f"/api/v1/projects/{pid}/documents/{document_id}", headers={"If-Match": str(revision)},
                           json={"content": dump_yaml(resource)})
        assert saved.status_code == 200, saved.text
        revision = saved.json()["revision"]
    report = client.get(url).json()
    rate = next(p for p in report["parameters"] if p["parameterId"] == "rate")
    assert rate["status"] == "ambiguous" and [layer["value"] for layer in rate["chain"]] == [1.0, 2.0, 3.0]
    rebound = client.patch(f"/api/v1/projects/{pid}/deployment-variants/{variant['documentId']}", headers={"If-Match": str(revision)},
                           json={"baseRevision": revision, "bindingId": "plant-binding", "realizationClass": "virtual"})
    assert rebound.status_code == 200, rebound.text
    assert "PRECEDENCE_UNDEFINED" in {d["code"] for d in rebound.json()["resolution"]["diagnostics"]}
    assert "PRECEDENCE_UNDEFINED" in {d["code"] for d in rebound.json()["compatibility"]["diagnostics"]}
    revision = rebound.json()["project"]["revision"]
    preflight = client.post(f"/api/v1/projects/{pid}/preflights", json={"revision": revision}).json()
    assert preflight["status"] == "blocked"
    assert "PRECEDENCE_UNDEFINED" in {d["code"] for d in preflight["diagnostics"]}
    assert client.get("/api/v1/runs").json()["items"] == []
    assert client.get(f"/api/v1/projects/{pid}/deployment-variants/missing/resolution").status_code == 404
    # An unparseable draft is reported as invalid source, never a server error.
    broken = client.put(f"/api/v1/projects/{pid}/documents/{variant['documentId']}", headers={"If-Match": str(revision)},
                        json={"content": "kind: Deployment\n  bad: ["})
    assert broken.status_code == 200, broken.text
    invalid = client.get(url)
    assert invalid.status_code == 200 and invalid.json()["sourceValid"] is False and invalid.json()["diagnostics"]
