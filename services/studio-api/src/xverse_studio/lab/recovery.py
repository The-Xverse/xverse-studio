"""Loss-of-connection projection; stop requests are distinct from observed stops."""


def handle_disconnect(policy: str, *, stop_permitted: bool = False, stop_action=None) -> dict:
    result = {"connection": "lost", "physicalState": "unknown", "cleanup": "unknown", "action": "none", "observations": [], "reasons": []}
    if policy == "observe_only":
        result["reasons"] = ["PHYSICAL_STATE_UNOBSERVED"]
        return result
    if policy != "request_stop":
        result["reasons"] = ["RECOVERY_POLICY_UNSUPPORTED"]
        return result
    if not stop_permitted or stop_action is None:
        result["reasons"] = ["STOP_AUTHORITY_UNAVAILABLE"]
        return result
    result["action"] = "stop_requested"
    try:
        observed = stop_action()
    except Exception:
        result.update(cleanup="failed", reasons=["STOP_REQUEST_FAILED"])
        return result
    if isinstance(observed, dict):
        result["observations"] = [observed]
        if observed.get("stoppedObserved") is True:
            result["physicalState"] = "stopped_observed"
        if observed.get("cleanupObserved") == "complete":
            result["cleanup"] = "complete"
        elif observed.get("cleanupObserved") == "failed":
            result["cleanup"] = "failed"
    if result["physicalState"] == "unknown":
        result["reasons"] = ["STOP_UNCONFIRMED"]
    return result
