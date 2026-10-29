"""Actual owned-worker temporary-resource release faults; no equipment access.

The test adds retained bytes only after verifying the original native child and
an actual model sample. Neither the worker's state nor its argv is substituted.
"""

import hashlib
import json
from pathlib import Path
import sys
import time

import psutil
import pytest

from test_advanced_api import prepared
from xverse_studio.storage.core import canonical, digest


@pytest.mark.skipif(sys.platform != "linux", reason="Owned Linux resource/symlink fault lane; native Windows remains held")
@pytest.mark.parametrize("boundary", ["empty", "stop", "cancel", "duration", "substitution", "finalization"])
def test_native_cleanup_reports_actual_retained_resources_without_deleting_contents(
    client, monkeypatch, record_property, boundary
):
    from xverse_studio.runs import service as module

    project, _ = prepared(client)
    edited = client.post(
        f"/api/v1/projects/{project['projectId']}/edits",
        headers={"If-Match": str(project["revision"])},
        json={"baseRevision": project["revision"], "edits": [
            {"kind": "set_parameter", "parameterId": "duration", "value": 5},
            {"kind": "set_parameter", "parameterId": "timestep", "value": 0.5},
        ]},
    )
    assert edited.status_code == 200, edited.text
    project = edited.json()
    checked = client.post(
        f"/api/v1/projects/{project['projectId']}/preflights",
        json={"revision": project["revision"]},
    )
    assert checked.status_code == 200 and checked.json()["status"] == "ready"
    preflight = checked.json()
    studio = client.app.state.studio
    snapshot = canonical(studio.store.get("snapshot", preflight["snapshotId"]))
    snapshot_file = studio.store.root / "snapshots" / preflight["snapshotId"] / "snapshot.json"
    snapshot_bytes = snapshot_file.read_bytes()
    launches = []
    original_launch = module.subprocess.Popen

    def tracked_launch(argv, *args, **kwargs):
        directory = Path(argv[-1])
        expected = [sys.executable, "-I", "-m", "xverse_studio.providers.worker", str(directory)]
        assert argv == expected and directory.parent == studio.store.root / "runs"
        known = studio.store.get("run", directory.name)
        assert known["launchArgvDigest"] == digest(expected)
        assert digest((directory / "owner.key").read_bytes()) == known["ownerDigest"]
        assert all(kwargs["env"][key] == str(directory / "tmp") for key in ["TMPDIR", "TEMP", "TMP"])
        child = original_launch(argv, *args, **kwargs)
        launches.append((child, psutil.Process(child.pid).create_time()))
        return child

    payload = {"snapshotId": preflight["snapshotId"], "preflightId": preflight["preflightId"]}
    headers = {"Idempotency-Key": "owned-cleanup-" + boundary}
    with monkeypatch.context() as tracking:
        tracking.setattr(module.subprocess, "Popen", tracked_launch)
        accepted = client.post("/api/v1/runs", headers=headers, json=payload)
    assert accepted.status_code == 202, accepted.text
    receipt = accepted.json()
    rid = receipt["runId"]
    assert len(launches) == 1
    child, birth = launches[0]
    directory = studio.runs.directory(rid)
    temporary = directory / "tmp"
    journal = directory / "evidence.jsonl"
    deadline = time.monotonic() + 20
    while time.monotonic() < deadline:
        current = client.get("/api/v1/runs/" + rid).json()
        if current["state"] == "running" and journal.is_file():
            records = [json.loads(line) for line in journal.read_bytes().splitlines(keepends=True) if line.endswith(b"\n")]
            if any(row["type"] == "observation.available" for row in records):
                break
        time.sleep(0.02)
    else:
        raise AssertionError("No original native sample preceded cleanup-fault delivery")
    known = studio.store.get("run", rid)
    state = json.loads((directory / "state.json").read_text())
    process = psutil.Process(child.pid)
    assert child.poll() is None and process.is_running()
    assert process.create_time() == birth == known["createTime"] == state["createTime"]
    assert process.cmdline() == [sys.executable, "-I", "-m", "xverse_studio.providers.worker", str(directory)]
    assert known["pid"] == state["pid"] == child.pid
    assert state["ownerDigest"] == known["ownerDigest"] == digest((directory / "owner.key").read_bytes())
    assert current["state"] == state["state"] == "running"
    assert temporary.is_dir() and not temporary.is_symlink()

    outside = studio.store.root / ("unrelated-" + rid)
    outside.mkdir()
    outside_file = outside / "preserved.bin"
    preserved = b"Owned test bytes outside worker cleanup authority\n"
    outside_file.write_bytes(preserved)
    retained = b"Retained native temporary-resource test bytes\n"
    if boundary == "substitution":
        temporary.rmdir()
        temporary.symlink_to(outside, target_is_directory=True)
    elif boundary != "empty":
        (temporary / "retained.bin").write_bytes(retained)
    retained_journal, prefix = None, None
    if boundary == "finalization":
        prefix = journal.read_bytes()
        retained_journal = directory / "retained-cleanup-journal.jsonl"
        journal.rename(retained_journal)
        journal.mkdir()

    operation = None
    if boundary in ("empty", "stop", "cancel", "substitution"):
        command = {"kind": "cancel" if boundary == "cancel" else "stop", "expectedStateVersion": current["stateVersion"]}
        command_headers = {"Idempotency-Key": "cleanup-control-" + boundary}
        response = client.post(f"/api/v1/runs/{rid}/commands", headers=command_headers, json=command)
        assert response.status_code == 202, response.text
        operation = response.json()
        assert client.post(f"/api/v1/runs/{rid}/commands", headers=command_headers, json=command).json() == operation

    exit_code = child.wait(timeout=20)
    state = json.loads((directory / "state.json").read_text())
    observed = client.get("/api/v1/runs/" + rid).json()
    record_property("native_cleanup", json.dumps(dict(
        scope="Actual owned Linux worker; fixed private temporary-directory fault, no equipment",
        boundary=boundary, runId=rid, snapshotId=preflight["snapshotId"],
        originalArgvOwnerBirthAndSampleVerified=True, nativeWorkerAttempts=len(launches),
        workerExit=exit_code, lifecycle=state["state"], cleanup=state["cleanup"],
        cleanupResources=state.get("cleanupResources"), observedCleanup=observed["cleanup"],
        unrelatedBytesPreserved=outside_file.read_bytes() == preserved,
    )))
    expected_resources = [] if boundary == "empty" else [{
        "resourceId": rid + ":temporary-directory", "kind": "temporary-directory",
        "status": "retained", "code": "TEMPORARY_DIRECTORY_NOT_RELEASED",
    }]
    assert state["state"] == observed["state"] == "stopped"
    assert state["cleanup"] == observed["cleanup"] == ("complete" if boundary == "empty" else "failed")
    assert state["cleanupResources"] == observed["cleanupResources"] == expected_resources
    assert exit_code == (0 if boundary == "empty" else 1)
    assert outside_file.read_bytes() == preserved
    if boundary == "empty":
        assert not temporary.exists()
    elif boundary == "substitution":
        assert temporary.is_symlink() and outside.is_dir()
    else:
        assert (temporary / "retained.bin").read_bytes() == retained
    if boundary == "finalization":
        assert state["evidence"] == "partial" and observed["evidence"] == "invalid"
        assert state["evidenceFailure"] == "EVIDENCE_FINALIZATION_FAILED"
        assert retained_journal.read_bytes().startswith(prefix)
        source = retained_journal
    else:
        assert state["evidence"] == observed["evidence"] == "complete"
        source = journal
    previous = "0" * 64
    events = []
    for sequence, line in enumerate(source.read_bytes().splitlines(), 1):
        row = json.loads(line)
        signature = row.pop("digest")
        assert row["runId"] == rid and row["snapshotId"] == preflight["snapshotId"]
        assert row["sequence"] == str(sequence) and row["previousDigest"] == previous
        assert hashlib.sha256(canonical(row).encode()).hexdigest() == signature
        previous = signature
        events.append(row)
    cleanup_event = next(row for row in events if row["type"] == "cleanup.updated")
    assert cleanup_event["payload"] == {"status": observed["cleanup"], "resources": expected_resources}
    if operation:
        assert client.get("/api/v1/operations/" + operation["operationId"]).json()["status"] == "completed"
        assert sum(row["type"] == "command.completed" and row["payload"]["operationId"] == operation["operationId"] for row in events) == 1
    assert observed["verdict"] is None
    assert client.post("/api/v1/runs", headers=headers, json=payload).json() == receipt
    assert len(studio.store.all("run")) == 1 and len(launches) == 1
    assert studio.projects.read(project["projectId"]) == project
    assert canonical(studio.store.get("snapshot", preflight["snapshotId"])) == snapshot
    assert snapshot_file.read_bytes() == snapshot_bytes
    if boundary != "empty":
        findings = client.get(f"/api/v1/runs/{rid}/diagnostics").json()["findings"]
        cleanup = next(f for f in findings if f["code"] == "CLEANUP_FAILED")
        assert rid + ":temporary-directory" in json.dumps(cleanup)
