"""M3/M4 facades. Every effect uses admitted server-owned services and identities."""
from __future__ import annotations

import json
from collections import OrderedDict
import threading
import time

from fastapi import Request, Response
from pydantic import Field

from xverse_studio.api.models import (Annotation, AnnotationUpdate, Body, Campaign, Evaluation, Reservation, Renewal, Retention, RetentionApply)
from xverse_studio.annotations import AnnotationError, create_annotation, revise_annotation
from xverse_studio.assertions import EvaluationError, UNIT_DEFINITIONS, aggregate_verdict, evaluate, snapshot_definitions
from xverse_studio.campaigns import CampaignError, CampaignPlanner, CampaignState
from xverse_studio.assertions.dependencies import definition_order, metric_references
from xverse_studio.assertions.evaluator import evaluator_identity
from xverse_studio.assertions.snapshot import definition_schema_digest
from xverse_studio.comparison import ComparisonError, compare_runs, recorded_input
from xverse_studio.evidence.reader import read_journal
from xverse_studio.lab import LabError
from xverse_studio.lab.assets import inventory_observation
from xverse_studio.lab.bindings import resolve_physical_bindings
from xverse_studio.lab.authority import LabAuthority
from xverse_studio.lab.configuration import LabHostConfiguration
from xverse_studio.lab.operations import LabOperations
from xverse_studio.lab.probes import LabProbes
from xverse_studio.api.models import ProbeRequest
from xverse_studio.storage.core import Problem, atomic, canonical, digest, uid
from xverse_studio.xdl import XDLRejected, reference_configuration
from xverse_studio.xdl.edits import semantic_edits


def _page(items, cursor=None, limit=100):
    try:
        offset = int(cursor or "0")
    except ValueError:
        raise Problem("CURSOR_INVALID", "Supply a valid page cursor.") from None
    if offset < 0 or not 1 <= limit <= 200:
        raise Problem("LIMIT_EXCEEDED", "Choose a result page between one and 200 records.")
    return {"items": items[offset:offset + limit], "nextCursor": str(offset + limit) if offset + limit < len(items) else None}


def _expected(request):
    value = request.headers.get("if-match")
    if value is None:
        raise Problem("REVISION_REQUIRED", "Supply the current annotation revision in If-Match.", 428)
    try:
        return int(value.strip('"'))
    except ValueError:
        raise Problem("REVISION_INVALID", "If-Match must contain a numeric revision.") from None


def _failure(error):
    code = getattr(error, "code", str(error))
    statuses = {"FORBIDDEN": 403, "RESOURCE_BUSY": 409, "REVISION_REQUIRED": 428, "REVISION_CONFLICT": 412, "RETENTION_PLAN_STALE": 409, "ASSET_UNAVAILABLE": 503, "RESERVATION_NOT_FOUND": 404}
    raise Problem(code, "The operation was refused by its versioned admission, ownership, revision or resource contract.", statuses.get(code, 422)) from None


def _journal_projection(run, snapshot, records, integrity):
    """Project complete canonical reference samples, preserving explicit coverage."""
    coverage_records = [r["payload"].get("coverage") for r in records if r["type"] == "evidence.updated" and isinstance(r.get("payload", {}).get("coverage"), dict)]
    original = coverage_records[-1] if coverage_records else {}
    effective_matches = run.get("effectivePlanDigest") == snapshot.get("planDigest") and run.get("effectiveSemanticDigest") == snapshot.get("semanticDigest")
    complete = integrity == "valid" and original.get("complete") is True and run.get("state") == "stopped" and effective_matches
    groups = {}
    for record in records:
        if record["type"] != "observation.available":
            continue
        payload = record["payload"]
        source = record.get("sourceTime") or {}
        for field, value in payload.get("values", {}).items():
            key = payload.get("observerRef"), field
            unit = payload.get("units", {}).get(field)
            if key not in groups:
                groups[key] = {"evidenceId": run["runId"] + ":reference-journal", "digest": run.get("journalDigest"), "snapshotId": snapshot["snapshotId"], "observerRef": key[0], "field": field, "schema": {"type": "number", "unit": unit, "quantity": UNIT_DEFINITIONS.get(unit, {}).get("quantity"), "unitDefinitionDigest": UNIT_DEFINITIONS.get(unit, {}).get("definitionDigest")}, "clockDomainRef": source.get("clockDomain"), "integrity": integrity if effective_matches else "invalid", "coverage": {"verified": integrity == "valid" and bool(original), "complete": complete, "startTick": original.get("startTick"), "endTick": original.get("endTick"), "gaps": [] if complete else [{"reason": "Canonical coverage is incomplete or unavailable."}]}, "samples": []}
            groups[key]["samples"].append({"tick": source.get("tick"), "value": value, "sequence": int(record["sequence"])})
    return list(groups.values())


class Empty(Body):
    pass


