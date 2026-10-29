"""Owned external Zenoh transport around the actual native C++ FIFO bridge.

Run with the enrolled component Python. Parent-only stdio supplies frozen host
configuration. No project command, dynamic import or remote endpoint is accepted.
The bridge publishes only after the native receive returns identical bytes.
"""
import argparse
import hashlib
import json
import os
import queue
import re
import select
import signal
import stat
import subprocess
import sys
import threading
import time

from native_signals import SIGNALS

MAX_MESSAGE = 65536
ENDPOINT = re.compile(r"tcp/127\.0\.0\.1:([1-9][0-9]{0,4})\Z")


class BridgeError(ValueError):
    pass


def encode(value):
    return (json.dumps(value, separators=(",", ":"), allow_nan=False) + "\n").encode()


def unique(pairs):
    value = {}
    for key, item in pairs:
        if key in value:
            raise BridgeError("NATIVE_DUPLICATE_KEY")
        value[key] = item
    return value


def read_line(fd, pending, deadline):
    while b"\n" not in pending:
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            raise BridgeError("NATIVE_REPLY_TIMEOUT")
        readable, _, _ = select.select([fd], [], [], remaining)
        if not readable:
            continue
        part = os.read(fd, 8192)
        if not part:
            raise BridgeError("NATIVE_PIPE_CLOSED")
        pending.extend(part)
        if len(pending) > MAX_MESSAGE:
            raise BridgeError("NATIVE_MESSAGE_LIMIT")
    line, _, rest = pending.partition(b"\n")
    pending[:] = rest
    return json.loads(line, object_pairs_hook=unique)


def write_all(fd, raw, deadline):
    if len(raw) > MAX_MESSAGE:
        raise BridgeError("NATIVE_MESSAGE_LIMIT")
    offset = 0
    while offset < len(raw):
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            raise BridgeError("NATIVE_INPUT_BACKPRESSURE")
        _, writable, _ = select.select([], [fd], [], remaining)
        if writable:
            try:
                offset += os.write(fd, raw[offset:offset + 8192])
            except BlockingIOError:
                pass


class NativeRPC:
    """Original child + pidfd; no signals reconstructed from a saved process ID."""
    def __init__(self, binary, expected_digest, config):
        descriptor = os.open(binary, os.O_RDONLY | os.O_NOFOLLOW)
        self.child, self.pidfd = None, None
        self.pending, self.sequence = bytearray(), 0
        try:
            before = os.fstat(descriptor)
            if not stat.S_ISREG(before.st_mode) or before.st_mode & 0o022 or before.st_size > 64 * 1024 * 1024:
                raise BridgeError("NATIVE_BINARY_INVALID")
            hasher = hashlib.sha256()
            while True:
                data = os.read(descriptor, 1024 * 1024)
                if not data:
                    break
                hasher.update(data)
            after = os.fstat(descriptor)
            if ("sha256:" + hasher.hexdigest() != expected_digest
                    or (before.st_ino, before.st_size, before.st_mtime_ns) != (after.st_ino, after.st_size, after.st_mtime_ns)):
                raise BridgeError("NATIVE_BINARY_CHANGED")
            # Execute the exact inspected open inode. The parent selects this
            # installed binary; imported content never supplies argv.
            self.child = subprocess.Popen([binary], executable="/proc/self/fd/" + str(descriptor),
                pass_fds=(descriptor,), stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                stderr=subprocess.DEVNULL, env={"LANG": "C"}, close_fds=True)
            self.pidfd = os.pidfd_open(self.child.pid)
            os.set_blocking(self.child.stdin.fileno(), False)
            os.set_blocking(self.child.stdout.fileno(), False)
            deadline = time.monotonic() + 3
            write_all(self.child.stdin.fileno(), encode(config), deadline)
            ready = read_line(self.child.stdout.fileno(), self.pending, deadline)
            if (ready.get("kind") != "ready" or ready.get("runId") != config["identity"]["runId"]
                    or ready.get("routeCount") != len(config["routes"])):
                raise BridgeError("NATIVE_READY_MISMATCH")
            self.ready = ready
        except BaseException:
            self.close()
            raise
        finally:
            os.close(descriptor)

    def call(self, kind, **values):
        self.sequence += 1
        deadline = time.monotonic() + 1
        write_all(self.child.stdin.fileno(), encode({"kind": kind, "requestId": self.sequence, **values}), deadline)
        value = read_line(self.child.stdout.fileno(), self.pending, deadline)
        if value.get("requestId") != self.sequence:
            raise BridgeError("NATIVE_REPLY_IDENTITY")
        return value

    def close(self):
        if self.child is not None:
            if self.child.poll() is None:
                if self.pidfd is not None:
                    try:
                        signal.pidfd_send_signal(self.pidfd, signal.SIGTERM)
                    except ProcessLookupError:
                        pass  # Original pidfd already names an exited child.
                else:
                    # Failed pidfd acquisition cannot authorize a PID signal.
                    self.child.stdin.close()
                try:
                    self.child.wait(timeout=2)
                except subprocess.TimeoutExpired:
                    if self.pidfd is not None:
                        signal.pidfd_send_signal(self.pidfd, signal.SIGKILL)
                        self.child.wait(timeout=2)
                    else:
                        raise BridgeError("NATIVE_OWNERSHIP_UNCONFIRMED") from None
            for stream in (self.child.stdin, self.child.stdout):
                if stream and not stream.closed:
                    stream.close()
        if self.pidfd is not None:
            os.close(self.pidfd)
            self.pidfd = None


