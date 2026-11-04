"""Installed native package recovery using an actual completed Autoverse recording.

The installed launcher has no external integration configured. It must preserve
recorded bytes and import authority boundaries without starting a new workload.
Only explicit, newly copied workspace roots and original subprocess handles are
used. Full Windows and release acceptance remain separate.
"""

import argparse
import base64
import importlib.util
import json
import os
from pathlib import Path
import shutil
import sqlite3
import subprocess

from xverse_studio.host.ownership import own_root
from xverse_studio.storage.core import digest


_spec = importlib.util.spec_from_file_location(
    "package_exchange_tools", Path(__file__).with_name("autoverse_exchange_native.py")
)
exchange = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(exchange)
native, recorded = exchange.native, exchange.recorded


def metadata(root):
    with sqlite3.connect(
        (root / "studio.sqlite").as_uri() + "?mode=ro", uri=True
    ) as db:
        records = db.execute(
            "SELECT kind,id,body FROM records WHERE kind!='session' ORDER BY kind,id"
        ).fetchall()
        keys = db.execute(
            "SELECT scope,key,fingerprint,result FROM idempotency ORDER BY scope,key"
        ).fetchall()
        sessions = db.execute(
            "SELECT count(*) FROM records WHERE kind='session'"
        ).fetchone()[0]
    return {"records": records, "idempotency": keys}, sessions


def preserved_files(root):
    return {
        p.relative_to(root).as_posix(): digest(p.read_bytes())
        for folder in ("projects", "snapshots", "runs", "evidence-imports")
        for p in (root / folder).rglob("*")
        if p.is_file()
    }


def cli(installed, args, output, name, *, code=None):
    argv = [
        str(installed / ".venv/bin/python"),
        "-I",
        "-m",
        "xverse_studio.host.launcher",
        *map(str, args),
    ]
    (output / (name + "-command.private.json")).write_text(
        json.dumps(argv, indent=2) + "\n"
    )
    child = subprocess.run(
        argv, cwd=installed, stdin=subprocess.DEVNULL, capture_output=True, timeout=90
    )
    (output / (name + ".stdout.private")).write_bytes(child.stdout)
    (output / (name + ".stderr.private")).write_bytes(child.stderr)
    if code:
        assert child.returncode != 0 and code.encode() in child.stderr, (
            name,
            child.returncode,
        )
    else:
        assert child.returncode == 0, (name, child.returncode)
    return json.loads(child.stdout) if not code else child.returncode


def browser(host, api, args, context):
    data = host.data
    (data / "exchange-recording.private.json").write_text(json.dumps(context))
    raw = (args.exchange / "evidence.zip").read_bytes()
    (data / "evidence-valid.zip").write_bytes(raw)
    files = exchange.unpack(raw)
    files["evidence/reference.jsonl"] += b"Damaged imported canonical evidence\n"
    manifest = json.loads(files["manifest.json"])
    manifest["files"] = {n: digest(v) for n, v in files.items() if n != "manifest.json"}
    from xverse_studio.storage.core import canonical

    files["manifest.json"] = canonical(manifest).encode()
    (data / "evidence-damaged.zip").write_bytes(
        base64.b64decode(exchange.archive(files))
    )
    state = {
        "cookies": [
            {
                "name": c.name,
                "value": c.value,
                "domain": c.domain,
                "path": c.path,
                "secure": c.secure,
                "httpOnly": True,
                "sameSite": "Strict",
            }
            for c in api.cookies.jar
        ]
    }
    session = data / "browser-session.private.json"
    session.write_text(json.dumps(state))
    session.chmod(0o600)
    env = dict(
        os.environ,
        STUDIO_BASE_URL=host.url,
        STUDIO_BROWSER_DATA=str(data),
        STUDIO_BROWSER_REPORT=str(args.output / "browser.json"),
        STUDIO_BROWSER_OUTPUT=str(args.output / "browser-artifacts"),
        PLAYWRIGHT_BROWSERS_PATH=str(args.browser_cache.resolve()),
    )
    argv = [
        str(args.node.resolve()),
        str(args.playwright_cli.resolve()),
        "test",
        "--config",
        "tests/live/autoverse-exchange.config.ts",
    ]
    with (args.output / "browser.log").open("xb") as log:
        child = subprocess.Popen(
            argv,
            cwd=native.ROOT,
            env=env,
            stdin=subprocess.DEVNULL,
            stdout=log,
            stderr=subprocess.STDOUT,
        )
        owner = native.psutil.Process(child.pid)
        identity = {"pid": child.pid, "birth": owner.create_time(), "argv": argv}
        (args.output / "browser-owner.private.json").write_text(
            json.dumps(identity, indent=2) + "\n"
        )
        try:
            native.wait(
                lambda: owner.cmdline() == argv and owner.ppid() == os.getpid(),
                bool,
                timeout=3,
            )
            result = child.wait(timeout=240)
        finally:
            if child.poll() is None:
                assert (
                    owner.create_time() == identity["birth"]
                    and owner.ppid() == os.getpid()
                    and owner.cmdline() == argv
                )
                child.terminate()
                child.wait(timeout=30)
        assert child.poll() is not None and result == 0, (
            "Actual installed browser journey failed"
        )
    return {
        "journeysPassed": 1,
        "actualUploads": 4,
        "viewports": [[1024, 768], [1440, 900]],
        "originalBrowserExited": True,
        "transportFixtures": False,
    }


