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


@pytest.mark.parametrize("layer", ["default", "instance", "conflict"])
def test_actual_autoverse_parameter_sources_never_invent_precedence(composed, layer):
    app, api, provider, p = composed
    _, component = document(p, "Component")
    definition = SAFE.load(component["content"])["metadata"]["name"]
    p = save(
        api,
        p,
        "Component",
        lambda r: r["spec"].update(
            parameters=[
                {
                    "id": "review-rate",
                    "valueType": "number",
                    "unitSemantics": "1/s",
                    "default": 1.0,
                    "mutability": "configuration",
                }
            ]
        ),
    )
    _, system = document(p, "System")
    instance = next(
        e["id"]
        for e in SAFE.load(system["content"])["spec"]["componentInstances"]
        if e["componentRef"]["name"] == definition
    )
    if layer != "default":

        def instance_value(r):
            next(e for e in r["spec"]["componentInstances"] if e["id"] == instance)[
                "parameterValues"
            ] = {"review-rate": 2.0}

        p = save(api, p, "System", instance_value)
    if layer == "conflict":

        def binding_value(r):
            next(
                b
                for b in r["spec"]["bindings"]
                if b["logicalRef"]["element"] == instance
            )["parameterValues"] = {"review-rate": 3.0}

        p = save(api, p, "Deployment", binding_value)
    variant = checked(
        api.get(f"/api/v1/projects/{p['projectId']}/deployment-variants")
    )["items"][0]
    report = checked(
        api.get(
            f"/api/v1/projects/{p['projectId']}/deployment-variants/{variant['documentId']}/resolution",
            params={"providerId": provider.descriptor()["providerId"]},
        )
    )
    entry = next(
        x
        for x in report["parameters"]
        if x["elementId"] == instance and x["parameterId"] == "review-rate"
    )
    assert [x["value"] for x in entry["chain"]] == {
        "default": [1],
        "instance": [1, 2],
        "conflict": [1, 2, 3],
    }[layer]
    if layer == "conflict":
        assert (
            entry["status"] == "ambiguous"
            and entry["code"] == "PRECEDENCE_UNDEFINED"
            and entry["effective"] is None
        )
    else:
        assert entry["effective"] == (1 if layer == "default" else 2)
        assert entry["source"] == (
            "definition-default" if layer == "default" else "system-instance"
        )
    assert app.state.studio.store.all("snapshot") == []


def test_actual_autoverse_resource_and_environment_declarations_stay_unexecuted(
    composed,
):
    app, api, provider, p = composed
    original_system = document(p, "System")[1]["content"]

    def constrained(r):
        spec = r["spec"]
        spec["resources"] = [
            {
                "id": "exclusive-review-gpu",
                "resourceClass": "gpu",
                "capacity": {"value": 1, "unit": "device"},
                "allocationPolicy": "exclusive",
            }
        ]
        for binding in spec["bindings"]:
            binding["resourceIds"] = ["exclusive-review-gpu"]
        spec["resources"].append(
            {
                "id": "review-spare",
                "resourceClass": "storage",
                "capacity": {"value": 1, "unit": "GiB"},
                "allocationPolicy": "quota",
            }
        )
        for target in spec["targets"]:
            target["offeredResourceIds"] = ["review-spare"]
        spec["bindings"][0]["secretRefs"] = ["secret://review-only/external-handle"]
        spec["bindings"][0]["parameterValues"] = {
            "cache": "/var/cache/declared-autoverse-review"
        }

    p = save(api, p, "Deployment", constrained)
    variant = checked(
        api.get(f"/api/v1/projects/{p['projectId']}/deployment-variants")
    )["items"][0]
    report = checked(
        api.get(
            f"/api/v1/projects/{p['projectId']}/deployment-variants/{variant['documentId']}/resolution",
            params={"providerId": provider.descriptor()["providerId"]},
        )
    )
    codes = {d["code"] for d in report["diagnostics"]}
    assert {"RESOURCE_CONFLICT", "RESOURCE_NOT_OFFERED", "BINDING_UNRESOLVED"} <= codes
    assert any(
        e["kind"] == "secret" and e["status"] == "unresolved"
        for e in report["environment"]
    )
    assert "secret://" not in json.dumps(report["portableIntent"])
    assert any(c["pointer"].endswith("/cache") for c in report["portability"])
    assert (
        document(p, "System")[1]["content"] == original_system
        and app.state.studio.store.all("snapshot") == []
    )


