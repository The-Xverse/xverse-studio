"""Original Autoverse playback and draft-only journeys on a native copied workspace."""

import argparse
import importlib.util
import json
import os
from pathlib import Path
import shutil
import signal
import sqlite3
import subprocess
import sys
import uuid

from xverse_studio.host.ownership import own_root
from xverse_studio.storage.core import digest


_spec = importlib.util.spec_from_file_location(
    "exchange_native_tools", Path(__file__).with_name("autoverse_exchange_native.py")
)
exchange = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(exchange)
native, recorded = exchange.native, exchange.recorded


def device_free_browser_command(argv):
    """Optional Linux contributor isolation; never an application prerequisite."""
    wrapper = shutil.which("bwrap")
    if not sys.platform.startswith("linux") or wrapper is None:
        raise RuntimeError("BROWSER_DEVICE_ISOLATION_UNAVAILABLE")
    return [
        wrapper,
        "--unshare-user",
        "--uid",
        str(os.getuid()),
        "--gid",
        str(os.getgid()),
        "--ro-bind",
        "/",
        "/",
        "--bind",
        str(native.ROOT),
        str(native.ROOT),
        "--dev",
        "/dev",
        "--tmpfs",
        "/tmp",
        "--tmpfs",
        "/run",
        "--unsetenv",
        "DISPLAY",
        "--unsetenv",
        "WAYLAND_DISPLAY",
        "--unsetenv",
        "XAUTHORITY",
        "--unsetenv",
        "DBUS_SESSION_BUS_ADDRESS",
        "--die-with-parent",
        "--",
        *argv,
    ]


