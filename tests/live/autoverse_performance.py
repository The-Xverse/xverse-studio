"""Declared authoring/history benchmarks based on copied actual Autoverse inputs.

Generated load is explicitly synthetic and inert. It grants no runtime authority,
modifies no original recording, and never calls preflight or starts a provider.
"""

from copy import deepcopy
from datetime import datetime, timedelta, timezone
import hashlib
import importlib.util
import json
from pathlib import Path
import time

from ruamel.yaml import YAML

from xverse_studio.evidence.reader import read_journal
from xverse_studio.runs.service import Runs
from xverse_studio.storage.core import canonical, uid
from xverse_studio.xdl.examples import dump_yaml


_spec = importlib.util.spec_from_file_location(
    "performance_exchange_tools",
    Path(__file__).with_name("autoverse_exchange_native.py"),
)
exchange = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(exchange)
native, recorded = exchange.native, exchange.recorded


def model_fixture(projects, portable):
    files = exchange.unpack(portable)
    manifest = json.loads(files["project.studio.json"])
    manifest["name"] = (
        "Autoverse load · 200 visible elements / 400 connections · " + uid("case-")[-8:]
    )
    files["project.studio.json"] = canonical(manifest).encode()
    project = projects.import_archive(exchange.archive(files))
    yaml = YAML(typ="safe")
    resources = {k: yaml.load(v["content"]) for k, v in project["documents"].items()}
    system_id = next(k for k, v in resources.items() if v["kind"] == "System")
    deployment_id = next(k for k, v in resources.items() if v["kind"] == "Deployment")
    scenario_id = next(k for k, v in resources.items() if v["kind"] == "Scenario")
    system = resources[system_id]
    spec = system["spec"]
    count = len(spec["componentInstances"]) + len(spec["devices"])
    # A placement node without a component instance is also a visible Element
    # projection. Retain the actual device/node separation instead of silently
    # dropping those original Autoverse objects to fit a benchmark assertion.
    occupied = {v.get("nodeId") for v in spec["componentInstances"]}
    placements = sum(v["id"] not in occupied for v in spec["nodes"])
    count += placements
    base = spec["componentInstances"][0]
    component = next(
        v
        for v in resources.values()
        if v["kind"] == "Component"
        and v["metadata"]["name"] == base["componentRef"]["name"]
    )
    interface = component["spec"]["interfaces"][0]["id"]
    deployment = resources[deployment_id]
    base_binding = next(
        v
        for v in deployment["spec"]["bindings"]
        if v["logicalRef"].get("element") == base["id"]
    )
    owners = [base["id"]]
    added = []
    for i in range(200 - count):
        name = f"load-element-{i:03d}"
        added.append(name)
        owners.append(name)
        spec["nodes"].append(
            {"id": name + "-node", "roles": ["Synthetic Autoverse authoring load"]}
        )
        spec["componentInstances"].append(
            {**deepcopy(base), "id": name, "nodeId": name + "-node"}
        )
        binding = deepcopy(base_binding)
        binding["id"] = name + "-binding"
        binding["logicalRef"]["element"] = name
        deployment["spec"]["bindings"].append(binding)
    spec["endpoints"] = [
        {
            "id": f"load-{direction}-{i}",
            "ownerId": name,
            "interfaceId": interface,
            "direction": direction,
        }
        for i, name in enumerate(owners)
        for direction in ["input", "output"]
    ]
    pairs = []
    for delta in [1, 2, 3]:
        for i in range(len(owners) - delta):
            pairs.append((i, i + delta))
            if len(pairs) == 400:
                break
        if len(pairs) == 400:
            break
    assert len(pairs) == 400
    previous_flows = {v["id"] for v in spec["flows"]}
    spec["flows"] = [
        {
            "id": f"load-flow-{i:03d}",
            "sourceEndpointId": f"load-output-{source}",
            "destinationEndpointIds": [f"load-input-{target}"],
            "interfaceId": interface,
            "timeDomainId": spec["defaultTimeDomainId"],
            "deliveryIntent": "best-effort",
        }
        for i, (source, target) in enumerate(pairs)
    ]
    scenario = resources[scenario_id]
    for observer in scenario["spec"].get("observers", []):
        target = observer.get("targetRef", {})
        if target.get("kind") == "System" and target.get("element") in previous_flows:
            target["element"] = spec["flows"][0]["id"]
    for doc_id, resource in [
        (system_id, system),
        (deployment_id, deployment),
        (scenario_id, scenario),
    ]:
        project = projects.save(
            project["projectId"],
            doc_id,
            project["revision"],
            dump_yaml(resource),
            "yaml",
        )
    sources = projects.sources(project)
    validated = projects.adapter.validate(sources)
    compiled = projects.adapter.compile(sources)
    assert validated["valid"], validated
    assert compiled["valid"], compiled
    return project, {
        "projectId": project["projectId"],
        "projectName": project["name"],
        "revision": project["revision"],
        "elements": 200,
        "logicalAssets": 200 - placements,
        "standalonePlacementNodes": placements,
        "connections": 400,
        "selectionIds": added[:31],
        "semanticDigest": compiled["semanticDigest"],
        "planDigest": compiled["planDigest"],
        "authoritativeValidation": True,
        "authoritativeCompilation": True,
        "scope": "Synthetic authoring load based on the actual Autoverse project; no runtime fidelity or admission",
    }