def validate(config):
    if set(config) != {"native", "transports", "endpoints", "binarySha256", "maxRuntimeSeconds"}:
        raise BridgeError("NATIVE_CONFIGURATION_INVALID")
    if (type(config["maxRuntimeSeconds"]) is not int or not 1 <= config["maxRuntimeSeconds"] <= 3600
            or not re.fullmatch(r"sha256:[0-9a-f]{64}", config["binarySha256"])):
        raise BridgeError("NATIVE_CONFIGURATION_INVALID")
    endpoints = config["endpoints"]
    if set(endpoints) != {"outside", "vcu"} or endpoints["outside"] == endpoints["vcu"]:
        raise BridgeError("NATIVE_ENDPOINT_INVALID")
    for endpoint in endpoints.values():
        match = ENDPOINT.fullmatch(endpoint)
        if match is None or int(match[1]) > 65535:
            raise BridgeError("NATIVE_ENDPOINT_INVALID")
    transports = config["transports"]
    if len(transports) != len(SIGNALS) or len(config["native"]["routes"]) != len(SIGNALS):
        raise BridgeError("NATIVE_ROUTES_INVALID")
    for route, (name, topic, direction) in zip(transports, SIGNALS, strict=True):
        if route["topic"] != topic or route["direction"] != direction or route["flowId"] != name + "-flow":
            raise BridgeError("NATIVE_ROUTES_INVALID")