def test_actual_autoverse_compatible_domain_profiles_and_conflicting_lock_are_inert(
    composed,
):
    app, api, _, p = composed
    topology = document(p, "System")[1]["content"]
    available = checked(api.get("/api/v1/profiles"))["items"]
    chosen = [
        v
        for v in available
        if v["profileId"]
        in {
            "io.xverse.experiment",
            "io.xverse.studio.native-runtime",
            "io.xverse.studio.domain.automotive",
            "io.xverse.studio.domain.process-control",
        }
    ]
    assert len(chosen) == 4
    locks = [
        {
            k: v[k]
            for k in ("profileId", "version", "schemaDigest", "presentationDigest")
        }
        for v in chosen
    ]
    p = checked(
        api.post(
            f"/api/v1/projects/{p['projectId']}/profile-bindings",
            headers={"If-Match": str(p["revision"])},
            json={"baseRevision": p["revision"], "profiles": locks},
        )
    )
    assert document(p, "System")[1]["content"] == topology
    assert app.state.studio.adapter.validate(sources(p))["valid"]
    assert {x["namespace"] for x in p["manifest"]["profiles"]} == {
        x["profileId"] for x in locks
    }
    altered = deepcopy(locks)
    altered[0]["schemaDigest"] = "sha256:" + "0" * 64
    refused = api.post(
        f"/api/v1/projects/{p['projectId']}/profile-bindings",
        headers={"If-Match": str(p["revision"])},
        json={"baseRevision": p["revision"], "profiles": altered},
    )
    assert (
        refused.status_code == 422
        and checked(api.get(f"/api/v1/projects/{p['projectId']}")) == p
    )
    assert app.state.studio.store.all("snapshot") == []


def test_actual_autoverse_unknown_xdl_version_remains_exact_and_blocked(composed):
    app, api, provider, p = composed
    key, source = document(p, "System")
    value = SAFE.load(source["content"])
    value["apiVersion"] = "xverse.io/xdl/v99"
    raw = dump_yaml(value)
    p = checked(
        api.put(
            f"/api/v1/projects/{p['projectId']}/documents/{key}",
            headers={"If-Match": str(p["revision"])},
            json={"content": raw},
        )
    )
    assert p["documents"][key]["content"] == raw
    report = checked(
        api.post(
            f"/api/v1/projects/{p['projectId']}/compilations",
            json={
                "revision": p["revision"],
                "providerId": provider.descriptor()["providerId"],
            },
        )
    )
    assert report["valid"] is False
    assert (
        checked(api.get(f"/api/v1/projects/{p['projectId']}"))["documents"][key][
            "content"
        ]
        == raw
    )
    assert app.state.studio.store.all("snapshot") == []


def test_actual_autoverse_external_source_conflict_preserves_and_recovers_bytes(
    composed,
):
    app, api, _, p = composed
    key, doc = document(p, "System")
    path = (
        app.state.studio.store.root
        / "projects"
        / p["projectId"]
        / "revisions"
        / str(p["revision"])
        / doc["path"]
    )
    external = "# External inert edit Ω\n" + doc["content"]
    path.write_text(external)
    refused = api.put(
        f"/api/v1/projects/{p['projectId']}/documents/{key}",
        headers={"If-Match": str(p["revision"])},
        json={"content": doc["content"]},
    )
    assert (
        refused.status_code == 412
        and refused.json()["code"] == "REVISION_CONFLICT"
        and path.read_text() == external
    )
    result = checked(
        api.post(
            f"/api/v1/projects/{p['projectId']}/recoveries",
            headers={"If-Match": str(p["revision"])},
            json={"expectedRevision": p["revision"], "action": "adopt_external"},
        )
    )
    adopted = result["project"]
    assert (
        adopted["documents"][key]["content"] == external
        and adopted["revision"] > p["revision"]
    )
    preserved = checked(
        api.get(
            f"/api/v1/projects/{p['projectId']}/recoveries/{result['recovery']['recoveryId']}/preserved",
            params={"key": "document:" + key},
        )
    )
    assert preserved["content"] == external
    assert (
        app.state.studio.adapter.compile(sources(adopted))["planDigest"]
        == app.state.studio.adapter.compile(sources(p))["planDigest"]
    )