def history_fixture(store, projects, original_run_id):
    adapter = projects.adapter
    runs = Runs(store, projects, adapter)
    source = store.get("run", original_run_id)
    assert (
        source["providerId"] == "autoverse.demo"
        and source["state"] == "stopped"
        and source["evidenceScope"] == "external_demo"
    )
    snapshot = store.get("snapshot", source["snapshotId"])
    runs.verify_snapshot(snapshot)
    records, integrity = read_journal(runs.directory(original_run_id), source)
    assert integrity == "valid" and records
    run_id, operation_id = uid("run-autoverse-load-"), uid("op-autoverse-load-")
    destination = runs.directory(run_id)
    destination.mkdir(exist_ok=False)
    journal = destination / "evidence.jsonl"
    previous = "0" * 64
    whole = hashlib.sha256()
    epoch = datetime(2026, 11, 4, tzinfo=timezone.utc)
    with journal.open("xb") as stream:
        for index in range(1, 50001):
            record = {
                "schemaVersion": "1.0",
                "eventId": f"{run_id}:record-{index}",
                "runId": run_id,
                "snapshotId": snapshot["snapshotId"],
                "sequence": str(index),
                "type": "log.appended",
                "recordedAt": (epoch + timedelta(milliseconds=index)).isoformat(),
                "source": {
                    "providerId": "owned.recorded-fixture",
                    "kind": "synthetic-autoverse-load",
                },
                "elementRefs": [],
                "evidenceClass": "inferred",
                "evidenceRefs": [],
                "payload": {
                    "severity": "info",
                    "message": f"Synthetic Autoverse benchmark log {index:05d}",
                    "scope": "Generated load only; no simulator or device observation.",
                },
                "previousDigest": previous,
            }
            previous = hashlib.sha256(canonical(record).encode()).hexdigest()
            line = (canonical({**record, "digest": previous}) + "\n").encode()
            stream.write(line)
            whole.update(line)
    run = {
        "runId": run_id,
        "snapshotId": snapshot["snapshotId"],
        "projectId": source["projectId"],
        "revision": snapshot["revision"],
        "operationId": operation_id,
        "state": "stopped",
        "stateVersion": 1,
        "cleanup": "not_applicable",
        "evidence": "complete",
        "evaluation": "not_started",
        "verdict": None,
        "capabilities": [],
        "evidenceScope": "recorded_fixture",
        "providerId": "owned.recorded-fixture",
        "createdAt": time.time(),
        "endedAt": time.time(),
        "planDigest": snapshot["planDigest"],
        "semanticDigest": snapshot["semanticDigest"],
        "journalDigest": "sha256:" + whole.hexdigest(),
        "eventCount": 50000,
        "sourceRunId": original_run_id,
        "limitations": [
            "Synthetic Autoverse history benchmark, not captured observations.",
            "Existing frozen snapshot is reused as input provenance only; no execution or provider authority.",
        ],
    }
    generated, checked = read_journal(destination, run)
    assert len(generated) == 50000 and checked == "valid"
    with store.tx() as db:
        store.put(
            "operation",
            operation_id,
            {
                "operationId": operation_id,
                "status": "completed",
                "kind": "recorded_fixture",
                "runId": run_id,
                "result": {"scope": "recorded_fixture"},
            },
            db,
        )
        store.put("run", run_id, run, db)
    return {
        "projectId": source["projectId"],
        "runId": run_id,
        "snapshotId": snapshot["snapshotId"],
        "sourceRunId": original_run_id,
        "sourceRecordCount": len(records),
        "sourceJournalDigest": source["journalDigest"],
        "recordCount": 50000,
        "journalDigest": run["journalDigest"],
        "journalBytes": journal.stat().st_size,
        "integrity": checked,
        "evidenceScope": "recorded_fixture",
        "providerAuthority": False,
    }


