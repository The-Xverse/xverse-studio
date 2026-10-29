"""Record an exact native verification environment without collecting secrets or hostnames."""

import argparse
import hashlib
from importlib.metadata import version
import json
import os
from pathlib import Path
import platform
import shutil
import subprocess
import sys
import psutil

root = Path(__file__).resolve().parents[1]
parser = argparse.ArgumentParser()
parser.add_argument("--output", type=Path, required=True)
args = parser.parse_args()
node = shutil.which("node")
linux = {}
if sys.platform == "linux":
    for line in Path("/etc/os-release").read_text().splitlines():
        if "=" in line:
            key, value = line.split("=", 1)
            if key in ("ID", "VERSION_ID", "PRETTY_NAME"):
                linux[key] = value.strip('"')
result = {
    "scope": "native_verification_environment",
    "gitCandidate": subprocess.check_output(
        ["git", "rev-parse", "HEAD"], cwd=root, text=True
    ).strip(),
    "os": platform.system(),
    "release": platform.release(),
    "version": platform.version(),
    "architecture": platform.machine(),
    "distribution": linux,
    "windows": {
        "release": platform.win32_ver(),
        "edition": platform.win32_edition() if os.name == "nt" else None,
    },
    "python": platform.python_version(),
    "node": subprocess.check_output([node, "--version"], text=True).strip()
    if node
    else None,
    "cpuLogicalCount": psutil.cpu_count(),
    "memoryBytes": psutil.virtual_memory().total,
    "packages": {
        name: version(name)
        for name in [
            "xverse-studio",
            "xverse-xdl",
            "fastapi",
            "pydantic",
            "uvicorn",
            "psutil",
            "jsonschema",
            "referencing",
            "ruamel.yaml",
            "pytest",
            "httpx",
        ]
    },
    "providerScope": "owned_reference; external and physical admission recorded separately",
}
paths = subprocess.check_output(
    [
        "git",
        "ls-files",
        "--",
        "services",
        "apps",
        "scripts",
        "tests",
        "packages",
        "config",
        "pyproject.toml",
        "uv.lock",
        "package.json",
        "package-lock.json",
    ],
    cwd=root,
    text=True,
).splitlines()
result["sourceFiles"] = {
    name: hashlib.sha256((root / name).read_bytes()).hexdigest()
    for name in paths
    if (root / name).is_file()
}
result["sourceDigest"] = (
    "sha256:"
    + hashlib.sha256(
        json.dumps(
            result["sourceFiles"], sort_keys=True, separators=(",", ":")
        ).encode()
    ).hexdigest()
)
args.output.parent.mkdir(parents=True, exist_ok=True)
args.output.write_text(json.dumps(result, indent=2) + "\n")
print(
    json.dumps(
        {k: v for k, v in result.items() if k not in ("sourceFiles", "packages")}
    )
)
