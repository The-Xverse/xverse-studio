"""Derived metadata and retention invariants; archive tests are owned by exchange."""

from copy import deepcopy
import pytest
from xverse_studio.annotations import (
    create_annotation,
    revise_annotation,
    AnnotationError,
)
from xverse_studio.retention import plan_retention, check_plan


def test_annotations_keep_history_and_never_mutate_original_record():
    body = {
        "kind": "comment",
        "text": "Observed fixture",
        "evidenceRefs": ["run:journal"],
    }
    original = create_annotation("run", body, author="operator")
    revised = revise_annotation(
        original, {**body, "text": "Correction"}, expected_revision=1, author="operator"
    )
    assert original["text"] == "Observed fixture" and original["revision"] == 1
    assert revised["history"][0]["text"] == original["text"]
    assert revised["revision"] == 2
    with pytest.raises(AnnotationError, match="REVISION_CONFLICT"):
        revise_annotation(revised, body, expected_revision=1, author="operator")
    tombstone = revise_annotation(
        revised, {}, expected_revision=2, author="operator", delete=True
    )
    assert tombstone["deleted"] and len(tombstone["history"]) == 2


@pytest.mark.parametrize(
    "uri",
    [
        "javascript:alert(1)",
        "file:///etc/passwd",
        "https://name:password@example.com/r",
        "https://example.com/?token=secret",
        "http://[broken",
        "https://example.com/\nnext",
    ],
)
def test_trace_targets_are_inert_and_credential_free(uri):
    with pytest.raises(AnnotationError):
        create_annotation(
            "run",
            {"kind": "trace_link", "target": {"uri": uri, "revision": "unknown"}},
            author="operator",
        )


def test_trace_links_pin_revision_without_claiming_target_validity():
    row = create_annotation(
        "run",
        {
            "kind": "trace_link",
            "target": {"uri": "urn:test:requirement:12", "revision": "rev-1"},
        },
        author="operator",
    )
    assert row["target"]["revision"] == "rev-1"
    assert "verdict" not in row


def test_retention_is_read_only_and_protects_active_and_derived_dependencies():
    state = {
        "runs": [
            {"runId": "active", "state": "unknown"},
            {"runId": "done", "state": "stopped"},
            {"runId": "derived", "state": "stopped"},
        ],
        "evaluations": [{"evaluationId": "eval-derived", "runId": "derived"}],
    }
    before = deepcopy(state)
    plan = plan_retention(["active", "done", "derived"], state)
    assert [r["runId"] for r in plan["removals"]] == ["done"]
    assert state == before
    assert check_plan(plan, state, plan["fingerprint"]) == plan["removals"]
    state["runs"][1]["state"] = "running"
    with pytest.raises(ValueError, match="RETENTION_PLAN_STALE"):
        check_plan(plan, state, plan["fingerprint"])


def test_expanded_retention_protects_historical_project_and_artifact_dependencies():
    state = {
        "runs": [],
        "snapshots": [
            {
                "snapshotId": "snap-1",
                "projectId": "project-1",
                "documents": {
                    "deployment.yaml": "kind: Deployment\nspec:\n  artifacts:\n  - digest: sha256:artifact\n"
                },
            }
        ],
        "projects": [{"projectId": "project-1"}, {"projectId": "project-free"}],
        "artifacts": [
            {
                "entryId": "artifact-shared",
                "digest": "sha256:artifact",
                "originRef": "urn:shared",
            },
            {
                "entryId": "artifact-free",
                "digest": "sha256:free",
                "originRef": "urn:free",
            },
        ],
    }
    original = deepcopy(state)
    plan = plan_retention(
        [],
        state,
        project_ids=["project-1", "project-free"],
        artifact_ids=["artifact-shared", "artifact-free"],
    )
    assert state == original
    assert {r.get("projectId") for r in plan["removals"] if "projectId" in r} == {
        "project-free"
    }
    assert {r.get("artifactId") for r in plan["removals"] if "artifactId" in r} == {
        "artifact-free"
    }
    assert any(
        edge["source"] == {"kind": "snapshot", "id": "snap-1"}
        and edge["target"] == {"kind": "project", "id": "project-1"}
        for edge in plan["dependencyEdges"]
    )
    assert any(
        edge["target"] == {"kind": "artifact", "id": "artifact-shared"}
        for edge in plan["dependencyEdges"]
    )
    assert plan["dependencyReportComplete"] is True


def test_expanded_retention_refuses_unknown_or_unbounded_selection_and_unresolved_scan():
    with pytest.raises(ValueError, match="RETENTION_SELECTION_INVALID"):
        plan_retention([], {"projects": []}, project_ids=["../outside"])
    with pytest.raises(ValueError, match="RETENTION_SELECTION_INVALID"):
        plan_retention([], {"projects": []})
    with pytest.raises(ValueError, match="RETENTION_PROJECT_NOT_FOUND"):
        plan_retention([], {"projects": []}, project_ids=["missing"])
    with pytest.raises(ValueError, match="RETENTION_DEPENDENCIES_UNRESOLVED"):
        plan_retention(
            [],
            {
                "projects": [
                    {
                        "projectId": "p",
                        "documents": {"doc": {"content": "kind: [broken"}},
                    }
                ],
                "artifacts": [
                    {"entryId": "a", "digest": "sha256:a", "originRef": "urn:a"}
                ],
            },
            artifact_ids=["a"],
        )


