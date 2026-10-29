"""Finite disposable fixture; invokes the real route and StreamingResponse lifecycle."""
import asyncio
import hashlib
import importlib.util
import json
from pathlib import Path
import tempfile

from starlette.requests import Request
from xverse_studio.api.app import create_app

ROOT = Path(__file__).resolve().parents[4]
FILES = ["services/studio-api/src/xverse_studio/events/__init__.py", "services/studio-api/src/xverse_studio/api/app.py"]
def hashes():
    return {p: hashlib.sha256((ROOT / p).read_bytes()).hexdigest() for p in FILES}

def load_fixture():
    path = ROOT / "tests/fixtures/evidence/stream_fixtures.py"
    spec = importlib.util.spec_from_file_location("independent_stream_fixture", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

async def probe(base):
    source = load_fixture().AdvancingJournal(base / "journal")
    source.append()
    original = source.path.read_bytes()
    app = create_app(base / "data", bootstrap_token="new-owned-fixture")
    app.state.studio.events.runs = source
    endpoint = next(r.endpoint for r in app.routes if getattr(r, "path", "") == "/api/v1/runs/{runId}/events")
    results = []
    for mode in ("headers_oserror", "headers_cancelled"):
        scope = {"type": "http", "asgi": {"version": "3.0", "spec_version": "2.4"}, "method": "GET", "scheme": "http", "path": "/api/v1/runs/fixture-stream/events", "raw_path": b"/api/v1/runs/fixture-stream/events", "root_path": "", "query_string": b"streamVersion=1.1", "headers": [], "server": ("testserver", 80), "client": ("127.0.0.1", 1)}
        response = await endpoint(source.run_id, Request(scope), streamVersion="1.1")
        admitted = len(app.state.studio.events.leases)
        calls = []
        async def send(message):
            calls.append(message["type"])
            if mode == "headers_oserror":
                raise OSError("Owned synthetic disconnected transport")
            raise asyncio.CancelledError()
        async def receive():
            return {"type": "http.disconnect"}
        try:
            await response(scope, receive, send)
        except BaseException as exc:
            error = type(exc).__name__
        else:
            error = None
        remaining = len(app.state.studio.events.leases)
        await response.body_iterator.aclose()
        after_close = len(app.state.studio.events.leases)
        results.append({"mode": mode, "admitted": admitted, "sendCalls": calls, "responseError": error, "remainingAfterResponse": remaining, "remainingAfterIteratorClose": after_close})
        app.state.studio.events.leases.clear()
    return {"cases": results, "originalJournalUnchanged": source.path.read_bytes() == original, "scope": "Real API endpoint and Starlette response invoked directly; synthetic transport disconnect; no server/runtime process launched."}

if __name__ == "__main__":
    before = hashes()
    (ROOT / ".studio-local/review-temp").mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="stream-disconnect-", dir=ROOT / ".studio-local/review-temp") as directory:
        result = asyncio.run(asyncio.wait_for(probe(Path(directory)), timeout=15))
    print(json.dumps({"sourceBefore": before, "sourceAfter": hashes(), **result}, indent=2))
