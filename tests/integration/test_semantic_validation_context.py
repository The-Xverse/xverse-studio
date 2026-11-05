"""Semantic transactions retain the actual project's admitted schema context."""

import json
from pathlib import Path

import pytest

from xverse_studio.xdl import XDLAdapter


@pytest.mark.parametrize("operation", ["binding", "semantic_edit"])
def test_changed_admitted_schema_refuses_semantic_rewrite_without_advancing_source(client, tmp_path, operation):
    adapter = client.app.state.studio.adapter
    schema = tmp_path / "admitted-experiment.schema.json"
    original = Path(adapter.profile_schema_paths[0]).read_bytes()
    schema.write_bytes(original)
    adapter.profile_schema_paths = (str(schema), *adapter.profile_schema_paths[1:])
    response = client.post("/api/v1/projects", json={"name": "Exact admitted validation context"})
    assert response.status_code == 201
    project = response.json()
    pid, revision = project["projectId"], project["revision"]
    sources = client.app.state.studio.projects.sources(project)
    assert adapter.validate(sources)["valid"]
    variants = client.get(f"/api/v1/projects/{pid}/deployment-variants").json()
    variant = variants["items"][0]
    changed_schema = json.loads(original)
    changed_schema["not"] = {}
    schema.write_text(json.dumps(changed_schema))
    assert not adapter.validate(sources)["valid"]
    # A fresh default adapter would accept the same bytes. It is the wrong
    # authority for this application's already-admitted schema selection.
    assert XDLAdapter().validate(sources)["valid"]
    before_revisions = client.app.state.studio.store.all("revision")
    if operation == "binding":
        response = client.patch(
            f"/api/v1/projects/{pid}/deployment-variants/{variant['documentId']}",
            headers={"If-Match": str(revision)},
            json={"baseRevision": revision, "bindingId": "plant-binding", "realizationClass": "virtual"},
        )
    else:
        response = client.post(
            f"/api/v1/projects/{pid}/edits",
            headers={"If-Match": str(revision)},
            json={"baseRevision": revision, "edits": [{"kind": "set_parameter", "parameterId": "gain", "value": .4}]},
        )
    assert response.status_code == 422, response.text
    assert response.json()["code"] == "MODEL_INVALID"
    current = client.get(f"/api/v1/projects/{pid}").json()
    assert current["revision"] == revision and current["documents"] == project["documents"]
    assert client.app.state.studio.store.all("revision") == before_revisions
    assert client.get("/api/v1/runs").json()["items"] == []
    schema.write_bytes(original)
    assert adapter.validate(sources)["valid"]
