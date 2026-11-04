"""Four actual evidence uploads on a clean native workspace copy; no runtime."""

import argparse
import importlib.util
import json
import os
from pathlib import Path
import sqlite3
import subprocess
import sys
import uuid

from xverse_studio.host.ownership import own_root
from xverse_studio.storage.core import canonical, digest


_spec = importlib.util.spec_from_file_location(
    "exchange_native_tools", Path(__file__).with_name("autoverse_exchange_native.py")
)
exchange = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(exchange)
native, recorded = exchange.native, exchange.recorded


def imports(root):
    with sqlite3.connect(
        (root / "studio.sqlite").as_uri() + "?mode=ro", uri=True
    ) as db:
        return db.execute(
            "SELECT count(*) FROM records WHERE kind='importedEvidence'"
        ).fetchone()[0]


def main():
    p = argparse.ArgumentParser()
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
    a.output.mkdir(parents=True, exist_ok=False)
    result = json.loads((a.recording / "native-result.json").read_bytes())
    assert (
        result["outcome"] == "passed"
        and result["importsCreateNoRunOperationEvaluation"]
    )
    original = Path(
        json.loads((a.recording / "data-roots.private.json").read_bytes())["target"]
    )
    before = recorded.hashes(original)
    database = digest((original / "studio.sqlite").read_bytes())
    data = (
        native.ROOT
        / ".studio-local/browser-tests"
        / ("exchange-browser-Ω-" + uuid.uuid4().hex)
    )
    exchange.clone(original, data)
    valid = (a.recording / "evidence.zip").read_bytes()
    assert digest(valid) == result["evidenceArchiveDigest"]
    (data / "evidence-valid.zip").write_bytes(valid)
    files = exchange.unpack(valid)
    snapshot = json.loads(files["snapshot.json"])
    context = {
        "sourceRunId": result["sourceRunId"],
        "sourceSnapshotId": result["sourceSnapshotId"],
        "installationDigest": snapshot["providerIdentity"]["installationDigest"],
        "compiledProfileDigest": snapshot["plan"]["profile"]["resourceDigest"]["value"],
    }
    (data / "exchange-recording.private.json").write_text(json.dumps(context))
    files["evidence/reference.jsonl"] += b"Damaged imported canonical evidence\n"
    manifest = json.loads(files["manifest.json"])
    manifest["files"] = {
        name: digest(value) for name, value in files.items() if name != "manifest.json"
    }
    files["manifest.json"] = canonical(manifest).encode()
    import base64

    (data / "evidence-damaged.zip").write_bytes(
        base64.b64decode(exchange.archive(files))
    )
    baseline, import_count = recorded.ledger(data), imports(data)
    host = native.NativeHost(
        data,
        a.output,
        None,
        Path(sys.executable),
        a.static_dir.resolve(),
        register_provider=False,
    )
    outcome = {
        "scope": "Actual Autoverse evidence upload/inspection on a clean target without installed provider; no transport fixture or new execution",
        "before": baseline,
        "importsBefore": import_count,
    }
    exit_code = 1
    try:
        host.start()
        api = native.login(host)
        try:
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
                "tests/live/autoverse-exchange.config.ts",
            ]
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
                try:
                    exit_code = child.wait(timeout=240)
                finally:
                    if child.poll() is None:
                        assert (
                            owner.create_time() == birth and owner.ppid() == os.getpid()
                        )
                        child.terminate()
                        child.wait(timeout=30)
                outcome["originalBrowserExited"] = child.poll() is not None
            outcome["after"], outcome["importsAfter"] = (
                recorded.ledger(data),
                imports(data),
            )
            assert outcome["after"] == baseline
            if exit_code == 0:
                assert outcome["importsAfter"] == import_count + 4
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
    )
    raise SystemExit(exit_code)


if __name__ == "__main__":
    main()
