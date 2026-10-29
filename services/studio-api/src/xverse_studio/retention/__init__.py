"""Explicit dependency-aware retention; never deletes external artifact bytes."""

from copy import deepcopy
import hashlib
import json
import re
import time
import uuid

from ruamel.yaml import YAML

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
MAX_SELECTIONS = 128
MAX_DEPENDENCY_EDGES = 4096
MAX_REFERENCE_NODES = 200_000
_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,119}$")


def state_fingerprint(state: dict) -> str:
    return (
        "sha256:"
        + hashlib.sha256(
            json.dumps(
                state, sort_keys=True, separators=(",", ":"), allow_nan=False
            ).encode()
        ).hexdigest()
    )


def _selection(values):
    if (
        not isinstance(values, list)
        or len(values) > MAX_SELECTIONS
        or any(
            not isinstance(value, str) or not _ID.fullmatch(value) for value in values
        )
        or len(set(values)) != len(values)
    ):
        raise ValueError("RETENTION_SELECTION_INVALID")
    return values


def _references(record):
    """Conservative exact declarative references, including opaque source payloads.

    YAML is loaded safely as data only. Unknown/deep/malformed source cannot prove
    dependency absence and refuses a deletion plan rather than hiding an edge.
    """
    result, seen, count = set(), set(), 0
    stack = [(record, 0)]
    yaml = YAML(typ="safe")
    while stack:
        value, depth = stack.pop()
        count += 1
        if count > MAX_REFERENCE_NODES or depth > 64:
            raise ValueError("RETENTION_DEPENDENCIES_UNRESOLVED")
        if isinstance(value, str):
            result.add(value)
        elif isinstance(value, (dict, list)):
            if id(value) in seen:
                continue
            seen.add(id(value))
            if isinstance(value, list):
                stack.extend((item, depth + 1) for item in value)
                continue
            for key, item in value.items():
                if isinstance(key, str):
                    result.add(key)
                if key in {"documents", "projectDocuments"}:
                    if not isinstance(item, dict):
                        raise ValueError("RETENTION_DEPENDENCIES_UNRESOLVED")
                    for document in item.values():
                        content = (
                            document
                            if isinstance(document, str)
                            else document.get("content")
                            if isinstance(document, dict)
                            else None
                        )
                        if not isinstance(content, str):
                            raise ValueError("RETENTION_DEPENDENCIES_UNRESOLVED")
                        try:
                            parsed = yaml.load(content)
                        except Exception:
                            raise ValueError(
                                "RETENTION_DEPENDENCIES_UNRESOLVED"
                            ) from None
                        if (
                            not isinstance(parsed, dict)
                            or parsed.get("kind")
                            not in {
                                "Component",
                                "System",
                                "Deployment",
                                "Scenario",
                                "Profile",
                            }
                            or not isinstance(parsed.get("spec"), dict)
                        ):
                            raise ValueError("RETENTION_DEPENDENCIES_UNRESOLVED")
                        stack.append((parsed, depth + 1))
                elif key == "supportingFiles":
                    if not isinstance(item, dict):
                        raise ValueError("RETENTION_DEPENDENCIES_UNRESOLVED")
                    for name, content in item.items():
                        if not isinstance(content, str):
                            raise ValueError("RETENTION_DEPENDENCIES_UNRESOLVED")
                        if not name.endswith((".json", ".yaml", ".yml", ".md")):
                            raise ValueError("RETENTION_DEPENDENCIES_UNRESOLVED")
                        try:
                            parsed = (
                                yaml.load(content)
                                if name.endswith((".json", ".yaml", ".yml"))
                                else content
                            )
                        except Exception:
                            raise ValueError(
                                "RETENTION_DEPENDENCIES_UNRESOLVED"
                            ) from None
                        stack.append((parsed, depth + 1))
                else:
                    stack.append((item, depth + 1))
    return result


def _source_records(state):
    mappings = (
        ("projects", "project", "projectId"),
        ("snapshots", "snapshot", "snapshotId"),
        ("runs", "run", "runId"),
        ("campaigns", "campaign", "campaignId"),
        ("evaluations", "evaluation", "evaluationId"),
        ("annotations", "annotation", "annotationId"),
        ("importedEvidence", "imported_evidence", "bundleId"),
        ("importedSnapshots", "imported_evidence_snapshot", "bundleId"),
    )
    for collection, kind, id_field in mappings:
        for record in state.get(collection, []):
            yield kind, record.get(id_field), record


