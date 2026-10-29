"""Trusted host enrollment for the explicitly selected, existing demo installation.

Only the native launcher calls enrollment. XDL, imports and browser requests cannot
choose host paths, containers, executables or command arguments.
"""
from pathlib import Path
import hashlib
import io
import tarfile
import json
import os
import platform
import shutil
import socket
import subprocess
import psutil

from xverse_studio.storage.core import canonical, digest

CONTAINERS = {"someip-bridge": "bridge-e2e", "score": "docker_setup-adas_score-1", "android": "cuttlefish-orchestration-cont"}
REQUIRED = ["run_autoverse.py", "vecu/vcu_zenoh/src/main.py",
            "bridges/carla/examples/virtual_vehicle.py", "bridges/carla/examples/signals_config.json",
            "aaos_digital_cluster/cuttlefish_emulator/ctl.sh",
            "aaos_digital_cluster/cuttlefish_emulator/apk/digital-cluster-app-debug.apk",
            "vecu/s-core/cc_s-core/bazel-bin/tests/integration/cruise_control_someip_config.bin",
            "vecu/s-core/cc_s-core/bazel-bin/tests/integration/gatewayd/gatewayd.exe",
            "vecu/s-core/cc_s-core/bazel-bin/tests/integration/someipd/someipd.exe",
            "vecu/s-core/cc_s-core/bazel-bin/score/cruise_control/cruise_control_main",
            "vecu/s-core/cc_s-core/tests/integration/run_gateway.sh",
            "vecu/s-core/cc_s-core/deployment/xverse/docker_setup/entrypoint.sh",
            "vecu/s-core/cc_s-core/deployment/xverse/docker_setup/vsomeip.json",
            "vecu/s-core/cc_s-core/score/cruise_control/config/mw_com_config.json"]
PORTS = (2000, 2001, 2002, 7447, 6520, 8443, 8000)


class InstallationError(ValueError):
    pass


def command(argv, timeout=15):
    result = subprocess.run(argv, stdin=subprocess.DEVNULL, capture_output=True, timeout=timeout, check=False)
    if result.returncode or len(result.stdout) > 4 * 1024 * 1024:
        raise InstallationError("AUTOVERSE_HOST_COMMAND_FAILED")
    return result.stdout


def file_digest(path):
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(chunk)
    return "sha256:" + h.hexdigest()


def container_fact(row):
    # Hash environment/mount details without exporting potentially private values.
    return {"id": row["Id"], "image": row["Image"], "name": row["Name"],
            "configurationDigest": digest({key: row[key] for key in ("Config", "HostConfig", "Mounts")})}


def inspect(docker, identifier):
    rows = json.loads(command([docker, "inspect", identifier]))
    if len(rows) != 1:
        raise InstallationError("AUTOVERSE_CONTAINER_IDENTITY_UNKNOWN")
    return rows[0]


def container_file_digest(docker, identifier, name):
    # Docker's read-only archive API can resolve mounted Bazel outputs while the
    # container is stopped; host access to the Docker data directory is unnecessary.
    result = subprocess.run([docker, "cp", "-L", identifier + ":" + name, "-"],
                            capture_output=True, timeout=60, check=False)
    if result.returncode or len(result.stdout) > 256 * 1024 * 1024:
        raise InstallationError("AUTOVERSE_CONTAINER_ARTIFACT_MISSING")
    with tarfile.open(fileobj=io.BytesIO(result.stdout)) as archive:
        members = archive.getmembers()
        if len(members) != 1 or not members[0].isfile():
            raise InstallationError("AUTOVERSE_CONTAINER_ARTIFACT_INVALID")
        with archive.extractfile(members[0]) as source:
            return "sha256:" + hashlib.file_digest(source, "sha256").hexdigest()


