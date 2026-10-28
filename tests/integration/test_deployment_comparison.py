"""Revision-coherent static deployment comparison; no provider contact or run."""

from copy import deepcopy

import pytest
from ruamel.yaml import YAML

from xverse_studio.deployments import Deployments, compile_selection
from xverse_studio.storage.core import Problem, digest
from xverse_studio.xdl.examples import dump_yaml


def variants(client):
    response = client.post("/api/v1/projects", json={"name": "Coherent variants"})
    assert response.status_code == 201
    project = response.json()
    url = "/api/v1/projects/" + project["projectId"] + "/deployment-variants"
    left = client.get(url).json()["items"][0]
    response = client.post(
        url,
        headers={"If-Match": str(project["revision"])},
        json={"name": "Comparison candidate", "baseRevision": project["revision"]},
    )
    assert response.status_code == 201, response.text
    value = response.json()
    right = next(
        v
        for v in client.get(url).json()["items"]
        if v["documentId"] == value["variant"]["documentId"]
    )
    return value["project"], left, right, url


def test_resolution_refuses_requested_stale_revision_instead_of_relabelling_new_source(
    client,
):
    project, left, _, url = variants(client)
    response = client.get(
        url + "/" + left["documentId"] + "/resolution",
        params={"revision": project["revision"] - 1},
    )
    assert response.status_code == 412, response.text
    assert response.json()["code"] == "REVISION_CONFLICT"


def test_comparison_uses_one_authored_revision_and_preserves_project_and_runs(client):
    project, left, right, url = variants(client)
    before = client.get("/api/v1/projects/" + project["projectId"]).json()
    response = client.get(
        url + "/" + left["documentId"] + "/comparison",
        params={
            "otherDocumentId": right["documentId"],
            "revision": project["revision"],
        },
    )
    assert response.status_code == 200, response.text
    value = response.json()
    assert value["comparisonVersion"] == "1.0"
    assert value["projectId"] == project["projectId"]
    assert value["revision"] == project["revision"]
    assert value["scope"] == "static_deployment_comparison"
    assert value["left"]["resolution"]["documentId"] == left["documentId"]
    assert value["right"]["resolution"]["documentId"] == right["documentId"]
    assert (
        value["left"]["resolution"]["revision"]
        == value["right"]["resolution"]["revision"]
        == project["revision"]
    )
    system = next(
        d
        for d in project["documents"].values()
        if d["path"].endswith("/system.xdl.yaml")
    )
    assert value["sharedSystem"]["sourceDigest"] == digest(system["content"].encode())
    assert value["sharedSystem"]["ref"] == left["systemRef"] == right["systemRef"]
    assert value["physicalState"] == value["cleanup"] == "unknown"
    assert value["runtimeAdmission"] == "preflight_required"
    assert client.get("/api/v1/projects/" + project["projectId"]).json() == before
    assert client.get("/api/v1/runs").json()["items"] == []


def comparison(client, project, left, right, **extra):
    return client.get(
        "/api/v1/projects/"
        + project["projectId"]
        + "/deployment-variants/"
        + left["documentId"]
        + "/comparison",
        params={
            "revision": project["revision"],
            "otherDocumentId": right["documentId"],
            **extra,
        },
    )


@pytest.mark.parametrize("revision", [0, -1, "unknown", 9007199254740992])
def test_comparison_invalid_revision_rejected_at_http_boundary(client, revision):
    project, left, right, _ = variants(client)
    assert (
        comparison(client, project, left, right, revision=revision).status_code == 422
    )


def test_comparison_missing_revision_and_stale_revision_are_distinct_refusals(client):
    project, left, right, url = variants(client)
    assert (
        client.get(
            url + "/" + left["documentId"] + "/comparison",
            params={"otherDocumentId": right["documentId"]},
        ).status_code
        == 422
    )
    response = comparison(
        client, project, left, right, revision=project["revision"] - 1
    )
    assert (
        response.status_code == 412 and response.json()["code"] == "REVISION_CONFLICT"
    )


def test_comparison_rejects_missing_non_deployment_and_same_document(client):
    project, left, right, _ = variants(client)
    for identifier in [
        "missing",
        next(
            k
            for k, d in project["documents"].items()
            if d["path"].endswith("/system.xdl.yaml")
        ),
    ]:
        response = comparison(client, project, left, {"documentId": identifier})
        assert response.status_code == 404 and response.json()["code"] == "NOT_FOUND"
    response = comparison(client, project, left, left)
    assert (
        response.status_code == 422
        and response.json()["code"] == "COMPARISON_SELECTION_INVALID"
    )


