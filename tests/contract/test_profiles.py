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
    assert len(updated["manifest"]["profiles"]) == 2
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
    for entry in ProfileRegistry(XDLAdapter()).list()["items"]:
        assert set(entry["presentation"]) <= {"name", "description", "labels", "formGroups", "documentation"}
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
