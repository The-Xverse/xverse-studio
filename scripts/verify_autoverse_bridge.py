"""Explicit native Zenoh adapter check; not CARLA/S-CORE/demo acceptance.

The supplied component interpreter must already provide Eclipse Zenoh. The check
owns an isolated loopback router and two clients; it contacts no existing demo.
Telemetry test values are labelled fixtures, never vehicle observations.
"""
import argparse
import json
import os
from pathlib import Path
import subprocess
import sys


def native_check(router, bridge_path):
    import queue
    import socket
    import threading
    import time
    from importlib.metadata import version
    import zenoh

    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        port = sock.getsockname()[1]
    endpoint = f"tcp/127.0.0.1:{port}"
    env = dict(os.environ, RUST_LOG="error")
    env.pop("PYTHONPATH", None)
    daemon = subprocess.Popen([router, "--listen", endpoint, "--no-multicast-scouting",
                               "--cfg", "scouting/gossip/enabled:false"], env=env,
                              stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
    session, bridge, subscribers = None, None, []
    seen, lock = {}, threading.Lock()

    def wait_for(predicate, label, seconds=5):
        deadline = time.monotonic() + seconds
        while time.monotonic() < deadline:
            result = predicate()
            if result:
                return result
            time.sleep(.01)
        raise AssertionError(label)

    def values(topic):
        with lock:
            return list(seen.get(topic, []))

    try:
        def listening():
            if daemon.poll() is not None:
                raise AssertionError("Owned router exited before readiness")
            with socket.socket() as sock:
                sock.settimeout(.1)
                return sock.connect_ex(("127.0.0.1", port)) == 0
        wait_for(listening, "Owned router readiness")
        cfg = zenoh.Config()
        for key, value in {"mode": "client", "connect/endpoints": [endpoint], "connect/timeout_ms": 3000,
                           "connect/exit_on_failure": True, "listen/endpoints": [],
                           "scouting/multicast/enabled": False, "scouting/gossip/enabled": False}.items():
            cfg.insert_json5(key, json.dumps(value))
        session = zenoh.open(cfg)
        topics = ["vehicle/command/acc_pedal_sts", "vehicle/command/brake_pedal_sts",
                  "vehicle/command/steer_sts", "vehicle/control/cc_engage_req", "vehicle/control/delta_speed"]
        for topic in topics:
            def receive(sample, key=topic):
                with lock:
                    entries = seen.setdefault(key, [])
                    entries.append(bytes(sample.payload).decode())
                    del entries[:-64]
            subscribers.append(session.declare_subscriber(topic, receive))
        bridge = subprocess.Popen([sys.executable, "-E", bridge_path, "--endpoint", endpoint, "--duration", "15"],
                                  env=env, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        incoming = queue.Queue(maxsize=64)
        def read_output():
            for line in bridge.stdout:
                try:
                    incoming.put_nowait(json.loads(line))
                except Exception as error:
                    incoming.put_nowait({"type": "reader_error", "detail": type(error).__name__})
        threading.Thread(target=read_output, daemon=True).start()
        report = []
        def receive_until(predicate, label):
            def next_record():
                try:
                    row = incoming.get_nowait()
                except queue.Empty:
                    if bridge.poll() is not None:
                        raise AssertionError("Adapter exited before " + label)
                    return None
                report.append(row)
                return row if predicate(row) else None
            return wait_for(next_record, label)
        ready = receive_until(lambda row: row.get("type") == "ready", "Adapter readiness")
        assert ready["protocolVersion"] == "1.0" and ready["physicalEffects"] is False
        frame = {"sequence": 1, "throttle": .4, "brake": 0, "steer": -.3, "cruise": True, "deltaSpeed": 1}
        def send(request):
            bridge.stdin.write((json.dumps(request) + "\n").encode())
            bridge.stdin.flush()
        send({"type": "drive", "id": "first", "frame": frame})
        first = receive_until(lambda row: row.get("id") == "first", "Input receipt")
        assert first["type"] == "input_accepted" and first["duplicate"] is False
        assert first["effect"] == "publication_only_not_vehicle_acknowledgement"
        wait_for(lambda: "0.4" in values(topics[0]) and "-0.3" in values(topics[2])
                 and "true" in values(topics[3]) and "1.0" in values(topics[4]), "Actual Zenoh input messages")
        send({"type": "drive", "id": "retry", "frame": frame})
        retried = receive_until(lambda row: row.get("id") == "retry", "Same-frame receipt")
        assert retried["type"] == "input_accepted" and retried["duplicate"] is True
        wait_for(lambda: "1.0" in values(topics[1])[-2:] and values(topics[0])[-1:] == ["0.0"]
                 and values(topics[3])[-1:] == ["false"], "Actual expiry braking/cruise request")
        assert values(topics[4]) == ["1.0"]
        # These are explicit observer fixtures over the actual native transport.
        session.put("vehicle/status/velocity_status", "12.5")
        session.put("vcu/control/cc_engage_sts", "true")
        observed = receive_until(lambda row: row.get("type") == "telemetry"
                                  and row["data"]["items"]["speed"]["value"] == 12.5, "Fixture telemetry round trip")
        assert observed["data"]["simulationTime"] is None
        assert observed["data"]["items"]["speed"]["status"] == "observed"
        send({"type": "drive", "id": "bad", "frame": {**frame, "sequence": 2, "throttle": True}})
        rejected = receive_until(lambda row: row.get("id") == "bad", "Invalid input refusal")
        assert rejected["type"] == "input_rejected"
        send({"type": "stop", "id": "stop"})
        assert bridge.wait(timeout=5) == 0
        return {"outcome": "passed", "scope": "owned_isolated_loopback_native_zenoh_transport",
                "componentPython": sys.version.split()[0], "zenohPython": version("eclipse-zenoh"),
                "actualInputPublication": True, "sameFrameNoDeltaReplay": True,
                "leaseExpiryBrakingRequest": True, "invalidInputRejected": True,
                "telemetryValues": "explicit fixtures over actual transport", "actualVehicleEffect": False,
                "completeAutoverseDemo": False, "protocolRecords": len(report)}
    finally:
        if bridge and bridge.poll() is None:
            bridge.terminate()
            try: bridge.wait(timeout=5)
            except subprocess.TimeoutExpired: bridge.kill(); bridge.wait(timeout=5)
        for subscriber in subscribers:
            subscriber.undeclare()
        if session:
            session.close()
        if daemon.poll() is None:
            daemon.terminate()
            try: daemon.wait(timeout=5)
            except subprocess.TimeoutExpired: daemon.kill(); daemon.wait(timeout=5)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--python", type=Path)
    parser.add_argument("--router", required=True, type=Path)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--native-child", action="store_true", help=argparse.SUPPRESS)
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    if args.native_child:
        result = native_check(str(args.router.resolve()), str(root / "services/studio-api/src/xverse_studio/providers/autoverse/zenoh_bridge.py"))
    else:
        if args.python is None or args.output is None:
            parser.error("Provide the admitted component --python and a new --output receipt.")
        if args.output.exists():
            parser.error("Refusing to overwrite an existing verification receipt.")
        env = dict(os.environ); env.pop("PYTHONPATH", None)
        native = subprocess.run([str(args.python), "-E", str(Path(__file__).resolve()), "--router", str(args.router), "--native-child"],
                                capture_output=True, text=True, timeout=35, env=env)
        if native.returncode:
            args.output.parent.mkdir(parents=True, exist_ok=True)
            args.output.write_text(json.dumps({"outcome": "failed", "nativeExitCode": native.returncode,
                                              "scope": "owned native Zenoh transport only"}, indent=2)+"\n")
            sys.stderr.write(native.stderr)
            return native.returncode
        result = json.loads(native.stdout)
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(result, indent=2)+"\n")
    print(json.dumps(result))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
