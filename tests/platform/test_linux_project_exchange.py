"""T048: actual native HTTP workspaces exchange portable XDL without host authority."""

import base64
from contextlib import contextmanager
import io
import json
import socket
import subprocess
import sys
import time
import zipfile

import httpx
import pytest
from ruamel.yaml import YAML

from xverse_studio.xdl import XDLAdapter, examples
from xverse_studio.xdl.examples import dump_yaml


@contextmanager
def native_workspace(root):
    with socket.socket() as socket_:
        socket_.bind(("127.0.0.1", 0))
        port = socket_.getsockname()[1]
    url = f"http://127.0.0.1:{port}"
    child = subprocess.Popen(
        [sys.executable, "-I", "-m", "xverse_studio.host.launcher", "--data-dir", str(root), "--port", str(port)],
        stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
    )
    client = httpx.Client(base_url=url, headers={"Origin": url}, timeout=5)
    try:
        deadline = time.monotonic() + 15
        while time.monotonic() < deadline:
            assert child.poll() is None, "The original native launcher exited before readiness"
            try:
                if client.get("/api/v1/session").status_code == 401:
                    break
            except httpx.HTTPError:
                pass
            time.sleep(.05)
        else:
            raise AssertionError("The owned native workspace did not become ready")
        bootstrap = json.loads((root / "bootstrap.json").read_text())
        response = client.post("/api/v1/session", json={"bootstrapToken": bootstrap["bootstrapToken"]})
        assert response.status_code == 200, response.text
        client.headers["X-CSRF-Token"] = response.json()["csrfToken"]
        yield client
    finally:
        client.close()
        if child.poll() is None:
            child.terminate()
            try:
                child.wait(timeout=10)
            except subprocess.TimeoutExpired:
                child.kill()
                child.wait(timeout=5)
        assert child.poll() is not None


def source_documents(physical):
    documents = dict(examples()[0]["documents"])
    if physical:
        deployment = YAML(typ="safe").load(documents["deployment.xdl.yaml"])
        next(binding for binding in deployment["spec"]["bindings"] if binding["id"] == "plant-binding")["realizationClass"] = "physical"
        deployment["spec"]["targets"][0]["externalAssetRef"] = "urn:fixture:unadmitted-process-bench"
        documents["deployment.xdl.yaml"] = dump_yaml(deployment)
    documents["Système Ω with spaces.xdl.yaml"] = documents.pop("system.xdl.yaml")
    return {"xdl/" + name: ("# Authored Ω source\n" + text).replace("\n", "\r\n")
            for name, text in documents.items()}


def portable_archive(documents):
    manifest = {"formatVersion": "1.0", "name": "Portable Process Ω",
                "resources": [{"path": name, "format": "yaml"} for name in documents],
                "profiles": [], "layoutFiles": ["layout/model.json"],
                "org.example.opaque": {"preserve": ["unknown metadata", 42]}}
    data = io.BytesIO()
    with zipfile.ZipFile(data, "w") as bundle:
        bundle.writestr("project.studio.json", json.dumps(manifest))
        bundle.writestr("layout/model.json", json.dumps({"positions": {"plant": {"x": 32.0, "y": 64.0}}}))
        for name, text in documents.items():
            bundle.writestr(name, text.encode())
    return base64.b64encode(data.getvalue()).decode()


def compile_project(client, project, physical):
    response = client.post(f"/api/v1/projects/{project['projectId']}/compilations", json={"revision": project["revision"]})
    assert response.status_code == 200, response.text
    report = response.json()
    if physical:
        assert report["valid"] is False and report["plan"] is None
        assert report["planDigest"] is None and report["semanticDigest"] is None
        assert {row["code"] for row in report["diagnostics"]} == {"XDL1-PLAN-REALIZATION-UNSUPPORTED"}
    else:
        assert report["valid"] and report["planDigest"] and report["semanticDigest"], report["diagnostics"]
    return response.json()


def sources(project):
    return {doc["path"]: doc["content"] for doc in project["documents"].values()}


