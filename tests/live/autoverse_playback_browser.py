"""Original Autoverse playback and draft-only journeys on a native copied workspace."""

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
    p.add_argument("--suite", choices=("playback", "diagnostics", "authoring", "lab-inventory"), default="playback")
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
    for name in ("recording", "static_dir", "output", "node", "playwright_cli", "browser_cache"):
        setattr(a, name, getattr(a, name).resolve())
    a.output.mkdir(parents=True, exist_ok=False)
    source_names = subprocess.check_output([
        "git", "ls-files", "--cached", "--others", "--exclude-standard", "-z", "--",
        "apps", "services", "packages", "tests", "config", "scripts", "package.json",
        "package-lock.json", "pyproject.toml", "uv.lock",
    ], cwd=native.ROOT).decode().split("\0")

    def source_inputs():
        return {name: digest((native.ROOT / name).read_bytes()) for name in sorted(set(source_names))
                if name and (native.ROOT / name).is_file()}

    def ui_inputs():
        return {file.relative_to(a.static_dir).as_posix(): digest(file.read_bytes())
                for file in a.static_dir.rglob("*") if file.is_file()}

    source_before, ui_before = source_inputs(), ui_inputs()
    (a.output / "source-inputs.json").write_text(json.dumps(source_before, indent=2) + "\n")
    (a.output / "ui-inputs.json").write_text(json.dumps(ui_before, indent=2) + "\n")
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
        "scope": "Actual original Autoverse recording; playback/diagnosis or copy-local draft authoring; separate labelled HTTP fixtures; no new execution",
        "suite": a.suite,
        "sourceCandidate": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=native.ROOT, text=True).strip(),
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
                {
                    "playback": "tests/live/autoverse-recorded-payloads.config.ts",
                    "diagnostics": "tests/live/autoverse-diagnostic-keyboard.config.ts",
                    "authoring": "tests/live/autoverse-authoring-keyboard.config.ts",
                    "lab-inventory": "tests/live/autoverse-lab-inventory-keyboard.config.ts",
                }[a.suite],
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
        outcome["sourceInputsUnchanged"] = source_inputs() == source_before
        outcome["uiInputsUnchanged"] = ui_inputs() == ui_before
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
        and outcome["sourceInputsUnchanged"]
        and outcome["uiInputsUnchanged"]
    )
    raise SystemExit(exit_code)


if __name__ == "__main__":
    main()
