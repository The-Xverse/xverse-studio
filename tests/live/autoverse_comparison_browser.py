"""Read-only comparison UI on independent copies of actual native recordings."""

import argparse
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

_spec = importlib.util.spec_from_file_location(
    "recorded_comparison_tools",
    Path(__file__).with_name("autoverse_campaign_browser.py"),
)
recorded = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(recorded)
native = recorded.native


def main():
    p = argparse.ArgumentParser()
    for name in (
        "recording",
        "static-dir",
        "output",
        "node",
        "playwright-cli",
        "browser-cache",
    ):
        p.add_argument("--" + name, type=Path, required=True)
    p.add_argument("--receipt", type=Path)
    p.add_argument("--recorded-only", action="store_true",
                   help="Inspect without installing a runtime provider; rerun stays unavailable.")
    p.add_argument("--isolate-browser-devices", action="store_true")
    a = p.parse_args()
    if not a.recorded_only and a.receipt is None:
        p.error("--receipt is required unless --recorded-only is selected")
    a.output.mkdir(parents=True, exist_ok=False)
    result = json.loads((a.recording / "native-result.json").read_bytes())
    assert result["outcome"] in {"passed", "failed"}
    original = Path(
        json.loads((a.recording / "data-root.private.json").read_bytes())["dataRoot"]
    )
    before = recorded.hashes(original)
    data = (
        native.ROOT
        / ".studio-local/browser-tests"
        / ("recorded-comparison-" + uuid.uuid4().hex)
    )
    with own_root(original):
        assert all(not f.is_symlink() for f in original.rglob("*"))
        shutil.copytree(
            original,
            data,
            ignore=shutil.ignore_patterns(
                "studio.lock",
                "studio.sqlite*",
                "browser-session.private.json",
                "bootstrap.json",
            ),
        )
        with (
            sqlite3.connect(
                (original / "studio.sqlite").as_uri() + "?mode=ro", uri=True
            ) as source,
            sqlite3.connect(data / "studio.sqlite") as target,
        ):
            source.backup(target)
            target.execute("DELETE FROM records WHERE kind='session'")
    assert recorded.hashes(data) == before
    baseline = recorded.ledger(data)
    context = {
        k: result[k]
        for k in (
            "projectId",
            "runId",
            "snapshotId",
            "sourceRunId",
            "sourceSnapshotId",
            "rerunOperationId",
        )
    }
    with sqlite3.connect(
        (data / "studio.sqlite").as_uri() + "?mode=ro", uri=True
    ) as db:
        runs = [
            json.loads(r[0])
            for r in db.execute("SELECT body FROM records WHERE kind='run'")
        ]
    siblings = [
        r
        for r in runs
        if r["projectId"] == context["projectId"]
        and r["runId"] not in (context["runId"], context["sourceRunId"])
    ]
    assert len(siblings) == 1
    context["siblingRunId"] = siblings[0]["runId"]
    selected = next(r for r in runs if r["runId"] == context["runId"])
    source_run = next(r for r in runs if r["runId"] == context["sourceRunId"])
    assert source_run["state"] == "stopped" and source_run["cleanup"] == "complete"
    if result["outcome"] == "failed":
        assert (
            selected["state"] == "failed"
            and selected["cleanup"] == "complete"
            and selected["reason"] == "AUTOVERSE_CARLA_NOT_READY"
        )
    else:
        assert result["fullAndroidAndSpeedObserved"] and selected["state"] == "stopped"
    context["selectedState"] = selected["state"]
    if a.recorded_only:
        journal_records = [
            json.loads(line)
            for line in (original / "runs" / result["runId"] / "evidence.jsonl").read_bytes().splitlines()
        ]
        context["originalObservations"] = [row for row in journal_records if row["type"] == "observation.available"]
        assert context["originalObservations"]
    (data / "comparison-recording.private.json").write_text(json.dumps(context))
    (data / "comparison-recording.private.json").chmod(0o600)
    (a.output / "data-root.private.json").write_text(
        json.dumps({"dataRoot": str(data)}) + "\n"
    )
    host = native.NativeHost(
        data,
        a.output,
        a.receipt.resolve() if a.receipt else None,
        Path(sys.executable),
        a.static_dir.resolve(),
        register_provider=not a.recorded_only,
    )
    outcome = {
        "scope": "Actual recorded comparison and disabled unsupported playback; no new preflight, workload, operation or evaluation",
        "before": baseline,
        "sourceNativeOutcome": result["outcome"],
        "selectedExecutionState": selected["state"],
        "fullRerunExecutionVerified": result["outcome"] == "passed",
        "acknowledgementFixture": "The initial POST acknowledgement uses the retained actual operation; child-provider corruption is a labelled transport fixture. No new admission or Start.",
        "installedAutoverseProviderRegistered": not a.recorded_only,
    }
    if a.recorded_only:
        outcome["acknowledgementFixture"] = "NOT_RUN; no provider installed or acknowledgement fixture used."
    exit_code = 1
    try:
        host.start()
        api = native.login(host)
        try:
            session = data / "browser-session.private.json"
            session.write_text(
                json.dumps(
                    {
                        "cookies": [
                            {
                                "name": c.name,
                                "value": c.value,
                                "domain": c.domain,
                                "path": c.path,
                                "secure": c.secure,
                                "httpOnly": True,
                                "sameSite": "Strict",
                            }
                            for c in api.cookies.jar
                        ]
                    }
                )
            )
            session.chmod(0o600)
            env = dict(
                os.environ,
                STUDIO_BASE_URL=host.url,
                STUDIO_BROWSER_DATA=str(data),
                STUDIO_BROWSER_REPORT=str(a.output / "browser.json"),
                STUDIO_BROWSER_OUTPUT=str(a.output / "artifacts"),
                PLAYWRIGHT_BROWSERS_PATH=str(a.browser_cache.resolve()),
                STUDIO_BROWSER_RECORDED_ONLY="1" if a.recorded_only else "0",
            )
            argv = [
                str(a.node.resolve()),
                str(a.playwright_cli.resolve()),
                "test",
                "--config",
                "tests/live/autoverse-comparison.config.ts",
            ]
            if a.isolate_browser_devices:
                isolation_spec = importlib.util.spec_from_file_location(
                    "recorded_playback_isolation", Path(__file__).with_name("autoverse_playback_browser.py")
                )
                isolation = importlib.util.module_from_spec(isolation_spec)
                isolation_spec.loader.exec_module(isolation)
                env["STUDIO_BROWSER_CPU_ONLY"] = "1"
                env["STUDIO_BROWSER_DEVICE_PROOF"] = str(a.output.resolve() / "browser-device-proof.private.json")
                env["STUDIO_BROWSER_HOST_MOUNT_NS"] = os.readlink("/proc/self/ns/mnt")
                argv = isolation.device_free_browser_command(argv)
            (a.output / "command.private.json").write_text(
                json.dumps({"argv": argv, "context": context}, indent=2) + "\n"
            )
            with (a.output / "browser.log").open("xb") as log:
                child = subprocess.Popen(
                    argv,
                    cwd=native.ROOT,
                    env=env,
                    stdin=subprocess.DEVNULL,
                    stdout=log,
                    stderr=subprocess.STDOUT,
                )
                process = native.psutil.Process(child.pid)
                birth = process.create_time()
                try:
                    exit_code = child.wait(timeout=240)
                finally:
                    if child.poll() is None:
                        assert (
                            process.create_time() == birth
                            and process.ppid() == os.getpid()
                        )
                        child.terminate()
                        child.wait(timeout=30)
                outcome["originalBrowserExited"] = child.poll() is not None
            outcome["after"] = recorded.ledger(data)
            assert outcome["after"] == baseline
        finally:
            api.close()
    finally:
        host.stop()
        with own_root(data):
            outcome["originalRootReleased"] = True
        outcome["originalRecordingUnchanged"] = recorded.hashes(original) == before
        outcome["copiedRecordingUnchanged"] = recorded.hashes(data) == before
        outcome["backendShutdown"] = host.observations
        outcome["browserExit"] = exit_code
        (a.output / "verification.json").write_text(
            json.dumps(outcome, indent=2) + "\n"
        )
    assert outcome["originalRecordingUnchanged"] and outcome["copiedRecordingUnchanged"]
    raise SystemExit(exit_code)


if __name__ == "__main__":
    main()
