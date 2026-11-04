"""Actual Autoverse project/evidence exchange between isolated native workspaces.

Only the source copy registers the prepared provider. The clean target uses the
ordinary launcher without an installed Autoverse integration. Import/reopen,
canonical bytes, derived results and local-binding refusals require no workload.
"""

import argparse
import base64
import importlib.util
import io
import json
from pathlib import Path
import shutil
import sqlite3
import sys
import uuid
import zipfile

from xverse_studio.host.ownership import own_root
from xverse_studio.storage.core import canonical, digest


_spec = importlib.util.spec_from_file_location(
    "native_recording_exchange",
    Path(__file__).with_name("autoverse_campaign_browser.py"),
)
recorded = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(recorded)
native = recorded.native


def clone(original, destination):
    with own_root(original):
        assert all(not p.is_symlink() for p in original.rglob("*"))
        shutil.copytree(
            original,
            destination,
            ignore=shutil.ignore_patterns(
                "studio.lock",
                "studio.sqlite*",
                "bootstrap.json",
                "browser-session.private.json",
            ),
        )
        with (
            sqlite3.connect(
                (original / "studio.sqlite").as_uri() + "?mode=ro", uri=True
            ) as source,
            sqlite3.connect(destination / "studio.sqlite") as target,
        ):
            source.backup(target)
            target.execute("DELETE FROM records WHERE kind='session'")


def unpack(raw):
    with zipfile.ZipFile(io.BytesIO(raw)) as archive:
        return {name: archive.read(name) for name in archive.namelist()}


def archive(files):
    stream = io.BytesIO()
    with zipfile.ZipFile(stream, "w", compression=zipfile.ZIP_STORED) as bundle:
        for name, raw in files.items():
            bundle.writestr(name, raw)
    return base64.b64encode(stream.getvalue()).decode()


def sources(project):
    return {doc["path"]: doc["content"] for doc in project["documents"].values()}


