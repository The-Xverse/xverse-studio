"""Managed, explicit retention with bounded proofs and recoverable project retirement."""

from copy import deepcopy
import json
from pathlib import Path
import shutil
import sqlite3
import time

from xverse_studio.storage.core import Problem, canonical, digest
from xverse_studio.retention import _selection, plan_retention, check_plan
from .files import (
    ProofBudget,
    ProofLimit,
    inspect_tree,
    managed_path,
    read_bounded,
    MAX_DEPENDENCY_RECORDS,
)


class RetentionService:
    def __init__(self, store, projects, runs):
        self.store, self.projects, self.runs = store, projects, runs
        self.recoveryProblems = []
        self.recover_stages()

    def _all(self, kind, db, budget, *, suffix="", parameters=()):
        result = []
        # Reserve encoded size before SQLite/Python materializes a record body.
        for identifier, size in db.execute(
            "SELECT id,length(CAST(body AS BLOB)) FROM records WHERE kind=?"
            + suffix
            + " ORDER BY rowid DESC",
            (kind, *parameters),
        ):
            if len(result) >= MAX_DEPENDENCY_RECORDS:
                raise ProofLimit("RETENTION_PROOF_LIMIT")
            budget.record()
            budget.read(size)
            raw = db.execute(
                "SELECT body FROM records WHERE kind=? AND id=?", (kind, identifier)
            ).fetchone()[0]
            try:
                result.append(json.loads(raw))
            except (ValueError, TypeError):
                raise ValueError("RETENTION_DEPENDENCIES_UNRESOLVED") from None
        return result

    def _source(self, path, budget, *, limit=64 * 1024 * 1024):
        return read_bounded(self.store.root, path, budget, limit=limit)

    def _project_path(self, pid):
        return managed_path(self.store.root, self.store.root / "projects" / pid)

    def _stage_path(self, tombstone):
        # Only server-generated relative quarantine identities are accepted.
        relative = tombstone.get("quarantineRef", "")
        if (
            not isinstance(relative, str)
            or not relative.startswith("retention-staging/")
            or len(Path(relative).parts) != 3
        ):
            raise ValueError("UNSAFE_RETAINED_PATH")
        for part in Path(relative).parts[1:]:
            _selection([part])
        return managed_path(self.store.root, self.store.root / relative)

    def state(self, selection, db=None):
        if db is None:
            with self.store.tx() as connection:
                return self.state(selection, connection)
        budget = ProofBudget()
        mapping = {
            "runs": "run",
            "evaluations": "evaluation",
            "annotations": "annotation",
            "campaigns": "campaign",
        }
        extended = bool(selection.get("projectIds") or selection.get("artifactIds"))
        if extended:
            mapping.update(
                projects="project",
                snapshots="snapshot",
                artifacts="catalogArtifact",
                importedEvidence="importedEvidence",
            )
        state = {name: self._all(kind, db, budget) for name, kind in mapping.items()}
        if extended:
            state["retentionStages"] = self._all(
                "retentionProjectStage",
                db,
                budget,
                suffix=" AND json_extract(body,'$.phase') IN ('accepted','quarantined','unknown')",
            )
            selected_tombstones = [
                "project:" + pid for pid in selection.get("projectIds", [])
            ]
            conditions = []
            parameters = []
            if selected_tombstones:
                conditions.append(
                    "id IN (" + ",".join("?" for _ in selected_tombstones) + ")"
                )
                parameters.extend(selected_tombstones)
            if selection.get("artifactIds"):
                conditions.append(
                    "(json_extract(body,'$.kind')='project' AND json_extract(body,'$.remainingFiles')=1)"
                )
            state["retentionTombstones"] = (
                self._all(
                    "retentionTombstone",
                    db,
                    budget,
                    suffix=" AND (" + " OR ".join(conditions) + ")",
                    parameters=parameters,
                )
                if conditions
                else []
            )
        state["filesystem"] = {}
        state["dependencyScanProblems"] = []
        if selection.get("artifactIds") and (
            state.get("retentionStages")
            or any(
                t.get("remainingFiles") for t in state.get("retentionTombstones", [])
            )
        ):
            state["dependencyScanProblems"].append(
                {
                    "kind": "retention",
                    "id": None,
                    "code": "RETAINED_RECOVERY_INPUTS_UNRESOLVED",
                }
            )
        try:
            for rid in selection.get("runIds", []):
                state["filesystem"]["run:" + rid] = inspect_tree(
                    self.store.root, self.runs.directory(rid), budget
                )
            targets = set(selection.get("projectIds", []))
            for project in state.get("projects", []):
                pid = project["projectId"]
                if pid in targets:
                    state["filesystem"]["project:" + pid] = inspect_tree(
                        self.store.root, self._project_path(pid), budget
                    )
                if selection.get("artifactIds"):
                    try:
                        for document in project.get("documents", {}).values():
                            path = (
                                self.projects._dir(pid, project["revision"])
                                / document["path"]
                            )
                            raw = self._source(path, budget, limit=1024 * 1024)
                            if digest(raw) != document.get("digest"):
                                raise ValueError()
                            document["content"] = raw.decode()
                        for name, expected_content in project.get(
                            "supportingFiles", {}
                        ).items():
                            raw = self._source(
                                self.projects._dir(pid, project["revision"]) / name,
                                budget,
                                limit=1024 * 1024,
                            )
                            if raw != expected_content.encode():
                                raise ValueError()
                        validation = self.projects.adapter.validate(
                            {
                                document["path"]: document["content"]
                                for document in project["documents"].values()
                            }
                        )
                        if not validation["valid"]:
                            raise ValueError()
                        # Unindexed paths cannot silently conceal dependencies.
                        revision = self.projects._dir(pid, project["revision"])
                        proof = inspect_tree(
                            self.store.root, revision, budget, collect_names=True
                        )
                        expected = {
                            "project.studio.json",
                            *[d["path"] for d in project["documents"].values()],
                            *project.get("supportingFiles", {}),
                        }
                        actual = set(proof.pop("fileNames", []))
                        if actual != expected or proof["blockedReasons"]:
                            raise ValueError()
                        state["filesystem"]["project-current:" + pid] = proof
                    except ProofLimit:
                        raise
                    except (OSError, ValueError, Problem, UnicodeError):
                        state["dependencyScanProblems"].append(
                            {
                                "kind": "project",
                                "id": pid,
                                "code": "SOURCE_DEPENDENCIES_UNRESOLVED",
                            }
                        )
            for tombstone in state.get("retentionTombstones", []):
                if (
                    tombstone.get("kind") == "project"
                    and tombstone.get("remainingFiles")
                    and tombstone["resourceId"] in targets
                ):
                    state["filesystem"]["project:" + tombstone["resourceId"]] = (
                        inspect_tree(
                            self.store.root, self._stage_path(tombstone), budget
                        )
                    )
            for snapshot in state.get("snapshots", []):
                sid = snapshot["snapshotId"]
                path = self.store.root / "snapshots" / sid / "snapshot.json"
                proof = inspect_tree(self.store.root, path, budget)
                state["filesystem"]["snapshot:" + sid] = proof
                try:
                    raw = self._source(path, budget)
                    if (
                        proof["blockedReasons"]
                        or raw != canonical(snapshot).encode()
                        or snapshot.get("snapshotDigest")
                        != digest(
                            {k: v for k, v in snapshot.items() if k != "snapshotDigest"}
                        )
                    ):
                        raise ValueError()
                    if (
                        selection.get("artifactIds")
                        and not self.projects.adapter.validate(snapshot["documents"])[
                            "valid"
                        ]
                    ):
                        raise ValueError()
                except ProofLimit:
                    raise
                except (OSError, ValueError, KeyError, TypeError, UnicodeError):
                    state["dependencyScanProblems"].append(
                        {
                            "kind": "snapshot",
                            "id": sid,
                            "code": "SNAPSHOT_DEPENDENCIES_UNRESOLVED",
                        }
                    )
            state["importedSnapshots"] = []
            for imported in state.get("importedEvidence", []):
                bid = imported["bundleId"]
                path = self.store.root / "evidence-imports" / bid / "snapshot.json"
                proof = inspect_tree(self.store.root, path, budget)
                state["filesystem"]["imported:" + bid] = proof
                try:
                    raw = self._source(path, budget)
                    if (
                        proof["blockedReasons"]
                        or digest(raw) != imported["manifest"]["files"]["snapshot.json"]
                    ):
                        raise ValueError()
                    snapshot = json.loads(raw)
                    if snapshot.get("snapshotDigest") != digest(
                        {k: v for k, v in snapshot.items() if k != "snapshotDigest"}
                    ):
                        raise ValueError()
                    if (
                        selection.get("artifactIds")
                        and not self.projects.adapter.validate(snapshot["documents"])[
                            "valid"
                        ]
                    ):
                        raise ValueError()
                    state["importedSnapshots"].append(
                        {"bundleId": bid, "snapshot": snapshot}
                    )
                except ProofLimit:
                    raise
                except (OSError, ValueError, KeyError, TypeError, UnicodeError):
                    state["dependencyScanProblems"].append(
                        {
                            "kind": "imported_evidence",
                            "id": bid,
                            "code": "IMPORTED_DEPENDENCIES_UNRESOLVED",
                        }
                    )
        except ProofLimit:
            raise
        except (OSError, ValueError, KeyError, TypeError):
            state["dependencyScanProblems"].append(
                {
                    "kind": "filesystem",
                    "id": None,
                    "code": "SOURCE_DEPENDENCIES_UNRESOLVED",
                }
            )
        return state

    def reconcile_runs(self, run_ids):
        for rid in run_ids:
            try:
                self.runs.read(rid)
            except (TypeError, KeyError, AttributeError):
                raise ValueError("RETENTION_DEPENDENCIES_UNRESOLVED") from None

    def plan(self, selection):
        self.validate_selection(selection)
        self.reconcile_runs(selection.get("runIds", []))
        with self.store.tx() as db:
            state = self.state(selection, db)
            plan = plan_retention(
                selection.get("runIds", []),
                state,
                project_ids=selection.get("projectIds", []),
                artifact_ids=selection.get("artifactIds", []),
                rule=selection.get("rule", "explicit"),
            )
            plan["filesystem"] = deepcopy(state["filesystem"])
            self.store.put("retention", plan["planId"], plan, db)
            return plan

    @staticmethod
    def validate_selection(selection):
        for field in ("runIds", "projectIds", "artifactIds"):
            _selection(selection.get(field, []))
        if (
            not 0
            < sum(
                len(selection.get(field, []))
                for field in ("runIds", "projectIds", "artifactIds")
            )
            <= 128
            or selection.get("rule", "explicit") != "explicit"
        ):
            raise ValueError("RETENTION_SELECTION_INVALID")

    def _restore(self, stage):
        original = self._project_path(stage["resourceId"])
        quarantine = self._stage_path(stage)
        if quarantine.exists():
            if original.exists():
                raise ValueError("RETENTION_RECOVERY_CONFLICT")
            original.parent.mkdir(parents=True, exist_ok=True)
            quarantine.rename(original)

    def _tombstone(self, kind, identifier):
        try:
            return self.store.get("retentionTombstone", kind + ":" + identifier)
        except Problem:
            return None

    def _retire_artifact(self, identifier, plan):
        tombstone_id = "artifact:" + identifier
        try:
            with self.store.tx() as db:
                original = self.store.get("catalogArtifact", identifier, db)
                tombstone = {
                    "kind": "artifact",
                    "resourceId": identifier,
                    "originalRecord": original,
                    "planId": plan["planId"],
                    "retiredAt": time.time(),
                    "externalArtifactPreserved": True,
                }
                self.store.put("retentionTombstone", tombstone_id, tombstone, db)
                self.store.put(
                    "retentionHistory",
                    plan["planId"] + ":artifact:" + identifier,
                    tombstone,
                    db,
                )
                db.execute(
                    "DELETE FROM records WHERE kind=? AND id=?",
                    ("catalogArtifact", identifier),
                )
        except Exception:
            retired = self._tombstone("artifact", identifier)
            try:
                self.store.get("catalogArtifact", identifier)
                still_present = True
            except Problem:
                still_present = False
            if not retired or retired.get("planId") != plan["planId"] or still_present:
                return {
                    "artifactId": identifier,
                    "status": "failed",
                    "reason": "METADATA_COMMIT_FAILED",
                    "externalArtifactPreserved": True,
                }
        return {
            "artifactId": identifier,
            "status": "removed",
            "externalArtifactPreserved": True,
        }

    def _retire_project(self, identifier, plan):
        existing = self._tombstone("project", identifier)
        residue = existing is not None and existing.get("remainingFiles")
        if residue:
            try:
                self.store.get("project", identifier)
            except Problem:
                pass
            else:
                return {
                    "projectId": identifier,
                    "status": "failed",
                    "reason": "RETENTION_RECOVERY_CONFLICT",
                }
        if residue:
            stage = existing
            quarantine = self._stage_path(stage)
        else:
            original = self._project_path(identifier)
            stage = {
                "kind": "project",
                "resourceId": identifier,
                "planId": plan["planId"],
                "quarantineRef": f"retention-staging/{plan['planId']}/{identifier}",
                "phase": "accepted",
                "originalFingerprint": plan["filesystem"]["project:" + identifier][
                    "fingerprint"
                ],
            }
            quarantine = self._stage_path(stage)
            if quarantine.exists():
                return {
                    "projectId": identifier,
                    "status": "failed",
                    "reason": "RETENTION_STAGING_CONFLICT",
                }
            self.store.put(
                "retentionProjectStage", plan["planId"] + ":" + identifier, stage
            )
            try:
                quarantine.parent.mkdir(parents=True, exist_ok=True)
                managed_path(self.store.root, quarantine.parent)
                if original.exists():
                    original.rename(quarantine)
                proof = inspect_tree(self.store.root, quarantine, ProofBudget())
                if (
                    proof["blockedReasons"]
                    or proof["fingerprint"] != stage["originalFingerprint"]
                ):
                    self._restore(stage)
                    raise ValueError("RETENTION_FILES_CHANGED")
                stage["phase"] = "quarantined"
                self.store.put(
                    "retentionProjectStage", plan["planId"] + ":" + identifier, stage
                )
                with self.store.tx() as db:
                    record = self.store.get("project", identifier, db)
                    self.store.on_rollback(db, lambda: self._restore(stage))
                    tombstone = {
                        **stage,
                        "phase": "retired",
                        "originalRecord": record,
                        "retiredAt": time.time(),
                        "remainingFiles": quarantine.exists(),
                    }
                    self.store.put(
                        "retentionTombstone", "project:" + identifier, tombstone, db
                    )
                    self.store.put(
                        "retentionHistory",
                        plan["planId"] + ":project:" + identifier,
                        tombstone,
                        db,
                    )
                    db.execute(
                        "DELETE FROM records WHERE kind=? AND id=?",
                        ("project", identifier),
                    )
                    self.store.put(
                        "retentionProjectStage",
                        plan["planId"] + ":" + identifier,
                        {**stage, "phase": "retired"},
                        db,
                    )
                existing = tombstone
            except Exception:
                existing = self._tombstone("project", identifier)
                if existing is None or existing.get("planId") != plan["planId"]:
                    try:
                        self._restore(stage)
                    except (OSError, ValueError):
                        return {
                            "projectId": identifier,
                            "status": "failed",
                            "reason": "RETENTION_RECOVERY_REQUIRED",
                        }
                    stage["phase"] = "aborted"
                    self.store.put(
                        "retentionProjectStage",
                        plan["planId"] + ":" + identifier,
                        stage,
                    )
                    return {
                        "projectId": identifier,
                        "status": "failed",
                        "reason": "PROJECT_RETIREMENT_FAILED",
                    }
        try:
            if quarantine.exists():
                shutil.rmtree(managed_path(self.store.root, quarantine))
        except (OSError, ValueError):
            existing.update(remainingFiles=True, cleanupStatus="failed")
            self.store.put("retentionTombstone", "project:" + identifier, existing)
            return {
                "projectId": identifier,
                "status": "failed",
                "reason": "FILESYSTEM_REMOVAL_FAILED",
                "metadataRemoved": True,
                "remainingManagedFiles": True,
                "retryScope": "owned_project_retention_residue",
            }
        existing.update(remainingFiles=False, cleanupStatus="complete")
        self.store.put("retentionTombstone", "project:" + identifier, existing)
        return {
            "projectId": identifier,
            "status": "removed",
            "metadataRemoved": True,
            "remainingManagedFiles": False,
        }

    def recover_stages(self):
        try:
            with self.store.tx() as db:
                pending = self._all(
                    "retentionProjectStage",
                    db,
                    ProofBudget(),
                    suffix=" AND json_extract(body,'$.phase') IN ('accepted','quarantined')",
                )
        except (ProofLimit, ValueError, sqlite3.DatabaseError):
            self.recoveryProblems.append({"code": "RETENTION_RECOVERY_REQUIRED"})
            return
        for stage in pending:
            try:
                if not isinstance(stage, dict):
                    raise ValueError()
                identifier = stage["resourceId"]
                _selection([identifier])
                _selection([stage["planId"]])
                retired = self._tombstone("project", identifier)
                if retired:
                    # A proven committed retirement is never reversed.
                    try:
                        self.store.get("project", identifier)
                    except Problem:
                        pass
                    else:
                        raise ValueError("RETENTION_RECOVERY_CONFLICT")
                    if retired.get("planId") != stage["planId"]:
                        raise ValueError("RETENTION_RECOVERY_CONFLICT")
                    stage["phase"] = "retired"
                else:
                    self.store.get("project", identifier)
                    original = self._project_path(identifier)
                    quarantine = self._stage_path(stage)
                    if quarantine.exists():
                        proof = inspect_tree(self.store.root, quarantine, ProofBudget())
                        if (
                            proof["blockedReasons"]
                            or proof["fingerprint"] != stage["originalFingerprint"]
                            or original.exists()
                        ):
                            raise ValueError()
                        self._restore(stage)
                    stage["phase"] = "aborted"
                self.store.put(
                    "retentionProjectStage", stage["planId"] + ":" + identifier, stage
                )
            except Exception:
                self.recoveryProblems.append(
                    {
                        "code": "RETENTION_RECOVERY_REQUIRED",
                        "resourceId": stage.get("resourceId")
                        if isinstance(stage, dict)
                        else None,
                    }
                )
                if (
                    isinstance(stage, dict)
                    and isinstance(stage.get("resourceId"), str)
                    and isinstance(stage.get("planId"), str)
                ):
                    stage["phase"] = "unknown"
                    stage["reason"] = "RETENTION_RECOVERY_REQUIRED"
                    self.store.put(
                        "retentionProjectStage",
                        stage["planId"] + ":" + stage["resourceId"],
                        stage,
                    )

    def apply(self, plan_id, fingerprint, principal, key):
        initial = self.store.get("retention", plan_id)
        self.reconcile_runs(initial.get("runIds", []))

        def accepted(db):
            plan = self.store.get("retention", plan_id, db)
            selection = {
                field: plan.get(field, [])
                for field in ("runIds", "projectIds", "artifactIds")
            }
            check_plan(plan, self.state(selection, db), fingerprint)
            if plan["status"] != "planned":
                raise Problem(
                    "RETENTION_PLAN_STALE",
                    "This plan already has an accepted apply operation.",
                    409,
                )
            from xverse_studio.storage.core import uid

            oid = uid("op-")
            plan.update(status="applying", operationId=oid, outcomes=[])
            self.store.put("retention", plan_id, plan, db)
            self.store.put(
                "operation",
                oid,
                {
                    "operationId": oid,
                    "kind": "retention",
                    "planId": plan_id,
                    "status": "accepted",
                },
                db,
            )
            return {"planId": plan_id, "operationId": oid}

        result, is_new = self.store.idempotent(
            principal,
            "POST /retention/" + plan_id + "/apply",
            key,
            {"fingerprint": fingerprint},
            accepted,
        )
        if is_new:
            with self.store.lock:
                plan = self.store.get("retention", plan_id)
                operation = self.store.get("operation", result["operationId"])
                selection = {
                    field: plan.get(field, [])
                    for field in ("runIds", "projectIds", "artifactIds")
                }
                try:
                    removals = check_plan(plan, self.state(selection), fingerprint)
                except (ValueError, ProofLimit):
                    plan.update(status="rejected", reason="RETENTION_PLAN_STALE")
                    self.store.put("retention", plan_id, plan)
                    operation.update(
                        status="rejected",
                        code="RETENTION_PLAN_STALE",
                        result={
                            "planId": plan_id,
                            "status": "rejected",
                            "outcomes": [],
                        },
                    )
                    self.store.put("operation", operation["operationId"], operation)
                    return {
                        **result,
                        **operation["result"],
                        "operationStatus": "rejected",
                    }
                operation["status"] = "delegated"
                self.store.put("operation", operation["operationId"], operation)
                for removal in removals:
                    id_field = next(
                        field
                        for field in ("runId", "projectId", "artifactId")
                        if field in removal
                    )
                    identifier = removal[id_field]
                    current_selection = {
                        "runIds": [],
                        "projectIds": [],
                        "artifactIds": [],
                    }
                    current_selection[id_field[:-2] + "Ids"] = [identifier]
                    try:
                        current = self.state(current_selection)
                        fresh = plan_retention(
                            current_selection["runIds"],
                            current,
                            project_ids=current_selection["projectIds"],
                            artifact_ids=current_selection["artifactIds"],
                        )
                        proof_key = (
                            "project:" if id_field == "projectId" else "run:"
                        ) + identifier
                        if (
                            fresh["protected"]
                            or removal not in fresh["removals"]
                            or id_field != "artifactId"
                            and current["filesystem"].get(proof_key)
                            != plan["filesystem"].get(proof_key)
                        ):
                            raise ValueError("RETENTION_DEPENDENCIES_CHANGED")
                        if id_field == "artifactId":
                            outcome = self._retire_artifact(identifier, plan)
                        elif id_field == "projectId":
                            outcome = self._retire_project(identifier, plan)
                        else:
                            root = managed_path(
                                self.store.root, self.runs.directory(identifier)
                            )
                            if root.exists():
                                shutil.rmtree(root)
                            outcome = {
                                "runId": identifier,
                                "status": "removed",
                                "snapshotPreserved": True,
                            }
                    except ProofLimit:
                        outcome = {
                            id_field: identifier,
                            "status": "failed",
                            "reason": "RETENTION_PROOF_LIMIT",
                        }
                    except (OSError, ValueError, Problem):
                        outcome = {
                            id_field: identifier,
                            "status": "failed",
                            "reason": "FILESYSTEM_REMOVAL_FAILED"
                            if id_field == "runId"
                            else "RETENTION_DEPENDENCIES_CHANGED",
                        }
                    plan["outcomes"].append(outcome)
                    self.store.put("retention", plan_id, plan)
                plan.update(status="applied", appliedAt=time.time())
                self.store.put("retention", plan_id, plan)
                operation.update(
                    status="completed",
                    result={
                        "planId": plan_id,
                        "status": "complete"
                        if all(o["status"] == "removed" for o in plan["outcomes"])
                        else "partial",
                        "outcomes": plan["outcomes"],
                        "protected": plan["protected"],
                    },
                )
                self.store.put("operation", operation["operationId"], operation)
        operation = self.store.get("operation", result["operationId"])
        return {
            **result,
            **operation.get("result", {}),
            "operationStatus": operation["status"],
        }
