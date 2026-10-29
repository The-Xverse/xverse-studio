"""Single fenced browser driver, bounded latest-value mailbox, signed by backend."""
import hashlib
import hmac
import json
import secrets
import time
from xverse_studio.storage.core import Problem, atomic, canonical, digest
from .controls import ControlRejected, driver_frame


def input_request(root, action, payload, session):
    if not isinstance(payload, dict) or len(canonical(payload)) > 2048:
        raise Problem("CONTROL_REQUEST_INVALID", "Use the declared bounded input contract.")
    owner_path = root / "input-owner.json"
    owner = json.loads(owner_path.read_text()) if owner_path.exists() else {"generation": 0, "expires": 0, "globalSequence": 0}
    now = time.monotonic()
    if action == "acquire" and not payload:
        if owner["expires"] > now:
            raise Problem("CONTROL_DRIVER_BUSY", "Another browser driver holds the lease; release it or wait for expiry.", 409)
        token = secrets.token_urlsafe(32)
        owner = {"generation": owner["generation"] + 1, "tokenDigest": digest(token), "session": session,
                 "expires": now + 0.75, "globalSequence": owner["globalSequence"], "clientSequence": -1, "frame": None, "discreteCount": owner.get("discreteCount", 0)}
        atomic(owner_path, canonical(owner).encode())
        return {"leaseToken": token, "generation": owner["generation"], "leaseSeconds": 0.75}
    if action not in ("frame", "release") or set(payload) != ({"leaseToken", "generation", "frame"} if action == "frame" else {"leaseToken", "generation"}):
        raise Problem("CONTROL_REQUEST_INVALID", "Use acquire, frame or release with the declared fields.")
    if (type(payload["generation"]) is not int or payload["generation"] != owner["generation"]
        or not isinstance(payload["leaseToken"], str) or not hmac.compare_digest(digest(payload["leaseToken"]), owner.get("tokenDigest", ""))
        or owner.get("session") != session or now >= owner["expires"]):
        raise Problem("CONTROL_LEASE_EXPIRED", "The driver lease expired or belongs to another session; acquire a fresh lease.", 409)
    if action == "release":
        frame = {"sequence": owner["clientSequence"] + 1, "throttle": 0, "brake": 1, "steer": 0, "cruise": False}
    else:
        try:
            frame = driver_frame(payload["frame"])
        except ControlRejected as error:
            raise Problem(str(error), "The driver frame violates the input contract.") from None
        if frame["sequence"] <= owner["clientSequence"]:
            if frame == owner["frame"]:
                return {"status": "duplicate", "publicationSequence": owner["globalSequence"], "leaseRenewed": False}
            raise Problem("CONTROL_SEQUENCE_CONFLICT", "Driver sequence must increase; an exact retry never renews the lease.", 409)
    if action == "frame":
        if now - owner.get("acceptedAt", -1e10) < 0.04:
            raise Problem("CONTROL_RATE_LIMIT", "Driver input is limited to 25 requests per second.", 429)
        observed = json.loads((root / "state.json").read_text())
        telemetry = observed.get("inputTelemetry", {})
        previous = owner.get("frame") or {}
        if set(previous) & {"cruise", "reverse", "deltaSpeed"} and telemetry.get("lastPublishedSequence", 0) < owner["globalSequence"]:
            return {"status": "publication_pending", "publicationSequence": owner["globalSequence"], "leaseRenewed": False}
        items = telemetry.get("items", {})
        def fresh(name):
            item = items.get(name, {})
            return item.get("status") == "observed" and type(item.get("ageSeconds")) in (int, float) and 0 <= item["ageSeconds"] < 1 and 0 <= time.time() - observed.get("updatedAt", 0) < 1
        if frame.get("cruise") is True and not (fresh("speed") and items["speed"]["value"] >= 10 and fresh("reverseEngaged") and items["reverseEngaged"]["value"] is False and frame["brake"] == 0):
            raise Problem("CONTROL_CRUISE_PRECONDITION", "Engagement requires fresh speed of at least 10 km/h, forward mode, and released brake.", 409)
        if "reverse" in frame and not (fresh("speed") and items["speed"]["value"] <= 5 and fresh("cruiseEngaged") and items["cruiseEngaged"]["value"] is False):
            raise Problem("CONTROL_REVERSE_PRECONDITION", "Direction changes require fresh speed at most 5 km/h and cruise disengaged.", 409)
        if frame.get("deltaSpeed", 0) and not (fresh("cruiseEngaged") and items["cruiseEngaged"]["value"] is True):
            raise Problem("CONTROL_CRUISE_PRECONDITION", "A target-speed change requires fresh observed cruise engagement.", 409)
        if set(frame) & {"cruise", "reverse", "deltaSpeed"}:
            if owner.get("discreteCount", 0) >= 256:
                raise Problem("CONTROL_REQUEST_LIMIT", "This run reached its 256 discrete-request budget.")
            owner["discreteCount"] = owner.get("discreteCount", 0) + 1
    if owner["globalSequence"] >= 2**53 - 1:
        raise Problem("CONTROL_SEQUENCE_LIMIT", "Start a new run after reaching the sequence limit.")
    initial = owner["clientSequence"] < 0
    initial_gear = initial and owner["globalSequence"] == 0
    owner.update(clientSequence=frame["sequence"], frame=frame, globalSequence=owner["globalSequence"] + 1,
                 expires=0 if action == "release" else now + 0.75)
    packet = {"generation": owner["generation"], "issuedAt": now, "expiresAt": now + 0.75,
              "frame": {**({"cruise": False} if initial else {}), **({"reverse": False} if initial_gear else {}), **frame, "sequence": owner["globalSequence"]}}
    secret = (root / "owner.key").read_bytes()
    packet["signature"] = hmac.new(secret, canonical(packet).encode(), hashlib.sha256).hexdigest()
    # Save the sequence before delegation; a crash may leave a gap, never replay a pulse.
    owner["acceptedAt"] = now
    atomic(owner_path, canonical(owner).encode())
    atomic(root / "input.json", canonical(packet).encode())
    return {"status": "staged", "publicationSequence": owner["globalSequence"], "effect": "pending_publication_not_vehicle_acknowledgement"}
