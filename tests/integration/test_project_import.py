import base64
import io
import zipfile


def test_project_exchange_preserves_sources_layout_and_no_execution(client):
    p = client.post("/api/v1/projects", json={"name": "Portable System Ω"}).json()
    source = {id: d["content"] for id, d in p["documents"].items()}
    response = client.put(
        f"/api/v1/projects/{p['projectId']}/layout",
        headers={"If-Match": str(p["presentationRevision"])},
        json={"positions": {"controller": {"x": 42.0, "y": 24.0}}},
    )
    assert response.status_code == 200, response.text
    op = client.post(
        f"/api/v1/projects/{p['projectId']}/exports",
        headers={"Idempotency-Key": "export"},
        json={"revision": p["revision"]},
    )
    assert op.status_code == 202, op.text
    archive = client.get(op.json()["result"]["downloadUrl"])
    assert archive.status_code == 200
    files = zipfile.ZipFile(io.BytesIO(archive.content))
    assert "owner.key" not in files.namelist()
    imported = client.post(
        "/api/v1/projects/imports",
        json={"archiveBase64": base64.b64encode(archive.content).decode()},
    )
    assert imported.status_code == 201, imported.text
    copy = imported.json()
    assert copy["projectId"] != p["projectId"]
    assert sorted(d["content"] for d in copy["documents"].values()) == sorted(
        source.values()
    )
    assert copy["layout"]["positions"]["controller"]["x"] == 42.0
    a = client.post(
        f"/api/v1/projects/{p['projectId']}/compilations",
        json={"revision": p["revision"]},
    ).json()
    b = client.post(
        f"/api/v1/projects/{copy['projectId']}/compilations",
        json={"revision": copy["revision"]},
    ).json()
    assert a["planDigest"] == b["planDigest"]
    assert client.get("/api/v1/runs").json()["items"] == []
