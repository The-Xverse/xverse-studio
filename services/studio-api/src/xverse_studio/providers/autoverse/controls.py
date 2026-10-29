"""Closed browser-input/Zenoh boundary for the existing virtual vehicle demo.

This module uses only the standard library so the installed component interpreter
can use the same contract as Studio. It performs no network, device or process I/O.
Topics and wire formats match Autoverse's existing manual-control/VCU interfaces.
"""
from dataclasses import dataclass
import math
import threading

PROTOCOL_VERSION = "1.0"
MAX_DRIVER_LEASE_SECONDS = 0.75
MAX_INPUT_SEQUENCE = 2**53 - 1
MAX_PAYLOAD_BYTES = 256
TELEMETRY_STALE_SECONDS = 2.0


class ControlRejected(ValueError):
    pass


@dataclass(frozen=True)
class Signal:
    topic: str
    value_type: str
    minimum: float
    maximum: float
    unit: str


DRIVER_SIGNALS = {
    "throttle": Signal("vehicle/command/acc_pedal_sts", "number", 0, 1, "scalar"),
    "brake": Signal("vehicle/command/brake_pedal_sts", "number", 0, 1, "scalar"),
    "steer": Signal("vehicle/command/steer_sts", "number", -1, 1, "scalar"),
    "cruise": Signal("vehicle/control/cc_engage_req", "boolean", 0, 1, "N/A"),
    "reverse": Signal("vehicle/control/reverse_req", "boolean", 0, 1, "N/A"),
    "deltaSpeed": Signal("vehicle/control/delta_speed", "number", -20, 20, "km/h"),
}
TELEMETRY_SIGNALS = {
    "speed": Signal("vehicle/status/velocity_status", "number", 0, 260, "km/h"),
    "cruiseEngaged": Signal("vcu/control/cc_engage_sts", "boolean", 0, 1, "N/A"),
    "reverseEngaged": Signal("vcu/control/reverse_sts", "boolean", 0, 1, "N/A"),
    "brakeEngaged": Signal("vcu/control/brake_sts", "boolean", 0, 1, "N/A"),
    "vcuThrottleCommand": Signal("vcu/control/throttle_cmd", "number", -1, 1, "scalar"),
    "vcuBrakeCommand": Signal("vcu/control/brake_cmd", "number", 0, 1, "scalar"),
    "driverSteeringCommand": Signal("vehicle/command/steer_sts", "number", -1, 1, "scalar"),
    "cruiseTargetSpeed": Signal("adas/cruise_control/target_speed", "number", 0, 1000, "km/h"),
    "reportedElapsedSeconds": Signal("vehicle/status/clock_status", "number", 0, 1000000, "s"),
}
_BY_TOPIC = {signal.topic: (name, signal) for name, signal in TELEMETRY_SIGNALS.items()}


def _value(value, signal):
    if signal.value_type == "boolean":
        if type(value) is not bool:
            raise ControlRejected("CONTROL_BOOLEAN_REQUIRED")
        return value
    if (isinstance(value, bool) or not isinstance(value, (int, float))
            or not signal.minimum <= value <= signal.maximum or not math.isfinite(value)):
        raise ControlRejected("CONTROL_VALUE_OUT_OF_RANGE")
    return float(value)


def driver_frame(value):
    """Full analog state plus optional explicit requests, never toggle commands."""
    if not isinstance(value, dict) or set(value) - {"sequence", *DRIVER_SIGNALS} or not {"sequence", "throttle", "brake", "steer"} <= set(value):
        raise ControlRejected("CONTROL_FRAME_INVALID")
    sequence = value["sequence"]
    if type(sequence) is not int or not 0 <= sequence <= MAX_INPUT_SEQUENCE:
        raise ControlRejected("CONTROL_SEQUENCE_INVALID")
    result = {"sequence": sequence}
    for name, signal in DRIVER_SIGNALS.items():
        if name in value:
            result[name] = _value(value[name], signal)
    if result["throttle"] > 0 and result["brake"] > 0:
        raise ControlRejected("CONTROL_PEDAL_CONFLICT")
    return result


def wire_messages(frame, *, include_requests=True):
    """Serialization only; publication is not acknowledgement of an effect."""
    frame = driver_frame(frame)
    messages = []
    for name, signal in DRIVER_SIGNALS.items():
        if name not in frame or (not include_requests and name in {"cruise", "reverse", "deltaSpeed"}):
            continue
        value = frame[name]
        if name == "deltaSpeed" and value == 0:
            continue
        messages.append((signal.topic, (str(value).lower() if isinstance(value, bool) else str(value)).encode("ascii")))
    return messages


