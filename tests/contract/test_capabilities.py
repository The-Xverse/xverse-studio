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
