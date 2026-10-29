"""Actual owned Linux worker I/O faults, without changing its executable argv.

A directory blocks the owned canonical journal path. For finalization, the open
journal is first retained under another private name: its bytes are preserved,
but it is not substituted as evidence through the application reader.
"""

import hashlib
import json
import os
from pathlib import Path
import sys
import time

import psutil
import pytest

from test_advanced_api import prepared
from xverse_studio.storage.core import canonical, digest


@pytest.mark.skipif(sys.platform != "linux", reason="Owned Linux filesystem-fault lane; native Windows remains held")
@pytest.mark.parametrize("boundary", ["journal_open", "journal_exists", "journal_finalize"])
def test_native_evidence_io_failure_preserves_known_lifecycle_and_cleanup(
    client, monkeypatch, record_property, boundary
):
    from xverse_studio.runs import service as module

    project, _ = prepared(client)
    changed = client.post(
        f"/api/v1/projects/{project['projectId']}/edits",
        headers={"If-Match": str(project["revision"])},
        json={"baseRevision": project["revision"], "edits": [
            {"kind": "set_parameter", "parameterId": "duration", "value": 4},
            {"kind": "set_parameter", "parameterId": "timestep", "value": 1},
        ]},
    )
    assert changed.status_code == 200, changed.text
    project = changed.json()
    selected = client.post(
        f"/api/v1/projects/{project['projectId']}/preflights",
        json={"revision": project["revision"]},
    )
    assert selected.status_code == 200 and selected.json()["status"] == "ready"
    preflight = selected.json()
    studio = client.app.state.studio
    snapshot = canonical(studio.store.get("snapshot", preflight["snapshotId"]))
    snapshot_file = studio.store.root / "snapshots" / preflight["snapshotId"] / "snapshot.json"
    snapshot_bytes = snapshot_file.read_bytes()
    launches = []
    original_launch = module.subprocess.Popen

    def launch_with_owned_path_fault(argv, *args, **kwargs):
        directory = Path(argv[-1])
        expected = [sys.executable, "-I", "-m", "xverse_studio.providers.worker", str(directory)]
        assert argv == expected and directory.parent == studio.store.root / "runs"
        known = studio.store.get("run", directory.name)
        assert known["providerId"] == "studio.reference"
        assert known["launchArgvDigest"] == digest(expected)
        assert digest((directory / "owner.key").read_bytes()) == known["ownerDigest"]
        if boundary == "journal_open":
            (directory / "evidence.jsonl").mkdir()
        elif boundary == "journal_exists":
            (directory / "evidence.jsonl").write_bytes(b'{"retained":"owned prior bytes"}\n')
        child = original_launch(argv, *args, **kwargs)
        process = psutil.Process(child.pid)
        assert child.pid != os.getpid() and process.cmdline() == expected
        launches.append((child, process.create_time()))
        return child

    payload = {"snapshotId": preflight["snapshotId"], "preflightId": preflight["preflightId"]}
    headers = {"Idempotency-Key": "owned-evidence-io-" + boundary}
    with monkeypatch.context() as fault:
        fault.setattr(module.subprocess, "Popen", launch_with_owned_path_fault)
        accepted = client.post("/api/v1/runs", headers=headers, json=payload)
    assert accepted.status_code == 202, accepted.text
    receipt = accepted.json()
    rid = receipt["runId"]
    assert len(launches) == 1
    child, birth = launches[0]
    directory = studio.runs.directory(rid)
    journal = directory / "evidence.jsonl"
    retained, initial_bytes = None, None
    if boundary == "journal_finalize":
        deadline = time.monotonic() + 20
        while time.monotonic() < deadline:
            current = client.get("/api/v1/runs/" + rid).json()
            # Metadata and a later journal read are separate observations. Both
            # must establish the running fault-delivery window before mutation.
            if current["state"] == "running" and journal.is_file():
                data = journal.read_bytes()
                records = [json.loads(line) for line in data.splitlines(keepends=True) if line.endswith(b"\n")]
                if any(row["type"] == "observation.available" for row in records):
                    break
            time.sleep(0.02)
        else:
            raise AssertionError("No actual owned observation preceded the finalization fault")
        known = studio.store.get("run", rid)
        state = json.loads((directory / "state.json").read_text())
        process = psutil.Process(child.pid)
        assert child.poll() is None and process.is_running()
        assert process.create_time() == birth == known["createTime"] == state["createTime"]
        assert process.cmdline() == [sys.executable, "-I", "-m", "xverse_studio.providers.worker", str(directory)]
        assert known["pid"] == state["pid"] == child.pid
        assert state["ownerDigest"] == known["ownerDigest"] == digest((directory / "owner.key").read_bytes())
        assert current["state"] == state["state"] == "running"
        initial_bytes = journal.read_bytes()
        retained = directory / "retained-before-finalization-fault.jsonl"
        assert not retained.exists()
        journal.rename(retained)
        journal.mkdir()

    assert child.wait(timeout=20) == 1
    state = json.loads((directory / "state.json").read_text())
    known = studio.store.get("run", rid)
    assert state["pid"] == known["pid"] == child.pid
    assert state["createTime"] == known["createTime"] == birth
    assert state["ownerDigest"] == known["ownerDigest"]
    assert state["cleanup"] == "complete"
    if boundary in ("journal_open", "journal_exists"):
        if boundary == "journal_exists":
            assert journal.read_bytes() == b'{"retained":"owned prior bytes"}\n'
        assert state["state"] == "failed" and state["reason"] == "EVIDENCE_OPEN_FAILED"
        assert state["evidence"] == "unavailable" and "startedAt" not in state
    else:
        assert state["state"] == "stopped" and state["reason"] == "EVIDENCE_FINALIZATION_FAILED"
        assert state["evidence"] == "partial" and isinstance(state["startedAt"], (int, float))
        assert state["evidenceFailure"] == "EVIDENCE_FINALIZATION_FAILED"
        assert "journalDigest" not in state and "eventCount" not in state
        assert retained.read_bytes().startswith(initial_bytes)
        previous = "0" * 64
        for sequence, line in enumerate(retained.read_bytes().splitlines(), 1):
            row = json.loads(line)
            expected = row.pop("digest")
            assert row["runId"] == rid and row["snapshotId"] == preflight["snapshotId"]
            assert row["sequence"] == str(sequence) and row["previousDigest"] == previous
            assert hashlib.sha256(canonical(row).encode()).hexdigest() == expected
            previous = expected
    observed = client.get("/api/v1/runs/" + rid).json()
    assert observed["state"] == state["state"] and observed["reason"] == state["reason"]
    assert observed["cleanup"] == "complete" and observed["evidence"] == "invalid"
    assert observed["verdict"] is None
    assert client.post("/api/v1/runs", headers=headers, json=payload).json() == receipt
    assert len(studio.store.all("run")) == 1 and len(launches) == 1
    assert studio.projects.read(project["projectId"]) == project
    assert canonical(studio.store.get("snapshot", preflight["snapshotId"])) == snapshot
    assert snapshot_file.read_bytes() == snapshot_bytes
    record_property("owned_evidence_io", json.dumps(dict(
        scope="Actual owned Linux worker; fixed private filesystem fault, no equipment",
        boundary=boundary, runId=rid, snapshotId=preflight["snapshotId"],
        originalArgvAndOwnerVerified=True, nativeWorkerAttempts=len(launches),
        originalCanonicalBytesRetained=boundary == "journal_finalize",
        lifecycle=observed["state"], cleanup=observed["cleanup"], evidence=observed["evidence"],
    )))
