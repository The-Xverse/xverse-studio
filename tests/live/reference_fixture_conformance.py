"""T011 native executable verification under the user's reference-only exception.

Every case owns a fresh native host and private root. Faults use the closed
developer host, never project commands or a production injection API. Synthetic
and recorded fixtures cannot establish the positive execution asserted here.
"""

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import select
import sqlite3
import subprocess
import sys
import time
import uuid

import httpx
import psutil

from xverse_studio.evidence.reader import read_journal, verify_journal
from xverse_studio.host.ownership import own_root, RootOwnedError

ROOT = Path(__file__).resolve().parents[2]
CASES = ["normal", "normal-repeat", "mismatch", "prepare_denied", "launch_denied",
         "journal_open", "active_failure", "ownership_recovery", "journal_finalize", "cleanup_failure"]


def response(value, expected=200):
    assert value.status_code == expected, (value.status_code, value.text[:1200])
    return value.json()


def wait(read, predicate, timeout=20):
    deadline = time.monotonic() + timeout
    value = None
    while time.monotonic() < deadline:
        value = read()
        if predicate(value):
            return value
        time.sleep(0.03)
    raise AssertionError(("Original native fixture observation timed out", value))


def private_run(data, rid):
    with sqlite3.connect((data / "studio.sqlite").as_uri() + "?mode=ro", uri=True) as db:
        return json.loads(db.execute("SELECT body FROM records WHERE kind=? AND id=?", ("run", rid)).fetchone()[0])


def ready(child):
    deadline, raw = time.monotonic() + 20, b""
    while time.monotonic() < deadline:
        assert child.poll() is None, "Original native fixture host exited before readiness"
        if select.select([child.stdout], [], [], 0.1)[0]:
            raw += os.read(child.stdout.fileno(), 4097)
            assert len(raw) <= 4096
            if b"\n" in raw:
                value = json.loads(raw.splitlines()[0])
                assert value["pid"] == child.pid
                assert re.fullmatch(r"http://127\.0\.0\.1:[0-9]{1,5}", value["origin"])
                return value["origin"]
    raise AssertionError("Original native fixture readiness timed out")


