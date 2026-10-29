"""Complete installed simulation delegated to the public Maestro service.

Studio's journal/state remain separate from original Maestro/native Argus records.
The host enrollment grants only its exact installation, root and finite simulation.
"""
import hashlib
import hmac
import json
import os
from pathlib import Path
import signal
import sys
import threading
import time

from xverse.argus import EvidenceStore
from xverse.maestro.execution import ExecutionInputError, HostExecutionPermit, NativeObservationBatch, PublicExecutionService
from xverse_studio.storage.core import atomic, canonical, digest
from xverse_studio.xdl import XDLAdapter
from .execution import AutoverseExecution
from .installation import InstallationError
from .native_protocol import collection_interval, native_configuration
from .platform_adapter import PlatformProvider, platform_configuration
from .platform_installation import current_identity
from .preparation import prepare_snapshot
from .worker import Cancelled, Demo


class PlatformDemo(Demo):
    provider_id = "autoverse.platform"

    def __init__(self, root):
        self.native_buffer = bytearray()
        self.native_ready = None
        self.native_pipe_closed = False
        self.native_replies = {}
        self.native_request = 0
        self.final_native = None
        self.native_quiesced = False
        self.platform_latest = None
        self.projection_lock = threading.Lock()
        self.projection_order = (-1, -1, -1)
        super().__init__(root)
        self.activation_deadline = time.monotonic() + self.request["configuration"]["durationSeconds"] + 900

    def save(self):
        if self.platform_latest:
            self.state["platformStatus"] = {k: self.platform_latest[k] for k in (
                "runId", "planDigest", "inputSemanticDigest", "operationId", "correlationId",
                "stopOperationId", "state", "stateVersion", "cleanup", "evidenceWriter", "nativeSources")
                if k in self.platform_latest}
        super().save()

    def validate_requested_inputs(self):
        compiled = XDLAdapter().compile(self.snapshot["documents"])
        actual = platform_configuration(self.snapshot["documents"], compiled)
        if digest(PlatformProvider(self.installation).descriptor()) != digest(self.snapshot.get("providerIdentity")):
            raise InstallationError("AUTOVERSE_PROVIDER_IDENTITY_CHANGED")
        if (actual != self.request["configuration"] or compiled.get("planDigest") != self.snapshot["planDigest"]
                or compiled.get("semanticDigest") != self.snapshot["semanticDigest"]):
            raise InstallationError("EFFECTIVE_INPUT_MISMATCH")
        return compiled, actual

    def start_router(self):
        super().start_router()
        self.launch("vcu-router", [self.installation["zenohd"], "--listen", "tcp/127.0.0.1:7448",
            "--no-multicast-scouting", "--cfg", "scouting/gossip/enabled:false"])
        self.wait(.5)

    def start_vcu(self):
        # Same public CLI and exact source, with its supported configuration
        # selecting the isolated VCU endpoint. No companion file is changed.
        root, installation = Path(self.installation["root"]), self.installation
        config = self.root / "vcu-zenoh.private.json5"
        atomic(config, canonical({"mode": "client", "connect": {"endpoints": ["tcp/127.0.0.1:7448"]},
            "listen": {"endpoints": []}, "scouting": {"multicast": {"enabled": False}, "gossip": {"enabled": False}}}).encode())
        self.launch("vcu", [installation["python"], "-E", str(root / "vecu/vcu_zenoh/src/main.py"),
            "--config", str(config)], cwd=str(root / "vecu/vcu_zenoh"))

    def process_output(self, role, data):
        if role != "native-bridge":
            return False
        self.native_buffer.extend(data)
        if len(self.native_buffer) > 128 * 1024:
            raise InstallationError("AUTOVERSE_NATIVE_OUTPUT_LIMIT")
        while b"\n" in self.native_buffer:
            line, _, rest = self.native_buffer.partition(b"\n")
            self.native_buffer[:] = rest
            value = json.loads(line)
            if value.get("kind") == "ready" and self.native_ready is None:
                if value.get("runId") != self.request["runId"] or value.get("routeCount") != 11:
                    raise InstallationError("AUTOVERSE_NATIVE_READY_MISMATCH")
                self.native_ready = value
            else:
                identifier = value.get("requestId")
                if type(identifier) is not int or identifier != self.native_request or len(self.native_replies) >= 2:
                    raise InstallationError("AUTOVERSE_NATIVE_REPLY_MISMATCH")
                self.native_replies[identifier] = value
        return True

    def write_native(self, value, deadline):
        packet, offset = (canonical(value) + "\n").encode(), 0
        if len(packet) > 65536:
            raise InstallationError("AUTOVERSE_NATIVE_INPUT_LIMIT")
        pipe = self.processes["native-bridge"]["process"].stdin
        while offset < len(packet):
            if self.active_phase is not None and self.stop_requested:
                raise Cancelled()
            if time.monotonic() >= deadline:
                raise InstallationError("AUTOVERSE_NATIVE_INPUT_TIMEOUT")
            try:
                offset += os.write(pipe.fileno(), packet[offset:offset + 8192])
            except BlockingIOError:
                self.tick(cancellable=False)

    def process_eof(self, role):
        if role == "native-bridge":
            self.native_pipe_closed = True

    def start_native_bridge(self, context, prepared):
        self.phase("native-communications")
        native, transports = native_configuration(prepared, operation_id=context.operation_id,
            correlation_id=context.correlation_id, provider_id=self.provider_id)
        self.launch("native-bridge", [self.installation["python"], "-E", str(Path(__file__).with_name("native_transport.py")),
            "--native", self.installation["nativeBridge"]["binary"]], interactive=True, diagnostics=True)
        self.write_native({"native": native, "transports": transports,
            "endpoints": {"outside": "tcp/127.0.0.1:7447", "vcu": "tcp/127.0.0.1:7448"},
            "binarySha256": self.installation["nativeBridge"]["binarySha256"],
            "maxRuntimeSeconds": self.request["configuration"]["durationSeconds"] + 900}, context.deadline)
        while self.native_ready is None:
            self.tick()
            if self.processes["native-bridge"]["process"].poll() is not None:
                raise InstallationError("AUTOVERSE_NATIVE_START_FAILED")
        self.state["runtimeStatus"]["components"]["native-bridge"] = "transport_ready"

    def native_call(self, kind, deadline):
        self.native_request += 1
        self.write_native({"kind": kind, "requestId": self.native_request}, deadline)
        while self.native_request not in self.native_replies:
            if time.monotonic() >= deadline:
                raise InstallationError("AUTOVERSE_NATIVE_REPLY_TIMEOUT")
            self.tick(cancellable=False)
            if self.native_pipe_closed and self.native_request not in self.native_replies:
                raise InstallationError("AUTOVERSE_NATIVE_EXITED_WITHOUT_REPLY")
        reply = self.native_replies.pop(self.native_request)
        if reply.get("kind") not in ("batch", "idle"):
            raise InstallationError("AUTOVERSE_NATIVE_REPLY_INVALID")
        return reply

    def quiesce_native(self):
        if self.native_ready is None or self.native_quiesced:
            return
        reply = self.native_call("quiesce", min(self.activation_deadline, time.monotonic() + 5))
        if reply.get("routesReleased") is not True or reply.get("quiesced") is not True:
            raise InstallationError("AUTOVERSE_NATIVE_CLOSE_UNCONFIRMED")
        self.final_native = reply
        self.native_quiesced = True

    def project_platform(self, snapshot):
        """Signed bounded read projection, never replacement canonical evidence."""
        count = len(snapshot.get("observations", []))
        rank = {"preparing": 0, "running": 1, "stopping": 2, "stopped": 3, "failed": 3, "unknown": 3}
        order = (snapshot["stateVersion"], count, rank[snapshot["state"]])
        with self.projection_lock:
            if order < self.projection_order:
                return
            self.projection_order = order
            body = {**snapshot, "observations": snapshot.get("observations", [])[-64:],
                "omittedObservations": max(0, count - 64), "source": "public-maestro-read-snapshot",
                "runtimeBindingDigest": self.service.runtime_binding_digest, "capturedAt": time.time(),
                "studioStartOperationId": self.request["operationId"],
                "studioStopOperationId": self.stop_command["operationId"] if self.stop_command else None}
            signature = hmac.new(self.secret, canonical(body).encode(), hashlib.sha256).hexdigest()
            atomic(self.root / "maestro.private.json", canonical({**body, "signature": signature}).encode())
            self.platform_latest = body


