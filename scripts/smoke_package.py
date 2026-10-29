"""Provision and launch a fresh package extraction using only native executable argv."""

from pathlib import Path
import argparse
import json
import os
import shutil
import socket
import subprocess
import sys
import time
import uuid
import zipfile
import httpx

root = Path(__file__).resolve().parents[1]
parser = argparse.ArgumentParser()
parser.add_argument(
    "--output", type=Path, default=root / "evidence/local/package-smoke.json"
)
args = parser.parse_args()
work = root / ".studio-local/package-smoke" / uuid.uuid4().hex
work.mkdir(parents=True)
archive = work / "studio.zip"
created = subprocess.run(
    [sys.executable, str(root / "scripts/package_studio.py"), "--output", str(archive)],
    cwd=root,
    capture_output=True,
    text=True,
)
if created.returncode:
    raise SystemExit(created.stderr)
with zipfile.ZipFile(archive) as z:
    z.extractall(work / "extracted")
installed = work / "extracted/xverse-studio"
uv = shutil.which("uv")
if not uv:
    raise SystemExit("The pinned uv tool is required for native package provisioning.")
env = dict(os.environ)
cache = os.environ.get("UV_CACHE_DIR")
provision = subprocess.run(
    [uv, "sync", "--frozen", "--no-dev", "--offline", "--project", str(installed)],
    env=env,
    capture_output=True,
    text=True,
)
result = {
    "scope": "fresh_local_package_extraction_offline_with_prepared_dependency_cache",
    "package": json.loads(created.stdout),
    "provisionExit": provision.returncode,
    "os": sys.platform,
    "python": sys.version.split()[0],
    "usedPreparedCache": True,
    "browserWorkflow": "covered separately by native browser tests",
    "windows": "NOT_RUN on this host"
    if os.name != "nt"
    else "native process test host",
}
if provision.returncode:
    result["outcome"] = "failed"
    result["diagnostic"] = provision.stderr[-2000:]
else:
    native = installed / (
        ".venv/Scripts/python.exe" if os.name == "nt" else ".venv/bin/python"
    )
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        port = sock.getsockname()[1]
    data = work / "Native package Ω data"
    url = f"http://127.0.0.1:{port}"
    backend = subprocess.Popen(
        [
            str(native),
            "-I",
            "-m",
            "xverse_studio.host.launcher",
            "--data-dir",
            str(data),
            "--port",
            str(port),
        ],
        stdin=subprocess.DEVNULL,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    try:
        deadline = time.monotonic() + 15
        while time.monotonic() < deadline:
            try:
                if httpx.get(url + "/api/v1/session", timeout=1).status_code == 401:
                    break
            except httpx.HTTPError:
                pass
            time.sleep(0.1)
        else:
            raise RuntimeError("Packaged native backend did not become ready.")
        with httpx.Client(base_url=url, headers={"Origin": url}) as client:
            bootstrap = json.loads((data / "bootstrap.json").read_text())
            auth = client.post(
                "/api/v1/session", json={"bootstrapToken": bootstrap["bootstrapToken"]}
            )
            auth.raise_for_status()
            client.headers["X-CSRF-Token"] = auth.json()["csrfToken"]
            index = client.get("/")
            assert index.status_code == 200 and "assets/" in index.text
            project = client.post(
                "/api/v1/projects", json={"name": "Fresh packaged System Ω"}
            )
            project.raise_for_status()
            p = project.json()
            check = client.post(
                f"/api/v1/projects/{p['projectId']}/compilations",
                json={"revision": p["revision"]},
            )
            check.raise_for_status()
            assert check.json()["valid"]
            result.update(
                outcome="passed",
                staticIndexHTTP=index.status_code,
                projectPersisted=True,
                authoritativeCompilation=True,
                planDigest=check.json()["planDigest"],
            )
    except Exception as e:
        result.update(outcome="failed", diagnostic=type(e).__name__)
    finally:
        backend.terminate()
        try:
            backend.wait(timeout=10)
        except subprocess.TimeoutExpired:
            backend.kill()
            backend.wait(timeout=5)
args.output.parent.mkdir(parents=True, exist_ok=True)
args.output.write_text(json.dumps(result, indent=2) + "\n")
print(json.dumps({k: v for k, v in result.items() if k != "diagnostic"}))
raise SystemExit(0 if result["outcome"] == "passed" else 1)
