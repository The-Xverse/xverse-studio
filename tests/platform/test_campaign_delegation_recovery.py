"""Linux-only native campaign recovery at a declared acknowledgement fault boundary.

The initial backend has an explicit test-only pause. Workers and the restart use
unmodified product paths. No provider, owner record or canonical file is rewritten.
These tests are separate from Windows and external/physical-provider acceptance.
"""

import sys
import pytest

GATE_SOURCE = '''"""Test-only backend pause after actual Start returns, before campaign acknowledgement.

This fixture changes only the campaign acknowledgement boundary in this process.
It does not wrap the worker, replace argv or rewrite persisted campaign/run records.
The successor starts through the ordinary unmodified native launcher.
"""
from pathlib import Path
import json,os,sys,time
from xverse_studio.campaigns import CampaignState
from xverse_studio.host.launcher import main

arguments=sys.argv[1:];root=Path(arguments[arguments.index('--data-dir')+1]);marker=root/'delegated-start-gate.fixture.json'
original=CampaignState.mark_started
def paused(self,key,run_id):
    if not marker.exists():
        with marker.open('x') as f:
            json.dump({'scope':'Test-only pause after real runs.start returned; no campaign mark_started executed.','backendPid':os.getpid(),'campaignId':self.record['campaignId'],'childKey':key,'runId':run_id},f)
            f.flush();os.fsync(f.fileno())
        deadline=time.monotonic()+30
        while time.monotonic()<deadline:time.sleep(.05)
        raise RuntimeError('Owned crash fixture deadline expired before delivery')
    return original(self,key,run_id)
CampaignState.mark_started=paused
main()
'''


