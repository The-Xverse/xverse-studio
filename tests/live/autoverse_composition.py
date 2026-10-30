"""Combined authoring/deployment/connection regression on enrolled Autoverse.

Static declarations and negative admission are not live execution. A separate
complete native/browser demo guards actual execution of the admitted baseline.
"""

from copy import deepcopy
import json
import sqlite3

import pytest
from ruamel.yaml import YAML

import autoverse_provider_admission as enrollment
from autoverse_provider_admission import application, authenticated, project
from xverse_studio.host.migration import migrate_full
from xverse_studio.projects.service import Projects
from xverse_studio.storage.core import Store, Problem
from xverse_studio.xdl.examples import dump_yaml
from xverse_studio.blueprints.autoverse import NAMESPACE

target = enrollment.target
SAFE = YAML(typ="safe")


def checked(response, status=200):
    assert response.status_code == status, response.text
    return response.json()


def forbidden(*args, **kwargs):
    raise AssertionError("Authoring inspection attempted runtime dispatch")


@pytest.fixture
def composed(target, tmp_path, monkeypatch):
    provider, blueprint = target
    app = application(tmp_path / "Autoverse composition Ω", provider)
    monkeypatch.setattr(app.state.studio.runs, "_dispatch", forbidden)
    with authenticated(app) as api:
        p = project(api, blueprint)
        yield app, api, provider, p
        assert app.state.studio.store.all("run") == []


def document(p, kind):
    return next(
        (key, doc)
        for key, doc in p["documents"].items()
        if SAFE.load(doc["content"]).get("kind") == kind
    )


def sources(p):
    return {d["path"]: d["content"] for d in p["documents"].values()}


def save(api, p, kind, change):
    key, doc = document(p, kind)
    value = SAFE.load(doc["content"])
    change(value)
    return checked(
        api.put(
            f"/api/v1/projects/{p['projectId']}/documents/{key}",
            headers={"If-Match": str(p["revision"])},
            json={"content": dump_yaml(value), "format": "yaml"},
        )
    )


def variants(api, p):
    first = checked(api.get(f"/api/v1/projects/{p['projectId']}/deployment-variants"))[
        "items"
    ][0]
    created = checked(
        api.post(
            f"/api/v1/projects/{p['projectId']}/deployment-variants",
            headers={"If-Match": str(p["revision"])},
            json={"baseRevision": p["revision"], "name": "Alternative Autoverse"},
        ),
        201,
    )
    return created["project"], first, created["variant"]


def test_actual_installed_provider_connection_admission_is_available(composed):
    app, api, provider, p = composed
    pid = provider.descriptor()["providerId"]
    discovered = next(
        v
        for v in checked(api.get("/api/v1/providers"))["items"]
        if v["providerId"] == pid
    )
    assert discovered["available"]
    report = checked(
        api.get(
            f"/api/v1/projects/{p['projectId']}/connections", params={"providerId": pid}
        )
    )
    assert report["providerId"] == pid and report["blocking"] == 0
    assert report["cycles"] and all(c["status"] == "admitted" for c in report["cycles"])
    assert all(c["admission"] == "admitted" for c in report["connections"])
    assert checked(api.get(f"/api/v1/projects/{p['projectId']}")) == p
    assert app.state.studio.store.all("snapshot") == []


def test_actual_installed_provider_resolution_is_available(composed):
    app, api, provider, p = composed
    variant = checked(
        api.get(f"/api/v1/projects/{p['projectId']}/deployment-variants")
    )["items"][0]
    report = checked(
        api.get(
            f"/api/v1/projects/{p['projectId']}/deployment-variants/{variant['documentId']}/resolution",
            params={
                "providerId": provider.descriptor()["providerId"],
                "revision": p["revision"],
            },
        )
    )
    assert (
        report["sourceValid"]
        and report["providerId"] == provider.descriptor()["providerId"]
    )
    assert report["connections"]["blocking"] == 0
    assert checked(api.get(f"/api/v1/projects/{p['projectId']}")) == p
    assert app.state.studio.store.all("snapshot") == []


