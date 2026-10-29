"""Record the specified 50,000-event local history workload; no live-provider claim."""

import argparse
import hashlib
import json
from pathlib import Path
import platform
import statistics
import time
from fastapi.testclient import TestClient
from xverse_studio.api.app import create_app
from xverse_studio.storage.core import canonical, digest, atomic, uid

parser = argparse.ArgumentParser()
parser.add_argument("--output", type=Path, required=True)
parser.add_argument("--data-dir", type=Path, required=True)
args = parser.parse_args()
args.data_dir.mkdir(parents=True, exist_ok=True)
app = create_app(
    args.data_dir,
    allowed_hosts=["testserver"],
    bootstrap_token="synthetic-performance-bootstrap",
)
s = app.state.studio
rid = uid("fixture-")
root = s.runs.directory(rid)
root.mkdir(parents=True)
previous = "0" * 64
with (root / "evidence.jsonl").open("wb") as f:
    for i in range(50000):
        row = {
            "schemaVersion": "1.0",
            "eventId": rid + ":" + str(i + 1),
            "runId": rid,
            "snapshotId": "recorded-fixture-only",
            "sequence": str(i + 1),
            "type": "log.appended",
            "recordedAt": i,
            "sourceTime": None,
            "source": {"providerId": "owned.recorded-fixture"},
            "elementRefs": [],
            "evidenceClass": "observed",
            "payload": {
                "severity": "info",
                "message": "Retained canonical workload record " + str(i),
            },
            "evidenceRefs": [],
            "previousDigest": previous,
        }
        previous = hashlib.sha256(canonical(row).encode()).hexdigest()
        f.write((canonical({**row, "digest": previous}) + "\n").encode())
s.store.put(
    "run",
    rid,
    {
        "runId": rid,
        "snapshotId": "recorded-fixture-only",
        "state": "stopped",
        "stateVersion": 1,
        "cleanup": "complete",
        "evidence": "complete",
        "journalDigest": digest((root / "evidence.jsonl").read_bytes()),
        "evidenceScope": "recorded_fixture",
        "providerId": "owned.recorded-fixture",
        "capabilities": [],
    },
)
with TestClient(app, base_url="http://testserver") as client:
    client.headers["Origin"] = "http://testserver"
    auth = client.post(
        "/api/v1/session", json={"bootstrapToken": "synthetic-performance-bootstrap"}
    )
    client.headers["X-CSRF-Token"] = auth.json()["csrfToken"]
    url = f"/api/v1/runs/{rid}/history?limit=200&type=log.appended"
    warmup = client.get(url)
    samples = []
    correct = warmup.status_code == 200 and len(warmup.json().get("items", [])) == 200
    for _ in range(30):
        start = time.perf_counter()
        response = client.get(url)
        samples.append((time.perf_counter() - start) * 1000)
        correct &= (
            response.status_code == 200
            and len(response.json().get("items", [])) == 200
            and response.json().get("integrity") == "valid"
        )
    p95 = sorted(samples)[28]
result = {
    "scope": "recorded_local_evidence_fixture_api_only",
    "browserPresentation": "NOT_RUN by this script",
    "os": platform.platform(),
    "python": platform.python_version(),
    "events": 50000,
    "pageSize": 200,
    "warmups": 1,
    "repetitions": 30,
    "milliseconds": samples,
    "p95Milliseconds": p95,
    "correctPages": correct,
    "targetMilliseconds": 2000,
    "passed": correct and p95 <= 2000,
    "nativeWindows": "NOT_RUN",
}
args.output.parent.mkdir(parents=True, exist_ok=True)
args.output.write_text(json.dumps(result, indent=2) + "\n")
print(json.dumps({k: v for k, v in result.items() if k != "milliseconds"}))
raise SystemExit(0 if result["passed"] else 1)
