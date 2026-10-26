"""T016: project inspection of declared dependencies, example scope and unresolved content."""
import base64
import io
import json
import zipfile

from ruamel.yaml import YAML

from xverse_studio.storage.core import digest
from xverse_studio.xdl import examples
from xverse_studio.xdl.examples import dump_yaml


def _archive(documents, manifest=None, extra=None):
    data = io.BytesIO()
    with zipfile.ZipFile(data, "w") as z:
        z.writestr("project.studio.json", json.dumps(manifest or {
            "formatVersion": "1.0", "name": "Imported scenario",
            "resources": [{"path": "xdl/" + n, "format": "yaml"} for n in documents],
            "profiles": [], "layoutFiles": []}))
        for name, content in documents.items():
            z.writestr("xdl/" + name, content)
        for name, content in (extra or {}).items():
            z.writestr(name, content)
    return base64.b64encode(data.getvalue()).decode()


def _import(client, archive):
    response = client.post("/api/v1/projects/imports", json={"archiveBase64": archive})
    assert response.status_code == 201, response.text
    return response


def test_inspection_reports_example_scope_and_admitted_dependencies(client):
    entry = examples()[0]
    project = client.post("/api/v1/projects", json={"name": "Inspect", "blueprintRef": entry["id"]}).json()
    report = client.get(f"/api/v1/projects/{project['projectId']}/inspection").json()
    assert report["revision"] == project["revision"]
    assert report["example"]["scope"] == entry["scope"] and report["example"]["limitations"] == entry["limitations"]
    assert report["unresolved"] == [] and report["unparsed"] == [] and report["executionBlocked"] is False
    assert client.get("/api/v1/projects/missing/inspection").status_code == 404


def test_inspection_shows_unresolved_content_exactly_and_never_executes(client):
    documents = dict(examples()[0]["documents"])
    system = YAML(typ="safe").load(documents["system.xdl.yaml"])
    system["extensions"] = {"org.example.unresolved": {"script": "rm -rf /", "opaque": [1, 2, 3]}}
    system["spec"]["componentInstances"][0]["extensions"] = {"org.example/nested": {"note": "kept"}}
    out = io.StringIO()
    YAML().dump(system, out)
    documents["system.xdl.yaml"] = out.getvalue()
    sidecar = '{"declared": true}'
    manifest = {"formatVersion": "1.0", "name": "Unresolved import",
                "resources": [{"path": "xdl/" + n, "format": "yaml"} for n in documents],
                "profiles": [{"namespace": "org.example.unresolved", "version": "1.0.0",
                              "schemaPath": "profiles/unresolved.schema.json", "schemaDigest": "sha256:" + "0" * 64}],
                "layoutFiles": []}
    project = _import(client, _archive(documents, manifest, extra={"profiles/unresolved.schema.json": sidecar})).json()
    report = client.get(f"/api/v1/projects/{project['projectId']}/inspection").json()
    found = {item["namespace"]: item for item in report["unresolved"]}
    assert set(found) == {"org.example.unresolved", "org.example/nested"}
    root = found["org.example.unresolved"]
    assert root["status"] == "unresolved" and root["pointer"] == "/extensions/org.example.unresolved"
    assert YAML(typ="safe").load(root["content"]) == {"script": "rm -rf /", "opaque": [1, 2, 3]}
    assert found["org.example/nested"]["pointer"] == "/spec/componentInstances/0/extensions/org.example~1nested"
    assert all(item["executionAllowed"] is False for item in report["unresolved"])
    assert report["dependencies"]["profileLocks"][0]["status"] == "unresolved"
    assert report["dependencies"]["supportingFiles"] == [
        {"path": "profiles/unresolved.schema.json", "bytes": len(sidecar), "digest": digest(sidecar.encode()), "executed": False}]
    assert report["executionBlocked"] is True and report["provenance"]["imported"] is True
    # Inspection is read-only: the revision and stored bytes are unchanged and nothing ran.
    again = client.get(f"/api/v1/projects/{project['projectId']}").json()
    assert again["revision"] == project["revision"] and again["documents"] == project["documents"]
    assert client.get("/api/v1/runs").json()["items"] == []


def test_inspection_distinguishes_unadmitted_and_conflicting_profiles(client):
    documents = dict(examples()[0]["documents"])
    profile = YAML(typ="safe").load(documents["profile.xdl.yaml"])
    profile["metadata"]["version"] = "9.9.9"  # redefines the admitted experiment profile
    documents["profile.xdl.yaml"] = dump_yaml(profile)
    project = _import(client, _archive(documents)).json()
    report = client.get(f"/api/v1/projects/{project['projectId']}/inspection").json()
    statuses = {item["namespace"]: item["status"] for item in report["unresolved"]}
    assert statuses and set(statuses.values()) == {"conflict"}
    assert all("version" in item["reason"] for item in report["unresolved"])


def _bound_export(client):
    """An exported project whose admitted profile locks carry their declared sidecars."""
    project = client.post("/api/v1/projects", json={"name": "Locked dependencies"}).json()
    profiles = client.get("/api/v1/profiles").json()["items"]
    bound = client.post(f"/api/v1/projects/{project['projectId']}/profile-bindings", headers={"If-Match": str(project["revision"])},
                        json={"baseRevision": project["revision"], "profiles": [
                            {k: p[k] for k in ("profileId", "version", "schemaDigest", "presentationDigest")} for p in profiles]})
    assert bound.status_code == 200, bound.text
    op = client.post(f"/api/v1/projects/{project['projectId']}/exports", headers={"Idempotency-Key": "inspect-" + project["projectId"]},
                     json={"revision": bound.json()["revision"]})
    return zipfile.ZipFile(io.BytesIO(client.get(op.json()["result"]["downloadUrl"]).content))