def _validate_retained_links(state, *, require_projects=False):
    if not isinstance(state, dict):
        raise ValueError("RETENTION_DEPENDENCIES_UNRESOLVED")
    identifiers = {
        "projects": "projectId",
        "snapshots": "snapshotId",
        "runs": "runId",
        "campaigns": "campaignId",
        "evaluations": "evaluationId",
        "annotations": "annotationId",
        "importedEvidence": "bundleId",
        "importedSnapshots": "bundleId",
        "artifacts": "entryId",
        "retentionTombstones": "resourceId",
        "retentionStages": "resourceId",
    }
    total = 0
    for collection, id_field in identifiers.items():
        records = state.get(collection, [])
        if not isinstance(records, list):
            raise ValueError("RETENTION_DEPENDENCIES_UNRESOLVED")
        total += len(records)
        if total > 10_000:
            raise ValueError("RETENTION_DEPENDENCIES_UNRESOLVED")
        seen = set()
        for record in records:
            if (
                not isinstance(record, dict)
                or not isinstance(record.get(id_field), str)
                or not _ID.fullmatch(record[id_field])
            ):
                raise ValueError("RETENTION_DEPENDENCIES_UNRESOLVED")
            # Multiple audit/staging entries may refer to one retained resource;
            # identity-bearing operational collections cannot silently shadow.
            if (
                collection not in {"retentionTombstones", "retentionStages"}
                and record[id_field] in seen
            ):
                raise ValueError("RETENTION_DEPENDENCIES_UNRESOLVED")
            seen.add(record[id_field])
            if "projectId" in record and (
                not isinstance(record["projectId"], str)
                or not _ID.fullmatch(record["projectId"])
            ):
                raise ValueError("RETENTION_DEPENDENCIES_UNRESOLVED")
            if (
                require_projects
                and collection in {"snapshots", "runs"}
                and "projectId" not in record
            ):
                raise ValueError("RETENTION_DEPENDENCIES_UNRESOLVED")
            if collection == "runs" and record.get("state") not in ACTIVE | {
                "stopped",
                "failed",
            }:
                raise ValueError("RETENTION_DEPENDENCIES_UNRESOLVED")
            if collection == "campaigns":
                nested = record.get("baseSnapshot")
                children = record.get("children", [])
                if (
                    not isinstance(nested, dict)
                    or not isinstance(nested.get("projectId"), str)
                    or not _ID.fullmatch(nested["projectId"])
                    or not isinstance(children, list)
                    or len(children) > 64
                ):
                    raise ValueError("RETENTION_DEPENDENCIES_UNRESOLVED")
                for child in children:
                    if (
                        not isinstance(child, dict)
                        or child.get("runId") is not None
                        and (
                            not isinstance(child["runId"], str)
                            or not _ID.fullmatch(child["runId"])
                        )
                    ):
                        raise ValueError("RETENTION_DEPENDENCIES_UNRESOLVED")
            if collection == "importedSnapshots":
                nested = record.get("snapshot")
                if (
                    not isinstance(nested, dict)
                    or not isinstance(nested.get("projectId"), str)
                    or not _ID.fullmatch(nested["projectId"])
                ):
                    raise ValueError("RETENTION_DEPENDENCIES_UNRESOLVED")
            if collection == "artifacts" and any(
                not isinstance(record.get(field), str) or not record[field]
                for field in ("digest", "originRef")
            ):
                raise ValueError("RETENTION_DEPENDENCIES_UNRESOLVED")
            for field in ("runId", "snapshotId"):
                if field in record and (
                    not isinstance(record[field], str)
                    or not _ID.fullmatch(record[field])
                ):
                    raise ValueError("RETENTION_DEPENDENCIES_UNRESOLVED")


