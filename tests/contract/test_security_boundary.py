import io
import zipfile
import base64
from fastapi.testclient import TestClient
from xverse_studio.api.app import create_app


def test_auth_origin_csrf_and_strict_fields(client):
    assert client.get("/api/v1/capabilities").status_code == 200
    assert (
        client.get(
            "/api/v1/capabilities", headers={"Origin": "https://evil.test"}
        ).status_code
        == 403
    )
    assert (
        client.post(
            "/api/v1/projects", json={"name": "safe"}, headers={"X-CSRF-Token": "wrong"}
        ).status_code
        == 403
    )
    r = client.post("/api/v1/projects", json={"name": "safe", "command": "touch nope"})
    assert r.status_code == 422
    assert all(k in r.json() for k in ["code", "message", "requestId", "retryable"])
    with TestClient(client.app, base_url="http://testserver") as other:
        assert other.get("/api/v1/projects").status_code == 401


def test_bootstrap_one_use(client):
    assert (
        client.post(
            "/api/v1/session", json={"bootstrapToken": "test-bootstrap"}
        ).status_code
        == 401
    )


def test_archive_portable_path_rejection(client):
    for path in [
        "../outside",
        "/etc/hello",
        "C:/escape",
        "C:escape",
        "a\\b",
        "x/CON.txt",
        "x/name.",
        "x/a:ads",
        "//server/share",
    ]:
        b = io.BytesIO()
        with zipfile.ZipFile(b, "w") as z:
            z.writestr(path, "innocent")
        r = client.post(
            "/api/v1/projects/imports",
            json={"archiveBase64": base64.b64encode(b.getvalue()).decode()},
        )
        assert r.status_code in (413, 422), (path, r.text)


def test_symlink_and_case_collision_zip_rejected(client):
    for names in [("xdl/A.yaml", "xdl/a.yaml"), ("xdl/link",)]:
        b = io.BytesIO()
        with zipfile.ZipFile(b, "w") as z:
            for n in names:
                info = zipfile.ZipInfo(n)
                if n.endswith("link"):
                    info.external_attr = 0o120777 << 16
                z.writestr(info, "outside")
        assert (
            client.post(
                "/api/v1/projects/imports",
                json={"archiveBase64": base64.b64encode(b.getvalue()).decode()},
            ).status_code
            == 422
        )


def test_private_host_paths_rejected_on_export_without_echo(client):
    p = client.post(
        "/api/v1/projects", json={"name": "private portable metadata"}
    ).json()
    store = client.app.state.studio.store
    record = store.get("project", p["projectId"])
    record["supportingFiles"]["README.md"] = (
        "Private path /home/synthetic-private-marker/project"
    )
    store.put("project", p["projectId"], record)
    r = client.post(
        f"/api/v1/projects/{p['projectId']}/exports",
        json={"revision": p["revision"]},
        headers={"Idempotency-Key": "private-export"},
    )
    assert r.status_code == 422 and r.json()["code"] == "HOST_BINDING_NOT_PORTABLE"
    assert "synthetic-private-marker" not in r.text
    assert (
        store.get("project", p["projectId"])["supportingFiles"]["README.md"]
        == record["supportingFiles"]["README.md"]
    )