def test_provider_absence_is_not_fabricated_as_available_controls(client):
    project, left, right, _ = variants(client)
    response = comparison(client, project, left, right, providerId="not-installed")
    assert (
        response.status_code == 404
        and response.json()["code"] == "PROVIDER_UNAVAILABLE"
    )
    response = comparison(client, project, left, right, providerId="xverse.lite")
    assert response.status_code == 200, response.text
    value = response.json()
    assert value["provider"]["available"] is False
    assert value["provider"]["operations"] == []
    assert value["synchronization"] == {
        "status": "unmeasured",
        "preciseLatencyAvailable": False,
    }
    assert value["physicalState"] == value["cleanup"] == "unknown"


def test_external_source_change_refuses_both_resolution_and_comparison_without_overwriting(
    client,
):
    project, left, right, url = variants(client)
    projects = client.app.state.studio.projects
    path = projects.document_path(project["projectId"], right["documentId"])
    changed = path.read_bytes() + b"\n# owned external edit\n"
    path.write_bytes(changed)
    for response in [
        comparison(client, project, left, right),
        client.get(
            url + "/" + left["documentId"] + "/resolution",
            params={"revision": project["revision"]},
        ),
    ]:
        assert (
            response.status_code == 412
            and response.json()["code"] == "REVISION_CONFLICT"
        )
    assert path.read_bytes() == changed


def test_invalid_source_draft_does_not_create_a_coherent_result(client):
    project, left, right, _ = variants(client)
    projects = client.app.state.studio.projects
    changed = projects.save(
        project["projectId"],
        right["documentId"],
        project["revision"],
        "kind: invalid\n",
        "yaml",
    )
    response = comparison(client, changed, left, right)
    assert response.status_code == 422 and response.json()["code"] == "MODEL_INVALID"


def test_one_captured_project_read_and_one_provider_descriptor(client, monkeypatch):
    import xverse_studio.deployments.comparison as comparison_module
    from xverse_studio.providers import registry

    project, left, right, _ = variants(client)
    state = client.app.state.studio
    service = Deployments(state.projects, state.adapter)
    original = state.projects.read
    reads = []
    descriptor_reads = []
    native_descriptors = registry.descriptors

    def descriptors():
        descriptor_reads.append(True)
        return native_descriptors()

    def read(*args, **kwargs):
        reads.append(args[0])
        return original(*args, **kwargs)

    monkeypatch.setattr(state.projects, "read", read)
    monkeypatch.setattr(registry, "descriptors", descriptors)
    monkeypatch.setattr(comparison_module, "descriptors", descriptors)
    value = service.comparison(
        project["projectId"],
        left["documentId"],
        right["documentId"],
        project["revision"],
    )
    assert reads == [project["projectId"]]
    assert descriptor_reads == [True]
    assert (
        value["left"]["resolution"]["providerId"]
        == value["right"]["resolution"]["providerId"]
        == value["providerId"]
    )
    assert value["providerDigest"].startswith("sha256:")


def test_concurrent_commit_between_resolutions_cannot_mix_revisions_or_bindings(
    client, monkeypatch
):
    project, left, right, _ = variants(client)
    state = client.app.state.studio
    service = Deployments(state.projects, state.adapter)
    original = service._resolve
    sources = []

    def resolve(documents, *args, **kwargs):
        sources.append(digest(documents))
        result = original(documents, *args, **kwargs)
        if len(sources) == 1:
            changed = project["documents"][right["documentId"]]["content"].replace(
                "reference-target", "newer-target"
            )
            state.projects.save(
                project["projectId"],
                right["documentId"],
                project["revision"],
                changed,
                "yaml",
            )
        return result

    monkeypatch.setattr(service, "_resolve", resolve)
    result = service.comparison(
        project["projectId"],
        left["documentId"],
        right["documentId"],
        project["revision"],
    )
    assert len(sources) == 2 and sources[0] == sources[1]
    assert (
        result["revision"]
        == result["left"]["resolution"]["revision"]
        == result["right"]["resolution"]["revision"]
        == project["revision"]
    )
    assert {b["targetId"] for b in result["right"]["resolution"]["bindings"]} == {
        "reference-target"
    }
    now = state.projects.read(project["projectId"])
    assert now["revision"] == project["revision"] + 1
    assert "newer-target" in now["documents"][right["documentId"]]["content"]


