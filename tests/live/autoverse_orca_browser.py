"""Opt-in native Linux Orca/AT-SPI verification on a private Autoverse recording copy.

Contributor-only bwrap/Xvfb/Orca prerequisites; no product runtime dependency.
Trusted executable paths are explicit CLI arguments, never imported project data.
"""

import argparse
import hashlib
from contextlib import closing
import importlib.util
import json
import os
from pathlib import Path
import select
import signal
import sqlite3
import subprocess
import sys
import time

import psutil

ROOT = Path(__file__).resolve().parents[2]
STATE = Path(__file__).resolve().parent
parser = argparse.ArgumentParser()
for name in ("recording", "static-dir", "output", "node", "browser-cache", "xvfb"):
    parser.add_argument("--" + name, type=Path, required=True)
parser.add_argument("--width", type=int, choices=(1024, 1440), required=True)
parser.add_argument("--source-exit", choices=("escape", "close-button"), default="escape")
parser.add_argument(
    "--suite",
    choices=(
        "retained-results",
        "scenario-conditions",
        "scenario-stimulus",
        "lab-inventory",
    ),
    default="retained-results",
)
a = parser.parse_args()
if a.source_exit != "escape" and a.suite != "scenario-stimulus":
    parser.error("--source-exit applies only to the scenario-stimulus suite")
for name in ("recording", "static_dir", "output", "node", "browser_cache", "xvfb"):
    setattr(a, name, getattr(a, name).resolve())


def terminate_owned_test(signum, frame):
    raise KeyboardInterrupt("Owned Orca verification interrupted")


signal.signal(signal.SIGTERM, terminate_owned_test)
spec = importlib.util.spec_from_file_location(
    "playback", ROOT / "tests/live/autoverse_playback_browser.py"
)
playback = importlib.util.module_from_spec(spec)
spec.loader.exec_module(playback)
native, exchange, recorded = playback.native, playback.exchange, playback.recorded
out = a.output
out.mkdir(mode=0o700, exist_ok=False)


def sha(data):
    return hashlib.sha256(data).hexdigest()


names = subprocess.check_output(
    [
        "git",
        "ls-files",
        "--cached",
        "--others",
        "--exclude-standard",
        "-z",
        "--",
        "apps",
        "services",
        "packages",
        "tests",
        "config",
        "scripts",
        "package.json",
        "package-lock.json",
        "pyproject.toml",
        "uv.lock",
    ],
    text=True,
).split("\0")


def inputs():
    return {
        p: sha((ROOT / p).read_bytes())
        for p in sorted(set(names))
        if p and (ROOT / p).is_file()
    }


source = inputs()
ui = a.static_dir


def assets():
    return {
        p.relative_to(ui).as_posix(): sha(p.read_bytes())
        for p in ui.rglob("*")
        if p.is_file()
    }


ui_before = assets()
(out / "source-inputs.json").write_text(json.dumps(source, indent=2) + "\n")
(out / "ui-inputs.json").write_text(json.dumps(ui_before, indent=2) + "\n")
recording = a.recording
result = json.loads((recording / "native-result.json").read_bytes())
assert result["outcome"] == "passed" and result["fullAndroidAndSpeedObserved"]
original = Path(
    json.loads((recording / "data-root.private.json").read_bytes())["dataRoot"]
)
original_hashes = recorded.hashes(original)
database = sha((original / "studio.sqlite").read_bytes())
data = out / "data"
project_id = json.loads(
    (original / "snapshots" / result["snapshotId"] / "snapshot.json").read_bytes()
)["projectId"]
exchange.clone(original, data)
canonical = recorded.hashes(data)


def project_files():
    return {
        p.relative_to(data).as_posix(): sha(p.read_bytes())
        for p in (data / "projects").rglob("*")
        if p.is_file()
    }


def protected_records():
    with sqlite3.connect(
        (data / "studio.sqlite").as_uri() + "?mode=ro", uri=True
    ) as db:
        return {
            (kind, key): body
            for kind, key, body in db.execute(
                "SELECT kind,id,body FROM records WHERE kind!='session'"
            )
        }


