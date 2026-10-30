"""Classic Autoverse's closed browser-forwarding fault contract (ADR-0052).

The public XDL plan owns timing normalization. Runtime observations describe only
the original bridge's publication lease, never vehicle acknowledgement.
"""

from copy import deepcopy
import math

from xverse_studio.xdl.examples import PROFILE_NAMESPACE

CONTRACT = "urn:xverse:studio:autoverse:input-loss:1.0"
ACTIVATION, RECOVERY = CONTRACT + ":activation", CONTRACT + ":recovery"
CLOCK = "host-runtime"
CODEC = "autoverse.host-elapsed-microseconds.v1"
MAX_FAULTS = 8
DESCRIPTOR = {
    "contractRef": CONTRACT,
    "clockDomain": CLOCK,
    "clockCodec": CODEC,
    "tickUnit": "microsecond",
    "epoch": "actual-running-transition",
    "maxFaults": MAX_FAULTS,
    "minimumRecoveryGapSeconds": 2,
    "faults": [
        {
            "kind": "driver-input-loss",
            "target": "driver",
            "inputSurface": "studio-browser",
            "activation": ACTIVATION,
            "recovery": RECOVERY,
            "durationSeconds": {"minimum": 2, "maximum": 30},
            "effectScope": "driver-bridge-publication-lease",
            "physicalEffects": False,
        }
    ],
    "limitations": [
        "Suppression and bridge lease observations are separate from vehicle/controller effects.",
        "No simulation clock, native X-COM fault or deterministic replay is admitted.",
    ],
}


