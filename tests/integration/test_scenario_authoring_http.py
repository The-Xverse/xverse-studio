"""HTTP scenario edits preserve source transactions and never dispatch actions."""

from copy import deepcopy
import subprocess

from ruamel.yaml import YAML


def test_scenario_authoring_http_revision_controls_and_no_execution(
    client, monkeypatch
):
    def forbidden(*args, **kwargs):
        raise AssertionError("Scenario authoring must not start a process")

    monkeypatch.setattr(subprocess, "Popen", forbidden)
    project = client.post(
        "/api/v1/projects", json={"name": "Scenario authoring"}
    ).json()
    pid = project["projectId"]
    docid = next(
        key
        for key, value in project["documents"].items()
        if YAML(typ="safe").load(value["content"])["kind"] == "Scenario"
    )
    original = deepcopy(project)
    spec = YAML(typ="safe").load(project["documents"][docid]["content"])["spec"]
    edit = {
        "kind": "add_scenario_item",
        "documentId": docid,
        "itemKind": "fault",
        "itemId": "authored-fault",
        "properties": {
            "targetRef": spec["steps"][0]["targetRef"],
            "faultKind": "opaque-provider-fault",
            "activation": "recorded intent only",
            "recovery": "recorded recovery only",
            "maturity": "prototype",
        },
    }
    response = client.post(
        f"/api/v1/projects/{pid}/edits",
        json={"baseRevision": 1, "edits": [edit]},
        headers={"If-Match": "1"},
    )
    assert response.status_code == 200, response.text
    changed = response.json()
    assert changed["revision"] == 2
    assert (
        changed["documents"][docid]["content"]
        != original["documents"][docid]["content"]
    )
    assert client.post(
        f"/api/v1/projects/{pid}/validations", json={"revision": 2}
    ).json()["valid"]
    preflight = client.post(f"/api/v1/projects/{pid}/preflights", json={"revision": 2})
    assert preflight.status_code == 200, preflight.text
    assert preflight.json()["status"] != "ready"
    assert client.get("/api/v1/runs").json()["items"] == []
    assert (
        client.get("/api/v1/capabilities").json()["limits"]["scenarioAuthoring"][
            "steps"
        ]
        == 64
    )
    assert (
        client.get("/api/v1/capabilities").json()["studio"]["windowsAcceptance"]
        == "BLOCKED_USER_REQUEST"
    )
    invalid = {
        "kind": "update_scenario_item",
        "documentId": docid,
        "itemKind": "step",
        "itemId": "start-reference",
        "properties": {"schedule": {"at": -1, "unit": "s"}},
    }
    rejected = client.post(
        f"/api/v1/projects/{pid}/edits",
        json={"baseRevision": 2, "edits": [invalid]},
        headers={"If-Match": "2"},
    )
    assert rejected.status_code == 422, rejected.text
    assert (
        client.get(f"/api/v1/projects/{pid}").json()["documents"]
        == changed["documents"]
    )
    stale = client.post(
        f"/api/v1/projects/{pid}/edits",
        json={"baseRevision": 1, "edits": [edit]},
        headers={"If-Match": "1"},
    )
    assert stale.status_code == 412, stale.text


def test_deep_scenario_patch_has_typed_http_limit_without_revising_project(client):
    project = client.post(
        "/api/v1/projects", json={"name": "Deep intent refusal"}
    ).json()
    pid = project["projectId"]
    value = {"leaf": "data"}
    for _ in range(600):
        value = {"nested": value}
    response = client.post(
        f"/api/v1/projects/{pid}/edits",
        headers={"If-Match": "1"},
        json={
            "baseRevision": 1,
            "edits": [
                {
                    "kind": "set_scenario_conditions",
                    "properties": {"initialConditions": value},
                }
            ],
        },
    )
    assert response.status_code == 422, response.text
    assert response.json()["code"] == "LIMIT_EXCEEDED"
    after = client.get(f"/api/v1/projects/{pid}").json()
    assert after["revision"] == 1
    assert after["documents"] == project["documents"]