class PlatformExecution(AutoverseExecution):
    @property
    def installation_digest(self):
        return current_identity(self.demo.installation, deadline=self.demo.activation_deadline)

    def observation_clock_declarations(self, effective, run_id, operation_id):
        # A new process elapsed clock origin is a definition, not an invented
        # current reading or synchronization with the simulator/host clocks.
        return {"native": {"domain": "native-" + operation_id, "unit": "ns", "value": 0}}

    def read_observation_batch(self, effective, context):
        reply = self.demo.final_native
        if reply is not None:
            self.demo.final_native = None
        elif self.demo.native_quiesced:
            return None
        else:
            reply = self.demo.native_call("collect", context.deadline)
        if reply["kind"] == "idle":
            return None
        raw = reply["projectionJson"].encode()
        original = json.loads(raw)
        return NativeObservationBatch(self.provider_id,
            original["extensions"]["io.xverse.maestro.execution"]["batchSequence"], raw)

    def observe_runtime(self, effective, context):
        if getattr(self.demo, "runtime_fault", False) or getattr(self.demo, "supervisor_error", None):
            return "unknown"
        if not self.demo.native_quiesced and self._process("native-bridge") != "running":
            return "exited"
        if self._process("vcu-router") != "running":
            return "exited"
        return super().observe_runtime(effective, context)