def _rezip(archive, change):
    files = {name: archive.read(name).decode() for name in archive.namelist()}
    change(files)
    data = io.BytesIO()
    with zipfile.ZipFile(data, "w") as z:
        for name, content in files.items():
            z.writestr(name, content)
    return base64.b64encode(data.getvalue()).decode()


def test_explicit_dependency_import_verifies_declared_locks_and_sidecars(client):
    archive = _bound_export(client)
    project = _import(client, _rezip(archive, lambda files: None)).json()
    report = client.get(f"/api/v1/projects/{project['projectId']}/inspection").json()
    locks = report["dependencies"]["profileLocks"]
    assert {lock["namespace"]: lock["status"] for lock in locks} == {
        "io.xverse.experiment": "admitted", "io.xverse.studio.experiments": "admitted", "io.xverse.studio.connections": "admitted",
        "io.xverse.studio.domain.process-control": "admitted", "io.xverse.studio.domain.automotive": "admitted"}
    sidecars = {f["path"] for f in report["dependencies"]["supportingFiles"]}
    assert {lock["schemaPath"] for lock in locks} <= sidecars and all(not f["executed"] for f in report["dependencies"]["supportingFiles"])
    assert report["executionBlocked"] is False

    # A sidecar whose bytes disagree with its lock, or a duplicated lock, is never reported admitted.
    def tamper(files):
        manifest = json.loads(files["project.studio.json"])
        files[manifest["profiles"][0]["schemaPath"]] += "\n"
        manifest["profiles"].append(dict(manifest["profiles"][1]))
        files["project.studio.json"] = json.dumps(manifest)
    tampered = _import(client, _rezip(archive, tamper)).json()
    report = client.get(f"/api/v1/projects/{tampered['projectId']}/inspection").json()
    statuses = [(lock["namespace"], lock["status"]) for lock in report["dependencies"]["profileLocks"]]
    assert statuses == [("io.xverse.experiment", "conflict"), ("io.xverse.studio.experiments", "admitted"),
                        ("io.xverse.studio.connections", "admitted"), ("io.xverse.studio.domain.process-control", "admitted"),
                        ("io.xverse.studio.domain.automotive", "admitted"), ("io.xverse.studio.experiments", "conflict")]
    assert "digest" in report["dependencies"]["profileLocks"][0]["reason"]
    assert "more than one" in report["dependencies"]["profileLocks"][5]["reason"]
    assert report["executionBlocked"] is True


def test_inspection_reports_an_authored_but_unadmitted_profile(client):
    documents = dict(examples()[0]["documents"])
    yaml = YAML(typ="safe")
    profile = yaml.load(documents["profile.xdl.yaml"])
    profile["metadata"]["name"] = "custom-profile"
    profile["spec"]["extensionNamespace"] = "org.example.custom"
    documents["custom-profile.xdl.yaml"] = dump_yaml(profile)
    system = yaml.load(documents["system.xdl.yaml"])
    system["extensions"] = {"org.example.custom": {"note": "authored"}}
    documents["system.xdl.yaml"] = dump_yaml(system)
    project = _import(client, _archive(documents)).json()
    report = client.get(f"/api/v1/projects/{project['projectId']}/inspection").json()
    assert [(item["namespace"], item["status"]) for item in report["unresolved"]] == [("org.example.custom", "unadmitted")]


def test_inspection_survives_malformed_authored_shapes_and_unparsed_sources(client):
    documents = dict(examples()[0]["documents"])
    yaml = YAML(typ="safe")
    system = yaml.load(documents["system.xdl.yaml"])
    system["extensions"] = {1: "numeric key", None: "null key"}
    documents["system.xdl.yaml"] = dump_yaml(system)
    profile = yaml.load(documents["profile.xdl.yaml"])
    profile["metadata"] = "not a mapping"
    documents["profile.xdl.yaml"] = dump_yaml(profile)
    extra = yaml.load(documents["evaluation-profile.xdl.yaml"])
    extra["spec"]["extensionNamespace"] = ["not", "hashable"]
    documents["evaluation-profile.xdl.yaml"] = dump_yaml(extra)
    project = _import(client, _archive(documents)).json()
    pid = project["projectId"]
    response = client.get(f"/api/v1/projects/{pid}/inspection")
    assert response.status_code == 200, response.text
    statuses = {(item["pointer"], item["status"]) for item in response.json()["unresolved"]}
    assert {("/extensions/1", "unresolved"), ("/extensions/None", "unresolved")} <= statuses
    # The broken Profile resources make their namespaces conflicting or unresolved, never admitted.
    assert ("/extensions/io.xverse.experiment", "conflict") in statuses
    assert ("/extensions/io.xverse.studio.experiments", "unresolved") in statuses
    preflight = client.post(f"/api/v1/projects/{pid}/preflights", json={"revision": project["revision"]})
    assert preflight.status_code == 200 and preflight.json()["status"] == "blocked"
    document_id = next(i for i, d in project["documents"].items() if d["path"].endswith("/scenario.xdl.yaml"))
    saved = client.put(f"/api/v1/projects/{pid}/documents/{document_id}", headers={"If-Match": str(project["revision"])},
                       json={"content": "kind: Scenario\n  bad: ["})
    assert saved.status_code == 200, saved.text
    report = client.get(f"/api/v1/projects/{pid}/inspection").json()
    assert report["unparsed"] == [{"documentId": document_id, "path": "xdl/scenario.xdl.yaml"}]
    assert report["executionBlocked"] is True
