"""Build a native-installable source bundle with the compiled browser UI and pinned locks."""

from pathlib import Path
import argparse
import hashlib
import json
import subprocess
import zipfile

root = Path(__file__).resolve().parents[1]
parser = argparse.ArgumentParser()
parser.add_argument(
    "--output", type=Path, default=root / "dist/xverse-studio-reference.zip"
)
args = parser.parse_args()
if not (root / "apps/studio-web/dist/index.html").is_file():
    parser.error("Build the frontend with npm ci and npm run build first.")
if args.output.exists():
    parser.error("Refusing to overwrite an existing package; choose a new output path.")
files = []
for directory in [
    "services/studio-api",
    "apps/studio-web/dist",
    "scripts",
    "docs/user",
    "docs/providers",
    "docs/releases",
    "config",
    "packages/contracts",
]:
    for p in (root / directory).rglob("*"):
        if (
            p.is_file()
            and not any(
                x in ("__pycache__", ".venv", "node_modules")
                for x in p.relative_to(root).parts
            )
            and p.suffix not in (".pyc", ".log")
        ):
            files.append(p)
for name in ["pyproject.toml", "uv.lock", ".python-version", "README.md", "LICENSE"]:
    files.append(root / name)
manifest = {
    "formatVersion": "1.0",
    "scope": "owned_reference_implementation",
    "candidate": subprocess.check_output(
        ["git", "rev-parse", "HEAD"], cwd=root, text=True
    ).strip(),
    "nativeVerification": {
        "Linux": "see candidate evidence",
        "Windows": "NOT_RUN unless separate CI evidence proves this candidate",
    },
    "files": {
        str(p.relative_to(root)).replace("\\", "/"): "sha256:"
        + hashlib.sha256(p.read_bytes()).hexdigest()
        for p in sorted(set(files))
    },
    "limitations": [
        "External Lite/CARLA and hardware providers are unavailable.",
        "Native target installation requires Python3.13 and uv0.12.17; first provisioning resolves the pinned Git dependency.",
        "No Studio1.0 release claim. M5 deferred.",
    ],
}
manifest["workingTreeDirty"] = bool(
    subprocess.check_output(
        ["git", "status", "--porcelain"], cwd=root, text=True
    ).strip()
)
manifest["sourceTreeDigest"] = (
    "sha256:"
    + hashlib.sha256(
        json.dumps(manifest["files"], sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()
)
args.output.parent.mkdir(parents=True, exist_ok=True)
with zipfile.ZipFile(args.output, "x", compression=zipfile.ZIP_DEFLATED) as z:
    for p in sorted(set(files)):
        z.write(p, "xverse-studio/" + p.relative_to(root).as_posix())
    z.writestr(
        "xverse-studio/package-manifest.json", json.dumps(manifest, indent=2) + "\n"
    )
print(
    json.dumps(
        {
            "package": args.output.name,
            "sha256": hashlib.sha256(args.output.read_bytes()).hexdigest(),
            "files": len(set(files)),
            "candidate": manifest["candidate"],
        }
    )
)
