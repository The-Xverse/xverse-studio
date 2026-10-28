"""Closed native failure fixture; the stock application has no fault controls."""

import argparse
from contextlib import asynccontextmanager
import importlib.util
import json
import os
from pathlib import Path
import socket
import threading
import time

import uvicorn

from xverse_studio.api.app import create_app
from xverse_studio.runs import service as run_module
from xverse_studio.storage.core import canonical


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--data", type=Path, required=True)
    parser.add_argument("--scenario", choices=["mismatch", "launch_denied", "active_failure", "normal", "ownership_recovery"], required=True)
    args = parser.parse_args()
    args.data = args.data.resolve()
    root = Path(__file__).resolve().parents[4]
    observation = dict(scope="owned native fault fixture; no equipment", scenario=args.scenario,
                       workerAttempts=0, corruptions=0, launchRefusals=0, interruptions=0, ownershipDenials=0, errors=[])
    threads = []
    with socket.socket() as listener:
        listener.bind(("127.0.0.1", 0))
        port = listener.getsockname()[1]
        app = create_app(args.data, allowed_hosts=[f"127.0.0.1:{port}"], static_dir=root / "apps/studio-web/dist")
        runs, store = app.state.studio.runs, app.state.studio.store
        original_write, original_launch = run_module.atomic, run_module.subprocess.Popen
        if args.scenario == "ownership_recovery":
            original_psutil = run_module.psutil

            class OwnedObservationFault:
                def __getattr__(self, name):
                    return getattr(original_psutil, name)

                def Process(self, pid=None, *values, **options):
                    if (args.data / "deny-owned-observation").exists() and any(
                        child.pid == pid for child in runs.children.values()
                    ):
                        observation["ownershipDenials"] += 1
                        raise original_psutil.AccessDenied(pid)
                    return original_psutil.Process(pid, *values, **options)

            # This closed host only faults observation of its own recorded child.
            # The actual psutil module/class and worker process remain unchanged.
            run_module.psutil = OwnedObservationFault()

        def injected_write(path, body):
            target = Path(path)
            if args.scenario == "mismatch" and target.name == "request.json" and target.parent.parent == args.data / "runs":
                request = json.loads(body)
                assert request["snapshot"]["providerId"] == "studio.reference"
                request["configuration"]["gain"] += 0.125
                observation["corruptions"] += 1
                return original_write(path, canonical(request).encode())
            return original_write(path, body)

        def interrupt_after_sample(run_id):
            try:
                deadline = time.monotonic() + 10
                while time.monotonic() < deadline:
                    record = store.get("run", run_id)
                    if run_id in runs.children and record.get("pid") and (runs.directory(run_id) / "state.json").exists():
                        break
                    time.sleep(0.02)
                else:
                    raise AssertionError("Owned worker identity was not recorded")
                # Reuse the existing Linux-only exact PID/birth/argv/owner/sleep guard.
                spec = importlib.util.spec_from_file_location("owned_failure_guard", root / "tests/integration/test_campaign_worker_failure.py")
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
                module.interrupt_owned_sleeping_worker(runs, store, run_id)
                observation["interruptions"] += 1
            except Exception as error:
                observation["errors"].append(type(error).__name__)

        def injected_launch(argv, *values, **options):
            worker = isinstance(argv, list) and len(argv) == 5 and argv[1:4] == ["-I", "-m", "xverse_studio.providers.worker"]
            if worker:
                directory = Path(argv[4])
                assert directory.parent == args.data / "runs"
                observation["workerAttempts"] += 1
                if args.scenario == "launch_denied":
                    observation["launchRefusals"] += 1
                    raise OSError("Labelled owned launch refusal")
            child = original_launch(argv, *values, **options)
            if worker and args.scenario == "active_failure":
                thread = threading.Thread(target=interrupt_after_sample, args=(directory.name,), daemon=True)
                threads.append(thread)
                thread.start()
            return child

        run_module.atomic, run_module.subprocess.Popen = injected_write, injected_launch
        original_lifespan = app.router.lifespan_context

        @asynccontextmanager
        async def retained_lifespan(application):
            try:
                async with original_lifespan(application):
                    yield
            finally:
                for thread in threads:
                    thread.join(timeout=12)
                if any(thread.is_alive() for thread in threads):
                    observation["errors"].append("FaultThreadStillActive")
                (args.data / "fixture-observation.json").write_text(json.dumps(observation), encoding="utf-8")

        app.router.lifespan_context = retained_lifespan
        print(json.dumps(dict(origin=f"http://127.0.0.1:{port}", pid=os.getpid())), flush=True)
        uvicorn.Server(uvicorn.Config(app, host="127.0.0.1", port=port, access_log=False, log_level="error")).run(sockets=[listener])


if __name__ == "__main__":
    main()
