"""Reported external claims are inert, revisioned metadata, never verdicts."""

from copy import deepcopy
import base64
import io
import json
import zipfile

import pytest

from xverse_studio.annotations import (
    AnnotationError,
    create_annotation,
    revise_annotation,
)
from xverse_studio.storage.core import digest


def claim(status="Externally accepted / pending recheck"):
    return {
        "kind": "trace_link",
        "target": {
            "uri": "urn:test:requirement:17",
            "revision": "external-r7",
            "claimStatus": status,
        },
    }


def test_reported_claim_is_preserved_exactly_without_verdict_or_legacy_rewrite():
    legacy = create_annotation(
        "run",
        {
            "kind": "trace_link",
            "target": {"uri": "urn:test:legacy:1", "revision": "unknown"},
        },
        author="operator",
    )
    original = deepcopy(legacy)
    updated = revise_annotation(
        legacy, claim("  Accepted externally  "), expected_revision=1, author="reviewer"
    )
    assert legacy == original
    assert updated["history"] == [{k: v for k, v in original.items() if k != "history"}]
    assert updated["target"]["claimStatus"] == "  Accepted externally  "
    assert updated["history"][0]["target"] == {
        "uri": "urn:test:legacy:1",
        "revision": "unknown",
    }
    assert "claimStatus" not in legacy["target"]
    assert not {"verdict", "proof", "evaluation"} & updated.keys()
    removed = revise_annotation(
        updated,
        {"kind": "comment", "text": "Link removed explicitly"},
        expected_revision=2,
        author="reviewer",
    )
    assert removed["target"] is None
    assert removed["history"][1]["target"]["claimStatus"] == "  Accepted externally  "


@pytest.mark.parametrize(
    "status",
    ["", "   ", None, True, 7, {}, [], "x" * 257, "line\nbreak", "control\x7f"],
)
def test_invalid_reported_status_rejects_without_coercion(status):
    with pytest.raises(AnnotationError, match="TRACE_TARGET_INVALID"):
        create_annotation("run", claim(status), author="operator")


def test_definition_subject_is_revisioned_and_replacement_can_clear_it():
    refs = [
        {"definitionRef": "bounded-state", "definitionDigest": "sha256:" + "a" * 64}
    ]
    initial = create_annotation(
        "run", {**claim(), "definitionRefs": refs}, author="operator"
    )
    assert initial["definitionRefs"] == refs
    refs[0]["definitionRef"] = "changed-input"
    assert initial["definitionRefs"][0]["definitionRef"] == "bounded-state"
    revised = revise_annotation(
        initial, claim("reported waived"), expected_revision=1, author="operator"
    )
    assert not revised.get("definitionRefs")
    assert revised["history"][0]["definitionRefs"] == initial["definitionRefs"]


@pytest.mark.parametrize(
    "refs",
    [
        None,
        {},
        [{}],
        [{"definitionRef": "id", "definitionDigest": "sha256:bad"}],
        [
            {
                "definitionRef": "id",
                "definitionDigest": "sha256:" + "a" * 64,
                "extra": "invalid",
            }
        ],
    ],
)
def test_malformed_definition_refs_reject(refs):
    with pytest.raises(AnnotationError):
        create_annotation("run", {**claim(), "definitionRefs": refs}, author="operator")