def test_different_system_sources_are_not_joined_by_matching_element_names(client):
    project, left, right, _ = variants(client)
    projects = client.app.state.studio.projects
    system = next(
        d
        for d in project["documents"].values()
        if d["path"].endswith("/system.xdl.yaml")
    )
    alternate = YAML(typ="safe").load(system["content"])
    old_name = alternate["metadata"]["name"]
    alternate["metadata"]["name"] = "different-system"

    def transform(p):
        docs = deepcopy(p["documents"])
        docs["different-system"] = {
            "path": "xdl/different-system.xdl.yaml",
            "format": "yaml",
            "content": dump_yaml(alternate),
        }
        for identifier, document in docs.items():
            item = YAML(typ="safe").load(document["content"])
            if identifier == right["documentId"] or (
                item.get("kind") == "Scenario"
                and item["spec"].get("deploymentRef", {}).get("name") == right["name"]
            ):

                def change(v):
                    if isinstance(v, dict):
                        if v.get("kind") == "System" and v.get("name") == old_name:
                            v["name"] = "different-system"
                        for x in v.values():
                            change(x)
                    elif isinstance(v, list):
                        for x in v:
                            change(x)

                change(item)
                document["content"] = dump_yaml(item)
        return docs

    changed = projects.mutate(project["projectId"], project["revision"], transform)
    assert client.app.state.studio.adapter.validate(projects.sources(changed))["valid"]
    response = comparison(client, changed, left, right)
    assert (
        response.status_code == 422
        and response.json()["code"] == "SELECTION_INCOMPATIBLE"
    )


def test_physical_declaration_remains_unsupported_and_preserves_system_source(client):
    project, left, right, _ = variants(client)
    state = client.app.state.studio
    document = YAML(typ="safe").load(
        project["documents"][right["documentId"]]["content"]
    )
    document["spec"]["bindings"][1]["realizationClass"] = "physical"
    document["spec"]["targets"][0]["externalAssetRef"] = "urn:fixture:unadmitted-bench"
    changed = state.projects.save(
        project["projectId"],
        right["documentId"],
        project["revision"],
        dump_yaml(document),
        "yaml",
    )
    response = comparison(client, changed, left, right)
    assert response.status_code == 200, response.text
    value = response.json()
    assert value["sharedSystem"]["sourceDigest"] == next(
        d["digest"]
        for d in project["documents"].values()
        if d["path"].endswith("/system.xdl.yaml")
    )
    row = next(
        b
        for b in value["right"]["resolution"]["bindings"]
        if b["bindingId"] == "plant-binding"
    )
    assert row["realizationClass"] == "physical" and row["status"] == "unsupported"
    compiled = compile_selection(
        state.projects.sources(changed), {"deploymentRef": right["ref"]}, state.adapter
    )
    assert not compiled["valid"]
    assert "XDL1-PLAN-REALIZATION-UNSUPPORTED" in {
        d["code"] for d in compiled["diagnostics"]
    }
    assert "urn:fixture:unadmitted-bench" not in response.text
    assert value["physicalState"] == value["cleanup"] == "unknown"
    assert value["runtimeAdmission"] == "preflight_required"


def test_target_capability_bounds_and_private_text_are_not_authority(client):
    project, left, right, _ = variants(client)
    state = client.app.state.studio
    document = YAML(typ="safe").load(
        project["documents"][right["documentId"]]["content"]
    )
    document["spec"]["targets"][0]["capabilities"] = [
        "pause",
        "password:synthetic-hidden",
    ]
    with pytest.raises(Problem, match="inline credentials"):
        state.projects.save(
            project["projectId"],
            right["documentId"],
            project["revision"],
            dump_yaml(document),
            "yaml",
        )
    assert state.projects.read(project["projectId"])["revision"] == project["revision"]
    document["spec"]["targets"][0]["capabilities"] = ["pause", "opaque@host"]
    changed = state.projects.save(
        project["projectId"],
        right["documentId"],
        project["revision"],
        dump_yaml(document),
        "yaml",
    )
    response = comparison(client, changed, left, right)
    assert response.status_code == 200, response.text
    value = response.json()
    assert value["right"]["declaredTargets"][0]["capabilities"] == ["pause"]
    assert value["right"]["declaredTargets"][0]["omittedCapabilities"] == 1
    assert "opaque@host" not in response.text
    assert "pause" not in value["provider"]["operations"]
    assert (
        value["limits"]
        == client.get("/api/v1/capabilities").json()["limits"]["deploymentComparison"]
    )
    document["spec"]["targets"][0]["capabilities"] = [
        "cap-" + str(i) for i in range(65)
    ]
    changed = state.projects.save(
        project["projectId"],
        right["documentId"],
        changed["revision"],
        dump_yaml(document),
        "yaml",
    )
    response = comparison(client, changed, left, right)
    assert response.status_code == 413 and response.json()["code"] == "LIMIT_EXCEEDED"


