from __future__ import annotations

from copy import deepcopy
import hashlib
import itertools
import json
import math
import threading
from typing import Callable


class CampaignError(ValueError):
    def __init__(self, code):
        self.code = code
        super().__init__(code)


def _identity(value):
    try:
        return "sha256:" + hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()).hexdigest()
    except (ValueError, TypeError, RecursionError):
        raise CampaignError("INVALID_CAMPAIGN") from None


class CampaignPlanner:
    def __init__(self, *, max_children=64, max_axes=8, max_axis_values=16, max_concurrency=1, allowed_parameters=None):
        self.max_children = max_children
        self.max_axes = max_axes
        self.max_axis_values = max_axis_values
        self.max_concurrency = max_concurrency
        self.allowed_parameters = set(allowed_parameters) if allowed_parameters is not None else {"gain", "target", "initial", "duration", "timestep"}

    def preview(self, base_snapshot: dict, matrix: dict, *, budget: dict, concurrency: int = 1, duration_seconds: float = 1.0, stop_policy: str = "continue") -> dict:
        if not isinstance(base_snapshot, dict) or not isinstance(base_snapshot.get("snapshotId"), str) or not base_snapshot["snapshotId"]:
            raise CampaignError("BASE_SNAPSHOT_REQUIRED")
        if not isinstance(matrix, dict) or not matrix or len(matrix) > self.max_axes or matrix.keys() - self.allowed_parameters:
            raise CampaignError("INVALID_MATRIX")
        if not isinstance(budget, dict) or budget.keys() - {"maxRuns", "maxTotalSeconds"}:
            raise CampaignError("INVALID_BUDGET")
        if not isinstance(concurrency, int) or isinstance(concurrency, bool) or not 1 <= concurrency <= self.max_concurrency:
            raise CampaignError("CAMPAIGN_CONCURRENCY")
        max_runs = budget.get("maxRuns")
        if not isinstance(max_runs, int) or isinstance(max_runs, bool) or not 1 <= max_runs <= self.max_children:
            raise CampaignError("CAMPAIGN_BUDGET")
        cardinality = 1
        axes = sorted(matrix)
        for axis in axes:
            values = matrix[axis]
            if not isinstance(values, list) or not 1 <= len(values) <= self.max_axis_values:
                raise CampaignError("MATRIX_LIMIT")
            if any(not isinstance(v, (int, float)) or isinstance(v, bool) or not math.isfinite(v) for v in values):
                raise CampaignError("INVALID_PARAMETER")
            if len(set(values)) != len(values):
                raise CampaignError("DUPLICATE_MATRIX_VALUE")
            cardinality *= len(values)
            if cardinality > min(self.max_children, max_runs):
                raise CampaignError("CAMPAIGN_BUDGET")
        if not isinstance(duration_seconds, (int, float)) or isinstance(duration_seconds, bool) or not math.isfinite(duration_seconds) or duration_seconds <= 0:
            raise CampaignError("INVALID_DURATION")
        total = cardinality * duration_seconds
        time_budget = budget.get("maxTotalSeconds", total)
        if not isinstance(time_budget, (int, float)) or isinstance(time_budget, bool) or not math.isfinite(time_budget) or time_budget <= 0 or total > time_budget:
            raise CampaignError("CAMPAIGN_BUDGET")
        if stop_policy not in {"continue", "stop_on_failure"}:
            raise CampaignError("INVALID_STOP_POLICY")
        base_digest = _identity(base_snapshot)
        children = []
        for i, combination in enumerate(itertools.product(*(matrix[a] for a in axes))):
            params = dict(zip(axes, combination))
            children.append({"index": i, "childKey": _identity({"baseDigest": base_digest, "index": i, "parameters": params}), "parameters": params, "state": "pending", "runId": None})
        return {"baseSnapshotId": base_snapshot["snapshotId"], "baseSnapshotDigest": base_digest, "baseSnapshot": deepcopy(base_snapshot), "matrix": deepcopy(matrix), "cardinality": cardinality, "concurrency": concurrency, "budget": {"maxRuns": max_runs, "maxTotalSeconds": time_budget}, "estimatedTotalSeconds": total, "stopPolicy": stop_policy, "children": children}


