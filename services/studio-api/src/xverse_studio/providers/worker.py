"""Studio-owned native reference workload; never executes imported command text."""

from __future__ import annotations
import hashlib
import hmac
import json
import os
from pathlib import Path
import sys
import time
import traceback
import psutil
from xverse_studio.storage.core import atomic, canonical, digest
from xverse_studio.providers.reference_control import (
    CONTROL_STATES, MAX_PAUSED_WALL_SECONDS, REFERENCE_VERSION,
)


def main():
    root = Path(sys.argv[1]).resolve()
    request = json.loads((root / "request.json").read_text())
    secret = (root / "owner.key").read_bytes()
    config = request["configuration"]
    snapshot = request["snapshot"]
    # Re-validate exact effective inputs in the admitted provider, before effects.
    from xverse_studio.xdl import XDLAdapter
    from xverse_studio.xdl import reference_configuration

    adapter = XDLAdapter()
    compiled = adapter.compile(snapshot["documents"])
    actual = reference_configuration(snapshot["documents"], compiled)
    if (
        digest(actual) != digest(config)
        or compiled["planDigest"] != snapshot["planDigest"]
        or snapshot.get("providerIdentity", {}).get("limits", {}).get("maxPausedWallSeconds") != MAX_PAUSED_WALL_SECONDS
    ):
        atomic(
            root / "state.json",
            canonical(
                {
                    "state": "failed",
                    "stateVersion": 1,
                    "cleanup": "complete",
                    "evidence": "unavailable",
                    "reason": "EFFECTIVE_INPUT_MISMATCH",
                    "pid": os.getpid(),
                    "createTime": psutil.Process().create_time(),
                    "ownerDigest": digest(secret),
                    "endedAt": time.time(),
                }
            ).encode(),
        )
        return 2
    state = {
        "state": "running",
        "stateVersion": 1,
        "cleanup": "not_started",
        "evidence": "collecting",
        "pid": os.getpid(),
        "createTime": psutil.Process().create_time(),
        "ownerDigest": digest(secret),
        "effectivePlanDigest": compiled["planDigest"],
        "effectiveSemanticDigest": compiled.get("semanticDigest"),
        "startedAt": time.time(),
        "commandResults": {},
    }
    atomic(root / "state.json", canonical(state).encode())
    previous = "0" * 64
    count = 0
    runid = request["runId"]
    snapid = snapshot["snapshotId"]
    evidence = (root / "evidence.jsonl").open("xb", buffering=0)

    def emit(kind, payload, tick=None):
        nonlocal previous, count
        count += 1
        body = {
            "schemaVersion": "1.0",
            "eventId": f"{runid}:{count}",
            "runId": runid,
            "snapshotId": snapid,
            "sequence": str(count),
            "type": kind,
            "recordedAt": time.time(),
            "sourceTime": None
            if tick is None
            else {
                "tick": str(tick),
                "clockDomain": "simulation-time",
                "resolution": "microsecond",
                "uncertainty": 0,
            },
            "source": {"providerId": "studio.reference", "version": REFERENCE_VERSION},
            "elementRefs": config.get("elementRefs", []),
            "evidenceClass": "observed",
            "payload": payload,
            "evidenceRefs": [f"{runid}:reference-journal"],
            "previousDigest": previous,
        }
        previous = hashlib.sha256(canonical(body).encode()).hexdigest()
        evidence.write((canonical({**body, "digest": previous}) + "\n").encode())

    def save():
        state["updatedAt"] = time.time()
        atomic(root / "state.json", canonical(state).encode())

    def owned_command():
        # Only an owner-signed admitted request is attributable to an operation.
        command_path = root / "command.json"
        if not command_path.exists():
            return None
        cmd = json.loads(command_path.read_text())
        signature = cmd.pop("signature", "")
        if not hmac.compare_digest(
            signature,
            hmac.new(secret, canonical(cmd).encode(), hashlib.sha256).hexdigest(),
        ) or cmd["kind"] not in CONTROL_STATES:
            return None
        if cmd["operationId"] in state["commandResults"]:
            return None
        return cmd

    def fail_pending_command(code, message):
        # An accepted command that this workload never applied failed; it was not executed.
        cmd = owned_command()
        if cmd is None:
            return
        state["commandResults"][cmd["operationId"]] = {"status": "failed", "code": code}
        emit(
            "command.failed",
            {
                "operationId": cmd["operationId"],
                "kind": cmd["kind"],
                "code": code,
                "message": message,
            },
        )

    try:
        emit(
            "run.state_changed",
            {"state": "running", "stateVersion": 1, "evidenceScope": "owned_reference"},
        )
        emit(
            "log.appended",
            {
                "severity": "info",
                "message": "The owned first-order reference model started.",
                "providerScope": "owned_reference",
            },
        )
        step = float(config["timestep"])
        duration = float(config["duration"])
        n = min(10000, int(round(duration / step)))
        value = float(config["initial"])
        initial = value
        target = float(config["target"])
        gain = float(config["gain"])
        converter = config.get("converter")
        start = time.monotonic()
        stopped = False
        terminal_reason = None
        paused_at = None
        paused_total = 0.0
        completed_controls = set()
        fault_emitted = False
        for i in range(n):
            tick = round(i * step * 1_000_000)
            while True:
                cmd = owned_command()
                if cmd is not None:
                    operation = cmd["operationId"]
                    if cmd["kind"] in ("stop", "cancel"):
                        state["state"] = "stopping"
                        state["stateVersion"] += 1
                        save()
                        emit("command.delegated", {"operationId": operation, "kind": cmd["kind"]}, tick)
                        state["commandResults"][operation] = {"status": "completed"}
                        stopped = True
                        break
                    emit("command.delegated", {"operationId": operation, "kind": cmd["kind"]}, tick)
                    version = cmd.get("expectedStateVersion")
                    if (
                        type(version) is not int or version != state["stateVersion"]
                        or state["state"] not in CONTROL_STATES[cmd["kind"]]
                    ):
                        state["commandResults"][operation] = {"status": "failed", "code": "COMMAND_STATE_CONFLICT"}
                        emit("command.failed", {"operationId": operation, "code": "COMMAND_STATE_CONFLICT"}, tick)
                    else:
                        now = time.monotonic()
                        if cmd["kind"] == "resume" and paused_total + now - paused_at >= MAX_PAUSED_WALL_SECONDS:
                            state["commandResults"][operation] = {"status": "failed", "code": "PAUSE_BUDGET_EXHAUSTED"}
                            emit("command.failed", {"operationId": operation, "code": "PAUSE_BUDGET_EXHAUSTED"}, tick)
                            save()
                            continue
                        if cmd["kind"] == "pause":
                            paused_at = now
                            state["state"] = "paused"
                        else:
                            elapsed = now - paused_at
                            paused_total += elapsed
                            start += elapsed
                            paused_at = None
                            state["state"] = "running"
                        state["stateVersion"] += 1
                        emit("run.state_changed", {"state": state["state"], "stateVersion": state["stateVersion"]}, tick)
                        state["commandResults"][operation] = {"status": "completed"}
                        emit("command.completed", {"operationId": operation}, tick)
                        completed_controls.add(operation)
                    save()
                if state["state"] != "paused":
                    break
                remaining = MAX_PAUSED_WALL_SECONDS - paused_total - (time.monotonic() - paused_at)
                if remaining <= 0:
                    stopped = True
                    terminal_reason = "PAUSE_BUDGET_EXHAUSTED"
                    state["reason"] = terminal_reason
                    emit("log.appended", {"severity": "warning", "message": "The cumulative wall-time pause budget expired; the owned model stopped without completing its simulation coverage."}, tick)
                    break
                time.sleep(min(0.05, remaining))
            if stopped:
                break
            fault = config.get("fault", "none") == "stuck-sensor" and i >= n // 2
            if fault and not fault_emitted:
                emit(
                    "fault.activation_requested",
                    {"kind": "stuck-sensor", "target": config.get("observerRef")},
                    tick,
                )
                emit(
                    "fault.activation_observed",
                    {"kind": "stuck-sensor", "measuredValue": initial},
                    tick,
                )
                fault_emitted = True
            measured = initial if fault else value
            # Unit-delay loop: the plant applies this step's command only at the next step
            # (state[n+1] = state[n] + command[n]·step); sensing and control are within the step.
            control = gain * (target - measured)
            observation = {
                "observerRef": config.get("observerRef", "reference-observer"),
                "values": {
                    "value": value,
                    "measured": measured,
                    "target": target,
                    "control": control,
                },
                "units": {
                    "value": "1",
                    "measured": "1",
                    "target": "1",
                    "control": "1",
                },
                "coverage": "sample",
                "evidenceScope": "owned_reference",
            }
            if converter:
                # The declared linear converter maps exactly the plant state its flow carries.
                observation["values"]["observed"] = (
                    converter["scale"] * value + converter["offset"]
                )
                observation["units"]["observed"] = converter["toUnit"]
                observation["conversion"] = {
                    "field": "observed",
                    "source": "value",
                    **converter,
                }
            emit("observation.available", observation, tick)
            value += control * step
            delay = start + (i + 1) * step - time.monotonic()
            if delay > 0:
                time.sleep(min(delay, step))
        state["state"] = "stopped"
        state["stateVersion"] += 1
        state["cleanup"] = "complete"
        state["evidence"] = "complete"
        state["endedAt"] = time.time()
        emit(
            "run.state_changed",
            {
                "state": "stopped",
                "stateVersion": state["stateVersion"],
                "reason": terminal_reason or ("cancelled" if stopped else "duration_complete"),
            },
            round((i if stopped else n) * step * 1e6),
        )
        emit("cleanup.updated", {"status": "complete", "resources": []})
        for op, result in state["commandResults"].items():
            if result["status"] == "completed" and op not in completed_controls:
                emit("command.completed", {"operationId": op})
        if not stopped:
            fail_pending_command(
                "RUN_COMPLETED_BEFORE_COMMAND",
                "The run reached its declared duration before this accepted command could take effect.",
            )
        emit(
            "evidence.updated",
            {
                "status": "complete",
                "coverage": {
                    "clockDomain": "simulation-time",
                    "startTick": "0",
                    "endTick": str(round((i if stopped else n) * step * 1e6)),
                    "samplingPeriodTick": str(round(step * 1e6)),
                    "complete": not stopped,
                },
                "effectivePlanDigest": compiled["planDigest"],
            },
        )
        evidence.flush()
        os.fsync(evidence.fileno())
        state["journalDigest"] = digest((root / "evidence.jsonl").read_bytes())
        state["eventCount"] = count
        save()
    except BaseException as error:
        state.update(
            state="failed",
            stateVersion=state["stateVersion"] + 1,
            cleanup="unknown",
            evidence="partial",
            reason="REFERENCE_WORKER_ERROR",
        )
        try:
            emit(
                "log.appended",
                {
                    "severity": "error",
                    "message": "Reference workload failed; inspect canonical evidence and ownership.",
                },
            )
            save()
        except OSError:
            pass
        try:
            fail_pending_command(
                "REFERENCE_WORKER_ERROR",
                "The reference workload failed before this accepted command took effect.",
            )
            save()
        except (OSError, ValueError, KeyError, TypeError):
            pass
        return 1
    finally:
        evidence.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