def run_case(case, out, backend):
    scenario = "normal" if case == "normal-repeat" else case
    data = ROOT / ".studio-local/browser-tests" / ("t011-" + case + "-" + uuid.uuid4().hex)
    assert not data.exists()
    launch = [str(backend), "-I", str(ROOT / "tests/fixtures/providers/run_failures/host.py"),
              "--data", str(data), "--scenario", scenario]
    (out / (case + "-command.private.json")).open("x").write(json.dumps({"argv": launch, "dataRoot": str(data)}, indent=2) + "\n")
    result = {"case": case, "scenario": scenario, "scope": "actual owned executable reference; T011 exception", "outcome": "failed"}
    rid, api, snapshot_path, snapshot_hash = None, None, None, None
    with (out / (case + "-host.log")).open("xb") as log:
        child = subprocess.Popen(launch, cwd=ROOT, stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=log)
        process = psutil.Process(child.pid)
        owner = {"birth": process.create_time(), "argv": process.cmdline(), "uid": process.uids().real}
        assert process.ppid() == os.getpid() and owner["uid"] == os.getuid() and owner["argv"] == launch
        try:
            origin = ready(child)
            api = httpx.Client(base_url=origin, headers={"Origin": origin}, timeout=30)
            wait(lambda: api.get("/api/v1/session").status_code, lambda v: v == 401)
            try:
                with own_root(data):
                    raise AssertionError("A second native owner acquired the live fixture root")
            except RootOwnedError:
                result["secondRootOwnerRefused"] = True
            token = json.loads((data / "bootstrap.json").read_bytes())["bootstrapToken"]
            session = response(api.post("/api/v1/session", json={"bootstrapToken": token}))
            api.headers["X-CSRF-Token"] = session["csrfToken"]
            p = response(api.post("/api/v1/projects", json={"name": "T011 owned executable fixture"}), 201)
            duration, timestep = (5.0, 1.0) if case == "active_failure" else (3.0, 0.1) if case == "ownership_recovery" else (0.5, 0.1)
            p = response(api.post(
                f"/api/v1/projects/{p['projectId']}/edits", headers={"If-Match": str(p["revision"])},
                json={"baseRevision": p["revision"], "edits": [
                    {"kind": "set_parameter", "parameterId": "duration", "value": duration},
                    {"kind": "set_parameter", "parameterId": "gain", "value": 0.8},
                    {"kind": "set_parameter", "parameterId": "timestep", "value": timestep},
                ]},
            ))
            pf = response(api.post(f"/api/v1/projects/{p['projectId']}/preflights", json={"revision": p["revision"], "providerId": "studio.reference"}))
            assert pf["status"] == "ready", pf
            assert pf["providerIdentity"]["providerVersion"] == "1.2.0"
            assert pf["providerIdentity"]["contractVersion"] == "1.0"
            assert pf["providerIdentity"]["supportedHostOS"] == ["Linux"]
            snapshot_path = data / "snapshots" / pf["snapshotId"] / "snapshot.json"
            snapshot_hash = hashlib.sha256(snapshot_path.read_bytes()).hexdigest()
            receipt = response(api.post("/api/v1/runs", headers={"Idempotency-Key": "t011-original-start"},
                                        json={k: pf[k] for k in ("snapshotId", "preflightId")}), 202)
            rid = receipt["runId"]
            def read():
                return response(api.get("/api/v1/runs/" + rid))
            if case == "ownership_recovery":
                running = wait(read, lambda v: v["state"] == "running")
                flag = data / "deny-owned-observation"
                flag.open("xb").write(b"Closed fixture observation denial\n")
                denied = wait(read, lambda v: v["state"] == "unknown")
                assert denied["cleanup"] == "unknown"
                blocked = api.post(f"/api/v1/runs/{rid}/commands", headers={"Idempotency-Key": "t011-no-unknown-owner-control"},
                                   json={"kind": "stop", "expectedStateVersion": denied["stateVersion"]})
                assert blocked.status_code == 409
                flag.unlink()
                recovered = wait(read, lambda v: v["state"] == "running")
                assert recovered["runId"] == running["runId"] and recovered["snapshotId"] == running["snapshotId"]
                result["originalOwnershipRecoveredWithoutStartReplay"] = True
            terminal = wait(read, lambda v: v["state"] in {"stopped", "failed"}, timeout=25)
            own = private_run(data, rid)
            directory = data / "runs" / rid
            source_state = json.loads((directory / "state.json").read_bytes()) if (directory / "state.json").is_file() else own
            records, integrity = read_journal(directory, source_state)
            samples = [r for r in records if r["type"] == "observation.available"]
            result.update(runId=rid, snapshotId=pf["snapshotId"], planDigest=pf["planDigest"], semanticDigest=pf["semanticDigest"],
                          terminal={k: terminal.get(k) for k in ["state", "cleanup", "evidence", "reason"]},
                          integrity=integrity, actualSamples=len(samples), sourceProviderVersion=pf["providerIdentity"]["providerVersion"])
            if case in {"normal", "normal-repeat", "ownership_recovery", "cleanup_failure"}:
                assert terminal["state"] == "stopped" and terminal["evidence"] == "complete"
                assert terminal["cleanup"] == ("failed" if case == "cleanup_failure" else "complete")
                assert integrity == "valid" and len(samples) == round(duration / timestep)
                assert terminal["effectivePlanDigest"] == pf["planDigest"]
                assert all(s["source"]["providerId"] == "studio.reference" and s["source"]["version"] == "1.2.0"
                           and s["runId"] == rid and s["evidenceClass"] == "observed" for s in samples)
                assert all(s["sourceTime"]["clockDomain"] == "simulation-time" and s["sourceTime"]["uncertainty"] == 0 for s in samples)
                assert [s["sourceTime"]["tick"] for s in samples] == [str(round(i * timestep * 1e6)) for i in range(len(samples))]
                assert samples[0]["payload"]["values"]["value"] == 0 and samples[-1]["payload"]["values"]["value"] > 0
                result["logicalSamples"] = [{"tick": s["sourceTime"]["tick"], "values": s["payload"]["values"]} for s in samples]
                result["journalDigest"] = terminal["journalDigest"]
                if case == "cleanup_failure":
                    assert (directory / "tmp/retained-fixture.bin").read_bytes() == b"Owned native cleanup fixture bytes\n"
                    assert source_state["cleanupResources"][0]["code"] == "TEMPORARY_DIRECTORY_NOT_RELEASED"
            elif case == "mismatch":
                assert terminal["state"] == "failed" and terminal["reason"] == "EFFECTIVE_INPUT_MISMATCH"
                assert terminal["cleanup"] == "complete" and not samples
            elif case == "prepare_denied":
                assert terminal["state"] == "failed" and terminal["reason"] == "PREPARATION_FAILED" and not samples
            elif case == "launch_denied":
                assert terminal["state"] == "failed" and terminal["reason"] == "LAUNCH_FAILED"
                assert terminal["cleanup"] == "unknown" and not samples
            elif case == "journal_open":
                assert terminal["state"] == "failed" and terminal["reason"] == "EVIDENCE_OPEN_FAILED"
                assert source_state["evidence"] == "unavailable" and not samples
            elif case == "active_failure":
                assert terminal["state"] == "failed" and terminal["reason"] == "REFERENCE_WORKER_ERROR"
                assert terminal["cleanup"] == "unknown" and terminal["evidence"] == "partial" and samples
            elif case == "journal_finalize":
                assert terminal["state"] == "stopped" and terminal["cleanup"] == "complete"
                assert source_state["evidence"] == "partial" and source_state["evidenceFailure"] == "EVIDENCE_FINALIZATION_FAILED"
                retained = (directory / "retained-before-finalization-fault.jsonl").read_bytes()
                retained_records, retained_integrity = verify_journal(retained, source_state)
                assert retained_integrity == "verified_prefix"
                assert any(r["type"] == "observation.available" for r in retained_records)
                result.update(retainedOriginalSamples=sum(r["type"] == "observation.available" for r in retained_records), retainedIntegrity=retained_integrity)
            assert hashlib.sha256(snapshot_path.read_bytes()).hexdigest() == snapshot_hash
            assert len(response(api.get("/api/v1/runs"))["items"]) == 1
            result["frozenInputsUnchanged"] = True
            result["outcome"] = "passed"
        except BaseException as error:
            result["failureType"] = type(error).__name__
            raise
        finally:
            try:
                flag = data / "deny-owned-observation"
                if flag.is_file():
                    flag.unlink()
                if api is not None:
                    api.close()
                if child.poll() is None:
                    original = psutil.Process(child.pid)
                    assert original.create_time() == owner["birth"] and original.cmdline() == owner["argv"] and original.uids().real == owner["uid"]
                    child.terminate()
                try:
                    child.wait(timeout=30)
                except subprocess.TimeoutExpired:
                    child.kill()
                    child.wait(timeout=10)
                child.stdout.close()
                assert child.returncode in {0, -15}, "Original fixture host did not complete graceful shutdown"
                result["originalHostExit"] = child.returncode
                if (data / "fixture-observation.json").is_file():
                    observed = json.loads((data / "fixture-observation.json").read_bytes())
                    assert observed["errors"] == [], observed
                    assert observed["workerAttempts"] == (0 if case == "prepare_denied" else 1)
                    assert len(observed["originalWorkers"]) == (0 if case in {"prepare_denied", "launch_denied"} else 1)
                    for worker in observed["originalWorkers"]:
                        try:
                            assert psutil.Process(worker["pid"]).create_time() != worker["birth"]
                        except psutil.NoSuchProcess:
                            pass
                    result["fixtureObservation"] = observed
                    result["originalWorkersAbsent"] = True
                if (data / "studio.lock").exists():
                    with own_root(data):
                        pass
                    result["originalRootLockReleased"] = True
            except BaseException as cleanup_error:
                result["outcome"] = "failed"
                result["cleanupFailureType"] = type(cleanup_error).__name__
                raise
            finally:
                (out / (case + ".json")).open("x").write(json.dumps(result, indent=2) + "\n")
    assert result["outcome"] == "passed" and result["originalRootLockReleased"]
    return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--backend-python", type=Path, default=Path(sys.executable))
    parser.add_argument("--cases", choices=CASES, nargs="+", default=CASES)
    args = parser.parse_args()
    if not sys.platform.startswith("linux"):
        parser.error("The admitted T011 native fixture target is Linux.")
    args.output.mkdir(parents=True, exist_ok=False)
    results = []
    for case in args.cases:
        value = run_case(case, args.output, args.backend_python.absolute())
        results.append(value)
        print(case, value["outcome"], value["terminal"], flush=True)
    normal = {v["case"]: v for v in results if v["case"] in {"normal", "normal-repeat"}}
    if len(normal) == 2:
        assert normal["normal"]["logicalSamples"] == normal["normal-repeat"]["logicalSamples"]
        assert normal["normal"]["planDigest"] == normal["normal-repeat"]["planDigest"]
        assert normal["normal"]["semanticDigest"] == normal["normal-repeat"]["semanticDigest"]
        assert normal["normal"]["runId"] != normal["normal-repeat"]["runId"]
        assert normal["normal"]["journalDigest"] != normal["normal-repeat"]["journalDigest"]
    summary = {"scope": "T011 user-approved studio.reference exception", "outcome": "passed", "cases": len(results),
               "allOriginalWorkersAbsent": True, "allOriginalRootLocksReleased": True,
               "logicalSampleRepeatabilityVerified": len(normal) == 2, "recordingsNotUsedAsExecution": True}
    (args.output / "summary.json").open("x").write(json.dumps(summary, indent=2) + "\n")
    print(json.dumps(summary), flush=True)


if __name__ == "__main__":
    main()
