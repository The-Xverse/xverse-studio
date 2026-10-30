"""Actual Autoverse enrollment failures must not disable native Studio authoring."""

import json
import os
from pathlib import Path
import socket
import subprocess
import sys
import time

import httpx
import pytest


@pytest.mark.parametrize("mode", ["missing-tools", "missing-platform-build"])
def test_requested_autoverse_unavailability_preserves_native_authoring(tmp_path, mode):
    receipt = os.environ.get("STUDIO_AUTOVERSE_TEST_INSTALLATION")
    assert receipt, "An explicit actual Autoverse receipt is required"
    enrolled = json.loads(Path(receipt).read_bytes())["classic"]
    data = tmp_path / "Native Autoverse availability Ω"
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        port = sock.getsockname()[1]
    url = f"http://127.0.0.1:{port}"
    argv = [
        sys.executable,
        "-I",
        "-m",
        "xverse_studio.host.launcher",
        "--data-dir",
        str(data),
        "--port",
        str(port),
        "--autoverse-root",
        enrolled["root"],
        "--autoverse-native-bridge",
        str(tmp_path / "missing-native-build"),
    ]
    env = dict(os.environ)
    if mode == "missing-tools":
        tools = tmp_path / "empty-native-tools"
        tools.mkdir()
        env["PATH"] = str(tools)
    child = subprocess.Popen(
        argv,
        env=env,
        stdin=subprocess.DEVNULL,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    try:
        deadline = time.monotonic() + 45
        with httpx.Client(base_url=url, headers={"Origin": url}, timeout=10) as api:
            while time.monotonic() < deadline:
                try:
                    if api.get("/api/v1/session").status_code == 401:
                        break
                except httpx.HTTPError:
                    pass
                assert child.poll() is None, (
                    "Requested unavailable Autoverse integration disabled the native backend"
                )
                time.sleep(0.1)
            else:
                pytest.fail(
                    "Original native Autoverse availability host never became ready"
                )
            bootstrap = json.loads((data / "bootstrap.json").read_bytes())[
                "bootstrapToken"
            ]
            login = api.post("/api/v1/session", json={"bootstrapToken": bootstrap})
            assert login.status_code == 200, login.text
            api.headers["X-CSRF-Token"] = login.json()["csrfToken"]
            listed = api.get("/api/v1/providers")
            assert listed.status_code == 200, listed.text
            providers = {p["providerId"]: p for p in listed.json()["items"]}
            assert providers["autoverse.platform"]["available"] is False
            assert providers["autoverse.demo"]["available"] is (mode != "missing-tools")
            blocked = providers[
                "autoverse.demo" if mode == "missing-tools" else "autoverse.platform"
            ]
            assert blocked["blockedReasons"][0]["code"] == (
                "AUTOVERSE_DEPENDENCY_MISSING"
                if mode == "missing-tools"
                else "AUTOVERSE_PLATFORM_ENROLLMENT_FAILED"
            )
            p = api.post(
                "/api/v1/projects",
                json={
                    "name": "Autoverse remains authorable",
                    "blueprintRef": "autoverse-classic",
                },
            )
            assert p.status_code == 201, p.text
            compiled = api.post(
                f"/api/v1/projects/{p.json()['projectId']}/compilations",
                json={"revision": p.json()["revision"]},
            )
            assert compiled.status_code == 200 and compiled.json()["valid"], (
                compiled.text
            )
            pf = api.post(
                f"/api/v1/projects/{p.json()['projectId']}/preflights",
                json={
                    "revision": p.json()["revision"],
                    "providerId": blocked["providerId"],
                },
            )
            assert pf.status_code == 200 and pf.json()["status"] == "blocked", pf.text
            assert api.get("/api/v1/runs").json()["items"] == []
            assert not (data / "platform-runtime").exists()
    finally:
        if child.poll() is None:
            child.terminate()
        try:
            child.wait(timeout=15)
        except subprocess.TimeoutExpired:
            child.kill()
            child.wait(timeout=5)