def plan_retention(
    run_ids: list[str],
    state: dict,
    *,
    project_ids=None,
    artifact_ids=None,
    rule="explicit",
    ttl_seconds=60,
) -> dict:
    run_ids, project_ids, artifact_ids = (
        _selection(run_ids),
        _selection(project_ids or []),
        _selection(artifact_ids or []),
    )
    if (
        not 0 < len(run_ids) + len(project_ids) + len(artifact_ids) <= MAX_SELECTIONS
        or rule != "explicit"
    ):
        raise ValueError("RETENTION_SELECTION_INVALID")
    _validate_retained_links(state, require_projects=bool(project_ids or artifact_ids))
    runs = {r["runId"]: r for r in state.get("runs", [])}
    projects = {r["projectId"]: r for r in state.get("projects", [])}
    artifacts = {r["entryId"]: r for r in state.get("artifacts", [])}
    tombstones = {
        r["resourceId"]: r
        for r in state.get("retentionTombstones", [])
        if r.get("kind") == "project" and r.get("remainingFiles")
    }
    planned, protected, edges = [], [], []
    edge_keys = set()

    def edge(source_kind, source_id, target_kind, target_id, reason):
        key = (source_kind, source_id, target_kind, target_id, reason)
        if key not in edge_keys:
            if len(edges) >= MAX_DEPENDENCY_EDGES:
                raise ValueError("RETENTION_DEPENDENCY_LIMIT")
            edge_keys.add(key)
            edges.append(
                {
                    "source": {"kind": source_kind, "id": source_id},
                    "target": {"kind": target_kind, "id": target_id},
                    "reason": reason,
                }
            )

    for rid in run_ids:
        if rid not in runs:
            raise ValueError("RETENTION_RUN_NOT_FOUND")
        reasons = []
        if runs[rid].get("state") in ACTIVE:
            reasons.append("ACTIVE_RUN_PROTECTED")
        for collection, kind, field, reason in (
            (
                "evaluations",
                "evaluation",
                "evaluationId",
                "EVALUATION_DEPENDS_ON_EVIDENCE",
            ),
            (
                "annotations",
                "annotation",
                "annotationId",
                "ANNOTATION_DEPENDS_ON_EVIDENCE",
            ),
        ):
            for record in state.get(collection, []):
                if record.get("runId") == rid and not (
                    kind == "annotation" and record.get("deleted")
                ):
                    reasons.append(reason)
                    edge(kind, record.get(field), "run", rid, reason)
        for campaign in state.get("campaigns", []):
            if any(c.get("runId") == rid for c in campaign.get("children", [])):
                reasons.append("CAMPAIGN_DEPENDS_ON_RUN")
                edge(
                    "campaign",
                    campaign.get("campaignId"),
                    "run",
                    rid,
                    "CAMPAIGN_DEPENDS_ON_RUN",
                )
        proof = state.get("filesystem", {}).get("run:" + rid, {})
        reasons.extend(proof.get("blockedReasons", []))
        if reasons:
            protected.append({"runId": rid, "reasons": list(dict.fromkeys(reasons))})
        else:
            planned.append(
                {"runId": rid, "scope": "owned_run_files", "snapshotProtected": True}
            )

    # All retained authored/history evidence is indexed before any artifact
    # deletion can be considered eligible. There is no truncated safe report.
    references = []
    if project_ids or artifact_ids:
        if state.get("dependencyScanProblems"):
            raise ValueError("RETENTION_DEPENDENCIES_UNRESOLVED")
        for kind, identifier, record in _source_records(state):
            references.append(
                (
                    kind,
                    identifier,
                    record,
                    _references(record) if artifact_ids else None,
                )
            )

    for pid in project_ids:
        if pid not in projects and pid not in tombstones:
            raise ValueError("RETENTION_PROJECT_NOT_FOUND")
        reasons = []
        for kind, identifier, record, _ in references:
            if kind == "project" and identifier == pid:
                continue
            # Envelope links are structural metadata; source language remains
            # authoritative and is not rewritten to make deletion possible.
            linked = record.get("projectId") == pid
            if kind == "campaign":
                linked = (
                    linked or record.get("baseSnapshot", {}).get("projectId") == pid
                )
            if kind == "imported_evidence_snapshot":
                linked = linked or record.get("snapshot", {}).get("projectId") == pid
            if linked:
                reason = {
                    "snapshot": "SNAPSHOT_DEPENDS_ON_PROJECT",
                    "run": "RUN_HISTORY_DEPENDS_ON_PROJECT",
                    "campaign": "CAMPAIGN_DEPENDS_ON_PROJECT",
                    "imported_evidence_snapshot": "EVIDENCE_DEPENDS_ON_PROJECT",
                }.get(kind, "HISTORICAL_RECORD_DEPENDS_ON_PROJECT")
                reasons.append(reason)
                edge(kind, identifier, "project", pid, reason)
                if kind == "run" and record.get("state") in ACTIVE:
                    reasons.append("ACTIVE_RUN_PROJECT_INPUTS_PROTECTED")
        for stage in state.get("retentionStages", []):
            if stage.get("resourceId") == pid and stage.get("phase") in {
                "accepted",
                "quarantined",
                "unknown",
            }:
                reasons.append("RETENTION_RECOVERY_REQUIRED")
        proof = state.get("filesystem", {}).get("project:" + pid, {})
        reasons.extend(proof.get("blockedReasons", []))
        if reasons:
            protected.append(
                {"projectId": pid, "reasons": list(dict.fromkeys(reasons))}
            )
        else:
            planned.append(
                {
                    "projectId": pid,
                    "scope": "owned_project_retention_residue"
                    if pid in tombstones and pid not in projects
                    else "owned_project_files_and_index",
                }
            )

    for aid in artifact_ids:
        if aid not in artifacts:
            raise ValueError("RETENTION_ARTIFACT_NOT_FOUND")
        artifact = artifacts[aid]
        tokens = {
            v
            for v in (aid, artifact.get("digest"), artifact.get("originRef"))
            if isinstance(v, str) and v
        }
        reasons = []
        for kind, identifier, record, mentioned in references:
            if tokens & mentioned:
                reason = {
                    "project": "PROJECT_DEPENDS_ON_ARTIFACT",
                    "snapshot": "SNAPSHOT_DEPENDS_ON_ARTIFACT",
                    "run": "RUN_EVIDENCE_DEPENDS_ON_ARTIFACT",
                    "campaign": "CAMPAIGN_DEPENDS_ON_ARTIFACT",
                    "evaluation": "EVALUATION_DEPENDS_ON_ARTIFACT",
                    "annotation": "ANNOTATION_DEPENDS_ON_ARTIFACT",
                }.get(kind, "IMPORTED_EVIDENCE_DEPENDS_ON_ARTIFACT")
                reasons.append(reason)
                edge(kind, identifier, "artifact", aid, reason)
        if reasons:
            protected.append(
                {"artifactId": aid, "reasons": list(dict.fromkeys(reasons))}
            )
        else:
            planned.append(
                {
                    "artifactId": aid,
                    "scope": "catalog_registration_metadata_only",
                    "externalArtifactPreserved": True,
                }
            )
    known_bytes = sum(
        state.get("filesystem", {})
        .get(
            ("run:" + r["runId"]) if "runId" in r else ("project:" + r["projectId"]), {}
        )
        .get("byteCount", 0)
        for r in planned
        if "artifactId" not in r
    )
    return {
        "planId": "ret-" + str(uuid.uuid4()),
        "fingerprint": state_fingerprint(state),
        "runIds": deepcopy(run_ids),
        "projectIds": deepcopy(project_ids),
        "artifactIds": deepcopy(artifact_ids),
        "rule": rule,
        "removals": planned,
        "protected": protected,
        "dependencyEdges": edges,
        "dependencyReportComplete": True,
        "counts": {
            "selected": len(run_ids) + len(project_ids) + len(artifact_ids),
            "eligible": len(planned),
            "protected": len(protected),
            "knownManagedBytes": known_bytes,
        },
        "expiresAt": time.time() + min(300, max(1, ttl_seconds)),
        "status": "planned",
        "limits": {
            "maxSelections": MAX_SELECTIONS,
            "maxDependencyEdges": MAX_DEPENDENCY_EDGES,
        },
    }


def check_plan(plan, state, fingerprint):
    if (
        fingerprint != plan["fingerprint"]
        or state_fingerprint(state) != plan["fingerprint"]
        or plan["expiresAt"] <= time.time()
    ):
        raise ValueError("RETENTION_PLAN_STALE")
    fresh = plan_retention(
        plan.get("runIds", []),
        state,
        project_ids=plan.get("projectIds", []),
        artifact_ids=plan.get("artifactIds", []),
        rule=plan.get("rule", "explicit"),
    )
    if (
        fresh["removals"] != plan["removals"]
        or fresh["protected"] != plan["protected"]
        or fresh.get("dependencyEdges", []) != plan.get("dependencyEdges", [])
    ):
        raise ValueError("RETENTION_PLAN_STALE")
    return deepcopy(plan["removals"])