class Compare(Body):
    leftRunId: str = Field(max_length=80)
    rightRunId: str = Field(max_length=80)


def install_advanced(app, store, projects, runs, adapter, *, lab_host=None, lab_probe_host=None):
    if lab_host is not None and not isinstance(lab_host, LabHostConfiguration):
        raise LabError('PROVIDER_CONFIG_INVALID')
    lab_service = lab_host.bind(store) if lab_host is not None else LabOperations(store, {}, {}, LabAuthority())
    lab = lab_service.registry  # Stock native launcher installs no provider or grants.
    app.state.studio.lab = lab
    app.state.studio.lab_reservations = lab_service
    probe_service = LabProbes(store, lab_probe_host)
    app.state.studio.lab_probes = probe_service
    for pending in store.all("evaluation"):
        if pending.get("status") in {"running", "not_started"}:
            pending.update(status="error", verdict=None, reasons=["EVALUATION_INTERRUPTED"], completedAt=time.time())
            store.put("evaluation", pending["evaluationId"], pending)
            operation = store.get("operation", pending["operationId"])
            operation.update(status="failed", code="EVALUATION_INTERRUPTED")
            store.put("operation", operation["operationId"], operation)
    for pending in store.find("operation", "kind", "campaign_cancel"):
        if pending.get("kind") == "campaign_cancel" and pending.get("status") in {"accepted", "delegated"}:
            pending.update(status="unknown", code="CAMPAIGN_CANCELLATION_INTERRUPTED")
            store.put("operation", pending["operationId"], pending)
    for pending in store.all("retention"):
        if pending.get("status") == "applying":
            pending.update(status="unknown", reason="RETENTION_APPLY_INTERRUPTED")
            store.put("retention", pending["planId"], pending)
            operation = store.get("operation", pending["operationId"])
            operation.update(status="unknown", code="RETENTION_APPLY_INTERRUPTED", result={"planId": pending["planId"], "outcomes": pending.get("outcomes", [])})
            store.put("operation", operation["operationId"], operation)
    manager_lock = threading.RLock()
    planner = CampaignPlanner(max_children=32, max_concurrency=1)
    definition_cache = OrderedDict()
    definition_cache_lock = threading.RLock()

    def assessment_summary(run):
        # Runs owns lifecycle/cleanup. This callback reads trusted immutable
        # assessment records only and must never recurse through Runs.read.
        try:
            snapshot = store.get("snapshot", run.get("snapshotId"))
        except Problem:
            return {}  # Owned performance/metadata fixtures may have no snapshot.
        snapshot_digest = snapshot.get("snapshotDigest")
        if snapshot_digest != digest({k: v for k, v in snapshot.items() if k != "snapshotDigest"}):
            return {"evaluation": "error", "verdict": "indeterminate", "evaluationSummary": {"diagnostics": ["SNAPSHOT_INTEGRITY_INVALID"], "definitions": []}}
        try:
            # Admission depends on exact frozen documents and the pinned validation
            # context, not a new snapshot UUID/time. Verify the whole snapshot above
            # before a cache hit; per-run evaluation records are never shared.
            admission_key = digest({"documents": snapshot.get("documents"), "compiler": adapter.identity,
                                    "evaluator": evaluator_identity(), "schemaDigest": definition_schema_digest()})
            with definition_cache_lock:
                if admission_key not in definition_cache:
                    definition_cache[admission_key] = snapshot_definitions(snapshot, adapter)
                    if len(definition_cache) > 64:
                        definition_cache.popitem(last=False)
                definition_cache.move_to_end(admission_key)
                admitted = definition_cache[admission_key]
        except EvaluationError as exc:
            return {"evaluation": "unavailable", "verdict": None, "evaluationSummary": {"diagnostics": [exc.code], "definitions": []}}
        required = [d for d in admitted if d["definition"]["kind"] == "assertion"]
        known = {d["definitionRef"]: d for d in admitted}
        latest = {}
        for row in store.find("evaluation", "runId", run.get("runId")):
            definition_ref = row.get("definitionRef")
            entry = known.get(definition_ref)
            if row.get("runId") != run.get("runId") or row.get("snapshotId") != snapshot["snapshotId"] or entry is None or row.get("definitionDigest") != entry["definitionDigest"]:
                continue
            previous = latest.get(definition_ref)
            if previous is None or (row.get("createdAt", 0), row["evaluationId"]) > (previous.get("createdAt", 0), previous["evaluationId"]):
                latest[definition_ref] = row
        definitions_summary, required_results = [], []
        counts = {"pass": 0, "fail": 0, "indeterminate": 0, "not_started": 0, "running": 0, "complete": 0, "error": 0, "unavailable": 0}
        for entry in required:
            row = latest.get(entry["definitionRef"])
            status = row.get("status", "not_started") if row else "not_started"
            verdict = row.get("verdict") if row and status == "complete" else None
            if verdict not in {"pass", "fail", "indeterminate", None}:
                verdict = "indeterminate"
            counts[status] = counts.get(status, 0) + 1
            if verdict is not None:
                counts[verdict] += 1
            required_results.append({"status": status, "verdict": verdict})
            definitions_summary.append({"definitionRef": entry["definitionRef"], "definitionDigest": entry["definitionDigest"], "evaluationId": row["evaluationId"] if row else None, "status": status, "verdict": verdict, "coverage": row.get("coverage") if row else None, "reasons": row.get("reasons", []) if row else []})
        any_attempt = bool(latest)
        statuses = [r["status"] for r in required_results]
        actual_jobs = [r.get("status", "not_started") for r in latest.values()]
        if "running" in actual_jobs:
            execution = "running"
        elif "error" in actual_jobs:
            execution = "error"
        elif "unavailable" in actual_jobs:
            execution = "unavailable"
        elif not required or any(status != "complete" for status in statuses):
            execution = "not_started"
        else:
            execution = "complete"
        verdict = aggregate_verdict(required_results) if any_attempt and required else None
        metric_jobs = []
        for entry in admitted:
            if entry["definition"]["kind"] != "metric":
                continue
            row = latest.get(entry["definitionRef"])
            metric_jobs.append({"definitionRef": entry["definitionRef"], "definitionDigest": entry["definitionDigest"], "evaluationId": row["evaluationId"] if row else None, "status": row.get("status", "not_started") if row else "not_started", "verdict": None, "coverage": row.get("coverage") if row else None, "value": row.get("value") if row else None, "unit": row.get("unit") if row else None})
        return {"evaluation": execution, "verdict": verdict, "evaluationSummary": {"requiredAssertions": len(required), "attemptedDefinitions": len(latest), "counts": counts, "definitions": definitions_summary, "metricDefinitions": len(metric_jobs), "metricJobs": metric_jobs, "diagnostics": []}}

    runs.assessment_summary = assessment_summary

    def definitions(run_id):
        run = runs.read(run_id)
        snapshot = store.get("snapshot", run["snapshotId"])
        try:
            return snapshot_definitions(snapshot, adapter)
        except EvaluationError as exc:
            _failure(exc)

    @app.get('/api/v1/assets/{assetId}/probe-options')
    def probe_options(assetId: str, request: Request):
        try:
            return probe_service.options(assetId, owner=request.state.principal)
        except LabError as exc:
            _failure(exc)

    @app.post('/api/v1/assets/{assetId}/probes', status_code=202)
    def probe_asset(assetId: str, body: ProbeRequest, request: Request):
        try:
            return probe_service.request(assetId, owner=request.state.principal,
                key=request.headers.get('idempotency-key'), expected_binding=body.expectedBindingDigest,
                scope=body.scope)
        except LabError as exc:
            if exc.code == 'PROBE_NOT_ADMITTED':
                raise Problem(exc.code, 'No reviewed observation installation is configured for this asset. Ask the host integrator to install the provider and grant explicit observation permission.', 503) from None
            if exc.code == 'PROBE_BINDING_CHANGED':
                raise Problem(exc.code, 'The observation binding changed. Refresh the options before submitting a new request.', 409) from None
            _failure(exc)

    @app.get("/api/v1/assets")
    def assets(cursor: str | None = None, limit: int = 100):
        # Reject invalid paging before contacting even explicitly registered inventory.
        _page([], cursor, limit)
        observed = inventory_observation(lab)
        return {**_page(observed["items"], cursor, limit), "scope": "explicitly_registered_inventory_observations",
                "physicalProviderStatus": "unavailable", "activeReady": False, "truncated": observed["truncated"],
                "complete": observed["complete"],
                "diagnostics": [{"code": "PHYSICAL_PROVIDER_NOT_ADMITTED"}, *observed["diagnostics"]]}

    @app.get("/api/v1/projects/{projectId}/deployment-variants/{documentId}/physical-bindings")
    def physical_bindings(projectId: str, documentId: str, revision: int | None = None):
        return resolve_physical_bindings(projects, adapter, lab, projectId, documentId, revision)

    @app.post("/api/v1/assets/{assetId}/reservations", status_code=202)
    def reserve(assetId: str, body: Reservation, request: Request):
        # Empty production inventory refuses here before any effect. A trusted
        # administrative integration must install durable lease backing before
        # registering a physical provider for API use.
        try:
            if lab_service.enabled:
                return lab_service.reserve(assetId, owner=request.state.principal,
                    key=request.headers.get('idempotency-key'), scope=body.scope, duration=body.durationSeconds)
            if not any(a["assetId"] == assetId for a in lab.inventory()):
                raise LabError("ASSET_UNAVAILABLE")
            raise LabError("PROVIDER_RESERVATION_NOT_ADMITTED")
        except LabError as exc:
            _failure(exc)

    @app.get("/api/v1/assets/{assetId}/reservation-options")
    def reservation_options(assetId: str, request: Request):
        try:
            return lab_service.options(assetId, owner=request.state.principal)
        except LabError as exc:
            _failure(exc)

    @app.get("/api/v1/reservations")
    def reservation_history(request: Request, cursor: str | None = None, limit: int = 100):
        _page([], cursor, limit)
        try:
            observed = lab_service.history(owner=request.state.principal)
            return {**observed, **_page(observed["items"], cursor, limit)}
        except LabError as exc:
            _failure(exc)

    @app.get("/api/v1/reservations/{reservationId}")
    def reservation(reservationId: str, request: Request):
        try:
            return lab_service.get(reservationId, owner=request.state.principal)
        except LabError as exc:
            _failure(exc)

    @app.post("/api/v1/reservations/{reservationId}/renewals", status_code=202)
    def renew(reservationId: str, body: Renewal, request: Request):
        try:
            if lab_service.enabled:
                return lab_service.renew(reservationId, owner=request.state.principal,
                    key=request.headers.get('idempotency-key'), fence=body.fencingIdentity, duration=body.durationSeconds)
            lab.get(reservationId, owner=request.state.principal)
            raise LabError("PROVIDER_RESERVATION_NOT_ADMITTED")
        except LabError as exc:
            _failure(exc)

    @app.delete("/api/v1/reservations/{reservationId}", status_code=202)
    def release(reservationId: str, request: Request):
        try:
            if lab_service.enabled:
                return lab_service.release(reservationId, owner=request.state.principal,
                    key=request.headers.get('idempotency-key'))
            lab.get(reservationId, owner=request.state.principal)
            raise LabError("PROVIDER_RESERVATION_NOT_ADMITTED")
        except LabError as exc:
            _failure(exc)

    @app.post('/api/v1/reservations/{reservationId}/reconciliations', status_code=202)
    def reconcile_reservation(reservationId: str, body: Empty, request: Request):
        try:
            if lab_service.enabled:
                return lab_service.reconcile(reservationId, owner=request.state.principal,
                    key=request.headers.get('idempotency-key'))
            lab.get(reservationId, owner=request.state.principal)
            raise LabError('PROVIDER_RESERVATION_NOT_ADMITTED')
        except LabError as exc:
            _failure(exc)

    @app.get("/api/v1/runs/{runId}/definitions")
    def run_definitions(runId: str):
        return {"items": definitions(runId), "nextCursor": None}

    @app.post("/api/v1/runs/{runId}/evaluations", status_code=202)
    def new_evaluation(runId: str, body: Evaluation, request: Request):
        key = request.headers.get("idempotency-key")
        route = "POST /runs/" + runId + "/evaluations"
        if not key or len(key) > 128:
            raise Problem("IDEMPOTENCY_REQUIRED", "Supply an Idempotency-Key of at most 128 characters.", 428)
        with store.tx() as db:
            prior = db.execute("SELECT fingerprint,result FROM idempotency WHERE scope=? AND key=?", (request.state.principal + ":" + route, key)).fetchone()
            if prior:
                if prior[0] != digest(body.model_dump()):
                    raise Problem("IDEMPOTENCY_CONFLICT", "This key already identifies a different evaluation request.", 409)
                result = json.loads(prior[1])
                return {**result, "status": store.get("evaluation", result["evaluationId"], db)["status"]}
        run = runs.read(runId)
        if body.snapshotId != run["snapshotId"]:
            raise Problem("SNAPSHOT_MISMATCH", "Evaluation must select the run's exact immutable snapshot.")
        snapshot = store.get("snapshot", run["snapshotId"])
        admitted = definitions(runId)
        selected = next((d for d in admitted if d["definitionRef"] == body.definitionRef), None)
        if selected is None:
            raise Problem("PROFILE_UNRESOLVED", "This frozen run has no admitted evaluation definition with that identity.")
        if selected["definitionDigest"] != body.definitionDigest:
            raise Problem("DEFINITION_DIGEST_MISMATCH", "The definition digest differs from the frozen run inputs.")
        evidence_id = runId + ":reference-journal"
        if body.evidenceRefs != [evidence_id]:
            raise Problem("EVIDENCE_SELECTION_INVALID", "Select this run's exact canonical reference journal.")
        # Read only authoritative bytes, never browser-supplied chart points.
        records, integrity = read_journal(runs.directory(runId), run)
        projected = _journal_projection(run, snapshot, records, integrity)
        try:
            definition_order(admitted, selected["definitionRef"])
        except EvaluationError as exc:
            _failure(exc)
        params = body.model_dump()
        def accept(db):
            evaluation_id, operation_id = uid("eval-"), uid("op-")
            row = {"evaluationId": evaluation_id, "runId": runId, "snapshotId": body.snapshotId, "definitionRef": body.definitionRef, "definitionDigest": body.definitionDigest, "definition": selected["definition"], "profileNamespace": selected["profileNamespace"], "schemaDigest": selected["schemaDigest"], "operationId": operation_id, "status": "running", "verdict": None, "evidenceRefs": body.evidenceRefs, "createdAt": time.time()}
            store.put("evaluation", evaluation_id, row, db)
            store.put("operation", operation_id, {"operationId": operation_id, "kind": "evaluation", "runId": runId, "evaluationId": evaluation_id, "status": "accepted"}, db)
            return {"evaluationId": evaluation_id, "operationId": operation_id}
        result, is_new = store.idempotent(request.state.principal, "POST /runs/" + runId + "/evaluations", request.headers.get("idempotency-key"), params, accept)
        if is_new:
            try:
                ordered = definition_order(admitted, selected["definitionRef"])
            except EvaluationError as exc:
                _failure(exc)
            metric_results, completed_rows = {}, {}
            for entry in ordered:
                definition_ref = entry["definitionRef"]
                is_parent = definition_ref == selected["definitionRef"]
                dependency_refs = metric_references(entry["definition"]["expression"])
                dependency_results = [{"evaluationId": completed_rows[ref["evaluationId"]]["evaluationId"], "definitionRef": ref["evaluationId"], "definitionDigest": ref["definitionDigest"], "resultDigest": digest(completed_rows[ref["evaluationId"]])} for ref in dependency_refs]
                if is_parent:
                    evaluation_id, operation_id = result["evaluationId"], result["operationId"]
                    row = store.get("evaluation", evaluation_id)
                else:
                    evaluation_id, operation_id = uid("eval-"), uid("op-")
                    row = {"evaluationId": evaluation_id, "runId": runId, "snapshotId": body.snapshotId, "definitionRef": definition_ref, "definitionDigest": entry["definitionDigest"], "definition": entry["definition"], "profileNamespace": entry["profileNamespace"], "schemaDigest": entry["schemaDigest"], "operationId": operation_id, "parentEvaluationId": result["evaluationId"], "status": "running", "verdict": None, "evidenceRefs": body.evidenceRefs, "createdAt": time.time()}
                    with store.tx() as db:
                        store.put("evaluation", evaluation_id, row, db)
                        store.put("operation", operation_id, {"operationId": operation_id, "kind": "evaluation", "runId": runId, "evaluationId": evaluation_id, "status": "accepted"}, db)
                row["dependencyResults"] = dependency_results
                row["inputEvidenceDigests"] = sorted({p["digest"] for p in projected if isinstance(p.get("digest"), str)})
                row["evaluatorIdentity"] = evaluator_identity()
                store.put("evaluation", evaluation_id, row)
                operation = store.get("operation", operation_id)
                operation["status"] = "delegated"
                store.put("operation", operation_id, operation)
                actual = evaluate(entry["definition"], projected, units=UNIT_DEFINITIONS, metrics=metric_results, profile_admitted=True, snapshot_id=body.snapshotId, budget_seconds=2)
                actual.pop("evaluationId", None)
                if integrity != "valid" or run.get("effectivePlanDigest") != snapshot.get("planDigest") or run.get("effectiveSemanticDigest") != snapshot.get("semanticDigest"):
                    actual.update(status="complete", verdict="indeterminate" if entry["definition"]["kind"] == "assertion" else None, value=None, coverage="invalid", reasons=["EVIDENCE_INVALID" if integrity != "valid" else "EFFECTIVE_INPUT_MISMATCH"])
                row.update(actual, completedAt=time.time(), evidenceReader="studio.reference.hash-chain-v1")
                store.put("evaluation", evaluation_id, row)
                operation.update(status="completed" if actual["status"] == "complete" else "failed", result={"evaluationId": evaluation_id, "status": actual["status"], "verdict": actual["verdict"]})
                store.put("operation", operation_id, operation)
                completed_rows[definition_ref] = row
                if entry["definition"]["kind"] == "metric":
                    metric_results[definition_ref] = {**actual, "evaluationId": definition_ref, "version": entry["definition"]["version"], "definitionDigest": entry["definitionDigest"], "kind": "metric", "dependencyRefs": [ref["evaluationId"] for ref in dependency_refs]}
        return {**result, "status": store.get("evaluation", result["evaluationId"])["status"]}

    @app.get("/api/v1/runs/{runId}/evaluations")
    def evaluations(runId: str, cursor: str | None = None, limit: int = 100):
        runs.read(runId)
        return _page([r for r in store.all("evaluation") if r["runId"] == runId], cursor, limit)

    @app.get("/api/v1/evaluations/{evaluationId}")
    def evaluation(evaluationId: str):
        return store.get("evaluation", evaluationId)

    def campaign_preview(body, db=None):
        snapshot = store.get("snapshot", body.snapshotId, db)
        runs.require_campaign_snapshot(snapshot, db)
        try:
            maximum_duration = max([snapshot["configuration"]["duration"], *body.matrix.get("duration", [])])
            return planner.preview(snapshot, body.matrix, budget=body.budget, concurrency=body.concurrency, duration_seconds=maximum_duration, stop_policy=body.stopPolicy)
        except (CampaignError, TypeError, ValueError) as exc:
            _failure(exc if isinstance(exc, CampaignError) else CampaignError("INVALID_CAMPAIGN"))

    def campaign_state(row):
        return CampaignState.from_record(row, persist=lambda record: store.put("campaign", record["campaignId"], record))

    def prepare_child(campaign, child):
        base = campaign["baseSnapshot"]
        docs = semantic_edits(base["documents"], [{"kind": "set_parameter", "parameterId": key, "value": value} for key, value in child["parameters"].items()])
        compiled = adapter.compile(docs)
        configuration = reference_configuration(docs, compiled)
        snapshot_id, preflight_id = uid("snap-"), uid("pf-")
        snapshot = {**base, "snapshotId": snapshot_id, "parentSnapshotId": base["snapshotId"], "documents": docs, "plan": compiled["plan"], "planDigest": compiled["planDigest"], "semanticDigest": compiled["semanticDigest"], "configuration": configuration, "createdAt": time.time(), "campaignId": campaign["campaignId"], "campaignChildKey": child["childKey"]}
        snapshot.pop("snapshotDigest", None)
        snapshot["snapshotDigest"] = digest(snapshot)
        preflight = {"preflightId": preflight_id, "snapshotId": snapshot_id, "status": "ready", "planDigest": snapshot["planDigest"], "capabilityDigest": base["capabilityDigest"], "expiresAt": time.time() + 60, "diagnostics": []}
        with store.tx() as db:
            store.put("snapshot", snapshot_id, snapshot, db)
            store.put("preflight", preflight_id, preflight, db)
        atomic(store.root / "snapshots" / snapshot_id / "snapshot.json", canonical(snapshot).encode())
        return {"snapshotId": snapshot_id, "preflightId": preflight_id}

    def campaign_tick():
        # Backend-owned lifespan polling advances campaigns independently of tabs.
        with manager_lock:
            for row in store.all("campaign")[:128]:
                state = campaign_state(row)
                for child in list(state.record["children"]):
                    if child["state"] == "unknown" and child.get("operationKey"):
                        # Reconcile durable start acknowledgement; never invoke
                        # start to discover whether an unknown dispatch happened.
                        with store.tx() as db:
                            found = db.execute("SELECT result FROM idempotency WHERE scope=? AND key=?", (state.record["principal"] + ":POST /runs", child["operationKey"])).fetchone()
                        if found:
                            acknowledged = json.loads(found[0])
                            state.mark_started(child["childKey"], acknowledged["runId"])
                            child = next(c for c in state.record["children"] if c["childKey"] == child["childKey"])
                    if child.get("runId") and child["state"] in {"running", "unknown"}:
                        observed = runs.read(child["runId"])
                        if observed["state"] in {"stopped", "failed"}:
                            state.mark_terminal(child["childKey"], observed["state"])
                operation = store.get("operation", state.record["operationId"])
                children = state.record["children"]
                if any(c["state"] == "unknown" for c in children):
                    operation.update(status="unknown", code="CHILD_OWNERSHIP_UNKNOWN")
                elif state.record["status"] in {"complete", "cancelled"}:
                    operation.update(status="completed", result={"campaignId": row["campaignId"], "status": state.record["status"], "childStates": [c["state"] for c in children]})
                elif any(c["state"] != "pending" for c in children):
                    operation["status"] = "delegated"
                store.put("operation", operation["operationId"], operation)
                child = state.claim_next()
                if child is None:
                    continue
                try:
                    payload = prepare_child(state.record, child)
                    result = runs.start(state.record["principal"], child["operationKey"], payload, allow_frozen=True)
                    state.mark_started(child["childKey"], result["runId"])
                except (Problem, XDLRejected, CampaignError) as exc:
                    current = next(c for c in state.record["children"] if c["childKey"] == child["childKey"])
                    current["reason"] = getattr(exc, "code", "CAMPAIGN_ADMISSION_REJECTED")
                    state.mark_terminal(child["childKey"], "rejected")
                except Exception:
                    state.mark_unknown(child["childKey"])

    # Never replay a dispatch whose process acknowledgement was lost on restart.
    for row in store.all("campaign"):
        campaign_state(row).recover()
    app.state.studio.campaign_tick = campaign_tick

    def campaign_public(row):
        """Inert presentation provenance; never advances or repairs a campaign."""
        base = row.get("baseSnapshot")
        try:
            if (not isinstance(base, dict) or base.get("snapshotId") != row["baseSnapshotId"]
                    or digest(base) != row["baseSnapshotDigest"]):
                raise Problem("SNAPSHOT_INTEGRITY", "The campaign base cannot be verified.")
            runs.verify_snapshot(base)
            provenance = {"status": "verified", **{key: base[key] for key in
                ["snapshotId", "snapshotDigest", "projectId", "revision", "selection", "providerId"]}}
        except (Problem, KeyError, TypeError):
            provenance = {"status": "unavailable", "reason": "SNAPSHOT_INTEGRITY"}
        return {**{k: v for k, v in row.items() if k not in {"baseSnapshot", "principal"}},
                "campaignVersion": "1.0", "baseInput": provenance}

    @app.post("/api/v1/campaigns/preview")
    def preview_campaign(body: Campaign):
        preview = campaign_preview(body)
        return campaign_public(preview)

    @app.post("/api/v1/campaigns", status_code=202)
    def new_campaign(body: Campaign, request: Request):
        def accepted(db):
            preview = campaign_preview(body, db)
            if len(store.all("campaign", db)) >= 128:
                raise Problem("LIMIT_EXCEEDED", "The retained campaign limit is 128; export and apply an admitted retention policy before scheduling more.", 413)
            campaign_id, operation_id = uid("campaign-"), uid("op-")
            state = CampaignState.create(campaign_id, preview)
            state.record.update(principal=request.state.principal, operationId=operation_id, createdAt=time.time())
            store.put("campaign", campaign_id, state.record, db)
            store.put("operation", operation_id, {"operationId": operation_id, "kind": "campaign", "campaignId": campaign_id, "status": "accepted"}, db)
            return {"campaignId": campaign_id, "operationId": operation_id}
        result, _ = store.idempotent(request.state.principal, "POST /campaigns", request.headers.get("idempotency-key"), body.model_dump(), accepted)
        return result

    @app.get("/api/v1/campaigns")
    def campaigns(cursor: str | None = None, limit: int = 100):
        page = _page(store.all("campaign"), cursor, limit)
        return {**page, "items": [campaign_public(row) for row in page["items"]]}

    @app.get("/api/v1/campaigns/{campaignId}")
    def campaign(campaignId: str):
        row = store.get("campaign", campaignId)
        return campaign_public(row)

    @app.post("/api/v1/campaigns/{campaignId}/cancel", status_code=202)
    def cancel_campaign(campaignId: str, body: Empty, request: Request):
        with manager_lock:
            def accepted(db):
                row = store.get("campaign", campaignId, db)
                if row["principal"] != request.state.principal:
                    raise Problem("FORBIDDEN", "This campaign is owned by another principal.", 403)
                state = CampaignState.from_record(row, persist=lambda r: store.put("campaign", campaignId, r, db))
                result = state.cancel(cancel_active=True)
                operation_id = uid("op-")
                store.put("operation", operation_id, {"operationId": operation_id, "kind": "campaign_cancel", "campaignId": campaignId, "status": "accepted"}, db)
                return {**result, "operationId": operation_id}
            result, is_new = store.idempotent(request.state.principal, "POST /campaigns/" + campaignId + "/cancel", request.headers.get("idempotency-key"), {}, accepted)
            if is_new:
                outcomes = []
                for rid in result["activeRunIds"]:
                    observed = runs.read(rid)
                    if observed["state"] in {"running", "preparing", "ready", "paused"}:
                        try:
                            command = runs.command(rid, request.state.principal, "campaign-cancel:" + campaignId + ":" + rid, {"kind": "cancel", "expectedStateVersion": observed["stateVersion"], "parameters": {}})
                            outcomes.append({"runId": rid, "status": "accepted", "operationId": command["operationId"]})
                        except Problem as exc:
                            outcomes.append({"runId": rid, "status": "rejected", "reason": exc.code})
                    else:
                        outcomes.append({"runId": rid, "status": "not_requested", "observedState": observed["state"]})
                operation = store.get("operation", result["operationId"])
                operation.update(status="completed", result={**result, "activeCancellationOutcomes": outcomes})
                store.put("operation", operation["operationId"], operation)
            operation = store.get("operation", result["operationId"])
            return {**result, **operation.get("result", {}), "operationStatus": operation["status"]}

    def comparable(run_id):
        run = runs.read(run_id)
        snapshot = store.get("snapshot", run["snapshotId"])
        runs.verify_snapshot(snapshot)
        records, integrity = read_journal(runs.directory(run_id), run)
        return recorded_input(run, snapshot, records, integrity, snapshot_integrity="valid")

    def recorded_comparison(left, right):
        try:
            return compare_runs(comparable(left), comparable(right))
        except ComparisonError as exc:
            _failure(exc)

    @app.post("/api/v1/comparisons")
    def comparison(body: Compare):
        return recorded_comparison(body.leftRunId, body.rightRunId)

    @app.get("/api/v1/runs/{runId}/comparison")
    def run_comparison(runId: str, baselineRunId: str):
        return recorded_comparison(baselineRunId, runId)

    @app.get("/api/v1/runs/{runId}/annotations")
    def annotations(runId: str, cursor: str | None = None, limit: int = 100):
        runs.read(runId)
        return _page([a for a in store.all("annotation") if a["runId"] == runId], cursor, limit)

    def annotation_refs(run_id, body):
        if set(body.evidenceRefs) - {run_id + ":reference-journal"}:
            raise Problem("EVIDENCE_SELECTION_INVALID", "Annotation evidence references must belong to this run.")
        if body.elementRefs or body.definitionRefs:
            run = runs.read(run_id)
            snapshot = store.get("snapshot", run["snapshotId"])
            if snapshot.get("snapshotDigest") != digest({key: value for key, value in snapshot.items() if key != "snapshotDigest"}):
                raise Problem("SNAPSHOT_INTEGRITY_INVALID", "Annotation subjects require the unchanged frozen run snapshot.")
            runs.verify_snapshot(snapshot)
            if body.elementRefs:
                graph = adapter.project(snapshot["documents"])
                known = {r["ref"] for r in graph.get("resources", []) + graph.get("elements", []) + graph.get("connections", [])}
                if set(body.elementRefs) - known:
                    raise Problem("MODEL_REFERENCE_UNRESOLVED", "Annotation model references must resolve in this run's frozen inputs.")
            if body.definitionRefs:
                try:
                    definitions = {d["definitionRef"]: d["definitionDigest"] for d in snapshot_definitions(snapshot, adapter)}
                except EvaluationError as exc:
                    _failure(exc)
                for ref in body.definitionRefs:
                    if set(ref) != {"definitionRef", "definitionDigest"} or definitions.get(ref.get("definitionRef")) != ref.get("definitionDigest"):
                        raise Problem("DEFINITION_REFERENCE_UNRESOLVED", "Annotation assertion/metric subjects must resolve with their exact definition digest in this run's frozen inputs.")

    @app.post("/api/v1/runs/{runId}/annotations", status_code=201)
    def annotate(runId: str, body: Annotation, request: Request, response: Response):
        runs.read(runId)
        annotation_refs(runId, body)
        try:
            row = create_annotation(runId, body.model_dump(), author=request.state.principal)
        except AnnotationError as exc:
            _failure(exc)
        store.put("annotation", row["annotationId"], row)
        response.headers["ETag"] = '"1"'
        return row

    @app.put("/api/v1/annotations/{annotationId}")
    def update_annotation(annotationId: str, body: AnnotationUpdate, request: Request, response: Response):
        expected = _expected(request)
        if body.revision != expected:
            raise Problem("REVISION_CONFLICT", "Body revision and If-Match must agree.", 412)
        existing = store.get("annotation", annotationId)
        annotation_refs(existing["runId"], body)
        with store.tx() as db:
            row = store.get("annotation", annotationId, db)
            try:
                updated = revise_annotation(row, body.model_dump(exclude={"revision"}), expected_revision=expected, author=request.state.principal)
            except AnnotationError as exc:
                _failure(exc)
            store.put("annotation", annotationId, updated, db)
        response.headers["ETag"] = f'"{updated["revision"]}"'
        return updated

    @app.delete("/api/v1/annotations/{annotationId}")
    def delete_annotation(annotationId: str, request: Request):
        expected = _expected(request)
        with store.tx() as db:
            row = store.get("annotation", annotationId, db)
            try:
                updated = revise_annotation(row, {}, expected_revision=expected, author=request.state.principal, delete=True)
            except AnnotationError as exc:
                _failure(exc)
            store.put("annotation", annotationId, updated, db)
        return updated

    from xverse_studio.retention.service import RetentionService
    from xverse_studio.retention.files import ProofLimit
    retention_service = RetentionService(store, projects, runs)
    app.state.studio.retention = retention_service

    def retention_error(exc):
        if isinstance(exc, ProofLimit) or str(exc) == "RETENTION_DEPENDENCY_LIMIT":
            raise Problem("LIMIT_EXCEEDED", "Retention proof exceeds its advertised bounded scan. Reduce the selected scope or resolve retained dependencies before retrying.", 413) from None
        _failure(exc)

    @app.post("/api/v1/retention/plans")
    def retention(body: Retention):
        try:
            return retention_service.plan(body.model_dump())
        except (ValueError, ProofLimit) as exc:
            retention_error(exc)

    @app.get("/api/v1/retention/plans/{planId}")
    def retention_plan(planId: str):
        return store.get("retention", planId)

    @app.post("/api/v1/retention/plans/{planId}/apply", status_code=202)
    def apply_retention(planId: str, body: RetentionApply, request: Request):
        try:
            return retention_service.apply(planId, body.fingerprint, request.state.principal, request.headers.get("idempotency-key"))
        except (ValueError, ProofLimit) as exc:
            retention_error(exc)
