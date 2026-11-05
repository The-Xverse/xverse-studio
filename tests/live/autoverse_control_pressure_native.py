"""Actual full Autoverse control under bounded, explicitly synthetic presentation load.

Only an explicitly reverified isolated installation is operated. Original source
recordings stay immutable. Generated history is inert; actual producer observations,
accepted controls and owned cleanup are verified separately through public APIs.
"""

import argparse
import importlib.util
import json
from pathlib import Path
import signal
import sys
import threading
import time
import uuid

import httpx

from xverse_studio.evidence.reader import read_journal
from xverse_studio.host.ownership import own_root
from xverse_studio.storage.core import digest


_spec = importlib.util.spec_from_file_location(
    "pressure_performance_tools", Path(__file__).with_name("autoverse_performance.py")
)
benchmark = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(benchmark)
native, recorded = benchmark.native, benchmark.recorded


def first_frame(lines):
    fields = {}
    for line in lines:
        if not line and "data" in fields:
            fields["data"] = json.loads(fields["data"])
            return fields
        key, separator, value = line.partition(":")
        if separator and key:
            fields[key] = value.lstrip(" ")
    raise AssertionError("No complete initial SSE frame")


class PresentationPressure:
    """Finite read-only HTTP clients; no injected route, provider or journal data."""

    def __init__(self, api, history, source_run, sibling_run, campaign, actual_run):
        self.url = str(api.base_url)
        self.cookies = dict(api.cookies)
        self.headers = {"Origin": self.url.rstrip("/"), "X-CSRF-Token": api.headers["X-CSRF-Token"]}
        self.history, self.source, self.sibling = history, source_run, sibling_run
        self.campaign, self.actual = campaign, actual_run
        self.release = threading.Event()
        self.disconnect_live = threading.Event()
        self.live_ready = threading.Event()
        self.static_ready = threading.Event()
        self.lock = threading.Lock()
        self.threads, self.errors, self.requests, self.slow = [], [], {}, []

    def client(self):
        return httpx.Client(base_url=self.url, cookies=self.cookies, headers=self.headers, timeout=30)

    def request_loop(self, kind):
        try:
            with self.client() as api:
                count, maximum = 0, 0
                while not self.release.is_set():
                    begin = time.monotonic()
                    if kind == "history":
                        body = native.checked(api.get(
                            f"/api/v1/runs/{self.history['runId']}/history",
                            params={"limit": 200, "type": "log.appended", "severity": "info"},
                        ))
                        assert body["integrity"] == "valid" and len(body["items"]) == 200
                        assert body["counts"]["totalRecords"] == 50000
                    elif kind == "comparison":
                        body = native.checked(api.post("/api/v1/comparisons", json={
                            "leftRunId": self.source, "rightRunId": self.sibling,
                        }))
                        assert body["compatible"] is False and body["rerunRequiresFreshAdmission"]
                    else:
                        body = native.checked(api.get("/api/v1/campaigns/" + self.campaign))
                        assert body["campaignId"] == self.campaign
                    maximum = max(maximum, time.monotonic() - begin)
                    count += 1
                    assert count <= 4096
                    with self.lock:
                        self.requests[kind] = {"count": count, "maximumSeconds": maximum}
                    self.release.wait(.05)
        except BaseException as error:
            with self.lock:
                self.errors.append({"client": kind, "error": type(error).__name__, "message": str(error)[:1000]})

    def paused_stream(self, run_id, ready, release, synthetic):
        try:
            with self.client() as api, api.stream(
                "GET", f"/api/v1/runs/{run_id}/events", params={"streamVersion": "1.1"}
            ) as response:
                assert response.status_code == 200
                lines = response.iter_lines()
                frame = first_frame(lines)
                if synthetic:
                    assert frame["event"] == "studio.stream_control"
                    assert frame["data"]["type"] == "stream.gap"
                    assert frame["data"]["firstMissingSequence"] == "1"
                    assert frame["data"]["lastMissingSequence"] == "49800"
                    assert frame["data"]["missingCount"] == 49800
                else:
                    assert frame["data"]["runId"] == self.actual
                began = time.monotonic()
                ready.set()
                assert release.wait(90), "Paused consumer exceeded its contributor deadline"
                with self.lock:
                    self.slow.append({"runId": run_id, "synthetic": synthetic,
                                      "pausedApplicationReadSeconds": time.monotonic() - began,
                                      "firstFrame": frame, "explicitlyDisconnected": True})
        except BaseException as error:
            with self.lock:
                self.errors.append({"client": "paused-stream", "error": type(error).__name__, "message": str(error)[:1000]})
            ready.set()

    def start(self):
        targets = [(self.request_loop, (kind,)) for kind in ["history", "comparison", "campaign"]]
        targets += [
            (self.paused_stream, (self.actual, self.live_ready, self.disconnect_live, False)),
            (self.paused_stream, (self.history["runId"], self.static_ready, self.release, True)),
        ]
        for function, args in targets:
            thread = threading.Thread(target=function, args=args, daemon=False)
            self.threads.append(thread)
            thread.start()
        assert self.live_ready.wait(30) and self.static_ready.wait(30)
        assert not self.errors, self.errors

    def stop(self):
        self.disconnect_live.set()
        self.release.set()
        for thread in self.threads:
            thread.join(timeout=35)
        assert all(not thread.is_alive() for thread in self.threads)

    def report(self):
        return {"requests": self.requests, "pausedConsumers": self.slow,
                "errors": self.errors, "allClientThreadsExited": all(not t.is_alive() for t in self.threads),
                "scope": "Synthetic50k source plus real live source; paused application reads do not assert a saturated TCP sender window."}


