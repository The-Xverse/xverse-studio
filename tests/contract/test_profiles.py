import pytest

from xverse_studio.profiles import ProfileRegistry
from xverse_studio.projects.service import Projects
from xverse_studio.storage.core import Problem, Store
from xverse_studio.xdl import XDLAdapter


def test_admitted_profile_lock_materializes_exact_local_schema_and_preserves_execution(tmp_path):
    adapter = XDLAdapter()
    projects = Projects(Store(tmp_path), adapter)
    project = projects.create("Profile binding")
    registry = ProfileRegistry(adapter)
    admitted = registry.list()["items"]
    locks = [{key: entry[key] for key in ("profileId", "version", "schemaDigest", "presentationDigest")} for entry in admitted]
    before = adapter.compile(projects.sources(project))
    updated = registry.bind(projects, project["projectId"], 1, locks)
    assert updated["revision"] == 2
    assert len(updated["manifest"]["profiles"]) == len(registry.list()["items"]) == 6
    for lock in updated["manifest"]["profiles"]:
        assert lock["schemaPath"] in updated["supportingFiles"]
        assert lock["presentationPath"] in updated["supportingFiles"]
    after = adapter.compile(projects.sources(updated))
    assert after["valid"]
    assert before["planDigest"] == after["planDigest"]


def test_profile_digest_conflict_and_unknown_version_do_not_mutate_project(tmp_path):
    adapter = XDLAdapter()
    projects = Projects(Store(tmp_path), adapter)
    project = projects.create("Profile conflict")
    registry = ProfileRegistry(adapter)
    profile = registry.list()["items"][0]
    lock = {key: profile[key] for key in ("profileId", "version", "schemaDigest", "presentationDigest")}
    for changes in ({"version": "999.0.0"}, {"schemaDigest": "sha256:" + "0" * 64}, {"profileId": "org.unknown.profile"}):
        with pytest.raises(Problem):
            registry.bind(projects, project["projectId"], 1, [{**lock, **changes}])
        assert projects.read(project["projectId"])["revision"] == 1


def test_profile_presentation_has_no_executable_hooks_or_core_redefinitions():
    from xverse_studio.profiles.presentation import sanitize_presentation

    for entry in ProfileRegistry(XDLAdapter()).list()["items"]:
        assert set(entry["presentation"]) <= {"name", "description", "labels", "formGroups", "documentation", "icons", "domain", "namespaces"}
        if entry.get("kind") == "domain-presentation":
            assert entry["presentation"] == sanitize_presentation(entry["presentation"])
        assert entry["executionAllowed"] is False
        assert "providerId" not in entry["presentation"]


def test_binding_malformed_profile_draft_refuses_without_parser_failure(tmp_path):
    from ruamel.yaml import YAML
    from xverse_studio.xdl.examples import dump_yaml
    adapter = XDLAdapter()
    projects = Projects(Store(tmp_path), adapter)
    project = projects.create("Malformed profile draft")
    identifier, document = next((key, value) for key, value in project["documents"].items() if value["path"].endswith("/profile.xdl.yaml"))
    resource = YAML(typ="safe").load(document["content"])
    resource["metadata"] = []
    authored = dump_yaml(resource)
    project = projects.save(project["projectId"], identifier, 1, authored, "yaml")
    registry = ProfileRegistry(adapter)
    entry = registry.list()["items"][0]
    lock = {key: entry[key] for key in ("profileId", "version", "schemaDigest", "presentationDigest")}
    with pytest.raises(Problem) as error:
        registry.bind(projects, project["projectId"], 2, [lock])
    assert error.value.code == "PROFILE_CONFLICT"
    assert projects.read(project["projectId"])["documents"][identifier]["content"] == authored


def test_binding_known_missing_profile_resolves_only_its_admitted_namespace(tmp_path):
    adapter = XDLAdapter()
    projects = Projects(Store(tmp_path), adapter)
    project = projects.create("Known missing profile")
    identifier = next(key for key, doc in project["documents"].items() if doc["path"].endswith("/profile.xdl.yaml"))
    def remove_profile(p):
        return {key: doc for key, doc in p["documents"].items() if key != identifier}
    project = projects.mutate(project["projectId"], 1, remove_profile)
    assert adapter.validate(projects.sources(project))["valid"] is False
    registry = ProfileRegistry(adapter)
    profile = registry.get("io.xverse.experiment")
    lock = {key: profile[key] for key in ("profileId", "version", "schemaDigest", "presentationDigest")}
    resolved = registry.bind(projects, project["projectId"], 2, [lock])
    assert adapter.validate(projects.sources(resolved))["valid"]


