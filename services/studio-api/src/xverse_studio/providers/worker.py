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
            "source": {"providerId": "studio.reference", "version": "1.0.0"},
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
        # Only an owner-signed stop/cancel request is attributable to an operation.
        command_path = root / "command.json"
        if not command_path.exists():
            return None
        cmd = json.loads(command_path.read_text())
        signature = cmd.pop("signature", "")
        if not hmac.compare_digest(
            signature,
            hmac.new(secret, canonical(cmd).encode(), hashlib.sha256).hexdigest(),
        ) or cmd["kind"] not in ("stop", "cancel"):
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
        start = time.monotonic()
        stopped = False
        fault_emitted = False
        for i in range(n):
            tick = round(i * step * 1_000_000)
            cmd = owned_command()
            if cmd is not None:
                operation = cmd["operationId"]
                state["state"] = "stopping"
                state["stateVersion"] += 1
                save()
                emit(
                    "command.delegated",
                    {"operationId": operation, "kind": cmd["kind"]},
                    tick,
                )
                state["commandResults"][operation] = {"status": "completed"}
                stopped = True
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
            control = gain * (target - measured)
            emit(
                "observation.available",
                {
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
                },
                tick,
            )
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
                "reason": "cancelled" if stopped else "duration_complete",
            },
            round(duration * 1e6),
        )
        emit("cleanup.updated", {"status": "complete", "resources": []})
        for op, result in state["commandResults"].items():
            if result["status"] == "completed":
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