def main():
    p = argparse.ArgumentParser()
    for name in (
        "installed",
        "recording",
        "exchange",
        "output",
        "node",
        "playwright-cli",
        "browser-cache",
    ):
        p.add_argument("--" + name, type=Path, required=True)
    args = p.parse_args()
    args.output = args.output.absolute()
    args.output.mkdir(exist_ok=False)
    installed = args.installed.resolve()
    manifest = json.loads((installed / "package-manifest.json").read_bytes())
    assert manifest["workingTreeDirty"] is False
    assert manifest["nativeVerification"]["Windows"] == "NOT_RUN"
    for name, expected in manifest["files"].items():
        assert digest((installed / name).read_bytes()) == expected, name
    result = json.loads((args.recording / "native-result.json").read_bytes())
    assert result["outcome"] == "passed" and result["fullAndroidAndSpeedObserved"]
    original = Path(
        json.loads((args.recording / "data-root.private.json").read_bytes())["dataRoot"]
    )
    original_hashes, original_db = (
        recorded.hashes(original),
        digest((original / "studio.sqlite").read_bytes()),
    )
    data, backup, restored = [
        args.output / n
        for n in (
            "Native Autoverse Ω data",
            "Private backup 制御",
            "Restored native Ω data",
        )
    ]
    exchange.clone(original, data)
    assert recorded.hashes(data) == original_hashes
    original_files = preserved_files(original)
    initial_ledger = recorded.ledger(data)
    for name in ("source", "restarted", "restored"):
        (args.output / name).mkdir()
    hosts = [
        native.NativeHost(
            data if name != "restored" else restored,
            args.output / name,
            None,
            installed / ".venv/bin/python",
            None,
            register_provider=False,
        )
        for name in ("source", "restarted", "restored")
    ]
    report = {
        "outcome": "failed",
        "candidate": manifest["candidate"],
        "scope": "Actual completed Autoverse recording in a clean installed native Linux package; no new workload or provider/device admission",
    }
    api = None
    try:
        host = hosts[0]
        host.start()
        api = native.login(host)
        capabilities = native.checked(api.get("/api/v1/capabilities"))["studio"]
        assert capabilities["nativeTargets"] == ["Linux", "Windows"]
        assert capabilities["verifiedNativeOS"] == ["Linux"]
        assert capabilities["windowsAcceptance"] == "NOT_RUN"
        # No static-dir argument: test the installed package's own asset discovery.
        index = api.get("/")
        assert index.status_code == 200
        for name in manifest["files"]:
            if name.startswith("apps/studio-web/dist/assets/"):
                r = api.get("/assets/" + name.rsplit("/", 1)[-1])
                assert (
                    r.status_code == 200
                    and digest(r.content) == manifest["files"][name]
                )
        assert (
            index.content
            == (installed / "apps/studio-web/dist/index.html").read_bytes()
        )
        rid, sid = result["runId"], result["snapshotId"]
        run = native.checked(api.get("/api/v1/runs/" + rid))
        assert run["snapshotId"] == sid and run["state"] == "stopped"
        project = native.checked(api.get("/api/v1/projects/" + run["projectId"]))
        compiled = native.checked(
            api.post(
                f"/api/v1/projects/{project['projectId']}/compilations",
                json={"revision": project["revision"]},
            )
        )
        assert compiled["valid"]
        evidence_raw = (args.exchange / "evidence.zip").read_bytes()
        imported = native.checked(
            api.post(
                "/api/v1/evidence/imports",
                json={"archiveBase64": base64.b64encode(evidence_raw).decode()},
            ),
            201,
        )
        assert (
            imported["inspection"]["integrity"] == "unavailable"
            and imported["inspection"]["executionAllowed"] is False
        )
        bundle_id = imported["bundleId"]
        before_live = recorded.hashes(data)
        cli(
            installed,
            ["--data-dir", data, "--backup-full", args.output / "Refused live backup"],
            args.output,
            "backup-live",
            code="RECOVERY_ROOT_OWNED",
        )
        cli(
            installed,
            ["--data-dir", data, "--port", str(host.port)],
            args.output,
            "second-owner",
            code="owned by another",
        )
        assert (
            not (args.output / "Refused live backup").exists()
            and recorded.hashes(data) == before_live
        )
        old_cookies = api.cookies
        api.close()
        api = None
        host.stop()
        hosts[1].start()
        from httpx import Client

        with Client(base_url=hosts[1].url, cookies=old_cookies) as old:
            assert old.get("/api/v1/session").status_code == 200
        api = native.login(hosts[1])
        assert native.checked(api.get("/api/v1/runs/" + rid))["snapshotId"] == sid
        assert (
            native.checked(api.get("/api/v1/evidence/imports/" + bundle_id))[
                "inspection"
            ]
            == imported["inspection"]
        )
        api.close()
        api = None
        hosts[1].stop()
        saved_metadata, sessions = metadata(data)
        assert sessions >= 1
        source_hashes = recorded.hashes(data)
        source_files = preserved_files(data)
        summary = cli(
            installed,
            ["--data-dir", data, "--backup-full", backup],
            args.output,
            "backup-stopped",
        )
        assert summary["integrity"] == "valid"
        assert not (backup / "files/bootstrap.json").exists()
        restored_summary = cli(
            installed,
            ["--data-dir", restored, "--restore-from", backup],
            args.output,
            "restore-new",
        )
        assert (
            restored_summary["sessionsInvalidated"] is True
            and not (restored / ".recovery-incomplete").exists()
        )
        assert metadata(restored) == (saved_metadata, 0)
        assert recorded.hashes(restored) == source_hashes
        assert preserved_files(restored) == source_files
        # Controlled old schema header on an actual-data copy, not an invented
        # claim that an unidentified historical release created this workspace.
        legacy, migration_backup, migrated = [
            args.output / name
            for name in (
                "Controlled schema zero Ω",
                "Migration backup Ω",
                "Migrated native 制御",
            )
        ]
        shutil.copytree(backup / "files", legacy)
        with sqlite3.connect(legacy / "studio.sqlite") as db:
            db.execute("PRAGMA journal_mode=DELETE")
            db.execute("PRAGMA user_version=0")
        legacy_database = digest((legacy / "studio.sqlite").read_bytes())
        migrated_summary = cli(
            installed,
            [
                "--data-dir",
                migrated,
                "--migrate-from",
                legacy,
                "--migration-backup",
                migration_backup,
            ],
            args.output,
            "migrate-copy",
        )
        assert migrated_summary["status"] == "migrated"
        migration_report = json.loads((migrated / "migration-report.json").read_bytes())
        assert migration_report["semanticDiff"]["unchanged"] is True
        assert (
            migration_report["semanticDiff"]["before"]
            == migration_report["semanticDiff"]["after"]
        )
        assert migration_report["sessionsInvalidated"] == sessions
        assert metadata(migrated) == (saved_metadata, 0)
        assert preserved_files(migrated) == source_files
        assert preserved_files(legacy) == source_files
        assert digest((legacy / "studio.sqlite").read_bytes()) == legacy_database
        assert not (migrated / "bootstrap.json").exists()
        migration_output = args.output / "migrated"
        migration_output.mkdir()
        migrated_host = native.NativeHost(
            migrated,
            migration_output,
            None,
            installed / ".venv/bin/python",
            None,
            register_provider=False,
        )
        hosts.append(migrated_host)
        migrated_host.start()
        with native.login(migrated_host) as migrated_api:
            assert (
                native.checked(migrated_api.get("/api/v1/runs/" + rid))["snapshotId"]
                == sid
            )
            migrated_compile = native.checked(
                migrated_api.post(
                    f"/api/v1/projects/{project['projectId']}/compilations",
                    json={"revision": project["revision"]},
                )
            )
            assert (
                migrated_compile["valid"]
                and migrated_compile["planDigest"] == compiled["planDigest"]
            )
        migrated_host.stop()
        # Both backup and destination are private; refuse corruption/overwrite before allocation.
        cli(
            installed,
            ["--data-dir", restored, "--restore-from", backup],
            args.output,
            "restore-existing",
            code="RECOVERY_TARGET_EXISTS",
        )
        corrupt = args.output / "Corrupt backup"
        shutil.copytree(backup, corrupt)
        protected_file = next(
            p for p in (corrupt / "files/snapshots").rglob("snapshot.json")
        )
        protected_file.write_bytes(protected_file.read_bytes() + b"\n")
        rejected = args.output / "Refused corrupt restore"
        cli(
            installed,
            ["--data-dir", rejected, "--restore-from", corrupt],
            args.output,
            "restore-corrupt",
            code="RECOVERY_DIGEST_MISMATCH",
        )
        assert not rejected.exists()
        hosts[2].start()
        with Client(base_url=hosts[2].url, cookies=old_cookies) as old:
            assert old.get("/api/v1/session").status_code == 401
        api = native.login(hosts[2])
        assert (
            native.checked(api.get("/api/v1/projects/" + project["projectId"]))[
                "documents"
            ]
            == project["documents"]
        )
        assert native.checked(api.get("/api/v1/runs/" + rid))["snapshotId"] == sid
        again = native.checked(api.get("/api/v1/evidence/imports/" + bundle_id))
        assert again["inspection"] == imported["inspection"]
        ledger_before = recorded.ledger(restored)
        snapshot = json.loads(exchange.unpack(evidence_raw)["snapshot.json"])
        browser_result = browser(
            hosts[2],
            api,
            args,
            {
                "sourceRunId": rid,
                "sourceSnapshotId": sid,
                "installationDigest": snapshot["providerIdentity"][
                    "installationDigest"
                ],
                "compiledProfileDigest": snapshot["plan"]["profile"]["resourceDigest"][
                    "value"
                ],
            },
        )
        assert recorded.ledger(restored) == ledger_before
        assert recorded.ledger(restored) == initial_ledger
        assert recorded.hashes(restored) == source_hashes
        assert all(
            preserved_files(restored).get(name) == value
            for name, value in source_files.items()
        )
        report.update(
            outcome="passed",
            sourceRunId=rid,
            sourceSnapshotId=sid,
            staticAssetsServedFromPackage=True,
            packagedUiAssetCount=sum(
                n.startswith("apps/studio-web/dist/assets/") for n in manifest["files"]
            ),
            unicodeDataBackupAndRestore=True,
            duplicateRootOwnerRefused=True,
            liveBackupRefused=True,
            restartRetainsUnexpiredSession=True,
            restoreInvalidatesCopiedSessions=True,
            controlledSchemaZeroCopyMigration=True,
            migrationSourceDatabaseUnchanged=True,
            migratedCompilationPlanUnchanged=True,
            migrationInvalidatesCopiedSessions=True,
            migrationStartsNoWorkload=True,
            windowsVerificationNotRun=True,
            backupIntegrity=summary["integrity"],
            restoredAllNonSessionMetadataExactly=True,
            restoredSnapshotsJournalAndProjectBytesExactly=True,
            restoredBrowser=browser_result,
            corruptBackupRefusedBeforeDestination=True,
            overwriteRefused=True,
            originalImportedInspectionPreserved=True,
            noNewRunOperationEvaluation=True,
            limitations=[
                "Native Linux prepared-cache offline installation only; Windows unverified.",
                "No new runtime/provider/hardware execution, full regression, performance or milestone acceptance.",
            ],
        )
    finally:
        if api is not None:
            api.close()
        for host in hosts:
            host.stop()
        for directory in {host.data for host in hosts}:
            if directory.exists():
                with own_root(directory):
                    pass
        assert (
            recorded.hashes(original) == original_hashes
            and digest((original / "studio.sqlite").read_bytes()) == original_db
            and preserved_files(original) == original_files
        )
        report.update(
            originalRecordingUnchanged=True,
            originalBackendInstancesAbsent=sum(len(h.observations) for h in hosts),
            rootOwnershipReleased=True,
        )
        (args.output / "data-roots.private.json").write_text(
            json.dumps({"source": str(data), "restored": str(restored)}, indent=2)
            + "\n"
        )
        (args.output / "verification.json").write_text(
            json.dumps(report, indent=2) + "\n"
        )
    assert report["outcome"] == "passed"
    print(json.dumps(report))


if __name__ == "__main__":
    main()
