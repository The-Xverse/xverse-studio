"""Actual campaign inspection and read-only preflight on an independent recording copy.

No workload or campaign is created. The default planning suite registers the
prepared provider and freezes one copy-local preflight. The separate keyboard
suite reads retained history without registering a provider or creating inputs.
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


_spec = importlib.util.spec_from_file_location(
    "assessment_native_host",
    Path(__file__).with_name("autoverse_lifecycle_conformance.py"),
)
native = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(native)


def hashes(root):
    return {
        p.relative_to(root).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
        for folder in ("runs", "snapshots")
        for p in (root / folder).rglob("*")
        if p.is_file()
    }


def ledger(root):
    with sqlite3.connect(
        (root / "studio.sqlite").as_uri() + "?mode=ro", uri=True
    ) as db:
        counts = {
            kind: db.execute(
                "SELECT count(*) FROM records WHERE kind=?", (kind,)
            ).fetchone()[0]
            for kind in (
                "run",
                "operation",
                "evaluation",
                "snapshot",
                "campaign",
                "preflight",
            )
        }
        counts["idempotency"] = db.execute(
            "SELECT count(*) FROM idempotency"
        ).fetchone()[0]
        return counts


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--recording", required=True, type=Path)
    p.add_argument("--receipt", type=Path)
    p.add_argument("--suite", choices=("planning", "keyboard"), default="planning")
    p.add_argument("--isolate-browser-devices", action="store_true")
    p.add_argument("--output", required=True, type=Path)
    p.add_argument("--static-dir", required=True, type=Path)
    p.add_argument("--node", required=True, type=Path)
    p.add_argument("--playwright-cli", required=True, type=Path)
    p.add_argument("--browser-cache", required=True, type=Path)
    p.add_argument("--grep")
    a = p.parse_args()
    if a.suite == "planning" and a.receipt is None:
        p.error("The planning suite requires an explicit provider enrollment receipt")
    for field in (
        "recording",
        "receipt",
        "output",
        "static_dir",
        "node",
        "playwright_cli",
        "browser_cache",
    ):
        if getattr(a, field) is not None:
            setattr(a, field, getattr(a, field).resolve())
    a.output.mkdir(parents=True, exist_ok=False)
    result = json.loads((a.recording / "native-result.json").read_bytes())
    assert result["outcome"] == "passed"
    original = Path(
        json.loads((a.recording / "data-root.private.json").read_bytes())["dataRoot"]
    )
    before = hashes(original)
    database_before = hashlib.sha256((original / "studio.sqlite").read_bytes()).hexdigest()
    data = (
        native.ROOT
        / ".studio-local/browser-tests"
        / ("recorded-campaigns-" + uuid.uuid4().hex)
    )
    with own_root(original):
        assert all(not item.is_symlink() for item in original.rglob("*"))
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
            sqlite3.connect(data / "studio.sqlite") as dest,
        ):
            source.backup(dest)
            dest.execute("DELETE FROM records WHERE kind='session'")
    assert hashes(data) == before
    baseline = ledger(data)
    host = native.NativeHost(
        data, a.output, a.receipt, Path(sys.executable), a.static_dir,
        register_provider=a.suite == "planning",
    )
    outcome = {
        "scope": ("actual campaign inspection and one copy-local preflight; no new workload"
                  if a.suite == "planning" else "retained actual campaign keyboard inspection; no provider, preflight or workload"),
        "suite": a.suite,
        "before": baseline,
    }
    paths = [
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
    ]
    names = (
        subprocess.check_output(
            [
                "git",
                "ls-files",
                "--cached",
                "--others",
                "--exclude-standard",
                "-z",
                "--",
                *paths,
            ],
            cwd=native.ROOT,
        )
        .decode()
        .split("\0")
    )

    def inputs():
        return {
            name: hashlib.sha256((native.ROOT / name).read_bytes()).hexdigest()
            for name in sorted(set(names))
            if name and (native.ROOT / name).is_file()
        }

    source_before = inputs()
    ui_before = {
        v.relative_to(a.static_dir).as_posix(): hashlib.sha256(
            v.read_bytes()
        ).hexdigest()
        for v in a.static_dir.rglob("*")
        if v.is_file()
    }
    (a.output / "source-inputs.json").write_text(
        json.dumps(source_before, indent=2) + "\n"
    )
    outcome["sourceCandidate"] = subprocess.check_output(
        ["git", "rev-parse", "HEAD"], cwd=native.ROOT, text=True
    ).strip()
    outcome["uiFiles"] = ui_before
    exit_code = 1
    try:
        host.start()
        with closing(native.login(host)) as api:
            campaign = native.checked(
                api.get("/api/v1/campaigns/" + result["campaignId"])
            )
            assert campaign["status"] == "complete" and len(campaign["children"]) == 2
            private = {
                "projectId": result["projectId"],
                "campaignId": result["campaignId"],
                "baseSnapshotId": result["baseSnapshotId"],
                "children": campaign["children"],
            }
            private["children"] = [
                {
                    **child,
                    "snapshotId": native.checked(
                        api.get("/api/v1/runs/" + child["runId"])
                    )["snapshotId"],
                }
                for child in campaign["children"]
            ]
            (data / "campaign-recording.private.json").write_text(json.dumps(private))
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
                PLAYWRIGHT_BROWSERS_PATH=str(a.browser_cache),
            )
            argv = [
                str(a.node),
                str(a.playwright_cli),
                "test",
                "--config",
                {"planning": "tests/live/autoverse-campaigns.config.ts",
                 "keyboard": "tests/live/autoverse-campaign-keyboard.config.ts"}[a.suite],
            ]
            if a.isolate_browser_devices:
                spec = importlib.util.spec_from_file_location(
                    "campaign_browser_isolation", Path(__file__).with_name("autoverse_playback_browser.py"))
                isolation = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(isolation)
                env["STUDIO_BROWSER_CPU_ONLY"] = "1"
                env["STUDIO_BROWSER_DEVICE_PROOF"] = str(a.output / "browser-device-proof.private.json")
                env["STUDIO_BROWSER_HOST_MOUNT_NS"] = os.readlink("/proc/self/ns/mnt")
                argv = isolation.device_free_browser_command(argv)
            if a.grep:
                argv += ["--grep", a.grep]
            (a.output / "command.private.json").write_text(
                json.dumps({"argv": argv, "dataRoot": str(data)})
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
                assert (
                    process.ppid() == os.getpid() and process.uids().real == os.getuid()
                )
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
                outcome["browserExit"] = exit_code
            outcome["after"] = ledger(data)
            expected = baseline if a.suite == "keyboard" else {
                **baseline,
                "snapshot": baseline["snapshot"] + 1,
                "preflight": baseline["preflight"] + 1,
            }
            assert outcome["after"] == expected
    finally:
        host.stop()
        with own_root(data):
            outcome["originalRootReleased"] = True
        outcome["hostShutdown"] = host.observations
        outcome["sourceInputsUnchanged"] = inputs() == source_before
        outcome["uiInputsUnchanged"] = {
            v.relative_to(a.static_dir).as_posix(): hashlib.sha256(
                v.read_bytes()
            ).hexdigest()
            for v in a.static_dir.rglob("*")
            if v.is_file()
        } == ui_before
        outcome["originalRecordingUnchanged"] = hashes(original) == before
        outcome["originalDatabaseUnchanged"] = hashlib.sha256((original / "studio.sqlite").read_bytes()).hexdigest() == database_before
        copied_after = hashes(data)
        outcome["copiedOriginalRecordingUnchanged"] = all(
            copied_after.get(k) == v for k, v in before.items()
        )
        outcome["copyLocalNewSnapshotCount"] = len(set(copied_after) - set(before))
        assert outcome["copyLocalNewSnapshotCount"] == (0 if a.suite == "keyboard" else 1)
        (a.output / "verification.json").write_text(
            json.dumps(outcome, indent=2) + "\n"
        )
        assert all(
            outcome[key]
            for key in [
                "sourceInputsUnchanged",
                "uiInputsUnchanged",
                "originalRecordingUnchanged",
                "originalDatabaseUnchanged",
                "copiedOriginalRecordingUnchanged",
            ]
        )
    raise SystemExit(exit_code)


if __name__ == "__main__":
    main()
