"""Actual owned-child failure cleanup; no CARLA/container acceptance substitution."""

import selectors
import subprocess
import sys
import time
import psutil
import pytest
from xverse_studio.providers.autoverse.worker import Demo, finish
from xverse_studio.storage.core import digest


def workload(tmp_path):
    process = subprocess.Popen(
        [sys.executable, "-I", "-c", "import time; time.sleep(120)"],
        stdin=subprocess.DEVNULL,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    owner = psutil.Process(process.pid)
    demo = Demo.__new__(Demo)
    demo.root = tmp_path
    demo.request = {"runId": "run-test", "snapshot": {}}
    demo.snapshot = {"snapshotId": "snap-test"}
    demo.processes = {
        "owned": {
            "process": process,
            "pid": process.pid,
            "createTime": owner.create_time(),
            "argvDigest": digest(owner.cmdline()),
        }
    }
    demo.containers = {}
    demo.lock = None
    demo.selector = selectors.DefaultSelector()
    demo.state = {
        "state": "running",
        "stateVersion": 2,
        "cleanup": "not_started",
        "commandResults": {},
        "runtimeStatus": {},
    }
    demo.stop_command = {"operationId": "op-stop"}
    demo.input_loss = None
    demo.count = demo.journal_bytes = 0
    demo.previous = "0" * 64
    demo.journal = (tmp_path / "evidence.jsonl").open("xb", buffering=0)
    return demo, process


def test_failed_state_storage_cannot_prevent_real_owned_child_cleanup(tmp_path):
    demo, process = workload(tmp_path)

    def unavailable():
        raise OSError("simulated storage failure")

    demo.save = unavailable
    try:
        assert finish(demo, False) == 1
        assert process.poll() is not None
        assert demo.state["cleanup"] == "complete"
        assert demo.state["evidence"] == "partial"
        assert demo.state["evidenceFailure"] == "AUTOVERSE_EVIDENCE_IO_FAILED"
        assert demo.journal.closed
    finally:
        if process.poll() is None:
            process.terminate()
            process.wait(timeout=5)


def test_birth_identity_mismatch_never_signals_an_unconfirmed_process(tmp_path):
    demo, process = workload(tmp_path)
    demo.processes["owned"]["createTime"] += 100
    try:
        demo.cleanup()
        assert process.poll() is None
        assert demo.state["cleanup"] == "unknown"
        assert demo.state["cleanupResources"] == [
            {"resourceId": "owned", "kind": "process", "status": "unknown"}
        ]
    finally:
        process.terminate()
        process.wait(timeout=5)
        demo.journal.close()


def test_phase_deadline_interrupts_owned_command_without_losing_cleanup_handle(
    tmp_path,
):
    from xverse_studio.providers.autoverse.installation import InstallationError
    from xverse_studio.storage.core import atomic, canonical

    atomic(tmp_path / "owner.key", b"x" * 32)
    atomic(
        tmp_path / "request.json",
        canonical(
            {
                "runId": "run-deadline",
                "nativeInstallation": {},
                "snapshot": {"snapshotId": "snap-deadline"},
                "configuration": {"inputSurface": "native-pygame"},
            }
        ).encode(),
    )
    demo = Demo(tmp_path)
    demo.environment = lambda: {}  # Trusted owned test interpreter, no simulator.
    started = time.monotonic()
    demo.phase_deadline = started + 0.15
    try:
        with pytest.raises(InstallationError, match="AUTOVERSE_PHASE_DEADLINE"):
            demo.execute(
                "owned", [sys.executable, "-I", "-c", "import time; time.sleep(120)"]
            )
        process = demo.processes["owned"]["process"]
        assert process.poll() is None and time.monotonic() - started < 2
        # An expired phase cannot acquire another child while awaiting rollback.
        with pytest.raises(InstallationError, match="AUTOVERSE_PHASE_DEADLINE"):
            demo.launch("late", [sys.executable, "-I", "-c", "pass"])
        assert "late" not in demo.processes
    finally:
        demo.phase_deadline = None
        demo.cleanup()
        demo.journal.close()
    assert process.poll() is not None and demo.state["cleanup"] == "complete"


def phase_demo(tmp_path):
    from xverse_studio.storage.core import atomic, canonical

    atomic(tmp_path / "owner.key", b"x" * 32)
    atomic(
        tmp_path / "request.json",
        canonical(
            {
                "runId": "run-phases",
                "nativeInstallation": {},
                "snapshot": {"snapshotId": "snap-phases"},
                "configuration": {"inputSurface": "native-pygame"},
            }
        ).encode(),
    )
    demo = Demo(tmp_path)
    demo.environment = lambda: {}
    return demo


def test_original_child_exiting_before_cmdline_observation_is_retained(tmp_path, monkeypatch):
    import os
    import xverse_studio.providers.autoverse.worker as module

    demo = phase_demo(tmp_path)
    original_process = psutil.Process

    class ExitedChild:
        def __init__(self, pid):
            self.owner = original_process(pid)
            self.pid = pid

        def create_time(self):
            return self.owner.create_time()

        def cmdline(self):
            # Observe a real exited, unreaped child rather than synthesizing an
            # exception. The original Popen still owns its exit status.
            os.waitid(os.P_PID, self.pid, os.WEXITED | os.WNOWAIT)
            return self.owner.cmdline()

    argv = [sys.executable, "-I", "-c", "pass"]
    try:
        with monkeypatch.context() as patch:
            patch.setattr(module.psutil, "Process", ExitedChild)
            process = demo.launch("fast-command", argv)
        assert process.poll() == 0
        record = demo.processes["fast-command"]
        assert record["createTime"] is not None
        assert record["argvDigest"] == digest(argv)
        demo.cleanup()
        assert demo.state["cleanup"] == "complete"
    finally:
        demo.cleanup()
        demo.journal.close()


def test_zombie_observation_does_not_admit_a_still_running_child(tmp_path, monkeypatch):
    import xverse_studio.providers.autoverse.worker as module

    demo = phase_demo(tmp_path)
    original_process = psutil.Process

    class InconsistentObservation:
        def __init__(self, pid):
            self.owner = original_process(pid)
            self.pid = pid

        def create_time(self):
            return self.owner.create_time()

        def cmdline(self):
            raise psutil.ZombieProcess(self.pid)

    try:
        with monkeypatch.context() as patch:
            patch.setattr(module.psutil, "Process", InconsistentObservation)
            with pytest.raises(psutil.ZombieProcess):
                demo.launch("live-command", [sys.executable, "-I", "-c", "import time; time.sleep(120)"])
        assert demo.processes["live-command"]["process"].poll() is None
    finally:
        # Use the retained original child directly: its command line was never
        # admitted, so generic cleanup must not guess or signal an identity.
        process = demo.processes["live-command"]["process"]
        process.terminate()
        process.wait(timeout=3)
        demo.cleanup()
        demo.journal.close()


def test_phase_rollback_releases_only_its_actual_owned_children(tmp_path):
    demo = phase_demo(tmp_path)
    argv = [sys.executable, "-I", "-c", "import time; time.sleep(120)"]
    try:
        demo.active_phase = "first-start"
        first = demo.launch("first", argv)
        demo.active_phase = "second-start"
        second = demo.launch("second", argv)
        demo.active_phase = None
        assert demo.cleanup_phase("second-start", time.monotonic() + 3) == "released"
        assert second.poll() is not None and first.poll() is None
        assert demo.state["cleanupResources"] == [
            {
                "resourceId": "second",
                "kind": "process",
                "status": "released",
                "phaseId": "second-start",
            }
        ]
        assert demo.cleanup_phase("first-start", time.monotonic() - 1) == "unknown"
        assert first.poll() is None
        assert demo.cleanup_phase("first-start", time.monotonic() + 3) == "released"
        assert first.poll() is not None
    finally:
        demo.cleanup()
        demo.journal.close()


def test_failure_observing_new_child_retains_original_handle_for_unknown_cleanup(
    tmp_path, monkeypatch
):
    import xverse_studio.providers.autoverse.worker as module

    demo = phase_demo(tmp_path)
    demo.active_phase = "partial-start"

    def unavailable(_pid):
        raise psutil.AccessDenied()

    try:
        with monkeypatch.context() as patch:
            patch.setattr(module.psutil, "Process", unavailable)
            with pytest.raises(psutil.AccessDenied):
                demo.launch(
                    "partial",
                    [sys.executable, "-I", "-c", "import time; time.sleep(120)"],
                )
        process = demo.processes["partial"]["process"]
        assert process.poll() is None
        assert demo.phase_resources["partial-start"]["processes"] == ["partial"]
        assert demo.cleanup_phase("partial-start", time.monotonic() + 3) == "unknown"
        assert process.poll() is None
    finally:
        # Fixture teardown owns the original Popen; this does not manufacture a
        # birth witness or turn an unknown runtime cleanup into success.
        process = demo.processes["partial"]["process"]
        process.terminate()
        process.wait(timeout=5)
        demo.cleanup()
        demo.journal.close()
