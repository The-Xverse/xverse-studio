"""Complete native Autoverse: two recoveries and Stop during a third input loss."""

import argparse
import importlib.util
import json
from pathlib import Path
import signal
import sys
import time
import uuid

from ruamel.yaml import YAML
from xverse_studio.blueprints.autoverse import documents, NAMESPACE
from xverse_studio.evidence.reader import read_journal
from xverse_studio.host.ownership import own_root
from xverse_studio.security.managed_io import create_directory
from xverse_studio.storage.core import digest
from xverse_studio.xdl.examples import dump_yaml

ROOT = Path(__file__).resolve().parents[2]


def module(name, filename):
    spec = importlib.util.spec_from_file_location(
        name, Path(__file__).with_name(filename)
    )
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


native = module("input_loss_native_host", "autoverse_lifecycle_conformance.py")
source = module("input_loss_source_fragments", "autoverse_input_loss_sources.py")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--receipt", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--static-dir", type=Path, required=True)
    args = parser.parse_args()
    args.output.mkdir(parents=True)
    data = (
        ROOT
        / ".studio-local/browser-tests"
        / ("scheduled-input-loss-" + uuid.uuid4().hex)
    )
    with create_directory(Path("/"), data.absolute(), parents=True):
        pass
    (args.output / "data-root.private.json").write_text(
        json.dumps({"dataRoot": str(data)}) + "\n"
    )
    host = native.NativeHost(
        data,
        args.output,
        args.receipt.absolute(),
        Path(sys.executable),
        args.static_dir.absolute(),
    )
    api = None
    worker = None
    rid = None
    report = {
        "scope": "Complete actual native Autoverse with bounded browser-forwarding losses; bridge lease effects only",
        "outcome": "failed",
        "newPhysicalEffects": False,
    }
    try:
        host.start()
        api = native.login(host)
        p = native.checked(
            api.post(
                "/api/v1/projects",
                json={
                    "name": "Autoverse scheduled input loss",
                    "blueprintRef": "autoverse-classic",
                },
            ),
            201,
        )
        variant = documents("studio-browser")
        scenario = YAML(typ="safe").load(variant["scenario.xdl.yaml"])
        scenario["extensions"][NAMESPACE]["durationSeconds"] = 30
        scenario["spec"]["faults"] = [
            source.fault(scenario, "first-loss", 5, 3),
            source.fault(scenario, "second-loss", 13, 3),
            source.fault(scenario, "interrupted-loss", 21, 3),
        ]
        variant["scenario.xdl.yaml"] = dump_yaml(scenario)
        for key, doc in list(p["documents"].items()):
            raw = variant[Path(doc["path"]).name]
            if raw != doc["content"]:
                p = native.checked(
                    api.put(
                        f"/api/v1/projects/{p['projectId']}/documents/{key}",
                        headers={"If-Match": str(p["revision"])},
                        json={"content": raw},
                    )
                )
        pf = native.checked(
            api.post(
                f"/api/v1/projects/{p['projectId']}/preflights",
                json={"revision": p["revision"], "providerId": "autoverse.demo"},
            )
        )
        assert pf["status"] == "ready", pf
        payload = {k: pf[k] for k in ["preflightId", "snapshotId"]}
        receipt = native.checked(
            api.post(
                "/api/v1/runs",
                headers={"Idempotency-Key": "scheduled-loss-original-start"},
                json=payload,
            ),
            202,
        )
        assert (
            native.checked(
                api.post(
                    "/api/v1/runs",
                    headers={"Idempotency-Key": "scheduled-loss-original-start"},
                    json=payload,
                ),
                202,
            )
            == receipt
        )
        rid = receipt["runId"]
        route = "/api/v1/runs/" + rid

        def run():
            return native.checked(api.get(route))

        directory = data / "runs" / rid
        report.update(
            runId=rid, snapshotId=pf["snapshotId"], operationId=receipt["operationId"]
        )

        def capture():
            r = native.private_record(data, "run", rid)
            return r if r.get("pid") and (directory / "state.json").exists() else None

        r = native.wait(capture, bool, timeout=30)
        assert digest((directory / "owner.key").read_bytes()) == r["ownerDigest"]
        worker = native.OriginalProcess(
            r["pid"], r["createTime"], r["launchArgvDigest"], parent=host.child.pid
        )
        snapshot_file = data / "snapshots" / pf["snapshotId"] / "snapshot.json"
        snapshot_bytes = snapshot_file.read_bytes()
        report["originalWorkerPidfdCaptured"] = True
        previous = None
        deadline = time.monotonic() + 540
        while time.monotonic() < deadline:
            r = run()
            phase = (r["state"], r.get("runtimeStatus", {}).get("phase"))
            if phase != previous:
                print("AUTOVERSE_INPUT_LOSS", phase, flush=True)
                previous = phase
            if r["state"] == "running":
                break
            assert r["state"] not in {"failed", "stopped", "unknown"}, r
            time.sleep(0.5)
        assert (
            r["state"] == "running"
            and r["runtimeStatus"]["components"]["android"] == "booted_apk_started"
        )
        assert r["inputTelemetry"]["items"]["speed"]["status"] == "observed"
        owner = native.checked(api.post(route + "/input/acquire", json={}))
        owner = {k: owner[k] for k in ["leaseToken", "generation"]}
        sequence = 0
        staged = []
        observations = []
        stop_deadline = time.monotonic() + 26
        next_history = 0
        third_observed = False
        while time.monotonic() < stop_deadline:
            sequence += 1
            response = native.checked(
                api.post(
                    route + "/input/frame",
                    json={
                        **owner,
                        "frame": {
                            "sequence": sequence,
                            "throttle": 0,
                            "brake": 1,
                            "steer": 0,
                        },
                    },
                )
            )
            assert response["status"] == "staged"
            staged.append(response["publicationSequence"])
            if time.monotonic() >= next_history:
                r = run()
                assert r["state"] == "running", r
                worker.verify()
                assert snapshot_file.read_bytes() == snapshot_bytes
                native_state = json.loads((directory / "state.json").read_bytes())
                assert 0 <= time.time() - native_state["updatedAt"] < 1.0, (
                    "Worker heartbeat must survive continuous suppressed frames"
                )
                observations.append(
                    {
                        "driverLeaseActive": r["inputTelemetry"].get(
                            "driverLeaseActive"
                        ),
                        "lastPublishedSequence": r["inputTelemetry"].get(
                            "lastPublishedSequence"
                        ),
                    }
                )
                history = native.checked(
                    api.get(
                        route + "/history",
                        params={"type": "fault.activation_observed", "limit": 200},
                    )
                )
                third_observed = any(
                    v["payload"].get("faultId") == "interrupted-loss"
                    for v in history["items"]
                )
                next_history = time.monotonic() + 0.3
            if third_observed:
                break
            time.sleep(0.06)
        assert third_observed, (
            "Third real bridge lease-expiry observation not received before Stop"
        )
        assert any(v["driverLeaseActive"] is True for v in observations) and any(
            v["driverLeaseActive"] is False for v in observations
        )
        r = run()
        assert r["state"] == "running"
        stopped = native.checked(
            api.post(
                route + "/commands",
                headers={"Idempotency-Key": "scheduled-loss-original-stop"},
                json={"kind": "stop", "expectedStateVersion": r["stateVersion"]},
            ),
            202,
        )
        final = native.wait(
            run,
            lambda v: v["state"] == "stopped" and v["cleanup"] == "complete",
            timeout=90,
        )
        assert (
            native.checked(api.get("/api/v1/operations/" + stopped["operationId"]))[
                "status"
            ]
            == "completed"
        )
        native.wait(worker.exited, bool, timeout=90)
        report["cleanup"] = native.verify_released(data, rid)
        assert report["cleanup"]["exactStoppedContainers"] == 3
        assert snapshot_file.read_bytes() == snapshot_bytes
        records, integrity = read_journal(directory, final)
        assert integrity == "valid"
        faults = [v for v in records if v["type"].startswith("fault.")]
        report["faultEvents"] = faults
        for fid in ["first-loss", "second-loss"]:
            selected = [v for v in faults if v["payload"]["faultId"] == fid]
            assert [v["type"] for v in selected] == [
                "fault.activation_requested",
                "fault.activation_observed",
                "fault.recovery_requested",
                "fault.recovery_observed",
            ]
            activated, recovered = selected[1], selected[3]
            assert (
                activated["payload"]["suppressedFrames"] > 0
                and activated["payload"]["bridgeLeaseActive"] is False
            )
            assert (
                recovered["payload"]["bridgeLeaseActive"] is True
                and recovered["payload"]["publicationSequence"]
                > activated["payload"]["lastDroppedSequence"]
            )
            for v in selected:
                assert (
                    v["source"]["version"] == "0.2.0"
                    and v["sourceTime"]["clockDomain"] == "host-runtime"
                )
                assert (
                    v["payload"]["vehicleEffect"] == "not_attested"
                    and v["payload"]["effectScope"] == "driver-bridge-publication-lease"
                )
                due = (
                    v["payload"]["scheduledRecoveryTick"]
                    if "recovery" in v["type"]
                    else v["payload"]["scheduledActivationTick"]
                )
                assert int(v["sourceTime"]["tick"]) >= int(due)
        third = [v for v in faults if v["payload"]["faultId"] == "interrupted-loss"]
        assert [v["type"] for v in third] == [
            "fault.activation_requested",
            "fault.activation_observed",
            "fault.interrupted",
        ]
        assert (
            third[-1]["payload"]["activationObserved"] is True
            and third[-1]["payload"]["recoveryObserved"] is False
        )
        assert final["verdict"] is None
        report.update(
            outcome="passed",
            canonicalIntegrity=integrity,
            canonicalRecords=len(records),
            inputFramesStaged=len(staged),
            leaseObservations=observations,
            snapshotBytesUnchanged=True,
            fullAndroidAndSpeedObserved=True,
            stopDuringActiveFault=True,
        )
    finally:
        try:
            if (
                api is not None
                and rid is not None
                and worker is not None
                and not worker.exited()
            ):
                try:
                    r = run()
                    if r["state"] not in {"stopped", "failed"}:
                        api.post(
                            route + "/commands",
                            headers={"Idempotency-Key": "failure-cleanup-stop"},
                            json={
                                "kind": "stop",
                                "expectedStateVersion": r["stateVersion"],
                            },
                        )
                    native.wait(worker.exited, bool, timeout=90)
                except Exception:
                    pass
            host.stop()
            if worker is not None and not worker.exited():
                worker.send(signal.SIGTERM)
                native.wait(worker.exited, bool, timeout=90)
        finally:
            if api is not None:
                api.close()
            if worker is not None:
                report["originalWorkerExited"] = worker.exited()
                worker.close()
            with own_root(data):
                report["originalRootLockReleased"] = True
            report["nativeBackendObservations"] = host.observations
            (args.output / "native-result.json").write_text(
                json.dumps(report, indent=2) + "\n"
            )
    print(
        "Complete scheduled input-loss demo and exact native cleanup passed.",
        flush=True,
    )


if __name__ == "__main__":
    main()
