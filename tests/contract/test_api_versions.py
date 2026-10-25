def test_error_envelope_version_and_unknown_fields(client):
    assert client.get("/api/v2/capabilities").status_code == 404
    response = client.post("/api/v1/projects", json={"name": "hello", "unknown": 1})
    assert response.status_code == 422
    body = response.json()
    assert set(["code", "message", "requestId", "retryable"]).issubset(body)
    assert all("input" not in item for item in body.get("diagnostics", []))
    spec = client.get("/api/v1/openapi.json").json()
    assert spec["info"]["title"] == "X-Verse Studio"


def test_capability_host_provider_separation(client):
    c = client.get("/api/v1/capabilities").json()
    assert c["apiVersion"] == "1.0"
    assert c["host"]["os"] in ("Linux", "Windows")
    ref = next(p for p in c["providers"] if p["providerId"] == "studio.reference")
    lite = next(p for p in c["providers"] if p["providerId"] == "xverse.lite")
    assert ref["evidenceScope"] == "owned_reference"
    assert not lite["available"]
    assert ref["supportedHostOS"] == ["Linux", "Windows"]