def test_duplicate_namespaces_and_executable_lock_fields_never_mutate_project(tmp_path):
    adapter = XDLAdapter()
    store = Store(tmp_path)
    projects = Projects(store, adapter)
    project = projects.create("Profile namespace and inertness checks")
    registry = ProfileRegistry(adapter)
    profile = registry.get("io.xverse.experiment")
    lock = {key: profile[key] for key in ("profileId", "version", "schemaDigest", "presentationDigest")}
    for bindings in ([lock, lock], [{**lock, "hooks": ["execute"]}], [{**lock, "profileId": "xverse.core.redefinition"}]):
        with pytest.raises(Problem):
            registry.bind(projects, project["projectId"], 1, bindings)
        assert projects.read(project["projectId"])["revision"] == 1
    assert store.all("run") == []


def test_declared_profile_sidecars_must_match_registry_and_actual_locked_bytes(tmp_path):
    from copy import deepcopy
    from xverse_studio.storage.core import digest
    adapter = XDLAdapter()
    projects = Projects(Store(tmp_path), adapter)
    project = projects.create("Declared sidecar identities")
    registry = ProfileRegistry(adapter)
    locks = [{key: p[key] for key in ("profileId", "version", "schemaDigest", "presentationDigest")} for p in registry.list()["items"]]
    project = registry.bind(projects, project["projectId"], 1, locks)
    assert registry.validate_project(project) == project["manifest"]["profiles"]
    for kind in ("schema", "presentation"):
        changed = deepcopy(project)
        lock = changed["manifest"]["profiles"][0]
        changed["supportingFiles"][lock[kind + "Path"]] = "{}"
        lock[kind + "Digest"] = digest(b"{}")
        with pytest.raises(Problem) as error:
            registry.validate_project(changed)
        assert error.value.code == "PROFILE_CONFLICT"
    changed = deepcopy(project)
    lock = changed["manifest"]["profiles"][0]
    changed["supportingFiles"][lock["schemaPath"]] += "\n"
    with pytest.raises(Problem):
        registry.validate_project(changed)
    forged = {"profileLocks": deepcopy(project["manifest"]["profiles"])}
    forged["profileLocks"][0]["version"] = "999.0.0"
    with pytest.raises(Problem):
        registry.validate_snapshot(forged)


import importlib.util as _util
from pathlib import Path as _Path

_spec = _util.spec_from_file_location(
    "profile_fixtures", _Path(__file__).resolve().parents[1] / "fixtures/profiles/profile_fixtures.py"
)
profile_fixtures = _util.module_from_spec(_spec)
_spec.loader.exec_module(profile_fixtures)


def _bound_project(tmp_path):
    adapter = XDLAdapter()
    projects = Projects(Store(tmp_path), adapter)
    project = projects.create("Profile fixtures")
    registry = ProfileRegistry(adapter)
    locks = [{k: e[k] for k in ("profileId", "version", "schemaDigest", "presentationDigest")}
             for e in registry.list()["items"]]
    return projects, registry, registry.bind(projects, project["projectId"], 1, locks)


def _preflight(client, documents, profiles=(), supporting=None):
    import base64
    import io
    import json
    import zipfile

    archive = io.BytesIO()
    with zipfile.ZipFile(archive, "w") as z:
        z.writestr("project.studio.json", json.dumps({
            "formatVersion": "1.0", "name": "profile fixture",
            "resources": [{"path": "xdl/" + n, "format": "yaml"} for n in documents],
            "profiles": list(profiles), "layoutFiles": []}))
        for name, content in documents.items():
            z.writestr("xdl/" + name, content)
        for name, content in (supporting or {}).items():
            z.writestr(name, content)
    response = client.post("/api/v1/projects/imports",
                           json={"archiveBase64": base64.b64encode(archive.getvalue()).decode()})
    if response.status_code != 201:
        return None, response
    project = response.json()
    return project, client.post(f"/api/v1/projects/{project['projectId']}/preflights",
                                json={"revision": project["revision"]})


def test_reference_examples_have_no_authored_profile_findings():
    from xverse_studio.xdl import examples

    registry = ProfileRegistry(XDLAdapter())
    for example in examples():
        assert registry.authored_findings(example["documents"]) == []


