"""Reproduce review boundaries in fresh isolated data roots; no live runtime starts.

Use --scratch-root on an approved filesystem. Retains all fixture files for inspection.
This script prints observations rather than converting historical failures into passing assertions.
"""

import argparse
import hashlib
import io
import json
from pathlib import Path
import tempfile
import zipfile

from fastapi.testclient import TestClient

from xverse_studio.api.app import create_app
from xverse_studio.projects.service import Projects
from xverse_studio.security.files import check_text, safe_name
from xverse_studio.storage.core import Problem, Store
from xverse_studio.xdl import XDLAdapter


def reproduce(scratch_root):
    result = {}
    try:
        check_text("endpoint: https://user:synthetic-value@example.invalid")
        result["M0-R01_uri_userinfo"] = "ACCEPTED"
    except Problem:
        result["M0-R01_uri_userinfo"] = "REJECTED"
    result["M0-R02_portable_names"] = {}
    for name in ("xdl/bad?.yaml", "xdl/bad*.yaml", "xdl/bad<.yaml", "xdl/bad|.yaml"):
        try:
            safe_name(name)
            result["M0-R02_portable_names"][name] = "ACCEPTED"
        except Problem:
            result["M0-R02_portable_names"][name] = "REJECTED"
    root = Path(tempfile.mkdtemp(prefix="review-http-", dir=scratch_root))
    app = create_app(root, allowed_hosts=["testserver"], bootstrap_token="isolated-review-bootstrap")
    with TestClient(app, base_url="http://testserver") as client:
        client.headers["Origin"] = "http://testserver"
        session = client.post("/api/v1/session", json={"bootstrapToken": "isolated-review-bootstrap"})
        client.headers["X-CSRF-Token"] = session.json()["csrfToken"]
        project = client.post("/api/v1/projects", json={"name": "Isolated review project"}).json()
        project_id = project["projectId"]
        revision = project["revision"]
        response = client.post(f"/api/v1/projects/{project_id}/preflights", json={
            "revision": revision, "scenarioRef": "xdl://org.example/scenario/not-supplied"})
        result["M1-R01_missing_selected_scenario"] = {"http": response.status_code, "status": response.json().get("status")}
        store = app.state.studio.store
        record = store.get("project", project_id)
        record["supportingFiles"]["artifacts.lock.json"] = json.dumps({
            "formatVersion": "1.0", "entries": [{"artifactId": "pinned-reference", "digest": "sha256:" + "a" * 64, "distribution": "restricted"}]})
        store.put("project", project_id, record)
        operation = client.post(f"/api/v1/projects/{project_id}/exports", json={"revision": revision},
                                headers={"Idempotency-Key": "isolated-review-export"}).json()
        archive = client.get(operation["result"]["downloadUrl"]).content
        with zipfile.ZipFile(io.BytesIO(archive)) as bundle:
            result["M0-R03_export_lock_entries"] = json.loads(bundle.read("artifacts.lock.json"))["entries"]
        doc_id = next(identifier for identifier, doc in project["documents"].items() if doc["path"].endswith("scenario.xdl.yaml"))
        source_file = app.state.studio.projects.document_path(project_id, doc_id)
        source_file.write_text(source_file.read_text().replace("value: 0.8", "value: 0.7"))
        response = client.post(f"/api/v1/projects/{project_id}/preflights", json={"revision": revision})
        result["M1-R02_external_source_edit"] = {"http": response.status_code, "status": response.json().get("status")}

    root = Path(tempfile.mkdtemp(prefix="review-persistence-", dir=scratch_root))
    store = Store(root)
    projects = Projects(store, XDLAdapter())
    project = projects.create("Persistence failure review")
    doc_id = next(iter(project["documents"]))
    content = project["documents"][doc_id]["content"]
    original_put = store.put

    def fail_after_metadata_write(kind, identifier, body, db=None):
        value = original_put(kind, identifier, body, db)
        if kind == "project" and body["revision"] == 2:
            raise OSError("synthetic post-rename metadata failure")
        return value

    store.put = fail_after_metadata_write
    try:
        projects.save(project["projectId"], doc_id, 1, content + "\n# changed\n", "yaml")
    except OSError:
        pass
    finally:
        store.put = original_put
    failure = {"committedRevision": projects.read(project["projectId"])["revision"],
               "orphanRevision2Exists": projects._dir(project["projectId"], 2).exists()}
    try:
        projects.save(project["projectId"], doc_id, 1, content + "\n# retried\n", "yaml")
        failure["retry"] = "saved"
    except Problem as error:
        failure["retry"] = {"code": error.code, "http": error.status}
    result["M0-R04_commit_failure"] = failure
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--scratch-root", type=Path, required=True)
    args = parser.parse_args()
    if not args.scratch_root.is_dir():
        parser.error("Select an existing approved scratch directory.")
    source_root = Path(__file__).resolve().parents[3] / "services" / "studio-api" / "src" / "xverse_studio"
    observed_files = ("security/files.py", "projects/service.py", "api/exchange.py", "runs/service.py", "api/app.py")
    identities = {name: hashlib.sha256((source_root / name).read_bytes()).hexdigest() for name in observed_files}
    outcomes = reproduce(args.scratch_root)
    identities_after = {name: hashlib.sha256((source_root / name).read_bytes()).hexdigest() for name in observed_files}
    print(json.dumps({"scope": "owned_isolated_review_fixtures", "sourceHashesBefore": identities,
                      "sourceHashesAfter": identities_after, "sourceUnchangedDuringReview": identities == identities_after,
                      "outcomes": outcomes}, indent=2))