@pytest.mark.parametrize("physical", [False, True], ids=["owned-reference", "unadmitted-physical-binding"])
def test_native_exchange_reopen_line_endings_and_host_bindings_preserve_identity(tmp_path, physical):
    original_root, target_root = (tmp_path / name for name in ("Source workspace Ω with spaces", "Target workspace 制御"))
    documents = source_documents(physical)
    original_archive = portable_archive(documents)
    with native_workspace(original_root) as source:
        response = source.post("/api/v1/projects/imports", json={"archiveBase64": original_archive})
        assert response.status_code == 201, response.text
        original = response.json()
        assert sources(original) == documents
        validation = source.post(f"/api/v1/projects/{original['projectId']}/validations", json={"revision": original["revision"]})
        assert validation.status_code == 200 and validation.json()["valid"], validation.text
        compiled = compile_project(source, original, physical)
        original_cookie = source.cookies.get("studio_session")
        private = original_root / "private-host-binding.json"
        private.write_text('{"localOnly":"synthetic-private-host-material"}')
        exported = source.post(f"/api/v1/projects/{original['projectId']}/exports",
                               headers={"Idempotency-Key": "native-exchange"}, json={"revision": original["revision"]})
        assert exported.status_code == 202, exported.text
        exported_bytes = source.get(exported.json()["result"]["downloadUrl"]).content
        with zipfile.ZipFile(io.BytesIO(exported_bytes)) as bundle:
            assert all(bundle.read(name).decode() == text for name, text in documents.items())
            assert "private-host-binding.json" not in bundle.namelist() and "studio.sqlite" not in bundle.namelist()
        assert b"synthetic-private-host-material" not in exported_bytes
        assert source.get("/api/v1/runs").json()["items"] == []

    # The same exact sources also use the actual pinned CLI with explicit schemas.
    cli_root = tmp_path / "CLI inputs Ω"
    paths = []
    for name, text in documents.items():
        path = cli_root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(text.encode())
        paths.append(str(path))
    schema_args = [part for schema in XDLAdapter().profile_schema_paths for part in ("--profile-schema", schema)]
    result = subprocess.run([sys.executable, "-I", "-m", "xverse_xdl", "experiment", "compile", "--format", "json",
                             *schema_args, *paths], capture_output=True, text=True, timeout=30)
    assert (result.returncode == 0) is (not physical), result.stderr
    cli = json.loads(result.stdout)
    assert cli["valid"] == compiled["valid"] and cli["plan"] == compiled["plan"]
    assert {row["code"] for row in cli["diagnostics"]} == {row["code"] for row in compiled["diagnostics"]}

    with native_workspace(target_root) as target:
        foreign = target.get("/api/v1/projects", headers={"Cookie": "studio_session=" + original_cookie})
        assert foreign.status_code == 401  # another root's session confers no authority
        response = target.post("/api/v1/projects/imports", json={"archiveBase64": base64.b64encode(exported_bytes).decode()})
        assert response.status_code == 201, response.text
        imported = response.json()
        assert imported["projectId"] != original["projectId"] and sources(imported) == documents
        assert imported["layout"] == original["layout"]
        assert imported["manifest"]["org.example.opaque"] == original["manifest"]["org.example.opaque"]
        assert "Host-local bindings require revalidation." in imported["manifest"]["provenance"]["limitations"]
        assert compile_project(target, imported, physical)["plan"] == compiled["plan"]
        preflight = target.post(f"/api/v1/projects/{imported['projectId']}/preflights", json={"revision": imported["revision"]})
        assert preflight.status_code == 200, preflight.text
        if physical:
            assert preflight.json()["status"] == "blocked"
            assert "XDL1-PLAN-REALIZATION-UNSUPPORTED" in {row["code"] for row in preflight.json()["diagnostics"]}
        else:
            assert preflight.json()["status"] == "ready"
        document_id = next(key for key, doc in imported["documents"].items() if "Système" in doc["path"])
        text = imported["documents"][document_id]["content"].replace("\r\n", "\n")
        changed = target.put(f"/api/v1/projects/{imported['projectId']}/documents/{document_id}",
                             headers={"If-Match": str(imported["revision"])}, json={"content": text, "format": "yaml"})
        assert changed.status_code == 200, changed.text
        imported = changed.json()
        assert imported["documents"][document_id]["content"] == text
        assert compile_project(target, imported, physical)["plan"] == compiled["plan"]
        assert target.get("/api/v1/runs").json()["items"] == []
    with native_workspace(target_root) as reopened:
        persisted = reopened.get("/api/v1/projects/" + imported["projectId"]).json()
        assert sources(persisted) == sources(imported)
        assert compile_project(reopened, persisted, physical)["plan"] == compiled["plan"]
        assert reopened.get("/api/v1/runs").json()["items"] == []
    assert private.read_text() == '{"localOnly":"synthetic-private-host-material"}'
    assert not (target_root / private.name).exists()