def test_declared_deployment_and_scenario_tolerances_keep_owner_and_are_not_measurements(
    client,
):
    project, left, right, _ = variants(client)
    state = client.app.state.studio
    system_id, source = next(
        (k, d)
        for k, d in project["documents"].items()
        if d["path"].endswith("/system.xdl.yaml")
    )
    system = YAML(typ="safe").load(source["content"])
    system["spec"]["timeDomains"].append(
        dict(id="wall-time", clockClass="wall", epoch="unix", rate="1", monotonic=False)
    )
    project = state.projects.save(
        project["projectId"], system_id, project["revision"], dump_yaml(system), "yaml"
    )
    deployment = YAML(typ="safe").load(
        project["documents"][right["documentId"]]["content"]
    )
    system_ref = deployment["spec"]["systemRef"]
    mapping = dict(
        id="wall-to-sim",
        sourceTimeDomainRef={**system_ref, "element": "wall-time"},
        targetTimeDomainRef={**system_ref, "element": "simulation-time"},
        mapping="offset-at-start",
        tolerance={"value": 0.001, "unit": "s"},
    )
    deployment["spec"]["timeMappings"] = [mapping]
    project = state.projects.save(
        project["projectId"],
        right["documentId"],
        project["revision"],
        dump_yaml(deployment),
        "yaml",
    )
    scenario_id, scenario = next(
        (k, YAML(typ="safe").load(d["content"]))
        for k, d in project["documents"].items()
        if d["path"].endswith("/scenario-comparison-candidate.xdl.yaml")
    )
    scenario["spec"]["timeMappings"] = [
        {
            "sourceTimeDomainId": "wall-time",
            "targetTimeDomainId": "simulation-time",
            "mapping": "offset-at-start",
            "tolerance": {"value": 0.02, "unit": "s"},
        }
    ]
    project = state.projects.save(
        project["projectId"],
        scenario_id,
        project["revision"],
        dump_yaml(scenario),
        "yaml",
    )
    before = state.projects.read(project["projectId"])
    assert state.adapter.validate(state.projects.sources(project))["valid"]
    response = comparison(client, project, left, right)
    assert response.status_code == 200, response.text
    value = response.json()
    assert value["left"]["declaredMappings"] == []
    mappings = value["right"]["declaredMappings"]
    assert len(mappings) == 2 and {m["origin"] for m in mappings} == {
        "deployment",
        "scenario",
    }
    assert [m["mappingId"] for m in mappings] == ["wall-to-sim", None]
    assert all(m["pointer"] == "/spec/timeMappings/0" for m in mappings)
    assert len({m["ownerRef"] for m in mappings}) == 2
    assert [m["tolerance"]["value"] for m in mappings] == [0.001, 0.02]
    assert all(
        m["sourceClock"].endswith("#wall-time")
        and m["targetClock"].endswith("#simulation-time")
        for m in mappings
    )
    assert value["synchronization"] == {
        "status": "unmeasured",
        "preciseLatencyAvailable": False,
    }
    assert value["fidelity"] == "unverified"
    assert state.projects.read(project["projectId"]) == before
    preflight = client.post(
        "/api/v1/projects/" + project["projectId"] + "/preflights",
        json={
            "revision": project["revision"],
            "deploymentRef": right["ref"],
            "scenarioRef": right["scenarioRefs"][0],
        },
    )
    assert preflight.status_code == 200, preflight.text
    assert preflight.json()["status"] == "blocked"
    assert client.get("/api/v1/runs").json()["items"] == []


def test_comparison_requires_session_and_rejects_foreign_origin(client):
    project, left, right, _ = variants(client)
    client.headers["Origin"] = "http://foreign.invalid"
    response = comparison(client, project, left, right)
    assert response.status_code == 403
    assert "comparisonVersion" not in response.json()
    client.headers["Origin"] = "http://testserver"
    client.cookies.clear()
    response = comparison(client, project, left, right)
    assert response.status_code == 401
    assert "comparisonVersion" not in response.json()