@pytest.mark.parametrize("changes,field", [
    ({"schemaRef": "https://example.invalid/redefined-core.schema.json"}, "schemaRef"),
    ({"conflictPolicy": "override"}, "conflictPolicy"),
    ({"compatibleApiVersions": ["xverse.io/xdl/v9"]}, "compatibleApiVersions"),
    ({"version": "9.0.0"}, "version"),
])
def test_redefining_an_admitted_profile_is_an_explicit_conflict(client, changes, field):
    documents = profile_fixtures.redefined_admitted_profile(**changes)
    findings = ProfileRegistry(XDLAdapter()).authored_findings(documents)
    assert [f["code"] for f in findings] == ["PROFILE_CONFLICT"]
    assert field in findings[0]["message"]
    project, preflight = _preflight(client, documents)
    body = preflight.json()
    assert body["status"] == "blocked"
    assert "PROFILE_CONFLICT" in {d["code"] for d in body["diagnostics"]}
    # The authored bytes are preserved exactly for inspection.
    stored = client.get(f"/api/v1/projects/{project['projectId']}").json()
    profile = next(d for d in stored["documents"].values() if d["path"].endswith("/profile.xdl.yaml"))
    assert profile["content"] == documents["profile.xdl.yaml"]


def test_core_looking_unadmitted_namespace_is_explicitly_unresolved(client):
    documents = profile_fixtures.core_namespace_profile()
    assert XDLAdapter().validate(documents)["valid"]  # XDL keeps it valid and intact
    findings = ProfileRegistry(XDLAdapter()).authored_findings(documents)
    assert [f["code"] for f in findings] == ["PROFILE_UNRESOLVED"]
    assert "xverse.io" in findings[0]["message"]
    _, preflight = _preflight(client, documents)
    assert "PROFILE_UNRESOLVED" in {d["code"] for d in preflight.json()["diagnostics"]}
    assert preflight.json()["status"] == "blocked"


def test_namespace_collisions_are_refused_by_bind_and_lock_validation(tmp_path):
    adapter = XDLAdapter()
    documents = profile_fixtures.duplicate_owner_profile()
    report = adapter.validate(documents)
    assert "XDL-SEMANTIC-DUPLICATE-PROFILE-NAMESPACE" in {d["code"] for d in report["diagnostics"]}
    projects = Projects(Store(tmp_path), adapter)
    project = projects.create("Duplicate owner", documents=documents)
    registry = ProfileRegistry(adapter)
    entry = registry.list()["items"][0]
    lock = {k: entry[k] for k in ("profileId", "version", "schemaDigest", "presentationDigest")}
    with pytest.raises(Problem) as error:
        registry.bind(projects, project["projectId"], 1, [lock])
    assert error.value.code == "PROFILE_CONFLICT"
    assert projects.read(project["projectId"])["revision"] == 1
    # Two manifest locks for one namespace are refused even when each is admitted.
    projects2, registry2, bound = _bound_project(tmp_path / "second")
    duplicated = {**bound, "manifest": {**bound["manifest"],
                  "profiles": bound["manifest"]["profiles"] + bound["manifest"]["profiles"][:1]}}
    with pytest.raises(Problem) as error:
        registry2.validate_project(duplicated)
    assert error.value.code == "PROFILE_CONFLICT"


@pytest.mark.parametrize("name", sorted(profile_fixtures.MALICIOUS_PRESENTATIONS))
def test_malicious_presentation_is_never_admitted_even_with_a_matching_digest(client, tmp_path, name):
    from xverse_studio.storage.core import digest

    projects, registry, project = _bound_project(tmp_path)
    lock = project["manifest"]["profiles"][0]
    payload = profile_fixtures.presentation_bytes(name)
    # A self-consistent lock (digest of the malicious bytes) is still not an admitted asset.
    forged = {**lock, "presentationDigest": digest(payload.encode())}
    tampered = {**project, "manifest": {**project["manifest"], "profiles": [forged] + project["manifest"]["profiles"][1:]},
                "supportingFiles": {**project["supportingFiles"], lock["presentationPath"]: payload}}
    with pytest.raises(Problem) as error:
        registry.validate_project(tampered)
    assert error.value.code == "PROFILE_CONFLICT"
    assert "not an admitted declarative asset" in error.value.message
    # Imported, the bytes stay inert data and execution is refused before any run.
    sources = {d["path"].rsplit("/", 1)[-1]: d["content"] for d in project["documents"].values()}
    supporting = {**project["supportingFiles"], lock["presentationPath"]: payload}
    before = len(client.get("/api/v1/projects").json()["items"])
    imported, response = _preflight(client, sources, [forged] + project["manifest"]["profiles"][1:], supporting)
    if imported is None:
        # Refused at import: no project is created from unsafe presentation bytes.
        assert response.status_code == 422 and response.json()["code"] == "UNSAFE_PROFILE"
        assert len(client.get("/api/v1/projects").json()["items"]) == before
    else:
        assert response.status_code == 422 and response.json()["code"] == "PROFILE_CONFLICT"
    assert client.get("/api/v1/runs").json()["items"] == []


