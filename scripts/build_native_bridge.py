"""Build the Studio-owned bridge against an explicitly admitted local native SDK.

Contributor/host administration only. Never called by project loading or HTTP.
Imports existing static libraries; does not modify or build companion sources.
"""
import argparse
import hashlib
from importlib.metadata import distribution
import json
import os
from pathlib import Path
import platform
import subprocess

from xverse_studio.xdl import PLATFORM_REVISION


def sha256(path):
    with path.open("rb") as stream:
        return "sha256:" + hashlib.file_digest(stream, "sha256").hexdigest()


def command(argv, *, cwd=None):
    return subprocess.run(argv, cwd=cwd, stdin=subprocess.DEVNULL, capture_output=True,
                          text=True, check=True, timeout=120).stdout


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--platform-source", required=True, type=Path)
    parser.add_argument("--platform-build", required=True, type=Path)
    parser.add_argument("--third-party-include", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    if platform.system() != "Linux" or platform.machine() != "x86_64":
        raise SystemExit("This native bridge build is currently verified only for Linux x86_64.")
    source, build, third = (p.resolve(strict=True) for p in
                             (args.platform_source, args.platform_build, args.third_party_include))
    provenance = json.loads(distribution("xverse-xdl").read_text("direct_url.json"))
    if provenance.get("vcs_info", {}).get("commit_id") != PLATFORM_REVISION:
        raise SystemExit("Installed SDK revision differs from the Studio pin.")
    if command(["git", "rev-parse", "HEAD"], cwd=source).strip() != PLATFORM_REVISION:
        raise SystemExit("Explicit native source is not the accepted SDK revision.")
    command(["git", "diff", "--exit-code", "HEAD", "--", "src/xverse/xcom", "cmake", "CMakeLists.txt"], cwd=source)
    cache = (build / "CMakeCache.txt").read_text()
    if "CMAKE_HOME_DIRECTORY:INTERNAL=" + str(source) + "\n" not in cache:
        raise SystemExit("Native build belongs to another source checkout.")
    dry_run = command(["ninja", "-C", str(build), "-n", "xverse_xcom_provider_loopback"])
    if "no work to do" not in dry_run:
        raise SystemExit("Native SDK artifacts require verification/rebuild before bridge admission.")
    libraries = {name: sha256(build / "src/xverse/xcom" / ("libxverse_xcom_" + name + ".a"))
                 for name in ("provider_loopback", "endpoint_route_lifecycle", "observation", "core_types")}
    headers = {p.relative_to(third).as_posix(): sha256(p) for p in sorted((third / "nlohmann").rglob("*.hpp"))}
    if not headers or not (third / "nlohmann/json.hpp").is_file():
        raise SystemExit("Admitted nlohmann headers are missing.")
    root = Path(__file__).resolve().parents[1]
    owned_source = root / "services/studio-api/native/xcom_bridge"
    output = args.output.absolute()
    output.mkdir(parents=True, mode=0o700, exist_ok=True)
    if output != output.resolve() or output.stat().st_mode & 0o022:
        raise SystemExit("Use a private native bridge output directory without symlinks.")
    configure = ["cmake", "-S", str(owned_source), "-B", str(output), "-G", "Ninja",
                 "-DPLATFORM_SOURCE=" + str(source), "-DPLATFORM_BUILD=" + str(build),
                 "-DTHIRD_PARTY_INCLUDE=" + str(third)]
    compile_command = ["cmake", "--build", str(output), "-j2"]
    prior_mask = os.umask(0o022)
    try:
        (output / "configure.log").write_text(command(configure))
        (output / "build.log").write_text(command(compile_command))
    finally:
        os.umask(prior_mask)
    binary = output / "studio_native_xcom_bridge"
    binary.chmod(0o755)
    native_sources = {p.relative_to(source).as_posix(): sha256(p)
                      for p in sorted((source / "src/xverse/xcom").rglob("*"))
                      if p.is_file() and p.suffix in (".hpp", ".cpp", ".txt", ".cmake")}
    manifest = {"formatVersion": "1.0", "platformRevision": PLATFORM_REVISION,
        "scope": "Linux x86_64 owned native FIFO bridge build; not live Autoverse acceptance",
        "studioNativeSources": {p.name: sha256(p) for p in (owned_source / "bridge.cpp", owned_source / "CMakeLists.txt")},
        "platformNativeSources": native_sources, "nativeLibraries": libraries,
        "thirdPartyHeaders": headers, "compiler": command(["c++", "--version"]).splitlines()[0],
        "cmake": command(["cmake", "--version"]).splitlines()[0],
        "binary": {"file": binary.name, "sha256": sha256(binary), "mode": "0755"},
        "companionSourceChanged": False}
    (output / "build-manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    (output / "execution.private.json").write_text(json.dumps({"commands": [configure, compile_command],
        "source": str(source), "build": str(build), "thirdParty": str(third), "output": str(output)}, indent=2) + "\n")
    print(json.dumps({"built": True, "platformRevision": PLATFORM_REVISION, "binarySha256": manifest["binary"]["sha256"]}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