def protected_files(root):
    return {
        p.relative_to(root).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
        for folder in ("projects", "runs", "snapshots")
        for p in (root / folder).rglob("*")
        if p.is_file()
    }


def main():
    import argparse
    import os
    import subprocess
    import sys
    import uuid

    from xverse_studio.host.ownership import own_root
    from xverse_studio.storage.core import Store

    p = argparse.ArgumentParser()
    for name in (
        "prepared",
        "output",
        "static-dir",
        "node",
        "playwright-cli",
        "browser-cache",
    ):
        p.add_argument("--" + name, type=Path, required=True)
    p.add_argument("--isolate-browser-devices", action="store_true")
    args = p.parse_args()
    args.output = args.output.absolute()
    args.output.mkdir(exist_ok=False)
    context = json.loads((args.prepared / "fixtures.json").read_bytes())
    roots = json.loads((args.prepared / "data-root.private.json").read_bytes())
    prepared, original = Path(roots["dataRoot"]), Path(roots["original"])
    original_before = protected_files(original)
    original_database = hashlib.sha256(
        (original / "studio.sqlite").read_bytes()
    ).hexdigest()
    prepared_before = protected_files(prepared)
    prepared_database = hashlib.sha256(
        (prepared / "studio.sqlite").read_bytes()
    ).hexdigest()
    data = (
        native.ROOT
        / ".studio-local/browser-tests"
        / ("autoverse-performance-" + uuid.uuid4().hex)
    )
    exchange.clone(prepared, data)
    assert protected_files(data) == prepared_before
    baseline = recorded.ledger(data)
    assert baseline["run"] == 2 and baseline["evaluation"] == 6
    (data / "performance-context.private.json").write_text(
        json.dumps(context, indent=2) + "\n"
    )
    host = native.NativeHost(
        data,
        args.output,
        None,
        Path(sys.executable),
        args.static_dir.resolve(),
        register_provider=False,
    )
    outcome = {
        "scope": "Declared inert Autoverse authoring/history benchmarks on native Linux; no runtime admission or execution",
        "outcome": "failed",
        "before": baseline,
    }
    child = None
    owner = None
    browser_birth = None
    samples = []
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
        finally:
            api.close()
        session = data / "browser-session.private.json"
        session.write_text(json.dumps(cookies))
        session.chmod(0o600)
        env = dict(
            os.environ,
            STUDIO_BASE_URL=host.url,
            STUDIO_BROWSER_DATA=str(data),
            STUDIO_BROWSER_REPORT=str(args.output / "browser.json"),
            STUDIO_BROWSER_OUTPUT=str(args.output / "artifacts"),
            PLAYWRIGHT_BROWSERS_PATH=str(args.browser_cache.resolve()),
        )
        argv = [
            str(args.node.resolve()),
            str(args.playwright_cli.resolve()),
            "test",
            "--config",
            "tests/live/autoverse-performance.config.ts",
        ]
        if args.isolate_browser_devices:
            isolation_spec = importlib.util.spec_from_file_location(
                "performance_browser_isolation", Path(__file__).with_name("autoverse_playback_browser.py")
            )
            isolation = importlib.util.module_from_spec(isolation_spec)
            isolation_spec.loader.exec_module(isolation)
            env["STUDIO_BROWSER_CPU_ONLY"] = "1"
            env["STUDIO_BROWSER_DEVICE_PROOF"] = str(args.output / "browser-device-proof.private.json")
            env["STUDIO_BROWSER_HOST_MOUNT_NS"] = os.readlink("/proc/self/ns/mnt")
            argv = isolation.device_free_browser_command(argv)
        (args.output / "browser-command.private.json").write_text(
            json.dumps(argv, indent=2) + "\n"
        )
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
            browser_birth = owner.create_time()
            native.wait(
                lambda: owner.cmdline() == argv and owner.ppid() == os.getpid(),
                bool,
                timeout=3,
            )
            (args.output / "browser-owner.private.json").write_text(
                json.dumps(
                    {"pid": child.pid, "birth": browser_birth, "argv": argv}, indent=2
                )
                + "\n"
            )
            backend = native.psutil.Process(host.child.pid)
            deadline = time.monotonic() + 660
            while child.poll() is None and time.monotonic() < deadline:
                assert backend.create_time() == host.owner["birth"]
                samples.append(backend.memory_info().rss)
                assert len(samples) <= 4000
                time.sleep(0.2)
            if child.poll() is None:
                assert (
                    owner.create_time() == browser_birth
                    and owner.ppid() == os.getpid()
                    and owner.cmdline() == argv
                )
                child.terminate()
            exit_code = child.wait(timeout=30)
        outcome.update(
            browserExit=exit_code,
            originalBrowserDriverAbsent=True,
            backendRssSampleCount=len(samples),
            maximumBackendRssBytes=max(samples),
            backendRssSamplesBytes=samples,
        )
        outcome["after"] = recorded.ledger(data)
        assert outcome["after"] == baseline
        assert protected_files(data) == prepared_before
        assert exit_code == 0, (
            "Declared Autoverse performance/browser case failed; original samples retained"
        )
        store = Store(data)
        fixture_run = store.get("run", context["history"]["runId"])
        rows, integrity = read_journal(
            data / "runs" / fixture_run["runId"], fixture_run
        )
        assert (
            len(rows) == 50000
            and integrity == "valid"
            and fixture_run["capabilities"] == []
        )
        assert not any(
            k in fixture_run
            for k in ("pid", "ownerDigest", "createTime", "launchArgvDigest")
        )
        outcome.update(
            outcome="passed",
            fixtureJournalIntegrity="valid",
            fixtureRecordCount=50000,
            unchangedRunOperationEvaluationSnapshotAndPreflightCounts=True,
            originalAndSyntheticProtectedBytesUnchanged=True,
            providerConfigured=False,
            newLiveExecution=False,
            browserNativeWorkload="200 elements/400 connections and 50000 records/200 displayed rows; two viewports,30repetitions after1warmup",
        )
    finally:
        if child is not None and child.poll() is None:
            assert owner.create_time() == browser_birth and owner.ppid() == os.getpid()
            child.terminate()
            child.wait(timeout=30)
        host.stop()
        with own_root(data):
            pass
        assert protected_files(original) == original_before
        assert (
            hashlib.sha256((original / "studio.sqlite").read_bytes()).hexdigest()
            == original_database
        )
        assert protected_files(prepared) == prepared_before
        assert (
            hashlib.sha256((prepared / "studio.sqlite").read_bytes()).hexdigest()
            == prepared_database
        )
        outcome.update(
            originalSourceRecordingUnchanged=True,
            preparedInputsUnchanged=True,
            originalBackendAbsent=True,
            rootOwnershipReleased=True,
        )
        (args.output / "data-root.private.json").write_text(
            json.dumps({"dataRoot": str(data)}, indent=2) + "\n"
        )
        (args.output / "verification.json").write_text(
            json.dumps(outcome, indent=2) + "\n"
        )
    print(
        json.dumps({k: v for k, v in outcome.items() if k != "backendRssSamplesBytes"})
    )


if __name__ == "__main__":
    main()
