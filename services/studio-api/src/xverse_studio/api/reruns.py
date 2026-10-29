"""Explicit fresh execution of verified owned snapshots; recorded replay remains read-only."""
from __future__ import annotations

from copy import deepcopy
import json
import shutil
import time

from fastapi import Request
from xverse_xdl import plan_matches_digest

from xverse_studio.api.models import Body
from xverse_studio.providers.registry import capability_digest, descriptors
from xverse_studio.profiles import ProfileRegistry
from xverse_studio.storage.core import Problem, atomic, canonical, contained, digest, uid
from xverse_studio.xdl import XDLRejected, reference_configuration


class RerunRequest(Body):
    pass


class Reruns:
    def __init__(self, store, projects, runs, adapter):
        self.store, self.projects, self.runs, self.adapter = store, projects, runs, adapter

    def verify_source(self, source_run_id, db):
        source = self.store.get("run", source_run_id, db)
        if source.get("providerId") != "studio.reference" or source.get("evidenceScope") != "owned_reference":
            raise Problem("RERUN_UNSUPPORTED", "This source has no admitted owned-reference rerun capability. Imported evidence and physical/live provider claims confer no execution authority.")
        try:
            snapshot = self.store.get("snapshot", source["snapshotId"], db)
            path = contained(self.store.root, self.store.root / "snapshots" / snapshot["snapshotId"] / "snapshot.json")
            if snapshot["snapshotId"] != source["snapshotId"] or snapshot.get("projectId") != source.get("projectId") or snapshot.get("revision") != source.get("revision") or path.is_symlink() or not path.is_file() or path.read_bytes() != canonical(snapshot).encode() or snapshot.get("snapshotDigest") != digest({k: v for k, v in snapshot.items() if k != "snapshotDigest"}):
                raise ValueError()
            plan = snapshot["plan"]
            if not plan_matches_digest(plan) or "sha256:" + plan["digest"]["value"] != snapshot["planDigest"] or snapshot["planDigest"] != source.get("planDigest") or snapshot["semanticDigest"] != source.get("semanticDigest"):
                raise ValueError()
            if snapshot.get("providerId") != source["providerId"]:
                raise ValueError()
        except (Problem, OSError, ValueError, KeyError, TypeError, AttributeError, RecursionError):
            raise Problem("SNAPSHOT_INTEGRITY", "The original frozen snapshot bytes, identity or source-run binding cannot be verified.") from None
        ProfileRegistry(self.adapter).validate_snapshot(snapshot)
        provider = next((provider for provider in descriptors() if provider["providerId"] == "studio.reference"), None)
        if not provider or not provider.get("available") or not provider.get("hostCompatible") or "start" not in provider.get("operations", []):
            raise Problem("PROVIDER_UNAVAILABLE", "The current host has no admitted executable reference provider for these frozen inputs.", 503)
        try:
            compiled = self.adapter.compile(snapshot["documents"], snapshot.get("selection"))
            if not compiled["valid"] or compiled["planDigest"] != snapshot["planDigest"] or compiled["semanticDigest"] != snapshot["semanticDigest"]:
                raise XDLRejected("The current authoritative compiler does not reproduce the original input/plan identity.")
            configuration = reference_configuration(snapshot["documents"], compiled)
            if digest(configuration) != digest(snapshot["configuration"]):
                raise XDLRejected("The current provider does not reproduce the original effective configuration.")
        except (XDLRejected, KeyError, TypeError, ValueError):
            raise Problem("RERUN_INPUT_INCOMPATIBLE", "The current admitted compiler/provider cannot execute these exact original frozen inputs without changing their semantics.") from None
        return source, snapshot, compiled, configuration, provider

    def create(self, source_run_id, principal, key):
        def accepted(db):
            source, original, compiled, configuration, provider = self.verify_source(source_run_id, db)
            operation_id, snapshot_id, preflight_id = uid("op-"), uid("snap-"), uid("pf-")
            now = time.time()
            snapshot = deepcopy(original)
            for field in ("snapshotDigest", "campaignId", "campaignChildKey"):
                snapshot.pop(field, None)
            snapshot.update(snapshotId=snapshot_id, parentSnapshotId=original["snapshotId"], sourceRunId=source_run_id,
                            sourceSnapshotDigest=original["snapshotDigest"], rerunOperationId=operation_id,
                            createdAt=now, compiler=compiled["compiler"], plan=compiled["plan"],
                            capabilityDigest=capability_digest(), configuration=configuration, providerIdentity=provider)
            snapshot["snapshotDigest"] = digest(snapshot)
            preflight = {"preflightId": preflight_id, "snapshotId": snapshot_id, "status": "ready", "planDigest": compiled["planDigest"],
                         "semanticDigest": compiled["semanticDigest"], "capabilityDigest": snapshot["capabilityDigest"],
                         "expiresAt": now + 60, "diagnostics": [], "selection": snapshot.get("selection", {}),
                         "dimensions": {"model": "valid", "target": "ready", "evidenceScope": "owned_reference"},
                         "limitations": ["Freshly admitted reference execution, separate from recorded observation replay. Completion alone is not an assertion verdict."]}
            operation = {"operationId": operation_id, "kind": "rerun", "status": "accepted", "sourceRunId": source_run_id,
                         "parentSnapshotId": original["snapshotId"], "snapshotId": snapshot_id, "createdAt": now,
                         "evidenceScope": "owned_reference", "message": "This operation creates a new run; its completion does not imply experiment completion or a passing assertion."}
            dispatch = {"operationId": operation_id, "sourceRunId": source_run_id, "sourceSnapshotId": original["snapshotId"],
                        "snapshotId": snapshot_id, "preflightId": preflight_id, "principal": principal,
                        "childStartKey": "rerun-child-" + operation_id, "createdAt": now}
            root = contained(self.store.root, self.store.root / "snapshots" / snapshot_id)
            if root.exists():
                raise Problem("IDENTITY_CONFLICT", "The newly allocated snapshot identity is already in use.", 409)
            self.store.on_rollback(db, lambda: shutil.rmtree(root) if root.exists() else None)
            atomic(root / "snapshot.json", canonical(snapshot).encode())
            self.store.put("snapshot", snapshot_id, snapshot, db)
            self.store.put("preflight", preflight_id, preflight, db)
            self.store.put("rerunDispatch", operation_id, dispatch, db)
            self.store.put("operation", operation_id, operation, db)
            return {"operationId": operation_id}
        result, created = self.store.idempotent(principal, "POST /runs/" + source_run_id + "/reruns", key, {}, accepted)
        if created:
            # No runtime effect occurs inside the outer SQLite transaction.
            self.dispatch(result["operationId"])
        return result

    def _child_mapping(self, dispatch, db):
        scope = dispatch["principal"] + ":POST /runs"
        row = db.execute("SELECT fingerprint,result FROM idempotency WHERE scope=? AND key=?", (scope, dispatch["childStartKey"])).fetchone()
        if row is None:
            return None
        expected = {"snapshotId": dispatch["snapshotId"], "preflightId": dispatch["preflightId"]}
        child = json.loads(row[1])
        if row[0] != digest(expected):
            raise Problem("RERUN_CHILD_IDENTITY_CONFLICT", "The recorded child operation fingerprint is incompatible.")
        run = self.store.get("run", child["runId"], db)
        operation = self.store.get("operation", child["operationId"], db)
        if run.get("snapshotId") != dispatch["snapshotId"] or run.get("operationId") != child["operationId"] or operation.get("runId") != run["runId"]:
            raise Problem("RERUN_CHILD_IDENTITY_CONFLICT", "The recorded child run/operation does not match this rerun request.")
        return {"runId": child["runId"], "startOperationId": child["operationId"]}

    def reconcile_operation(self, operation_id, *, after_restart=False):
        with self.store.tx() as db:
            operation = self.store.get("operation", operation_id, db)
            if operation.get("kind") != "rerun" or operation["status"] in {"completed", "failed", "rejected"}:
                return operation
            try:
                dispatch = self.store.get("rerunDispatch", operation_id, db)
                child = self._child_mapping(dispatch, db)
                if child:
                    operation.update(status="completed", result=child, runId=child["runId"], completedAt=time.time())
                    operation.pop("error", None)
                elif after_restart or time.time() - operation.get("delegatedAt", operation["createdAt"]) > 5:
                    operation.update(status="unknown", error={"code": "RERUN_DISPATCH_UNKNOWN", "message": "No acknowledged child start can be proven. The backend will not replay this request automatically.", "retryable": False})
            except (Problem, KeyError, TypeError, ValueError):
                operation.update(status="unknown", error={"code": "RERUN_DISPATCH_CONTEXT_UNAVAILABLE", "message": "The child ownership mapping cannot be verified; no start is replayed.", "retryable": False})
            self.store.put("operation", operation_id, operation, db)
            return operation

    def reconcile_pending(self):
        for operation in self.store.all("operation"):
            if operation.get("kind") == "rerun" and operation["status"] in {"accepted", "delegated", "unknown"}:
                self.reconcile_operation(operation["operationId"], after_restart=True)

    def dispatch(self, operation_id):
        dispatch = self.store.get("rerunDispatch", operation_id)
        operation = self.store.get("operation", operation_id)
        operation.update(status="delegated", delegatedAt=time.time())
        self.store.put("operation", operation_id, operation)
        try:
            self.runs.start(dispatch["principal"], dispatch["childStartKey"],
                            {"snapshotId": dispatch["snapshotId"], "preflightId": dispatch["preflightId"]}, allow_frozen=True)
        except Problem as error:
            # If durable child creation happened, retain it regardless of a lost acknowledgement.
            reconciled = self.reconcile_operation(operation_id, after_restart=True)
            if reconciled["status"] != "completed" and reconciled.get("error", {}).get("code") == "RERUN_DISPATCH_UNKNOWN":
                reconciled.update(status="rejected", error={"code": error.code, "message": error.message, "retryable": False})
                self.store.put("operation", operation_id, reconciled)
        except Exception:
            self.reconcile_operation(operation_id, after_restart=True)
        else:
            self.reconcile_operation(operation_id)


def install_reruns(app, store, projects, runs, adapter):
    service = Reruns(store, projects, runs, adapter)
    app.state.studio.reruns = service
    service.reconcile_pending()

    @app.post("/api/v1/runs/{runId}/reruns", status_code=202)
    def rerun(runId: str, body: RerunRequest, request: Request):
        return service.create(runId, request.state.principal, request.headers.get("idempotency-key"))