def test_actual_installed_provider_comparison_is_coherent_and_read_only(
    composed, monkeypatch
):
    app, api, provider, p = composed
    p, first, second = variants(api, p)
    original = provider.descriptor
    captured = []

    def describe():
        value = deepcopy(original())
        captured.append(True)
        if len(captured) > 1:
            value["limits"]["maxElements"] += 1
        return value

    monkeypatch.setattr(provider, "descriptor", describe)
    report = checked(
        api.get(
            f"/api/v1/projects/{p['projectId']}/deployment-variants/{first['documentId']}/comparison",
            params={
                "providerId": original()["providerId"],
                "otherDocumentId": second["documentId"],
                "revision": p["revision"],
            },
        )
    )
    assert captured == [True]
    assert report["revision"] == p["revision"]
    for side in ("left", "right"):
        assert report[side]["resolution"]["providerId"] == original()["providerId"]
    assert checked(api.get(f"/api/v1/projects/{p['projectId']}")) == p
    assert app.state.studio.store.all("snapshot") == []


def test_noop_rebinding_uses_the_selected_installed_configuration(composed):
    app, api, provider, p = composed
    variant = checked(
        api.get(f"/api/v1/projects/{p['projectId']}/deployment-variants")
    )["items"][0]
    binding = variant["bindings"][0]
    result = checked(
        api.patch(
            f"/api/v1/projects/{p['projectId']}/deployment-variants/{variant['documentId']}",
            params={"providerId": provider.descriptor()["providerId"]},
            headers={"If-Match": str(p["revision"])},
            json={
                "baseRevision": p["revision"],
                "bindingId": binding["id"],
                "targetId": binding["targetId"],
            },
        )
    )
    assert result["compatibility"]["status"] == "preflight_required", result[
        "compatibility"
    ]
    assert (
        app.state.studio.adapter.compile(sources(result["project"]))["planDigest"]
        == app.state.studio.adapter.compile(sources(p))["planDigest"]
    )


@pytest.mark.parametrize("route", ["connections", "resolution", "comparison"])
def test_unknown_provider_never_falls_back_to_a_builtin(composed, route):
    _, api, _, p = composed
    p, first, second = variants(api, p)
    base = f"/api/v1/projects/{p['projectId']}"
    path = base + (
        "/connections"
        if route == "connections"
        else f"/deployment-variants/{first['documentId']}/{route}"
    )
    params = {"providerId": "missing.enrolled.provider", "revision": p["revision"]}
    if route == "comparison":
        params["otherDocumentId"] = second["documentId"]
    response = api.get(path, params=params)
    assert (
        response.status_code == 404
        and response.json()["code"] == "PROVIDER_UNAVAILABLE"
    )
    assert checked(api.get(base)) == p


@pytest.mark.parametrize(
    "fault",
    [
        "direction",
        "interface",
        "converter",
        "quality",
        "multiplicity",
        "feedback",
        "coupling",
    ],
)
def test_actual_autoverse_connection_negatives_block_without_dispatch(composed, fault):
    app, api, provider, p = composed

    def change(value):
        spec = value["spec"]
        flow = spec["flows"][0]
        interface = next(
            i for i in spec["interfaces"] if i["id"] == flow["interfaceId"]
        )
        if fault == "direction":
            flow["sourceEndpointId"] = flow["destinationEndpointIds"][0]
        elif fault == "interface":
            flow["interfaceId"] = next(
                i["id"] for i in spec["interfaces"] if i["id"] != flow["interfaceId"]
            )
        elif fault == "converter":
            interface["compatibility"] = "explicit-converter"
        elif fault == "quality":
            flow["quality"] = {"latencyBound": {"value": 10, "unit": "ms"}}
        elif fault == "multiplicity":
            next(e for e in spec["endpoints"] if e["id"] == flow["sourceEndpointId"])[
                "multiplicity"
            ] = "exactly-one"
        elif fault == "feedback":
            value["extensions"].pop(NAMESPACE)
        elif fault == "coupling":
            spec.setdefault("models", []).append(
                {
                    "id": "unavailable-coupling",
                    "modelKind": "physical",
                    "externalRef": "urn:example:coupling:unavailable",
                    "inputs": [interface["id"]],
                    "outputs": [interface["id"]],
                    "maturity": "prototype",
                }
            )

    p = save(api, p, "System", change)
    report = checked(
        api.get(
            f"/api/v1/projects/{p['projectId']}/connections",
            params={"providerId": provider.descriptor()["providerId"]},
        )
    )
    assert report["blocking"] > 0
    if fault == "coupling":
        assert report["couplings"][0]["code"] == "MODEL_COUPLING_UNSUPPORTED"
    pf = checked(
        api.post(
            f"/api/v1/projects/{p['projectId']}/preflights",
            json={
                "revision": p["revision"],
                "providerId": provider.descriptor()["providerId"],
            },
        )
    )
    assert pf["status"] == "blocked"
    refused = api.post(
        "/api/v1/runs",
        headers={"Idempotency-Key": "unsupported-authored-connection"},
        json={k: pf[k] for k in ("snapshotId", "preflightId")},
    )
    assert refused.status_code == 422 and refused.json()["code"] == "ADMISSION_REJECTED"
    assert app.state.studio.store.all("operation") == []