def main():
    parser = argparse.ArgumentParser()
    for name in ["recording", "receipt", "static-dir", "output"]:
        parser.add_argument("--" + name, type=Path, required=True)
    parser.add_argument("--control", choices=["stop", "cancel"], required=True)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=False)
    source_result = json.loads((args.recording / "native-result.json").read_bytes())
    assert source_result["outcome"] == "passed" and len(source_result["children"]) == 2
    source = source_result["children"][0]
    assert source["fullAndroidAndVehicleSpeedObserved"]
    original = Path(json.loads((args.recording / "data-root.private.json").read_bytes())["dataRoot"])
    original_hashes = benchmark.protected_files(original)
    original_database = digest((original / "studio.sqlite").read_bytes())
    data = native.ROOT / ".studio-local/browser-tests" / ("autoverse-pressure-" + uuid.uuid4().hex)
    benchmark.exchange.clone(original, data)
    from xverse_studio.projects.service import Projects
    from xverse_studio.storage.core import Store
    from xverse_studio.xdl import XDLAdapter

    with own_root(data):
        store = Store(data)
        history = benchmark.history_fixture(store, Projects(store, XDLAdapter()), source["runId"])
    synthetic = data / "runs" / history["runId"] / "evidence.jsonl"
    synthetic_digest = digest(synthetic.read_bytes())
    baseline = recorded.ledger(data)
    (args.output / "data-root.private.json").write_text(json.dumps({"dataRoot": str(data)}) + "\n")
    report = {"outcome": "failed", "control": args.control, "before": baseline,
              "scope": "Actual full rendered/sensor/Android Autoverse pipeline with accepted control under presentation pressure; no physical/deterministic/numeric mapping claim",
              "sourceRunId": source["runId"], "syntheticHistory": history}
    host = native.NativeHost(data, args.output, args.receipt.resolve(), Path(sys.executable), args.static_dir.resolve())
    api, worker, run_id, pressure = None, None, None, None
    try:
        host.start()
        api = native.login(host)
        accepted = native.checked(api.post(
            f"/api/v1/runs/{source['runId']}/reruns",
            headers={"Idempotency-Key": "pressure-fresh-rerun"}, json={},
        ), 202)
        operation = native.checked(api.get("/api/v1/operations/" + accepted["operationId"]))
        assert operation["status"] == "completed", operation
        run_id = operation["result"]["runId"]
        route = "/api/v1/runs/" + run_id
        row = native.wait(lambda: native.private_record(data, "run", run_id), lambda r: bool(r.get("pid")), timeout=30)
        worker = native.OriginalProcess(row["pid"], row["createTime"], row["launchArgvDigest"], parent=host.child.pid)
        frozen_path = data / "snapshots" / row["snapshotId"] / "snapshot.json"
        frozen_bytes = frozen_path.read_bytes()
        frozen = json.loads(frozen_bytes)
        original_frozen = json.loads((data / "snapshots" / source["snapshotId"] / "snapshot.json").read_bytes())
        assert all(frozen[k] == original_frozen[k] for k in ["documents", "selection", "configuration", "planDigest", "semanticDigest"])
        report.update(runId=run_id, snapshotId=row["snapshotId"], rerunOperationId=accepted["operationId"])
        previous = None
        deadline = time.monotonic() + 540
        while time.monotonic() < deadline:
            run = native.checked(api.get(route))
            phase = run["state"], run.get("runtimeStatus", {}).get("phase")
            if phase != previous:
                print("AUTOVERSE_CONTROL_PRESSURE", args.control, run_id, phase, flush=True)
                previous = phase
            if run["state"] == "running":
                break
            assert run["state"] not in {"failed", "stopped", "unknown"}, run
            time.sleep(.5)
        assert run["state"] == "running" and run["runtimeStatus"]["components"]["android"] == "booted_apk_started"
        lease = native.checked(api.post(route + "/input/acquire", json={}))
        lease = {k: lease[k] for k in ["leaseToken", "generation"]}
        sequence = 0

        def drive(throttle, brake):
            nonlocal sequence
            sequence += 1
            native.checked(api.post(route + "/input/frame", json={
                **lease, "frame": {"sequence": sequence, "throttle": throttle, "brake": brake, "steer": 0},
            }))
            return native.checked(api.get(route))

        speed_seen = False
        while time.monotonic() < deadline:
            run = drive(.5, 0)
            assert run["state"] == "running"
            speed = run.get("inputTelemetry", {}).get("items", {}).get("speed", {})
            if speed.get("status") == "observed" and isinstance(speed.get("value"), (int, float)) and speed["value"] > .1:
                speed_seen = True
                break
            time.sleep(.1)
        assert speed_seen
        pressure = PresentationPressure(api, history, source["runId"], source_result["children"][1]["runId"], source_result["campaignId"], run_id)
        native.checked(api.post(route + "/input/release", json=lease))
        setup_started = time.monotonic()
        pressure.start()
        # Preparing independent HTTP clients/first captures is not a driver
        # heartbeat. Acquire a new public lease for the measured active phase;
        # the original 0.75s expiry and safe fallback remain enforced.
        lease = native.checked(api.post(route + "/input/acquire", json={}))
        lease = {k: lease[k] for k in ["leaseToken", "generation"]}
        sequence = 0
        report["inputPreparation"] = {"leaseReleasedBeforeClientSetup": True,
                                      "setupSeconds": time.monotonic() - setup_started,
                                      "freshLeaseAcquiredAfterSetup": True, "unchangedLeaseSeconds": .75}
        journal = data / "runs" / run_id / "evidence.jsonl"
        initial = journal.read_bytes()
        ticks = [{"phase": "consumers_paused", "records": len(initial.splitlines())}]
        started = time.monotonic()
        disconnected = False
        while time.monotonic() - started < 6:
            run = drive(0, 1)
            assert run["state"] == "running", run
            worker.verify()
            assert journal.read_bytes().startswith(initial)
            if not disconnected and time.monotonic() - started >= 3:
                pressure.disconnect_live.set()
                disconnected = True
                ticks.append({"phase": "live_consumer_disconnected", "records": len(journal.read_bytes().splitlines())})
            time.sleep(.1)
        ticks.append({"phase": "before_control", "records": len(journal.read_bytes().splitlines())})
        assert len(ticks) == 3 and ticks[0]["records"] < ticks[1]["records"] < ticks[2]["records"], ticks
        assert not pressure.errors and all(pressure.requests.get(k, {}).get("count", 0) > 0 for k in ["history", "comparison", "campaign"])
        body = {"kind": args.control, "expectedStateVersion": run["stateVersion"], "parameters": {}}
        key = {"Idempotency-Key": "pressure-owned-" + args.control}
        begin = time.monotonic()
        command = native.checked(api.post(route + "/commands", headers=key, json=body), 202)
        acknowledgment_seconds = time.monotonic() - begin
        assert acknowledgment_seconds < 30  # Existing native client's request budget; not a new product SLA.
        assert native.checked(api.post(route + "/commands", headers=key, json=body), 202) == command
        final = native.wait(lambda: native.checked(api.get(route)), lambda r: r["state"] in {"stopped", "failed"}, timeout=120)
        cleanup_seconds = time.monotonic() - begin
        assert final["state"] == "stopped" and final["cleanup"] == "complete", final
        settled = native.checked(api.get("/api/v1/operations/" + command["operationId"]))
        assert settled["status"] == "completed", settled
        assert native.checked(api.post(route + "/commands", headers=key, json=body), 202) == command
        pressure.stop()
        assert not pressure.errors, pressure.errors
        report["pressure"] = pressure.report()
        report["controlResult"] = {"operationId": command["operationId"], "status": settled["status"],
                                   "acknowledgmentSeconds": acknowledgment_seconds, "acknowledgmentHarnessBudgetSeconds": 30,
                                   "terminalCleanupSeconds": cleanup_seconds, "terminalHarnessBudgetSeconds": 120,
                                   "exactRetryCreatesNothing": True, "producerProgress": ticks}
        native.wait(worker.exited, bool, timeout=30)
        worker.close()
        worker = None
        report["cleanup"] = native.verify_released(data, run_id)
        rows, integrity = read_journal(journal.parent, native.private_record(data, "run", run_id))
        assert integrity == "valid"
        # This provider's authenticated state carries control receipts; its
        # canonical journal independently records terminal state/resource facts.
        producer = json.loads((journal.parent / "state.json").read_bytes())
        assert producer["commandResults"][command["operationId"]]["status"] == "completed"
        assert settled["runId"] == run_id and settled["kind"] == args.control
        assert settled["expectedStateVersion"] == body["expectedStateVersion"]
        assert frozen_path.read_bytes() == frozen_bytes and digest(synthetic.read_bytes()) == synthetic_digest
        report["after"] = recorded.ledger(data)
        expected = {**baseline, "run": baseline["run"] + 1, "operation": baseline["operation"] + 3,
                    "snapshot": baseline["snapshot"] + 1, "preflight": baseline["preflight"] + 1,
                    "idempotency": baseline["idempotency"] + 3}
        assert report["after"] == expected, (report["after"], expected)
        report.update(outcome="passed", fullAndroidAndSpeedObserved=True, canonicalIntegrity=integrity,
                      canonicalRecords=len(rows), terminal={k: final.get(k) for k in ["state", "cleanup", "evidence", "reason", "verdict"]},
                      syntheticCanonicalBytesUnchanged=True, frozenInputsUnchanged=True)
    finally:
        try:
            if pressure is not None:
                pressure.stop()
                report["pressure"] = pressure.report()
            if api is not None and run_id is not None:
                state = native.checked(api.get("/api/v1/runs/" + run_id))
                if state["state"] in {"preparing", "running", "ready", "paused"}:
                    native.checked(api.post(f"/api/v1/runs/{run_id}/commands",
                                            headers={"Idempotency-Key": "pressure-failure-owned-stop"},
                                            json={"kind": "stop", "expectedStateVersion": state["stateVersion"]}), 202)
                    native.wait(lambda: native.checked(api.get("/api/v1/runs/" + run_id)), lambda r: r["state"] in {"stopped", "failed"}, timeout=120)
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
            report["originalRecordingUnchanged"] = benchmark.protected_files(original) == original_hashes and digest((original / "studio.sqlite").read_bytes()) == original_database
            copied = benchmark.protected_files(data)
            report["copiedOriginalRecordingUnchanged"] = all(copied.get(k) == v for k, v in original_hashes.items())
            report["backendShutdown"] = host.observations
            (args.output / "native-result.json").write_text(json.dumps(report, indent=2) + "\n")
    assert report["outcome"] == "passed" and report["originalRecordingUnchanged"] and report["copiedOriginalRecordingUnchanged"]
    print(json.dumps({"outcome": report["outcome"], "control": args.control, "controlResult": report["controlResult"]}))


if __name__ == "__main__":
    main()
