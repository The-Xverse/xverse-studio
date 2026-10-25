from __future__ import annotations
import hashlib
import hmac
import json
import os
from pathlib import Path
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
    REFERENCE,
    descriptors,
    admit_descriptor,
)
from xverse_studio.xdl import XDLRejected, reference_configuration
from xverse_studio.evidence.reader import read_journal
from xverse_studio.deployments import compile_selection
from xverse_studio.profiles import ProfileRegistry

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


class Runs:
    def __init__(self, store, projects, adapter):
        self.store, self.projects, self.adapter = store, projects, adapter
        self.children = {}

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
        profile_locks = ProfileRegistry(self.adapter).validate_project(p)
        documents = self.projects.sources(p)
        project_documents = documents
        compiled = self.compilation(documents, selection)
        refs = compiled["selection"]
        if compiled["valid"]:
            documents = compiled["contributingDocuments"]
        diagnostics = list(compiled["diagnostics"])
        configuration = None
        provider = next(
            value
            for value in descriptors()
            if value["providerId"] == "studio.reference"
        )
        try:
            if not provider.get("available") or not provider.get("hostCompatible"):
                raise XDLRejected(
                    "The selected provider has no admitted native operation on this host.",
                    "PROVIDER_UNAVAILABLE",
                )
            admit_descriptor(provider)
            if not compiled["valid"]:
                raise XDLRejected(
                    "Correct authoritative XDL diagnostics before executing.",
                    "MODEL_INVALID",
                )
            configuration = reference_configuration(documents, compiled)
            if selection.get("providerId", "studio.reference") != "studio.reference":
                raise XDLRejected(
                    "This provider has no admitted execution path on this host.",
                    "PROVIDER_UNAVAILABLE",
                )
        except XDLRejected as e:
            diagnostics.append(
                {
                    "code": e.code,
                    "severity": "error",
                    "message": str(e),
                    "remediation": "Select the owned reference blueprint or install an independently admitted provider.",
                }
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
            "providerId": "studio.reference",
            "providerIdentity": provider,
            "capabilityDigest": capability_digest(),
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
            "status": "ready" if ready else "blocked",
            "planDigest": compiled.get("planDigest"),
            "semanticDigest": compiled.get("semanticDigest"),
            "capabilityDigest": capability_digest(),
            "expiresAt": time.time() + 60,
            "diagnostics": diagnostics,
            "dimensions": {
                "model": "valid" if compiled["valid"] else "invalid",
                "target": "ready" if ready else "blocked",
                "ownership": "available",
                "evidenceScope": "owned_reference",
            },
            "limits": REFERENCE["limits"],
            "selection": refs,
            "contributingDocuments": list(documents),
        }
        with self.store.tx() as db:
            self.store.put("snapshot", snapid, snapshot, db)
            self.store.put("preflight", pfid, pf, db)
        atomic(
            self.store.root / "snapshots" / snapid / "snapshot.json",
            canonical(snapshot).encode(),
        )
        return pf

    def start(self, principal, key, payload, *, allow_frozen=False):
        def accepted(db):
            pf = self.store.get("preflight", payload["preflightId"], db)
            snap = self.store.get("snapshot", payload["snapshotId"], db)
            frozen = (
                self.store.root / "snapshots" / snap["snapshotId"] / "snapshot.json"
            )
            if (
                digest({k: v for k, v in snap.items() if k != "snapshotDigest"})
                != snap.get("snapshotDigest")
                or not frozen.is_file()
                or frozen.read_bytes() != canonical(snap).encode()
            ):
                raise Problem(
                    "SNAPSHOT_INTEGRITY",
                    "The frozen snapshot identity or immutable bytes cannot be verified.",
                )
            if pf["snapshotId"] != snap["snapshotId"] or pf["status"] != "ready":
                raise Problem(
                    "ADMISSION_REJECTED",
                    "Only a ready preflight for these exact inputs can start.",
                )
            if (
                pf["expiresAt"] <= time.time()
                or pf["capabilityDigest"] != capability_digest()
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
            config = reference_configuration(snap["documents"], compiled)
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
                "cleanup": "not_started",
                "evidence": "pending",
                "evaluation": "not_started",
                "verdict": None,
                "evidenceScope": "owned_reference",
                "providerId": "studio.reference",
                "createdAt": time.time(),
                "planDigest": snap["planDigest"],
                "semanticDigest": snap["semanticDigest"],
                "capabilities": ["stop", "cancel"],
            }
            operation = {
                "operationId": oid,
                "status": "accepted",
                "runId": rid,
                "kind": "start",
            }
            self.store.put("run", rid, run, db)
            self.store.put("operation", oid, operation, db)
            return {"runId": rid, "operationId": oid, "stateVersion": 0}

        for old in self.store.all("run"):
            if old["state"] in ACTIVE:
                self.read(old["runId"])
        result, new = self.store.idempotent(
            principal, "POST /runs", key, payload, accepted
        )
        if new:
            self._dispatch(result["runId"])
        return result

    def _dispatch(self, rid):
        run = self.store.get("run", rid)
        snap = self.store.get("snapshot", run["snapshotId"])
        root = self.directory(rid)
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
                }
            ).encode(),
        )
        launch_argv = [
            sys.executable,
            "-I",
            "-m",
            "xverse_studio.providers.worker",
            str(root),
        ]
        run.update(
            ownerDigest=digest(secret),
            state="preparing",
            launchArgvDigest=digest(launch_argv),
        )
        self.store.put("run", rid, run)
        op = self.store.get("operation", run["operationId"])
        op["status"] = "delegated"
        self.store.put("operation", op["operationId"], op)
        try:
            kwargs = (
                {"start_new_session": True}
                if os.name != "nt"
                else {
                    "creationflags": subprocess.CREATE_NEW_PROCESS_GROUP
                    | subprocess.DETACHED_PROCESS
                }
            )
            worker_tmp = root / "tmp"
            worker_tmp.mkdir(exist_ok=True)
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
        except OSError:
            run.update(
                state="failed",
                cleanup="unknown",
                evidence="unavailable",
                reason="LAUNCH_FAILED",
            )
            op.update(status="failed", code="LAUNCH_FAILED")
            self.store.put("run", rid, run)
            self.store.put("operation", op["operationId"], op)
            return
        try:
            run.update(
                pid=process.pid, createTime=psutil.Process(process.pid).create_time()
            )
        except psutil.Error:
            run.update(
                state="unknown", cleanup="unknown", reason="LAUNCH_ACKNOWLEDGEMENT_LOST"
            )
            op["status"] = "unknown"
            self.store.put("operation", op["operationId"], op)
        self.store.put("run", rid, run)

    def read(self, rid):
        with self.store.lock:
            run = self.store.get("run", rid)
            root = self.directory(rid)
            statepath = root / "state.json"
            observed = None
            try:
                if statepath.exists():
                    observed = json.loads(statepath.read_text())
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
                if observed and observed["state"] not in ("stopped", "failed"):
                    process = psutil.Process(observed["pid"])
                    if (
                        abs(process.create_time() - observed["createTime"]) > 0.001
                        or not process.is_running()
                        or process.status() == psutil.STATUS_ZOMBIE
                    ):
                        observed = None
            except (OSError, ValueError, psutil.Error):
                observed = None
            if observed:
                run.update(
                    {
                        k: observed[k]
                        for k in (
                            "state",
                            "stateVersion",
                            "cleanup",
                            "evidence",
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
                op["status"] = "completed"
                op["result"] = {
                    "effectivePlanDigest": observed.get("effectivePlanDigest")
                }
                self.store.put("operation", op["operationId"], op)
                for oid, result in observed.get("commandResults", {}).items():
                    try:
                        op = self.store.get("operation", oid)
                        op.update(result)
                        self.store.put("operation", oid, op)
                    except Problem:
                        pass
            elif run["state"] in ACTIVE:
                if (
                    run.get("state") == "preparing"
                    and time.time() - run["createdAt"] < 5
                ):
                    return run
                run.update(
                    state="unknown",
                    cleanup="unknown",
                    evidence="partial",
                    reason="OWNERSHIP_UNKNOWN",
                )
                op = self.store.get("operation", run["operationId"])
                if op["status"] not in ("completed", "failed"):
                    op["status"] = "unknown"
                    self.store.put("operation", op["operationId"], op)
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
            self.store.put("run", rid, run)
            if rid in self.children and self.children[rid].poll() is not None:
                self.children.pop(rid)
            return run

    def command(self, rid, principal, key, payload):
        # Reconciliation precedes state/authority enforcement; retries still resolve before a new mutation.
        self.read(rid)

        def accepted(db):
            run = self.store.get("run", rid, db)
            if payload.get("parameters"):
                raise Problem(
                    "COMMAND_PARAMETERS_UNSUPPORTED",
                    "Stop and cancel accept no additional parameters.",
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
            if run["state"] not in ("running", "preparing", "ready", "paused"):
                raise Problem(
                    "STATE_CONFLICT",
                    "The current owned state does not permit this command.",
                    409,
                )
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
            self.store.put("operation", oid, op, db)
            return {"operationId": oid, "runId": rid, "status": "accepted"}

        result, new = self.store.idempotent(
            principal, "POST /runs/" + rid + "/commands", key, payload, accepted
        )
        if new:
            root = self.directory(rid)
            secret = (root / "owner.key").read_bytes()
            cmd = {"operationId": result["operationId"], "kind": payload["kind"]}
            cmd["signature"] = hmac.new(
                secret, canonical(cmd).encode(), hashlib.sha256
            ).hexdigest()
            atomic(root / "command.json", canonical(cmd).encode())
            op = self.store.get("operation", result["operationId"])
            op["status"] = "delegated"
            self.store.put("operation", op["operationId"], op)
        return result

    def shutdown(self):
        # Native foreground shutdown requests only admitted, ownership-confirmed cancellation.
        for r in self.store.all("run"):
            run = self.read(r["runId"])
            if run["state"] == "running":
                try:
                    self.command(
                        run["runId"],
                        "native-launcher",
                        uid("shutdown-"),
                        {"kind": "cancel", "expectedStateVersion": run["stateVersion"]},
                    )
                except (Problem, OSError):
                    pass
        deadline = time.monotonic() + 3
        while self.children and time.monotonic() < deadline:
            for rid in list(self.children):
                self.read(rid)
            time.sleep(0.05)