def main():
    def terminate_owned_test(signum, frame):
        raise KeyboardInterrupt("Owned contributor verification interrupted")
    signal.signal(signal.SIGTERM, terminate_owned_test)
    p = argparse.ArgumentParser()
    p.add_argument("--case-filter")
    p.add_argument("--suite", choices=("playback", "diagnostics", "authoring", "lab-inventory", "assessments-keyboard", "exports-keyboard", "bindings-keyboard", "provider-scope", "evaluation-keyboard"), default="playback")
    p.add_argument("--receipt", type=Path, help="Trusted current installation locator for the fixed evaluation suite; the launcher still enrolls the actual installation.")
    p.add_argument(
        "--isolate-browser-devices",
        action="store_true",
        help="Linux contributor-only minimal /dev and software rendering; no application dependency.",
    )
    for name in (
        "recording",
        "static-dir",
        "output",
        "node",
        "playwright-cli",
        "browser-cache",
    ):
        p.add_argument("--" + name, type=Path, required=True)
    a = p.parse_args()
    if a.suite == "exports-keyboard" and a.case_filter:
        p.error("The export suite requires its full matrix for exact operation/import accounting.")
    if (a.suite == "evaluation-keyboard") != (a.receipt is not None):
        p.error("Only the evaluation-keyboard suite requires the explicitly selected installation receipt.")
    if a.receipt is not None:
        a.receipt = a.receipt.resolve(strict=True)
    for name in ("recording", "static_dir", "output", "node", "playwright_cli", "browser_cache"):
        setattr(a, name, getattr(a, name).resolve())
    a.output.mkdir(parents=True, exist_ok=False)
    source_names = subprocess.check_output([
        "git", "ls-files", "--cached", "--others", "--exclude-standard", "-z", "--",
        "apps", "services", "packages", "tests", "config", "scripts", "package.json",
        "package-lock.json", "pyproject.toml", "uv.lock",
    ], cwd=native.ROOT).decode().split("\0")

    def source_inputs():
        return {name: digest((native.ROOT / name).read_bytes()) for name in sorted(set(source_names))
                if name and (native.ROOT / name).is_file()}

    def ui_inputs():
        return {file.relative_to(a.static_dir).as_posix(): digest(file.read_bytes())
                for file in a.static_dir.rglob("*") if file.is_file()}

    source_before, ui_before = source_inputs(), ui_inputs()
    (a.output / "source-inputs.json").write_text(json.dumps(source_before, indent=2) + "\n")
    (a.output / "ui-inputs.json").write_text(json.dumps(ui_before, indent=2) + "\n")
    result = json.loads((a.recording / "native-result.json").read_bytes())
    assert result["outcome"] == "passed" and result["fullAndroidAndSpeedObserved"]
    original = Path(
        json.loads((a.recording / "data-root.private.json").read_bytes())["dataRoot"]
    )
    before = recorded.hashes(original)
    database = digest((original / "studio.sqlite").read_bytes())
    data = (
        native.ROOT
        / ".studio-local/browser-tests"
        / ("recorded-payloads-Ω-" + uuid.uuid4().hex)
    )
    exchange.clone(original, data)
    if a.suite == "evaluation-keyboard":
        # Only the copied private receipt is moved. The normal launcher must
        # enroll current SDK/files/stopped containers rather than adopt old facts.
        with own_root(data):
            receipt = data / "autoverse-installation.private.json"
            if receipt.exists():
                receipt.rename(data / "autoverse-installation.previous.private.json")
    protected_kinds = ("run", "operation", "evaluation", "snapshot", "campaign", "preflight", "project")
    def protected_records():
        with sqlite3.connect((data / "studio.sqlite").as_uri() + "?mode=ro", uri=True) as db:
            return {(kind, key): json.loads(body) for kind, key, body in db.execute("SELECT kind,id,body FROM records") if kind in protected_kinds}
    original_records = protected_records()
    def idempotency_records():
        with sqlite3.connect((data / "studio.sqlite").as_uri() + "?mode=ro", uri=True) as db:
            return {(scope, key): (fingerprint, json.loads(result)) for scope, key, fingerprint, result in db.execute("SELECT scope,key,fingerprint,result FROM idempotency")}
    original_receipts = idempotency_records()
    rows = [
        json.loads(line)
        for line in (original / "runs" / result["runId"] / "evidence.jsonl")
        .read_bytes()
        .splitlines()
    ]
    observations = [row for row in rows if row["type"] == "observation.available"]
    assert len(observations) == 21
    snapshot = json.loads(
        (original / "snapshots" / result["snapshotId"] / "snapshot.json").read_bytes()
    )
    context = {
        "runId": result["runId"],
        "snapshotId": result["snapshotId"],
        "projectId": snapshot["projectId"],
        "records": observations,
    }
    (data / "playback-recording.private.json").write_text(json.dumps(context))
    baseline = recorded.ledger(data)
    def record_count(kind):
        with sqlite3.connect((data / "studio.sqlite").as_uri() + "?mode=ro", uri=True) as db:
            return db.execute("SELECT count(*) FROM records WHERE kind=?", (kind,)).fetchone()[0]
    imported_before = {kind: record_count(kind) for kind in ("project", "importedEvidence")}
    host = native.NativeHost(
        data,
        a.output,
        a.receipt,
        Path(sys.executable),
        a.static_dir.resolve(),
        register_provider=a.suite == "evaluation-keyboard",
    )
    outcome = {
        "scope": ("Actual original Autoverse recording; genuine fresh installed mapping and derived evaluation submissions; no model or guest start"
                  if a.suite == "evaluation-keyboard" else
                  "Actual original Autoverse recording; fixed playback/authoring/export suites on private copies; labelled HTTP fixtures; no model or evaluation start"),
        "suite": a.suite,
        "sourceCandidate": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=native.ROOT, text=True).strip(),
        "before": baseline,
        "originalObservationRecords": len(observations),
    }
    exit_code = 1
    try:
        host.start()
        api = native.login(host)
        try:
            if a.suite == "evaluation-keyboard":
                support = native.checked(api.get(f"/api/v1/runs/{context['runId']}/assessment-support"))
                definitions = native.checked(api.get(f"/api/v1/runs/{context['runId']}/definitions"))["items"]
                assert support["status"] == "supported" and len(definitions) == 6
                context["historicalEvaluations"] = native.checked(api.get(f"/api/v1/runs/{context['runId']}/evaluations"))["items"]
                assert len(context["historicalEvaluations"]) == 6
                (data / "playback-recording.private.json").write_text(json.dumps(context))
                assert (data / "autoverse-installation.private.json").is_file()
                (a.output / "installed-evaluation-support.json").write_text(json.dumps(support, indent=2) + "\n")
            if a.suite == "exports-keyboard":
                binding = native.checked(api.get(f"/api/v1/projects/{context['projectId']}/local-bindings"))
                assert binding["state"] == "empty"
                declared = native.checked(api.put(f"/api/v1/projects/{context['projectId']}/local-bindings",
                    headers={"If-Match": str(binding["bindingRevision"])}, json={"formatVersion": "1.0", "bindings": [{
                        "bindingId": "keyboard-export-private", "kind": "credential", "reference": "urn:keyboard:local-only",
                        "providerId": "autoverse.demo", "credentialRef": "urn:keyboard:private-export-exclusion"}]}))
                assert declared["validation"] == "unverified" and declared["executionAllowed"] is False
            cookies = {
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
            session.write_text(json.dumps(cookies))
            session.chmod(0o600)
            env = dict(
                os.environ,
                STUDIO_BASE_URL=host.url,
                STUDIO_BROWSER_DATA=str(data),
                STUDIO_BROWSER_REPORT=str(a.output / "browser.json"),
                STUDIO_BROWSER_OUTPUT=str(a.output / "artifacts"),
                PLAYWRIGHT_BROWSERS_PATH=str(a.browser_cache.resolve()),
            )
            argv = [
                str(a.node.resolve()),
                str(a.playwright_cli.resolve()),
                "test",
                "--config",
                {
                    "playback": "tests/live/autoverse-recorded-payloads.config.ts",
                    "diagnostics": "tests/live/autoverse-diagnostic-keyboard.config.ts",
                    "authoring": "tests/live/autoverse-authoring-keyboard.config.ts",
                    "lab-inventory": "tests/live/autoverse-lab-inventory-keyboard.config.ts",
                    "assessments-keyboard": "tests/live/autoverse-assessments-keyboard.config.ts",
                    "exports-keyboard": "tests/live/autoverse-exports-keyboard.config.ts",
                    "bindings-keyboard": "tests/live/autoverse-bindings-keyboard.config.ts",
                    "provider-scope": "tests/live/autoverse-provider-scope.config.ts",
                    "evaluation-keyboard": "tests/live/autoverse-evaluation-keyboard.config.ts",
                }[a.suite],
            ]
            if a.case_filter:
                argv.extend(["--grep", a.case_filter])
            if a.isolate_browser_devices:
                env["STUDIO_BROWSER_CPU_ONLY"] = "1"
                env["STUDIO_BROWSER_DEVICE_PROOF"] = str(
                    a.output.resolve() / "browser-device-proof.private.json"
                )
                env["STUDIO_BROWSER_HOST_MOUNT_NS"] = os.readlink("/proc/self/ns/mnt")
                argv = device_free_browser_command(argv)
            (a.output / "command.private.json").write_text(
                json.dumps({"argv": argv}, indent=2) + "\n"
            )
            with (a.output / "browser.log").open("xb") as log:
                child = subprocess.Popen(
                    argv,
                    cwd=native.ROOT,
                    env=env,
                    stdin=subprocess.DEVNULL,
                    stdout=log,
                    stderr=subprocess.STDOUT,
                )
                owner = native.psutil.Process(child.pid)
                birth = owner.create_time()
                native.wait(
                    lambda: owner.cmdline() == argv and owner.ppid() == os.getpid(),
                    bool,
                    timeout=3,
                )
                (a.output / "browser-owner.private.json").write_text(
                    json.dumps({"pid": child.pid, "birth": birth, "argv": argv}) + "\n"
                )
                try:
                    exit_code = child.wait(timeout=360)
                finally:
                    if child.poll() is None:
                        assert (
                            owner.create_time() == birth
                            and owner.ppid() == os.getpid()
                            and owner.cmdline() == argv
                        )
                        child.terminate()
                        child.wait(timeout=30)
                outcome["originalBrowserExited"] = child.poll() is not None
            outcome["after"] = recorded.ledger(data)
            expected = ({**baseline, "operation": baseline["operation"] + 8, "idempotency": baseline["idempotency"] + 8}
                        if a.suite == "exports-keyboard" else baseline)
            if a.suite == "evaluation-keyboard":
                after_records = protected_records()
                checker_spec = importlib.util.spec_from_file_location("evaluation_record_readback", Path(__file__).with_name("autoverse_evaluation_records.py"))
                checker = importlib.util.module_from_spec(checker_spec)
                checker_spec.loader.exec_module(checker)
                outcome["protectedRecordReadback"] = checker.verify_protected_records(original_records, after_records, context["runId"], context["snapshotId"])
                added = {key: value for key, value in after_records.items() if key not in original_records}
                evaluations = {key[1]: value for key, value in added.items() if key[0] == "evaluation"}
                operations = {key[1]: value for key, value in added.items() if key[0] == "operation"}
                assert set(key[0] for key in added) <= {"evaluation", "operation"}
                count = len(evaluations)
                assert len(operations) == count <= 24
                if exit_code == 0 and not a.case_filter:
                    assert count == 24
                for row in evaluations.values():
                    definition = next(d for d in definitions if d["definitionRef"] == row["definitionRef"])
                    assert row["runId"] == context["runId"] and row["snapshotId"] == context["snapshotId"]
                    assert row["definitionDigest"] == definition["definitionDigest"] and row["status"] in {"complete", "error"}
                    assert row["evidenceMapping"] == support and row["evidenceRefs"] == [support["evidenceId"]]
                    operation = operations[row["operationId"]]
                    assert operation["kind"] == "evaluation" and operation["evaluationId"] == row["evaluationId"]
                    assert operation["status"] == ("completed" if row["status"] == "complete" else "failed")
                    assert operation["result"] == {"evaluationId": row["evaluationId"], "status": row["status"], "verdict": row["verdict"]}
                current_receipts = idempotency_records()
                assert all(current_receipts.get(key) == value for key, value in original_receipts.items())
                new_receipts = {key: value for key, value in current_receipts.items() if key not in original_receipts}
                assert len(new_receipts) == count
                for (scope, _), (fingerprint, result) in new_receipts.items():
                    assert scope.endswith(f":POST /runs/{context['runId']}/evaluations")
                    assert result["evaluationId"] in evaluations and result["operationId"] == evaluations[result["evaluationId"]]["operationId"]
                    row = evaluations[result["evaluationId"]]
                    assert fingerprint == digest({key: row[key] for key in ("snapshotId", "definitionRef", "definitionDigest", "evidenceRefs")})
                expected = {**baseline, **{kind: baseline[kind] + count for kind in ("operation", "evaluation", "idempotency")}}
                outcome["newDerivedEvaluations"] = count
                outcome["oldProtectedRecordsAndDerivedIndexVerified"] = True
                outcome["failedCohortMayStopBeforeFullMatrix"] = exit_code != 0
            outcome["expectedExecutionCounts"] = expected
            assert outcome["after"] == expected
            if a.suite == "exports-keyboard":
                outcome["importsBefore"] = imported_before
                outcome["importsAfter"] = {kind: record_count(kind) for kind in imported_before}
                assert outcome["importsAfter"] == {kind: count + 2 for kind, count in imported_before.items()}
                spec = importlib.util.spec_from_file_location("export_download_readback", Path(__file__).with_name("autoverse_export_downloads.py"))
                readback = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(readback)
                verified = readback.verify_downloads(a.output, data, context)
                (a.output / "export-readback.json").write_text(json.dumps(verified, indent=2) + "\n")
        finally:
            api.close()
    finally:
        host.stop()
        with own_root(data):
            outcome["originalRootReleased"] = True
        outcome["originalRecordingUnchanged"] = (
            recorded.hashes(original) == before
            and digest((original / "studio.sqlite").read_bytes()) == database
        )
        copied = recorded.hashes(data)
        outcome["copiedOriginalCanonicalUnchanged"] = all(
            copied.get(k) == v for k, v in before.items()
        )
        outcome["backendShutdown"] = host.observations
        outcome["sourceInputsUnchanged"] = source_inputs() == source_before
        outcome["uiInputsUnchanged"] = ui_inputs() == ui_before
        outcome["browserExit"] = exit_code
        (a.output / "data-root.private.json").write_text(
            json.dumps({"dataRoot": str(data)}) + "\n"
        )
        (a.output / "verification.json").write_text(
            json.dumps(outcome, indent=2) + "\n"
        )
    assert (
        outcome["originalRecordingUnchanged"]
        and outcome["copiedOriginalCanonicalUnchanged"]
        and outcome["sourceInputsUnchanged"]
        and outcome["uiInputsUnchanged"]
    )
    raise SystemExit(exit_code)


if __name__ == "__main__":
    main()