def main():
    parser = argparse.ArgumentParser()
    for name in ("recording", "receipt", "static-dir", "output"):
        parser.add_argument("--" + name, type=Path, required=True)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=False)
    original_result = json.loads((args.recording / "native-result.json").read_bytes())
    assert (
        original_result["outcome"] == "passed"
        and original_result["fullAndroidAndSpeedObserved"]
    )
    original = Path(
        json.loads((args.recording / "data-root.private.json").read_bytes())["dataRoot"]
    )
    protected = recorded.hashes(original)
    original_database = digest((original / "studio.sqlite").read_bytes())
    token = uuid.uuid4().hex
    roots = [
        native.ROOT / ".studio-local/browser-tests" / (prefix + token)
        for prefix in (
            "exchange-source-Ω-",
            "exchange-target-制御-",
            "exchange-moved-Ω-",
        )
    ]
    source_root, target_root, moved_root = roots
    clone(original, source_root)
    assert recorded.hashes(source_root) == protected
    target_root.mkdir(mode=0o700)
    (args.output / "source").mkdir()
    (args.output / "target").mkdir()
    (args.output / "moved").mkdir()
    source_host = native.NativeHost(
        source_root,
        args.output / "source",
        args.receipt.resolve(),
        Path(sys.executable),
        args.static_dir.resolve(),
    )
    target_host = native.NativeHost(
        target_root,
        args.output / "target",
        None,
        Path(sys.executable),
        args.static_dir.resolve(),
        register_provider=False,
    )
    moved_host = native.NativeHost(
        moved_root,
        args.output / "moved",
        None,
        Path(sys.executable),
        args.static_dir.resolve(),
        register_provider=False,
    )
    report = {
        "outcome": "failed",
        "scope": "Actual recorded Autoverse export and inert import between native Linux workspaces; no new workload, provider/device admission or evaluation",
    }
    apis = []
    try:
        source_host.start()
        source = native.login(source_host)
        apis.append(source)
        rid = original_result["runId"]
        run = native.checked(source.get("/api/v1/runs/" + rid))
        project = native.checked(source.get("/api/v1/projects/" + run["projectId"]))
        pid = project["projectId"]
        compiled = native.checked(
            source.post(
                f"/api/v1/projects/{pid}/compilations",
                json={"revision": project["revision"]},
            )
        )
        assert compiled["valid"]
        local = native.checked(source.get(f"/api/v1/projects/{pid}/local-bindings"))
        assert local["state"] == "empty"
        declared = native.checked(
            source.put(
                f"/api/v1/projects/{pid}/local-bindings",
                headers={"If-Match": "0"},
                json={
                    "formatVersion": "1.0",
                    "bindings": [
                        {
                            "bindingId": "exchange-local-credential",
                            "kind": "credential",
                            "reference": "urn:exchange:private-binding",
                            "providerId": "autoverse.demo",
                            "credentialRef": "urn:exchange:external-handle",
                        }
                    ],
                },
            )
        )
        assert (
            declared["validation"] == "unverified"
            and declared["executionAllowed"] is False
        )
        comment = native.checked(
            source.post(
                f"/api/v1/runs/{rid}/annotations",
                json={"kind": "comment", "text": "Native exchange review"},
            ),
            201,
        )
        revised = native.checked(
            source.put(
                "/api/v1/annotations/" + comment["annotationId"],
                headers={"If-Match": "1"},
                json={
                    "kind": "comment",
                    "text": "Native exchange reviewed",
                    "revision": 1,
                },
            )
        )
        assert revised["revision"] == 2 and len(revised["history"]) == 1
        native.checked(
            source.post(
                f"/api/v1/runs/{rid}/annotations",
                json={
                    "kind": "trace_link",
                    "target": {
                        "uri": "urn:requirement:exchange:1",
                        "revision": "rev-1",
                    },
                },
            ),
            201,
        )

        def export(route, body, key):
            accepted = native.checked(
                source.post(route, headers={"Idempotency-Key": key}, json=body), 202
            )
            raw = source.get(accepted["result"]["downloadUrl"])
            assert (
                raw.status_code == 200
                and digest(raw.content) == accepted["result"]["digest"]
            )
            assert (
                native.checked(
                    source.post(route, headers={"Idempotency-Key": key}, json=body), 202
                )
                == accepted
            )
            return raw.content, accepted

        project_zip, project_export = export(
            f"/api/v1/projects/{pid}/exports",
            {"revision": project["revision"]},
            "native-portable-project",
        )
        evidence_zip, evidence_export = export(
            f"/api/v1/runs/{rid}/exports", {}, "native-recorded-evidence"
        )
        project_files, evidence_files = unpack(project_zip), unpack(evidence_zip)
        assert {
            name: project_files[name].decode() for name in sources(project)
        } == sources(project)
        assert not any("local-bindings" in name for name in project_files)
        assert b"urn:exchange:external-handle" not in b"".join(project_files.values())
        assert (
            evidence_files["snapshot.json"]
            == (
                source_root / "snapshots" / run["snapshotId"] / "snapshot.json"
            ).read_bytes()
        )
        assert (
            evidence_files["evidence/reference.jsonl"]
            == (source_root / "runs" / rid / "evidence.jsonl").read_bytes()
        )
        derived = json.loads(evidence_files["evaluations.json"])
        assert len(derived) == 6 and {v["verdict"] for v in derived} >= {
            "pass",
            "fail",
            "indeterminate",
            None,
        }
        annotations = json.loads(evidence_files["annotations.json"])
        assert any(a["revision"] == 2 and len(a["history"]) == 1 for a in annotations)
        source_cookie = source.cookies.get("studio_session")
        (args.output / "project.zip").write_bytes(project_zip)
        (args.output / "evidence.zip").write_bytes(evidence_zip)
        source.close()
        source_host.stop()
        with own_root(source_root):
            assert recorded.hashes(source_root) == protected
        target_host.start()
        target = native.login(target_host)
        apis.append(target)
        assert (
            target.get(
                "/api/v1/projects",
                headers={"Cookie": "studio_session=" + source_cookie},
            ).status_code
            == 401
        )
        assert native.checked(target.get("/api/v1/projects"))["items"] == []
        assert native.checked(target.get("/api/v1/runs"))["items"] == []
        imported = native.checked(
            target.post(
                "/api/v1/projects/imports",
                json={"archiveBase64": base64.b64encode(project_zip).decode()},
            ),
            201,
        )
        imported_pid = imported["projectId"]
        assert imported_pid != pid and sources(imported) == sources(project)
        assert imported["layout"] == project["layout"]
        target_compiled = native.checked(
            target.post(
                f"/api/v1/projects/{imported_pid}/compilations",
                json={"revision": imported["revision"]},
            )
        )
        assert target_compiled["valid"] and all(
            target_compiled[k] == compiled[k]
            for k in ("planDigest", "semanticDigest", "plan")
        )
        target_bindings = native.checked(
            target.get(f"/api/v1/projects/{imported_pid}/local-bindings")
        )
        assert (
            target_bindings["state"] == "empty"
            and target_bindings["executionAllowed"] is False
        )
        (source_binding,) = (source_root / "projects" / pid / "local-bindings").glob(
            "*.json"
        )
        hostile = {
            **project_files,
            "local-bindings/captured.json": source_binding.read_bytes(),
        }
        rejected = target.post(
            "/api/v1/projects/imports", json={"archiveBase64": archive(hostile)}
        )
        assert (
            rejected.status_code == 422 and rejected.json()["code"] == "UNSAFE_ARCHIVE"
        ), rejected.text[:500]
        assert len(native.checked(target.get("/api/v1/projects"))["items"]) == 1
        # The target has no installed provider; importing its pins cannot add one.
        before_import = recorded.ledger(target_root)
        imported_evidence = native.checked(
            target.post(
                "/api/v1/evidence/imports",
                json={"archiveBase64": base64.b64encode(evidence_zip).decode()},
            ),
            201,
        )
        inspection = imported_evidence["inspection"]
        assert (
            inspection["executionAllowed"] is False
            and inspection["declaredEvidenceScope"] == "external_demo"
        )
        assert (
            inspection["journalIntegrity"] == "unavailable"
            and "SOURCE_PROVIDER_READER_UNSUPPORTED" in inspection["diagnostics"]
        )
        assert (
            imported_evidence["evaluations"] == derived
            and imported_evidence["annotations"] == annotations
        )
        assert recorded.ledger(target_root) == before_import
        damaged = dict(evidence_files)
        damaged["evidence/reference.jsonl"] += b"Damaged imported canonical evidence\n"
        manifest = json.loads(damaged["manifest.json"])
        manifest["files"] = {
            name: digest(value)
            for name, value in damaged.items()
            if name != "manifest.json"
        }
        damaged["manifest.json"] = canonical(manifest).encode()
        damaged_evidence = native.checked(
            target.post(
                "/api/v1/evidence/imports", json={"archiveBase64": archive(damaged)}
            ),
            201,
        )
        assert (
            damaged_evidence["inspection"]["integrity"] == "invalid"
            and damaged_evidence["inspection"]["executionAllowed"] is False
        )
        assert damaged_evidence["report"]["integrity"] == "valid"
        blocked = native.checked(
            target.post(
                f"/api/v1/projects/{imported_pid}/preflights",
                json={"revision": imported["revision"], "providerId": "autoverse.demo"},
            )
        )
        assert (
            blocked["status"] == "blocked" and blocked["providerId"] == "autoverse.demo"
        )
        assert native.checked(target.get("/api/v1/runs"))["items"] == []
        # Imported evidence never becomes an owned run or rerun source.
        refused = target.post(
            f"/api/v1/runs/{imported_evidence['bundleId']}/reruns",
            headers={"Idempotency-Key": "inert-import-no-rerun"},
            json={},
        )
        assert refused.status_code == 404
        target.close()
        target_host.stop()
        target_host.start()
        target = native.login(target_host)
        apis.append(target)
        reopened = native.checked(target.get(f"/api/v1/projects/{imported_pid}"))
        assert sources(reopened) == sources(project)
        assert (
            native.checked(
                target.get("/api/v1/evidence/imports/" + imported_evidence["bundleId"])
            )["inspection"]
            == inspection
        )
        assert (
            native.checked(
                target.get("/api/v1/evidence/imports/" + damaged_evidence["bundleId"])
            )["inspection"]["integrity"]
            == "invalid"
        )
        assert native.checked(target.get("/api/v1/runs"))["items"] == []
        target.close()
        target_host.stop()
        clone(source_root, moved_root)
        moved_host.start()
        moved = native.login(moved_host)
        apis.append(moved)
        moved_bindings = native.checked(
            moved.get(f"/api/v1/projects/{pid}/local-bindings")
        )
        assert (
            moved_bindings["state"] == "needs_review"
            and moved_bindings["environmentChanged"] is True
        )
        assert (
            moved_bindings["executionAllowed"] is False
            and moved_bindings["validation"] == "unverified"
        )
        moved_project = native.checked(moved.get(f"/api/v1/projects/{pid}"))
        assert sources(moved_project) == sources(project)
        moved_compiled = native.checked(
            moved.post(
                f"/api/v1/projects/{pid}/compilations",
                json={"revision": moved_project["revision"]},
            )
        )
        assert (
            moved_compiled["semanticDigest"] == compiled["semanticDigest"]
            and moved_compiled["planDigest"] == compiled["planDigest"]
        )
        moved.close()
        moved_host.stop()
        assert recorded.hashes(source_root) == recorded.hashes(moved_root) == protected
        report.update(
            outcome="passed",
            sourceRunId=rid,
            sourceSnapshotId=run["snapshotId"],
            sourceProjectId=pid,
            importedProjectId=imported_pid,
            projectArchiveDigest=digest(project_zip),
            evidenceArchiveDigest=digest(evidence_zip),
            sourceSemanticDigest=compiled["semanticDigest"],
            sourcePlanDigest=compiled["planDigest"],
            exactSourcesPreserved=True,
            exactSnapshotAndJournalPreserved=True,
            derivedEvaluationsPreserved=len(derived),
            annotationsPreserved=len(annotations),
            importedEvidenceId=imported_evidence["bundleId"],
            damagedEvidenceId=damaged_evidence["bundleId"],
            inspection=inspection,
            privateBindingExcluded=True,
            privateBindingImportRefused=True,
            movedPrivateBindingNeedsReview=True,
            missingInstalledProviderBlocksExecution=True,
            importsCreateNoRunOperationEvaluation=True,
            cleanTargetRestartPreservesInspection=True,
            foreignSessionRefused=True,
            projectExport=project_export["result"],
            evidenceExport=evidence_export["result"],
            targetLedger=recorded.ledger(target_root),
        )
    finally:
        for api in apis:
            api.close()
        for host in (source_host, target_host, moved_host):
            host.stop()
        for path in roots:
            if path.exists():
                with own_root(path):
                    pass
        report["hostShutdown"] = {
            "source": source_host.observations,
            "target": target_host.observations,
            "moved": moved_host.observations,
        }
        report["originalRecordingUnchanged"] = recorded.hashes(original) == protected
        report["originalDatabaseUnchanged"] = (
            digest((original / "studio.sqlite").read_bytes()) == original_database
        )
        (args.output / "data-roots.private.json").write_text(
            json.dumps(
                dict(zip(("source", "target", "moved"), map(str, roots))), indent=2
            )
            + "\n"
        )
        (args.output / "native-result.json").write_text(
            json.dumps(report, indent=2) + "\n"
        )
    assert (
        report["outcome"] == "passed"
        and report["originalRecordingUnchanged"]
        and report["originalDatabaseUnchanged"]
    )


if __name__ == "__main__":
    main()
