"""Backend-lifetime ownership of the original public Maestro service.

No recovered claim creates an ownership handle. Lost-owner registrations remain
fenced. Each callback selects its original run context, including reverse cleanup.
"""

from pathlib import Path
import json
import threading
import uuid

import psutil
from xverse.maestro.execution import ExecutionInputError, PublicExecutionService
from xverse_studio.providers.backend_task import BackendTask
from xverse_studio.security.managed_io import open_read
from xverse_studio.storage.core import atomic, canonical
from .installation import InstallationError
from .preparation import AutoverseInputs

MARKER = ".studio-owner.json"


def prior_owner(installation):
    root = Path(installation["nativeBridge"]["runtimeRoot"])
    if not (root / MARKER).exists():
        return False
    # A marker from a preceding owner is a fence, never a recoverable PID handle.
    with open_read(root, root / MARKER) as stream:
        raw = stream.read(65537)
    if len(raw) > 65536:
        raise InstallationError("AUTOVERSE_PLATFORM_OWNER_METADATA_INVALID")
    try:
        value = json.loads(raw)
        if value.get("version") != "1.0" or not isinstance(value.get("ownerId"), str):
            raise ValueError()
    except (ValueError, TypeError, AttributeError):
        raise InstallationError("AUTOVERSE_PLATFORM_OWNER_METADATA_INVALID") from None
    return True


class RuntimeRouter(AutoverseInputs):
    """One installed provider; original callback contexts are keyed by run ID."""

    def __init__(self, installation, adapter):
        super().__init__(installation, runtime_adapter=adapter)
        self.contexts = {}

    def context(self, run_id):
        try:
            return self.contexts[run_id]
        except KeyError:
            raise ExecutionInputError(
                "AUTOVERSE_ORIGINAL_CONTEXT_UNAVAILABLE"
            ) from None

    @property
    def installation_digest(self):
        # Only one run may be active; a retained unresolved context fences starts.
        if len(self.contexts) != 1:
            raise ExecutionInputError("AUTOVERSE_ORIGINAL_CONTEXT_UNAVAILABLE")
        return next(iter(self.contexts.values())).installation_digest

    def validate_runtime(self, effective, prepared):
        return self.context(prepared.submission.run_id).validate_runtime(
            effective, prepared
        )

    def dispatch(self, phase, effective, context):
        return self.context(context.run_id).dispatch(phase, effective, context)

    def cleanup(self, phase, effective, context):
        return self.context(context.run_id).cleanup(phase, effective, context)

    def observe_runtime(self, effective, context):
        return self.context(context.run_id).observe_runtime(effective, context)

    def observation_clock_declarations(self, effective, run_id, operation_id):
        return self.context(run_id).observation_clock_declarations(
            effective, run_id, operation_id
        )

    def read_observation_batch(self, effective, context):
        return self.context(context.run_id).read_observation_batch(effective, context)


class PlatformOwner:
    def __init__(self, installation, adapter):
        self.installation = installation
        self.adapter = adapter
        self.owner_id = "owner-" + uuid.uuid4().hex
        self.root = Path(installation["nativeBridge"]["runtimeRoot"])
        self.router = RuntimeRouter(installation, adapter)
        self.service = None
        self.host = None
        self.task = None
        self.closed = False
        self.fenced = prior_owner(installation)
        self.completed = set()
        self.attempted = set()
        self._lock = threading.RLock()

    def assert_available(self):
        if (
            self.closed
            or self.fenced
            or (
                self.router.contexts
                and (self.task is None or self.task.poll() is not None)
            )
        ):
            raise InstallationError("AUTOVERSE_PLATFORM_OWNER_RECOVERY_REQUIRED")
        if self.task is not None and self.task.poll() is None:
            raise InstallationError("AUTOVERSE_PLATFORM_OWNER_BUSY")
        if len(self.completed) >= 128:
            raise InstallationError("AUTOVERSE_PLATFORM_OWNER_RUN_LIMIT")

    def prepare_task(self, root):
        with self._lock:
            self.assert_available()
            # Imports stay inside the installed integration; no project code runs.
            from .maestro_worker import PlatformDemo, execute

            def target(task_id):
                demo = PlatformDemo(root, owner_task_id=task_id)
                return execute(demo, owner=self)

            self.task = BackendTask(target)
            return self.task

    def acquire(self, preparation, provider):
        with self._lock:
            if self.closed or self.fenced or self.router.contexts:
                raise InstallationError("AUTOVERSE_PLATFORM_OWNER_RECOVERY_REQUIRED")
            if self.host is not None and preparation.host != self.host:
                raise InstallationError("AUTOVERSE_PLATFORM_OWNER_HOST_CHANGED")
            run_id = preparation.prepared.submission.run_id
            self.router.contexts[run_id] = provider
            try:
                if self.service is None:
                    self.service = PublicExecutionService(
                        self.root,
                        preparation.host,
                        (self.router,),
                        max_runtime_seconds=2700,
                        cleanup_budget_seconds=60,
                    )
                    self.host = preparation.host
                self.attempted.add(run_id)
                self._record_owner(run_id)
                return self.service
            except BaseException:
                self.router.contexts.pop(run_id)
                raise

    def _record_owner(self, run_id):
        process = psutil.Process()
        atomic(
            self.root / MARKER,
            canonical(
                {
                    "version": "1.0",
                    "ownerId": self.owner_id,
                    "pid": process.pid,
                    "createTime": process.create_time(),
                    "fenced": self.fenced,
                    "runIds": sorted(self.attempted),
                    "lastRunId": run_id,
                }
            ).encode(),
        )

    def release_run(self, demo, snapshot):
        with self._lock:
            if snapshot is None:
                # A claim may have been written before an IO/provider failure.
                # Absence of a readable result never establishes release.
                self.fenced = True
            else:
                self.completed.add(snapshot["runId"])
                original_children_live = any(
                    record["process"].poll() is None
                    for record in demo.processes.values()
                )
                if snapshot.get("cleanup") == "released" and original_children_live:
                    # A contradictory provider receipt cannot retire an actual
                    # original child handle or authorize another activation.
                    demo.owner_cleanup_contradiction = True
                if (
                    snapshot.get("cleanup") != "released"
                    or snapshot.get("state") not in ("stopped", "failed")
                    or original_children_live
                ):
                    self.fenced = True
                else:
                    self.router.contexts.pop(snapshot["runId"], None)
                    # All original acquired resources were released by Core.
                    # Dispose only their already-exited stdio handles.
                    for record in demo.processes.values():
                        process = record["process"]
                        if process.poll() is not None:
                            for pipe in (process.stdin, process.stdout, process.stderr):
                                if pipe is not None:
                                    pipe.close()
            self._record_owner(demo.request["runId"])

    def close(self):
        with self._lock:
            if self.task is not None and self.task.poll() is None:
                return False
            if self.router.contexts:
                return False
            if self.service is not None:
                self.service.close()
            self.closed = True
            return True
