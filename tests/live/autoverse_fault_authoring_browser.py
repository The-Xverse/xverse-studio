"""Owned browser stage before the existing complete native demo controller."""

import json
import os
import signal
import subprocess
import time
from xverse_studio.storage.core import digest


def author(native, host, api, project, output, node, cli, cache, *, stage="authoring"):
    assert stage in {"authoring", "timeline"}
    data = host.data
    (data / "fault-authoring-project.private.json").write_text(json.dumps(project))
    session = {
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
    private = data / "browser-session.private.json"
    if not private.exists():
        with private.open("x") as stream:
            os.chmod(private, 0o600)
            json.dump(session, stream)
    env = dict(
        os.environ,
        STUDIO_BASE_URL=host.url,
        STUDIO_AUTOVERSE_BROWSER_STAGE=stage,
        STUDIO_BROWSER_DATA=str(data),
        STUDIO_BROWSER_REPORT=str(output / f"{stage}-browser.json"),
        STUDIO_BROWSER_OUTPUT=str(output / f"{stage}-artifacts"),
        PLAYWRIGHT_BROWSERS_PATH=str(cache),
    )
    argv = [
        str(node),
        str(cli),
        "test",
        "--config",
        "tests/live/autoverse-fault-authoring.config.ts",
    ]
    (output / f"{stage}-command.private.json").write_text(
        json.dumps({"argv": argv, "dataRoot": str(data)})
    )
    with (output / f"{stage}-browser.log").open("x") as log:
        child = subprocess.Popen(
            argv,
            cwd=native.ROOT,
            env=env,
            stdin=subprocess.DEVNULL,
            stdout=log,
            stderr=subprocess.STDOUT,
        )
        process = native.psutil.Process(child.pid)
        original = native.OriginalProcess(
            child.pid, process.create_time(), digest(argv), parent=os.getpid()
        )
        try:
            deadline = time.monotonic() + 240
            while child.poll() is None and time.monotonic() < deadline:
                time.sleep(0.1)
            assert child.poll() == 0, (
                "Actual Autoverse browser authoring failed; see retained report."
            )
            report = json.loads((output / f"{stage}-browser.json").read_bytes())
            assert report["stats"]["expected"] == 1 and all(
                report["stats"][k] == 0 for k in ["unexpected", "skipped", "flaky"]
            )
            return {
                "passed": 1,
                "viewports": [1024, 1440],
                "originalBrowserDriverExited": original.exited(),
            }
        finally:
            if child.poll() is None:
                original.send(signal.SIGTERM)
                child.wait(timeout=15)
            original.close()
