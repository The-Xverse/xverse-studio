"""Actual isolated Zenoh/native-X-COM exchange; not full Autoverse acceptance.

Explicit host-run test using the enrolled component Python. Owns two ephemeral
loopback routers, the transport and its native child, and public Zenoh peers.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import queue
import select
import shutil
import socket
import subprocess
import sys
import time

import psutil
import zenoh


def wait_line(process, deadline):
    while time.monotonic() < deadline:
        if process.poll() is not None:
            raise RuntimeError("Owned transport exited: " + str(process.returncode))
        readable, _, _ = select.select([process.stdout], [], [], .1)
        if readable:
            line = process.stdout.readline(65537)
            if not line or len(line) > 65536:
                raise RuntimeError("Invalid owned transport output")
            return json.loads(line)
    raise RuntimeError("Owned transport response timed out")


def free_port():
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        return sock.getsockname()[1]


def session(port):
    config = zenoh.Config()
    for key, value in {"mode": "client", "connect/endpoints": ["tcp/127.0.0.1:" + str(port)],
        "connect/timeout_ms": 3000, "connect/exit_on_failure": True, "listen/endpoints": [],
        "scouting/multicast/enabled": False, "scouting/gossip/enabled": False}.items():
        config.insert_json5(key, json.dumps(value))
    return zenoh.open(config)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--native", required=True, type=Path)
    parser.add_argument("--configuration", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=False)
    root = Path(__file__).resolve().parents[2]
    transport = root / "services/studio-api/src/xverse_studio/providers/autoverse/native_transport.py"
    native = args.native.resolve(strict=True)
    frozen = json.loads(args.configuration.read_bytes())
    outside_port, vcu_port = free_port(), free_port()
    while outside_port == vcu_port:
        vcu_port = free_port()
    digest = "sha256:" + hashlib.sha256(native.read_bytes()).hexdigest()
    config = {"native": frozen["native"], "transports": frozen["transports"],
              "endpoints": {"outside": "tcp/127.0.0.1:" + str(outside_port), "vcu": "tcp/127.0.0.1:" + str(vcu_port)},
              "binarySha256": digest, "maxRuntimeSeconds": 30}
    (args.output / "configuration.private.json").write_text(json.dumps(config, indent=2))
    children, sessions, handles, logs, native_children = [], [], [], [], []
    try:
        for name, port in (("outside", outside_port), ("vcu", vcu_port)):
            out = (args.output / (name + ".log")).open("wb")
            logs.append(out)
            child = subprocess.Popen([shutil.which("zenohd"), "--listen", "tcp/127.0.0.1:" + str(port),
                "--no-multicast-scouting", "--cfg", "scouting/gossip/enabled:false"],
                stdin=subprocess.DEVNULL, stdout=out, stderr=subprocess.STDOUT, close_fds=True)
            children.append(child)
        deadline = time.monotonic() + 5
        while True:
            try:
                for port in (outside_port, vcu_port):
                    with socket.create_connection(("127.0.0.1", port), timeout=.1):
                        pass
                break
            except OSError:
                assert all(p.poll() is None for p in children)
                if time.monotonic() >= deadline:
                    raise
                time.sleep(.05)
        err = (args.output / "transport.stderr").open("wb")
        logs.append(err)
        child = subprocess.Popen([sys.executable, "-E", str(transport), "--native", str(native)],
            stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=err, close_fds=True)
        children.append(child)
        child.stdin.write((json.dumps(config) + "\n").encode())
        child.stdin.flush()
        ready = wait_line(child, time.monotonic() + 10)
        assert ready["kind"] == "ready" and ready["routeCount"] == 11
        native_children = psutil.Process(child.pid).children(recursive=True)
        assert len(native_children) == 1
        assert Path(native_children[0].cmdline()[0]).resolve() == native
        outside, vcu = session(outside_port), session(vcu_port)
        sessions.extend((outside, vcu))
        incoming, outgoing = queue.Queue(), queue.Queue()
        speed = outside.declare_publisher("vehicle/status/velocity_status", congestion_control=zenoh.CongestionControl.DROP)
        throttle = vcu.declare_publisher("vcu/control/throttle_cmd", congestion_control=zenoh.CongestionControl.DROP)
        brake = vcu.declare_publisher("vcu/control/brake_cmd", congestion_control=zenoh.CongestionControl.DROP)
        handles.extend((speed, throttle, brake,
            vcu.declare_subscriber("vehicle/status/velocity_status", lambda s: incoming.put(bytes(s.payload))),
            outside.declare_subscriber("vcu/control/throttle_cmd", lambda s: outgoing.put(bytes(s.payload)))))
        # Public best-effort transport has discovery latency; repeat a finite
        # harmless state value until actual matching receipt is observed.
        deadline = time.monotonic() + 5
        while incoming.empty() or outgoing.empty():
            speed.put(b"23.0")
            throttle.put(b"0.25")
            brake.put(b"0.0")
            if time.monotonic() >= deadline:
                raise RuntimeError("Actual cross-boundary receipt unavailable")
            time.sleep(.05)
        assert incoming.get(timeout=1) == b"23.0" and outgoing.get(timeout=1) == b"0.25"
        # Generate actual native coalescing rather than patching a counter.
        for _ in range(4):
            speed.put(b"24.0")
            throttle.put(b"0.5")
            brake.put(b"0.1")
            time.sleep(.05)
        child.stdin.write(b'{"kind":"collect","requestId":1}\n')
        child.stdin.flush()
        result = wait_line(child, time.monotonic() + 3)
        assert result["kind"] == "batch" and result["requestId"] == 1
        projection = json.loads(result["projectionJson"])
        assert len(projection["records"]) == 3
        assert all(r["counters"]["coalesced"] > 0 for r in projection["records"])
        assert all(i["upstreamCausationId"] is None for i in projection["extensions"]["io.xverse.native.inputs"])
        (args.output / "native-projection.json").write_text(result["projectionJson"])
        (args.output / "collection.json").write_text(json.dumps(result, indent=2))
        child.stdin.write(b'{"kind":"quiesce","requestId":2}\n')
        child.stdin.flush()
        stopped = wait_line(child, time.monotonic() + 4)
        assert stopped["quiesced"] is True and stopped["routesReleased"] is True
        child.wait(timeout=3)
        assert child.returncode == 0
        assert all(not native_child.is_running() for native_child in native_children)
        while not incoming.empty():
            incoming.get_nowait()
        speed.put(b"99.0")
        try:
            unexpected = incoming.get(timeout=.5)
            raise AssertionError("Traffic bypassed stopped native bridge: " + repr(unexpected))
        except queue.Empty:
            pass
        (args.output / "stop.json").write_text(json.dumps(stopped, indent=2))
        proof = {"scope": "actual isolated Zenoh/native-XCOM exchange; not full Autoverse acceptance",
                 "routeCount": 11, "observedRoutes": 3, "bidirectionalPayloadReceipt": True,
                 "stoppingBridgePreventsForwarding": True, "originalNativeCoalescingObserved": True,
                 "unknownUpstreamCausePreserved": True, "nativeBinarySha256": digest,
                 "python": sys.version, "pid": os.getpid(), "exitStatus": 0}
        (args.output / "result.json").write_text(json.dumps(proof, indent=2))
        print(json.dumps({k: v for k, v in proof.items() if k not in ("python", "pid")}))
        return 0
    finally:
        for handle in handles:
            handle.undeclare()
        for opened in sessions:
            opened.close()
        for child in reversed(children):
            if child.poll() is None:
                child.terminate()  # Original children owned by this isolated test.
                try:
                    child.wait(timeout=3)
                except subprocess.TimeoutExpired:
                    child.kill()
                    child.wait(timeout=3)
        for out in logs:
            out.close()


if __name__ == "__main__":
    raise SystemExit(main())
