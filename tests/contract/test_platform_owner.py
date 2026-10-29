"""Real public Core across owned-child runs; external demo actions are substituted.

These checks do not establish CARLA/native-message/browser live acceptance.
"""

from copy import deepcopy
import hashlib
import hmac
import json
from pathlib import Path
import sys
import threading
import time

import psutil
import pytest
from fastapi.testclient import TestClient
from ruamel.yaml import YAML
from xverse.argus import EvidenceStore
from xverse.maestro.execution import ExecutionInputError

from xverse_studio.api.app import create_app
from xverse_studio.blueprints.autoverse import NAMESPACE, platform_example
from xverse_studio.providers.autoverse.installation import InstallationError
from xverse_studio.providers.autoverse.maestro_worker import PlatformDemo
from xverse_studio.providers.autoverse.platform_adapter import (
    PlatformProvider,
    platform_configuration,
)
from xverse_studio.providers.autoverse.platform_owner import PlatformOwner
from xverse_studio.storage.core import atomic, canonical
from xverse_studio.xdl import XDLAdapter
from xverse_studio.xdl.examples import dump_yaml


def installation(tmp_path):
    return {
        "identityDigest": "sha256:" + "1" * 64,
        "nativeBridge": {
            "nativeSources": {},
            "runtimeRoot": str(tmp_path.resolve() / "maestro"),
            "hostId": "owned-persistent-test",
        },
        "platformHostGrant": {
            "scope": "owned-simulation",
            "maxRuntimeSeconds": 2700,
            "maxCleanupSeconds": 60,
            "approvalReference": "owned-child-conformance-only",
        },
    }


def request(tmp_path, native, run_id, duration=30):
    documents = platform_example()["documents"]
    scenario = YAML(typ="safe").load(documents["scenario.xdl.yaml"])
    scenario["extensions"][NAMESPACE]["durationSeconds"] = duration
    documents["scenario.xdl.yaml"] = dump_yaml(scenario)
    compiled = XDLAdapter().compile(documents)
    assert compiled["valid"], compiled["diagnostics"]
    snapshot = {
        "snapshotId": "snap-" + run_id,
        "documents": documents,
        "plan": compiled["plan"],
        "planDigest": compiled["planDigest"],
        "semanticDigest": compiled["semanticDigest"],
        "providerIdentity": PlatformProvider(native).descriptor(),
    }
    root = tmp_path / run_id
    root.mkdir()
    atomic(root / "owner.key", b"x" * 32)
    atomic(
        root / "request.json",
        canonical(
            {
                "runId": run_id,
                "operationId": "op-" + run_id,
                "snapshot": snapshot,
                "configuration": platform_configuration(documents, compiled),
                "nativeInstallation": native,
            }
        ).encode(),
    )
    return root


@pytest.fixture
def owned_actions(monkeypatch):
    import xverse_studio.providers.autoverse.execution as callbacks
    import xverse_studio.providers.autoverse.maestro_worker as worker

    entered = {}
    demos = {}
    monkeypatch.setattr(callbacks, "verify", lambda _installation: True)
    monkeypatch.setattr(
        worker, "current_identity", lambda inst, **kwargs: inst["identityDigest"]
    )
    monkeypatch.setattr(PlatformProvider, "verify_installation", lambda self: None)
    monkeypatch.setattr(PlatformDemo, "environment", lambda self: {})
    monkeypatch.setattr(
        PlatformDemo, "claim_installation", lambda self, _compiled: None
    )

    def start_router(demo):
        demos[demo.request["runId"]] = demo
        demo.launch(
            "router", [sys.executable, "-I", "-c", "import time; time.sleep(120)"]
        )

    def prepare(demo):
        entered.setdefault(demo.request["runId"], threading.Event()).set()
        while True:
            demo.tick()

    monkeypatch.setattr(PlatformDemo, "start_router", start_router)
    monkeypatch.setattr(PlatformDemo, "prepare_simulator", prepare)
    yield entered, demos
    # Only original fixture handles, never PID/name lookup, for test failure cleanup.
    for demo in demos.values():
        if demo.state["state"] not in ("stopped", "failed"):
            cancel(demo.root)
            until(lambda: demo.state["state"] in ("stopped", "failed"))
        for resource in demo.processes.values():
            process = resource["process"]
            if process.poll() is None:
                process.terminate()
                process.wait(timeout=5)
        # Test-only emergency disposal after checking and retaining uncertainty:
        # original child handles are now absent; no unknown claim is removed or
        # relabelled and no new activation is attempted in that registration.
        demo.service.close()