class DriverLease:
    """One already-authorized owner; the service separately authenticates/fences it.

    Same-frame retry does not renew a lease or reapply pulse requests. A fresh
    sequence is required for a heartbeat. Never infer received/applied vehicle
    state from these requested input values.
    """
    def __init__(self):
        self._frame = None
        self._desired = {}
        self._received = None

    def accept(self, value, now):
        frame = driver_frame(value)
        if not isinstance(now, (int, float)) or isinstance(now, bool) or not math.isfinite(now):
            raise ControlRejected("CONTROL_CLOCK_INVALID")
        if self._received is not None and now < self._received:
            raise ControlRejected("CONTROL_CLOCK_REVERSED")
        if self._frame is not None and frame["sequence"] <= self._frame["sequence"]:
            if frame == self._frame:
                return {"accepted": True, "duplicate": True, "sequence": frame["sequence"]}
            raise ControlRejected("CONTROL_SEQUENCE_CONFLICT")
        if self._received is None or now - self._received >= MAX_DRIVER_LEASE_SECONDS:
            self._desired = {key: value for key, value in self._desired.items() if key == "reverse"}
        self._desired.update({key: frame[key] for key in ("cruise", "reverse") if key in frame})
        if frame["brake"] > 0:
            self._desired["cruise"] = False
        self._frame, self._received = frame, now
        return {"accepted": True, "duplicate": False, "sequence": frame["sequence"]}

    def requested(self, now):
        known_clock = (isinstance(now, (int, float)) and not isinstance(now, bool) and math.isfinite(now)
                       and self._received is not None and now >= self._received)
        if known_clock and now - self._received < MAX_DRIVER_LEASE_SECONDS:
            return {"active": True, "frame": {**self._frame, **self._desired}}
        # This requests virtual braking and cruise disengagement only. Reverse
        # is not changed by expiry. Actual response requires live observations.
        return {"active": False, "frame": {"sequence": 0, "throttle": 0.0, "brake": 1.0, "steer": 0.0, "cruise": False}}


def decode_telemetry(topic, payload):
    if topic not in _BY_TOPIC or not isinstance(payload, bytes) or len(payload) > MAX_PAYLOAD_BYTES:
        raise ControlRejected("TELEMETRY_UNSUPPORTED")
    name, signal = _BY_TOPIC[topic]
    try:
        text = payload.decode("utf-8").strip()
        if signal.value_type == "boolean":
            if text.lower() not in {"true", "false", "1", "0", "on", "off"}:
                raise ValueError()
            value = text.lower() in {"true", "1", "on"}
        else:
            value = float(text)
        return name, _value(value, signal)
    except (ValueError, UnicodeError, OverflowError):
        raise ControlRejected("TELEMETRY_VALUE_INVALID") from None


class LatestTelemetry:
    """Bounded latest-value projection; silence/staleness never becomes zero."""
    def __init__(self):
        self._values = {}
        self._invalid = 0
        self._lock = threading.Lock()

    def receive(self, topic, payload, now):
        try:
            if isinstance(now, bool) or not isinstance(now, (int, float)) or not math.isfinite(now):
                raise ControlRejected("TELEMETRY_CLOCK_INVALID")
            name, value = decode_telemetry(topic, payload)
        except ControlRejected:
            with self._lock:
                self._invalid = min(2**31 - 1, self._invalid + 1)
            return False
        with self._lock:
            self._values[name] = value, now
        return True

    def snapshot(self, now):
        with self._lock:
            items = {}
            for name, signal in TELEMETRY_SIGNALS.items():
                sample = self._values.get(name)
                elapsed = now - sample[1] if sample and type(now) in (int, float) and math.isfinite(now) else None
                status = "unknown" if elapsed is None or elapsed < 0 else "stale" if elapsed >= TELEMETRY_STALE_SECONDS else "observed"
                items[name] = {**({"metadataConflict": "The installed publisher emits elapsed seconds; its signal metadata describes frame-delta milliseconds. No cross-clock mapping is inferred."} if name == "reportedElapsedSeconds" else {}), "value": sample[0] if status != "unknown" else None, "status": status,
                               "ageSeconds": elapsed if elapsed is not None and elapsed >= 0 else None,
                               "unit": signal.unit, "topic": signal.topic}
            return {"items": items, "invalidPayloads": self._invalid, "clock": "host_monotonic_receipt",
                    "simulationTime": None, "limitation": "Receipt freshness does not establish simulation-clock synchronization or command application."}
