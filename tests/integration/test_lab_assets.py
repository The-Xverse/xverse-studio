"""T072 read-only placement observations: synthetic inventory, never hardware admission."""

from copy import deepcopy
import json

import pytest
from ruamel.yaml import YAML

from xverse_studio.lab.assets import inventory_observation
from xverse_studio.lab import LabError, LabRegistry, validate_binding
from xverse_studio.xdl.examples import dump_yaml


class InventoryFixture:
    def __init__(self, assets=(), *, failure=False):
        self.assets = list(assets)
        self.failure = failure
        self.calls = 0

    def inventory(self):
        self.calls += 1
        if self.failure:
            raise OSError("private provider endpoint and credential must never escape")
        return deepcopy(self.assets)

    def __getattr__(self, operation):
        raise AssertionError(f"Inventory observation must not delegate {operation}")


def asset(interfaces=None, **changes):
    return {
        "assetId": "urn:fixture:bench",
        "providerId": "fixture",
        "physical": True,
        "evidenceScope": "fixture",
        "identity": {"serial": "SYNTHETIC-001", "model": "Contract bench"},
        "firmware": {"status": "observed", "version": "fixture-1.0.0"},
        "interfaces": interfaces if interfaces is not None else {},
        "capabilities": ["observe", "stimulate"],
        "available": True,
        **changes,
    }


@pytest.fixture
def placement(client):
    projects = client.app.state.studio.projects
    project = projects.create("Physical placement observation")
    yaml = YAML(typ="safe")
    deployment_id, deployment_doc = next(
        (key, doc)
        for key, doc in project["documents"].items()
        if yaml.load(doc["content"])["kind"] == "Deployment"
    )
    deployment = yaml.load(deployment_doc["content"])
    deployment["spec"]["targets"][0]["externalAssetRef"] = "urn:fixture:bench"
    deployment["spec"]["bindings"][1]["realizationClass"] = "physical"
    project = projects.save(
        project["projectId"],
        deployment_id,
        project["revision"],
        dump_yaml(deployment),
        "yaml",
    )
    system = next(
        yaml.load(doc["content"])
        for doc in project["documents"].values()
        if yaml.load(doc["content"])["kind"] == "System"
    )
    provider = InventoryFixture(
        [asset({i["id"]: i for i in system["spec"]["interfaces"]})]
    )
    client.app.state.studio.lab.providers["fixture"] = provider
    url = f"/api/v1/projects/{project['projectId']}/deployment-variants/{deployment_id}/physical-bindings"
    return project, deployment_id, provider, url


def test_canonical_binding_uses_server_inventory_and_preserves_sources(
    client, placement
):
    project, document_id, provider, url = placement
    projects = client.app.state.studio.projects
    original = projects.sources(project)
    response = client.get(url, params={"revision": project["revision"]})
    assert response.status_code == 200, response.text
    report = response.json()
    assert report["sourceValid"] is True
    assert report["inventoryComplete"] is True
    assert (report["projectId"], report["documentId"], report["revision"]) == (
        project["projectId"],
        document_id,
        project["revision"],
    )
    assert (
        report["scope"] == "read_only_placement_observation"
        and report["activeReady"] is False
    )
    assert len(report["bindings"]) == 1
    row = report["bindings"][0]
    assert row["bindingId"] == "plant-binding" and row["logicalRef"].endswith("#plant")
    assert set(row["requiredInterfaces"]) == {"command", "state"}
    assert row["assetId"] == "urn:fixture:bench"
    assert row["asset"]["identity"]["serial"] == "SYNTHETIC-001"
    assert row["asset"]["firmware"] == {
        "status": "observed",
        "version": "fixture-1.0.0",
    }
    assert row["asset"]["artifactRevision"] == {"status": "unknown"}
    assert row["readiness"] == {
        "identity": "resolved",
        "interfaces": "compatible",
        "availability": "observed",
        "metadata": "partial",
        "providerAdmission": "unavailable",
        "permission": "unknown",
        "activeOperation": "blocked",
    }
    assert (
        row["evidenceScope"] == "fixture"
        and row["activeReady"] is False
        and row["ready"] is False
    )
    assert projects.sources(projects.read(project["projectId"])) == original
    assert provider.calls == 1
    assert client.get(url).json()["bindings"] == report["bindings"]