@pytest.mark.skipif(
    sys.platform != "linux",
    reason="Declared Linux kernel/process fault lane; native Windows verification is held separately.",
)
@pytest.mark.parametrize(
    "mode", ["while-running", "after-terminal", "failed-continue", "failed-stop"]
)
def test_native_campaign_recovers_durable_start_before_campaign_acknowledgement(
    tmp_path, mode
):
    """Actual native worker, deterministic labelled backend crash boundary, clean restart."""
    from pathlib import Path
    from datetime import datetime, timezone
    import hashlib, json, os, signal, socket, sqlite3, subprocess, sys, time
    import httpx, psutil
    from xverse_studio.storage.core import canonical, digest

    repo = Path(__file__).resolve().parents[2]
    base = tmp_path / "harness"
    base.mkdir()
    (base / "backend_gate.py").write_text(GATE_SOURCE)
    out = tmp_path / "observations"
    out.mkdir()
    data = out / "private Native delegation Ω data"
    data.mkdir()
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        port = sock.getsockname()[1]
    url = f"http://127.0.0.1:{port}"
    tail = ["--data-dir", str(data), "--port", str(port)]
    initial = [sys.executable, "-I", str(base / "backend_gate.py"), *tail]
    successor = [sys.executable, "-I", "-m", "xverse_studio.host.launcher", *tail]

    def launch(command):
        return subprocess.Popen(
            command,
            cwd=repo,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )

    def eventually(read, ready=lambda value: bool(value), timeout=25):
        deadline = time.monotonic() + timeout
        last = None
        while time.monotonic() < deadline:
            try:
                last = read()
                if ready(last):
                    return last
            except (httpx.HTTPError, OSError, ValueError):
                pass
            time.sleep(0.05)
        raise AssertionError("Owned fixture observation deadline expired")

    def disk(kind, identity):
        with sqlite3.connect(
            (data / "studio.sqlite").as_uri() + "?mode=ro", uri=True
        ) as db:
            row = db.execute(
                "SELECT body FROM records WHERE kind=? AND id=?", (kind, identity)
            ).fetchone()
        return json.loads(row[0]) if row else None

    def sha(path):
        return hashlib.sha256(path.read_bytes()).hexdigest()

    proc = launch(initial)
    backend_birth = psutil.Process(proc.pid).create_time()
    worker = None
    worker_birth = None
    client = httpx.Client(base_url=url, headers={"Origin": url}, timeout=5)
    started = time.monotonic()
    failure = None
    receipt = {
        "scope": "Labelled deterministic acknowledgement-pause fixture in an actual isolated native Linux backend. Real unchanged reference worker and normal native launcher restart; no Windows/external/physical-provider claim.",
        "mode": mode,
        "startedAtUtc": datetime.now(timezone.utc).isoformat(),
        "events": [],
    }

    def api(path, method="GET", body=None, key=None, revision=None):
        headers = {}
        if key:
            headers["Idempotency-Key"] = key
        if revision is not None:
            headers["If-Match"] = str(revision)
        response = client.request(method, "/api/v1" + path, json=body, headers=headers)
        assert response.is_success, (
            method,
            path,
            response.status_code,
            response.json().get("code"),
        )
        return response.json()

    try:
        eventually(lambda: client.get("/api/v1/session").status_code == 401)
        bootstrap = json.loads((data / "bootstrap.json").read_text())
        auth = client.post(
            "/api/v1/session", json={"bootstrapToken": bootstrap["bootstrapToken"]}
        )
        assert auth.status_code == 200
        client.headers["X-CSRF-Token"] = auth.json()["csrfToken"]
        project = api(
            "/projects",
            "POST",
            {
                "name": "Owned delegated acknowledgement crash Ω",
                "blueprintRef": "reference-process-control",
            },
        )
        project = api(
            "/projects/" + project["projectId"] + "/edits",
            "POST",
            {
                "baseRevision": project["revision"],
                "edits": [
                    {"kind": "set_parameter", "parameterId": "duration", "value": 5},
                    {"kind": "set_parameter", "parameterId": "timestep", "value": 1},
                ],
            },
            revision=project["revision"],
        )
        pf = api(
            "/projects/" + project["projectId"] + "/preflights",
            "POST",
            {"revision": project["revision"]},
        )
        assert pf["status"] == "ready"
        base_snapshot_file = data / "snapshots" / pf["snapshotId"] / "snapshot.json"
        base_snapshot_sha = sha(base_snapshot_file)
        payload = {
            "snapshotId": pf["snapshotId"],
            "matrix": {"gain": [0.4, 0.8]},
            "budget": {"maxRuns": 2, "maxTotalSeconds": 10},
            "concurrency": 1,
            "stopPolicy": "stop_on_failure" if mode == "failed-stop" else "continue",
        }
        accepted = api(
            "/campaigns", "POST", payload, key="native-delegated-campaign-once"
        )
        cid = accepted["campaignId"]
        marker = eventually(
            lambda: json.loads((data / "delegated-start-gate.fixture.json").read_text())
        )
        assert marker["campaignId"] == cid and marker["backendPid"] == proc.pid
        before = disk("campaign", cid)
        assert [c["state"] for c in before["children"]] == ["dispatching", "pending"]
        child = before["children"][0]
        assert child["runId"] is None and child["childKey"] == marker["childKey"]
        with sqlite3.connect(
            (data / "studio.sqlite").as_uri() + "?mode=ro", uri=True
        ) as db:
            row = db.execute(
                "SELECT result FROM idempotency WHERE scope=? AND key=?",
                (before["principal"] + ":POST /runs", child["operationKey"]),
            ).fetchone()
        assert row is not None
        ack = json.loads(row[0])
        rid = ack["runId"]
        assert rid == marker["runId"]
        known = disk("run", rid)
        assert (
            known["providerId"] == "studio.reference"
            and known["evidenceScope"] == "owned_reference"
        )
        directory = data / "runs" / rid
        observed = eventually(
            lambda: json.loads((directory / "state.json").read_text()),
            lambda s: s["state"] == "running",
        )
        worker = psutil.Process(known["pid"])
        worker_birth = worker.create_time()
        argv = [
            sys.executable,
            "-I",
            "-m",
            "xverse_studio.providers.worker",
            str(directory),
        ]
        assert (
            worker.pid != proc.pid
            and worker.pid != os.getpid()
            and worker.is_running()
            and worker.status() != psutil.STATUS_ZOMBIE
        )
        assert (
            worker_birth == known["createTime"] == observed["createTime"]
            and observed["pid"] == worker.pid
        )
        assert worker.cmdline() == argv and known["launchArgvDigest"] == digest(argv)
        owner_matches = (
            observed["ownerDigest"]
            == known["ownerDigest"]
            == digest((directory / "owner.key").read_bytes())
        )
        assert owner_matches, "Owned worker identity mismatch"
        snapshot = disk("snapshot", known["snapshotId"])
        assert (
            snapshot["campaignId"] == cid
            and snapshot["campaignChildKey"] == child["childKey"]
            and snapshot["parentSnapshotId"] == pf["snapshotId"]
        )
        snapshot_file = data / "snapshots" / snapshot["snapshotId"] / "snapshot.json"
        snapshot_sha = sha(snapshot_file)
        assert (
            proc.poll() is None
            and psutil.Process(proc.pid).create_time() == backend_birth
        )
        receipt.update(
            campaignId=cid,
            projectId=project["projectId"],
            before=before,
            durableStartReceipt=ack,
            backendBefore={"pid": proc.pid, "birth": backend_birth},
            workerBefore={"pid": worker.pid, "birth": worker_birth},
            snapshotId=snapshot["snapshotId"],
            snapshotDigest=snapshot["snapshotDigest"],
        )
        receipt["events"].append(
            {
                "kind": "durable-start-and-real-worker-before-campaign-ack",
                "elapsed": time.monotonic() - started,
            }
        )
        proc.kill()
        proc.wait(timeout=5)
        assert (
            worker.is_running()
            and worker.create_time() == worker_birth
            and worker.status() != psutil.STATUS_ZOMBIE
        )
        assert disk("campaign", cid) == before and disk("run", rid)["pid"] == worker.pid
        receipt["events"].append(
            {
                "kind": "exact-owned-backend-killed-worker-survives",
                "elapsed": time.monotonic() - started,
            }
        )
        terminal_bytes = None
        if mode.startswith("failed-"):

            def sleeping():
                s = json.loads((directory / "state.json").read_text())
                elapsed = time.time() - s["startedAt"]
                return {
                    "state": s,
                    "channel": (Path("/proc") / str(worker.pid) / "wchan")
                    .read_text()
                    .strip(),
                    "elapsed": elapsed,
                    "phase": elapsed % 1.0,
                }

            phase = eventually(
                sleeping,
                lambda p: (
                    p["state"]["state"] == "running"
                    and p["channel"] == "hrtimer_nanosleep"
                    and 0.15 <= p["phase"] <= 0.65
                    and p["elapsed"] < 4.5
                ),
                timeout=4,
            )
            assert (
                worker.create_time() == worker_birth
                and worker.is_running()
                and worker.status() != psutil.STATUS_ZOMBIE
            )
            assert worker.cmdline() == argv and disk("run", rid)[
                "launchArgvDigest"
            ] == digest(argv)
            s = json.loads((directory / "state.json").read_text())
            assert s["pid"] == worker.pid and s["createTime"] == worker_birth
            owner_matches = (
                s["ownerDigest"]
                == known["ownerDigest"]
                == digest((directory / "owner.key").read_bytes())
            )
            assert owner_matches, "Refusing fault after owner mismatch"
            assert (
                Path("/proc") / str(worker.pid) / "wchan"
            ).read_text().strip() == "hrtimer_nanosleep"
            worker.send_signal(signal.SIGINT)
            receipt["workerFault"] = {
                "kind": "SIGINT",
                "scope": "Exact owned reference worker, verified PID/birth/argv/owner and kernel sleep point; backend already crashed.",
                "pid": worker.pid,
                "birth": worker_birth,
                "elapsed": phase["elapsed"],
                "phase": phase["phase"],
                "kernelChannel": phase["channel"],
            }
        if mode != "while-running":
            terminal_state = "failed" if mode.startswith("failed-") else "stopped"
            terminal = eventually(
                lambda: json.loads((directory / "state.json").read_text()),
                lambda s: s["state"] == terminal_state,
            )
            assert terminal["cleanup"] == (
                "unknown" if mode.startswith("failed-") else "complete"
            )
            assert terminal["evidence"] == (
                "partial" if mode.startswith("failed-") else "complete"
            )
            terminal_bytes = {
                str(p.relative_to(directory)): sha(p)
                for p in directory.iterdir()
                if p.is_file() and p.name not in ["owner.key"]
            }
            receipt["events"].append(
                {
                    "kind": "worker-terminal-before-native-restart",
                    "elapsed": time.monotonic() - started,
                }
            )
        else:
            assert (
                json.loads((directory / "state.json").read_text())["state"] == "running"
            )
        proc = launch(successor)
        backend_birth = psutil.Process(proc.pid).create_time()
        eventually(lambda: client.get("/api/v1/session").status_code == 200)
        recovered = api("/campaigns/" + cid)
        same = recovered["children"][0]
        assert same["childKey"] == child["childKey"]
        reconciled = eventually(
            lambda: api("/campaigns/" + cid), lambda c: c["children"][0]["runId"] == rid
        )
        assert reconciled["children"][0]["childKey"] == child["childKey"]
        assert (
            api("/campaigns", "POST", payload, key="native-delegated-campaign-once")
            == accepted
        )
        assert (
            api("/runs/" + rid + "/snapshot")["snapshot"] == snapshot
            and sha(snapshot_file) == snapshot_sha
        )
        final = eventually(
            lambda: api("/campaigns/" + cid),
            lambda c: c["status"] == "complete",
            timeout=30,
        )
        states = (
            ["failed", "cancelled" if mode == "failed-stop" else "stopped"]
            if mode.startswith("failed-")
            else ["stopped", "stopped"]
        )
        assert [c["state"] for c in final["children"]] == states
        ids = [c["runId"] for c in final["children"] if c["runId"]]
        assert ids[0] == rid and len(set(ids)) == (1 if mode == "failed-stop" else 2)
        assert {r["runId"] for r in api("/runs")["items"]} == set(ids)
        assert [c["childKey"] for c in final["children"]] == [
            c["childKey"] for c in before["children"]
        ]
        for child in final["children"]:
            if child["runId"] is None:
                assert mode == "failed-stop" and child["state"] == "cancelled"
                continue
            run = api("/runs/" + child["runId"])
            assert run["state"] == child["state"]
            assert run["cleanup"] == (
                "unknown" if child["state"] == "failed" else "complete"
            ) and run["evidence"] == (
                "partial" if child["state"] == "failed" else "complete"
            )
            assert run["verdict"] is None
            snap = api("/runs/" + child["runId"] + "/snapshot")["snapshot"]
            assert (
                snap["campaignChildKey"] == child["childKey"]
                and snap["configuration"]["gain"] == child["parameters"]["gain"]
            )
        if terminal_bytes is not None:
            assert all(sha(directory / name) == h for name, h in terminal_bytes.items())
        if mode.startswith("failed-"):
            observations = api("/runs/" + rid + "/observations")
            assert (
                observations["integrity"] == "verified_prefix" and observations["items"]
            )
            events = []
            previous = "0" * 64
            for index, line in enumerate(
                (directory / "evidence.jsonl").read_bytes().splitlines(), 1
            ):
                event = json.loads(line)
                assert (
                    event["runId"] == rid
                    and event["snapshotId"] == snapshot["snapshotId"]
                    and event["sequence"] == str(index)
                    and event["previousDigest"] == previous
                )
                assert (
                    hashlib.sha256(
                        canonical(
                            {k: v for k, v in event.items() if k != "digest"}
                        ).encode()
                    ).hexdigest()
                    == event["digest"]
                )
                previous = event["digest"]
                events.append(event)
            assert any(
                e["type"] == "log.appended" and e["payload"].get("severity") == "error"
                for e in events
            )
            assert sha(directory / "evidence.jsonl") == terminal_bytes["evidence.jsonl"]
            receipt["failedEvidence"] = {
                "readerIntegrity": observations["integrity"],
                "journalRecords": len(events),
                "hashChainVerified": True,
                "errorEventPresent": True,
                "terminalJournalUnchanged": True,
                "originalWorkerIdentityRetained": True,
            }
        assert (
            api("/projects/" + project["projectId"]) == project
            and sha(snapshot_file) == snapshot_sha
        )
        assert sha(base_snapshot_file) == base_snapshot_sha
        for _ in range(2):
            assert (
                api("/campaigns", "POST", payload, key="native-delegated-campaign-once")
                == accepted
            )
            assert {r["runId"] for r in api("/runs")["items"]} == set(ids)
            assert (
                sha(snapshot_file) == snapshot_sha
                and sha(base_snapshot_file) == base_snapshot_sha
            )
        final_operation = eventually(
            lambda: api("/operations/" + accepted["operationId"]),
            lambda op: op["status"] == "completed",
        )
        final_known = disk("run", rid)
        final_state = json.loads((directory / "state.json").read_text())
        assert (
            final_known["pid"] == final_state["pid"] == worker.pid
            and final_known["createTime"] == final_state["createTime"] == worker_birth
        )
        receipt["originalWorkerIdentityRetained"] = True
        receipt.update(
            outcome="passed",
            afterRestart=recovered,
            reconciled=reconciled,
            final=final,
            operation=final_operation,
            noDuplicateRuns=True,
            canonicalProjectUnchanged=True,
            activeSnapshotUnchanged=True,
            terminalWorkerFilesUnchanged=terminal_bytes is not None,
        )
    except Exception as exc:
        failure = exc
        receipt.update(
            outcome="failed", failureType=type(exc).__name__, failure=str(exc)
        )
    finally:
        client.close()
        if proc.poll() is None:
            assert psutil.Process(proc.pid).create_time() == backend_birth
            proc.terminate()
            try:
                proc.wait(timeout=10)
            except subprocess.TimeoutExpired:
                proc.kill()
                proc.wait(timeout=5)
        if worker is not None:
            eventually(
                lambda: (
                    not worker.is_running()
                    or worker.create_time() != worker_birth
                    or worker.status() == psutil.STATUS_ZOMBIE
                ),
                timeout=12,
            )
        receipt.update(
            seconds=round(time.monotonic() - started, 3),
            initialBackendFixture="backend_gate.py",
            successorCommand=[
                sys.executable,
                "-I",
                "-m",
                "xverse_studio.host.launcher",
                "--data-dir",
                "<owned-private-root>",
                "--port",
                "<allocated-loopback-port>",
            ],
        )
        (out / "receipt.json").write_text(json.dumps(receipt, indent=2) + "\n")
    if failure:
        raise failure