def run(binary):
    import zenoh  # Enrolled public component SDK; opening is explicit below.

    stdin, stdout = sys.stdin.fileno(), sys.stdout.fileno()
    os.set_blocking(stdin, False)
    os.set_blocking(stdout, False)
    parent_pending, output = bytearray(), bytearray()
    config = read_line(stdin, parent_pending, time.monotonic() + 5)
    validate(config)
    native = None
    incoming = queue.Queue(maxsize=128)
    sessions, subscribers, publishers = {}, [], []
    fault, lock = [], threading.RLock()
    accepting = True
    published = [0] * len(SIGNALS)
    stop = False
    quiesced = False
    last_parent_request = 0
    blocked_since = None
    previous_handlers = {}

    def faulted(code):
        with lock:
            if not fault:
                fault.append(code)

    def emitted(value):
        raw = encode(value)
        if len(output) + len(raw) > MAX_MESSAGE:
            raise BridgeError("NATIVE_PARENT_BACKPRESSURE")
        output.extend(raw)

    def signal_stop(*_args):
        nonlocal stop
        stop = True

    def forward(route, payload):
        reply = native.call("ingress", route=route, payloadHex=payload.hex())
        if reply.get("kind") != "delivered" or reply.get("route") != route or reply.get("payloadHex") != payload.hex():
            raise BridgeError("NATIVE_DELIVERY_MISMATCH")
        publishers[route].put(payload)
        published[route] += 1  # Public put returned; downstream consumption unknown.

    try:
        for kind in (signal.SIGTERM, signal.SIGINT):
            previous_handlers[kind] = signal.signal(kind, signal_stop)
        native = NativeRPC(binary, config["binarySha256"], config["native"])
        for side, endpoint in config["endpoints"].items():
            if stop:
                raise BridgeError("NATIVE_PARENT_STOP_OR_DEADLINE")
            options = zenoh.Config()
            for key, value in {"mode": "client", "connect/endpoints": [endpoint],
                "connect/timeout_ms": 3000, "connect/exit_on_failure": True, "listen/endpoints": [],
                "scouting/multicast/enabled": False, "scouting/gossip/enabled": False}.items():
                options.insert_json5(key, json.dumps(value))
            sessions[side] = zenoh.open(options)
        for index, (_, topic, direction) in enumerate(SIGNALS):
            source, destination = ("outside", "vcu") if direction == "to-vcu" else ("vcu", "outside")
            publishers.append(sessions[destination].declare_publisher(topic, congestion_control=zenoh.CongestionControl.DROP))
            def received(sample, route=index, expected_topic=topic):
                try:
                    with lock:
                        if not accepting:
                            return  # Beyond the explicit transport admission cutoff.
                        if sample.kind != zenoh.SampleKind.PUT or str(sample.key_expr) != expected_topic or len(sample.payload) > 128:
                            faulted("NATIVE_SAMPLE_UNSUPPORTED")
                            return
                        incoming.put_nowait((route, bytes(sample.payload)))
                except queue.Full:
                    faulted("NATIVE_INGRESS_BACKPRESSURE")
                except Exception:
                    faulted("NATIVE_INGRESS_UNAVAILABLE")
            subscribers.append(sessions[source].declare_subscriber(topic, received))
        emitted({**native.ready, "authority": "parent-owned-stdio", "publication": "separate-public-put-receipt",
                 "downstreamConsumption": "unacknowledged"})
        deadline = time.monotonic() + config["maxRuntimeSeconds"]
        while True:
            if fault:
                raise BridgeError(fault[0])
            if stop or time.monotonic() >= deadline:
                raise BridgeError("NATIVE_PARENT_STOP_OR_DEADLINE")
            readable, writable, _ = select.select([stdin] if not quiesced else [], [stdout] if output else [], [],
                                                   0 if not incoming.empty() or parent_pending else .02)
            if writable:
                try:
                    count = os.write(stdout, output[:16384])
                    del output[:count]
                    blocked_since = None
                except BlockingIOError:
                    pass
            if output:
                blocked_since = time.monotonic() if blocked_since is None else blocked_since
                if time.monotonic() - blocked_since > 1:
                    raise BridgeError("NATIVE_PARENT_BACKPRESSURE")
            if quiesced and not output:
                return 0
            if readable:
                data = os.read(stdin, 8192)
                if not data:
                    raise BridgeError("NATIVE_PARENT_LOST")
                parent_pending.extend(data)
                if len(parent_pending) > MAX_MESSAGE:
                    raise BridgeError("NATIVE_PARENT_LIMIT")
            if b"\n" in parent_pending:
                line, _, rest = parent_pending.partition(b"\n")
                parent_pending[:] = rest
                command = json.loads(line, object_pairs_hook=unique)
                if (set(command) != {"kind", "requestId"} or type(command["requestId"]) is not int
                        or command["requestId"] != last_parent_request + 1
                        or command["kind"] not in ("collect", "quiesce")):
                    raise BridgeError("NATIVE_PARENT_COMMAND_INVALID")
                last_parent_request = command["requestId"]
                if command["kind"] == "quiesce":
                    with lock:
                        accepting = False
                    for subscriber in subscribers:
                        subscriber.undeclare()
                    subscribers.clear()
                    drain_deadline = time.monotonic() + 2
                    while not incoming.empty():
                        if time.monotonic() >= drain_deadline:
                            raise BridgeError("NATIVE_INGRESS_DRAIN_TIMEOUT")
                        forward(*incoming.get_nowait())
                    reply = native.call("stop")
                    if reply.get("routesReleased") is not True:
                        raise BridgeError("NATIVE_CLOSE_UNCONFIRMED")
                    native.child.wait(timeout=2)
                    if native.child.returncode != 0:
                        raise BridgeError("NATIVE_EXIT_FAILED")
                    quiesced = True
                else:
                    reply = native.call("collect")
                emitted({**reply, "nativeRequestId": reply["requestId"], "requestId": last_parent_request,
                         "quiesced": quiesced, "published": list(published), "pendingIngress": incoming.qsize()})
            if not quiesced:
                try:
                    forward(*incoming.get_nowait())
                except queue.Empty:
                    pass
    finally:
        # Continue closing every owned object even if an SDK close fails.
        for resource in [*subscribers, *publishers]:
            try:
                resource.undeclare()
            except Exception:
                pass
        for session in sessions.values():
            try:
                session.close()
            except Exception:
                pass
        try:
            if native is not None:
                native.close()
        finally:
            for kind, prior in previous_handlers.items():
                signal.signal(kind, prior)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--native", required=True)
    args = parser.parse_args()
    try:
        return run(args.native)
    except Exception as error:
        # Fixed diagnostic only; no payload, token, endpoint config or paths.
        code = str(error) if isinstance(error, BridgeError) else "NATIVE_TRANSPORT_FAILED"
        sys.stderr.write(code + "\n")
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
