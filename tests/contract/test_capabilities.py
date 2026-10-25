import copy
import pytest
from xverse_studio.providers.registry import descriptors, admit_descriptor
from xverse_studio.storage.core import Problem


def test_provider_admission_rejects_versions_missing_identity_and_unscoped_operations():
    provider = next(d for d in descriptors() if d["providerId"] == "studio.reference")
    assert admit_descriptor(provider) == provider
    changed = copy.deepcopy(provider)
    changed["contractVersion"] = "2.0"
    with pytest.raises(Problem, match="incompatible"):
        admit_descriptor(changed)
    changed = copy.deepcopy(provider)
    changed["implementationDigest"] = None
    with pytest.raises(Problem):
        admit_descriptor(changed)
    changed = copy.deepcopy(provider)
    changed["capabilityRecords"] = [{"kind": "pause"}]
    with pytest.raises(Problem):
        admit_descriptor(changed)


def test_incompatible_api_contract_rejected_before_mutation(client):
    response = client.post(
        "/api/v1/projects",
        headers={"X-Studio-Contract-Version": "2.0"},
        json={"name": "never created"},
    )
    assert response.status_code == 426
    assert response.json()["code"] == "API_VERSION_INCOMPATIBLE"
    assert client.get("/api/v1/projects").json()["items"] == []


def test_capabilities_advertise_the_admitted_xdl_api_versions(client):
    from xverse_studio.xdl import XDLAdapter

    capabilities = client.get("/api/v1/capabilities").json()
    # The advertised list is the authoritative validator's own admission.
    assert capabilities["xdl"] == {"apiVersions": XDLAdapter().identity["apiVersions"]}


def test_semantic_edits_refuse_a_project_with_a_non_admitted_xdl_version(client):
    import base64
    import importlib.util
    from pathlib import Path

    path = Path(__file__).resolve().parents[1] / "fixtures/projects/create_catalog_archive.py"
    spec = importlib.util.spec_from_file_location("catalog_archive_fixture", path)
    fixture = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(fixture)
    project = client.post(
        "/api/v1/projects/imports", json={"archiveBase64": fixture.archive("unsupported")}
    ).json()
    response = client.post(
        f"/api/v1/projects/{project['projectId']}/edits",
        headers={"If-Match": str(project["revision"])},
        json={
            "baseRevision": project["revision"],
            "edits": [{"kind": "add_element", "templateId": "telemetry-service", "elementId": "gateway"}],
        },
    )
    assert response.status_code == 422 and response.json()["code"] == "MODEL_INVALID"
    assert client.get(f"/api/v1/projects/{project['projectId']}").json()["revision"] == project["revision"]
    assert base64  # the archive itself was accepted inertly; only execution-relevant edits are refused
