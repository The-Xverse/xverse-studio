"""Bounded contributor timing host; normal unregistered launcher and real callbacks.

Never records headers, bodies, project text, secrets or session identities. Raw
cProfile paths remain private. Diagnostic overhead is not a performance verdict.
"""

import argparse
import atexit
import cProfile
from contextlib import asynccontextmanager
from functools import wraps
import json
from pathlib import Path
import threading
import time


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--data-dir", required=True, type=Path)
    parser.add_argument("--port", required=True, type=int)
    parser.add_argument("--static-dir", required=True, type=Path)
    args = parser.parse_args()
    data = args.data_dir.resolve()
    if data.parent.name != "browser-tests":
        parser.error("A dedicated contributor browser-tests root is required.")
    target = data / "binding-timing"
    target.mkdir(mode=0o700, exist_ok=False)
    lock = threading.Lock()
    counts = {"records": 0, "profiles": 0, "droppedRecords": 0, "droppedProfiles": 0, "writeErrors": 0}

    def emit(record):
        with lock:
            if counts["records"] >= 2048:
                counts["droppedRecords"] += 1
                return
            counts["records"] += 1
            try:
                with (target / "timing.jsonl").open("a", encoding="utf-8") as stream:
                    stream.write(json.dumps(record) + "\n")
                (target / "timing.jsonl").chmod(0o600)
            except OSError:
                counts["writeErrors"] += 1

    def finish():
        (target / "summary.json").write_text(json.dumps({"scope": "Instrumented contributor host only; no provider registration or runtime/device actions", "limits": {"records": 2048, "profiles": 64}, **counts}, indent=2) + "\n")
        (target / "summary.json").chmod(0o600)

    atexit.register(finish)
    from xverse_studio.deployments import Deployments
    from xverse_studio.storage.core import Store
    from xverse_studio.api import app as api_module

    original_update = Deployments.update_binding

    @wraps(original_update)
    def update(service, *positional, **keywords):
        if service.projects.store.root.resolve() != data:
            return original_update(service, *positional, **keywords)
        with lock:
            if counts["profiles"] >= 64:
                counts["droppedProfiles"] += 1
                index = None
            else:
                counts["profiles"] += 1
                index = counts["profiles"]
        started, cpu = time.monotonic_ns(), time.thread_time_ns()
        profiler = cProfile.Profile() if index is not None else None
        failed = False
        try:
            if profiler is None:
                return original_update(service, *positional, **keywords)
            return profiler.runcall(original_update, service, *positional, **keywords)
        except BaseException:
            failed = True
            raise
        finally:
            ended, cpu_end = time.monotonic_ns(), time.thread_time_ns()
            if profiler is not None:
                try:
                    path = target / f"binding-{index:04d}.pstats"
                    profiler.dump_stats(path)
                    path.chmod(0o600)
                except OSError:
                    with lock:
                        counts["writeErrors"] += 1
            emit({"kind": "binding_callback", "profile": index, "startedNs": started, "endedNs": ended, "wallNs": ended - started, "threadCpuNs": cpu_end - cpu, "failed": failed})

    Deployments.update_binding = update
    original_get = Store.get

    @wraps(original_get)
    def get(store, kind, identity, db=None):
        if db is not None or kind != "session" or store.root.resolve() != data:
            return original_get(store, kind, identity, db)
        started = time.monotonic_ns()
        try:
            return original_get(store, kind, identity, db)
        finally:
            emit({"kind": "session_lookup", "startedNs": started, "endedNs": time.monotonic_ns()})

    Store.get = get

    class Timing:
        def __init__(self, app):
            self.app = app

        async def __call__(self, scope, receive, send):
            if scope["type"] != "http" or not scope.get("path", "").startswith("/api/"):
                return await self.app(scope, receive, send)
            path = scope["path"]
            family = "binding" if "/deployment-variants/" in path else "session" if path == "/api/v1/session" else "other_api"
            started, first_receive, first_send, received_bytes, status = time.monotonic_ns(), None, None, 0, None

            async def observed_receive():
                nonlocal first_receive, received_bytes
                message = await receive()
                if message["type"] == "http.request":
                    if first_receive is None:
                        first_receive = time.monotonic_ns()
                    received_bytes += len(message.get("body", b""))
                return message

            async def observed_send(message):
                nonlocal first_send, status
                if message["type"] == "http.response.start":
                    first_send, status = time.monotonic_ns(), message["status"]
                await send(message)

            failed = False
            try:
                return await self.app(scope, observed_receive, observed_send)
            except BaseException:
                failed = True
                raise
            finally:
                emit({"kind": "request", "family": family, "method": scope["method"], "startedNs": started, "firstReceiveNs": first_receive, "firstSendNs": first_send, "endedNs": time.monotonic_ns(), "receivedBytes": received_bytes, "status": status, "failed": failed})

    create_app = api_module.create_app

    @wraps(create_app)
    def observed_app(*positional, **keywords):
        app = create_app(*positional, **keywords)
        app.add_middleware(Timing)
        original_lifespan = app.router.lifespan_context

        @asynccontextmanager
        async def lifespan(application):
            try:
                async with original_lifespan(application) as state:
                    yield state
            finally:
                finish()

        app.router.lifespan_context = lifespan
        return app

    api_module.create_app = observed_app
    # Import only after installing the contributor wrapper. The normal launcher
    # still owns startup, authentication, persistence, lifecycle and shutdown.
    from xverse_studio.host.launcher import main as launch

    launch()


if __name__ == "__main__":
    main()