def supervise(demo, finished):
    """Separate thread can request cancellation while SDK start owns its lock."""
    while not finished.wait(.25):
        try:
            demo.check_command()
            snapshot = demo.service.read(demo.request["runId"])
            demo.project_platform(snapshot)
            if demo.stop_requested and snapshot["state"] == "preparing":
                try:
                    demo.service.stop(snapshot["runId"], expected_version=snapshot["stateVersion"])
                except ExecutionInputError as error:
                    if error.code != "MPX-STATE-VERSION-CONFLICT":
                        raise
        except ExecutionInputError as error:
            if error.code != "MPX-RUN-NOT-FOUND":
                demo.supervisor_error = error.code
                demo.stop_requested = True
        except Exception:
            demo.supervisor_error = "AUTOVERSE_PLATFORM_SUPERVISION_FAILED"
            demo.stop_requested = True


def run(demo):
    compiled, config = demo.validate_requested_inputs()
    adapter = PlatformProvider(demo.installation)
    registered = demo.installation["nativeBridge"]
    grant = demo.installation["platformHostGrant"]
    runtime_budget = config["durationSeconds"] + 900
    if grant["scope"] != "owned-simulation" or runtime_budget > min(2700, grant["maxRuntimeSeconds"]) or grant["maxCleanupSeconds"] != 60:
        raise InstallationError("AUTOVERSE_PLATFORM_GRANT_INVALID")
    preparation = prepare_snapshot(demo.request["runId"], demo.snapshot, installation=demo.installation,
        host_id=registered["hostId"], runtime_adapter=adapter)
    provider = PlatformExecution(demo, preparation, runtime_adapter=adapter)
    demo.service = PublicExecutionService(Path(registered["runtimeRoot"]), preparation.host, (provider,),
        max_runtime_seconds=runtime_budget, cleanup_budget_seconds=60)
    now = time.time()
    permit = HostExecutionPermit("studio-" + demo.request["runId"], preparation.host.identity(),
        preparation.prepared.digest, preparation.lifecycle.digest, preparation.host.host_id,
        grant["approvalReference"], now, now + runtime_budget, runtime_binding_digest=demo.service.runtime_binding_digest)
    finished = threading.Event()
    watcher = threading.Thread(target=supervise, args=(demo, finished), daemon=True)
    watcher.start()
    snapshot = None
    try:
        snapshot = demo.service.start(preparation.prepared, preparation.lifecycle, permit, idempotency_key=demo.request["operationId"])
        demo.project_platform(snapshot)
        if snapshot["state"] == "running":
            demo.state.update(state="running", stateVersion=2, startedAt=time.time())
            demo.state["runtimeStatus"]["phase"] = "running"
            demo.emit("run.state_changed", {"state": "running", "stateVersion": 2,
                "platformRunId": snapshot["runId"], "platformOperationId": snapshot["operationId"]})
            demo.save()
            end = time.monotonic() + config["durationSeconds"]
            next_collect = next_observe = time.monotonic()
            while time.monotonic() < end and snapshot["state"] == "running":
                try:
                    demo.tick()
                except Cancelled:
                    break
                if demo.processes["manual"]["process"].poll() == 0:
                    demo.state["reason"] = "AUTOVERSE_MANUAL_WINDOW_CLOSED"
                    break
                instant = time.monotonic()
                if instant >= next_collect:
                    snapshot = demo.service.collect_native_observations(snapshot["runId"], expected_version=snapshot["stateVersion"])
                    next_collect = instant + collection_interval(config["durationSeconds"])
                if instant >= next_observe and snapshot["state"] == "running":
                    snapshot = demo.service.observe(snapshot["runId"], expected_version=snapshot["stateVersion"])
                    next_observe = instant + max(5, config["durationSeconds"] / 180)
                if instant - demo.last_evidence >= 1:
                    demo.emit("observation.available", {"observerId": "autoverse-telemetry",
                        "scope": "external_interface_receipts", **demo.state["inputTelemetry"]})
                    demo.last_evidence = instant
            if getattr(demo, "supervisor_error", None) and snapshot["state"] == "running":
                demo.runtime_fault = True
                snapshot = demo.service.observe(snapshot["runId"], expected_version=snapshot["stateVersion"])
            if snapshot["state"] == "running":
                demo.state.update(state="stopping", stateVersion=demo.state["stateVersion"] + 1, cleanup="in_progress")
                demo.emit("run.state_changed", {"state": "stopping", "stateVersion": demo.state["stateVersion"],
                    "scope": "studio-stop-coordination-before-platform-stop"})
                demo.save()
                demo.quiesce_native()
                snapshot = demo.service.collect_native_observations(snapshot["runId"], expected_version=snapshot["stateVersion"])
                if snapshot["state"] == "running":
                    snapshot = demo.service.stop(snapshot["runId"], expected_version=snapshot["stateVersion"])
        return snapshot
    except BaseException:
        demo.runtime_fault = True
        raise
    finally:
        # An adapter/IO failure outside SDK callbacks still requests owned cleanup.
        try:
            try:
                remaining = demo.service.read(demo.request["runId"])
            except ExecutionInputError as error:
                if error.code == "MPX-RUN-NOT-FOUND":
                    remaining = None
                else:
                    raise
            if remaining and remaining["state"] == "running" and getattr(demo, "runtime_fault", False):
                remaining = demo.service.observe(remaining["runId"], expected_version=remaining["stateVersion"])
            if remaining and remaining["state"] in ("preparing", "running", "stopping"):
                remaining = demo.service.stop(remaining["runId"], expected_version=remaining["stateVersion"])
            snapshot = remaining
            if snapshot:
                demo.project_platform(snapshot)
        finally:
            finished.set()
            watcher.join(timeout=2)
            demo.service.close()


