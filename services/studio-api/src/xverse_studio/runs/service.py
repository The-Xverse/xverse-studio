from __future__ import annotations
import hashlib
import hmac
import json
import math
import os
import platform
import secrets
import subprocess
import sys
import time
import psutil
from xverse_studio.storage.core import (
    Problem,
    atomic,
    canonical,
    digest,
    uid,
    contained,
)
from xverse_studio.providers.registry import (
    capability_digest,
    descriptors,
)
from xverse_studio.evidence.reader import read_journal
from xverse_studio.security.managed_io import read_bounded, SafeIOError
from xverse_studio.deployments import compile_selection
from xverse_studio.profiles import ProfileRegistry
from xverse_studio.preflight import reference_readiness
from xverse_studio.providers.reference_control import CONTROL_STATES, MAX_PAUSED_WALL_SECONDS, MAX_LIVE_MUTATIONS, admitted_controls, live_change


def _observation_version(run):
    version = run.get("observationVersion", 0)
    if type(version) is not int or not 0 <= version <= 2**53 - 1:
        raise Problem("RUN_OBSERVATION_UNAVAILABLE", "The stored observation version is invalid; inspect the retained data or restore a verified backup.", 503)
    return version


def _advance_observation(run):
    version = _observation_version(run)
    if version == 2**53 - 1:
        raise Problem("RUN_OBSERVATION_UNAVAILABLE", "The observation version limit was reached; retain this run and inspect its evidence before making another request.", 503)
    run["observationVersion"] = version + 1


ACTIVE = {
    "requested",
    "preparing",
    "ready",
    "running",
    "paused",
    "stopping",
    "reconciling",
    "unknown",
}
MAX_RUNTIME_REPORT_BYTES = 1024 * 1024
MAX_RUNTIME_REPORT_ATTEMPTS = 4


