"""Per-binding public Maestro callbacks for the installed Autoverse worker.

Not registered by Studio yet: native messaging, worker supervision and browser
evidence admission remain required. These callbacks never call Demo.run or issue
their own platform permit. The original Studio journal retains its own origin.
"""
import json
import time

import psutil
from xverse.maestro.execution import ExecutionInputError, PhaseReceipt

from xverse_studio.storage.core import canonical, digest
from .installation import InstallationError, container_fact, verify
from .preparation import AutoverseInputs
from .worker import Cancelled


class AutoverseExecution(AutoverseInputs):
    def __init__(self, demo, preparation, *, runtime_adapter=None):
        super().__init__(demo.installation, runtime_adapter=runtime_adapter)
        self.demo = demo
        self.preparation = preparation
        self._phases = {p.phase_id: p for p in preparation.lifecycle.phases}
        self._attempted = set()

    def validate_runtime(self, effective, prepared):
        if (prepared.digest != self.preparation.prepared.digest
                or effective != prepared.providers[0].configuration
                or json.loads(effective.private_config) != self.demo.request["configuration"]
                or json.loads(effective.private_config)["inputSurface"] != "native-pygame"
                or {name: raw.encode() for name, raw in self.demo.snapshot["documents"].items()} != dict(effective.documents)):
            raise ExecutionInputError("AUTOVERSE-RUNTIME-INPUT-MISMATCH")
        self.demo.validate_requested_inputs()
        verify(self.demo.installation)

    def _process(self, role):
        record = self.demo.processes.get(role)
        if record is None:
            raise ExecutionInputError("AUTOVERSE-RESOURCE-UNOBSERVED")
        if record["process"].poll() is not None:
            return "exited"
        try:
            owner = psutil.Process(record["pid"])
            if owner.create_time() != record["createTime"] or digest(owner.cmdline()) != record["argvDigest"]:
                return "unknown"
        except psutil.Error:
            return "unknown"
        return "running"

    def _container(self, role, deadline):
        claim = self.demo.containers.get(role)
        if claim is None or claim["startedAt"] is None:
            return "unknown"
        row = self.demo.inspect_container(claim["identity"]["id"], deadline=deadline)
        if container_fact(row) != claim["identity"] or row["State"]["StartedAt"] != claim["startedAt"]:
            return "unknown"
        return "running" if row["State"]["Running"] else "exited"

    def dispatch(self, phase, effective, context):
        if self._phases.get(phase.phase_id) != phase:
            raise ExecutionInputError("AUTOVERSE-PHASE-UNSUPPORTED")
        if effective != self.preparation.prepared.providers[0].configuration:
            raise ExecutionInputError("AUTOVERSE-RUNTIME-INPUT-MISMATCH")
        demo = self.demo
        demo.active_phase, demo.phase_deadline = phase.phase_id, context.deadline
        observation, readiness = {}, None
        self._attempted.add(phase.phase_id)
        try:
            demo.check_phase_deadline()
            demo.check_command()
            if demo.stop_requested:
                raise Cancelled()
            identifier = phase.phase_id
            if identifier == "carla-router-prepare":
                compiled, _ = demo.validate_requested_inputs()
                demo.claim_installation(compiled)
                demo.start_router()
            elif identifier == "carla-server-prepare":
                demo.prepare_simulator()
            elif identifier == "vcu-start":
                demo.start_vcu()
            elif identifier == "vcu-native-prepare":
                demo.start_native_bridge(context, self.preparation.prepared)
            elif identifier == "someip-start":
                demo.start_container("someip-bridge")
            elif identifier == "score-start":
                demo.start_container("score")
                demo.wait(12)
            elif identifier == "carla-vehicle-start":
                demo.start_vehicle()
            elif identifier == "driver-observer-prepare":
                demo.start_driver_observer()
            elif identifier == "carla-ready":
                demo.wait_vehicle_telemetry()
                observation = {"speedInterface": "observed", "sourceClockMapping": "unavailable"}
                readiness = "interface"
            elif identifier == "android-container-prepare":
                demo.start_android_container()
            elif identifier == "android-vm-start":
                demo.start_android_vm()
            elif identifier == "android-boot-start":
                demo.wait_android_boot()
            elif identifier == "android-apk-start":
                demo.install_android_cluster()
            elif identifier == "driver-start":
                demo.start_manual_window()
            elif identifier in ("vcu-ready", "driver-ready"):
                roles = ("vcu",) if identifier == "vcu-ready" else ("driver", "manual")
                if any(self._process(role) != "running" for role in roles):
                    raise ExecutionInputError("AUTOVERSE-PROCESS-NOT-READY")
                observation = {"processes": list(roles), "observation": "running"}
                readiness = "liveness"
            elif identifier in ("someip-ready", "score-ready", "android-ready"):
                role = {"someip-ready": "someip-bridge", "score-ready": "score", "android-ready": "android"}[identifier]
                if self._container(role, context.deadline) != "running":
                    raise ExecutionInputError("AUTOVERSE-CONTAINER-NOT-READY")
                observation, readiness = {"container": role, "observation": "running"}, "liveness"
            # The remaining three prepare phases validate a binding and acquire
            # nothing. They cannot claim component readiness.
            elif identifier not in ("vcu-prepare", "someip-prepare", "score-prepare"):
                raise ExecutionInputError("AUTOVERSE-PHASE-UNSUPPORTED")
            demo.check_phase_deadline()
            resources = demo.phase_resources.get(identifier, {"processes": [], "containers": []})
            references = tuple(kind + "-" + role for kind, roles in resources.items() for role in roles)
            outcome = {"prepare": "prepared", "start": "started", "ready": "ready"}[phase.operation]
            if outcome == "ready":
                role = phase.logical_id.rsplit("#", 1)[-1]
                demo.state["runtimeStatus"]["components"][role] = readiness + "_observed"
            return PhaseReceipt(outcome, references, readiness, canonical(observation).encode())
        except Cancelled:
            raise ExecutionInputError("MPX-START-CANCELLED") from None
        except InstallationError as error:
            raise ExecutionInputError(str(error)) from None
        finally:
            demo.active_phase = demo.phase_deadline = None

    def cleanup(self, phase, effective, context):
        if self._phases.get(phase.phase_id) != phase or phase.phase_id not in self._attempted:
            return "unknown"
        self.demo.stop_requested = True
        return self.demo.cleanup_phase(phase.phase_id, context.deadline)

    def observe_runtime(self, effective, context):
        try:
            for role in ("router", "carla", "vcu", "vehicle", "driver", "manual"):
                state = self._process(role)
                if state != "running":
                    return state
            for role in ("someip-bridge", "score", "android"):
                if time.monotonic() >= context.deadline:
                    return "unknown"
                state = self._container(role, context.deadline)
                if state != "running":
                    return state
            return "running"
        except (OSError, ValueError, KeyError, psutil.Error):
            return "unknown"
