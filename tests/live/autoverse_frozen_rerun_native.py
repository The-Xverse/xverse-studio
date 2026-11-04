"""Complete native rerun of an actual historical Autoverse campaign child.

The original store is copied under its root lock. Only the approved isolated
installation is operated; original canonical files and completed campaign stay
unchanged. A new child must demonstrate Android/APK, vehicle speed and cleanup.
"""

import argparse
import importlib.util
import json
from pathlib import Path
import shutil
import signal
import sqlite3
import sys
import time
import uuid

from xverse_studio.host.ownership import own_root
from xverse_studio.storage.core import digest


_spec = importlib.util.spec_from_file_location(
    "recorded_native_tools", Path(__file__).with_name("autoverse_campaign_browser.py")
)
recorded = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(recorded)
native = recorded.native


def main():
    parser = argparse.ArgumentParser()
    for name in ("recording", "receipt", "static-dir", "output"):
        parser.add_argument("--" + name, type=Path, required=True)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=False)
    original_result = json.loads((args.recording / "native-result.json").read_bytes())
    assert original_result["outcome"] == "passed"
    source_child = original_result["children"][0]
    assert source_child["fullAndroidAndVehicleSpeedObserved"]
    original = Path(
        json.loads((args.recording / "data-root.private.json").read_bytes())["dataRoot"]
    )
    before = recorded.hashes(original)
    data = (
        native.ROOT
        / ".studio-local/browser-tests"
        / ("frozen-rerun-" + uuid.uuid4().hex)
    )
    with own_root(original):
        assert all(not p.is_symlink() for p in original.rglob("*"))
        shutil.copytree(
            original,
            data,
            ignore=shutil.ignore_patterns(
                "studio.lock",
                "studio.sqlite*",
                "browser-session.private.json",
                "bootstrap.json",
            ),
        )
        with (
            sqlite3.connect(
                (original / "studio.sqlite").as_uri() + "?mode=ro", uri=True
            ) as source,
            sqlite3.connect(data / "studio.sqlite") as target,
        ):
            source.backup(target)
            target.execute("DELETE FROM records WHERE kind='session'")
    assert recorded.hashes(data) == before
    (args.output / "data-root.private.json").write_text(
        json.dumps({"dataRoot": str(data)}) + "\n"
    )
    report = {
        "outcome": "failed",
        "scope": "complete actual frozen-input rerun on the same isolated installed Autoverse; no deterministic replay or physical claim",
        "sourceRunId": source_child["runId"],
        "sourceSnapshotId": source_child["snapshotId"],
        "projectId": original_result["projectId"],
        "before": recorded.ledger(data),
    }
    host = native.NativeHost(
        data,
        args.output,
        args.receipt.resolve(),
        Path(sys.executable),
        args.static_dir.resolve(),
    )
    api, worker, rid = None, None, None
    try:
        host.start()
        api = native.login(host)
        source_route = "/api/v1/runs/" + source_child["runId"]
        frozen_bytes = (
            data / "snapshots" / source_child["snapshotId"] / "snapshot.json"
        ).read_bytes()
        frozen = json.loads(frozen_bytes)
        project = native.checked(api.get("/api/v1/projects/" + report["projectId"]))
        assert project["revision"] > frozen["revision"]
        for suffix in ("observations", "evidence", "history"):
            native.checked(api.get(source_route + "/" + suffix))
        before_execution = recorded.ledger(data)
        baseline = native.checked(
            api.post(
                "/api/v1/comparisons",
                json={
                    "leftRunId": source_child["runId"],
                    "rightRunId": original_result["children"][1]["runId"],
                },
            )
        )
        assert (
            baseline["compatible"] is False
            and baseline["mode"] == "recorded_observation_comparison"
        )
        assert recorded.ledger(data) == before_execution
        key = {"Idempotency-Key": "historical-installed-frozen-rerun"}
        receipt = native.checked(
            api.post(source_route + "/reruns", headers=key, json={}), 202
        )
        assert (
            native.checked(
                api.post(source_route + "/reruns", headers=key, json={}), 202
            )
            == receipt
        )
        operation = native.checked(
            api.get("/api/v1/operations/" + receipt["operationId"])
        )
        assert operation["status"] == "completed", operation
        rid = operation["result"]["runId"]
        route = "/api/v1/runs/" + rid
        row = native.wait(
            lambda: native.private_record(data, "run", rid),
            lambda r: bool(r.get("pid")),
            timeout=30,
        )
        worker = native.OriginalProcess(
            row["pid"],
            row["createTime"],
            row["launchArgvDigest"],
            parent=host.child.pid,
        )
        new_path = data / "snapshots" / row["snapshotId"] / "snapshot.json"
        new_bytes = new_path.read_bytes()
        new = json.loads(new_bytes)
        for field in (
            "documents",
            "projectDocuments",
            "profileLocks",
            "selection",
            "configuration",
            "planDigest",
            "semanticDigest",
            "revision",
        ):
            assert new[field] == frozen[field], field
        assert (
            new["sourceRunId"] == source_child["runId"]
            and new["parentSnapshotId"] == frozen["snapshotId"]
        )
        assert new["sourceSnapshotDigest"] == frozen["snapshotDigest"]
        assert new["snapshotId"] != frozen["snapshotId"] and "campaignId" not in new
        report.update(
            runId=rid,
            snapshotId=new["snapshotId"],
            rerunOperationId=receipt["operationId"],
            sourceSnapshotDigest=frozen["snapshotDigest"],
            newSnapshotDigest=new["snapshotDigest"],
            newSnapshotSha256=digest(new_bytes),
            declaredDurationSeconds=new["configuration"]["durationSeconds"],
        )
        counts = recorded.ledger(data)
        refused = api.post(
            source_route + "/reruns",
            headers={"Idempotency-Key": "occupied-installation-refusal"},
            json={},
        )
        assert (
            refused.status_code == 422
            and refused.json()["code"] == "ADMISSION_REJECTED"
        ), refused.text
        assert any(d["code"] == "RESOURCE_BUSY" for d in refused.json()["diagnostics"])
        assert recorded.ledger(data) == counts
        previous = None
        deadline = time.monotonic() + 540
        while time.monotonic() < deadline:
            run = native.checked(api.get(route))
            phase = run["state"], run.get("runtimeStatus", {}).get("phase")
            if phase != previous:
                print("AUTOVERSE_FROZEN_RERUN", rid, phase, flush=True)
                previous = phase
            if run["state"] == "running":
                break
            assert run["state"] not in {"failed", "stopped", "unknown"}, run
            time.sleep(0.5)
        assert (
            run["state"] == "running"
            and run["runtimeStatus"]["components"]["android"] == "booted_apk_started"
        )
        lease = native.checked(api.post(route + "/input/acquire", json={}))
        lease = {k: lease[k] for k in ("leaseToken", "generation")}
        speed_seen, sequence = False, 0
        while run["state"] == "running" and time.monotonic() < deadline:
            sequence += 1
            response = api.post(
                route + "/input/frame",
                json={
                    **lease,
                    "frame": {
                        "sequence": sequence,
                        "throttle": 0 if speed_seen else 0.5,
                        "brake": 1 if speed_seen else 0,
                        "steer": 0,
                    },
                },
            )
            run = native.checked(api.get(route))
            if response.status_code != 200:
                assert response.status_code == 409 and run["state"] in {
                    "stopping",
                    "stopped",
                }, response.text
                break
            speed = run.get("inputTelemetry", {}).get("items", {}).get("speed", {})
            if (
                speed.get("status") == "observed"
                and isinstance(speed.get("value"), (int, float))
                and speed["value"] > 0.1
            ):
                speed_seen = True
            if run["state"] != "running":
                break
            worker.verify()
            assert new_path.read_bytes() == new_bytes
            time.sleep(0.1)
        assert speed_seen, "Fresh historical rerun did not demonstrate vehicle speed"
        final = native.wait(
            lambda: native.checked(api.get(route)),
            lambda r: r["state"] in {"stopped", "failed"},
            timeout=120,
        )
        assert final["state"] == "stopped" and final["cleanup"] == "complete", final
        native.wait(worker.exited, bool, timeout=30)
        worker.close()
        worker = None
        report["cleanup"] = native.verify_released(data, rid)
        assert (
            native.checked(
                api.post(source_route + "/reruns", headers=key, json={}), 202
            )
            == receipt
        )
        comparison = native.checked(
            api.post(
                "/api/v1/comparisons",
                json={"leftRunId": source_child["runId"], "rightRunId": rid},
            )
        )
        assert (
            comparison["compatible"] is False
            and comparison["rerunRequiresFreshAdmission"] is True
        )
        assert (
            comparison["left"]["snapshotId"] == frozen["snapshotId"]
            and comparison["right"]["snapshotId"] == new["snapshotId"]
        )
        rows = {r["field"]: r for r in comparison["configuration"]}
        assert (
            rows["parameters"]["status"] == "same"
            and rows["providerIdentity"]["status"] == "different"
        )
        assert "OBSERVATION_PAYLOAD_UNAVAILABLE" in comparison["diagnostics"]
        (args.output / "comparison.json").write_text(
            json.dumps(comparison, indent=2) + "\n"
        )
        assert (
            native.checked(api.get("/api/v1/projects/" + report["projectId"]))
            == project
        )
        assert new_path.read_bytes() == new_bytes
        report["after"] = recorded.ledger(data)
        expected = {
            **report["before"],
            "run": report["before"]["run"] + 1,
            "operation": report["before"]["operation"] + 2,
            "snapshot": report["before"]["snapshot"] + 1,
            "preflight": report["before"]["preflight"] + 1,
            "idempotency": report["before"]["idempotency"] + 2,
        }
        assert report["after"] == expected, (report["after"], expected)
        report.update(
            outcome="passed",
            fullAndroidAndSpeedObserved=True,
            currentDraftPreserved=True,
            recordedInspectionCreatesNothing=True,
            occupiedAdmissionRefused=True,
            exactRetryCreatesNothing=True,
        )
    finally:
        try:
            if api is not None and rid is not None:
                run = native.checked(api.get("/api/v1/runs/" + rid))
                if run["state"] in {"preparing", "running", "ready", "paused"}:
                    native.checked(
                        api.post(
                            f"/api/v1/runs/{rid}/commands",
                            headers={
                                "Idempotency-Key": "failed-frozen-rerun-owned-stop"
                            },
                            json={
                                "kind": "stop",
                                "expectedStateVersion": run["stateVersion"],
                                "parameters": {},
                            },
                        ),
                        202,
                    )
                    native.wait(
                        lambda: native.checked(api.get("/api/v1/runs/" + rid)),
                        lambda r: r["state"] in {"stopped", "failed"},
                        timeout=120,
                    )
        finally:
            if api is not None:
                api.close()
            host.stop()
            if worker is not None:
                if not worker.exited():
                    worker.send(signal.SIGTERM)
                    native.wait(worker.exited, bool, timeout=120)
                worker.close()
            with own_root(data):
                report["originalRootReleased"] = True
            report["backendShutdown"] = host.observations
            report["originalRecordingUnchanged"] = recorded.hashes(original) == before
            copied_after = recorded.hashes(data)
            report["copiedOriginalRecordingUnchanged"] = all(
                copied_after.get(k) == v for k, v in before.items()
            )
            (args.output / "native-result.json").write_text(
                json.dumps(report, indent=2) + "\n"
            )
    assert (
        report["outcome"] == "passed"
        and report["originalRecordingUnchanged"]
        and report["copiedOriginalRecordingUnchanged"]
    )


if __name__ == "__main__":
    main()