@pytest.mark.parametrize(
    "changes,expected",
    [
        ({"identity": None}, "ASSET_IDENTITY_UNRESOLVED"),
        (
            {"identity": {"model": "Model name is not a serial"}},
            "ASSET_IDENTITY_UNRESOLVED",
        ),
        ({"available": False}, "ASSET_READINESS_UNPROVEN"),
        (
            {"interfaces": {"command": "wrong", "state": "wrong"}},
            "INTERFACE_INCOMPATIBLE",
        ),
        ({"interfaces": None}, "INTERFACE_INCOMPATIBLE"),
    ],
)
def test_unknown_identity_unavailable_and_mismatched_contracts_block(
    client, placement, changes, expected
):
    _, _, provider, url = placement
    provider.assets[0].update(changes)
    row = client.get(url).json()["bindings"][0]
    assert expected in row["diagnostics"]
    assert row["ready"] is False and row["readiness"]["activeOperation"] == "blocked"


def test_inventory_admission_text_and_fake_permissions_never_grant_authority(
    client, placement
):
    _, _, provider, url = placement
    provider.assets[0].update(
        evidenceScope="admitted_integration",
        permissionScope="destructive",
        activeReady=True,
        reservable=True,
    )
    row = client.get(url).json()["bindings"][0]
    assert row["asset"]["providerAdmission"] == "unavailable"
    assert (
        row["asset"]["permissionScope"] == "unknown"
        and row["asset"]["reservable"] is False
    )
    assert row["activeReady"] is False and row["ready"] is False
    response = client.post(
        "/api/v1/assets/urn:fixture:bench/reservations",
        json={"scope": "observe", "durationSeconds": 30},
    )
    assert (
        response.status_code == 422
        and response.json()["code"] == "PROVIDER_RESERVATION_NOT_ADMITTED"
    )


def test_inventory_public_allowlist_drops_private_payloads(client, placement):
    _, _, provider, url = placement
    provider.assets[0].update(
        endpoint="https://admin:do-not-export@private/bench",
        credentials={"private": "do-not-export"},
        privatePayload="do-not-export",
    )
    provider.assets[0]["identity"]["ownerKey"] = "do-not-export"
    provider.assets[0]["firmware"]["endpoint"] = "do-not-export"
    provider.assets[0]["interfaces"]["command"]["private"] = "do-not-export"
    for route in ("/api/v1/assets", url):
        response = client.get(route)
        assert response.status_code == 200, response.text
        assert "do-not-export" not in response.text
        assert "ownerKey" not in response.text and "privatePayload" not in response.text
    inventory = client.get("/api/v1/assets").json()["items"][0]
    assert (
        inventory["activeReady"] is False
        and inventory["firmware"]["status"] == "observed"
    )


def test_provider_failure_and_missing_asset_are_distinct_and_safe(client, placement):
    _, _, provider, url = placement
    provider.assets = []
    report = client.get(url).json()
    assert report["inventoryComplete"] is True
    assert "ASSET_UNAVAILABLE" in report["bindings"][0]["diagnostics"]
    provider.failure = True
    report = client.get(url).json()
    assert report["inventoryComplete"] is False
    assert {
        "code": "PROVIDER_INVENTORY_UNAVAILABLE",
        "providerId": "fixture",
    } in report["diagnostics"]
    assert "private provider" not in json.dumps(report)


@pytest.mark.parametrize(
    "raw",
    [
        None,
        [],
        "bad",
        {"assetId": "id"},
        {"assetId": "https://user:credential@host/a", "providerId": "fixture"},
    ],
)
def test_malformed_inventory_records_are_diagnostic_not_server_errors(
    client, placement, raw
):
    _, _, provider, url = placement
    provider.assets = [raw]
    for route in ("/api/v1/assets", url):
        response = client.get(route)
        assert response.status_code == 200, response.text
        assert any(
            d["code"] == "PROVIDER_INVENTORY_INVALID"
            for d in response.json()["diagnostics"]
        )


