"""Read-only browser verification on a private copy of a completed Autoverse run.

Does not start a workload or change the original recording/operator installation.
Controlled HTTP failures establish display behaviour, never provider admission.
"""
import argparse
from contextlib import closing
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import shutil
import sqlite3
import subprocess
import sys
import uuid

from xverse_studio.host.ownership import own_root


_spec = importlib.util.spec_from_file_location("assessment_native_host", Path(__file__).with_name("autoverse_lifecycle_conformance.py"))
native = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(native)


def hashes(root):
    return {p.relative_to(root).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
            for folder in ("runs", "snapshots") for p in (root / folder).rglob("*") if p.is_file()}


def ledger(root):
    with sqlite3.connect((root / "studio.sqlite").as_uri() + "?mode=ro", uri=True) as db:
        return {kind: db.execute("SELECT count(*) FROM records WHERE kind=?", (kind,)).fetchone()[0]
                for kind in ("run", "operation", "evaluation", "snapshot")}


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--recording", required=True, type=Path)
    p.add_argument("--receipt", required=True, type=Path)
    p.add_argument("--output", required=True, type=Path)
    p.add_argument("--static-dir", required=True, type=Path)
    p.add_argument("--node", required=True, type=Path)
    p.add_argument("--playwright-cli", required=True, type=Path)
    p.add_argument("--browser-cache", required=True, type=Path)
    p.add_argument("--grep")
    a = p.parse_args()
    for field in ("recording", "receipt", "output", "static_dir", "node", "playwright_cli", "browser_cache"):
        setattr(a, field, getattr(a, field).resolve())
    a.output.mkdir(parents=True, exist_ok=False)
    result = json.loads((a.recording / "native-result.json").read_bytes())
    assert result["outcome"] == "passed"
    original = Path(json.loads((a.recording / "data-root.private.json").read_bytes())["dataRoot"])
    before = hashes(original)
    data = native.ROOT / ".studio-local/browser-tests" / ("recorded-assessments-" + uuid.uuid4().hex)
    with own_root(original):
        assert all(not item.is_symlink() for item in original.rglob("*"))
        shutil.copytree(original, data, ignore=shutil.ignore_patterns("studio.lock", "studio.sqlite*", "browser-session.private.json", "bootstrap.json"))
        with sqlite3.connect((original / "studio.sqlite").as_uri() + "?mode=ro", uri=True) as source, sqlite3.connect(data / "studio.sqlite") as dest:
            source.backup(dest)
            dest.execute("DELETE FROM records WHERE kind='session'")
    assert hashes(data) == before
    baseline = ledger(data)
    host = native.NativeHost(data, a.output, a.receipt, Path(sys.executable), a.static_dir)
    outcome = {"scope": "recorded Autoverse read-only browser inspection; no new execution", "before": baseline}
    paths = ["apps", "services", "packages", "tests", "config", "scripts", "package.json", "package-lock.json", "pyproject.toml", "uv.lock"]
    names = subprocess.check_output(["git", "ls-files", "--cached", "--others", "--exclude-standard", "-z", "--", *paths], cwd=native.ROOT).decode().split("\0")
    def inputs():
        return {name: hashlib.sha256((native.ROOT / name).read_bytes()).hexdigest() for name in sorted(set(names)) if name and (native.ROOT / name).is_file()}
    source_before = inputs()
    ui_before = {v.relative_to(a.static_dir).as_posix(): hashlib.sha256(v.read_bytes()).hexdigest() for v in a.static_dir.rglob("*") if v.is_file()}
    (a.output / "source-inputs.json").write_text(json.dumps(source_before, indent=2) + "\n")
    outcome["sourceCandidate"] = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=native.ROOT, text=True).strip()
    outcome["uiFiles"] = ui_before
    exit_code = 1
    try:
        host.start()
        with closing(native.login(host)) as api:
            run = native.checked(api.get("/api/v1/runs/" + result["runId"]))
            assert run["state"] == "stopped" and run["cleanup"] == "complete"
            snapshot = native.checked(api.get("/api/v1/runs/" + result["runId"] + "/snapshot"))
            assert native.checked(api.get("/api/v1/runs/" + result["runId"] + "/definitions"))["items"] == []
            assert native.checked(api.get("/api/v1/runs/" + result["runId"] + "/evaluations"))["items"] == []
            private = {"runId": run["runId"], "snapshotId": run["snapshotId"], "projectId": run["projectId"], "snapshotResponse": snapshot}
            (data / "assessment-recording.private.json").write_text(json.dumps(private))
            cookies = {"cookies": [{"name": c.name, "value": c.value, "domain": c.domain, "path": c.path, "secure": c.secure, "httpOnly": True, "sameSite": "Strict"} for c in api.cookies.jar]}
            session = data / "browser-session.private.json"
            session.write_text(json.dumps(cookies))
            session.chmod(0o600)
            env = dict(os.environ, STUDIO_BASE_URL=host.url, STUDIO_BROWSER_DATA=str(data), STUDIO_BROWSER_REPORT=str(a.output / "browser.json"),
                       STUDIO_BROWSER_OUTPUT=str(a.output / "artifacts"), PLAYWRIGHT_BROWSERS_PATH=str(a.browser_cache))
            argv = [str(a.node), str(a.playwright_cli), "test", "--config", "tests/live/autoverse-assessments.config.ts"]
            if a.grep:
                argv += ["--grep", a.grep]
            (a.output / "command.private.json").write_text(json.dumps({"argv": argv, "dataRoot": str(data)}))
            with (a.output / "browser.log").open("xb") as log:
                child = subprocess.Popen(argv, cwd=native.ROOT, env=env, stdin=subprocess.DEVNULL, stdout=log, stderr=subprocess.STDOUT)
                process = native.psutil.Process(child.pid)
                birth = process.create_time()
                assert process.ppid() == os.getpid() and process.uids().real == os.getuid()
                try:
                    exit_code = child.wait(timeout=240)
                finally:
                    if child.poll() is None:
                        assert process.create_time() == birth and process.ppid() == os.getpid()
                        child.terminate()
                        child.wait(timeout=30)
                outcome["originalBrowserExited"] = child.poll() is not None
                outcome["browserExit"] = exit_code
            outcome["after"] = ledger(data)
            assert outcome["after"] == baseline
    finally:
        host.stop()
        with own_root(data):
            outcome["originalRootReleased"] = True
        outcome["hostShutdown"] = host.observations
        outcome["sourceInputsUnchanged"] = inputs() == source_before
        outcome["uiInputsUnchanged"] = {v.relative_to(a.static_dir).as_posix(): hashlib.sha256(v.read_bytes()).hexdigest() for v in a.static_dir.rglob("*") if v.is_file()} == ui_before
        outcome["originalRecordingUnchanged"] = hashes(original) == before
        outcome["copiedRecordingUnchanged"] = hashes(data) == before
        (a.output / "verification.json").write_text(json.dumps(outcome, indent=2) + "\n")
        assert all(outcome[key] for key in ["sourceInputsUnchanged", "uiInputsUnchanged", "originalRecordingUnchanged", "copiedRecordingUnchanged"])
    raise SystemExit(exit_code)


if __name__ == "__main__":
    main()