def test_frozen_subject_claim_http_revision_and_evidence_exchange(client):
    from test_advanced_api import prepared, start, wait_run

    project, preflight = prepared(client)
    rid = start(client, preflight, "trace-claim-run")
    run = wait_run(client, rid)
    assert run["state"] == "stopped", run
    store = client.app.state.studio.store
    snapshot = deepcopy(store.get("snapshot", preflight["snapshotId"]))
    run_dir = client.app.state.studio.runs.directory(rid)
    source_hashes = {
        str(p.relative_to(run_dir)): digest(p.read_bytes())
        for p in run_dir.rglob("*")
        if p.is_file()
    }
    definition = client.get(f"/api/v1/runs/{rid}/definitions").json()["items"][0]
    graph = client.app.state.studio.adapter.project(snapshot["documents"])
    model_ref = graph["elements"][0]["ref"]
    scenario_ref = next(r["ref"] for r in graph["resources"] if r["kind"] == "Scenario")
    refs = [
        {
            "definitionRef": definition["definitionRef"],
            "definitionDigest": definition["definitionDigest"],
        }
    ]
    body = {
        **claim("External team says passed"),
        "definitionRefs": refs,
        "elementRefs": [model_ref, scenario_ref],
        "evidenceRefs": [rid + ":reference-journal"],
    }
    response = client.post(f"/api/v1/runs/{rid}/annotations", json=body)
    assert response.status_code == 201, response.text
    original = response.json()
    assert original["definitionRefs"] == refs
    assert original["target"]["claimStatus"] == "External team says passed"
    assert client.get("/api/v1/runs/" + rid).json()["verdict"] is None
    assert store.get("snapshot", preflight["snapshotId"]) == snapshot
    assert {
        str(p.relative_to(run_dir)): digest(p.read_bytes())
        for p in run_dir.rglob("*")
        if p.is_file()
    } == source_hashes
    # Changing current authored definitions cannot reinterpret the frozen subject.
    did, doc = next(
        (k, v) for k, v in project["documents"].items() if "scenario" in v["path"]
    )
    saved = client.put(
        f"/api/v1/projects/{project['projectId']}/documents/{did}",
        headers={"If-Match": str(project["revision"])},
        json={
            "content": doc["content"].replace(
                "state-within-bound", "renamed-current-definition"
            ),
            "format": "yaml",
        },
    )
    assert saved.status_code == 200, saved.text
    changed = client.put(
        "/api/v1/annotations/" + original["annotationId"],
        headers={"If-Match": "1"},
        json={
            **body,
            "target": {
                **body["target"],
                "claimStatus": "External team now says waived",
            },
            "revision": 1,
        },
    )
    assert changed.status_code == 200, changed.text
    latest = changed.json()
    assert latest["history"] == [{k: v for k, v in original.items() if k != "history"}]
    assert latest["definitionRefs"] == refs
    stale = client.put(
        "/api/v1/annotations/" + original["annotationId"],
        headers={"If-Match": "1"},
        json={**body, "revision": 1},
    )
    assert stale.status_code == 412
    for bad in (
        [
            {
                "definitionRef": definition["definitionRef"],
                "definitionDigest": "sha256:" + "0" * 64,
            }
        ],
        [
            {
                "definitionRef": "missing-definition",
                "definitionDigest": definition["definitionDigest"],
            }
        ],
    ):
        rejected = client.post(
            f"/api/v1/runs/{rid}/annotations", json={**body, "definitionRefs": bad}
        )
        assert rejected.status_code == 422, rejected.text
    fresh_preflight = client.post(
        f"/api/v1/projects/{project['projectId']}/preflights",
        json={"revision": saved.json()["revision"]},
    )
    assert fresh_preflight.status_code == 200, fresh_preflight.text
    other_id = start(client, fresh_preflight.json(), "trace-claim-other-run")
    assert wait_run(client, other_id)["state"] == "stopped"
    other_definition = client.get(f"/api/v1/runs/{other_id}/definitions").json()[
        "items"
    ][0]
    assert other_definition["definitionRef"] != definition["definitionRef"]
    cross = client.post(
        f"/api/v1/runs/{rid}/annotations",
        json={
            **body,
            "definitionRefs": [
                {
                    "definitionRef": other_definition["definitionRef"],
                    "definitionDigest": other_definition["definitionDigest"],
                }
            ],
        },
    )
    assert cross.status_code == 422, cross.text
    wrong_subject = client.post(
        f"/api/v1/runs/{rid}/annotations",
        json={**body, "elementRefs": ["xdl://other/system/unknown#outside"]},
    )
    assert wrong_subject.status_code == 422, wrong_subject.text
    deleted = client.delete(
        "/api/v1/annotations/" + original["annotationId"], headers={"If-Match": "2"}
    )
    assert deleted.status_code == 200, deleted.text
    latest = deleted.json()
    assert latest["deleted"] and latest["revision"] == 3
    assert latest["target"]["claimStatus"] == "External team now says waived"
    assert [row["target"]["claimStatus"] for row in latest["history"]] == [
        "External team says passed",
        "External team now says waived",
    ]
    legacy_response = client.post(
        f"/api/v1/runs/{rid}/annotations",
        json={
            "kind": "trace_link",
            "target": {"uri": "urn:test:legacy:1", "revision": "unknown"},
        },
    )
    assert legacy_response.status_code == 201, legacy_response.text
    legacy = legacy_response.json()
    assert legacy["target"] == {"uri": "urn:test:legacy:1", "revision": "unknown"}
    assert "definitionRefs" not in legacy
    exported = client.post(
        f"/api/v1/runs/{rid}/exports",
        headers={"Idempotency-Key": "trace-claims-export"},
        json={},
    )
    assert exported.status_code == 202, exported.text
    data = client.get(exported.json()["result"]["downloadUrl"]).content
    with zipfile.ZipFile(io.BytesIO(data)) as archive:
        rows = json.loads(archive.read("annotations.json"))
    assert {row["annotationId"]: row for row in rows} == {
        row["annotationId"]: row for row in [latest, legacy]
    }
    before_runs = len(client.get("/api/v1/runs").json()["items"])
    imported = client.post(
        "/api/v1/evidence/imports",
        json={"archiveBase64": base64.b64encode(data).decode()},
    )
    assert imported.status_code == 201, imported.text
    assert imported.json()["annotations"] == rows
    assert imported.json()["inspection"]["executionAllowed"] is False
    assert len(client.get("/api/v1/runs").json()["items"]) == before_runs
    assert client.get("/api/v1/runs/" + rid).json()["verdict"] is None
    assert store.get("snapshot", preflight["snapshotId"]) == snapshot
    before_annotations = deepcopy(store.all("annotation"))
    tampered = {**snapshot, "semanticDigest": "sha256:tampered-snapshot"}
    store.put("snapshot", preflight["snapshotId"], tampered)
    try:
        rejected = client.post(
            f"/api/v1/runs/{rid}/annotations",
            json={**claim(), "elementRefs": [model_ref]},
        )
        assert (
            rejected.status_code == 422
            and rejected.json()["code"] == "SNAPSHOT_INTEGRITY_INVALID"
        ), rejected.text
        assert store.all("annotation") == before_annotations
    finally:
        store.put("snapshot", preflight["snapshotId"], snapshot)
    assert {
        str(p.relative_to(run_dir)): digest(p.read_bytes())
        for p in run_dir.rglob("*")
        if p.is_file()
    } == source_hashes
    # A self-consistent rehash of changed SQL metadata is still not the original
    # immutable file, and must not admit a forged assertion association.
    from io import StringIO
    from ruamel.yaml import YAML
    from xverse_studio.assertions import snapshot_definitions

    forged = deepcopy(snapshot)
    source_name = next(name for name in forged["documents"] if "scenario" in name)
    yaml = YAML()
    resource = yaml.load(forged["documents"][source_name])
    resource["extensions"]["io.xverse.studio.experiments"]["definitions"][0][
        "evaluationId"
    ] = "forged-metadata-only"
    output = StringIO()
    yaml.dump(resource, output)
    forged["documents"][source_name] = output.getvalue()
    forged.pop("snapshotDigest")
    forged["snapshotDigest"] = digest(forged)
    forged_definition = snapshot_definitions(forged, client.app.state.studio.adapter)[0]
    store.put("snapshot", preflight["snapshotId"], forged)
    try:
        for subject in (
            {"elementRefs": [model_ref]},
            {
                "definitionRefs": [
                    {
                        "definitionRef": forged_definition["definitionRef"],
                        "definitionDigest": forged_definition["definitionDigest"],
                    }
                ]
            },
        ):
            refused = client.post(
                f"/api/v1/runs/{rid}/annotations", json={**claim(), **subject}
            )
            assert (
                refused.status_code == 422
                and refused.json()["code"] == "SNAPSHOT_INTEGRITY"
            ), refused.text
        assert store.all("annotation") == before_annotations
    finally:
        store.put("snapshot", preflight["snapshotId"], snapshot)
    # Source unavailability still permits inert legacy commentary with no model
    # or assertion subject. No historical source bytes are regenerated.
    snapshot_file = store.root / "snapshots" / preflight["snapshotId"] / "snapshot.json"
    held = snapshot_file.with_suffix(".held")
    snapshot_file.rename(held)
    try:
        comment = client.post(
            f"/api/v1/runs/{rid}/annotations",
            json={
                "kind": "comment",
                "text": "Original sources temporarily unavailable",
            },
        )
        assert comment.status_code == 201, comment.text
        inert = client.post(f"/api/v1/runs/{rid}/annotations", json=claim())
        assert inert.status_code == 201, inert.text
        refused = client.post(
            f"/api/v1/runs/{rid}/annotations",
            json={**claim(), "elementRefs": [model_ref]},
        )
        assert (
            refused.status_code == 422
            and refused.json()["code"] == "SNAPSHOT_INTEGRITY"
        ), refused.text
    finally:
        held.rename(snapshot_file)