def test_api_profile_discovery_is_exact_and_independent_of_providers_and_blueprints(client):
    from importlib.resources import files
    from pathlib import Path

    from xverse_studio.storage.core import digest
    from xverse_studio.xdl.examples import examples

    import xverse_studio.assertions as assertions

    # Exact identities come from the packaged schemas and the blueprints' declared profile versions.
    sources = {
        "io.xverse.experiment": files("xverse_xdl").joinpath("profiles", "experiment-lite-v0.1.schema.json").read_bytes(),
        "io.xverse.studio.experiments": (Path(assertions.__file__).parent / "evaluation-v1.schema.json").read_bytes(),
        "io.xverse.studio.connections": (Path(assertions.__file__).parent.parent / "connections" / "connections-v1.schema.json").read_bytes(),
        "io.xverse.studio.domain.process-control": (Path(assertions.__file__).parent.parent / "profiles" / "domain-presentation-v1.schema.json").read_bytes(),
        "io.xverse.studio.domain.automotive": (Path(assertions.__file__).parent.parent / "profiles" / "domain-presentation-v1.schema.json").read_bytes(),
        "io.xverse.studio.reference-controls": (Path(assertions.__file__).parent.parent / "xdl" / "reference-controls-v1.schema.json").read_bytes(),
    }
    declared = {ref["namespace"]: ref["version"] for example in examples() for ref in example["profileRefs"]}
    listing = client.get("/api/v1/profiles").json()["items"]
    assert {entry["namespace"] for entry in listing} == set(sources)
    forbidden = {"os", "operatingSystems", "supportedHostOS", "hostCompatible", "architectures", "providerId", "providerIds"}

    def keys(value):
        if isinstance(value, dict):
            for key, item in value.items():
                yield key
                yield from keys(item)
        elif isinstance(value, list):
            for item in value:
                yield from keys(item)

    for entry in listing:
        detail = client.get("/api/v1/profiles/" + entry["profileId"]).json()
        assert detail["version"] == declared[detail["namespace"]]
        assert detail["schemaDigest"] == digest(sources[detail["namespace"]])
        assert detail["maturity"] == ("fixture" if detail.get("kind") in {"domain-presentation", "reference-controls"} else "admitted_integration") and detail["limitations"]
        for field in ("namespace", "version", "maturity", "limitations", "schemaDigest", "presentationDigest"):
            assert detail[field] == entry[field]
        # A profile never claims OS support, provider identity or execution authority.
        assert not forbidden & set(keys({k: v for k, v in detail.items() if k not in {"schema", "schemaText"}}))
        assert detail["executionAllowed"] is False
    assert client.get("/api/v1/profiles/org.unknown.profile").status_code == 404
    # OS compatibility is a provider-binding fact.
    providers_before = client.get("/api/v1/providers").json()
    assert all("supportedHostOS" in p and "hostCompatible" in p for p in providers_before["items"])
    # Profiles bind to a blueprint-composed project without changing provider availability or its plan.
    blueprint = examples()[-1]
    project = client.post("/api/v1/projects", json={"name": "profile independence", "blueprintRef": blueprint["id"]}).json()
    plan_before = client.post(f"/api/v1/projects/{project['projectId']}/compilations",
                              json={"revision": project["revision"]}).json()["planDigest"]
    response = client.post(
        f"/api/v1/projects/{project['projectId']}/profile-bindings",
        headers={"If-Match": str(project["revision"])},
        json={"baseRevision": project["revision"], "profiles": [
            {k: e[k] for k in ("profileId", "version", "schemaDigest", "presentationDigest")} for e in listing]},
    )
    assert response.status_code == 200, response.text
    bound = response.json()
    assert bound["revision"] > project["revision"]
    assert client.get("/api/v1/providers").json() == providers_before
    plan_after = client.post(f"/api/v1/projects/{project['projectId']}/compilations",
                             json={"revision": bound["revision"]}).json()["planDigest"]
    assert plan_after == plan_before
    # Profile discovery is unchanged by composing projects from blueprints.
    assert client.get("/api/v1/profiles").json()["items"] == listing