def test_actual_autoverse_authoring_layout_conflict_and_restore_share_identity(
    composed,
):
    app, api, provider, p = composed
    original = deepcopy(p)
    _, doc = document(p, "System")
    layout = {
        "positions": {"vcu": {"x": 21.5, "y": -7.0}},
        "viewport": {"x": 0, "y": 0, "zoom": 1},
    }
    moved = checked(
        api.put(
            f"/api/v1/projects/{p['projectId']}/layout",
            headers={"If-Match": str(p["presentationRevision"])},
            json=layout,
        )
    )
    assert moved["revision"] == p["revision"] and moved["documents"] == p["documents"]
    before = app.state.studio.adapter.compile(sources(p))
    assert (
        app.state.studio.adapter.compile(sources(moved))["planDigest"]
        == before["planDigest"]
    )
    p = checked(
        api.post(
            f"/api/v1/projects/{p['projectId']}/edits",
            headers={"If-Match": str(p["revision"])},
            json={
                "baseRevision": p["revision"],
                "edits": [
                    {
                        "kind": "rename_display_label",
                        "documentId": doc["path"],
                        "label": "Autoverse authored display Ω",
                    }
                ],
            },
        )
    )
    library = app.state.studio.adapter.compile(sources(p))
    assert library["valid"]
    http = checked(
        api.post(
            f"/api/v1/projects/{p['projectId']}/compilations",
            json={
                "revision": p["revision"],
                "providerId": provider.descriptor()["providerId"],
            },
        )
    )
    assert (
        http["planDigest"] == library["planDigest"]
        and http["semanticDigest"] == library["semanticDigest"]
    )
    stale = api.post(
        f"/api/v1/projects/{p['projectId']}/edits",
        headers={"If-Match": str(original["revision"])},
        json={
            "baseRevision": original["revision"],
            "edits": [
                {
                    "kind": "rename_display_label",
                    "documentId": doc["path"],
                    "label": "Stale display",
                }
            ],
        },
    )
    assert (
        stale.status_code == 412
        and checked(api.get(f"/api/v1/projects/{p['projectId']}")) == p
    )
    restored = checked(
        api.post(
            f"/api/v1/projects/{p['projectId']}/revisions/{original['revision']}/restore",
            headers={"If-Match": str(p["revision"])},
        )
    )
    assert (
        restored["revision"] > p["revision"]
        and restored["documents"] == original["documents"]
        and restored["layout"] == layout
    )
    assert (
        app.state.studio.adapter.compile(sources(restored))["planDigest"]
        == before["planDigest"]
    )


def inventory(root):
    return {
        p.relative_to(root).as_posix(): p.read_bytes()
        for p in root.rglob("*")
        if p.is_file() and p.name != "studio.lock"
    }


def test_known_metadata_copy_migration_preserves_actual_autoverse_semantics(
    target, tmp_path
):
    provider, blueprint = target
    source, backup, destination = (
        tmp_path / n for n in ["Autoverse original Ω", "Backup Ω", "Migrated Ω"]
    )
    app = application(source, provider)
    with authenticated(app) as api:
        p = project(api, blueprint)
        before = app.state.studio.adapter.compile(sources(p))
        assert before["valid"]
    with sqlite3.connect(source / "studio.sqlite") as db:
        db.execute("PRAGMA journal_mode=DELETE")
        db.execute("PRAGMA user_version=0")
    original = inventory(source)
    with pytest.raises(Problem) as error:
        Store(source)
    assert error.value.code == "MIGRATION_REQUIRED" and inventory(source) == original
    result = migrate_full(source, backup, destination)
    assert result["status"] == "migrated" and inventory(source) == original
    projects = Projects(Store(destination), app.state.studio.adapter)
    migrated = projects.read(p["projectId"])
    after = projects.adapter.compile(projects.sources(migrated))
    assert (
        migrated == p
        and after["planDigest"] == before["planDigest"]
        and after["semanticDigest"] == before["semanticDigest"]
    )
    assert projects.store.all("session") == []
    report = json.loads((destination / "migration-report.json").read_text())
    assert (
        report["sourceSchema"] == 0
        and report["targetSchema"] == 1
        and report["semanticDiff"]["unchanged"]
    )
    for name, raw in original.items():
        if name != "studio.sqlite":
            assert (destination / name).read_bytes() == raw