class CampaignState:
    """Transaction-friendly state machine; ambiguous starts remain blocked until reconciled.

    `persist` must durably commit the supplied deep copy or raise before the caller
    delegates work. A per-process lock guards concurrent API access; the integrating
    SQLite service must additionally enforce its own revision/transaction checks.
    """
    ACTIVE = {"dispatching", "running", "unknown"}
    TERMINAL = {"stopped", "failed", "cancelled", "rejected"}

    def __init__(self, record, persist=None):
        self.record = deepcopy(record)
        self._persist = persist
        self._lock = threading.RLock()

    @classmethod
    def create(cls, campaign_id: str, preview: dict, *, persist: Callable | None = None):
        obj = cls({**deepcopy(preview), "campaignId": campaign_id, "revision": 1, "status": "pending", "cancelRequested": False}, persist)
        obj._save()
        return obj

    @classmethod
    def from_record(cls, record: dict, *, persist: Callable | None = None):
        return cls(record, persist)

    def _save(self):
        if self._persist:
            self._persist(deepcopy(self.record))

    def _commit(self, change):
        before = deepcopy(self.record)
        try:
            change()
            self.record["revision"] += 1
            self._save()
        except Exception:
            self.record = before
            raise

    def _child(self, key):
        for child in self.record["children"]:
            if child["childKey"] == key:
                return child
        raise CampaignError("CHILD_NOT_FOUND")

    def claim_next(self):
        with self._lock:
            if self.record["cancelRequested"]:
                return None
            if sum(c["state"] in self.ACTIVE for c in self.record["children"]) >= self.record["concurrency"]:
                return None
            child = next((c for c in self.record["children"] if c["state"] == "pending"), None)
            if child is None:
                return None
            def change():
                child["state"] = "dispatching"
                child["operationKey"] = f"{self.record['campaignId']}:{child['childKey']}"
                self.record["status"] = "running"
            self._commit(change)
            return deepcopy(child)

    def mark_started(self, key, run_id):
        with self._lock:
            child = self._child(key)
            if child["runId"] is not None:
                if child["runId"] != run_id:
                    raise CampaignError("CHILD_RUN_CONFLICT")
                return
            if child["state"] not in {"dispatching", "unknown"} or not isinstance(run_id, str) or not run_id:
                raise CampaignError("CHILD_STATE_CONFLICT")
            self._commit(lambda: child.update(state="running", runId=run_id))

    def mark_unknown(self, key, reason="START_ACKNOWLEDGEMENT_LOST"):
        with self._lock:
            child = self._child(key)
            if child["state"] not in self.ACTIVE:
                raise CampaignError("CHILD_STATE_CONFLICT")
            self._commit(lambda: child.update(state="unknown", reason=reason))

    def mark_terminal(self, key, state):
        with self._lock:
            child = self._child(key)
            if state not in self.TERMINAL or child["state"] not in self.ACTIVE | self.TERMINAL:
                raise CampaignError("CHILD_STATE_CONFLICT")
            if child["state"] in self.TERMINAL:
                if child["state"] != state: raise CampaignError("CHILD_STATE_CONFLICT")
                return
            def change():
                child["state"] = state
                if state in {"failed", "rejected"} and self.record["stopPolicy"] == "stop_on_failure":
                    for other in self.record["children"]:
                        if other["state"] == "pending": other["state"] = "cancelled"
                if all(c["state"] in self.TERMINAL for c in self.record["children"]):
                    self.record["status"] = "cancelled" if self.record["cancelRequested"] else "complete"
            self._commit(change)

    def recover(self):
        with self._lock:
            affected = [c for c in self.record["children"] if c["state"] == "dispatching"]
            if affected:
                def change():
                    for c in affected: c.update(state="unknown", reason="RECONCILIATION_REQUIRED")
                self._commit(change)
            return deepcopy(self.record)

    def cancel(self, *, cancel_active=False):
        with self._lock:
            active = [c["runId"] for c in self.record["children"] if c["state"] in self.ACTIVE and c["runId"]]
            def change():
                self.record["cancelRequested"] = True
                for child in self.record["children"]:
                    if child["state"] == "pending": child["state"] = "cancelled"
                self.record["status"] = "cancelling" if any(c["state"] in self.ACTIVE for c in self.record["children"]) else "cancelled"
            self._commit(change)
            return {"campaignId": self.record["campaignId"], "activeRunIds": active if cancel_active else [], "activeCancellationRequested": cancel_active, "status": self.record["status"]}
