"""Keyboard campaign creation against a freshly enrolled, explicitly approved target.

The default cohort only previews. --live explicitly selects the two complete-demo
create/cancel cases, retaining renderer, sensors, Android and real speed evidence.
No reference provider or original recording is executed or rewritten.
"""

import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import signal
import sqlite3
import subprocess
import sys
import uuid

from xverse_studio.host.ownership import own_root
from xverse_studio.security.managed_io import create_directory

_spec = importlib.util.spec_from_file_location(
    "fresh_campaign_native", Path(__file__).with_name("autoverse_lifecycle_conformance.py")
)
native = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(native)


def main():
    p = argparse.ArgumentParser()
    for name in ["receipt", "output", "static-dir", "node", "playwright-cli", "browser-cache"]:
        p.add_argument("--" + name, type=Path, required=True)
    p.add_argument("--live", action="store_true")
    p.add_argument("--grep")
    a = p.parse_args()
    for name, value in vars(a).items():
        if isinstance(value, Path):
            setattr(a, name, value.resolve())
    a.output.mkdir(parents=True, exist_ok=False)
    data = native.ROOT / ".studio-local/browser-tests" / ("fresh-campaign-keys-" + uuid.uuid4().hex)
    with create_directory(Path("/"), data, parents=True):
        pass
    (a.output / "data-root.private.json").write_text(json.dumps({"dataRoot": str(data)}) + "\n")
    (a.output / "data-root.private.json").chmod(0o600)
    host = native.NativeHost(data, a.output, a.receipt, Path(sys.executable), a.static_dir)
    outcome = {"scope": "Actual approved full Autoverse campaign keyboard" if a.live else "Actual admitted side-effect-free campaign preview keyboard; no model/guest start", "live": a.live, "outcome": "failed", "children": []}
    paths = ["apps", "services", "packages", "tests", "config", "scripts", "package.json", "package-lock.json", "pyproject.toml", "uv.lock"]
    names = [n for n in subprocess.check_output(["git", "ls-files", "--cached", "--others", "--exclude-standard", "-z", "--", *paths], cwd=native.ROOT, text=True).split("\0") if n]

    def sources():
        return {n: hashlib.sha256((native.ROOT / n).read_bytes()).hexdigest() for n in sorted(set(names))}

    def ui():
        return {f.relative_to(a.static_dir).as_posix(): hashlib.sha256(f.read_bytes()).hexdigest() for f in a.static_dir.rglob("*") if f.is_file()}

    def records(kind):
        with sqlite3.connect((data / "studio.sqlite").as_uri() + "?mode=ro", uri=True) as db:
            return [json.loads(raw) for (raw,) in db.execute("SELECT body FROM records WHERE kind=?", (kind,))]

    before, assets = sources(), ui()
    (a.output / "source-inputs.json").write_text(json.dumps(before, indent=2) + "\n")
    (a.output / "ui-inputs.json").write_text(json.dumps(assets, indent=2) + "\n")
    outcome["candidate"] = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=native.ROOT, text=True).strip()
    exit_code, projects, bases = 1, {}, {}
    api = None
    try:
        host.start()
        api = native.login(host)
        for width in [1024, 1440]:
            project, preflight = native.author(api)
            projects[str(width)] = project
            bases[preflight["snapshotId"]] = (data / "snapshots" / preflight["snapshotId"] / "snapshot.json").read_bytes()
        marker = {width: {"projectId": project["projectId"]} for width, project in projects.items()}
        (data / "fresh-campaign-keyboard.private.json").write_text(json.dumps(marker) + "\n")
        cookies = {"cookies": [{"name": c.name, "value": c.value, "domain": c.domain, "path": c.path, "secure": c.secure, "httpOnly": True, "sameSite": "Strict"} for c in api.cookies.jar]}
        session = data / "browser-session.private.json"
        session.write_text(json.dumps(cookies) + "\n")
        session.chmod(0o600)
        env = dict(os.environ, STUDIO_BASE_URL=host.url, STUDIO_BROWSER_DATA=str(data), STUDIO_BROWSER_REPORT=str(a.output / "browser.json"), STUDIO_BROWSER_OUTPUT=str(a.output / "artifacts"), PLAYWRIGHT_BROWSERS_PATH=str(a.browser_cache))
        argv = [str(a.node), str(a.playwright_cli), "test", "--config", "tests/live/autoverse-campaign-create-keyboard.config.ts", "--grep", a.grep or ("live fresh campaign" if a.live else "fresh campaign preview")]
        if not a.live:
            argv += ["--grep-invert", "live fresh campaign"]
        isolation_spec = importlib.util.spec_from_file_location("campaign_key_browser_isolation", Path(__file__).with_name("autoverse_playback_browser.py"))
        isolation = importlib.util.module_from_spec(isolation_spec)
        isolation_spec.loader.exec_module(isolation)
        env.update(STUDIO_BROWSER_CPU_ONLY="1", STUDIO_BROWSER_DEVICE_PROOF=str(a.output / "browser-device-proof.private.json"), STUDIO_BROWSER_HOST_MOUNT_NS=os.readlink("/proc/self/ns/mnt"))
        argv = isolation.device_free_browser_command(argv)
        (a.output / "command.private.json").write_text(json.dumps({"argv": argv, "dataRoot": str(data)}, indent=2) + "\n")
        with (a.output / "browser.log").open("xb") as log:
            child = subprocess.Popen(argv, cwd=native.ROOT, env=env, stdin=subprocess.DEVNULL, stdout=log, stderr=subprocess.STDOUT)
            process = native.psutil.Process(child.pid)
            birth = process.create_time()
            assert process.ppid() == os.getpid() and process.uids().real == os.getuid()
            try:
                exit_code = child.wait(timeout=1550 if a.live else 360)
            finally:
                if child.poll() is None:
                    assert process.create_time() == birth and process.ppid() == os.getpid()
                    child.terminate()
                    child.wait(timeout=30)
            outcome.update(originalBrowserExited=child.poll() is not None, browserExit=exit_code)
        campaigns = records("campaign")
        runs = records("run")
        assert len(campaigns) <= (2 if a.live else 0) and len(runs) <= (2 if a.live else 0)
        if exit_code == 0 and a.live:
            assert len(campaigns) == len(runs) == 2
        for campaign in campaigns:
            value = native.checked(api.get("/api/v1/campaigns/" + campaign["campaignId"]))
            if exit_code == 0:
                assert value["status"] == "cancelled" and [c["state"] for c in value["children"]] == ["stopped", "cancelled"], value
        for run in runs:
            rid = run["runId"]
            final = native.checked(api.get("/api/v1/runs/" + rid))
            assert final["state"] == "stopped" and final["cleanup"] == "complete", final
            frozen = json.loads((data / "snapshots" / run["snapshotId"] / "snapshot.json").read_bytes())
            assert frozen["configuration"]["durationSeconds"] == 60 and frozen["campaignId"] in {c["campaignId"] for c in campaigns}
            outcome["children"].append({"runId": rid, "snapshotId": run["snapshotId"], "cleanup": native.verify_released(data, rid)})
        outcome.update(campaigns=len(campaigns), runs=len(runs), originalProjectsUnchanged=all(native.checked(api.get("/api/v1/projects/" + project["projectId"])) == project for project in projects.values()), originalBaseSnapshotsUnchanged=all((data / "snapshots" / sid / "snapshot.json").read_bytes() == raw for sid, raw in bases.items()))
        assert outcome["originalProjectsUnchanged"] and outcome["originalBaseSnapshotsUnchanged"]
        if exit_code == 0:
            outcome["outcome"] = "passed"
    finally:
        try:
            if api is not None:
                for campaign in records("campaign"):
                    route = "/api/v1/campaigns/" + campaign["campaignId"]
                    current = native.checked(api.get(route))
                    if current["status"] not in {"complete", "cancelled"}:
                        native.checked(api.post(route + "/cancel", headers={"Idempotency-Key": "fresh-keyboard-cleanup-" + campaign["campaignId"]}, json={}), 202)
                        native.wait(lambda: native.checked(api.get(route)), lambda row: row["status"] in {"complete", "cancelled"}, timeout=150)
                api.close()
        finally:
            host.stop()
            with own_root(data):
                outcome["originalRootReleased"] = True
            outcome.update(hostShutdown=host.observations, sourceInputsUnchanged=sources() == before, uiInputsUnchanged=ui() == assets)
            (a.output / "verification.json").write_text(json.dumps(outcome, indent=2) + "\n")
            assert outcome["sourceInputsUnchanged"] and outcome["uiInputsUnchanged"]
    raise SystemExit(exit_code)


if __name__ == "__main__":
    def stop(_sig, _frame):
        raise KeyboardInterrupt("Contributor supervisor requested owned cleanup")

    signal.signal(signal.SIGTERM, stop)
    main()
