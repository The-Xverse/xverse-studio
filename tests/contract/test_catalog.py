import pytest

from xverse_studio.catalog import Catalog
from xverse_studio.storage.core import Problem, Store


def test_catalog_filters_and_immutable_component_identity(tmp_path):
    catalog = Catalog(Store(tmp_path))
    entries = catalog.list(kind="component")["items"]
    assert {entry["name"] for entry in entries} >= {"reference-controller", "reference-plant"}
    assert all(entry["digest"].startswith("sha256:") and entry["provenance"] for entry in entries)
    plant = next(entry for entry in entries if entry["name"] == "reference-plant")
    assert plant["resource"]["kind"] == "Component"
    assert catalog.get(plant["entryId"])["digest"] == plant["digest"]
    assert catalog.list(kind="component", role="plant")["items"]
    assert not catalog.list(kind="component", role="nonexistent-role")["items"]


def test_artifact_registration_is_inert_idempotent_and_records_unavailability(tmp_path):
    store = Store(tmp_path)
    catalog = Catalog(store)
    body = {"name": "Uninstalled model", "version": "1.0.0", "artifactKind": "model", "digest": "sha256:" + "a" * 64,
            "originRef": "urn:example:missing-model", "providerIds": ["xverse.lite"], "apiVersions": ["xverse.io/xdl/v1alpha1"],
            "license": "LicenseRef-restricted", "limitations": ["Not distributed in this workspace."]}
    first = catalog.register(body, "catalog-review", "artifact-once")
    assert catalog.register(body, "catalog-review", "artifact-once") == first
    assert first["executionAllowed"] is False
    assert first["availability"] == "unavailable"
    assert store.all("run") == []
    with pytest.raises(Problem) as conflict:
        catalog.register({**body, "name": "Different request"}, "catalog-review", "artifact-once")
    assert conflict.value.code == "IDEMPOTENCY_CONFLICT"


@pytest.mark.parametrize("changes", [{"digest": "latest"}, {"originRef": "file:///private/model"}, {"script": "run-code"},
                                      {"originRef": "https://user:synthetic-secret@example.invalid/model"}, {"originRef": "https://[broken"},
                                      {"version": "1.0"}, {"version": "latest"}, {"version": "1.0.0-"}])
def test_artifact_registration_rejects_unsafe_or_unpinned_metadata(tmp_path, changes):
    catalog = Catalog(Store(tmp_path))
    body = {"name": "Model", "version": "1.0.0", "artifactKind": "model", "digest": "sha256:" + "b" * 64,
            "originRef": "urn:example:model", "providerIds": ["studio.reference"], "apiVersions": ["xverse.io/xdl/v1alpha1"]}
    with pytest.raises((Problem, ValueError)):
        catalog.register({**body, **changes}, "catalog-review", "unsafe-artifact")


def test_malformed_artifact_uri_has_typed_http_error_and_creates_no_metadata(client):
    response = client.post("/api/v1/catalog/artifacts", headers={"Idempotency-Key": "malformed-origin"}, json={
        "name": "Malformed source", "version": "1.0.0", "artifactKind": "model", "digest": "sha256:" + "d" * 64,
        "originRef": "https://[broken", "providerIds": [], "apiVersions": []})
    assert response.status_code == 422
    assert response.json()["code"] == "ARTIFACT_ORIGIN_UNSUPPORTED"
    assert client.app.state.studio.store.all("catalogArtifact") == []


@pytest.mark.parametrize("version", ["1.0", "latest", "v1.0.0"])
def test_api_refuses_invalid_artifact_versions_without_metadata(client, version):
    body = {"name": "Model", "version": version, "artifactKind": "model", "digest": "sha256:" + "c" * 64,
            "originRef": "urn:example:model"}
    response = client.post("/api/v1/catalog/artifacts", headers={"Idempotency-Key": "bad-" + version}, json=body)
    assert response.status_code == 422
    assert not [e for e in client.get("/api/v1/catalog").json()["items"] if e.get("kind") == "artifact"]


import importlib.util as _util
from pathlib import Path as _Path

_spec = _util.spec_from_file_location(
    "catalog_fixtures", _Path(__file__).resolve().parents[1] / "fixtures/catalog/catalog_fixtures.py"
)
catalog_fixtures = _util.module_from_spec(_spec)
_spec.loader.exec_module(catalog_fixtures)


@pytest.mark.parametrize("name", sorted(catalog_fixtures.UNTRUSTED_REGISTRATIONS))
def test_untrusted_form_metadata_is_stored_as_inert_text(client, name):
    body = catalog_fixtures.registration(name)
    response = client.post("/api/v1/catalog/artifacts", headers={"Idempotency-Key": "untrusted-" + name}, json=body)
    assert response.status_code == 201, response.text
    entry = response.json()
    # Exact bytes are kept as data; nothing interprets, executes or downloads them.
    assert entry["name"] == body["name"]
    assert body["limitations"][0] in entry["limitations"]
    assert entry["executionAllowed"] is False and entry["availability"] == "unavailable"
    assert client.get("/api/v1/runs").json()["items"] == []


