"""Create NEW inert retained-history evidence in an isolated browser-test root.

This trusted contributor helper is deliberately absent from the application API.
It never starts a provider, mutates an existing journal, or claims live evidence.
"""

from __future__ import annotations
import argparse
from datetime import datetime, timedelta, timezone
import hashlib
import json
from pathlib import Path
import time

from xverse_studio.storage.core import Store, canonical, uid
from xverse_studio.projects.service import Projects
from xverse_studio.runs.service import Runs
from xverse_studio.xdl import XDLAdapter
from xverse_studio.evidence.reader import read_journal


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--data-dir", required=True, type=Path)
    parser.add_argument("--project-id", required=True)
    args = parser.parse_args()
    root = args.data_dir.resolve()
    repository = Path(__file__).resolve().parents[3]
    allowed = repository / ".studio-local" / "browser-tests"
    if (
        not root.is_relative_to(allowed.resolve())
        or not (root / "studio.sqlite").is_file()
    ):
        parser.error(
            "Only an existing isolated .studio-local/browser-tests root is allowed."
        )
    store = Store(root)
    adapter = XDLAdapter()
    projects = Projects(store, adapter)
    project = projects.read(args.project_id)
    runs = Runs(store, projects, adapter)
    preflight = runs.preflight(project["projectId"], {"revision": project["revision"]})
    if preflight["status"] != "ready":
        raise RuntimeError(
            "The selected reference project is not authoritatively ready."
        )
    snapshot = store.get("snapshot", preflight["snapshotId"])
    run_id, operation_id = uid("run-recorded-fixture-"), uid("op-recorded-fixture-")
    destination = runs.directory(run_id)
    destination.mkdir(parents=True, exist_ok=False)
    journal = destination / "evidence.jsonl"
    previous = "0" * 64
    whole = hashlib.sha256()
    epoch = datetime(2026, 1, 1, tzinfo=timezone.utc)
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
                    "kind": "registered-log-fixture",
                },
                "elementRefs": [],
                "evidenceClass": "observed",
                "evidenceRefs": [],
                "payload": {
                    "severity": "info",
                    "message": f"Recorded fixture log {index:05d}",
                    "scope": "Synthetic registered records; no runtime, simulator or device observation.",
                },
                "previousDigest": previous,
            }
            previous = hashlib.sha256(canonical(record).encode()).hexdigest()
            record["digest"] = previous
            line = (canonical(record) + "\n").encode()
            stream.write(line)
            whole.update(line)
    run = {
        "runId": run_id,
        "snapshotId": snapshot["snapshotId"],
        "projectId": project["projectId"],
        "revision": project["revision"],
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
        "limitations": [
            "Trusted synthetic retained-history fixture only.",
            "No process ownership, provider operation or physical observation exists.",
        ],
    }
    records, integrity = read_journal(destination, run)
    if len(records) != 50000 or integrity != "valid":
        raise RuntimeError("Fixture journal integrity verification failed.")
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
    print(
        json.dumps(
            {
                "projectId": project["projectId"],
                "runId": run_id,
                "snapshotId": snapshot["snapshotId"],
                "recordCount": 50000,
                "journalDigest": run["journalDigest"],
                "journalBytes": journal.stat().st_size,
                "integrity": integrity,
                "evidenceScope": "recorded_fixture",
            }
        )
    )


if __name__ == "__main__":
    main()
