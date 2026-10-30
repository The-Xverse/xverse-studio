"""Owned native demo lifecycle. Fixed public entry points; no imported commands."""
from pathlib import Path
import hashlib
import hmac
import json
import os
import selectors
import signal
import subprocess
import sys
import time
import psutil
from xverse_studio.storage.core import atomic, canonical, digest
from .adapter import configuration
from .installation import container_fact, inspect, verify, InstallationError

MAX_LOG_BYTES = 2 * 1024 * 1024


class Cancelled(Exception):
    pass


class JournalOpenFailed(InstallationError):
    """An initial report was published before any runtime resource acquisition."""


class Demo:
    provider_id = "autoverse.demo"
    def __init__(self, root):
        self.root = root
        self.request = json.loads((root / "request.json").read_text())
        self.secret = (root / "owner.key").read_bytes()
        self.installation = self.request["nativeInstallation"]
        self.snapshot = self.request["snapshot"]
        self.state = {"state": "preparing", "stateVersion": 1, "cleanup": "not_started", "evidence": "collecting",
                      "pid": os.getpid(), "createTime": psutil.Process().create_time(), "ownerDigest": digest(self.secret),
                      "commandResults": {}, "runtimeStatus": {"phase": "verifying", "components": {}}, "inputTelemetry": {"items": {}}}
        self.processes, self.containers = {}, {}
        self.selector = selectors.DefaultSelector()
        self.log_sizes, self.log_dropped = {}, {}
        self.previous, self.count, self.journal_bytes = "0" * 64, 0, 0
        self.last_save = self.last_evidence = self.last_container_check = 0
        self.stop_command, self.stop_requested, self.bridge_ready = None, False, False
        self.last_input, self.input_generation = 0, 0
        self.bridge_buffer = bytearray()
        self.phase_deadline = None
        self.active_phase = None
        self.phase_resources = {}
        self.lock = None
        try:
            self.journal = (root / "evidence.jsonl").open("xb", buffering=0)
        except OSError:
            # Exclusive creation preserves a pre-existing object. No runtime
            # acquisition or canonical record has occurred at this boundary.
            self.selector.close()
            self.state.update(state="failed", cleanup="complete", cleanupResources=[],
                              evidence="unavailable", reason="EVIDENCE_OPEN_FAILED",
                              evidenceFailure="EVIDENCE_OPEN_FAILED", endedAt=time.time())
            self.save()  # A failed publication must remain unknown to the backend.
            raise JournalOpenFailed("EVIDENCE_OPEN_FAILED") from None
        self.save()

    def save(self):
        self.state["updatedAt"] = time.time()
        atomic(self.root / "state.json", canonical(self.state).encode())
        self.last_save = time.monotonic()

    def emit(self, kind, payload):
        self.count += 1
        body = {"schemaVersion": "1.0", "eventId": f'{self.request["runId"]}:{self.count}',
                "runId": self.request["runId"], "snapshotId": self.snapshot["snapshotId"], "sequence": str(self.count),
                "type": kind, "recordedAt": time.time(), "sourceTime": None,
                "source": {"providerId": self.provider_id, "version": "0.1.0"}, "elementRefs": [],
                "evidenceClass": "observed", "payload": payload, "evidenceRefs": [self.request["runId"] + ":provider-journal"], "previousDigest": self.previous}
        self.previous = hashlib.sha256(canonical(body).encode()).hexdigest()
        line = (canonical({**body, "digest": self.previous}) + "\n").encode()
        if self.journal_bytes + len(line) > 48 * 1024 * 1024 or self.count > 50000:
            raise InstallationError("AUTOVERSE_EVIDENCE_LIMIT")
        self.journal.write(line)
        self.journal_bytes += len(line)

    def phase(self, name):
        self.state["runtimeStatus"]["phase"] = name
        self.emit("log.appended", {"severity": "info", "message": "Demo preparation: " + name})
        self.save()

    def signed(self, path):
        try:
            raw = path.read_bytes()
            if len(raw) > 8192:
                return None
            value = json.loads(raw)
            signature = value.pop("signature", "")
            if not isinstance(signature, str) or not hmac.compare_digest(signature, hmac.new(self.secret, canonical(value).encode(), hashlib.sha256).hexdigest()):
                return None
            return value
        except (OSError, ValueError, TypeError):
            return None

    def check_command(self):
        value = self.signed(self.root / "command.json")
        if value and value.get("kind") in ("stop", "cancel") and value.get("operationId") not in self.state["commandResults"]:
            self.stop_command = value
            self.stop_requested = True

    def tick(self, *, cancellable=True):
        self.check_phase_deadline()
        self.check_command()
        for key, _ in self.selector.select(0.03):
            role = key.data
            data = os.read(key.fileobj.fileno(), 16384)
            if not data:
                self.selector.unregister(key.fileobj)
                self.process_eof(role)
                continue
            if self.process_output(role, data):
                continue
            if role == "driver":
                self.bridge_buffer.extend(data)
                if len(self.bridge_buffer) > 131072:
                    raise InstallationError("AUTOVERSE_BRIDGE_OUTPUT_LIMIT")
                while b"\n" in self.bridge_buffer:
                    line, _, remaining = self.bridge_buffer.partition(b"\n")
                    self.bridge_buffer[:] = remaining
                    value = json.loads(line)
                    if value["type"] == "ready":
                        self.bridge_ready = True
                    elif value["type"] == "telemetry":
                        self.state["inputTelemetry"] = {**value.get("data", {}), "driverLeaseActive": value.get("driverLeaseActive", False), "lastPublishedSequence": self.state["inputTelemetry"].get("lastPublishedSequence", 0)}
                    elif value["type"] == "input_accepted":
                        self.state["inputTelemetry"]["lastPublishedSequence"] = int(value["id"][2:])
                    elif value["type"] == "input_rejected":
                        self.state["inputTelemetry"]["lastRejection"] = value.get("code")
            else:
                size = self.log_sizes.get(role, 0)
                kept = data[:max(0, MAX_LOG_BYTES - size)]
                if kept:
                    with (self.root / (role + ".private.log")).open("ab") as out:
                        out.write(kept)
                    self.log_sizes[role] = size + len(kept)
                self.log_dropped[role] = self.log_dropped.get(role, 0) + len(data) - len(kept)
        now = time.monotonic()
        if self.bridge_ready and not self.stop_requested and self.request["configuration"].get("inputSurface", "studio-browser") == "studio-browser":
            packet = self.signed(self.root / "input.json")
            if packet and type(packet.get("generation")) is int and packet["generation"] >= self.input_generation and packet.get("expiresAt", 0) > now and 0 <= now - packet.get("issuedAt", 0) <= 0.75:
                from .controls import driver_frame
                frame = driver_frame(packet["frame"])
                if frame["sequence"] > self.last_input:
                    payload = (canonical({"type": "drive", "id": "i-" + str(frame["sequence"]), "frame": frame, "issuedAt": packet["issuedAt"]}) + "\n").encode()
                    try:
                        written = os.write(self.processes["driver"]["process"].stdin.fileno(), payload)
                        if written != len(payload):
                            raise InstallationError("AUTOVERSE_INPUT_BACKPRESSURE")
                    except BlockingIOError:
                        raise InstallationError("AUTOVERSE_INPUT_BACKPRESSURE") from None
                    self.last_input, self.input_generation = frame["sequence"], packet["generation"]
                    if set(frame) & {"cruise", "reverse", "deltaSpeed"}:
                        self.emit("log.appended", {"severity": "info", "message": "Discrete driver request delegated; publication and vehicle observations remain separate.", "inputSequence": self.last_input, "requests": frame})
        if now - self.last_save >= 0.2:
            self.save()
        if cancellable and self.stop_requested:
            raise Cancelled()

    def environment(self):
        env = {key: os.environ[key] for key in ("PATH", "HOME", "LANG", "USER", "LOGNAME") if key in os.environ}
        for key, field in (("DISPLAY", "display"), ("XAUTHORITY", "xauthority"), ("XDG_RUNTIME_DIR", "runtimeDir")):
            if self.installation.get(field):
                env[key] = self.installation[field]
        env.update(HOME=self.installation["home"], USER=self.installation["user"], LOGNAME=self.installation["user"], PYTHONUNBUFFERED="1", SDL_AUDIODRIVER="dummy")
        return env

    def check_phase_deadline(self):
        deadline = getattr(self, "phase_deadline", None)
        if deadline is not None and time.monotonic() >= deadline:
            raise InstallationError("AUTOVERSE_PHASE_DEADLINE")

    def process_output(self, role, data):
        return False

    def process_eof(self, role):
        pass

    def launch(self, role, argv, cwd=None, interactive=False, diagnostics=False):
        self.check_phase_deadline()
        self.emit("log.appended", {"severity": "info", "message": "Starting registered component " + role})
        prior = self.processes.get(role)
        if prior and prior["process"].poll() is None:
            raise InstallationError("AUTOVERSE_RESOURCE_STILL_OWNED")
        process = subprocess.Popen(argv, cwd=str(self.root) if cwd is None else cwd, env=self.environment(), start_new_session=True,
                                   stdin=subprocess.PIPE if interactive else subprocess.DEVNULL,
                                   stdout=subprocess.PIPE, stderr=subprocess.PIPE if diagnostics else subprocess.STDOUT if not interactive else subprocess.DEVNULL, close_fds=True)
        # Retain the original child before ownership observation or pipe setup:
        # either may fail after a successful acquisition.
        record = {"process": process, "pid": process.pid, "createTime": None, "argvDigest": None}
        self.processes[role] = record
        self.register_phase_resource("processes", role)
        owner = psutil.Process(process.pid)
        record.update(createTime=owner.create_time(), argvDigest=digest(owner.cmdline()))
        os.set_blocking(process.stdout.fileno(), False)
        if interactive:
            os.set_blocking(process.stdin.fileno(), False)
        self.selector.register(process.stdout, selectors.EVENT_READ, role)
        if diagnostics:
            os.set_blocking(process.stderr.fileno(), False)
            self.selector.register(process.stderr, selectors.EVENT_READ, role + "-diagnostic")
        self.state["runtimeStatus"]["components"][role] = "starting"
        atomic(self.root / "resources.private.json", canonical({key: {k: v for k, v in value.items() if k != "process"} for key, value in self.processes.items()}).encode())
        return process

    def wait(self, duration):
        deadline = time.monotonic() + duration
        while time.monotonic() < deadline:
            self.tick()

    def execute(self, role, argv, timeout=30, cancellable=True, allow_failure=False):
        process = self.launch(role, argv)
        deadline = time.monotonic() + timeout
        while process.poll() is None:
            self.tick(cancellable=cancellable)
            if time.monotonic() >= deadline:
                raise InstallationError("AUTOVERSE_COMMAND_TIMEOUT_" + role)
        self.tick(cancellable=cancellable)
        if process.returncode and not allow_failure:
            raise InstallationError("AUTOVERSE_COMMAND_FAILED_" + role)
        return process

    def inspect_container(self, identifier, *, deadline=None):
        deadline = self.phase_deadline if deadline is None else deadline
        timeout = 15 if deadline is None else min(15, deadline - time.monotonic())
        if timeout <= 0:
            raise InstallationError("AUTOVERSE_PHASE_DEADLINE")
        return inspect(self.installation["docker"], identifier, timeout=timeout)

    def start_container(self, role):
        expected = self.installation["containers"][role]
        row = self.inspect_container(expected["id"])
        if container_fact(row) != expected or row["State"]["Running"]:
            raise InstallationError("AUTOVERSE_CONTAINER_BUSY_OR_CHANGED")
        intent = {"identity": expected, "intentAt": time.time(), "startedAt": None}
        self.containers[role] = intent
        self.register_phase_resource("containers", role)
        self.container_receipt()
        self.execute("start-" + role, [self.installation["docker"], "start", expected["id"]])
        row = self.inspect_container(expected["id"])
        if not row["State"]["Running"] or container_fact(row) != expected:
            raise InstallationError("AUTOVERSE_CONTAINER_NOT_RUNNING_" + role)
        intent["startedAt"] = row["State"]["StartedAt"]
        self.container_receipt()
        self.state["runtimeStatus"]["components"][role] = "running"

    def container_receipt(self):
        atomic(self.root / "containers.private.json", canonical(self.containers).encode())

    def start_router(self):
        i = self.installation
        self.phase("router")
        self.launch("router", [i["zenohd"], "--listen", "tcp/127.0.0.1:7447", "--listen", "tcp/" + i["androidGateway"] + ":7447", "--no-multicast-scouting", "--cfg", "scouting/gossip/enabled:false"])
        self.wait(1)

    def prepare_simulator(self):
        i = self.installation
        self.phase("simulator")
        self.launch("carla", [str(Path(i["carlaRoot"]) / "CarlaUE4/Binaries/Linux/CarlaUE4-Linux-Shipping"), "CarlaUE4", "-prefernvidia", "-quality-level=Epic", "-carla-rpc-port=2000", "-RenderOffScreen"], cwd=i["carlaRoot"])
        deadline = time.monotonic() + 120
        while True:
            try:
                self.execute("carla-probe", [i["python"], "-E", str(Path(__file__).with_name("carla_probe.py"))], timeout=8)
                break
            except InstallationError:
                if time.monotonic() >= deadline or self.processes["carla"]["process"].poll() is not None:
                    raise InstallationError("AUTOVERSE_CARLA_NOT_READY") from None
                self.wait(1)
        self.execute("carla-prepare", [i["python"], "-E", str(Path(__file__).with_name("carla_prepare.py"))], timeout=25)
        self.state["runtimeStatus"]["components"]["carla"] = "ready"

    def start_vcu(self):
        r, i = Path(self.installation["root"]), self.installation
        self.phase("vcu-and-communications")
        config = self.root / "zenoh.private.json5"
        atomic(config, canonical({"mode": "client", "connect": {"endpoints": ["tcp/127.0.0.1:7447"]}, "listen": {"endpoints": []}, "scouting": {"multicast": {"enabled": False}, "gossip": {"enabled": False}}}).encode())
        self.launch("vcu", [i["python"], "-E", str(r / "vecu/vcu_zenoh/src/main.py"), "--config", str(config)], cwd=str(r / "vecu/vcu_zenoh"))

    def start_vehicle(self):
        r, i = Path(self.installation["root"]), self.installation
        self.phase("vehicle-and-driver")
        examples = r / "bridges/carla/examples"
        self.launch("vehicle", [i["python"], "-E", str(Path(__file__).with_name("public_entry.py")), str(examples / "virtual_vehicle.py"), "--verbose", "--sync", "--host", "127.0.0.1", "--port", "2000", "--router", "127.0.0.1", "--res", "1280x960", "--filter", "vehicle.audi.etron", "--rolename", "ego_vehicle", "--signals-config", str(examples / "signals_config.json"), "--enable-camera-display"], cwd=str(examples))

    def start_driver_observer(self):
        i = self.installation
        self.launch("driver", [i["python"], "-E", str(Path(__file__).with_name("zenoh_bridge.py")), "--duration", "1800", *(["--observe-only"] if self.request["configuration"]["inputSurface"] == "native-pygame" else [])], interactive=True)

    def wait_vehicle_telemetry(self):
        deadline = time.monotonic() + 120
        while not self.bridge_ready or self.state["inputTelemetry"].get("items", {}).get("speed", {}).get("status") != "observed":
            self.tick()
            if time.monotonic() > deadline:
                raise InstallationError("AUTOVERSE_VEHICLE_TELEMETRY_UNAVAILABLE")

    def start_android_container(self):
        self.phase("android")
        self.start_container("android")

    def start_android_vm(self):
        i = self.installation
        cid = i["containers"]["android"]["id"]
        self.execute("android-launch", [i["docker"], "exec", "--env", "ANDROID_HOST_OUT=/root/runtime", "--workdir", "/root/runtime", cid,
            "bash", "-c", "ulimit -n 65536; nohup ./bin/launch_cvd --system_image_dir=/root/runtime --assembly_dir=/root/runtime/cvd-assembly --instance_dir=/root/runtime/cvd-state --console=true --display0=width=1080,height=600,dpi=90 --display1=width=400,height=600,dpi=90 --start_webrtc=true --report_anonymous_usage_stats=no -- those --no-sandbox > cvd_launch.log 2>&1 &"])

    def wait_android_boot(self):
        i = self.installation
        deadline = time.monotonic() + 300
        while True:
            self.execute("adb-connect", [i["adb"], "connect", "localhost:6520"], timeout=10, allow_failure=True)
            self.execute("android-boot", [i["adb"], "-s", "localhost:6520", "shell", "getprop", "sys.boot_completed"], timeout=10, allow_failure=True)
            self.tick()
            output = (self.root / "android-boot.private.log").read_bytes() if (self.root / "android-boot.private.log").exists() else b""
            if b"1" in output.split():
                break
            if time.monotonic() > deadline:
                raise InstallationError("AUTOVERSE_ANDROID_BOOT_TIMEOUT")
            self.wait(2)

    def install_android_cluster(self):
        r, i = Path(self.installation["root"]), self.installation
        self.execute("android-install", [i["adb"], "-s", "localhost:6520", "install", "-r", str(r / "aaos_digital_cluster/cuttlefish_emulator/apk/digital-cluster-app-debug.apk")], timeout=90)
        self.execute("android-density", [i["adb"], "-s", "localhost:6520", "shell", "wm", "density", "90"])
        self.execute("android-open", [i["adb"], "-s", "localhost:6520", "shell", "am", "start", "-a", "android.intent.action.MAIN", "-c", "android.intent.category.LAUNCHER", "-p", "com.example.digitalclusterapp"])

    def start_manual_window(self):
        r, i = Path(self.installation["root"]), self.installation
        examples = r / "bridges/carla/examples"
        self.phase("manual-control-window")
        ready_file = self.root / "manual-window.private.json"
        manual = self.launch("manual", [i["python"], "-E", str(Path(__file__).with_name("pygame_manual.py")),
            "--root", str(r), "--ready-file", str(ready_file)], cwd=str(examples))
        deadline = time.monotonic() + 30
        while not ready_file.exists():
            self.tick()
            if manual.poll() is not None or time.monotonic() > deadline:
                raise InstallationError("AUTOVERSE_MANUAL_WINDOW_UNAVAILABLE")
        ready = json.loads(ready_file.read_bytes())
        if (ready.get("pid") != manual.pid or type(ready.get("windowId")) is not int
            or ready["windowId"] <= 0 or ready.get("title") != "Vehicle Manual Control" or ready.get("keyboardOnly") is not True):
            raise InstallationError("AUTOVERSE_MANUAL_WINDOW_UNCONFIRMED")
        self.state["runtimeStatus"]["nativeWindow"] = {"status": "opened", "title": ready["title"], "keyboardOnly": True}
        self.state["runtimeStatus"]["components"]["manual"] = "window_opened"

    def validate_requested_inputs(self):
        from xverse_studio.xdl import XDLAdapter
        compiled = XDLAdapter().compile(self.snapshot["documents"])
        actual = configuration(self.snapshot["documents"], compiled)
        from .adapter import AutoverseProvider
        if digest(AutoverseProvider(self.installation).descriptor()) != digest(self.snapshot.get("providerIdentity")):
            raise InstallationError("AUTOVERSE_PROVIDER_IDENTITY_CHANGED")
        if actual != self.request["configuration"] or compiled.get("planDigest") != self.snapshot["planDigest"] or compiled.get("semanticDigest") != self.snapshot["semanticDigest"]:
            raise InstallationError("EFFECTIVE_INPUT_MISMATCH")
        return compiled, actual

    def claim_installation(self, compiled):
        import fcntl  # This provider is admitted only on native Linux.
        lock_path = Path("/tmp") / ("xverse-autoverse-" + str(os.getuid()) + "-" + hashlib.sha256(self.installation["root"].encode()).hexdigest()[:20] + ".lock")
        self.lock = os.fdopen(os.open(lock_path, os.O_RDWR | os.O_CREAT | os.O_NOFOLLOW, 0o600), "a+")
        try:
            fcntl.flock(self.lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            raise InstallationError("AUTOVERSE_INSTALLATION_OWNED") from None
        verify(self.installation)
        self.state.update(effectivePlanDigest=compiled["planDigest"], effectiveSemanticDigest=compiled["semanticDigest"])
        self.emit("run.state_changed", {"state": "preparing", "stateVersion": 1, "installationDigest": self.installation["identityDigest"]})

    def run(self):
        compiled, actual = self.validate_requested_inputs()
        self.claim_installation(compiled)
        self.start_router()
        self.prepare_simulator()
        self.start_vcu()
        self.start_container("someip-bridge")
        self.start_container("score")
        self.wait(12)
        self.start_vehicle()
        self.start_driver_observer()
        self.wait_vehicle_telemetry()
        self.start_android_container()
        self.start_android_vm()
        self.wait_android_boot()
        self.install_android_cluster()
        if actual["inputSurface"] == "native-pygame":
            self.start_manual_window()
        self.state.update(state="running", stateVersion=2, startedAt=time.time())
        self.state["runtimeStatus"]["phase"] = "running"
        self.state["runtimeStatus"]["components"].update(router="running", driver="transport_ready", vehicle="speed_telemetry_observed", vcu="interface_observed", android="booted_apk_started")
        self.emit("run.state_changed", {"state": "running", "stateVersion": 2, "evidenceScope": "external_demo", "sourceClockMapping": "unavailable"})
        self.save()
        i = self.installation
        deadline = time.monotonic() + actual["durationSeconds"]
        while time.monotonic() < deadline:
            self.tick()
            if "manual" in self.processes:
                result = self.processes["manual"]["process"].poll()
                if result == 0:
                    self.state["reason"] = "AUTOVERSE_MANUAL_WINDOW_CLOSED"
                    return
                if result is not None:
                    raise InstallationError("AUTOVERSE_COMPONENT_EXITED_manual")
            for role in ("router", "carla", "vcu", "vehicle", "driver"):
                if self.processes[role]["process"].poll() is not None:
                    raise InstallationError("AUTOVERSE_COMPONENT_EXITED_" + role)
            if time.monotonic() - self.last_container_check >= 2:
                for role, claim in self.containers.items():
                    row = inspect(i["docker"], claim["identity"]["id"])
                    if (not row["State"]["Running"] or container_fact(row) != claim["identity"]
                        or row["State"]["StartedAt"] != claim["startedAt"]):
                        raise InstallationError("AUTOVERSE_COMPONENT_EXITED_OR_REPLACED_" + role)
                self.last_container_check = time.monotonic()
            if time.monotonic() - self.last_evidence >= 1:
                self.emit("observation.available", {"observerId": "autoverse-telemetry", "scope": "external_interface_receipts", **self.state["inputTelemetry"]})
                self.last_evidence = time.monotonic()

    def cleanup_resources(self, *, processes=None, containers=None, deadline=None):
        process_roles = list(self.processes) if processes is None else list(processes)
        container_roles = list(self.containers) if containers is None else list(containers)
        outcomes = []
        def budget(maximum):
            if deadline is None:
                return maximum
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                raise InstallationError("AUTOVERSE_CLEANUP_DEADLINE")
            return min(maximum, remaining)
        # Close the owned bridge; observe-only mode never publishes driver input.
        driver = self.processes.get("driver") if "driver" in process_roles else None
        if driver and driver["process"].stdin:
            try:
                budget(1)
                driver["process"].stdin.close()
            except (OSError, InstallationError):
                pass  # Continue every exact-resource cleanup attempt below.
        for role in reversed(process_roles):
            record = self.processes[role]
            process = record["process"]
            if process.poll() is not None:
                outcomes.append({"resourceId": role, "kind": "process", "status": "released"})
                continue
            try:
                budget(1)
                owner = psutil.Process(record["pid"])
                if owner.create_time() != record["createTime"] or digest(owner.cmdline()) != record["argvDigest"]:
                    raise InstallationError("AUTOVERSE_PROCESS_IDENTITY_UNKNOWN")
                # Capture descendant identities before signaling their owned parent.
                descendants = [(child, child.create_time()) for child in owner.children(recursive=True)]
                owner.send_signal(signal.SIGINT if role in ("vehicle", "driver", "manual") else signal.SIGTERM)
                try:
                    process.wait(timeout=budget(8))
                except subprocess.TimeoutExpired:
                    budget(1)
                    if owner.create_time() == record["createTime"]:
                        owner.kill()
                    process.wait(timeout=budget(3))
                for child, born in descendants:
                    try:
                        if child.create_time() == born and child.status() != psutil.STATUS_ZOMBIE:
                            budget(1)
                            child.terminate()
                            try:
                                child.wait(timeout=budget(3))
                            except psutil.TimeoutExpired:
                                budget(1)
                                if child.create_time() == born:
                                    child.kill()
                                    child.wait(timeout=budget(3))
                    except psutil.NoSuchProcess:
                        pass
                outcomes.append({"resourceId": role, "kind": "process", "status": "released"})
            except (psutil.Error, OSError, InstallationError, subprocess.TimeoutExpired):
                outcomes.append({"resourceId": role, "kind": "process", "status": "unknown"})
        for role in reversed(container_roles):
            from .cleanup import cleanup_container
            outcomes.append(cleanup_container(self.installation, role, self.containers[role], deadline=deadline))
        score = self.containers.get("score") if "score" in container_roles else None
        if score and score.get("startedAt") and any(row["resourceId"] == "score" and row["status"] == "released" and row["kind"] == "container" for row in outcomes):
            from .working_state import remember
            try:
                remember(self.installation, score["startedAt"])
                self.state["runtimeStatus"]["scratch"] = "retained_verified_middleware_working_files"
            except (ValueError, OSError):
                outcomes.append({"resourceId": "middleware-scratch", "kind": "working-state", "status": "unknown"})
        return outcomes

    def register_phase_resource(self, kind, role):
        phase = getattr(self, "active_phase", None)
        if phase is not None:
            resources = self.phase_resources.setdefault(phase, {"processes": [], "containers": []})
            if role not in resources[kind]:
                resources[kind].append(role)

    def cleanup_phase(self, phase, deadline):
        resources = self.phase_resources.get(phase, {"processes": [], "containers": []})
        outcomes = self.cleanup_resources(**resources, deadline=deadline)
        self.state.setdefault("cleanupResources", []).extend({**item, "phaseId": phase} for item in outcomes)
        return "released" if all(row["status"] == "released" for row in outcomes) else "unknown"

    def cleanup(self):
        self.stop_requested = True
        outcomes = self.cleanup_resources()
        self.state["cleanupResources"] = outcomes
        self.state["cleanup"] = "complete" if all(row["status"] == "released" for row in outcomes) else "unknown"
        if self.lock:
            self.lock.close()
        self.selector.close()


def finish(demo, failed):
    """Release owned resources even when state/evidence storage has failed."""
    io_failed = False
    def save():
        nonlocal io_failed
        try:
            demo.save()
        except OSError:
            io_failed = True
    demo.state.update(state="stopping", stateVersion=demo.state["stateVersion"] + 1)
    save()
    try:
        demo.cleanup()
    except Exception:
        # A cleanup implementation failure never manufactures release facts.
        demo.state["cleanup"] = "unknown"
        demo.state.setdefault("reason", "AUTOVERSE_CLEANUP_UNCONFIRMED")
    if demo.stop_command:
        demo.state["commandResults"][demo.stop_command["operationId"]] = {"status": "completed" if demo.state["cleanup"] == "complete" else "unknown"}
    demo.state.update(state="failed" if failed else "stopped", stateVersion=demo.state["stateVersion"] + 1,
                      endedAt=time.time(), evidence="partial" if failed or io_failed else "available")
    try:
        if failed and not demo.state.get("startedAt"):
            # The backend accepted this original Start, but the native target
            # never reached running. Record that operation's actual failure;
            # later workload failure must not retroactively fail a completed Start.
            demo.emit("command.failed", {"operationId": demo.request["operationId"],
                "kind": "start", "code": demo.state["reason"]})
        demo.emit("run.state_changed", {"state": demo.state["state"], "stateVersion": demo.state["stateVersion"], "cleanup": demo.state["cleanup"], "cleanupResources": demo.state.get("cleanupResources", []), "reason": demo.state.get("reason")})
    except (OSError, InstallationError):
        io_failed = True
    try:
        demo.journal.close()
        demo.state.update(journalDigest=digest((demo.root / "evidence.jsonl").read_bytes()), eventCount=demo.count)
    except OSError:
        io_failed = True
    if io_failed:
        demo.state.update(evidence="partial", evidenceFailure="AUTOVERSE_EVIDENCE_IO_FAILED")
    save()
    return int(failed or io_failed)


def main():
    try:
        demo = Demo(Path(sys.argv[1]).resolve())
    except JournalOpenFailed:
        return 1
    signal.signal(signal.SIGTERM, lambda *_: setattr(demo, "stop_requested", True))
    signal.signal(signal.SIGINT, lambda *_: setattr(demo, "stop_requested", True))
    failed = False
    try:
        demo.run()
    except Cancelled:
        pass
    except Exception as error:
        failed = True
        demo.state["reason"] = str(error) if isinstance(error, InstallationError) else "AUTOVERSE_WORKER_FAILED_" + type(error).__name__
    return finish(demo, failed)


if __name__ == "__main__":
    raise SystemExit(main())