def test_reported_pass_does_not_override_evaluated_failure(client):
    from io import StringIO
    from ruamel.yaml import YAML
    from test_advanced_api import prepared, start, wait_run

    project, _ = prepared(client)
    did, doc = next(
        (k, v) for k, v in project["documents"].items() if "scenario" in v["path"]
    )
    yaml = YAML()
    resource = yaml.load(doc["content"])
    resource["extensions"]["io.xverse.studio.experiments"]["definitions"][0][
        "expression"
    ]["right"]["value"] = -1
    output = StringIO()
    yaml.dump(resource, output)
    saved = client.put(
        f"/api/v1/projects/{project['projectId']}/documents/{did}",
        headers={"If-Match": str(project["revision"])},
        json={"content": output.getvalue(), "format": "yaml"},
    )
    assert saved.status_code == 200, saved.text
    pf = client.post(
        f"/api/v1/projects/{project['projectId']}/preflights",
        json={"revision": saved.json()["revision"]},
    )
    assert pf.status_code == 200, pf.text
    rid = start(client, pf.json(), "reported-pass-actual-fail")
    assert wait_run(client, rid)["state"] == "stopped"
    definition = client.get(f"/api/v1/runs/{rid}/definitions").json()["items"][0]
    evaluation = client.post(
        f"/api/v1/runs/{rid}/evaluations",
        headers={"Idempotency-Key": "actual-failing-assessment"},
        json={
            "snapshotId": pf.json()["snapshotId"],
            "definitionRef": definition["definitionRef"],
            "definitionDigest": definition["definitionDigest"],
            "evidenceRefs": [rid + ":reference-journal"],
        },
    )
    assert evaluation.status_code == 202, evaluation.text
    evaluated = client.get(
        "/api/v1/evaluations/" + evaluation.json()["evaluationId"]
    ).json()
    assert evaluated["verdict"] == "fail", evaluated
    store = client.app.state.studio.store
    snapshot = deepcopy(store.get("snapshot", pf.json()["snapshotId"]))
    response = client.post(
        f"/api/v1/runs/{rid}/annotations",
        json={
            **claim("Passed according to external tracker"),
            "definitionRefs": [
                {
                    "definitionRef": definition["definitionRef"],
                    "definitionDigest": definition["definitionDigest"],
                }
            ],
        },
    )
    assert response.status_code == 201, response.text
    assert client.get("/api/v1/runs/" + rid).json()["verdict"] == "fail"
    assert (
        client.get("/api/v1/evaluations/" + evaluation.json()["evaluationId"]).json()
        == evaluated
    )
    assert store.get("snapshot", pf.json()["snapshotId"]) == snapshot
    assert (
        client.get(f"/api/v1/runs/{rid}/annotations").json()["items"][0]["target"][
            "claimStatus"
        ]
        == "Passed according to external tracker"
    )