def until(predicate, timeout=10):
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if predicate():
            return
        time.sleep(0.03)
    raise AssertionError("Owned fixture did not reach its expected state")


def cancel(root):
    body = {"kind": "cancel", "operationId": "op-owned-cancel"}
    body["signature"] = hmac.new(
        (root / "owner.key").read_bytes(), canonical(body).encode(), hashlib.sha256
    ).hexdigest()
    atomic(root / "command.json", canonical(body).encode())


def test_original_service_survives_two_distinct_input_runs_and_retires_only_released_contexts(
    tmp_path, owned_actions
):
    entered, demos = owned_actions
    native = installation(tmp_path)
    adapter = PlatformProvider(native)
    owner = PlatformOwner(native, adapter)
    results = []
    original_service = None
    for rid, duration in [("owned-first", 30), ("owned-second", 45)]:
        root = request(tmp_path, native, rid, duration)
        task = owner.prepare_task(root)
        assert task.pid == psutil.Process().pid and task.poll() is None
        task.start()
        until(lambda: rid in entered and entered[rid].is_set())
        if original_service is None:
            original_service = owner.service
        assert owner.service is original_service
        child = demos[rid].processes["router"]["process"]
        assert psutil.Process(child.pid).cwd() == str(root)
        with pytest.raises(InstallationError):
            owner.prepare_task(root)
        cancel(root)
        assert task.wait(10) == 0
        state = json.loads((root / "state.json").read_text())
        assert state["state"] == "stopped" and state["cleanup"] == "complete"
        assert state["ownerTaskId"] == task.task_id
        snapshot = owner.service.read(rid)
        assert (
            snapshot["cleanup"] == "released"
            and snapshot["failureCode"] == "MPX-START-CANCELLED"
        )
        assert demos[rid].processes["router"]["process"].poll() is not None
        assert not owner.router.contexts
        reader = EvidenceStore.read_run(
            Path(native["nativeBridge"]["runtimeRoot"]) / (rid + ".argus")
        )
        assert any(
            r.get("extensions", {}).get("io.xverse.maestro.execution", {}).get("kind")
            == "run-terminal"
            for r in reader.records()
        )
        results.append(deepcopy(snapshot))
    assert results[0]["operationId"] != results[1]["operationId"]
    assert results[0]["correlationId"] != results[1]["correlationId"]
    assert results[0]["inputSemanticDigest"] != results[1]["inputSemanticDigest"]
    assert owner.service.read("owned-first") == results[0]
    assert owner.close() is True
    # A new owner cannot acquire the old registration, even in the same backend PID.
    successor = PlatformOwner(native, adapter)
    with pytest.raises(InstallationError, match="RECOVERY_REQUIRED"):
        successor.prepare_task(tmp_path / "unused")
    assert successor.service is None


