"""Owned stdio adapter for Autoverse's public Zenoh interfaces (Linux provider).

Run with the admitted component Python, not Studio's interpreter. The parent
owns both pipes. No project command, module, endpoint or signal path is loaded.
Bounded nonblocking output keeps a slow reader from stopping the driver watchdog.
"""
import argparse
import json
import os
import re
import select
import signal
import sys
import time

from controls import (
    ControlRejected, DRIVER_SIGNALS, DriverLease, LatestTelemetry,
    PROTOCOL_VERSION, TELEMETRY_SIGNALS, wire_messages,
)

MAX_INPUT_BYTES = 8192
MAX_OUTPUT_BYTES = 64 * 1024
CONTROL_RESERVE_BYTES = 8192
REQUEST_ID = re.compile(r"^[A-Za-z0-9-]{1,64}$")
ENDPOINT = re.compile(r"^tcp/127\.0\.0\.1:([1-9][0-9]{0,4})$")


def run(endpoint, duration, observe_only=False):
    import zenoh  # Existing admitted component dependency; no import opens a session.

    config = zenoh.Config()
    for key, value in {
        "mode": "client", "connect/endpoints": [endpoint], "connect/timeout_ms": 3000,
        "connect/exit_on_failure": True, "listen/endpoints": [],
        "scouting/multicast/enabled": False, "scouting/gossip/enabled": False,
    }.items():
        config.insert_json5(key, json.dumps(value))
    session = zenoh.open(config)
    telemetry, lease = LatestTelemetry(), DriverLease()
    publishers, subscribers = {}, []
    pending = bytearray()
    dropped = 0
    stopping = False
    input_buffer = bytearray()
    previous_handlers = {}

    def emit(value, priority=False):
        nonlocal dropped
        encoded = (json.dumps(value, separators=(",", ":"), allow_nan=False) + "\n").encode()
        limit = MAX_OUTPUT_BYTES if priority else MAX_OUTPUT_BYTES - CONTROL_RESERVE_BYTES
        if len(pending) + len(encoded) > limit:
            if priority:
                raise ControlRejected("CONTROL_OUTPUT_BACKPRESSURE")
            dropped = min(2**31-1, dropped+1)
            return
        pending.extend(encoded)

    def stop_requested(*_args):
        nonlocal stopping
        stopping = True

    def publish(frame, requests=False):
        for topic, payload in wire_messages(frame if requests else {key: value for key, value in frame.items() if key != "deltaSpeed"}, include_requests=True):
            publishers[topic].put(payload)

    try:
        for entry in ([] if observe_only else DRIVER_SIGNALS.values()):
            publishers[entry.topic] = session.declare_publisher(entry.topic, congestion_control=zenoh.CongestionControl.DROP)
        for entry in TELEMETRY_SIGNALS.values():
            def received(sample, topic=entry.topic):
                telemetry.receive(topic, bytes(sample.payload), time.monotonic())
            subscribers.append(session.declare_subscriber(entry.topic, received))
        for kind in (signal.SIGINT, signal.SIGTERM):
            previous_handlers[kind] = signal.signal(kind, stop_requested)
        stdin, stdout = sys.stdin.fileno(), sys.stdout.fileno()
        os.set_blocking(stdin, False)
        os.set_blocking(stdout, False)
        emit({"type": "ready", "protocolVersion": PROTOCOL_VERSION,
              "authority": "parent-owned-stdio", "physicalEffects": False, "inputMode": "observe-only" if observe_only else "driver"}, True)
        started = time.monotonic()
        next_publish = next_report = started
        blocked_since = None
        while not stopping and time.monotonic() - started < duration:
            now = time.monotonic()
            if now >= next_publish:
                requested = lease.requested(now)
                # Explicit requests are sent once at acceptance; continuous
                # analog values repeat at20Hz. Expiry requests cruise off.
                if not observe_only:
                    publish(requested["frame"], requests=not requested["active"])
                next_publish = now + .05
            if now >= next_report:
                emit({"type": "telemetry", "data": telemetry.snapshot(now),
                      "driverLeaseActive": lease.requested(now)["active"], "reportedAtMonotonic": now,
                      "droppedTelemetryReports": dropped})
                next_report = now + .2
            if len(pending) >= MAX_OUTPUT_BYTES - CONTROL_RESERVE_BYTES:
                blocked_since = now if blocked_since is None else blocked_since
                if now - blocked_since >= 1:
                    raise ControlRejected("CONTROL_OUTPUT_BACKPRESSURE")
            else:
                blocked_since = None
            wait = max(0, min(next_publish, next_report, started + duration) - time.monotonic())
            readable, writable, _ = select.select([stdin], [stdout] if pending else [], [], wait)
            if writable:
                try:
                    count = os.write(stdout, pending[:16384])
                    del pending[:count]
                except BlockingIOError:
                    pass
            if readable:
                chunk = os.read(stdin, 4096)
                if not chunk:
                    break
                input_buffer.extend(chunk)
                if len(input_buffer) > MAX_INPUT_BYTES:
                    raise ControlRejected("CONTROL_INPUT_LIMIT")
                while b"\n" in input_buffer and not stopping:
                    raw, _, rest = input_buffer.partition(b"\n")
                    input_buffer[:] = rest
                    request = None
                    try:
                        request = json.loads(raw)
                        if (not isinstance(request, dict) or not isinstance(request.get("id"), str)
                                or not REQUEST_ID.fullmatch(request["id"])):
                            raise ControlRejected("CONTROL_REQUEST_INVALID")
                        if request.get("type") == "stop" and set(request) == {"type", "id"}:
                            stopping = True
                            emit({"type": "stopping", "id": request["id"]}, True)
                        elif request.get("type") == "drive" and set(request) in ({"type", "id", "frame"}, {"type", "id", "frame", "issuedAt"}):
                            if observe_only:
                                raise ControlRejected("CONTROL_INPUT_NOT_SUPPORTED")
                            received_at = time.monotonic()
                            issued_at = request.get("issuedAt", received_at)
                            if type(issued_at) not in (int, float) or not 0 <= received_at - issued_at < .75:
                                raise ControlRejected("CONTROL_LEASE_EXPIRED")
                            result = lease.accept(request["frame"], issued_at)
                            if not result["duplicate"]:
                                publish(lease.requested(time.monotonic())["frame"], requests=True)
                            emit({"type": "input_accepted", "id": request["id"], **result,
                                  "effect": "publication_only_not_vehicle_acknowledgement"}, True)
                        else:
                            raise ControlRejected("CONTROL_REQUEST_UNSUPPORTED")
                    except (ValueError, UnicodeError) as exc:
                        emit({"type": "input_rejected", "id": request.get("id") if isinstance(request, dict) and isinstance(request.get("id"), str) and REQUEST_ID.fullmatch(request["id"]) else None,
                              "code": str(exc) if isinstance(exc, ControlRejected) else "CONTROL_JSON_INVALID"}, True)
    finally:
        # The receiving controller/vehicle remains responsible for actual effect.
        # Closing a pipe never creates an acknowledgement or a physical stop claim.
        try:
            if publishers:
                publish({"sequence": 0, "throttle": 0, "brake": 1, "steer": 0, "cruise": False}, requests=True)
        finally:
            for subscriber in subscribers:
                subscriber.undeclare()
            for publisher in publishers.values():
                publisher.undeclare()
            session.close()
            for kind, handler in previous_handlers.items():
                signal.signal(kind, handler)


def main():
    parser = argparse.ArgumentParser(description="Owned Autoverse stdio/Zenoh adapter")
    parser.add_argument("--endpoint", default="tcp/127.0.0.1:7447")
    parser.add_argument("--duration", type=int, default=1800)
    parser.add_argument("--observe-only", action="store_true")
    args = parser.parse_args()
    endpoint = ENDPOINT.fullmatch(args.endpoint)
    if endpoint is None or int(endpoint.group(1)) > 65535 or not 1 <= args.duration <= 1800:
        parser.error("Use an admitted loopback endpoint and duration between1 and1800 seconds.")
    try:
        run(args.endpoint, args.duration, args.observe_only)
        return 0
    except Exception as exc:
        # Do not copy dependency exceptions, credentials or installation paths
        # into this protocol. The owning worker records unconfirmed outcomes.
        diagnostic = str(exc) if isinstance(exc, ControlRejected) else type(exc).__name__
        os.write(sys.stderr.fileno(), ("AUTOVERSE_BRIDGE_FAILED: " + diagnostic + "\n").encode())
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
