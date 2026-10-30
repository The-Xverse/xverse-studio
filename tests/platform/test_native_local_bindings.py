"""Actual original owned native backend death at binding publication boundaries."""

from concurrent.futures import ThreadPoolExecutor
import json
import os
from pathlib import Path
import socket
import subprocess
import sys

import httpx
import psutil
import pytest

from test_native_recovery import eventually
from xverse_studio.projects.local_bindings import LocalBindingsUpdate
from xverse_studio.projects.service import Projects
from xverse_studio.storage.core import Store, digest
from xverse_studio.xdl import XDLAdapter


def authenticate(api, root):
    eventually(lambda: api.get("/api/v1/session").status_code in (200, 401))
    bootstrap = json.loads((root / "bootstrap.json").read_text())
    result = api.post("/api/v1/session", json={"bootstrapToken": bootstrap["bootstrapToken"]})
    assert result.status_code == 200, result.text
    api.headers["X-CSRF-Token"] = result.json()["csrfToken"]


@pytest.mark.parametrize("lane", ["before-head", "after-commit"])
def test_native_restart_never_adopts_prepared_bytes_or_replays_a_committed_save(tmp_path, lane):
    root, witness = tmp_path / "binding-owner-Ω", tmp_path / "witness.json"
    projects = Projects(Store(root), XDLAdapter())
    project = projects.create("Native binding persistence")
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        port = sock.getsockname()[1]
    url = f"http://127.0.0.1:{port}"
    fixture = Path(__file__).resolve().parents[1] / "fixtures/host/local_binding_publication.py"
    command = [sys.executable, "-I", str(fixture), "--data-dir", str(root), "--port", str(port), "--witness", str(witness), "--lane", lane]
    child = subprocess.Popen(command, stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    values = [{"bindingId": "model", "kind": "artifact", "reference": "urn:fixture:model", "providerId": "uninstalled.fixture", "path": str(tmp_path / "uncontacted.bin")}]
    assert LocalBindingsUpdate(bindings=values).bindings
    try:
        with httpx.Client(base_url=url, headers={"Origin": url}, timeout=20) as api:
            authenticate(api, root)
            route = f"/api/v1/projects/{project['projectId']}/local-bindings"
            with ThreadPoolExecutor(max_workers=1) as pool:
                request = pool.submit(api.put, route, headers={"If-Match": "0"}, json={"bindings": values})
                eventually(lambda: witness.is_file(), timeout=15)
                observed = json.loads(witness.read_text())
                process = psutil.Process(child.pid)
                assert observed["pid"] == child.pid and observed["uid"] == os.getuid()
                assert process.ppid() == os.getpid() and process.uids().real == os.getuid()
                assert process.create_time() == observed["birth"] and digest(process.cmdline()) == observed["argvDigest"] == digest(command)
                prepared = list((root / "projects" / project["projectId"] / "local-bindings").glob("*.json"))
                assert len(prepared) == 1
                original = prepared[0].read_bytes()
                child.kill()
                assert child.wait(timeout=5) != 0
                with pytest.raises(httpx.HTTPError):
                    request.result(timeout=5)
            child = subprocess.Popen([sys.executable, "-I", "-m", "xverse_studio.host.launcher", "--data-dir", str(root), "--port", str(port)],
                                     stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            authenticate(api, root)
            current = api.get(route)
            assert current.status_code == 200, current.text
            expected = 0 if lane == "before-head" else 1
            assert current.json()["bindingRevision"] == expected and current.json()["executionAllowed"] is False
            assert current.json()["bindings"] == ([] if expected == 0 else values)
            retry = api.put(route, headers={"If-Match": "0"}, json={"bindings": values})
            assert retry.status_code == (200 if expected == 0 else 412), retry.text
            assert api.get(route).json()["bindingRevision"] == 1 and prepared[0].read_bytes() == original
            assert api.get("/api/v1/runs").json()["items"] == []
            assert not (tmp_path / "uncontacted.bin").exists()
    finally:
        if child.poll() is None:
            child.terminate()
            child.wait(timeout=10)
