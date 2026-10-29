"""Explicit host enrollment for the Maestro/native-X-COM/Argus provider.

Browser/project content cannot nominate artifacts, roots, host grants or commands.
No source repository or container is modified by enrollment.
"""
from copy import deepcopy
from importlib.metadata import distribution
from importlib.resources import files
import json
from pathlib import Path
import stat
import time

from xverse.maestro import execution
from xverse_studio.storage.core import digest
from xverse_studio.xdl import PLATFORM_REVISION
from .installation import InstallationError, container_fact, container_file_digest, enroll, file_digest, inspect, verify


def native_source_root():
    source = Path(__file__).resolve().parents[4] / "native/xcom_bridge"
    return source if source.is_dir() else Path(str(files("xverse_studio.platform_observability").joinpath("native_bridge")))


def native_identity(installation):
    registered = installation["nativeBridge"]
    binary = Path(registered["binary"])
    manifest = Path(registered["manifest"])
    info = binary.lstat()
    if (not stat.S_ISREG(info.st_mode) or info.st_mode & 0o022
            or info.st_size > 64 * 1024 * 1024 or binary.resolve() != binary):
        raise InstallationError("AUTOVERSE_NATIVE_BINARY_UNSAFE")
    direct = json.loads(distribution("xverse-xdl").read_text("direct_url.json") or "{}")
    if direct.get("vcs_info", {}).get("commit_id") != PLATFORM_REVISION:
        raise InstallationError("AUTOVERSE_PLATFORM_SDK_CHANGED")
    modules = Path(execution.__file__).parent
    return {"binary": str(binary), "binarySha256": file_digest(binary),
        "manifest": str(manifest), "manifestSha256": file_digest(manifest),
        "platformRevision": PLATFORM_REVISION,
        "sdkModules": {p.name: file_digest(p) for p in sorted(modules.glob("*.py"))},
        "providerFiles": {p.name: file_digest(p) for p in sorted(Path(__file__).parent.glob("*.py"))},
        "backendTask": file_digest(Path(__file__).parent.parent / "backend_task.py"),
        "nativeSources": {name: file_digest(native_source_root() / name) for name in ("bridge.cpp", "CMakeLists.txt")},
        "runtimeRoot": registered["runtimeRoot"], "hostId": registered["hostId"]}


def current_identity(installation, *, deadline=None):
    """Observe actual enrolled file/container identities, including while active.

    This never starts a container or treats a content pin as an ownership handle.
    Public Maestro cleanup separately checks original process/container receipts.
    """
    def check():
        if deadline is not None and time.monotonic() >= deadline:
            raise InstallationError("AUTOVERSE_INSTALLATION_INSPECTION_TIMEOUT")
    actual_files = {}
    for name in installation["files"]:
        check()
        actual_files[name] = file_digest(Path(name))
    actual_containers = {}
    for role, expected in installation["containers"].items():
        check()
        timeout = 15 if deadline is None else min(15, max(.01, deadline - time.monotonic()))
        actual_containers[role] = container_fact(inspect(installation["docker"], expected["id"], timeout=timeout))
    actual_artifacts = {}
    for name in installation["containerFiles"]:
        check()
        actual_artifacts[name] = container_file_digest(installation["docker"], installation["containers"]["score"]["id"], name,
            timeout=60 if deadline is None else min(60, max(.01, deadline - time.monotonic())))
    check()
    classic = digest({"files": actual_files, "containers": actual_containers, "containerFiles": actual_artifacts})
    native = native_identity(installation)
    check()
    return digest({"classic": classic, "native": native})


def verify_platform(installation, *, require_stopped=True, deadline=None):
    if require_stopped:
        verify(installation)
    if current_identity(installation, deadline=deadline) != installation["identityDigest"]:
        raise InstallationError("AUTOVERSE_PLATFORM_INSTALLATION_CHANGED")
    return True


def enroll_platform(root, build_root, runtime_root):
    installation = enroll(root)
    build_root = Path(build_root).absolute()
    if build_root != build_root.resolve(strict=True) or build_root.stat().st_mode & 0o022:
        raise InstallationError("AUTOVERSE_NATIVE_BUILD_UNSAFE")
    manifest_path = build_root / "build-manifest.json"
    if manifest_path.is_symlink() or manifest_path.stat().st_size > 1024 * 1024:
        raise InstallationError("AUTOVERSE_NATIVE_MANIFEST_INVALID")
    manifest = json.loads(manifest_path.read_bytes())
    if (manifest["formatVersion"] != "1.0" or manifest["platformRevision"] != PLATFORM_REVISION
            or manifest["binary"]["file"] != "studio_native_xcom_bridge"):
        raise InstallationError("AUTOVERSE_NATIVE_MANIFEST_INVALID")
    runtime_root = Path(runtime_root).absolute()
    runtime_root.mkdir(parents=True, exist_ok=True, mode=0o700)
    if runtime_root != runtime_root.resolve() or runtime_root.stat().st_mode & 0o022:
        raise InstallationError("AUTOVERSE_PLATFORM_ROOT_UNSAFE")
    registered = {"binary": str(build_root / "studio_native_xcom_bridge"), "manifest": str(manifest_path),
        "runtimeRoot": str(runtime_root), "hostId": "autoverse-host-" + digest(str(installation["root"]))[7:27]}
    installation = deepcopy(installation)
    installation["nativeBridge"] = registered
    native = native_identity(installation)
    if (native["binarySha256"] != manifest["binary"]["sha256"]
            or native["nativeSources"] != manifest["studioNativeSources"]):
        raise InstallationError("AUTOVERSE_NATIVE_BUILD_CHANGED")
    registered.update(native)
    installation["identityDigest"] = current_identity(installation)
    # This is actual host enrollment policy, not a private-runtime review waiver
    # or data supplied by a project. It authorizes only the exact simulation set.
    installation["platformHostGrant"] = {"scope": "owned-simulation", "maxRuntimeSeconds": 2700,
        "maxCleanupSeconds": 60, "approvalReference": "explicit-studio-host-enrollment:" + installation["identityDigest"]}
    verify_platform(installation)
    return installation
