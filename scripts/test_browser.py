"""Run browser checks against an isolated real native launcher on either host OS."""

from pathlib import Path
import argparse
import os
import shutil
import socket
import subprocess
import sys
import time
import uuid
import httpx

root = Path(__file__).resolve().parents[1]
parser = argparse.ArgumentParser()
parser.add_argument("--performance", action="store_true")
parser.add_argument(
    "--grep",
    help="Run matching Playwright test names against the isolated native backend.",
)
args = parser.parse_args()
data = root / ".studio-local" / "browser-tests" / uuid.uuid4().hex
data.mkdir(parents=True)
with socket.socket() as sock:
    sock.bind(("127.0.0.1", 0))
    port = sock.getsockname()[1]
url = f"http://127.0.0.1:{port}"
process = subprocess.Popen(
    [
        sys.executable,
        "-I",
        "-m",
        "xverse_studio.host.launcher",
        "--data-dir",
        str(data),
        "--port",
        str(port),
        "--static-dir",
        str(root / "apps/studio-web/dist"),
    ],
    stdin=subprocess.DEVNULL,
    stdout=subprocess.DEVNULL,
    stderr=subprocess.DEVNULL,
    cwd=root,
)
try:
    deadline = time.monotonic() + 20
    while time.monotonic() < deadline:
        try:
            if httpx.get(url + "/api/v1/session", timeout=1).status_code == 401:
                break
        except httpx.HTTPError:
            pass
        time.sleep(0.1)
    else:
        raise RuntimeError("Native browser-test backend did not become ready.")
    node = shutil.which("node")
    npm = shutil.which("npm")
    if not node or not npm:
        raise RuntimeError(
            "The pinned Node/npm toolchain is required for contributor browser checks."
        )
    cli = Path(node).resolve().parent / "node_modules/npm/bin/npm-cli.js"
    if not cli.exists():
        cli = Path(npm).resolve()
    env = dict(
        os.environ,
        STUDIO_BASE_URL=url,
        STUDIO_BROWSER_DATA=str(data),
        STUDIO_BROWSER_REPORT=str(root / "test-results/browser-report.json"),
        STUDIO_BROWSER_OUTPUT=str(root / "test-results/browser"),
    )
    if args.performance:
        env["STUDIO_PERFORMANCE"] = "1"
    command = [node, str(cli), "run", "test:e2e"]
    if args.grep:
        command.extend(["--", "--grep", args.grep])
    result = subprocess.run(command, cwd=root, env=env)
    raise SystemExit(result.returncode)
finally:
    process.terminate()
    try:
        process.wait(timeout=15)
    except subprocess.TimeoutExpired:
        process.kill()
        process.wait(timeout=5)
