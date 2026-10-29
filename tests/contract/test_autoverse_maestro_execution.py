"""Adapter rollback with actual owned children and public Maestro/Argus.

External CARLA/container actions are explicitly substituted here. This verifies
adapter ownership/failure semantics, not live Autoverse acceptance or native X-COM.
"""
import json
import sys
import time

import pytest
from xverse.argus import EvidenceStore
from xverse.maestro.execution import ExecutionInputError, HostExecutionPermit, PublicExecutionService

from xverse_studio.blueprints.autoverse import documents
from xverse_studio.providers.autoverse.adapter import AutoverseProvider, configuration
from xverse_studio.providers.autoverse.execution import AutoverseExecution
from xverse_studio.providers.autoverse.installation import InstallationError
from xverse_studio.providers.autoverse.preparation import prepare_snapshot
from xverse_studio.providers.autoverse.worker import Demo
from xverse_studio.storage.core import atomic, canonical
from xverse_studio.xdl import XDLAdapter


def test_public_maestro_partial_phase_failure_rolls_back_actual_child_handles(tmp_path, monkeypatch):
    import xverse_studio.providers.autoverse.execution as module

    source = documents()
    compiled = XDLAdapter().compile(source)
    assert compiled["valid"]
    installation = {"identityDigest": "sha256:" + "1" * 64}
    snapshot = {"snapshotId": "snap-owned-contract", "documents": source, "plan": compiled["plan"],
                "planDigest": compiled["planDigest"], "semanticDigest": compiled["semanticDigest"],
                "providerIdentity": AutoverseProvider(installation).descriptor()}
    root = tmp_path.resolve() / "worker"
    root.mkdir()
    atomic(root / "owner.key", b"x" * 32)
    atomic(root / "request.json", canonical({"runId": "run-owned-contract", "snapshot": snapshot,
        "configuration": configuration(source, compiled), "nativeInstallation": installation}).encode())
    demo = Demo(root)
    demo.environment = lambda: {}
    argv = [sys.executable, "-I", "-c", "import time; time.sleep(120)"]
    def forbidden_whole_run():
        raise AssertionError("The complete worker cannot be a single Maestro phase")
    demo.run = forbidden_whole_run
    # Explicit owned test substitutions; no Docker/CARLA contact or fabricated
    # external readiness. Execution fails before reaching the VCU ready phase.
    monkeypatch.setattr(module, "verify", lambda _installation: True)
    demo.claim_installation = lambda _compiled: None
    demo.start_router = lambda: demo.launch("router", argv)
    demo.prepare_simulator = lambda: demo.launch("carla", argv)
    def partial_start():
        demo.launch("vcu", argv)
        raise InstallationError("AUTOVERSE_OWNED_TEST_AFTER_ACQUISITION")
    demo.start_vcu = partial_start
    preparation = prepare_snapshot("run-owned-contract", snapshot, installation=installation, host_id="owned-contract-host")
    provider = AutoverseExecution(demo, preparation)
    effective = preparation.prepared.providers[0].configuration
    # Canonical persistence changes key order, while preserving named bytes.
    assert tuple(demo.snapshot["documents"]) != tuple(source)
    provider.validate_runtime(effective, preparation.prepared)
    changed_name = next(iter(demo.snapshot["documents"]))
    original_body = demo.snapshot["documents"][changed_name]
    demo.snapshot["documents"][changed_name] += "\n# Different source bytes\n"
    with pytest.raises(ExecutionInputError, match="AUTOVERSE-RUNTIME-INPUT-MISMATCH"):
        provider.validate_runtime(effective, preparation.prepared)
    assert demo.processes == {}
    demo.snapshot["documents"][changed_name] = original_body
    service = PublicExecutionService(tmp_path.resolve() / "maestro", preparation.host, (provider,),
                                     max_runtime_seconds=30, cleanup_budget_seconds=10)
    prepared = preparation.prepared
    now = time.time()
    permit = HostExecutionPermit("owned-contract-permit", preparation.host.identity(), prepared.digest,
        preparation.lifecycle.digest, preparation.host.host_id, "owned-contract-fixture-only", now - 1, now + 30,
        runtime_binding_digest=service.runtime_binding_digest)
    try:
        result = service.start(prepared, preparation.lifecycle, permit, idempotency_key="start-owned-contract")
        assert result["state"] == "failed" and result["cleanup"] == "released"
        assert set(demo.processes) == {"router", "carla", "vcu"}
        assert all(record["process"].poll() is not None for record in demo.processes.values())
        assert demo.phase_resources["vcu-start"]["processes"] == ["vcu"]
        original = EvidenceStore.read_run(service.root / "run-owned-contract.argus")
        events = [r["extensions"]["io.xverse.maestro.execution"] for r in original.records()
                  if "io.xverse.maestro.execution" in r.get("extensions", {})]
        cleanup = [r["phaseId"] for r in events if r["kind"] == "cleanup-intent"]
        assert cleanup == ["vcu-start", "vcu-prepare", "carla-server-prepare", "carla-router-prepare"]
        assert not any(r["kind"] == "phase-outcome" and r["phaseId"] == "vcu-start" for r in events)
        assert not any(r["readinessKind"] == "functional" for r in events)
        assert all(r["runId"] == "run-owned-contract" and r["planDigest"] == compiled["planDigest"] for r in events)
        assert original.assessed_evidence_status == "incomplete"
        journal = [json.loads(line) for line in (root / "evidence.jsonl").read_bytes().splitlines()]
        assert journal and all(r["source"]["providerId"] == "autoverse.demo" for r in journal)
        assert not {r["eventId"] for r in journal} & {r["eventId"] for r in original.records()}
    finally:
        service.close()
        demo.cleanup()
        demo.journal.close()