project_before = project_files()
records_before = protected_records()
(out / "projects-before-hashes.json").write_text(
    json.dumps(project_before, indent=2) + "\n"
)
(out / "protected-before.private.json").write_text(
    json.dumps(
        [[kind, key, body] for (kind, key), body in records_before.items()], indent=2
    )
    + "\n"
)
(out / "protected-before.private.json").chmod(0o600)
ledger = recorded.ledger(data)
host = native.NativeHost(
    data, out, None, Path(sys.executable), ui, register_provider=False
)
observed = {}
gaps = 0
run_result = {
    "candidate": subprocess.check_output(
        ["git", "rev-parse", "HEAD"], text=True
    ).strip(),
    "scope": "Actual Orca/AT-SPI on copied Autoverse retained data; no provider registration or workload",
    "before": ledger,
}
exit_code = 1
baseline = None
try:
    host.start()
    with closing(native.login(host)) as api:
        baseline = native.checked(api.get(f"/api/v1/projects/{project_id}"))
        (out / "project-before.private.json").write_text(
            json.dumps(baseline, indent=2) + "\n"
        )
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
    (out / "browser-session.private.json").write_text(json.dumps(cookies))
    (out / "browser-session.private.json").chmod(0o600)
    context = {
        "url": host.url,
        "runId": result["runId"],
        "snapshotId": result["snapshotId"],
        "projectId": json.loads(
            (
                original / "snapshots" / result["snapshotId"] / "snapshot.json"
            ).read_bytes()
        )["projectId"],
        "out": str(out),
        "node": str(a.node),
        "xvfb": str(a.xvfb),
        "width": a.width,
        "suite": a.suite,
        "sourceExit": a.source_exit,
        "hostMount": os.readlink("/proc/self/ns/mnt"),
        "hostPid": os.readlink("/proc/self/ns/pid"),
        "hostIpc": os.readlink("/proc/self/ns/ipc"),
    }
    (out / "context.private.json").write_text(json.dumps(context))
    env = {k: v for k, v in os.environ.items() if k in {"PATH", "LANG", "LC_ALL", "TZ"}}
    runtime = "/run/user/" + str(os.getuid())
    env.update(
        PATH="/usr/bin:/bin",
        LANG="en_US.UTF-8",
        GSETTINGS_BACKEND="memory",
        XDG_RUNTIME_DIR=runtime,
        XDG_CONFIG_HOME=runtime + "/config",
        XDG_CACHE_HOME=runtime + "/cache",
        XDG_DATA_HOME=runtime + "/data",
        NO_AT_BRIDGE="0",
        GTK_MODULES="gail:atk-bridge",
        LIBGL_ALWAYS_SOFTWARE="1",
        __GLX_VENDOR_LIBRARY_NAME="mesa",
        PLAYWRIGHT_BROWSERS_PATH=str(a.browser_cache),
    )
    argv = [
        "/usr/bin/bwrap",
        "--unshare-user",
        "--uid",
        str(os.getuid()),
        "--gid",
        str(os.getgid()),
        "--unshare-pid",
        "--unshare-ipc",
        "--ro-bind",
        "/",
        "/",
        "--bind",
        str(out),
        str(out),
        "--proc",
        "/proc",
        "--dev",
        "/dev",
        "--tmpfs",
        "/tmp",
        "--tmpfs",
        "/run",
        "--dir",
        runtime,
        "--chmod",
        "0700",
        runtime,
        "--die-with-parent",
        "--",
        "/usr/bin/dbus-run-session",
        "--",
        "/usr/bin/python3",
        "-I",
        str(STATE / "autoverse_orca_session.py"),
        str(out),
    ]
    (out / "command.private.json").write_text(
        json.dumps({"argv": argv, "environment": env}, indent=2) + "\n"
    )
    with (out / "driver.log").open("xb") as log:
        child = subprocess.Popen(
            argv,
            env=env,
            stdin=subprocess.DEVNULL,
            stdout=log,
            stderr=subprocess.STDOUT,
        )
        owner = psutil.Process(child.pid)
        birth = owner.create_time()
        fd = os.pidfd_open(child.pid)
        started = time.monotonic()
        try:
            while child.poll() is None:
                assert time.monotonic() - started < 180
                logs = [*out.glob("*.log"), *(out / "speech-logs").glob("*")]
                assert (
                    len(logs) <= 32
                    and sum(p.stat().st_size for p in logs if p.is_file())
                    < 64 * 1024 * 1024
                )
                for proc in [owner, *owner.children(recursive=True)]:
                    handle = None
                    try:
                        key = (proc.pid, proc.create_time())
                        if key in observed:
                            continue
                        assert len(observed) < 128 and proc.uids().real == os.getuid()
                        handle = os.pidfd_open(proc.pid)
                        assert proc.create_time() == key[1]
                        observed[key] = {
                            "pid": proc.pid,
                            "birth": key[1],
                            "argv": proc.cmdline(),
                            "fd": handle,
                        }
                        handle = None
                    except (
                        psutil.NoSuchProcess,
                        psutil.ZombieProcess,
                        psutil.AccessDenied,
                        ProcessLookupError,
                    ):
                        gaps += 1
                    finally:
                        if handle is not None:
                            os.close(handle)
                time.sleep(0.1)
            exit_code = child.wait(timeout=10)
        finally:
            if child.poll() is None:
                assert owner.create_time() == birth and owner.ppid() == os.getpid()
                signal.pidfd_send_signal(fd, signal.SIGTERM, None, 0)
                child.wait(timeout=15)
            os.close(fd)
    run_result["isolatedExit"] = exit_code