def test_uncertain_cleanup_retains_original_context_and_blocks_owner_close(
    tmp_path, owned_actions, monkeypatch
):
    entered, demos = owned_actions
    native = installation(tmp_path)
    owner = PlatformOwner(native, PlatformProvider(native))
    root = request(tmp_path, native, "owned-unknown")
    monkeypatch.setattr(
        PlatformDemo, "cleanup_phase", lambda self, phase, deadline: "unknown"
    )
    task = owner.prepare_task(root)
    task.start()
    until(lambda: "owned-unknown" in entered)
    cancel(root)
    task.wait(10)
    assert (
        owner.fenced
        and owner.router.contexts["owned-unknown"].demo is demos["owned-unknown"]
    )
    assert owner.close() is False
    with pytest.raises(InstallationError):
        owner.prepare_task(tmp_path / "not-started")
    assert owner.service.read("owned-unknown")["cleanup"] == "unknown"


def test_routing_never_invents_original_run_context(tmp_path):
    native = installation(tmp_path)
    owner = PlatformOwner(native, PlatformProvider(native))
    with pytest.raises(ExecutionInputError, match="ORIGINAL_CONTEXT_UNAVAILABLE"):
        owner.router.context("missing")
    assert owner.close() is True


def test_http_backend_task_liveness_requires_original_handle_and_stop_reuses_service(
    tmp_path, owned_actions
):
    entered, _ = owned_actions
    native = installation(tmp_path)
    provider = PlatformProvider(native)
    app = create_app(
        tmp_path / "data",
        allowed_hosts=["testserver"],
        bootstrap_token="owned-conformance",
        installed_providers={"autoverse.platform": provider},
    )
    with TestClient(app, base_url="http://testserver") as client:
        client.headers["Origin"] = "http://testserver"
        session = client.post(
            "/api/v1/session", json={"bootstrapToken": "owned-conformance"}
        ).json()
        client.headers["X-CSRF-Token"] = session["csrfToken"]
        project = client.post(
            "/api/v1/projects",
            json={
                "name": "Owned persistent Core",
                "blueprintRef": "autoverse-platform",
            },
        ).json()
        core = None
        for index in range(2):
            pf = client.post(
                "/api/v1/projects/" + project["projectId"] + "/preflights",
                json={
                    "revision": project["revision"],
                    "providerId": "autoverse.platform",
                },
            ).json()
            assert pf["status"] == "ready", pf
            response = client.post(
                "/api/v1/runs",
                json={"snapshotId": pf["snapshotId"], "preflightId": pf["preflightId"]},
                headers={"Idempotency-Key": "owned-start-" + str(index)},
            )
            assert response.status_code == 202, response.text
            rid = response.json()["runId"]
            until(lambda: rid in entered)
            observed = client.get("/api/v1/runs/" + rid).json()
            assert observed["state"] == "preparing", observed
            assert observed["executionKind"] == "backend-task"
            tasks = app.state.studio.runs.children
            original = tasks.pop(rid)
            assert client.get("/api/v1/runs/" + rid).json()["state"] == "unknown"
            # Restore the actual object for this test, not a handle inferred from PID.
            tasks[rid] = original
            observed = client.get("/api/v1/runs/" + rid).json()
            assert observed["state"] == "preparing"
            response = client.post(
                "/api/v1/runs/" + rid + "/commands",
                json={
                    "kind": "cancel",
                    "expectedStateVersion": observed["stateVersion"],
                },
                headers={"Idempotency-Key": "owned-stop-" + str(index)},
            )
            assert response.status_code == 202, response.text
            until(
                lambda: client.get("/api/v1/runs/" + rid).json()["state"] == "stopped"
            )
            assert original.wait(10) == 0
            if core is None:
                core = provider._owner.service
            assert provider._owner.service is core
            assert client.get("/api/v1/runs/" + rid).json()["cleanup"] == "complete"
    assert provider._owner.closed is True


