"""Owned browser stage before the existing complete native demo controller."""

import json
import os
import signal
import select
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
        birth = process.create_time()
        fd = os.pidfd_open(child.pid, 0)

        def exited():
            return bool(select.select([fd], [], [], 0)[0])

        def verify():
            assert (
                process.create_time() == birth
                and process.ppid() == os.getpid()
                and process.uids().real == os.getuid()
            )

        # Node's test runner legitimately rewrites process.title/cmdline. The child
        # comes from our fixed Popen argv; bind its original pidfd, birth, parent/uid.
        verify()
        (output / f"{stage}-driver.private.json").write_text(
            json.dumps(
                {
                    "pid": child.pid,
                    "birth": birth,
                    "launchArgvDigest": digest(argv),
                    "observedCmdline": process.cmdline(),
                    "parentAndUidVerified": True,
                }
            )
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
                "originalBrowserDriverExited": exited(),
            }
        finally:
            if child.poll() is None:
                if not exited():
                    verify()
                    signal.pidfd_send_signal(fd, signal.SIGTERM, None, 0)
                child.wait(timeout=15)
            os.close(fd)