def _unique_report_fields(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("Duplicate runtime report field")
        result[key] = value
    return result


def _valid_observed_report(value):
    """Inspect known envelope fields; this grants no process or command authority."""
    if not isinstance(value, dict):
        return False
    try:
        canonical(value).encode("utf-8")
    except (TypeError, ValueError, RecursionError):
        return False
    state = value.get("state")
    if not isinstance(state, str) or state not in ACTIVE | {"stopped", "failed"}:
        return False
    if type(value.get("stateVersion")) is not int or value["stateVersion"] < 0:
        return False
    if type(value.get("pid")) is not int or value["pid"] <= 0:
        return False
    birth = value.get("createTime")
    if type(birth) not in (int, float):
        return False
    try:
        if not math.isfinite(birth) or birth < 0:
            return False
    except OverflowError:
        return False
    if not isinstance(value.get("ownerDigest"), str) or not value["ownerDigest"]:
        return False
    for key, allowed in (
        ("cleanup", {"not_started", "in_progress", "complete", "failed", "unknown"}),
        ("evidence", {"pending", "collecting", "complete", "partial", "invalid", "unavailable", "available"}),
    ):
        if key in value and (not isinstance(value[key], str) or value[key] not in allowed):
            return False
    results = value.get("commandResults", {})
    return isinstance(results, dict) and all(
        isinstance(result, dict) and isinstance(result.get("status"), str)
        for result in results.values()
    )


class Runs:
    def __init__(self, store, projects, adapter, installed_providers=None):
        self.store, self.projects, self.adapter = store, projects, adapter
        self.children = {}
        self.installed_providers = dict(installed_providers or {})
        from xverse_studio.platform_observability.views import PlatformViews
        self.platform_views = PlatformViews()
        import re
        builtins = {entry["providerId"] for entry in descriptors()}
        for provider_id in self.installed_providers:
            if (not isinstance(provider_id, str) or not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]{0,127}", provider_id)
                    or provider_id in builtins):
                raise Problem("PROVIDER_DESCRIPTOR_INVALID", "Installed provider identities must be unique and match their registration.")

    def provider_descriptors(self):
        from xverse_studio.providers.descriptors import admit_descriptor, unavailable_descriptor, validate_installed_binding, UnavailableProvider
        result = descriptors()
        for provider_id, provider in self.installed_providers.items():
            if type(provider) is UnavailableProvider:
                result.append(provider.descriptor())
                continue
            try:
                descriptor = admit_descriptor(provider.descriptor())
                if descriptor["providerId"] != provider_id:
                    raise Problem("PROVIDER_DESCRIPTOR_INVALID", "The provider identity differs from its native registration.")
                validate_installed_binding(provider, descriptor)
            except Problem as error:
                descriptor = unavailable_descriptor(provider_id, error.code)
            except Exception:
                # A native describe failure does not disable authoring or grant
                # operations. Never expose the exception or invalid raw payload.
                descriptor = unavailable_descriptor(provider_id, "PROVIDER_DESCRIPTOR_UNAVAILABLE")
            result.append(descriptor)
        return result

    def platform_view(self, rid, query):
        run = self.store.get("run", rid)
        snapshot = self.store.get("snapshot", run["snapshotId"])
        self.verify_snapshot(snapshot)
        provider = self.installed_providers.get(run["providerId"])
        binding = getattr(provider, "platform_evidence_binding", None)
        if binding is None:
            raise Problem("PLATFORM_SOURCE_UNAVAILABLE", "This run has no installed Maestro/X-COM/Argus reader binding. Its Studio journal remains available separately.", 404)
        return self.platform_views.read(binding(run, snapshot), query)

    def capability_digest(self):
        return digest(self.provider_descriptors()) if self.installed_providers else capability_digest()

    def readiness(self, documents, compiled, provider_id, provider, active_count):
        installed = self.installed_providers.get(provider_id)
        if installed is not None:
            import platform
            from xverse_studio.providers.descriptors import admit_descriptor
            try:
                value = admit_descriptor(provider)
                usable = (value["providerId"] == provider_id and value["available"] is True
                          and value["hostCompatible"] is True and platform.system() in value["supportedHostOS"]
                          and platform.machine() in value["architectures"])
            except Problem:
                usable = False
            if not usable:
                return reference_readiness(documents, compiled, provider_id, provider, active_count)
        return (installed.readiness if installed else reference_readiness)(documents, compiled, provider_id, provider, active_count)

    def _reconcile_active_observations(self):
        # Aggregate readiness uses the same original-owner and evidence checks
        # as Start. Unknown observations remain active; this never dispatches.
        for old in self.store.all("run"):
            if old["state"] in ACTIVE:
                self.read(old["runId"])

    def directory(self, rid):
        return contained(self.store.root, self.store.root / "runs" / rid)

    def compilation(self, documents, selection):
        refs = {
            field: selection[field]
            for field in ("systemRef", "deploymentRef", "scenarioRef")
            if selection.get(field) is not None
        }
        return compile_selection(documents, refs, self.adapter)

    def preflight(self, pid, selection):
        p = self.projects.read(pid)
        if selection["revision"] != p["revision"]:
            raise Problem(
                "REVISION_CONFLICT",
                "Select the current project revision.",
                412,
                currentRevision=p["revision"],
            )
        self.projects.assert_intact(p)
        registry = ProfileRegistry(self.adapter)
        profile_locks = registry.validate_project(p)
        documents = self.projects.sources(p)
        project_documents = documents
        compiled = self.compilation(documents, selection)
        refs = compiled["selection"]
        if compiled["valid"]:
            documents = compiled["contributingDocuments"]
        diagnostics = list(compiled["diagnostics"])
        provider_id = selection.get("providerId", "studio.reference")
        provider = next(
            (value for value in self.provider_descriptors() if value["providerId"] == provider_id),
            None,
        )
        self._reconcile_active_observations()
        active_count = sum(row["state"] in ACTIVE for row in self.store.all("run"))
        readiness, admission_diagnostics, configuration, limits = self.readiness(
            documents, compiled, provider_id, provider, active_count
        )
        diagnostics.extend(admission_diagnostics)
        # Authored profiles that are unadmitted or differ from admitted semantics never execute.
        diagnostics.extend(registry.authored_findings(project_documents))
        if compiled["valid"]:
            # Declared connection semantics without an admitted contract block execution.
            from xverse_studio.connections import admission_diagnostics as blocking
            from xverse_studio.connections import admit_connections

            diagnostics.extend(
                blocking(
                    admit_connections(
                        documents,
                        {"diagnostics": compiled.get("diagnostics", [])},
                        provider,
                    )
                )
            )
            # Undecidable compatibility, undefined precedence and unresolved environment
            # bindings of the selected Deployment block execution (ADR-0015).
            from xverse_studio.deployments.resolution import (
                resolution_diagnostics,
                resolve_deployment,
            )

            diagnostics.extend(
                resolution_diagnostics(
                    resolve_deployment(
                        documents,
                        refs["deploymentRef"],
                        host_os=platform.system(),
                        provider=provider,
                    )
                )
            )
        snapid = uid("snap-")
        pfid = uid("pf-")
        snapshot = {
            "snapshotId": snapid,
            "projectId": pid,
            "revision": p["revision"],
            "documents": documents,
            "projectDocuments": project_documents,
            "profileLocks": profile_locks,
            "projectRevisionInputsDigest": compiled["projectRevisionInputsDigest"],
            "plan": compiled.get("plan"),
            "planDigest": compiled.get("planDigest"),
            "semanticDigest": compiled.get("semanticDigest"),
            "configuration": configuration,
            "providerId": provider_id,
            "providerIdentity": provider,
            "capabilityDigest": self.capability_digest(),
            "createdAt": time.time(),
            "compiler": compiled.get("compiler"),
            "selection": refs,
        }
        snapshot["snapshotDigest"] = digest(snapshot)
        ready = configuration is not None and not any(
            d.get("severity") == "error" for d in diagnostics
        )
        pf = {
            "preflightId": pfid,
            "snapshotId": snapid,
            "snapshotDigest": snapshot["snapshotDigest"],
            "revision": p["revision"],
            "providerId": provider_id,
            "providerIdentity": provider,
            "readinessVersion": "1.0",
            "readiness": readiness,
            "status": "ready" if ready else "blocked",
            "planDigest": compiled.get("planDigest"),
            "semanticDigest": compiled.get("semanticDigest"),
            "capabilityDigest": self.capability_digest(),
            "expiresAt": time.time() + 60,
            "diagnostics": diagnostics,
            "dimensions": {
                **{name: fact["status"] for name, fact in readiness.items()},
                "evidenceScope": provider.get("evidenceScope", "unavailable")
                if provider
                else "unavailable",
            },
            "limits": limits,
            "selection": refs,
            "contributingDocuments": list(documents),
            "planPreview": {
                "snapshotId": snapid,
                "snapshotDigest": snapshot["snapshotDigest"],
                "revision": p["revision"],
                "selection": refs,
                "planDigest": compiled.get("planDigest"),
                "semanticDigest": compiled.get("semanticDigest"),
                "compiler": compiled.get("compiler"),
                "contributingDocuments": list(documents),
                "plan": compiled["plan"],
                "scope": "declared_intent_only",
            }
            if compiled.get("plan")
            else None,
        }
        with self.store.tx() as db:
            self.store.put("snapshot", snapid, snapshot, db)
            self.store.put("preflight", pfid, pf, db)
        atomic(
            self.store.root / "snapshots" / snapid / "snapshot.json",
            canonical(snapshot).encode(),
        )
        return pf

    def require_campaign_snapshot(self, snapshot, db=None):
        """Prior admission is required; a compiled blocked draft is not authority.

        Legacy snapshots remain immutable. Resolve their existing matching ready
        preflight with a bounded parameterized metadata query instead of upgrading
        a historical blocked snapshot to an owned reference configuration.
        """
        if db is None:
            with self.store.tx() as connection:
                return self.require_campaign_snapshot(snapshot, connection)
        if (
            snapshot.get("providerId") != "studio.reference"
            or not snapshot.get("configuration")
            or not snapshot.get("planDigest")
        ):
            raise Problem(
                "ADMISSION_REJECTED",
                "Campaigns require a previously admitted owned-reference snapshot.",
            )
        self.verify_snapshot(snapshot)
        needle = '"snapshotId":' + canonical(snapshot["snapshotId"])
        candidates = []
        for row in db.execute(
            "SELECT body FROM records WHERE kind=? AND instr(body,?)>0 LIMIT 32",
            ("preflight", needle),
        ):
            pf = json.loads(row[0])
            if pf.get("snapshotId") == snapshot["snapshotId"]:
                candidates.append(pf)
        if (
            len(candidates) != 1
            or candidates[0].get("status") != "ready"
            or candidates[0].get("planDigest") != snapshot["planDigest"]
            or candidates[0].get("capabilityDigest") != snapshot.get("capabilityDigest")
        ):
            raise Problem(
                "ADMISSION_REJECTED",
                "A matching original ready preflight is required; blocked drafts confer no campaign authority.",
            )

    def verify_snapshot(self, snapshot):
        from xverse_studio.security.managed_io import open_read, SafeIOError

        if digest(
            {k: v for k, v in snapshot.items() if k != "snapshotDigest"}
        ) != snapshot.get("snapshotDigest"):
            raise Problem(
                "SNAPSHOT_INTEGRITY", "The frozen snapshot digest cannot be verified."
            )
        try:
            with open_read(
                self.store.root,
                self.store.root
                / "snapshots"
                / snapshot["snapshotId"]
                / "snapshot.json",
            ) as source:
                if os.fstat(source.fileno()).st_size > 64 * 1024 * 1024:
                    raise Problem(
                        "SNAPSHOT_INTEGRITY",
                        "The frozen snapshot exceeds its read bound.",
                    )
                raw = source.read(64 * 1024 * 1024 + 1)
            if len(raw) > 64 * 1024 * 1024 or raw != canonical(snapshot).encode():
                raise Problem(
                    "SNAPSHOT_INTEGRITY",
                    "The immutable snapshot bytes cannot be verified.",
                )
        except (OSError, SafeIOError):
            raise Problem(
                "SNAPSHOT_INTEGRITY",
                "The frozen snapshot file is unavailable or changed during inspection.",
            ) from None

    def start(self, principal, key, payload, *, allow_frozen=False):
        def accepted(db):
            pf = self.store.get("preflight", payload["preflightId"], db)
            snap = self.store.get("snapshot", payload["snapshotId"], db)
            self.verify_snapshot(snap)
            if pf["snapshotId"] != snap["snapshotId"] or pf["status"] != "ready":
                raise Problem(
                    "ADMISSION_REJECTED",
                    "Only a ready preflight for these exact inputs can start.",
                )
            if (
                pf["expiresAt"] <= time.time()
                or pf["capabilityDigest"] != self.capability_digest()
            ):
                raise Problem(
                    "PREFLIGHT_STALE",
                    "Preflight expired or capabilities changed; preflight again.",
                    409,
                )
            ProfileRegistry(self.adapter).validate_snapshot(snap)
            p = self.projects.read(snap["projectId"], db)
            if not allow_frozen:
                self.projects.assert_intact(p)
                if ProfileRegistry(self.adapter).validate_project(p) != snap.get(
                    "profileLocks", []
                ):
                    raise Problem(
                        "PREFLIGHT_STALE",
                        "Profile lock identities changed after preflight.",
                        409,
                    )
            if not allow_frozen and (
                p["revision"] != snap["revision"]
                or digest(self.projects.sources(p))
                != snap.get("projectRevisionInputsDigest", digest(snap["documents"]))
            ):
                raise Problem(
                    "PREFLIGHT_STALE", "Project inputs changed after preflight.", 409
                )
            compiled = self.adapter.compile(snap["documents"])
            current_provider = next(
                (
                    value
                    for value in self.provider_descriptors()
                    if value["providerId"] == snap.get("providerId")
                ),
                None,
            )
            if snap.get("providerId") != "studio.reference" and snap.get("providerId") not in self.installed_providers:
                raise Problem(
                    "ADMISSION_REJECTED",
                    "This runtime cannot substitute an owned provider for the selected provider.",
                )
            if digest(current_provider) != digest(snap.get("providerIdentity")):
                raise Problem(
                    "PREFLIGHT_STALE",
                    "Selected provider identity or native compatibility changed; preflight again.",
                    409,
                )
            current_active = sum(
                row["state"] in ACTIVE for row in self.store.all("run", db)
            )
            checks, errors, config, _ = self.readiness(
                snap["documents"],
                compiled,
                snap["providerId"],
                current_provider,
                current_active,
            )
            if config is None:
                code = (
                    "RESOURCE_BUSY"
                    if any(error["code"] == "RESOURCE_BUSY" for error in errors)
                    else "ADMISSION_REJECTED"
                )
                raise Problem(
                    code,
                    "Current read-only admission facts no longer allow this execution. Recheck the independent readiness dimensions.",
                    409 if code == "RESOURCE_BUSY" else 422,
                    diagnostics=errors,
                    readiness=checks,
                )
            if (
                digest(config) != digest(snap["configuration"])
                or compiled["planDigest"] != snap["planDigest"]
            ):
                raise Problem(
                    "PREFLIGHT_STALE",
                    "Effective provider inputs differ from the snapshot.",
                    409,
                )
            if sum(r["state"] in ACTIVE for r in self.store.all("run", db)) >= 4:
                raise Problem(
                    "RESOURCE_BUSY",
                    "Reference concurrency limit is four owned runs.",
                    409,
                )
            rid = uid("run-")
            oid = uid("op-")
            run = {
                "runId": rid,
                "snapshotId": snap["snapshotId"],
                "projectId": snap["projectId"],
                "revision": snap["revision"],
                "operationId": oid,
                "state": "requested",
                "stateVersion": 0,
                "observationVersion": 0,
                "cleanup": "not_started",
                "evidence": "pending",
                "evaluation": "not_started",
                "verdict": None,
                "evidenceScope": snap["providerIdentity"]["evidenceScope"],
                "providerId": snap["providerId"],
                "createdAt": time.time(),
                "planDigest": snap["planDigest"],
                "semanticDigest": snap["semanticDigest"],
                "capabilities": list(self.installed_providers[snap["providerId"]].controls) if snap["providerId"] in self.installed_providers else admitted_controls(snap["providerIdentity"], config),
                "controlLimits": {} if snap["providerId"] in self.installed_providers else {"maxPausedWallSeconds": MAX_PAUSED_WALL_SECONDS},
            }
            if snap["providerId"] in self.installed_providers:
                installed = self.installed_providers[snap["providerId"]]
                run.update(installed.run_metadata(config) if hasattr(installed, "run_metadata") else {"inputSurface": snap["providerIdentity"].get("inputSurface")})
                run.update(journalId=rid + ":provider-journal", journalReader="studio.hash-chain-v1")
            if "set_parameter" in run["capabilities"]:
                run.update(liveInputs=config["liveInputs"], liveValues={"target": config["target"]}, liveMutationCount=0)
                run["controlLimits"]["maxLiveMutations"] = MAX_LIVE_MUTATIONS
            operation = {
                "operationId": oid,
                "status": "accepted",
                "runId": rid,
                "kind": "start",
            }
            self.store.put("run", rid, run, db)
            self.store.put("operation", oid, operation, db)
            return {"runId": rid, "operationId": oid, "stateVersion": 0}

        self._reconcile_active_observations()
        result, new = self.store.idempotent(
            principal, "POST /runs", key, payload, accepted
        )
        if new:
            self._dispatch(result["runId"])
        return result

    def _record_dispatch(self, rid, changes, operation_changes=None, *, acknowledged_pid=None):
        # A read may reconcile accepted/preparing state while file or process I/O
        # is in flight. Merge only this handoff's facts into the latest record.
        with self.store.tx() as db:
            run = self.store.get("run", rid, db)
            previous = canonical(run)
            if (
                changes.get("reason") == "LAUNCH_ACKNOWLEDGEMENT_LOST"
                and acknowledged_pid is not None
                and run.get("pid") == acknowledged_pid
                and run.get("createTime") is not None
                and run.get("ownerDigest")
                and run.get("state") in ("stopped", "failed")
            ):
                # A read already verified this exact child's terminal report.
                # A late parent lookup grants no new authority and cannot undo it.
                changes = {k: v for k, v in changes.items() if k not in {"state", "cleanup", "reason"}}
            run.update(changes)
            if changes.get("state") == "preparing" and run.get("reason") == "OWNERSHIP_UNKNOWN":
                run.pop("reason")
            if canonical(run) != previous:
                _advance_observation(run)
                self.store.put("run", rid, run, db)
            if operation_changes is not None:
                operation = self.store.get("operation", run["operationId"], db)
                previous_operation = canonical(operation)
                if not (
                    operation_changes.get("status") == "unknown"
                    and operation.get("status") in ("completed", "failed")
                ):
                    # Start completion is a historical receipt, independent of
                    # whether a later observation can establish current ownership.
                    operation.update(operation_changes)
                if canonical(operation) != previous_operation:
                    self.store.put("operation", operation["operationId"], operation, db)

    def _dispatch(self, rid):
        run = self.store.get("run", rid)
        snap = self.store.get("snapshot", run["snapshotId"])
        if snap["providerId"] in self.installed_providers:
            current = next((p for p in self.provider_descriptors() if p["providerId"] == snap["providerId"]), None)
            if current != snap["providerIdentity"] or not current or current.get("available") is not True:
                self._record_dispatch(rid,
                    dict(state="failed", cleanup="complete", evidence="unavailable",
                         reason="PROVIDER_ADMISSION_CHANGED", endedAt=time.time()),
                    dict(status="failed", code="PROVIDER_ADMISSION_CHANGED"))
                return
        root = self.directory(rid)
        try:
            root.mkdir(parents=True, exist_ok=True)
            secret = secrets.token_bytes(32)
            atomic(root / "owner.key", secret)
            try:
                (root / "owner.key").chmod(0o600)
            except OSError:
                pass
            atomic(
                root / "request.json",
                canonical(
                    {
                        "runId": rid,
                        "operationId": run["operationId"],
                        "snapshot": snap,
                        "configuration": snap["configuration"],
                        **({"nativeInstallation": self.installed_providers[snap["providerId"]].installation} if snap["providerId"] in self.installed_providers else {}),
                    }
                ).encode(),
            )
            worker_tmp = root / "tmp"
            worker_tmp.mkdir(exist_ok=True)
        except OSError:
            # No native launch was attempted. Retain partial private files for
            # inspection; there are no runtime resources or workload results.
            self._record_dispatch(
                rid,
                dict(state="failed", cleanup="complete", evidence="unavailable",
                     reason="PREPARATION_FAILED", endedAt=time.time()),
                dict(status="failed", code="PREPARATION_FAILED"),
            )
            return
        installed = self.installed_providers.get(snap["providerId"])
        prepare_task = getattr(installed, "prepare_backend_task", None)
        if callable(prepare_task):
            from xverse_studio.providers.backend_task import BackendTask
            try:
                task = prepare_task(root)
                if type(task) is not BackendTask:
                    raise ValueError("PROVIDER_TASK_INVALID")
            except (Problem, OSError, ValueError):
                self._record_dispatch(rid,
                    dict(state="failed", cleanup="complete", evidence="unavailable",
                         reason="PROVIDER_TASK_PREPARATION_FAILED", endedAt=time.time()),
                    dict(status="failed", code="PROVIDER_TASK_PREPARATION_FAILED"))
                return
            # Record the actual backend/task identity BEFORE its callback can
            # acquire anything. An alive backend PID alone is not task liveness.
            self.children[rid] = task
            self._record_dispatch(rid,
                dict(ownerDigest=digest(secret), state="preparing", executionKind="backend-task",
                     ownerTaskId=task.task_id, pid=task.pid, createTime=task.create_time,
                     launchArgvDigest=digest(task.argv), launchStartedAt=time.time()),
                dict(status="delegated"), acknowledged_pid=task.pid)
            try:
                task.start()
            except (OSError, RuntimeError):
                self._record_dispatch(rid,
                    dict(state="unknown", cleanup="unknown", evidence="partial", reason="LAUNCH_ACKNOWLEDGEMENT_LOST"),
                    dict(status="unknown"))
            return
        launch_argv = [
            sys.executable,
            "-I",
            "-m",
            self.installed_providers[snap["providerId"]].worker_module if snap["providerId"] in self.installed_providers else "xverse_studio.providers.worker",
            str(root),
        ]
        self._record_dispatch(
            rid,
            dict(ownerDigest=digest(secret), state="preparing", launchArgvDigest=digest(launch_argv)),
            dict(status="delegated"),
        )
        try:
            kwargs = (
                {"start_new_session": True}
                if os.name != "nt"
                else {
                    "creationflags": subprocess.CREATE_NEW_PROCESS_GROUP
                    | subprocess.DETACHED_PROCESS
                }
            )
            child_env = {
                key: os.environ[key]
                for key in (
                    "SystemRoot",
                    "WINDIR",
                    "PATH",
                    "LANG",
                    "LC_ALL",
                    "LC_CTYPE",
                )
                if key in os.environ
            }
            child_env.update(
                TMPDIR=str(worker_tmp), TEMP=str(worker_tmp), TMP=str(worker_tmp)
            )
            process = subprocess.Popen(
                launch_argv,
                cwd=str(root),
                env=child_env,
                stdin=subprocess.DEVNULL,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                close_fds=True,
                **kwargs,
            )
            self.children[rid] = process
            # Preparation can take longer than the worker's observation window.
            # Start the existing budget only once the native launch is acknowledged.
            acknowledgement = {"launchStartedAt": time.time()}
        except OSError:
            self._record_dispatch(
                rid,
                dict(state="failed", cleanup="unknown", evidence="unavailable", reason="LAUNCH_FAILED"),
                dict(status="failed", code="LAUNCH_FAILED"),
            )
            return
        operation_changes = None
        try:
            acknowledgement.update(
                pid=process.pid, createTime=psutil.Process(process.pid).create_time()
            )
        except psutil.Error:
            acknowledgement.update(
                state="unknown", cleanup="unknown", reason="LAUNCH_ACKNOWLEDGEMENT_LOST"
            )
            operation_changes = {"status": "unknown"}
        self._record_dispatch(rid, acknowledgement, operation_changes, acknowledged_pid=process.pid)

    def _read_report(self, statepath):
        for attempt in range(MAX_RUNTIME_REPORT_ATTEMPTS):
            try:
                raw = read_bounded(self.store.root, statepath, MAX_RUNTIME_REPORT_BYTES)
                break
            except SafeIOError as error:
                # A producer can atomically publish another complete report
                # during capture. Reacquire within the same declared bound.
                if error.code == "SOURCE_CHANGED" and attempt + 1 < MAX_RUNTIME_REPORT_ATTEMPTS:
                    continue
                raise
        return json.loads(raw.decode("utf-8"), object_pairs_hook=_unique_report_fields)

    def _terminal_after_exit(self, statepath, run):
        """Reacquire once after exit, using only an already recorded owner identity."""
        if (
            run.get("pid") is None
            or run.get("createTime") is None
            or not run.get("ownerDigest")
        ):
            return None
        observed = self._read_report(statepath)
        if (
            _valid_observed_report(observed)
            and observed.get("state") in ("stopped", "failed")
            and observed["stateVersion"] >= run["stateVersion"]
            and (run["state"] not in ("stopped", "failed") or observed["state"] == run["state"])
            and observed.get("ownerDigest") == run.get("ownerDigest")
            and observed.get("pid") == run["pid"]
            and observed.get("createTime") == run["createTime"]
        ):
            return observed
        return None

    def read(self, rid):
        with self.store.lock:
            run = self.store.get("run", rid)
            _observation_version(run)
            previous_run = canonical(run)
            # Observation acquisition enforces native containment itself. A
            # rebound directory must become unavailable, not a resolver error
            # before ownership reconciliation can retain its unknown outcome.
            root = self.store.root / "runs" / rid
            statepath = root / "state.json"
            observed = None
            report_present = True  # An inspection failure cannot use initial-absence grace.
            try:
                try:
                    observed = self._read_report(statepath)
                except SafeIOError as error:
                    report_present = error.code != "FILE_MISSING"
                    raise
                if not _valid_observed_report(observed):
                    observed = None
                if observed and (observed["stateVersion"] < run["stateVersion"]
                        or (run["state"] in ("stopped", "failed") and observed["state"] != run["state"])):
                    observed = None
                if observed and observed.get("ownerDigest") != run.get("ownerDigest"):
                    observed = None
                if observed:
                    if (
                        run.get("pid") is None
                        and observed.get("pid")
                        and observed.get("createTime")
                    ):
                        candidate = psutil.Process(observed["pid"])
                        argv = candidate.cmdline()
                        if abs(
                            candidate.create_time() - observed["createTime"]
                        ) <= 0.001 and digest(argv) == run.get(
                            "launchArgvDigest",
                            digest(
                                [
                                    sys.executable,
                                    "-I",
                                    "-m",
                                    "xverse_studio.providers.worker",
                                    str(root),
                                ]
                            ),
                        ):
                            run.update(
                                pid=observed["pid"], createTime=observed["createTime"]
                            )
                        else:
                            observed = None
                    elif run.get("pid") != observed.get("pid") or run.get(
                        "createTime"
                    ) != observed.get("createTime"):
                        observed = None
                if (observed and run.get("executionKind") == "backend-task"
                        and observed.get("ownerTaskId") != run.get("ownerTaskId")):
                    observed = None
                if observed and observed["state"] not in ("stopped", "failed"):
                    if run.get("executionKind") == "backend-task":
                        task = self.children.get(rid)
                        if (task is None or task.task_id != run.get("ownerTaskId")
                                or observed.get("ownerTaskId") != run.get("ownerTaskId")
                                or task.poll() is not None):
                            observed = self._terminal_after_exit(statepath, run)
                    if observed is None:
                        raise ValueError("ORIGINAL_BACKEND_TASK_UNAVAILABLE")
                    try:
                        process = psutil.Process(observed["pid"])
                        if abs(process.create_time() - observed["createTime"]) > 0.001:
                            observed = None
                        elif (
                            not process.is_running()
                            or process.status() == psutil.STATUS_ZOMBIE
                        ):
                            observed = self._terminal_after_exit(statepath, run)
                    except psutil.NoSuchProcess:
                        # A running file read may precede the worker's final atomic
                        # replacement and exit. This grants no process control.
                        observed = self._terminal_after_exit(statepath, run)
            except (OSError, ValueError, RecursionError, psutil.Error):
                observed = None
            if observed and not self._valid_observed_commands(run, observed):
                observed = None
            if observed:
                if (
                    run.get("reason") in ("OWNERSHIP_UNKNOWN", "LAUNCH_ACKNOWLEDGEMENT_LOST")
                    and observed.get("state") in ("running", "paused", "stopping", "stopped", "failed")
                    and "reason" not in observed
                ):
                    run.pop("reason", None)
                run.update(
                    {
                        k: observed[k]
                        for k in (
                            "state",
                            "stateVersion",
                            "cleanup",
                            "cleanupResources",
                            "runtimeStatus",
                            "platformStatus",
                            "inputTelemetry",
                            "liveValues",
                            "liveMutationCount",
                            "evidence",
                            "evidenceFailure",
                            "reason",
                            "effectivePlanDigest",
                            "effectiveSemanticDigest",
                            "startedAt",
                            "endedAt",
                            "journalDigest",
                            "eventCount",
                        )
                        if k in observed
                    }
                )
                op = self.store.get("operation", run["operationId"])
                previous_operation = canonical(op)
                op["status"] = ("failed" if observed["state"] == "failed" and not observed.get("startedAt") else "delegated" if observed["state"] in ("preparing", "ready") else "completed")
                op["result"] = {
                    "effectivePlanDigest": observed.get("effectivePlanDigest")
                }
                if canonical(op) != previous_operation:
                    self.store.put("operation", op["operationId"], op)
                for oid, result in observed.get("commandResults", {}).items():
                    try:
                        op = self.store.get("operation", oid)
                        previous_operation = canonical(op)
                        if result["status"] in ("accepted", "delegated"):
                            # Producer progress cannot erase a known receipt or
                            # turn an unknown outcome into a terminal result.
                            if op["status"] not in ("accepted", "delegated", "unknown"):
                                continue
                            result = {**result, "status": op["status"]}
                        op.update(result)
                        if canonical(op) != previous_operation:
                            self.store.put("operation", oid, op)
                    except Problem:
                        pass
            elif run["state"] in ACTIVE:
                task = self.children.get(rid)
                startup_identity_available = (run.get("executionKind") != "backend-task"
                    or (task is not None and task.task_id == run.get("ownerTaskId") and task.poll() is None))
                if (
                    run.get("state") == "preparing"
                    and not report_present
                    and startup_identity_available
                    and time.time() - run.get("launchStartedAt", run["createdAt"]) < 5
                ):
                    return run
                run.update(
                    state="unknown",
                    cleanup="unknown",
                    evidence="partial",
                    reason="OWNERSHIP_UNKNOWN",
                )
                op = self.store.get("operation", run["operationId"])
                if op["status"] not in ("completed", "failed", "unknown"):
                    op["status"] = "unknown"
                    self.store.put("operation", op["operationId"], op)
            self._reconcile_command(run, observed)
            _, integrity = read_journal(root, observed or run)
            run["evidenceAvailability"] = (
                "unavailable" if integrity == "unavailable" else "available"
            )
            if integrity == "invalid":
                run["evidence"] = "invalid"
            if integrity == "unavailable" and run["state"] in ("stopped", "failed"):
                run.setdefault("originalEvidenceStatus", run["evidence"])
                run["evidence"] = "unavailable"
            assessment = getattr(self, "assessment_summary", None)
            if assessment is not None:
                run.update(assessment(run))
            # Ownership, journal integrity and assessments are still observed on
            # every read. Only an actual metadata change needs a durable write.
            if canonical(run) != previous_run:
                _advance_observation(run)
                self.store.put("run", rid, run)
            if rid in self.children and self.children[rid].poll() is not None:
                self.children.pop(rid)
            return run

    def _valid_observed_commands(self, run, observed):
        results = observed.get("commandResults", {})
        if not results:
            return True
        immutable = ("operationId", "runId", "kind", "parameters", "principal", "expectedStateVersion")
        with self.store.tx() as db:
            for operation_id, result in results.items():
                try:
                    operation = self.store.get("operation", operation_id, db)
                except Problem as error:
                    if error.code == "NOT_FOUND":
                        # Owner-side maintenance receipts remain opaque; they
                        # cannot allocate or alter a Studio acceptance.
                        continue
                    return False
                if (not isinstance(operation, dict) or operation.get("runId") != run["runId"]
                        or operation_id == run["operationId"] or operation.get("kind") == "start"):
                    return False
                if result["status"] not in {"accepted", "delegated", "completed", "failed", "unknown", "rejected"}:
                    return False
                if any(key in result and (key not in operation or canonical(result[key]) != canonical(operation[key])) for key in immutable):
                    return False
        return True

    def _command_producer_finished(self, run):
        """Read original handle/identity liveness; never signal or adopt a process."""
        child = self.children.get(run["runId"])
        if child is not None:
            if getattr(child, "pid", None) != run.get("pid"):
                return None
            if (run.get("executionKind") == "backend-task"
                    and getattr(child, "task_id", None) != run.get("ownerTaskId")):
                return None
            return child.poll() is not None
        if run.get("executionKind") == "backend-task":
            # An alive backend PID does not establish completion of a lost task.
            return None
        if run.get("pid") is None or run.get("createTime") is None:
            return None
        try:
            process = psutil.Process(run["pid"])
            if abs(process.create_time() - run["createTime"]) > 0.001:
                return True  # The recorded original exited; this PID belongs elsewhere.
            return not process.is_running() or process.status() == psutil.STATUS_ZOMBIE
        except psutil.NoSuchProcess:
            return True
        except psutil.Error:
            return None

    def _reconcile_command(self, run, observed):
        # An accepted stop/cancel never stays delegated past the evidence that settles it.
        oid = run.get("pendingCommandId")
        if not oid:
            return
        op = self.store.get("operation", oid)
        previous_operation = canonical(op)
        if op["status"] not in ("accepted", "delegated", "unknown"):
            run.pop("pendingCommandId")
        elif observed and observed.get("state") in ("stopped", "failed"):
            finished = self._command_producer_finished(run)
            if finished is False:
                return  # Lifecycle may be terminal while cleanup/result reporting continues.
            final = None
            if finished is True:
                try:
                    final = self._terminal_after_exit(self.directory(run["runId"]) / "state.json", run)
                    if (final and (not self._valid_observed_commands(run, final)
                            or (run.get("executionKind") == "backend-task"
                                and final.get("ownerTaskId") != run.get("ownerTaskId")))):
                        final = None
                except (OSError, ValueError, RecursionError):
                    pass
            if final is not None:
                result = final.get("commandResults", {}).get(oid)
                if result is not None:
                    op.update(result)
                    if result["status"] in ("accepted", "delegated"):
                        op["status"] = "unknown"
                else:
                    op.update(status="failed", code="RUN_TERMINAL_BEFORE_COMMAND")
                if op["status"] not in ("accepted", "delegated", "unknown"):
                    run.pop("pendingCommandId")
            else:
                op["status"] = "unknown"
            if canonical(op) != previous_operation:
                self.store.put("operation", oid, op)
        elif (observed is None or run["state"] == "unknown") and op["status"] != "unknown":
            op["status"] = "unknown"
            self.store.put("operation", oid, op)

    def _require_active_provider(self, run, db=None):
        """Fresh callback compatibility, separate from original cleanup authority."""
        import platform
        try:
            snapshot = self.store.get("snapshot", run["snapshotId"], db)
            if not isinstance(snapshot, dict):
                raise ValueError()
            self.verify_snapshot(snapshot)
            if any(snapshot.get(key) != run.get(key) for key in (
                    "snapshotId", "projectId", "revision", "providerId", "planDigest", "semanticDigest")):
                raise ValueError()
        except Problem as error:
            if error.code != "NOT_FOUND":
                raise
            raise Problem("SNAPSHOT_INTEGRITY", "The original frozen input identity cannot be verified.") from None
        except (KeyError, ValueError, TypeError, AttributeError, RecursionError):
            raise Problem("SNAPSHOT_INTEGRITY", "The original frozen input identity cannot be verified.") from None
        current = next((value for value in self.provider_descriptors() if value["providerId"] == run["providerId"]), None)
        if (current != snapshot.get("providerIdentity") or not current
                or current.get("available") is not True or current.get("hostCompatible") is not True
                or platform.system() not in current.get("supportedHostOS", [])
                or platform.machine() not in current.get("architectures", [])):
            raise Problem("PROVIDER_ADMISSION_CHANGED",
                "Provider admission changed. Stop or Cancel the owned run, then verify the installation and preflight again.", 409)

    def command(self, rid, principal, key, payload):
        # Reconciliation precedes state/authority enforcement; retries still resolve before a new mutation.
        self.read(rid)

        def accepted(db):
            run = self.store.get("run", rid, db)
            if payload["kind"] != "set_parameter" and payload.get("parameters"):
                raise Problem(
                    "COMMAND_PARAMETERS_UNSUPPORTED",
                    "The admitted reference controls accept no additional parameters.",
                )
            if payload["kind"] not in run["capabilities"]:
                raise Problem(
                    "CAPABILITY_UNSUPPORTED",
                    "The selected provider does not support this command.",
                )
            if payload["expectedStateVersion"] != run["stateVersion"]:
                raise Problem(
                    "STATE_CONFLICT",
                    "Run state changed; refresh before controlling it.",
                    409,
                )
            if run["state"] not in CONTROL_STATES.get(payload["kind"], ()):
                raise Problem(
                    "STATE_CONFLICT",
                    "The current owned state does not permit this command.",
                    409,
                )
            if payload["kind"] not in ("stop", "cancel") and run["providerId"] in self.installed_providers:
                self._require_active_provider(run, db)
            if payload["kind"] == "set_parameter":
                try:
                    live_change(payload.get("parameters"), run.get("liveInputs"), run.get("liveValues"), run.get("liveMutationCount"))
                except ValueError as error:
                    raise Problem(str(error), "The live input declaration, value, observed old value or mutation budget does not permit this change.", 409 if str(error) == "LIVE_INPUT_CONFLICT" else 422) from None
            if any(
                op.get("runId") == rid
                and op.get("kind") != "start"
                and op["status"] in ("accepted", "delegated", "unknown")
                for op in self.store.all("operation", db)
            ):
                raise Problem(
                    "STATE_CONFLICT", "An existing command must reconcile first.", 409
                )
            oid = uid("op-")
            op = {
                "operationId": oid,
                "runId": rid,
                "kind": payload["kind"],
                "status": "accepted",
            }
            if payload["kind"] == "set_parameter":
                op.update(parameters=payload["parameters"], principal=principal,
                          expectedStateVersion=payload["expectedStateVersion"])
            self.store.put("operation", oid, op, db)
            run["pendingCommandId"] = oid
            self.store.put("run", rid, run, db)
            return {"operationId": oid, "runId": rid, "status": "accepted"}

        result, new = self.store.idempotent(
            principal, "POST /runs/" + rid + "/commands", key, payload, accepted
        )
        if new:
            root = self.directory(rid)
            secret = (root / "owner.key").read_bytes()
            cmd = {"operationId": result["operationId"], "kind": payload["kind"]}
            if payload["kind"] in ("pause", "resume", "set_parameter"):
                cmd["expectedStateVersion"] = payload["expectedStateVersion"]
            if payload["kind"] == "set_parameter":
                operation = self.store.get("operation", result["operationId"])
                cmd.update(parameters=operation["parameters"], principal=operation["principal"])
            cmd["signature"] = hmac.new(
                secret, canonical(cmd).encode(), hashlib.sha256
            ).hexdigest()
            # Serialized with reconciliation: a concurrent read may already have
            # settled this request, and delegation must never reopen that outcome.
            with self.store.lock:
                op = self.store.get("operation", result["operationId"])
                if (
                    op["status"] == "accepted"
                    and self.store.get("run", rid).get("pendingCommandId")
                    == op["operationId"]
                ):
                    current = self.store.get("run", rid)
                    if payload["kind"] not in ("stop", "cancel") and current["providerId"] in self.installed_providers:
                        try:
                            self._require_active_provider(current)
                        except Problem as error:
                            op.update(status="rejected", code=error.code)
                            self.store.put("operation", op["operationId"], op)
                            current.pop("pendingCommandId", None)
                            self.store.put("run", rid, current)
                            return result
                    atomic(root / "command.json", canonical(cmd).encode())
                    op["status"] = "delegated"
                    self.store.put("operation", op["operationId"], op)
        return result

    def input_request(self, rid, action, payload, session):
        with self.store.lock:
            run = self.read(rid)
            provider = self.installed_providers.get(run["providerId"])
            if provider is None or not hasattr(provider, "input_request") or (run.get("inputSurface") or {}).get("kind") != "normalized-driver":
                raise Problem("CAPABILITY_UNSUPPORTED", "This run has no admitted browser input surface.")
            if run["state"] != "running":
                raise Problem("STATE_CONFLICT", "Browser input requires the observed running state.", 409)
            self._require_active_provider(run)
            return provider.input_request(self.directory(rid), action, payload, session)

    def shutdown(self):
        # Native foreground shutdown requests only admitted, ownership-confirmed cancellation.
        for r in self.store.all("run"):
            run = self.read(r["runId"])
            if run["state"] in ("running", "paused", "preparing", "ready"):
                try:
                    self.command(
                        run["runId"],
                        "native-launcher",
                        uid("shutdown-"),
                        {"kind": "cancel", "expectedStateVersion": run["stateVersion"]},
                    )
                except (Problem, OSError):
                    pass
        shutdown_budget = max((min(90, max(3, getattr(provider, "shutdown_timeout_seconds", 45)))
                               for provider in self.installed_providers.values()), default=3)
        deadline = time.monotonic() + shutdown_budget
        while self.children and time.monotonic() < deadline:
            for rid in list(self.children):
                self.read(rid)
            time.sleep(0.05)
        # Installed long-lived services close only after their original tasks
        # have settled; they do not gain process-signalling authority here.
        for provider in self.installed_providers.values():
            close_owner = getattr(provider, "close_backend_owner", None)
            if callable(close_owner):
                close_owner()