def test_expanded_plan_fingerprint_detects_external_filesystem_proof_changes():
    state = {
        "projects": [{"projectId": "p"}],
        "filesystem": {"project:p": {"fingerprint": "old"}},
    }
    plan = plan_retention([], state, project_ids=["p"])
    state["filesystem"]["project:p"]["fingerprint"] = "changed"
    with pytest.raises(ValueError, match="RETENTION_PLAN_STALE"):
        check_plan(plan, state, plan["fingerprint"])


def test_artifact_registration_retention_never_removes_external_bytes(client, tmp_path):
    external = tmp_path / "external-model.bin"
    external.write_bytes(b"owned external fixture remains intact")
    registered = client.post(
        "/api/v1/catalog/artifacts",
        headers={"Idempotency-Key": "retention-register"},
        json={
            "name": "Metadata only",
            "version": "1.0.0",
            "artifactKind": "model",
            "digest": "sha256:" + "f" * 64,
            "originRef": "urn:owned:external-reference",
        },
    )
    assert registered.status_code == 201, registered.text
    aid = registered.json()["entryId"]
    response = client.post(
        "/api/v1/retention/plans", json={"artifactIds": [aid], "rule": "explicit"}
    )
    assert response.status_code == 200, response.text
    plan = response.json()
    assert plan["removals"] == [
        {
            "artifactId": aid,
            "scope": "catalog_registration_metadata_only",
            "externalArtifactPreserved": True,
        }
    ]
    assert client.get("/api/v1/catalog/" + aid).status_code == 200
    result = client.post(
        "/api/v1/retention/plans/" + plan["planId"] + "/apply",
        headers={"Idempotency-Key": "remove-artifact-metadata"},
        json={"fingerprint": plan["fingerprint"]},
    )
    assert result.status_code == 202, result.text
    assert result.json()["status"] == "complete"
    assert result.json()["outcomes"][0]["externalArtifactPreserved"] is True
    assert client.get("/api/v1/catalog/" + aid).status_code == 404
    assert external.read_bytes() == b"owned external fixture remains intact"
    assert (
        client.post(
            "/api/v1/retention/plans/" + plan["planId"] + "/apply",
            headers={"Idempotency-Key": "remove-artifact-metadata"},
            json={"fingerprint": plan["fingerprint"]},
        ).json()
        == result.json()
    )


def test_project_retention_is_explicit_and_preserves_unselected_projects(client):
    first = client.post(
        "/api/v1/projects", json={"name": "Retire this authored project"}
    ).json()
    second = client.post(
        "/api/v1/projects", json={"name": "Keep this authored project"}
    ).json()
    response = client.post(
        "/api/v1/retention/plans", json={"projectIds": [first["projectId"]]}
    )
    assert response.status_code == 200, response.text
    plan = response.json()
    assert plan["dependencyReportComplete"] is True
    assert client.get("/api/v1/projects/" + first["projectId"]).status_code == 200
    result = client.post(
        "/api/v1/retention/plans/" + plan["planId"] + "/apply",
        headers={"Idempotency-Key": "remove-project"},
        json={"fingerprint": plan["fingerprint"]},
    )
    assert result.status_code == 202, result.text
    assert result.json()["status"] == "complete"
    assert client.get("/api/v1/projects/" + first["projectId"]).status_code == 404
    assert client.get("/api/v1/projects/" + second["projectId"]).status_code == 200
    assert first["projectId"] not in [
        p["projectId"] for p in client.get("/api/v1/projects").json()["items"]
    ]
    assert not (
        client.app.state.studio.store.root / "projects" / first["projectId"]
    ).exists()
    assert (
        client.app.state.studio.store.get(
            "retentionTombstone", "project:" + first["projectId"]
        )["resourceId"]
        == first["projectId"]
    )
    store = client.app.state.studio.store
    # Revision history goes with its project; the kept project's history stays.
    assert store.find("revision", "projectId", first["projectId"]) == []
    assert [
        r["revision"] for r in store.find("revision", "projectId", second["projectId"])
    ] == [1]


def test_project_retention_protects_every_historical_snapshot_without_cascade(client):
    project = client.post("/api/v1/projects", json={"name": "Historical inputs"}).json()
    pf = client.post(
        "/api/v1/projects/" + project["projectId"] + "/preflights",
        json={"revision": project["revision"]},
    ).json()
    snapshot = client.app.state.studio.store.get("snapshot", pf["snapshotId"])
    response = client.post(
        "/api/v1/retention/plans", json={"projectIds": [project["projectId"]]}
    )
    assert response.status_code == 200, response.text
    plan = response.json()
    assert plan["removals"] == []
    assert "SNAPSHOT_DEPENDS_ON_PROJECT" in plan["protected"][0]["reasons"]
    applied = client.post(
        "/api/v1/retention/plans/" + plan["planId"] + "/apply",
        headers={"Idempotency-Key": "protected-project"},
        json={"fingerprint": plan["fingerprint"]},
    )
    assert applied.status_code == 202, applied.text
    assert client.app.state.studio.store.get("snapshot", pf["snapshotId"]) == snapshot
    assert client.get("/api/v1/projects/" + project["projectId"]).status_code == 200


