"""Canonical platform mode and real public-service cancellation; no live demo substitute."""
from copy import deepcopy
import hashlib
import hmac
import json
import sys
import threading
import time

from ruamel.yaml import YAML
from xverse.argus import EvidenceStore

from xverse_studio.blueprints.autoverse import documents, NAMESPACE, platform_example
from xverse_studio.providers.autoverse.adapter import configuration
from xverse_studio.providers.autoverse.platform_adapter import PlatformProvider, platform_configuration
from xverse_studio.providers.autoverse.preparation import prepare_snapshot
from xverse_studio.providers.autoverse.maestro_worker import PlatformDemo, run
from xverse_studio.storage.core import atomic, canonical
from xverse_studio.xdl import XDLAdapter
from xverse_studio.xdl.examples import dump_yaml


def installation(tmp_path):
    return {"identityDigest": "sha256:" + "1" * 64,
        "nativeBridge": {"nativeSources": {}, "runtimeRoot": str(tmp_path.resolve() / "maestro"), "hostId": "owned-platform-test"},
        "platformHostGrant": {"scope": "owned-simulation", "maxRuntimeSeconds": 2700,
            "maxCleanupSeconds": 60, "approvalReference": "owned-platform-conformance-only"}}


def test_explicit_platform_source_is_distinct_and_does_not_upgrade_classic():
    source = platform_example()["documents"]
    compiled = XDLAdapter().compile(source)
    assert compiled["valid"], compiled["diagnostics"]
    actual = platform_configuration(source, compiled)
    assert actual["platformIntegration"] == "public-maestro-native-xcom-argus-v1"
    assert actual["nativeSourceClockMapping"] == "unavailable"
    assert compiled["plan"]["timeMappings"] == []
    assert configuration(source, compiled) is None
    classic = documents()
    assert platform_configuration(classic, XDLAdapter().compile(classic)) is None
    assert compiled["semanticDigest"] != XDLAdapter().compile(classic)["semanticDigest"]


def test_classic_authored_bytes_match_the_pre_platform_checkpoint():
    expected = {"native-pygame": "cd597a163f91a232793e619b3140b0dfd781a3071b5490671c5c588bf30f5910",
                "studio-browser": "52ab76b1863657876de945c22925efeb8275a46dd81b2487efb63116b002808d"}
    for surface, identity in expected.items():
        raw = json.dumps(documents(surface), sort_keys=True, separators=(",", ":")).encode()
        assert hashlib.sha256(raw).hexdigest() == identity


def test_platform_pure_preparation_covers_all_bindings_and_native_acquisition(tmp_path):
    source = platform_example()["documents"]
    compiled = XDLAdapter().compile(source)
    native = installation(tmp_path)
    result = prepare_snapshot("owned-platform-preparation", {"documents": source, "plan": compiled["plan"],
        "planDigest": compiled["planDigest"], "semanticDigest": compiled["semanticDigest"]},
        installation=native, host_id="owned-test", runtime_adapter=PlatformProvider(native))
    assert result.prepared.summary()["executionAllowed"] is False
    assert {u["providerId"] for u in result.prepared.inspection.to_data()["units"]} == {"autoverse.platform"}
    assert len(result.lifecycle.phases) == 22
    positions = {p.phase_id: i for i, p in enumerate(result.lifecycle.phases)}
    assert positions["carla-router-prepare"] < positions["vcu-native-prepare"] < positions["vcu-start"]
    assert result.prepared.providers[0].configuration.documents == tuple((n, s.encode()) for n, s in source.items())


def test_platform_configuration_rejects_compilable_unimplemented_semantics():
    source = platform_example()["documents"]
    scenario = YAML(typ="safe").load(source["scenario.xdl.yaml"])
    scenario["spec"]["initialConditions"]["unimplementedBehavior"] = True
    source["scenario.xdl.yaml"] = dump_yaml(scenario)
    compiled = XDLAdapter().compile(source)
    assert compiled["valid"]
    assert platform_configuration(source, compiled) is None


def test_platform_duration_edit_preserves_original_documents_and_effective_value():
    source = platform_example()["documents"]
    scenario = YAML(typ="safe").load(source["scenario.xdl.yaml"])
    scenario["extensions"][NAMESPACE]["durationSeconds"] = 30
    source["scenario.xdl.yaml"] = dump_yaml(scenario)
    before = deepcopy(source)
    assert platform_configuration(source, XDLAdapter().compile(source))["durationSeconds"] == 30
    assert source == before


def test_public_service_start_cancellation_releases_actual_owned_children(tmp_path, monkeypatch):
    import xverse_studio.providers.autoverse.execution as callbacks
    import xverse_studio.providers.autoverse.maestro_worker as worker

    source = platform_example()["documents"]
    compiled = XDLAdapter().compile(source)
    enrolled = installation(tmp_path)
    snapshot = {"snapshotId": "snap-platform-cancel", "documents": source, "plan": compiled["plan"],
        "planDigest": compiled["planDigest"], "semanticDigest": compiled["semanticDigest"],
        "providerIdentity": PlatformProvider(enrolled).descriptor()}
    root = tmp_path / "worker"
    root.mkdir()
    atomic(root / "owner.key", b"x" * 32)
    atomic(root / "request.json", canonical({"runId": "run-platform-cancel", "operationId": "op-owned-start",
        "snapshot": snapshot, "nativeInstallation": enrolled, "configuration": platform_configuration(source, compiled)}).encode())
    demo = PlatformDemo(root)
    demo.environment = lambda: {}
    # Explicit external-action substitutions. No simulator/container/native
    # traffic is claimed. The actual Core, original child and Argus are used.
    monkeypatch.setattr(callbacks, "verify", lambda _installation: True)
    monkeypatch.setattr(worker, "current_identity", lambda inst, **_kwargs: inst["identityDigest"])
    demo.claim_installation = lambda _compiled: None
    demo.start_router = lambda: demo.launch("router", [sys.executable, "-I", "-c", "import time; time.sleep(120)"])
    entered = threading.Event()
    def wait_for_cancellation():
        entered.set()
        while True:
            demo.tick()
    demo.prepare_simulator = wait_for_cancellation
    def cancel():
        assert entered.wait(5)
        command = {"kind": "cancel", "operationId": "op-owned-cancel"}
        signature = hmac.new(demo.secret, canonical(command).encode(), hashlib.sha256).hexdigest()
        atomic(root / "command.json", canonical({**command, "signature": signature}).encode())
    cancellation = threading.Thread(target=cancel)
    cancellation.start()
    started = time.monotonic()
    try:
        result = run(demo)
        assert time.monotonic() - started < 10
        assert result["state"] == "failed" and result["failureCode"] == "MPX-START-CANCELLED"
        assert result["cleanup"] == "released"
        assert demo.processes["router"]["process"].poll() is not None
        records = EvidenceStore.read_run(tmp_path / "maestro/run-platform-cancel.argus").records()
        assert any(r.get("extensions", {}).get("io.xverse.maestro.execution", {}).get("kind") == "cleanup-outcome" for r in records)
        assert json.loads((root / "maestro.private.json").read_bytes())["runId"] == "run-platform-cancel"
    finally:
        cancellation.join(timeout=2)
        demo.cleanup()
        demo.journal.close()
