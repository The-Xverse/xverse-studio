"""Actual enrolled Autoverse worker journal-opening refusals; no fake runtime."""

import argparse
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import uuid

import psutil

from xverse_studio.host.ownership import own_root
from xverse_studio.security.managed_io import create_directory
from xverse_studio.storage.core import canonical, digest

ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location("native_lifecycle", Path(__file__).with_name("autoverse_lifecycle_conformance.py"))
native = importlib.util.module_from_spec(spec)
spec.loader.exec_module(native)


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--receipt", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    p.add_argument("--static-dir", type=Path, required=True)
    p.add_argument("--case", choices=["directory", "existing"], required=True)
    p.add_argument("--node", type=Path, required=True)
    p.add_argument("--playwright-cli", type=Path, required=True)
    p.add_argument("--browser-cache", type=Path, required=True)
    args = p.parse_args()
    args.output.mkdir(parents=True)
    data = ROOT / ".studio-local/browser-tests" / ("journal-open-" + uuid.uuid4().hex)
    with create_directory(Path("/"), data.absolute(), parents=True):
        pass
    (args.output / "data-root.private.json").write_text(json.dumps({"dataRoot": str(data)}))
    host = native.NativeHost(data, args.output, args.receipt.absolute(), Path(sys.executable), args.static_dir.absolute(),
                             host_arguments=("--journal-open-fault", args.case))
    report = {"scope": "Actual native enrolled Autoverse opening refusal; no workload execution or canonical failure event inferred", "case": args.case, "outcome": "failed"}
    api, rid, browser = None, None, None
    try:
        host.start()
        api = native.login(host)
        project, preflight = native.author(api)
        frozen = (data / "snapshots" / preflight["snapshotId"] / "snapshot.json").read_bytes()
        body = {key: preflight[key] for key in ("snapshotId", "preflightId")}
        receipt = native.checked(api.post("/api/v1/runs", headers={"Idempotency-Key": "journal-open-original-start"}, json=body), 202)
        rid = receipt["runId"]
        directory = data / "runs" / rid
        marker = json.loads((data / "journal-open-fault.private.json").read_bytes())
        assert marker["runId"] == rid and marker["operationId"] == receipt["operationId"]
        run = native.wait(lambda: native.checked(api.get(f"/api/v1/runs/{rid}")), lambda r: r["state"] in {"failed", "unknown"})
        report.update(runId=rid, snapshotId=preflight["snapshotId"], operationId=receipt["operationId"], observedState=run["state"], reason=run.get("reason"), cleanup=run["cleanup"], evidence=run["evidence"])
        assert run["state"] == "failed", "Accepted Start must have a structured native opening-failure report"
        assert run["reason"] == "EVIDENCE_OPEN_FAILED" and run["cleanup"] == "complete"
        state = json.loads((directory / "state.json").read_bytes())
        assert state["evidence"] == "unavailable" and state["evidenceFailure"] == "EVIDENCE_OPEN_FAILED"
        assert not state.get("startedAt") and not state.get("effectivePlanDigest")
        assert not state.get("journalDigest") and not state.get("eventCount")
        known = native.private_record(data, "run", rid)
        assert state["pid"] == known["pid"] and state["createTime"] == known["createTime"]
        assert state["ownerDigest"] == known["ownerDigest"] == digest((directory / "owner.key").read_bytes())
        def original_exited():
            try:
                worker = psutil.Process(state["pid"])
                return worker.create_time() != state["createTime"] or worker.status() == psutil.STATUS_ZOMBIE
            except psutil.NoSuchProcess:
                return True
        native.wait(original_exited, bool, timeout=10)
        assert not (directory / "resources.private.json").exists() and not (directory / "containers.private.json").exists()
        journal = directory / "evidence.jsonl"
        if args.case == "directory":
            assert journal.is_dir() and not list(journal.iterdir())
        else:
            assert journal.is_file() and digest(journal.read_bytes()) == marker["originalBytesDigest"]
        assert run["evidence"] == "invalid", "Unsafe pre-existing objects retain their invalid original reader verdict"
        op = native.checked(api.get("/api/v1/operations/" + receipt["operationId"]))
        assert op["status"] == "failed"
        assert native.checked(api.post("/api/v1/runs", headers={"Idempotency-Key": "journal-open-original-start"}, json=body), 202) == receipt
        assert len(native.checked(api.get("/api/v1/runs"))["items"]) == 1
        assert (data / "snapshots" / preflight["snapshotId"] / "snapshot.json").read_bytes() == frozen
        assert native.checked(api.get(f"/api/v1/projects/{project['projectId']}")) == project
        diagnosis = native.checked(api.get(f"/api/v1/runs/{rid}/diagnostics"))
        assert any(f["code"] == "EVIDENCE_OPEN_FAILED" for f in diagnosis["findings"])
        context = {"projectId": project["projectId"], "runId": rid, "snapshotId": preflight["snapshotId"], "operationId": receipt["operationId"]}
        native.atomic(data / "journal-open-browser.private.json", canonical(context).encode())
        # Transfer only this test's existing authenticated session to its owned
        # browser. Credentials remain inside the private0700 data root.
        cookies = [{"name": cookie.name, "value": cookie.value, "url": host.url, "httpOnly": True, "secure": False, "sameSite": "Strict"} for cookie in api.cookies.jar]
        native.atomic(data / "browser-session.private.json", canonical({"cookies": cookies}).encode())
        argv = [str(args.node.absolute()), str(args.playwright_cli.absolute()), "test", "--config", "tests/live/autoverse-journal-open.config.ts"]
        (args.output / "browser-command.private.json").write_text(json.dumps({"argv": argv, "dataRoot": str(data)}, indent=2) + "\n")
        env = dict(os.environ, STUDIO_BASE_URL=host.url, STUDIO_BROWSER_DATA=str(data), STUDIO_BROWSER_REPORT=str(args.output.absolute() / "browser.json"),
                   STUDIO_BROWSER_OUTPUT=str(args.output.absolute() / "browser-artifacts"), PLAYWRIGHT_BROWSERS_PATH=str(args.browser_cache.absolute()))
        with (args.output / "browser.log").open("xb") as log:
            browser = subprocess.Popen(argv, cwd=ROOT, env=env, stdin=subprocess.DEVNULL, stdout=log, stderr=subprocess.STDOUT)
            original = psutil.Process(browser.pid)
            birth = original.create_time()
            native.wait(lambda: original.create_time() == birth and original.ppid() == os.getpid() and original.uids().real == os.getuid() and original.cmdline() == argv, bool, timeout=3)
            report["originalBrowserDriver"] = {"pid": browser.pid, "birth": birth, "argvDigest": digest(argv), "nativeParentAndUidVerified": True}
            browser.wait(timeout=120)
        report["browserExit"] = browser.returncode
        assert browser.returncode == 0, "Actual browser opening-failure case failed; retain its original report"
        report.update(outcome="passed", originalWorkerExited=True, noWorkloadResources=True, originalJournalObjectPreserved=True,
                      immutableSnapshotPreserved=True, snapshotDigest=digest(frozen), sourceReportDigest=digest(canonical(state)),
                      originalStartReceiptPreserved=True, startOperationStatus=op["status"], functionalVerdict=run["verdict"])
    finally:
        if browser is not None and browser.poll() is None:
            browser.terminate()
            browser.wait(timeout=30)
        if api is not None:
            api.close()
        host.stop()
        with own_root(data):
            report["originalRootLockReleased"] = True
        report["nativeBackendObservations"] = host.observations
        (args.output / "native-result.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report))


if __name__ == "__main__":
    main()
