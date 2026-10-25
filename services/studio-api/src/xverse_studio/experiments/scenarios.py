from copy import deepcopy
import math


def validate_provider_scenario(scenario: dict, capabilities: dict) -> dict:
    """Check selected provider operation limits after authoritative XDL validation.

    XDL syntax, resource references and executable plan identity remain owned by
    the platform. Opaque activation/recovery strings are not evaluated here.
    """
    diagnostics = []
    def reject(code, ref, message):
        diagnostics.append({"code": code, "elementRef": ref, "severity": "error", "message": message})
    if not isinstance(scenario, dict) or scenario.get("kind") != "Scenario" or not isinstance(scenario.get("spec"), dict) or not isinstance(capabilities, dict):
        return {"ready": False, "diagnostics": [{"code": "SCENARIO_UNAVAILABLE", "severity": "error", "message": "Select an authoritative validated Scenario and admitted provider."}]}
    spec = scenario["spec"]
    steps = spec.get("steps", [])
    observers = spec.get("observers", [])
    faults = spec.get("faults", [])
    if not isinstance(steps, list) or len(steps) > capabilities.get("maxSteps", 64):
        reject("SCENARIO_LIMIT", None, "The provider's bounded step count is exceeded.")
        return {"ready": False, "diagnostics": diagnostics}
    if not isinstance(observers, list) or len(observers) > capabilities.get("maxObservers", 32):
        reject("OBSERVER_LIMIT", None, "The provider's admitted observation budget is exceeded.")
    seen = set()
    for step in steps:
        ref = step.get("id")
        target = step.get("targetRef", {}).get("element")
        capability = capabilities.get("actions", {}).get(step.get("actionKind"))
        schedule = step.get("schedule", {})
        at, unit = schedule.get("at"), schedule.get("unit")
        if not isinstance(capability, dict):
            reject("CAPABILITY_UNSUPPORTED", ref, "The selected provider has no admitted operation for this action.")
            continue
        if step.get("action", {}).get("operation") not in capability.get("operations", []):
            reject("ACTION_UNSUPPORTED", ref, "This action payload is not admitted by the provider.")
        if target not in capability.get("targets", []):
            reject("TARGET_UNSUPPORTED", ref, "The action target is outside the provider's admitted scope.")
        if step.get("timeDomainId") not in capability.get("clockDomains", []):
            reject("CLOCK_UNSUPPORTED", ref, "The provider cannot interpret the selected source clock.")
        if unit not in capability.get("scheduleUnits", []) or not isinstance(at, (int, float)) or isinstance(at, bool) or not math.isfinite(at) or not 0 <= at <= capabilities.get("maxDurationSeconds", 30):
            reject("SCHEDULE_UNSUPPORTED", ref, "The schedule exceeds provider bounds or uses an unsupported time unit.")
            continue
        key = target, step.get("timeDomainId"), at, unit
        if key in seen:
            reject("SCHEDULE_CONFLICT", ref, "Concurrent actions on this target need an explicitly admitted ordering policy.")
        seen.add(key)
    if not isinstance(faults, list) or len(faults) > capabilities.get("maxFaults", 32):
        reject("FAULT_LIMIT", None, "The provider's fault budget is exceeded.")
    else:
        for fault in faults:
            admitted = capabilities.get("faults", {}).get(fault.get("faultKind"))
            if not isinstance(admitted, dict) or fault.get("targetRef", {}).get("element") not in admitted.get("targets", []):
                reject("FAULT_UNSUPPORTED", fault.get("id"), "This fault/target has no admitted provider contract.")
            elif fault.get("activation") not in admitted.get("activationIntents", []) or fault.get("recovery") not in admitted.get("recoveryIntents", []):
                reject("FAULT_SCHEDULE_UNSUPPORTED", fault.get("id"), "Opaque fault schedule semantics are preserved but not interpreted by this provider.")
    return {"ready": not diagnostics, "diagnostics": diagnostics}


def scenario_timeline(scenario: dict) -> list[dict]:
    """Intent markers only; caller overlays separately observed provider evidence."""
    spec = scenario.get("spec", {})
    result = []
    for step in spec.get("steps", [])[:64]:
        result.append({"id": step.get("id"), "kind": "stimulus", "state": "requested", "clockDomainRef": step.get("timeDomainId"), "schedule": deepcopy(step.get("schedule")), "targetRef": deepcopy(step.get("targetRef")), "actionKind": step.get("actionKind")})
    for fault in spec.get("faults", [])[:32]:
        result.append({"id": fault.get("id"), "kind": "fault", "state": "requested", "activationIntent": fault.get("activation"), "recoveryIntent": fault.get("recovery"), "targetRef": deepcopy(fault.get("targetRef")), "observed": False})
    return result