finally:
    host.stop()
    deadline = time.monotonic() + 10
    while any(not select.select([v["fd"]], [], [], 0)[0] for v in observed.values()):
        assert time.monotonic() < deadline
        time.sleep(0.1)
    for v in observed.values():
        os.close(v.pop("fd"))
    (out / "observed-processes.private.json").write_text(
        json.dumps(list(observed.values()), indent=2) + "\n"
    )
    with native.own_root(data):
        pass
    mutation = None
    mutation_error = None
    if a.suite in ("scenario-conditions", "scenario-stimulus"):
        verifier_spec = importlib.util.spec_from_file_location(
            "orca_authoring_readback", STATE / "autoverse_orca_authoring_records.py"
        )
        verifier = importlib.util.module_from_spec(verifier_spec)
        verifier_spec.loader.exec_module(verifier)
        try:
            if baseline is None:
                assert (
                    records_before == protected_records()
                    and project_before == project_files()
                )
                mutation = {"acceptedSemanticEdits": 0, "baselineReadNotReached": True}
            else:
                readback = {
                    "scenario-conditions": verifier.verify_conditions,
                    "scenario-stimulus": verifier.verify_stimulus,
                }[a.suite]
                mutation = readback(
                    records_before,
                    protected_records(),
                    project_before,
                    project_files(),
                    baseline,
                    data,
                    a.width,
                    exit_code == 0,
                )
        except AssertionError as problem:
            mutation_error = {
                "type": type(problem).__name__,
                "message": str(problem)[:512],
            }
    run_result.update(
        suite=a.suite,
        sourceExit=a.source_exit,
        copyMutationReadback=mutation,
        copyMutationReadbackError=mutation_error,
        copiedProjectsUnchanged=project_files() == project_before,
        copiedProtectedRecordsUnchanged=protected_records() == records_before,
        after=recorded.ledger(data),
        originalRecordingUnchanged=recorded.hashes(original) == original_hashes
        and sha((original / "studio.sqlite").read_bytes()) == database,
        copiedCanonicalUnchanged=recorded.hashes(data) == canonical,
        sourceInputsUnchanged=inputs() == source,
        uiInputsUnchanged=assets() == ui_before,
        originalRootReleased=True,
        hostObservations=host.observations,
        observedProcessesExited=len(observed),
        failedProcessCaptureAttempts=gaps,
        allShortLivedProcessesObserved=False,
    )
    (out / "verification.private.json").write_text(
        json.dumps(run_result, indent=2) + "\n"
    )
    assert run_result["before"] == run_result["after"] and all(
        run_result[k]
        for k in (
            "originalRecordingUnchanged",
            "copiedCanonicalUnchanged",
            "sourceInputsUnchanged",
            "uiInputsUnchanged",
        )
    )
    if a.suite in ("retained-results", "lab-inventory"):
        assert (
            run_result["copiedProjectsUnchanged"]
            and run_result["copiedProtectedRecordsUnchanged"]
        )
    else:
        assert mutation is not None
print(
    json.dumps(
        {
            "exit": exit_code,
            "observedProcessesExited": len(observed),
            "unchangedLedger": run_result["before"] == run_result["after"],
        }
    ),
    flush=True,
)
raise SystemExit(exit_code)