def test_definition_and_instance_identities_are_distinct_and_the_definition_is_unchanged():
    from xverse_studio.xdl import XDLAdapter, examples
    from xverse_studio.xdl.edits import semantic_edits
    from ruamel.yaml import YAML

    documents = examples()[0]["documents"]
    updated = semantic_edits(documents, [
        {"kind": "add_element", "templateId": "reference-plant", "elementId": "plant-two", "nodeId": "plant-node"},
        {"kind": "add_element", "templateId": "reference-plant", "elementId": "plant-three"},
    ])
    assert XDLAdapter().validate(updated)["valid"]
    instances = YAML(typ="safe").load(updated["system.xdl.yaml"])["spec"]["componentInstances"]
    plants = [i for i in instances if i["componentRef"]["name"] == "reference-plant"]
    assert {i["id"] for i in plants} == {"plant", "plant-two", "plant-three"}
    assert len({tuple(sorted(i["componentRef"].items())) for i in plants}) == 1
    assert updated["plant.xdl.yaml"] == documents["plant.xdl.yaml"]


def test_role_realization_and_placement_are_independent_choices():
    from xverse_studio.xdl import XDLAdapter, examples
    from xverse_studio.xdl.edits import semantic_edits
    from ruamel.yaml import YAML

    documents = examples()[0]["documents"]
    # A plant definition placed on the controller-role node: the role is the node's, not the catalog's.
    placed = semantic_edits(documents, [
        {"kind": "add_element", "templateId": "reference-plant", "elementId": "plant-two", "nodeId": "controller-node"}])
    assert XDLAdapter().validate(placed)["valid"]
    instance = next(i for i in YAML(typ="safe").load(placed["system.xdl.yaml"])["spec"]["componentInstances"]
                    if i["id"] == "plant-two")
    assert instance["nodeId"] == "controller-node"
    assert set(instance) == {"id", "componentRef", "nodeId"}  # no role or realization copied
    # Placement alone creates no realization.
    assert placed["deployment.xdl.yaml"] == documents["deployment.xdl.yaml"]
    # Unplaced remains a valid, distinct choice.
    unplaced = semantic_edits(documents, [
        {"kind": "add_element", "templateId": "reference-plant", "elementId": "plant-two"}])
    assert "nodeId" not in next(i for i in YAML(typ="safe").load(unplaced["system.xdl.yaml"])["spec"]["componentInstances"]
                                if i["id"] == "plant-two")
    # Realization is chosen separately and does not alter placement.
    realized = semantic_edits(placed, [
        {"kind": "add_binding", "bindingId": "plant-two-binding", "elementId": "plant-two",
         "targetId": "reference-target", "realizationClass": "virtual"}])
    assert realized["system.xdl.yaml"] == placed["system.xdl.yaml"]
    binding = next(b for b in YAML(typ="safe").load(realized["deployment.xdl.yaml"])["spec"]["bindings"]
                   if b["id"] == "plant-two-binding")
    assert binding["realizationClass"] == "virtual"


def test_an_existing_instance_identity_cannot_be_reused():
    from xverse_studio.xdl import XDLRejected, examples
    from xverse_studio.xdl.edits import semantic_edits

    with pytest.raises(XDLRejected) as error:
        semantic_edits(examples()[0]["documents"], [
            {"kind": "add_element", "templateId": "reference-plant", "elementId": "plant"}])
    assert error.value.code == "IDENTITY_CONFLICT"


def test_artifact_versions_are_distinct_immutable_identities(client):
    body = catalog_fixtures.registration("none", name="Versioned model")
    first = client.post("/api/v1/catalog/artifacts", headers={"Idempotency-Key": "v1"}, json=body).json()
    second = client.post("/api/v1/catalog/artifacts", headers={"Idempotency-Key": "v2"},
                         json={**body, "version": "1.2.4"}).json()
    assert first["entryId"] != second["entryId"]
    assert first["metadataDigest"] != second["metadataDigest"]
    for entry in (first, second):
        fetched = client.get("/api/v1/catalog/" + entry["entryId"]).json()
        assert fetched["version"] == entry["version"] and fetched["executionAllowed"] is False


def test_untrusted_configuration_values_are_stored_as_data_not_interpreted():
    from io import StringIO
    from ruamel.yaml import YAML
    from xverse_studio.xdl import XDLAdapter, examples
    from xverse_studio.xdl.edits import semantic_edits

    documents = dict(examples()[0]["documents"])
    plant = YAML(typ="safe").load(documents["plant.xdl.yaml"])
    plant["spec"]["parameters"] = [{"id": "label", "valueType": "string", "unitSemantics": "1",
                                    "mutability": "configuration", "description": "<b>untrusted</b>"}]
    out = StringIO()
    YAML().dump(plant, out)
    documents["plant.xdl.yaml"] = out.getvalue()
    markup = "<img src=x onerror=alert(1)>{{constructor}}"
    updated = semantic_edits(documents, [{"kind": "add_element", "templateId": "reference-plant",
                                          "elementId": "plant-two", "parameterValues": {"label": markup}}])
    assert XDLAdapter().validate(updated)["valid"]
    instance = next(i for i in YAML(typ="safe").load(updated["system.xdl.yaml"])["spec"]["componentInstances"]
                    if i["id"] == "plant-two")
    assert instance["parameterValues"] == {"label": markup}