@pytest.mark.parametrize("fault", ["network", "clock", "placement", "artifact"])
def test_actual_autoverse_deployment_constraints_block_direct_start(composed, fault):
    app, api, provider, p = composed
    topology = document(p, "System")[1]["content"]
    system = SAFE.load(topology)
    ref = {
        "apiVersion": system["apiVersion"],
        "kind": "System",
        "namespace": system["metadata"]["namespace"],
        "name": system["metadata"]["name"],
    }
    expected = {
        "network": "NETWORK_BINDING_CONFLICT",
        "clock": "CLOCK_MAPPING_MISSING",
        "placement": "CAPABILITY_UNSUPPORTED",
        "artifact": "ARTIFACT_REQUIREMENT_UNMET",
    }[fault]
    if fault == "network":
        p = save(
            api,
            p,
            "System",
            lambda r: r["spec"].update(
                networks=[
                    {"id": "review-bus", "scope": "review", "capabilities": ["ordered"]}
                ]
            ),
        )
        _, profile = document(p, "Profile")
        profile = SAFE.load(profile["content"])
        profile_ref = {
            "apiVersion": profile["apiVersion"],
            "kind": "Profile",
            "namespace": profile["metadata"]["namespace"],
            "name": profile["metadata"]["name"],
        }
        p = save(
            api,
            p,
            "Deployment",
            lambda r: r["spec"].update(
                networkBindings=[
                    {
                        "id": name,
                        "logicalNetworkRef": {**ref, "element": "review-bus"},
                        "profileRef": profile_ref,
                        "limitations": ["Static review declaration only."],
                    }
                    for name in ["review-a", "review-b"]
                ]
            ),
        )
    elif fault == "clock":
        p = save(
            api,
            p,
            "System",
            lambda r: r["spec"]["timeDomains"].append(
                {
                    "id": "review-wall",
                    "clockClass": "wall",
                    "epoch": "unix",
                    "rate": "1",
                    "monotonic": False,
                }
            ),
        )
        p = save(
            api,
            p,
            "Deployment",
            lambda r: r["spec"].update(
                simulators=[
                    {
                        "id": "review-simulator",
                        "standardRef": "urn:standard:fmi:3.0",
                        "artifactId": "autoverse-contract",
                        "timeDomainId": "review-wall",
                    }
                ]
            ),
        )
    elif fault == "placement":
        p = save(
            api,
            p,
            "Deployment",
            lambda r: r["spec"]["targets"][0].update(targetClass="virtual-machine"),
        )
    else:
        p = save(
            api,
            p,
            "Component",
            lambda r: r["spec"].update(
                artifactRequirements=[
                    {
                        "id": "review-firmware",
                        "artifactKind": "firmware",
                        "versionConstraint": "1.0.0",
                    }
                ]
            ),
        )
    # XDL must still be valid: these are semantic compatibility negatives.
    validation = app.state.studio.adapter.validate(sources(p))
    assert validation["valid"], validation
    v = checked(api.get(f"/api/v1/projects/{p['projectId']}/deployment-variants"))[
        "items"
    ][0]
    report = checked(
        api.get(
            f"/api/v1/projects/{p['projectId']}/deployment-variants/{v['documentId']}/resolution",
            params={"providerId": provider.descriptor()["providerId"]},
        )
    )
    assert expected in {d["code"] for d in report["diagnostics"]}
    pf = checked(
        api.post(
            f"/api/v1/projects/{p['projectId']}/preflights",
            json={
                "revision": p["revision"],
                "providerId": provider.descriptor()["providerId"],
            },
        )
    )
    assert pf["status"] == "blocked" and expected in {
        d["code"] for d in pf["diagnostics"]
    }
    refused = api.post(
        "/api/v1/runs",
        headers={"Idempotency-Key": "unsupported-deployment-review"},
        json={k: pf[k] for k in ("snapshotId", "preflightId")},
    )
    assert refused.status_code == 422 and refused.json()["code"] == "ADMISSION_REJECTED"
    assert app.state.studio.store.all("operation") == []
