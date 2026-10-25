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
