"""Dependency-aware retention planning. Filesystem apply belongs to the API owner."""
from copy import deepcopy
import hashlib
import json
import time
import uuid

ACTIVE = {"requested", "preparing", "ready", "running", "paused", "stopping", "reconciling", "unknown"}


def state_fingerprint(state: dict) -> str:
    return "sha256:" + hashlib.sha256(json.dumps(state, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()).hexdigest()


def plan_retention(run_ids: list[str], state: dict, *, ttl_seconds=60) -> dict:
    if not isinstance(run_ids, list) or not 0 < len(run_ids) <= 128 or len(set(run_ids)) != len(run_ids) or any(not isinstance(v, str) for v in run_ids):
        raise ValueError("RETENTION_SELECTION_INVALID")
    runs = {r["runId"]: r for r in state.get("runs", [])}
    planned, protected = [], []
    for rid in run_ids:
        if rid not in runs:
            raise ValueError("RETENTION_RUN_NOT_FOUND")
        reasons = []
        if runs[rid].get("state") in ACTIVE:
            reasons.append("ACTIVE_RUN_PROTECTED")
        for evaluation in state.get("evaluations", []):
            if evaluation.get("runId") == rid:
                reasons.append("EVALUATION_DEPENDS_ON_EVIDENCE")
        for annotation in state.get("annotations", []):
            if annotation.get("runId") == rid and not annotation.get("deleted"):
                reasons.append("ANNOTATION_DEPENDS_ON_EVIDENCE")
        for campaign in state.get("campaigns", []):
            if any(c.get("runId") == rid for c in campaign.get("children", [])):
                reasons.append("CAMPAIGN_DEPENDS_ON_RUN")
        if reasons:
            protected.append({"runId": rid, "reasons": list(dict.fromkeys(reasons))})
        else:
            planned.append({"runId": rid, "scope": "owned_run_files", "snapshotProtected": True})
    return {"planId": "ret-" + str(uuid.uuid4()), "fingerprint": state_fingerprint(state), "runIds": deepcopy(run_ids), "removals": planned, "protected": protected, "expiresAt": time.time() + min(300, max(1, ttl_seconds)), "status": "planned"}


def check_plan(plan, state, fingerprint):
    if fingerprint != plan["fingerprint"] or state_fingerprint(state) != plan["fingerprint"] or plan["expiresAt"] <= time.time():
        raise ValueError("RETENTION_PLAN_STALE")
    fresh = plan_retention(plan["runIds"], state)
    if fresh["removals"] != plan["removals"] or fresh["protected"] != plan["protected"]:
        raise ValueError("RETENTION_PLAN_STALE")
    return deepcopy(plan["removals"])
