"""Externally changed authored files must not bypass source read bounds."""

from pathlib import Path

import pytest

from xverse_studio.storage.core import Problem


def project_service(client):
    project = client.post("/api/v1/projects", json={"name": "Bounded source"}).json()
    service = client.app.state.studio.projects
    return project, service


def test_project_read_does_not_use_unbounded_path_read_bytes(client, monkeypatch):
    project, service = project_service(client)

    def unbounded(*args, **kwargs):
        raise AssertionError("Unbounded project read_bytes is forbidden")

    monkeypatch.setattr(Path, "read_bytes", unbounded)
    assert service.read(project["projectId"])["documents"] == project["documents"]


def test_oversized_external_source_is_preserved_and_refused(client):
    project, service = project_service(client)
    docid = next(iter(project["documents"]))
    file = service.document_path(project["projectId"], docid)
    payload = b"# externally changed\n" + b"x" * (1024 * 1024)
    file.write_bytes(payload)
    with pytest.raises(Problem) as rejected:
        service.read(project["projectId"])
    assert rejected.value.code == "REVISION_CONFLICT"
    assert file.read_bytes() == payload
    assert (
        service.store.get("project", project["projectId"])["revision"]
        == project["revision"]
    )


def test_invalid_utf8_and_managed_tree_symlink_have_typed_no_effect_failure(client):
    project, service = project_service(client)
    docid = next(iter(project["documents"]))
    file = service.document_path(project["projectId"], docid)
    file.write_bytes(b"\xff\xfe")
    with pytest.raises(Problem) as rejected:
        service.read(project["projectId"])
    assert rejected.value.code == "PROJECT_UNAVAILABLE"
    file.unlink()
    foreign = service.store.root / "private-material"
    foreign.write_bytes(b"private material must not become authored XDL")
    file.symlink_to(foreign)
    with pytest.raises(Problem) as rejected:
        service.read(project["projectId"])
    assert rejected.value.code == "PROJECT_UNAVAILABLE"
    assert foreign.read_bytes() == b"private material must not become authored XDL"


def test_external_source_is_not_reported_as_a_saved_revision(client):
    project, service = project_service(client)
    docid = next(iter(project["documents"]))
    path = service.document_path(project["projectId"], docid)
    changed = b"# uncommitted external edit\n" + path.read_bytes()
    path.write_bytes(changed)
    response = client.get(f"/api/v1/projects/{project['projectId']}")
    assert response.status_code == 200, response.text
    assert response.json()["sourceIntegrity"] == "modified"
    diagnostic = response.json()["sourceDiagnostics"][0]
    assert diagnostic["code"] == "REVISION_CONFLICT"
    assert diagnostic["documentId"] == docid
    assert diagnostic["expectedDigest"] != diagnostic["actualDigest"]
    assert response.json()["documents"][docid]["content"] == changed.decode()
    assert path.read_bytes() == changed
    assert service.store.get("project", project["projectId"])["revision"] == 1


def test_external_growth_cannot_bypass_complete_project_read_budget(client):
    service = client.app.state.studio.projects
    project = service.create(
        "Aggregate source bound",
        documents={
            f"source-{i}.xdl.yaml": "# retained invalid draft\n" for i in range(17)
        },
    )
    payload = b"#" + b"x" * (1024 * 1024 - 1)
    files = [
        service.document_path(project["projectId"], docid)
        for docid in project["documents"]
    ]
    for path in files:
        path.write_bytes(payload)
    with pytest.raises(Problem) as rejected:
        service.read(project["projectId"])
    assert rejected.value.code == "REVISION_CONFLICT"
    assert all(path.stat().st_size == len(payload) for path in files)
    assert service.store.get("project", project["projectId"])["revision"] == 1
