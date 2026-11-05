"""Read back bounded browser downloads from the actual recorded export matrix.

Never extracts or executes an archive. Operation receipts, immutable source bytes,
private exclusions and authored inputs are checked independently of UI assertions.
"""
import base64
import io
import json
from pathlib import Path
import sqlite3
import zipfile

from xverse_studio.storage.core import digest
from xverse_studio.security.managed_io import read_bounded


def verify_downloads(output: Path, data: Path, context: dict) -> dict:
    report = json.loads((output / "browser.json").read_bytes())
    downloads = []

    def attachments(value):
        if isinstance(value, dict):
            if value.get("name") == "actual-export-keyboard" and "body" in value:
                downloads.append(json.loads(base64.b64decode(value["body"])))
            for child in value.values():
                attachments(child)
        elif isinstance(value, list):
            for child in value:
                attachments(child)
    attachments(report)
    assert len(downloads) == 8 and len({item["operation"]["operationId"] for item in downloads}) == 8
    with sqlite3.connect((data / "studio.sqlite").as_uri() + "?mode=ro", uri=True) as db:
        def records(kind):
            return {key: json.loads(body) for key, body in db.execute("SELECT id,body FROM records WHERE kind=?", (kind,))}
        projects, operations = records("project"), records("operation")
        expected_evaluations = [v for v in records("evaluation").values() if v.get("runId") == context["runId"]]
        expected_annotations = [v for v in records("annotation").values() if v.get("runId") == context["runId"]]
        receipts = [(scope, fingerprint, json.loads(result)) for scope, fingerprint, result in db.execute("SELECT scope,fingerprint,result FROM idempotency")]
        secret_values = {cookie["value"] for cookie in json.loads((data / "browser-session.private.json").read_bytes())["cookies"]}
        for value in records("session").values():
            secret_values.update(item for item in value.values() if isinstance(item, str) and len(item) >= 20)
    project = projects[context["projectId"]]
    expected_authored = {}
    for doc in project["documents"].values():
        source = data / "projects" / context["projectId"] / "revisions" / str(project["revision"]) / doc["path"]
        raw = read_bounded(data, source, 1024 * 1024)
        assert digest(raw) == doc["digest"]
        expected_authored[doc["path"]] = raw
    expected_snapshot = (data / "snapshots" / context["snapshotId"] / "snapshot.json").read_bytes()
    expected_journal = (data / "runs" / context["runId"] / "evidence.jsonl").read_bytes()
    captured = []
    for item in downloads:
        path = Path(item["path"])
        assert not path.is_symlink() and path.resolve().is_relative_to((output / "artifacts").resolve())
        assert path.stat().st_size <= 6 * 1024 * 1024
        raw = path.read_bytes()
        operation = item["operation"]
        assert operations[operation["operationId"]] == operation
        assert operation["status"] == "completed" and digest(raw) == item["digest"] == operation["result"]["digest"]
        assert len(raw) == item["bytes"] == operation["result"]["size"]
        assert raw == (data / "exports" / (operation["operationId"] + ".zip")).read_bytes()
        accepted = [(scope, fingerprint) for scope, fingerprint, result in receipts if result.get("operationId") == operation["operationId"]]
        assert len(accepted) == 1
        scope, fingerprint = accepted[0]
        route = (f"POST /projects/{context['projectId']}/exports" if item["kind"] == "project"
                 else f"POST /runs/{context['runId']}/exports")
        assert scope.endswith(":" + route)
        payload = {"revision": project["revision"], "inclusionPolicy": "project"} if item["kind"] == "project" else {}
        assert fingerprint == digest(payload)
        with zipfile.ZipFile(io.BytesIO(raw)) as archive:
            entries = archive.infolist()
            assert 0 < len(entries) <= 256 and len({v.filename for v in entries}) == len(entries)
            assert sum(v.file_size for v in entries) <= 16 * 1024 * 1024
            assert all(not v.filename.startswith("/") and ".." not in Path(v.filename).parts for v in entries)
            files = {v.filename: archive.read(v) for v in entries}
        combined = b"\n".join(files.values())
        assert b"urn:keyboard:private-export-exclusion" not in combined and b"keyboard-export-private" not in combined
        assert all(value.encode() not in combined for value in secret_values)
        assert not any("local-bindings" in name or name in {"bootstrap.json", "studio.sqlite", "browser-session.private.json"} for name in files)
        if item["kind"] == "project":
            manifest = json.loads(files["project.studio.json"])
            assert manifest["projectId"] == context["projectId"]
            assert {name: files[name] for name in expected_authored} == expected_authored
            assert json.loads(files["layout/model.json"]) == project["layout"]
            assert not any(name.startswith(("runs/", "evidence/")) or name == "snapshot.json" for name in files)
        else:
            manifest = json.loads(files["manifest.json"])
            assert manifest["kind"] == "studio.evidence" and manifest["integrity"] == "valid"
            assert manifest["files"] == {name: digest(value) for name, value in files.items() if name != "manifest.json"}
            assert files["snapshot.json"] == expected_snapshot and files["evidence/reference.jsonl"] == expected_journal
            run = json.loads(files["run.json"])
            assert run["runId"] == context["runId"] and run["snapshotId"] == context["snapshotId"]
            assert not {"pid", "createTime", "ownerDigest"}.intersection(run)
            assert sorted(json.loads(files["evaluations.json"]), key=lambda v: v["evaluationId"]) == sorted(expected_evaluations, key=lambda v: v["evaluationId"])
            assert sorted(json.loads(files["annotations.json"]), key=lambda v: v["annotationId"]) == sorted(expected_annotations, key=lambda v: v["annotationId"])
        captured.append({"kind": item["kind"], "width": item["width"], "operationId": operation["operationId"],
                         "digest": digest(raw), "bytes": len(raw), "files": len(files), "receiptAndBodyMatch": True,
                         "privateBindingsAndSessionValuesAbsent": True, "sourceContentMatch": True})
    return {"scope": "Actual bounded ZIP readback; no extraction or execution", "downloads": captured,
            "projectDownloads": sum(v["kind"] == "project" for v in captured),
            "evidenceDownloads": sum(v["kind"] == "evidence" for v in captured),
            "originalStoredEvaluations": len(expected_evaluations), "originalStoredAnnotations": len(expected_annotations),
            "privateSessionValuesCheckedWithoutDisclosure": len(secret_values)}