def enroll(root):
    """Read-only enrollment; never creates, downloads, starts or stops demo assets."""
    if platform.system() != "Linux" or platform.machine() != "x86_64":
        raise InstallationError("AUTOVERSE_LINUX_PROVIDER_REQUIRED")
    root = Path(root).resolve(strict=True)
    carla = root.parent / "carla-simulator"
    container_paths = ["/home/source/" + relative.split("cc_s-core/", 1)[1] for relative in REQUIRED if "/bazel-bin/" in relative]
    paths = {str((root / relative).absolute()) for relative in REQUIRED if "/bazel-bin/" not in relative}
    # Include local Python/config modules loaded by the public component entry points.
    for directory in (root / "vecu/vcu_zenoh/src", root / "bridges/carla/examples"):
        paths.update(str(p.absolute()) for p in directory.rglob("*") if p.is_file() and p.suffix in (".py", ".json", ".json5"))
    paths.update(str(carla / name) for name in ("CarlaUE4.sh", "CarlaUE4/Binaries/Linux/CarlaUE4-Linux-Shipping"))
    paths.update(str(root / "aaos_digital_cluster/cuttlefish_emulator/runtime" / name) for name in ("bin/launch_cvd", "bin/stop_cvd"))
    if len(paths) > 512:
        raise InstallationError("AUTOVERSE_INSTALLATION_LIMIT")
    executables = {name: shutil.which(name) for name in ("docker", "zenohd", "adb")}
    if not all(executables.values()) or not Path("/usr/bin/python3").is_file():
        raise InstallationError("AUTOVERSE_DEPENDENCY_MISSING")
    sdk = json.loads(command(["/usr/bin/python3", "-E", "-c", "import os; os.environ['PYGAME_HIDE_SUPPORT_PROMPT']='1'; import json,sys,importlib,importlib.metadata as m; names=['carla','zenoh','pygame','numpy','psutil']; print(json.dumps({'python':sys.version,'packages':{n:m.version('eclipse-zenoh' if n=='zenoh' else n) for n in names},'moduleFiles':{n:importlib.import_module(n).__file__ for n in names}}))"], timeout=30))
    for name in sdk["moduleFiles"].values():
        paths.add(name)
        paths.update(str(p) for p in Path(name).parent.glob("**/*.so"))
    addresses = [item.address for item in psutil.net_if_addrs().get("cvd-mtap-01", []) if item.family == socket.AF_INET]
    if len(addresses) != 1:
        raise InstallationError("AUTOVERSE_EMULATOR_GATEWAY_UNAVAILABLE")
    gateway = addresses[0]
    if len(paths) > 512:
        raise InstallationError("AUTOVERSE_INSTALLATION_LIMIT")
    paths.update(executables.values())
    paths.add("/usr/bin/python3")
    try:
        pins = {name: file_digest(Path(name)) for name in sorted(paths)}
    except OSError:
        raise InstallationError("AUTOVERSE_ARTIFACT_MISSING") from None
    containers = {}
    for role, name in CONTAINERS.items():
        row = inspect(executables["docker"], name)
        if row["State"]["Running"] or row["HostConfig"]["RestartPolicy"]["Name"] not in ("no", ""):
            raise InstallationError("AUTOVERSE_CONTAINER_BUSY_OR_RESTARTING")
        containers[role] = container_fact(row)
    command(["/usr/bin/python3", "-E", "-c", "import carla,zenoh,pygame,numpy,psutil"], timeout=30)
    artifact_pins = {name: container_file_digest(executables["docker"], containers["score"]["id"], name) for name in container_paths}
    receipt = {"sdk": sdk["packages"], "componentPythonVersion": sdk["python"], "androidGateway": gateway, "containerFiles": artifact_pins, "version": "1.0", "root": str(root), "carlaRoot": str(carla), "python": "/usr/bin/python3",
               **executables, "containers": containers, "files": pins,
               "home": str(Path.home()), "user": os.environ.get("USER", str(os.getuid())),
               "display": os.environ.get("DISPLAY"), "xauthority": os.environ.get("XAUTHORITY"),
               "runtimeDir": os.environ.get("XDG_RUNTIME_DIR")}
    if not receipt["display"]:
        raise InstallationError("AUTOVERSE_DISPLAY_UNAVAILABLE")
    receipt["identityDigest"] = digest({"files": pins, "containers": containers, "containerFiles": artifact_pins})
    verify(receipt)
    return receipt


def verify(installation):
    if platform.system() != "Linux" or platform.machine() != "x86_64":
        raise InstallationError("AUTOVERSE_LINUX_PROVIDER_REQUIRED")
    for name, expected in installation["files"].items():
        if file_digest(Path(name)) != expected:
            raise InstallationError("AUTOVERSE_INSTALLATION_CHANGED")
    for expected in installation["containers"].values():
        row = inspect(installation["docker"], expected["id"])
        if container_fact(row) != expected:
            raise InstallationError("AUTOVERSE_CONTAINER_CHANGED")
        if row["State"]["Running"]:
            raise InstallationError("AUTOVERSE_CONTAINER_BUSY")
    for name, expected in installation["containerFiles"].items():
        if container_file_digest(installation["docker"], installation["containers"]["score"]["id"], name) != expected:
            raise InstallationError("AUTOVERSE_ARTIFACT_CHANGED")
    # Existing middleware IPC is never removed or adopted by this wrapper.
    if Path("/tmp/mw_com_lola").exists() or Path("/tmp/score-xverse").exists():
        from .working_state import recognized
        if not recognized(installation, inspect(installation["docker"], installation["containers"]["score"]["id"])):
            raise InstallationError("AUTOVERSE_MIDDLEWARE_IPC_PRESENT")
    addresses = {item.address for item in psutil.net_if_addrs().get("cvd-mtap-01", []) if item.family == socket.AF_INET}
    if installation["androidGateway"] not in addresses:
        raise InstallationError("AUTOVERSE_EMULATOR_GATEWAY_CHANGED")
    for address, port in [("127.0.0.1", port) for port in PORTS] + [(installation["androidGateway"], 7447)]:
        with socket.socket() as probe:
            probe.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            try:
                probe.bind((address, port))
            except OSError:
                raise InstallationError("AUTOVERSE_PORT_BUSY_" + str(port)) from None
    return True
