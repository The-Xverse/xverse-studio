"""Independent local-fixture retention probes; no provider or physical operations."""
from pathlib import Path
from tempfile import TemporaryDirectory
import hashlib
import json
import subprocess
from unittest.mock import patch

from fastapi.testclient import TestClient
from xverse_studio.api.app import create_app

from pathlib import Path as _ReviewPath
_ReviewPath(".studio-local/review-temp").mkdir(parents=True, exist_ok=True)
_ReviewPath(".studio-local/review-pytest").mkdir(parents=True, exist_ok=True)

source_paths = [f"services/studio-api/src/xverse_studio/retention/{name}" for name in ("__init__.py", "files.py", "service.py")]
source_digests = lambda: {name: "sha256:" + hashlib.sha256(Path(name).read_bytes()).hexdigest() for name in source_paths}
report = {"sourceBefore": source_digests(), "cases": {}}

def no_process(*args, **kwargs):
    raise AssertionError("Retention probes must not start any provider process")

with TemporaryDirectory(dir=".studio-local/review-temp", prefix="retention-http-review-") as directory:
    app = create_app(Path(directory) / "state", allowed_hosts=["testserver"], bootstrap_token="review-fixture-bootstrap")
    with patch.object(subprocess, "Popen", no_process), TestClient(app, base_url="http://testserver") as client:
        client.headers["Origin"] = "http://testserver"
        session = client.post("/api/v1/session", json={"bootstrapToken": "review-fixture-bootstrap"})
        assert session.status_code == 200
        client.headers["X-CSRF-Token"] = session.json()["csrfToken"]
        state = app.state.studio
        def project(name):
            response = client.post("/api/v1/projects", json={"name": name})
            assert response.status_code == 201, response.text
            return response.json()
        def plan(selection):
            response = client.post("/api/v1/retention/plans", json=selection)
            assert response.status_code == 200, response.text
            return response.json()
        def apply(row, key):
            return client.post(f"/api/v1/retention/plans/{row['planId']}/apply", headers={"Idempotency-Key": key}, json={"fingerprint": row["fingerprint"]})

        selected = project("Retire only this fixture")
        kept = project("Keep this fixture")
        preview = plan({"projectIds": [selected["projectId"]]})
        assert (state.store.root / "projects" / selected["projectId"]).exists()
        result = apply(preview, "independent-delete")
        assert result.status_code == 202, result.text
        assert result.json()["status"] == "complete", result.text
        assert client.get(f"/api/v1/projects/{selected['projectId']}").status_code == 404
        assert client.get(f"/api/v1/projects/{kept['projectId']}").status_code == 200
        assert apply(preview, "independent-delete").json() == result.json()
        report["cases"]["explicit_project_delete_and_idempotency"] = "PASS"

        historical = project("Protect recorded immutable inputs")
        preflight = client.post(f"/api/v1/projects/{historical['projectId']}/preflights", json={"revision": 1})
        assert preflight.status_code == 200, preflight.text
        sid = preflight.json()["snapshotId"]
        original_snapshot = state.store.get("snapshot", sid)
        snapshot_path = state.store.root / "snapshots" / sid / "snapshot.json"
        original_snapshot_bytes = snapshot_path.read_bytes()
        preview = plan({"projectIds": [historical["projectId"]]})
        assert preview["removals"] == []
        assert "SNAPSHOT_DEPENDS_ON_PROJECT" in preview["protected"][0]["reasons"]
        assert apply(preview, "independent-protected").status_code == 202
        assert state.store.get("snapshot", sid) == original_snapshot
        assert snapshot_path.read_bytes() == original_snapshot_bytes
        report["cases"]["historical_snapshot_protects_project"] = "PASS"

        drift = project("Externally changed bytes")
        preview = plan({"projectIds": [drift["projectId"]]})
        did = next(iter(drift["documents"]))
        path = state.projects.document_path(drift["projectId"], did)
        changed_bytes = path.read_bytes() + b"\n# independently altered after preview\n"
        path.write_bytes(changed_bytes)
        result = apply(preview, "independent-stale-files")
        assert result.status_code == 409, result.text
        assert result.json()["code"] == "RETENTION_PLAN_STALE"
        assert path.read_bytes() == changed_bytes
        report["cases"]["filesystem_drift_rejected_before_effect"] = "PASS"

        external = Path(directory) / "external-origin.bin"
        external.write_bytes(b"external origin remains immutable")
        registration = client.post("/api/v1/catalog/artifacts", headers={"Idempotency-Key": "independent-register"}, json={"name": "Independent inert artifact", "version": "1.0.0", "artifactKind": "model", "digest": "sha256:" + "c" * 64, "originRef": "urn:review:external-origin"})
        assert registration.status_code == 201, registration.text
        aid = registration.json()["entryId"]
        # The earlier deliberately altered project makes artifact independence
        # unresolved. Restore exact committed bytes, then prove metadata-only scope.
        path.write_bytes(drift["documents"][did]["content"].encode())
        preview = plan({"artifactIds": [aid]})
        assert preview["removals"] == [{"artifactId": aid, "scope": "catalog_registration_metadata_only", "externalArtifactPreserved": True}]
        result = apply(preview, "independent-artifact-delete")
        assert result.status_code == 202 and result.json()["status"] == "complete", result.text
        assert external.read_bytes() == b"external origin remains immutable"
        assert client.get("/api/v1/catalog/" + aid).status_code == 404
        report["cases"]["artifact_metadata_only_origin_untouched"] = "PASS"

        linked = project("Unsafe project directory link")
        owned = state.store.root / "projects" / linked["projectId"]
        owned.rename(owned.with_name(owned.name + "-review-backup"))
        outside = Path(directory) / "outside"
        outside.mkdir()
        sentinel = outside / "preserve.txt"
        sentinel.write_bytes(b"outside owned fixture is preserved")
        owned.symlink_to(outside, target_is_directory=True)
        response = client.post("/api/v1/retention/plans", json={"projectIds": [linked["projectId"]]})
        if response.status_code == 200:
            row = response.json()
            assert row["removals"] == [] and row["protected"], response.text
        else:
            assert response.status_code == 422, response.text
            assert response.json()["code"] == "RETENTION_DEPENDENCIES_UNRESOLVED", response.text
        assert sentinel.read_bytes() == b"outside owned fixture is preserved"
        report["cases"]["symlink_project_target_refused_without_effect"] = "PASS"
        report["providerProcessStarts"] = 0

report["sourceAfter"] = source_digests()
report["sourceStable"] = report["sourceBefore"] == report["sourceAfter"]
print(json.dumps(report, indent=2))