def test_project_source_edit_after_plan_is_stale_and_preserved(client):
    project = client.post(
        "/api/v1/projects", json={"name": "Externally edited draft"}
    ).json()
    response = client.post(
        "/api/v1/retention/plans", json={"projectIds": [project["projectId"]]}
    )
    assert response.status_code == 200, response.text
    plan = response.json()
    did = next(iter(project["documents"]))
    path = client.app.state.studio.projects.document_path(project["projectId"], did)
    changed = path.read_bytes() + b"\n# external change after retention preview\n"
    path.write_bytes(changed)
    applied = client.post(
        "/api/v1/retention/plans/" + plan["planId"] + "/apply",
        headers={"Idempotency-Key": "stale-project-files"},
        json={"fingerprint": plan["fingerprint"]},
    )
    assert applied.status_code == 409, applied.text
    assert applied.json()["code"] == "RETENTION_PLAN_STALE"
    assert path.read_bytes() == changed


def test_shared_artifact_reference_protects_metadata_and_new_reference_stales_plan(
    client,
):
    project = client.post(
        "/api/v1/projects", json={"name": "Artifact references"}
    ).json()
    registered = client.post(
        "/api/v1/catalog/artifacts",
        headers={"Idempotency-Key": "shared-artifact"},
        json={
            "name": "Shared metadata",
            "version": "1.0.0",
            "artifactKind": "model",
            "digest": "sha256:" + "a" * 64,
            "originRef": "urn:owned:shared-artifact",
        },
    ).json()
    response = client.post(
        "/api/v1/retention/plans", json={"artifactIds": [registered["entryId"]]}
    )
    assert response.status_code == 200, response.text
    plan = response.json()
    docid, document = next(
        (key, value)
        for key, value in project["documents"].items()
        if "deployment" in value["path"]
    )
    # Exact authored provenance references protect registration identity even if
    # that imported implementation itself has no admitted executable provider.
    content = (
        document["content"] + "\n# edit only invalidates the old filesystem proof\n"
    )
    saved = client.put(
        "/api/v1/projects/" + project["projectId"] + "/documents/" + docid,
        headers={"If-Match": str(project["revision"])},
        json={"content": content, "format": "yaml"},
    )
    assert saved.status_code == 200, saved.text
    applied = client.post(
        "/api/v1/retention/plans/" + plan["planId"] + "/apply",
        headers={"Idempotency-Key": "artifact-state-changed"},
        json={"fingerprint": plan["fingerprint"]},
    )
    assert applied.status_code == 409, applied.text
    assert client.get("/api/v1/catalog/" + registered["entryId"]).status_code == 200


@pytest.mark.parametrize(
    "history",
    [
        {"snapshots": [{"snapshotId": "s", "projectId": ["p"]}]},
        {"campaigns": [{"campaignId": "c", "baseSnapshot": []}]},
        {"snapshots": [{"snapshotId": "s"}]},
        {"runs": [{"runId": "r", "projectId": None}]},
    ],
)
def test_malformed_retained_project_links_never_prove_dependency_absence(history):
    with pytest.raises(ValueError, match="RETENTION_DEPENDENCIES_UNRESOLVED"):
        plan_retention(
            [], {"projects": [{"projectId": "p"}], **history}, project_ids=["p"]
        )


@pytest.mark.parametrize(
    "malformed",
    [
        {"runs": ["bad"]},
        {"runs": [{"runId": [], "state": "stopped"}]},
        {"runs": [{"runId": "r", "state": "not-a-state"}]},
        {
            "campaigns": [
                {
                    "campaignId": "c",
                    "baseSnapshot": {"projectId": "p"},
                    "children": ["bad"],
                }
            ]
        },
        {"evaluations": [{"evaluationId": "e", "runId": ["r"]}]},
    ],
)
def test_run_only_retention_validates_shapes_before_indexing(malformed):
    state = {"runs": [{"runId": "r", "state": "stopped"}], **malformed}
    with pytest.raises(ValueError, match="RETENTION_DEPENDENCIES_UNRESOLVED"):
        plan_retention(["r"], state)


@pytest.mark.parametrize(
    "content", ["null", "opaque scalar", "[]", "kind: Unknown\nspec: {}"]
)
def test_unrecognized_authored_source_cannot_prove_artifact_absence(content):
    with pytest.raises(ValueError, match="RETENTION_DEPENDENCIES_UNRESOLVED"):
        plan_retention(
            [],
            {
                "projects": [
                    {"projectId": "p", "documents": {"doc": {"content": content}}}
                ],
                "artifacts": [
                    {"entryId": "a", "digest": "sha256:a", "originRef": "urn:a"}
                ],
            },
            artifact_ids=["a"],
        )