def test_two_normal_stop_runs_keep_same_core_with_owned_children_only(
    tmp_path, owned_actions, monkeypatch
):
    from xverse.maestro.execution import PhaseReceipt
    from xverse_studio.providers.autoverse.maestro_worker import PlatformExecution

    _, demos = owned_actions

    # Replace external phases/native sampling explicitly. The real public Core,
    # phase graph, original owned child, signed Stop and actual Argus are used.
    def dispatch(provider, phase, effective, context):
        demo = provider.demo
        provider._attempted.add(phase.phase_id)
        demo.active_phase = phase.phase_id
        try:
            if phase.phase_id == "carla-router-prepare":
                demo.start_router()
                demo.processes["manual"] = demo.processes["router"]
            return PhaseReceipt(
                {"prepare": "prepared", "start": "started", "ready": "ready"}[
                    phase.operation
                ],
                ("owned-router",) if phase.phase_id == "carla-router-prepare" else (),
                "liveness" if phase.operation == "ready" else None,
                b"{}",
            )
        finally:
            demo.active_phase = None

    monkeypatch.setattr(PlatformExecution, "dispatch", dispatch)
    monkeypatch.setattr(
        PlatformExecution,
        "observe_runtime",
        lambda provider, effective, context: provider._process("router"),
    )
    monkeypatch.setattr(PlatformExecution, "read_observation_batch", lambda *_: None)
    monkeypatch.setattr(
        PlatformDemo,
        "quiesce_native",
        lambda demo: setattr(demo, "native_quiesced", True),
    )
    native = installation(tmp_path)
    owner = PlatformOwner(native, PlatformProvider(native))
    core = None
    for rid in ["normal-first", "normal-second"]:
        root = request(tmp_path, native, rid)
        task = owner.prepare_task(root)
        task.start()
        until(lambda: rid in demos and demos[rid].state["state"] == "running")
        if core is None:
            core = owner.service
        assert owner.service is core
        cancel(root)
        assert task.wait(10) == 0
        actual = core.read(rid)
        assert actual["state"] == "stopped" and actual["cleanup"] == "released"
        assert actual["failureCode"] is None
        assert demos[rid].processes["router"]["process"].poll() is not None
    assert owner.close() is True


def test_previous_owner_marker_blocks_before_installation_probe(tmp_path, monkeypatch):
    import xverse_studio.providers.autoverse.platform_adapter as adapter

    native = installation(tmp_path)
    root = Path(native["nativeBridge"]["runtimeRoot"])
    root.mkdir()
    atomic(
        root / ".studio-owner.json",
        canonical({"version": "1.0", "ownerId": "a-prior-owner"}).encode(),
    )
    monkeypatch.setattr(
        adapter,
        "verify_platform",
        lambda *_: pytest.fail("Lost owner reached installation probe"),
    )
    with pytest.raises(InstallationError, match="RECOVERY_REQUIRED"):
        PlatformProvider(native).verify_installation()


def test_dead_backend_task_is_unknown_even_when_backend_process_is_alive(
    tmp_path, owned_actions, monkeypatch
):
    from xverse_studio.providers.backend_task import BackendTask
    from xverse_studio.storage.core import digest

    native = installation(tmp_path)
    provider = PlatformProvider(native)
    tasks = []

    def prepare(root):
        def target(task_id):
            process = psutil.Process()
            atomic(
                root / "state.json",
                canonical(
                    {
                        "state": "running",
                        "stateVersion": 2,
                        "cleanup": "not_started",
                        "evidence": "collecting",
                        "pid": process.pid,
                        "createTime": process.create_time(),
                        "ownerDigest": digest((root / "owner.key").read_bytes()),
                        "ownerTaskId": task_id,
                    }
                ).encode(),
            )
            # Simulated task failure without a terminal Studio state. No runtime,
            # child process or platform acquisition is substituted as successful.
            return 1

        task = BackendTask(target)
        tasks.append(task)
        return task

    monkeypatch.setattr(provider, "prepare_backend_task", prepare)
    app = create_app(
        tmp_path / "data",
        allowed_hosts=["testserver"],
        bootstrap_token="owned-task-failure",
        installed_providers={"autoverse.platform": provider},
    )
    with TestClient(app, base_url="http://testserver") as client:
        client.headers["Origin"] = "http://testserver"
        session = client.post(
            "/api/v1/session", json={"bootstrapToken": "owned-task-failure"}
        ).json()
        client.headers["X-CSRF-Token"] = session["csrfToken"]
        project = client.post(
            "/api/v1/projects",
            json={"name": "Dead task", "blueprintRef": "autoverse-platform"},
        ).json()
        pf = client.post(
            "/api/v1/projects/" + project["projectId"] + "/preflights",
            json={"revision": project["revision"], "providerId": "autoverse.platform"},
        ).json()
        response = client.post(
            "/api/v1/runs",
            json={"snapshotId": pf["snapshotId"], "preflightId": pf["preflightId"]},
            headers={"Idempotency-Key": "dead-task"},
        )
        assert response.status_code == 202, response.text
        assert tasks[0].wait(5) == 1
        assert psutil.Process(tasks[0].pid).is_running()
        observed = client.get("/api/v1/runs/" + response.json()["runId"]).json()
        assert observed["state"] == "unknown" and observed["cleanup"] == "unknown"