def test_duplicate_asset_identity_is_ambiguous_and_never_resolves(client, placement):
    _, _, provider, url = placement
    provider.assets.append(deepcopy(provider.assets[0]))
    report = client.get(url).json()
    assert any(d["code"] == "ASSET_IDENTITY_AMBIGUOUS" for d in report["diagnostics"])
    assert report["bindings"][0]["asset"] is None


def test_invalid_or_external_source_and_stale_revision_never_query_inventory(
    client, placement
):
    project, document_id, provider, url = placement
    assert (
        client.get(url, params={"revision": project["revision"] - 1}).status_code == 412
    )
    projects = client.app.state.studio.projects
    invalid = projects.save(
        project["projectId"], document_id, project["revision"], "invalid: [", "yaml"
    )
    response = client.get(url)
    assert response.status_code == 200, response.text
    assert response.json()["sourceValid"] is False and response.json()["bindings"] == []
    assert provider.calls == 0
    projects.document_path(project["projectId"], document_id).write_text(
        "external replacement"
    )
    assert client.get(url).status_code == 412
    assert provider.calls == 0 and invalid["revision"] == project["revision"] + 1


def test_wrong_kind_and_missing_document_do_not_query_inventory(client, placement):
    project, _, provider, url = placement
    system_id = next(
        key
        for key, doc in project["documents"].items()
        if YAML(typ="safe").load(doc["content"])["kind"] == "System"
    )
    prefix = url.rsplit("/", 2)[0]
    assert (
        client.get(prefix + "/" + system_id + "/physical-bindings").status_code == 422
    )
    assert client.get(prefix + "/missing/physical-bindings").status_code == 404
    assert provider.calls == 0


def test_inventory_bounds_include_malformed_records_and_diagnostics():
    provider = InventoryFixture([None] * 2000)
    registry = LabRegistry({"fixture": provider}, max_assets=150)
    report = inventory_observation(registry)
    assert report["truncated"] is True and report["items"] == []
    assert report["complete"] is False
    assert len(report["diagnostics"]) <= 100


def test_invalid_paging_does_not_contact_inventory(client, placement):
    _, _, provider, _ = placement
    assert client.get("/api/v1/assets", params={"limit": 201}).status_code == 422
    assert client.get("/api/v1/assets", params={"cursor": "invalid"}).status_code == 422
    assert provider.calls == 0


def test_malformed_binding_interfaces_raise_typed_error():
    with pytest.raises(LabError, match="^INVALID_BINDING$"):
        validate_binding(
            "system#device", asset(interfaces=[]), {"measurement": "scalar@1"}
        )


def test_saved_source_contract_changes_are_authoritative_not_inventory_inference(
    client, placement
):
    project, _, provider, url = placement
    projects = client.app.state.studio.projects
    system_id, document = next(
        (key, doc)
        for key, doc in project["documents"].items()
        if YAML(typ="safe").load(doc["content"])["kind"] == "System"
    )
    system = YAML(typ="safe").load(document["content"])
    system["spec"]["interfaces"][0]["unitSemantics"] = "V"
    saved = projects.save(
        project["projectId"], system_id, project["revision"], dump_yaml(system), "yaml"
    )
    response = client.get(url, params={"revision": saved["revision"]})
    assert response.status_code == 200, response.text
    report = response.json()
    assert report["sourceValid"] is True
    row = report["bindings"][0]
    assert row["requiredInterfaces"]["command"]["unitSemantics"] == "V"
    assert "INTERFACE_INCOMPATIBLE" in row["diagnostics"]
    assert provider.assets[0]["interfaces"]["command"]["unitSemantics"] == "1"


