"""Actual complete-demo campaign children; lifecycle/retry/restart and cleanup.

Only the explicitly enrolled isolated environment is operated. No source receipt,
worker or process owner is replaced. Backend crash uses its original native handle.
"""

import argparse
import importlib.util
import json
from pathlib import Path
import sys
import signal
import time
import uuid

from ruamel.yaml import YAML
from xverse_studio.xdl.examples import dump_yaml
from xverse_studio.blueprints.autoverse import NAMESPACE
from xverse_studio.evidence.reader import read_journal
from xverse_studio.host.ownership import own_root
from xverse_studio.security.managed_io import create_directory
from xverse_studio.storage.core import digest

spec = importlib.util.spec_from_file_location(
    "campaign_native_host",
    Path(__file__).with_name("autoverse_lifecycle_conformance.py"),
)
native = importlib.util.module_from_spec(spec)
spec.loader.exec_module(native)
ROOT = Path(__file__).resolve().parents[2]


def recorded_release(data, rid):
    """An earlier child may have a live successor using the same containers."""
    directory = data / "runs" / rid
    state = json.loads((directory / "state.json").read_bytes())
    processes = json.loads((directory / "resources.private.json").read_bytes())
    for entry in processes.values():
        try:
            process = native.psutil.Process(entry["pid"])
            assert (
                process.create_time() != entry["createTime"]
                or process.status() == native.psutil.STATUS_ZOMBIE
            )
        except native.psutil.NoSuchProcess:
            pass
    containers = json.loads((directory / "containers.private.json").read_bytes())
    records, integrity = read_journal(directory, state)
    assert integrity == "valid" and state["cleanup"] == "complete"
    terminal = [r for r in records if r["type"] == "run.state_changed"][-1]
    assert terminal["payload"]["cleanupResources"] == state["cleanupResources"]
    assert all(row["status"] == "released" for row in state["cleanupResources"])
    return {
        "originalProcessInstancesExited": len(processes),
        "recordedContainerReleases": len(containers),
        "terminalReleaseFactsMatchCanonicalJournal": True,
        "currentContainerObservation": "checked separately after the final child; a successor may already own them",
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--receipt", type=Path, required=True)
    parser.add_argument("--static-dir", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument(
        "--case", choices=["natural", "cancel", "restart"], default="natural"
    )
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=False)
    data = (
        ROOT / ".studio-local/browser-tests" / ("native-campaign-" + uuid.uuid4().hex)
    )
    with create_directory(Path("/"), data.absolute(), parents=True):
        pass
    (args.output / "data-root.private.json").write_text(
        json.dumps({"dataRoot": str(data)}) + "\n"
    )
    host = native.NativeHost(
        data,
        args.output,
        args.receipt.resolve(),
        Path(sys.executable),
        args.static_dir.resolve(),
    )
    report = {
        "scope": "actual complete native Autoverse campaign; no physical effects or applied seed",
        "case": args.case,
        "outcome": "failed",
        "children": [],
    }
    api, campaign_id, original_worker = None, None, None
    try:
        host.start()
        api = native.login(host)
        project, pf = native.author(api)
        base_bytes = (
            data / "snapshots" / pf["snapshotId"] / "snapshot.json"
        ).read_bytes()
        body = {
            "snapshotId": pf["snapshotId"],
            "matrix": {"durationSeconds": [30, 31]},
            "budget": {"maxRuns": 2, "maxTotalSeconds": 62},
            "concurrency": 1,
            "stopPolicy": "continue",
        }
        preview = native.checked(api.post("/api/v1/campaigns/preview", json=body))
        assert (
            preview["cardinality"] == 2 and preview["baseInput"]["status"] == "verified"
        ), preview
        receipt = native.checked(
            api.post(
                "/api/v1/campaigns",
                headers={"Idempotency-Key": "native-autoverse-campaign"},
                json=body,
            ),
            202,
        )
        campaign_id = receipt["campaignId"]
        report.update(
            campaignId=campaign_id,
            projectId=project["projectId"],
            baseSnapshotId=pf["snapshotId"],
        )
        assert (
            native.checked(
                api.post(
                    "/api/v1/campaigns",
                    headers={"Idempotency-Key": "native-autoverse-campaign"},
                    json=body,
                ),
                202,
            )
            == receipt
        )
        scenario_id, document = next(
            (key, value)
            for key, value in project["documents"].items()
            if Path(value["path"]).name == "scenario.xdl.yaml"
        )
        newer = YAML(typ="safe").load(document["content"])
        newer["extensions"][NAMESPACE]["durationSeconds"] = 60
        project = native.checked(
            api.put(
                f"/api/v1/projects/{project['projectId']}/documents/{scenario_id}",
                headers={"If-Match": str(project["revision"])},
                json={"content": dump_yaml(newer)},
            )
        )
        report["newerDraftRevision"] = project["revision"]
        processed = set()
        restarted = False
        cancelled = False
        deadline = time.monotonic() + 1200
        while time.monotonic() < deadline:
            campaign = native.checked(api.get("/api/v1/campaigns/" + campaign_id))
            if campaign["status"] in {"complete", "cancelled"}:
                break
            active = next(
                (
                    c
                    for c in campaign["children"]
                    if c.get("runId") and c["runId"] not in processed
                ),
                None,
            )
            if active is None:
                assert not any(
                    c["state"] == "rejected" for c in campaign["children"]
                ), campaign
                time.sleep(0.3)
                continue
            rid = active["runId"]
            route = "/api/v1/runs/" + rid

            def owner():
                row = native.private_record(data, "run", rid)
                return (
                    row
                    if row.get("pid") and (data / "runs" / rid / "state.json").exists()
                    else None
                )

            row = native.wait(owner, bool, timeout=30)
            original_worker = native.OriginalProcess(
                row["pid"],
                row["createTime"],
                row["launchArgvDigest"],
                parent=host.child.pid,
            )
            frozen_path = data / "snapshots" / row["snapshotId"] / "snapshot.json"
            frozen_bytes = frozen_path.read_bytes()
            frozen = json.loads(frozen_bytes)
            assert (
                frozen["parentSnapshotId"] == pf["snapshotId"]
                and frozen["campaignId"] == campaign_id
                and frozen["campaignChildKey"] == active["childKey"]
            )
            assert (
                frozen["configuration"]["durationSeconds"]
                == active["parameters"]["durationSeconds"]
            )
            previous = None
            running_deadline = time.monotonic() + 540
            while time.monotonic() < running_deadline:
                run = native.checked(api.get(route))
                phase = (run["state"], run.get("runtimeStatus", {}).get("phase"))
                if phase != previous:
                    print("AUTOVERSE_CAMPAIGN", rid, phase, flush=True)
                    previous = phase
                if run["state"] == "running":
                    break
                assert run["state"] not in {"failed", "stopped", "unknown"}, run
                time.sleep(0.5)
            assert (
                run["state"] == "running"
                and run["runtimeStatus"]["components"]["android"]
                == "booted_apk_started"
            )
            assert run["inputTelemetry"]["items"]["speed"]["status"] == "observed"
            lease = native.checked(api.post(route + "/input/acquire", json={}))
            lease = {k: lease[k] for k in ["leaseToken", "generation"]}
            sequence = 0
            speed_seen = False
            drive_deadline = time.monotonic() + 45
            while run["state"] == "running" and time.monotonic() < drive_deadline:
                sequence += 1
                frame_response = api.post(
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

                if frame_response.status_code != 200:
                    observed = native.checked(api.get(route))
                    assert (
                        frame_response.status_code == 409
                        and frame_response.json()["code"] == "STATE_CONFLICT"
                        and observed["state"] in {"stopping", "stopped"}
                    ), frame_response.text
                    run = observed
                    break
                run = native.checked(api.get(route))
                item = run.get("inputTelemetry", {}).get("items", {}).get("speed", {})
                if (
                    item.get("status") == "observed"
                    and isinstance(item.get("value"), (int, float))
                    and item["value"] > 0.1
                ):
                    speed_seen = True
                if run["state"] != "running":
                    break
                original_worker.verify()
                assert frozen_path.read_bytes() == frozen_bytes
                if speed_seen and args.case == "restart" and not restarted:
                    host.stop(crash=True)
                    original_worker.verify()
                    host.start()
                    api.close()
                    api = native.login(host)
                    original_worker.verify()
                    restarted = True
                    assert native.checked(api.get(route))["runId"] == rid
                    lease = native.checked(api.post(route + "/input/acquire", json={}))
                    lease = {k: lease[k] for k in ["leaseToken", "generation"]}
                    sequence = 0
                if speed_seen and args.case == "cancel" and not cancelled:
                    cancel = native.checked(
                        api.post(
                            "/api/v1/campaigns/" + campaign_id + "/cancel",
                            headers={"Idempotency-Key": "native-campaign-cancel"},
                            json={},
                        ),
                        202,
                    )
                    assert (
                        native.checked(
                            api.post(
                                "/api/v1/campaigns/" + campaign_id + "/cancel",
                                headers={"Idempotency-Key": "native-campaign-cancel"},
                                json={},
                            ),
                            202,
                        )
                        == cancel
                    )
                    cancelled = True
                    break
                if run["state"] != "running":
                    break
                time.sleep(0.1)
            assert speed_seen, "Complete-demo child never demonstrated vehicle speed"
            final = native.wait(
                lambda: native.checked(api.get(route)),
                lambda r: r["state"] in {"stopped", "failed"},
                timeout=120,
            )
            assert final["state"] == "stopped" and final["cleanup"] == "complete", final
            native.wait(original_worker.exited, bool, timeout=30)
            original_worker.close()
            original_worker = None
            cleanup = recorded_release(data, rid)
            journal, integrity = read_journal(
                data / "runs" / rid, native.private_record(data, "run", rid)
            )
            assert integrity == "valid"
            assert frozen_path.read_bytes() == frozen_bytes
            report["children"].append(
                {
                    "runId": rid,
                    "snapshotId": row["snapshotId"],
                    "parameters": active["parameters"],
                    "fullAndroidAndVehicleSpeedObserved": True,
                    "snapshotSha256": digest(frozen_bytes),
                    "canonicalIntegrity": integrity,
                    "canonicalRecords": len(journal),
                    "cleanup": cleanup,
                }
            )
            processed.add(rid)
        assert campaign["status"] == (
            "cancelled" if args.case == "cancel" else "complete"
        ), campaign
        report["finalContainerShutdown"] = native.verify_released(
            data, report["children"][-1]["runId"]
        )
        expected = 1 if args.case == "cancel" else 2
        assert len(processed) == expected
        assert [c["state"] for c in campaign["children"]] == (
            ["stopped", "cancelled"]
            if args.case == "cancel"
            else ["stopped", "stopped"]
        )
        assert (
            len(
                native.checked(
                    api.get("/api/v1/runs?projectId=" + project["projectId"])
                )["items"]
            )
            == expected
        )
        assert (
            native.checked(
                api.post(
                    "/api/v1/campaigns",
                    headers={"Idempotency-Key": "native-autoverse-campaign"},
                    json=body,
                ),
                202,
            )
            == receipt
        )
        assert (
            native.checked(api.get("/api/v1/projects/" + project["projectId"]))
            == project
        )
        assert (
            data / "snapshots" / pf["snapshotId"] / "snapshot.json"
        ).read_bytes() == base_bytes
        report.update(
            outcome="passed",
            finalCampaign=campaign,
            originalBaseUnchanged=True,
            newerDraftPreserved=True,
            restartVerified=restarted,
            cancelVerified=cancelled,
        )
    finally:
        try:
            if api is not None:
                if campaign_id is not None:
                    current = native.checked(
                        api.get("/api/v1/campaigns/" + campaign_id)
                    )
                    if current["status"] not in {"complete", "cancelled"}:
                        native.checked(
                            api.post(
                                "/api/v1/campaigns/" + campaign_id + "/cancel",
                                headers={"Idempotency-Key": "failed-case-cancel"},
                                json={},
                            ),
                            202,
                        )
                        native.wait(
                            lambda: native.checked(
                                api.get("/api/v1/campaigns/" + campaign_id)
                            ),
                            lambda c: c["status"] in {"complete", "cancelled"},
                            timeout=120,
                        )
                api.close()
        finally:
            host.stop()
            if original_worker is not None:
                if not original_worker.exited():
                    original_worker.send(signal.SIGTERM)
                    native.wait(original_worker.exited, bool, timeout=120)
                original_worker.close()
            with own_root(data):
                report["originalRootReleased"] = True
            report["backendShutdown"] = host.observations
            (args.output / "native-result.json").write_text(
                json.dumps(report, indent=2) + "\n"
            )
    assert report["outcome"] == "passed"


if __name__ == "__main__":
    main()