def test_backend_shutdown_cancels_original_active_task_before_closing_core(
    tmp_path, owned_actions
):
    entered, demos = owned_actions
    native = installation(tmp_path)
    provider = PlatformProvider(native)
    app = create_app(
        tmp_path / "data",
        allowed_hosts=["testserver"],
        bootstrap_token="owned-shutdown",
        installed_providers={"autoverse.platform": provider},
    )
    with TestClient(app, base_url="http://testserver") as client:
        client.headers["Origin"] = "http://testserver"
        session = client.post(
            "/api/v1/session", json={"bootstrapToken": "owned-shutdown"}
        ).json()
        client.headers["X-CSRF-Token"] = session["csrfToken"]
        project = client.post(
            "/api/v1/projects",
            json={"name": "Shutdown task", "blueprintRef": "autoverse-platform"},
        ).json()
        pf = client.post(
            "/api/v1/projects/" + project["projectId"] + "/preflights",
            json={"revision": project["revision"], "providerId": "autoverse.platform"},
        ).json()
        response = client.post(
            "/api/v1/runs",
            json={"snapshotId": pf["snapshotId"], "preflightId": pf["preflightId"]},
            headers={"Idempotency-Key": "shutdown-task"},
        )
        rid = response.json()["runId"]
        until(lambda: rid in entered)
        assert provider._owner.close() is False
    assert demos[rid].processes["router"]["process"].poll() is not None
    assert provider._owner.closed is True
    terminal = json.loads(
        (app.state.studio.runs.directory(rid) / "state.json").read_text()
    )
    assert terminal["state"] == "stopped" and terminal["cleanup"] == "complete"


def test_false_release_receipt_does_not_discard_a_live_original_child(
    tmp_path, owned_actions, monkeypatch
):
    entered, demos = owned_actions
    native = installation(tmp_path)
    owner = PlatformOwner(native, PlatformProvider(native))
    root = request(tmp_path, native, "contradictory-release")
    # Adversarial provider defect: public Core records the supplied receipt;
    # the Studio owner must preserve the contradictory actual owned child.
    monkeypatch.setattr(
        PlatformDemo, "cleanup_phase", lambda self, phase, deadline: "released"
    )
    task = owner.prepare_task(root)
    task.start()
    until(lambda: "contradictory-release" in entered)
    cancel(root)
    assert task.wait(10) == 1
    assert owner.service.read("contradictory-release")["cleanup"] == "released"
    assert (
        owner.fenced
        and owner.router.contexts["contradictory-release"].demo
        is demos["contradictory-release"]
    )
    state = json.loads((root / "state.json").read_text())
    assert state["state"] == "failed" and state["cleanup"] == "unknown"
    assert state["reason"] == "AUTOVERSE_PLATFORM_RELEASE_CONTRADICTION"
    assert owner.close() is False