def test_selected_deployment_document_resolves_its_own_asset_reference(
    client, placement
):
    project, _, provider, url = placement
    projects = client.app.state.studio.projects
    deployments = client.app.state.studio.deployments
    cloned = deployments.create(
        project["projectId"], project["revision"], {"name": "Other placement"}
    )
    project, variant = cloned["project"], cloned["variant"]
    deployment = YAML(typ="safe").load(
        project["documents"][variant["documentId"]]["content"]
    )
    deployment["spec"]["targets"][0]["externalAssetRef"] = "urn:fixture:other"
    projects.save(
        project["projectId"],
        variant["documentId"],
        project["revision"],
        dump_yaml(deployment),
        "yaml",
    )
    provider.assets.append(
        {
            **deepcopy(provider.assets[0]),
            "assetId": "urn:fixture:other",
            "identity": {"serial": "SYNTHETIC-002"},
        }
    )
    second_url = (
        url.rsplit("/", 2)[0] + "/" + variant["documentId"] + "/physical-bindings"
    )
    first, second = client.get(url).json(), client.get(second_url).json()
    assert first["bindings"][0]["assetId"] == "urn:fixture:bench"
    assert second["bindings"][0]["assetId"] == "urn:fixture:other"
    assert first["bindings"][0]["logicalRef"] == second["bindings"][0]["logicalRef"]
    assert first["deploymentRef"] != second["deploymentRef"]


def test_endpoint_asset_reference_is_not_echoed_or_contacted(client, placement):
    project, document_id, provider, url = placement
    projects = client.app.state.studio.projects
    deployment = YAML(typ="safe").load(project["documents"][document_id]["content"])
    deployment["spec"]["targets"][0]["externalAssetRef"] = "https://private.lab/asset"
    projects.save(
        project["projectId"],
        document_id,
        project["revision"],
        dump_yaml(deployment),
        "yaml",
    )
    response = client.get(url)
    assert response.status_code == 200, response.text
    assert response.json()["sourceValid"] is True
    row = response.json()["bindings"][0]
    assert row["assetId"] is None and "ASSET_REFERENCE_UNRESOLVED" in row["diagnostics"]
    assert "never-echo" not in response.text and "private.lab" not in response.text


def test_unsupported_firmware_metadata_never_becomes_an_observed_revision(
    client, placement
):
    _, _, provider, url = placement
    provider.assets[0]["firmware"] = {
        "status": "unsupported",
        "version": "unconfirmed-1.0",
    }
    row = client.get(url).json()["bindings"][0]
    assert row["asset"]["firmware"]["status"] == "unknown"
    assert row["asset"]["firmware"]["version"] == "unconfirmed-1.0"
    assert row["readiness"]["activeOperation"] == "blocked"


def test_inventory_reports_partial_yielded_results_on_provider_failure(
    client, placement
):
    _, _, provider, url = placement

    def partial():
        yield provider.assets[0]
        raise OSError("private failure detail")

    provider.inventory = partial
    response = client.get("/api/v1/assets").json()
    assert len(response["items"]) == 1 and response["complete"] is False
    assert response["truncated"] is False
    report = client.get(url).json()
    assert report["inventoryComplete"] is False
    assert report["bindings"][0]["activeReady"] is False


def test_oversized_asset_metadata_is_bounded_and_explicitly_incomplete(
    client, placement
):
    _, _, provider, url = placement
    provider.assets[0]["capabilities"] = ["unsupported"] * 64 + ["stimulate"]
    provider.assets[0]["supportedOS"] = ["unsupported"] * 16 + ["Windows"]
    provider.assets[0]["interfaces"].update(
        {f"extra-{i}": "urn:fixture:scalar:v1" for i in range(100)}
    )
    response = client.get("/api/v1/assets").json()
    projected = response["items"][0]
    assert projected["capabilities"] == [] and projected["supportedOS"] == []
    assert len(projected["interfaces"]) == 64
    assert projected["observationTruncated"] is True and response["complete"] is False
    assert any(
        d["code"] == "ASSET_METADATA_LIMIT_EXCEEDED" for d in response["diagnostics"]
    )
    assert client.get(url).json()["inventoryComplete"] is False