def main():
    demo = PlatformDemo(Path(sys.argv[1]).resolve())
    for kind in (signal.SIGTERM, signal.SIGINT):
        signal.signal(kind, lambda *_: setattr(demo, "stop_requested", True))
    failed = False
    snapshot = None
    try:
        snapshot = run(demo)
    except Exception as error:
        failed = True
        demo.state["reason"] = str(error) if isinstance(error, (InstallationError, ExecutionInputError)) else "AUTOVERSE_PLATFORM_WORKER_FAILED"
    actual = snapshot or demo.platform_latest or {}
    cancelled_start = demo.stop_requested and actual.get("failureCode") == "MPX-START-CANCELLED"
    failed |= actual.get("state") != "stopped" and not cancelled_start
    demo.state.update(state="failed" if failed else "stopped", stateVersion=demo.state["stateVersion"] + 1,
        endedAt=time.time(), cleanup="complete" if actual.get("cleanup") == "released" else "unknown", evidence="partial")
    try:
        original = EvidenceStore.read_run(Path(demo.installation["nativeBridge"]["runtimeRoot"]) / (demo.request["runId"] + ".argus"))
        demo.state["evidence"] = "available" if not failed and original.assessed_evidence_status == "complete" else "partial"
    except Exception:
        demo.state["evidenceFailure"] = "AUTOVERSE_PLATFORM_EVIDENCE_UNAVAILABLE"
    if demo.stop_command:
        demo.state["commandResults"][demo.stop_command["operationId"]] = {
            "status": "completed" if demo.state["cleanup"] == "complete" else "unknown",
            "platformStopOperationId": actual.get("stopOperationId")}
    try:
        demo.emit("run.state_changed", {"state": demo.state["state"], "cleanup": demo.state["cleanup"],
            "platformState": actual.get("state"), "platformStopOperationId": actual.get("stopOperationId")})
        demo.journal.close()
        demo.state.update(journalDigest=digest((demo.root / "evidence.jsonl").read_bytes()), eventCount=demo.count)
        demo.save()
    finally:
        if demo.lock:
            demo.lock.close()
        demo.selector.close()
    return int(failed)


if __name__ == "__main__":
    raise SystemExit(main())