def compile_input_loss(scenario, compiled, duration_seconds, input_surface):
    faults = scenario["spec"]["faults"]
    if input_surface != "studio-browser" or not 1 <= len(faults) <= MAX_FAULTS:
        raise ValueError("Unsupported input-loss scope")
    planned = {f["faultId"]: f for f in compiled["plan"]["faultSchedule"]}
    if len(planned) != len(faults):
        raise ValueError("Unresolved fault plan")
    system = {**scenario["spec"]["systemRef"], "element": "driver"}
    owner = {
        "apiVersion": scenario["apiVersion"],
        "kind": "Scenario",
        **{k: scenario["metadata"][k] for k in ["namespace", "name"]},
    }
    result = []
    for fault in faults:
        if (
            set(fault)
            != {
                "id",
                "targetRef",
                "faultKind",
                "activation",
                "recovery",
                "maturity",
                "extensions",
            }
            or fault["targetRef"] != system
            or fault["faultKind"] != "driver-input-loss"
            or fault["activation"] != ACTIVATION
            or fault["recovery"] != RECOVERY
            or fault["maturity"] != "prototype"
            or set(fault["extensions"]) != {PROFILE_NAMESPACE}
        ):
            raise ValueError("Unsupported fault binding")
        intent = fault["extensions"][PROFILE_NAMESPACE]
        plan = planned[fault["id"]]
        if (
            set(intent)
            != {
                "schemaVersion",
                "kind",
                "target",
                "trigger",
                "duration",
                "timeDomainId",
            }
            or intent["schemaVersion"] != "0.1"
            or intent["kind"] != "fault-intent"
            or intent["target"] != {**owner, "element": fault["id"]}
            or set(intent["trigger"]) != {"kind", "at", "unit"}
            or intent["trigger"]["kind"] != "time"
            or set(intent["duration"]) != {"value", "unit"}
            or intent["trigger"]["unit"] not in {"s", "ms", "us", "ns"}
            or intent["duration"]["unit"] not in {"s", "ms", "us", "ns"}
            or intent["timeDomainId"] != CLOCK
            or plan["timeDomainId"] != CLOCK
            or plan["trigger"]["kind"] != "time"
        ):
            raise ValueError("Unsupported fault timing")
        start_ns, duration_ns = plan["trigger"]["atTicks"], plan["duration"]["ticks"]
        if (
            type(start_ns) is not int
            or type(duration_ns) is not int
            or start_ns % 1000
            or duration_ns % 1000
            or start_ns < 2_000_000_000
            or not 2_000_000_000 <= duration_ns <= 30_000_000_000
            or start_ns + duration_ns > (duration_seconds - 2) * 1_000_000_000
        ):
            raise ValueError("Fault timing exceeds bounds")
        result.append(
            {
                "faultId": fault["id"],
                "targetRef": deepcopy(system),
                "activationTick": str(start_ns // 1000),
                "recoveryTick": str((start_ns + duration_ns) // 1000),
                "planActivationTick": str(start_ns),
                "planDurationTick": str(duration_ns),
                "trigger": deepcopy(intent["trigger"]),
                "duration": deepcopy(intent["duration"]),
            }
        )
    result.sort(key=lambda f: (int(f["activationTick"]), f["faultId"]))
    if any(
        int(b["activationTick"]) < int(a["recoveryTick"]) + 2_000_000
        for a, b in zip(result, result[1:])
    ):
        raise ValueError("Overlapping/adjacent fault intervals are not admitted")
    return {
        "contractRef": CONTRACT,
        "clockDomain": CLOCK,
        "clockCodec": CODEC,
        "tickUnit": "microsecond",
        "schedules": result,
    }


class InputLoss:
    """Bounded state driven by actual parent/bridge monotonic observations."""

    def __init__(self, configuration, origin_ns, emit):
        self.origin_ns, self.emit = origin_ns, emit
        self.entries = [
            {
                "schedule": deepcopy(s),
                "phase": "pending",
                "suppressedFrames": 0,
                "lastDroppedSequence": 0,
                "activationObserved": False,
                "recoveryObserved": False,
            }
            for s in configuration["schedules"]
        ]
        self.acknowledged_sequence = 0
        self.closed = False

    def tick(self, now_ns):
        return max(0, (now_ns - self.origin_ns) // 1000)

    def event(self, kind, entry, now_ns, **facts):
        schedule = entry["schedule"]
        tick = self.tick(now_ns)
        self.emit(
            kind,
            {
                "faultId": schedule["faultId"],
                "faultKind": "driver-input-loss",
                "contractRef": CONTRACT,
                "clockCodec": CODEC,
                "clockDomain": CLOCK,
                "tickUnit": "microsecond",
                "actualTick": str(tick),
                "scheduledActivationTick": schedule["activationTick"],
                "scheduledRecoveryTick": schedule["recoveryTick"],
                "effectScope": "driver-bridge-publication-lease",
                "vehicleEffect": "not_attested",
                "suppressedFrames": entry["suppressedFrames"],
                "lastDroppedSequence": entry["lastDroppedSequence"],
                **facts,
            },
            {"tick": str(tick), "clockDomain": CLOCK, "resolution": "microsecond"},
            schedule["targetRef"],
        )

    def advance(self, now_ns):
        if self.closed:
            return
        tick = self.tick(now_ns)
        for entry in self.entries:
            start, end = (
                int(entry["schedule"]["activationTick"]),
                int(entry["schedule"]["recoveryTick"]),
            )
            if entry["phase"] == "pending" and tick >= end:
                entry["phase"] = "finished"
                self.event("fault.schedule_missed", entry, now_ns)
            elif entry["phase"] == "pending" and tick >= start:
                # An older interval cannot acquire a recovery observation from
                # input accepted for a later interval.
                for previous in self.entries:
                    if previous["phase"] == "recovering":
                        previous["phase"] = "finished"
                        self.event(
                            "fault.effect_unobserved",
                            previous,
                            now_ns,
                            stage="recovery",
                        )
                entry.update(phase="active", activated_ns=now_ns)
                self.event("fault.activation_requested", entry, now_ns)
            elif entry["phase"] == "active" and tick >= end:
                entry.update(
                    phase="recovering",
                    recovered_ns=now_ns,
                    recovery_sequence=max(
                        self.acknowledged_sequence, entry["lastDroppedSequence"]
                    ),
                )
                self.event(
                    "fault.recovery_requested",
                    entry,
                    now_ns,
                    activationObserved=entry["activationObserved"],
                )

    def suppress(self, sequence, issued_ns, now_ns):
        if self.closed:
            return False
        active = next((e for e in self.entries if e["phase"] == "active"), None)
        if active is not None:
            active["suppressedFrames"] += 1
            active["lastDroppedSequence"] = sequence
            return True
        # Never replay a packet issued during inhibition after recovery.
        return any(
            e["phase"] == "recovering" and issued_ns < e["recovered_ns"]
            for e in self.entries
        )

    def acknowledge(self, sequence):
        self.acknowledged_sequence = max(self.acknowledged_sequence, sequence)

    def observe(self, active, produced_at, now_ns):
        if (
            self.closed
            or type(active) is not bool
            or type(produced_at) not in (int, float)
            or not math.isfinite(produced_at)
            or not 0 <= produced_at <= now_ns / 1_000_000_000
        ):
            return
        produced_ns = int(produced_at * 1_000_000_000)
        for entry in self.entries:
            if (
                entry["phase"] == "active"
                and not entry["activationObserved"]
                and entry["suppressedFrames"] > 0
                and active is False
                and produced_ns >= entry["activated_ns"]
            ):
                entry["activationObserved"] = True
                self.event(
                    "fault.activation_observed",
                    entry,
                    now_ns,
                    bridgeLeaseActive=False,
                    bridgeReportedTick=str(self.tick(produced_ns)),
                    publicationSequence=self.acknowledged_sequence,
                )
            elif (
                entry["phase"] == "recovering"
                and active is True
                and produced_ns >= entry["recovered_ns"]
                and self.acknowledged_sequence > entry["recovery_sequence"]
            ):
                entry.update(phase="finished", recoveryObserved=True)
                self.event(
                    "fault.recovery_observed",
                    entry,
                    now_ns,
                    bridgeLeaseActive=True,
                    bridgeReportedTick=str(self.tick(produced_ns)),
                    publicationSequence=self.acknowledged_sequence,
                )

    def close(self, now_ns):
        if self.closed:
            return
        self.closed = True
        for entry in self.entries:
            if entry["phase"] != "finished":
                self.event(
                    "fault.not_activated"
                    if entry["phase"] == "pending"
                    else "fault.interrupted",
                    entry,
                    now_ns,
                    activationObserved=entry["activationObserved"],
                    recoveryObserved=entry["recoveryObserved"],
                )
                entry["phase"] = "finished"
