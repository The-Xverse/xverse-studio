def test_atomic_revision_layout_and_external_conflict(client):
    p = client.post("/api/v1/projects", json={"name": "System α with spaces"}).json()
    pid = p["projectId"]
    doc = next(iter(p["documents"]))
    assert (
        client.put(
            f"/api/v1/projects/{pid}/documents/{doc}",
            json={"content": "invalid [", "format": "yaml"},
        ).status_code
        == 428
    )
    r = client.put(
        f"/api/v1/projects/{pid}/documents/{doc}",
        headers={"If-Match": str(p["revision"])},
        json={"content": "invalid [", "format": "yaml"},
    )
    assert r.status_code == 200, r.text
    assert r.json()["revision"] == p["revision"] + 1
    assert (
        client.put(
            f"/api/v1/projects/{pid}/documents/{doc}",
            headers={"If-Match": str(p["revision"])},
            json={"content": "overwrite", "format": "yaml"},
        ).status_code
        == 412
    )
    before = client.get(f"/api/v1/projects/{pid}").json()
    layout = client.put(
        f"/api/v1/projects/{pid}/layout",
        headers={"If-Match": str(before["presentationRevision"])},
        json={"positions": {"control": {"x": 100, "y": 10}}},
    )
    assert layout.status_code == 200, layout.text
    after = client.get(f"/api/v1/projects/{pid}").json()
    assert (
        before["documents"] == after["documents"]
        and before["revision"] == after["revision"]
    )
    store = client.app.state.studio
    path = store.projects.document_path(pid, doc)
    path.write_text("external edit")
    assert (
        client.put(
            f"/api/v1/projects/{pid}/documents/{doc}",
            headers={"If-Match": str(after["revision"])},
            json={"content": "overwrite", "format": "yaml"},
        ).status_code
        == 412
    )


def test_invalid_unknown_source_preserved_but_not_executable(client):
    p = client.post("/api/v1/projects", json={"name": "unknown"}).json()
    pid = p["projectId"]
    doc = next(iter(p["documents"]))
    content = "apiVersion: unknown/v900\nkind: System\ncustom: untouched\n"
    r = client.put(
        f"/api/v1/projects/{pid}/documents/{doc}",
        headers={"If-Match": str(p["revision"])},
        json={"content": content, "format": "yaml"},
    )
    assert r.status_code == 200
    assert r.json()["documents"][doc]["content"] == content
    pf = client.post(
        f"/api/v1/projects/{pid}/preflights", json={"revision": r.json()["revision"]}
    ).json()
    assert pf["status"] == "blocked"


def test_crlf_authored_bytes_preserved_and_admitted(client):
    p = client.post("/api/v1/projects", json={"name": "line endings"}).json()
    doc = next(iter(p["documents"]))
    crlf = p["documents"][doc]["content"].replace("\n", "\r\n")
    saved = client.put(
        f"/api/v1/projects/{p['projectId']}/documents/{doc}",
        headers={"If-Match": str(p["revision"])},
        json={"content": crlf, "format": "yaml"},
    )
    assert saved.status_code == 200, saved.text
    assert saved.json()["documents"][doc]["content"] == crlf
    pf = client.post(
        f"/api/v1/projects/{p['projectId']}/preflights",
        json={"revision": saved.json()["revision"]},
    )
    assert pf.status_code == 200 and pf.json()["status"] == "ready", pf.text


def test_portable_doc_path_collision_cannot_corrupt_committed_revision(client):
    from xverse_studio.storage.core import Problem
    import pytest

    p = client.post("/api/v1/projects", json={"name": "collision guard"}).json()
    projects = client.app.state.studio.projects
    first = next(iter(p["documents"]))

    def collide(record):
        record["documents"]["doc-collision"] = {
            **record["documents"][first],
            "path": record["documents"][first]["path"].upper(),
        }
        return record["documents"]

    with pytest.raises(Problem) as e:
        projects.mutate(p["projectId"], p["revision"], collide)
    assert e.value.code == "PROJECT_PATH_COLLISION"
    assert projects.read(p["projectId"])["revision"] == p["revision"]
    projects.assert_intact(projects.read(p["projectId"]))
