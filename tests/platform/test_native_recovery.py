"""Runs on a real native backend subprocess; fixture scope never implies live integration."""

import json
import os
from pathlib import Path
import socket
import subprocess
import sys
import time
import httpx
import psutil


def eventually(fn, timeout=10):
    end = time.monotonic() + timeout
    last = None
    while time.monotonic() < end:
        try:
            value = fn()
            if value:
                return value
        except (OSError, ValueError, httpx.HTTPError):
            pass
        time.sleep(0.05)
    raise AssertionError("Native readiness/ownership deadline expired")


def launch(root, port):
    return subprocess.Popen(
        [
            sys.executable,
            "-I",
            "-m",
            "xverse_studio.host.launcher",
            "--data-dir",
            str(root),
            "--port",
            str(port),
        ],
        stdin=subprocess.DEVNULL,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )


def test_native_backend_crash_reconcile_and_clean_shutdown(tmp_path):
    root = tmp_path / "Studio native Ω with spaces"
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        port = sock.getsockname()[1]
    proc = launch(root, port)
    client = httpx.Client(
        base_url=f"http://127.0.0.1:{port}",
        headers={"Origin": f"http://127.0.0.1:{port}"},
        timeout=5,
    )
    worker = None
    try:
        eventually(lambda: client.get("/api/v1/session").status_code == 401)
        boot = json.loads((root / "bootstrap.json").read_text())
        r = client.post(
            "/api/v1/session", json={"bootstrapToken": boot["bootstrapToken"]}
        )
        assert r.status_code == 200, r.text
        client.headers["X-CSRF-Token"] = r.json()["csrfToken"]
        p = client.post(
            "/api/v1/projects", json={"name": "native crash fixture"}
        ).json()
        p = client.post(
            f"/api/v1/projects/{p['projectId']}/edits",
            headers={"If-Match": str(p["revision"])},
            json={
                "baseRevision": p["revision"],
                "edits": [
                    {"kind": "set_parameter", "parameterId": "duration", "value": 3.0}
                ],
            },
        ).json()
        pf = client.post(
            f"/api/v1/projects/{p['projectId']}/preflights",
            json={"revision": p["revision"]},
        ).json()
        assert pf["status"] == "ready", pf
        payload = {"snapshotId": pf["snapshotId"], "preflightId": pf["preflightId"]}
        start = client.post(
            "/api/v1/runs", headers={"Idempotency-Key": "native-once"}, json=payload
        ).json()
        rid = start["runId"]
        eventually(
            lambda: client.get("/api/v1/runs/" + rid).json().get("state") == "running"
        )
        state = json.loads((root / "runs" / rid / "state.json").read_text())
        worker = psutil.Process(state["pid"])
        birth = worker.create_time()
        # Kill only our owned backend process. The provider must retain its own lifetime.
        proc.kill()
        proc.wait(timeout=5)
        assert worker.is_running() and worker.create_time() == birth
        proc = launch(root, port)
        eventually(lambda: client.get("/api/v1/session").status_code == 200)
        recovered = client.get("/api/v1/runs/" + rid).json()
        assert recovered["state"] in ("running", "stopped"), recovered
        assert (
            client.post(
                "/api/v1/runs", headers={"Idempotency-Key": "native-once"}, json=payload
            ).json()
            == start
        )
        assert len(client.get("/api/v1/runs").json()["items"]) == 1
        if recovered["state"] == "running":
            response = client.post(
                f"/api/v1/runs/{rid}/commands",
                headers={"Idempotency-Key": "native-cancel"},
                json={
                    "kind": "cancel",
                    "expectedStateVersion": recovered["stateVersion"],
                },
            )
            assert response.status_code == 202, response.text
        eventually(
            lambda: client.get("/api/v1/runs/" + rid).json().get("state") == "stopped"
        )
        assert client.get("/api/v1/runs/" + rid).json()["cleanup"] == "complete"
        client.close()
        proc.terminate()
        proc.wait(timeout=10)
        state = json.loads((root / "runs" / rid / "state.json").read_text())
        assert state["state"] == "stopped" and state["cleanup"] == "complete"
    finally:
        client.close()
        if proc.poll() is None:
            proc.terminate()
            proc.wait(timeout=10)
        if worker:
            # Never kill an unverified PID. The admitted reference has a <=30s bound.
            eventually(
                lambda: (
                    not worker.is_running() or worker.status() == psutil.STATUS_ZOMBIE
                ),
                timeout=6,
            )
