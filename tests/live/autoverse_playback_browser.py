"""Read-only original Autoverse observation playback on a native copied workspace."""

import argparse
import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import uuid

from xverse_studio.host.ownership import own_root
from xverse_studio.storage.core import digest


_spec = importlib.util.spec_from_file_location(
    "exchange_native_tools", Path(__file__).with_name("autoverse_exchange_native.py")
)
exchange = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(exchange)
native, recorded = exchange.native, exchange.recorded


def device_free_browser_command(argv):
    """Optional Linux contributor isolation; never an application prerequisite."""
    wrapper = shutil.which("bwrap")
    if not sys.platform.startswith("linux") or wrapper is None:
        raise RuntimeError("BROWSER_DEVICE_ISOLATION_UNAVAILABLE")
    return [
        wrapper,
        "--unshare-user",
        "--uid",
        str(os.getuid()),
        "--gid",
        str(os.getgid()),
        "--ro-bind",
        "/",
        "/",
        "--bind",
        str(native.ROOT),
        str(native.ROOT),
        "--dev",
        "/dev",
        "--tmpfs",
        "/tmp",
        "--tmpfs",
        "/run",
        "--unsetenv",
        "DISPLAY",
        "--unsetenv",
        "WAYLAND_DISPLAY",
        "--unsetenv",
        "XAUTHORITY",
        "--unsetenv",
        "DBUS_SESSION_BUS_ADDRESS",
        "--die-with-parent",
        "--",
        *argv,
    ]


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--case-filter")
    p.add_argument(
        "--isolate-browser-devices",
        action="store_true",
        help="Linux contributor-only minimal /dev and software rendering; no application dependency.",
    )
    for name in (
        "recording",
        "static-dir",
        "output",
        "node",
        "playwright-cli",
        "browser-cache",
    ):
        p.add_argument("--" + name, type=Path, required=True)
    a = p.parse_args()
    a.output.mkdir(parents=True, exist_ok=False)
    result = json.loads((a.recording / "native-result.json").read_bytes())
    assert result["outcome"] == "passed" and result["fullAndroidAndSpeedObserved"]
    original = Path(
        json.loads((a.recording / "data-root.private.json").read_bytes())["dataRoot"]
    )
    before = recorded.hashes(original)
    database = digest((original / "studio.sqlite").read_bytes())
    data = (
        native.ROOT
        / ".studio-local/browser-tests"
        / ("recorded-payloads-Ω-" + uuid.uuid4().hex)
    )
    exchange.clone(original, data)
    rows = [
        json.loads(line)
        for line in (original / "runs" / result["runId"] / "evidence.jsonl")
        .read_bytes()
        .splitlines()
    ]
    observations = [row for row in rows if row["type"] == "observation.available"]
    assert len(observations) == 21
    snapshot = json.loads(
        (original / "snapshots" / result["snapshotId"] / "snapshot.json").read_bytes()
    )
    context = {
        "runId": result["runId"],
        "snapshotId": result["snapshotId"],
        "projectId": snapshot["projectId"],
        "records": observations,
    }
    (data / "playback-recording.private.json").write_text(json.dumps(context))
    baseline = recorded.ledger(data)
    host = native.NativeHost(
        data,
        a.output,
        None,
        Path(sys.executable),
        a.static_dir.resolve(),
        register_provider=False,
    )
    outcome = {
        "scope": "Actual original Autoverse observation record playback; separate labelled transport/integrity/shape fixtures; no new execution",
        "before": baseline,
        "originalObservationRecords": len(observations),
    }
    exit_code = 1
    try:
        host.start()
        api = native.login(host)
        try:
            cookies = {
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
            session = data / "browser-session.private.json"
            session.write_text(json.dumps(cookies))
            session.chmod(0o600)
            env = dict(
                os.environ,
                STUDIO_BASE_URL=host.url,
                STUDIO_BROWSER_DATA=str(data),
                STUDIO_BROWSER_REPORT=str(a.output / "browser.json"),
                STUDIO_BROWSER_OUTPUT=str(a.output / "artifacts"),
                PLAYWRIGHT_BROWSERS_PATH=str(a.browser_cache.resolve()),
            )
            argv = [
                str(a.node.resolve()),
                str(a.playwright_cli.resolve()),
                "test",
                "--config",
                "tests/live/autoverse-recorded-payloads.config.ts",
            ]
            if a.case_filter:
                argv.extend(["--grep", a.case_filter])
            if a.isolate_browser_devices:
                env["STUDIO_BROWSER_CPU_ONLY"] = "1"
                env["STUDIO_BROWSER_DEVICE_PROOF"] = str(
                    a.output.resolve() / "browser-device-proof.private.json"
                )
                env["STUDIO_BROWSER_HOST_MOUNT_NS"] = os.readlink("/proc/self/ns/mnt")
                argv = device_free_browser_command(argv)
            (a.output / "command.private.json").write_text(
                json.dumps({"argv": argv}, indent=2) + "\n"
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
                owner = native.psutil.Process(child.pid)
                birth = owner.create_time()
                native.wait(
                    lambda: owner.cmdline() == argv and owner.ppid() == os.getpid(),
                    bool,
                    timeout=3,
                )
                (a.output / "browser-owner.private.json").write_text(
                    json.dumps({"pid": child.pid, "birth": birth, "argv": argv}) + "\n"
                )
                try:
                    exit_code = child.wait(timeout=360)
                finally:
                    if child.poll() is None:
                        assert (
                            owner.create_time() == birth
                            and owner.ppid() == os.getpid()
                            and owner.cmdline() == argv
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
        outcome["originalRecordingUnchanged"] = (
            recorded.hashes(original) == before
            and digest((original / "studio.sqlite").read_bytes()) == database
        )
        copied = recorded.hashes(data)
        outcome["copiedOriginalCanonicalUnchanged"] = all(
            copied.get(k) == v for k, v in before.items()
        )
        outcome["backendShutdown"] = host.observations
        outcome["browserExit"] = exit_code
        (a.output / "data-root.private.json").write_text(
            json.dumps({"dataRoot": str(data)}) + "\n"
        )
        (a.output / "verification.json").write_text(
            json.dumps(outcome, indent=2) + "\n"
        )
    assert (
        outcome["originalRecordingUnchanged"]
        and outcome["copiedOriginalCanonicalUnchanged"]
    )
    raise SystemExit(exit_code)


if __name__ == "__main__":
    main()
