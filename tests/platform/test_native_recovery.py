"""Runs on a real native backend subprocess; fixture scope never implies live integration."""

import json
import socket
import subprocess
import sys
import time
import httpx
import psutil


def eventually(fn, timeout=10):
    end = time.monotonic() + timeout
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


def test_native_full_backup_restore_preserves_completed_run_without_replay(tmp_path):
    root, saved, restored = (
        tmp_path / name for name in ["source Ω", "backup Ω", "restored Ω"]
    )
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        port = sock.getsockname()[1]
    client = httpx.Client(
        base_url=f"http://127.0.0.1:{port}",
        headers={"Origin": f"http://127.0.0.1:{port}"},
        timeout=5,
    )
    proc = launch(root, port)
    try:
        eventually(lambda: client.get("/api/v1/session").status_code == 401)
        token = json.loads((root / "bootstrap.json").read_text())["bootstrapToken"]
        session = client.post("/api/v1/session", json={"bootstrapToken": token})
        assert session.status_code == 200, session.text
        client.headers["X-CSRF-Token"] = session.json()["csrfToken"]
        project = client.post(
            "/api/v1/projects", json={"name": "Recovery System Ω"}
        ).json()
        pf = client.post(
            f"/api/v1/projects/{project['projectId']}/preflights",
            json={"revision": project["revision"]},
        ).json()
        assert pf["status"] == "ready", pf
        accepted = client.post(
            "/api/v1/runs",
            json={"snapshotId": pf["snapshotId"], "preflightId": pf["preflightId"]},
            headers={"Idempotency-Key": "recovery-completed-run"},
        )
        assert accepted.status_code == 202, accepted.text
        rid = accepted.json()["runId"]
        eventually(
            lambda: client.get("/api/v1/runs/" + rid).json().get("state") == "stopped"
        )
        original = client.get(f"/api/v1/runs/{rid}/snapshot").json()
        assert original["integrity"] == "valid"
        journal = (root / "runs" / rid / "evidence.jsonl").read_bytes()
        proc.terminate()
        proc.wait(timeout=10)
        command = [sys.executable, "-I", "-m", "xverse_studio.host.launcher"]
        for args in [
            ["--data-dir", str(root), "--backup-full", str(saved)],
            ["--data-dir", str(restored), "--restore-from", str(saved)],
        ]:
            result = subprocess.run(
                command + args, capture_output=True, text=True, timeout=15
            )
            assert result.returncode == 0, result.stderr
            assert json.loads(result.stdout)["integrity"] == "valid"
        proc = launch(restored, port)
        eventually(lambda: client.get("/api/v1/session").status_code == 401)
        token = json.loads((restored / "bootstrap.json").read_text())["bootstrapToken"]
        session = client.post("/api/v1/session", json={"bootstrapToken": token})
        assert session.status_code == 200, session.text
        client.headers["X-CSRF-Token"] = session.json()["csrfToken"]
        assert (
            client.get(f"/api/v1/projects/{project['projectId']}").json()["documents"]
            == project["documents"]
        )
        assert client.get(f"/api/v1/runs/{rid}/snapshot").json() == original
        assert (restored / "runs" / rid / "evidence.jsonl").read_bytes() == journal
        assert client.get("/api/v1/runs").json()["items"][0]["state"] == "stopped"
        assert len(client.get("/api/v1/runs").json()["items"]) == 1
        pf_again = client.post(
            f"/api/v1/projects/{project['projectId']}/preflights",
            json={"revision": project["revision"]},
        ).json()
        assert pf_again["status"] == "ready", pf_again
        assert pf_again["planDigest"] == pf["planDigest"]
    finally:
        client.close()
        if proc.poll() is None:
            proc.terminate()
            proc.wait(timeout=10)
