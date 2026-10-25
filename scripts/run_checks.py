"""Cross-platform checks; isolates unrelated host pytest plugins and contributor temp files."""

from pathlib import Path
import os
import subprocess
import sys
import uuid

root = Path(__file__).resolve().parents[1]
temp = root / ".studio-local" / "test-tmp" / uuid.uuid4().hex
temp.mkdir(parents=True)
env = dict(
    os.environ,
    PYTEST_DISABLE_PLUGIN_AUTOLOAD="1",
    TMPDIR=str(temp),
    TEMP=str(temp),
    TMP=str(temp),
)
commands = [
    [sys.executable, str(root / "scripts/validate_spec_package.py")],
    [sys.executable, str(root / "scripts/check_architecture.py")],
    [
        sys.executable,
        "-I",
        "-m",
        "pytest",
        str(root / "tests"),
        "--basetemp=" + str(temp / "pytest"),
        "-q",
        "--tb=short",
    ],
]
for command in commands:
    result = subprocess.run(command, cwd=root, env=env)
    if result.returncode:
        raise SystemExit(result.returncode)
