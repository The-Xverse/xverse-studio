"""Trusted NEW recorded reader fixtures; no provider start or existing journal edits.

CLI access is limited to an existing isolated native-browser-test data root. This
helper is not imported by application routes and is not a production injection API.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import time

from xverse_studio.storage.core import Store, canonical, uid
from xverse_studio.projects.service import Projects
from xverse_studio.runs.service import Runs
from xverse_studio.xdl import XDLAdapter


ALPHA = "clock-alpha"
BETA = "clock-beta"
START = "9007199254740993"
END = "9007199254740994"


def fixture_records(
    run_id="recorded-reader-fixture",
    snapshot_id="fixture-snapshot",
    *,
    system_ref="xdl://org.example/system/reader-fixture",
    noise=205,
):
    """Synthetic codec/clock data, not admitted runtime or physical observations."""
    rows, ids = [], {}

    def add(
        name,
        tick,
        *,
        clock=ALPHA,
        provider="fixture.alpha",
        observer="state-observer",
        values=None,
        receipt="2026-01-01T00:00:01Z",
        kind="observation.available",
        severity=None,
        element="plant",
    ):
        record = {
            "schemaVersion": "1.0",
            "eventId": run_id + ":" + name,
            "runId": run_id,
            "snapshotId": snapshot_id,
            "sequence": str(len(rows) + 1),
            "type": kind,
            "recordedAt": receipt,
            "sourceTime": None
            if tick is None
            else {
                "tick": tick,
                "clockDomain": clock,
                "resolution": "nanosecond" if clock == ALPHA else "microsecond",
                "uncertainty": 0,
            },
            "source": {
                "providerId": provider,
                "version": "1.0.0",
                "kind": "trusted-synthetic-reader-fixture",
            },
            "elementRefs": [system_ref + "#" + element],
            "evidenceClass": "unknown",
            "evidenceRefs": [run_id + ":reference-journal"],
        }
        if kind == "observation.available":
            record["payload"] = {
                "observerRef": observer,
                "values": values if values is not None else {"value": 1},
                "units": {"value": "1", "flag": "1"},
            }
        elif kind == "observation.gap":
            record["payload"] = {
                "reason": "Synthetic declared collection gap",
                "clockDomain": ALPHA,
                "startTick": "1",
                "endTick": "2",
            }
        else:
            record["payload"] = {
                "severity": severity or "info",
                "message": "Synthetic recorded reader fixture " + name,
            }
        rows.append(record)
        ids[name] = record["eventId"]

    add(
        "hugeBefore",
        "9007199254740992",
        provider="studio.reference",
        values={"value": 0, "flag": False},
        receipt=1767225600.25,
    )
    add(
        "hugeInside",
        START,
        values={"value": 0.25, "flag": False},
        receipt="2026-01-01T01:00:01+01:00",
    )
    add("hugeEnd", END, values={"value": 3}, receipt="2026-01-01T00:00:02Z")
    add("negative", "-2", values={"value": -2}, receipt="2026-01-01T00:00:03Z")
    add("zero", "0", values={"value": 0, "flag": False}, receipt="2026-01-01T00:00:04Z")
    add("missingTime", None, values={"value": 7}, receipt="2026-01-01T00:00:05Z")
    add(
        "malformedTime",
        "not-a-tick",
        values={"value": 8},
        receipt="2026-01-01T00:00:06Z",
    )
    add(
        "otherClock",
        START,
        clock=BETA,
        provider="fixture.beta",
        observer="external-observer",
        values={"value": 11},
        receipt="2026-01-01T00:00:07Z",
    )
    add("unknownReceipt", "4", provider="fixture.unknown", receipt=1767225600.5)
    add("missingReceipt", "5", receipt=None)
    add("gap", None, receipt="2026-01-01T00:00:10Z", kind="observation.gap")
    add("logAlpha", "6", receipt="2026-01-01T00:00:11Z", kind="log.appended")
    add(
        "logBeta",
        "7",
        clock=BETA,
        provider="fixture.beta",
        receipt="2026-01-01T00:00:12Z",
        kind="log.appended",
        severity="warning",
        element="controller",
    )
    for index in range(noise):
        add(
            "noise-" + str(index),
            str(100 + index),
            provider="fixture.noise",
            observer="noise-observer",
            values={"noise": index},
            receipt="2026-01-01T00:01:00Z",
        )
    add(
        "late",
        "999",
        provider="fixture.late",
        values={"selected": False},
        receipt="2026-01-01T00:02:00Z",
    )
    add(
        "lateLog",
        "1000",
        provider="fixture.late",
        receipt="2026-01-01T00:02:01Z",
        kind="log.appended",
        severity="error",
    )
    return rows, {
        name: value for name, value in ids.items() if not name.startswith("noise-")
    }


def write_journal(destination, records):
    """Exclusively write a NEW sealed journal and return its byte digest."""
    destination.mkdir(parents=True, exist_ok=False)
    previous, whole = "0" * 64, hashlib.sha256()
    with (destination / "evidence.jsonl").open("xb") as stream:
        for row in records:
            record = {**row, "previousDigest": previous}
            previous = hashlib.sha256(canonical(record).encode()).hexdigest()
            record["digest"] = previous
            line = (canonical(record) + "\n").encode()
            stream.write(line)
            whole.update(line)
    return "sha256:" + whole.hexdigest()


def create_recorded_evidence(store, projects, runs, project_id, *, noise=205):
    project = projects.read(project_id)
    preflight = runs.preflight(project_id, {"revision": project["revision"]})
    if preflight["status"] != "ready":
        raise RuntimeError("Choose an authoritatively ready owned reference project.")
    snapshot = store.get("snapshot", preflight["snapshotId"])
    run_id, operation_id = uid("run-reader-fixture-"), uid("op-reader-fixture-")
    records, ids = fixture_records(
        run_id,
        snapshot["snapshotId"],
        system_ref=snapshot["selection"]["systemRef"],
        noise=noise,
    )
    root = runs.directory(run_id)
    journal_digest = write_journal(root, records)
    now = time.time()
    run = {
        "runId": run_id,
        "snapshotId": snapshot["snapshotId"],
        "projectId": project_id,
        "revision": project["revision"],
        "operationId": operation_id,
        "state": "stopped",
        "stateVersion": 1,
        "cleanup": "not_applicable",
        "evidence": "partial",
        "evaluation": "not_started",
        "verdict": None,
        "capabilities": [],
        "evidenceScope": "recorded_fixture",
        "providerId": "owned.recorded-fixture",
        "createdAt": now,
        "endedAt": now,
        "planDigest": snapshot["planDigest"],
        "semanticDigest": snapshot["semanticDigest"],
        "journalDigest": journal_digest,
        "eventCount": len(records),
        "limitations": [
            "Trusted synthetic reader/codec fixture only; no process ownership or provider operation.",
            "Clock/observer/source labels exercise raw reader handling, not runtime or physical admission.",
            "Declared gap remains partial evidence even when hash integrity is valid.",
        ],
    }
    with store.tx() as db:
        store.put(
            "operation",
            operation_id,
            {
                "operationId": operation_id,
                "kind": "recorded_fixture",
                "status": "completed",
                "runId": run_id,
                "result": {"scope": "recorded_fixture"},
            },
            db,
        )
        store.put("run", run_id, run, db)
    return {
        "projectId": project_id,
        "runId": run_id,
        "snapshotId": snapshot["snapshotId"],
        "recordCount": len(records),
        "journalDigest": journal_digest,
        "events": ids,
        "ticks": {"start": START, "end": END},
        "clockDomains": [ALPHA, BETA],
        "observerRefs": ["state-observer", "external-observer", "noise-observer"],
        "sourceProviderIds": [
            "studio.reference",
            "fixture.alpha",
            "fixture.beta",
            "fixture.unknown",
            "fixture.noise",
            "fixture.late",
        ],
        "evidenceScope": "recorded_fixture",
        "gapReason": "Synthetic declared collection gap",
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--data-dir", type=Path, required=True)
    parser.add_argument("--project-id", required=True)
    args = parser.parse_args()
    root = args.data_dir.resolve()
    allowed = Path(__file__).resolve().parents[3] / ".studio-local/browser-tests"
    if (
        not root.is_relative_to(allowed.resolve())
        or not (root / "studio.sqlite").is_file()
    ):
        parser.error(
            "Only existing isolated .studio-local/browser-tests roots are allowed."
        )
    store = Store(root)
    adapter = XDLAdapter()
    projects = Projects(store, adapter)
    runs = Runs(store, projects, adapter)
    print(json.dumps(create_recorded_evidence(store, projects, runs, args.project_id)))


if __name__ == "__main__":
    main()
