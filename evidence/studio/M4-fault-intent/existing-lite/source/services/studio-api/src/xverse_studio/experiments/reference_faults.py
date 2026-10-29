"""Bounded, offline interpretation of an explicit owned XDL Profile.

This is not runtime admission. The existing reference provider continues to refuse
these declarations until its independently verified worker contract supports them.
Opaque native Fault activation/recovery strings are matched, never parsed.
"""
from copy import deepcopy
from decimal import Decimal
import hashlib
from pathlib import Path

from ruamel.yaml import YAML

from xverse_studio.storage.core import canonical, digest
from xverse_studio.xdl import XDLAdapter, XDLRejected
from xverse_studio.xdl.examples import API_VERSION, PROFILE_NAMESPACE, reference_resources

NAMESPACE = "io.xverse.studio.reference-faults"
SCHEMA_ID = "https://schemas.xverse.io/studio/reference-faults/1.0/schema.json"
SCHEMA_PATH = Path(__file__).with_name("reference-faults-v1.schema.json")
ACTIVATION = "urn:xverse:studio:reference-faults:1.0:activation"
RECOVERY = "urn:xverse:studio:reference-faults:1.0:recovery"
PROFILE_SPEC = {"extensionNamespace": NAMESPACE, "compatibleApiVersions": [API_VERSION],
                "schemaRef": SCHEMA_ID, "documentationRef": "urn:xverse:studio:reference-faults:1.0",
                "conflictPolicy": "reject"}


def _reject(message, code="FAULT_SCHEDULE_UNSUPPORTED"):
    raise XDLRejected(message, code)


def _microseconds(value, minimum, maximum):
    # Decimal conversion defines exact authored decimal seconds; no rounding or
    # epsilon joins positions to sample boundaries. Booleans are never numbers.
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        _reject("Reference time parameters require finite numeric seconds.")
    seconds = Decimal(str(value))
    if not seconds.is_finite() or not minimum <= seconds <= maximum:
        _reject("Reference time parameters exceed the owned model bounds.")
    ticks = seconds * 1_000_000
    if ticks != ticks.to_integral_value():
        _reject("Reference time parameters must resolve to exact whole microseconds.")
    return int(ticks)


def compile_reference_fault_intent(documents: dict[str, str]) -> dict:
    """Compile full authoritative sources, then bind this owned intent subset.

    Return original typed positions and canonical source ticks, not a shadow XDL
    definition. No worker, command, permission, clock mapping or file import is
    created. Unknown namespaces still fail authoritative full-source compilation.
    """
    adapter = XDLAdapter(profile_schema_paths=(SCHEMA_PATH,))
    compiled = adapter.compile(documents)
    if not compiled["valid"]:
        _reject("Authoritative XDL/profile compilation rejected the fault inputs.", "MODEL_INVALID")
    yaml = YAML(typ="safe")
    resources = [yaml.load(source) for source in documents.values()]
    profiles = [r for r in resources if r["kind"] == "Profile" and r["spec"].get("extensionNamespace") == NAMESPACE]
    if len(profiles) != 1 or profiles[0]["metadata"]["version"] != "1.0.0" or profiles[0]["spec"] != PROFILE_SPEC:
        _reject("Select the exact owned reference-faults Profile 1.0.0.", "PROFILE_UNRESOLVED")
    systems = [r for r in resources if r["kind"] == "System"]
    scenarios = [r for r in resources if r["kind"] == "Scenario"]
    if len(systems) != 1 or len(scenarios) != 1:
        _reject("Bind schedules only within one selected Scenario and System.")
    system, scenario = systems[0], scenarios[0]
    namespace = system["metadata"]["namespace"]
    template = reference_resources(namespace)
    expected_system = template["system.xdl.yaml"]
    expected_scenario = template["scenario.xdl.yaml"]
    if (system["metadata"]["name"] != "reference-loop"
        or system["spec"].get("timeDomains") != expected_system["spec"]["timeDomains"]
        or system["spec"].get("defaultTimeDomainId") != "simulation-time"):
        _reject("The schedule needs the exact owned simulation-time clock.", "CLOCK_UNSUPPORTED")
    observer = next((o for o in scenario["spec"].get("observers", []) if o["id"] == "state-observer"), None)
    expected_observer = expected_scenario["spec"]["observers"][0]
    if observer is None or any(observer.get(key) != value for key, value in expected_observer.items() if key != "description"):
        _reject("The schedule needs the declared owned state observer, target, sampling and dimensionless payload.", "TARGET_UNSUPPORTED")
    parameters = {p["id"]: p for p in compiled["plan"]["parameters"]}
    for name in ("duration", "timestep"):
        if name not in parameters or parameters[name].get("valueType") != "number" or parameters[name].get("unitSemantics") != "s":
            _reject("Duration and timestep require the owned seconds parameter contract.")
    if parameters.get("fault", {}).get("value") != "none":
        _reject("Explicit schedules cannot be mixed with the legacy fault parameter.", "FAULT_SCHEDULE_CONFLICT")
    duration = _microseconds(parameters["duration"]["value"], Decimal("0.1"), Decimal(30))
    step = _microseconds(parameters["timestep"]["value"], Decimal("0.01"), Decimal(1))
    if duration % step or not 1 <= duration // step <= 3000:
        _reject("Duration must contain at most 3,000 whole owned sample steps.")
    faults = scenario["spec"].get("faults", [])
    if not 1 <= len(faults) <= 32 or len({f["id"] for f in faults}) != len(faults):
        _reject("Select between one and 32 uniquely identified native faults.")
    # The profile is admitted only at the exact native fault attachment. A
    # second or misplaced payload cannot silently acquire binding semantics.
    attachments = []
    pending = list(resources)
    while pending:
        item = pending.pop()
        if isinstance(item, dict):
            if NAMESPACE in item.get("extensions", {}):
                attachments.append(item)
            pending.extend(item.values())
        elif isinstance(item, list):
            pending.extend(item)
    if len(attachments) != len(faults) or any(not any(item is fault for fault in faults) for item in attachments):
        _reject("The measurement binding belongs only on every selected native fault.")
    planned_faults = {f["faultId"]: f for f in compiled["plan"]["faults"]}
    intervals = []
    for fault in faults:
        binding = fault.get("extensions", {}).get(NAMESPACE)
        intent = fault.get("extensions", {}).get(PROFILE_NAMESPACE, {})
        planned = planned_faults[fault["id"]]
        expected_target = deepcopy(expected_observer["targetRef"])
        if (binding is None or fault["targetRef"] != expected_target or fault["faultKind"] != "measurement-hold"
            or set(fault.get("extensions", {})) != {NAMESPACE, PROFILE_NAMESPACE}
            or fault["activation"] != ACTIVATION or fault["recovery"] != RECOVERY):
            _reject("Only exact owned measurement-hold faults and Profile reference markers are supported.")
        if (set(intent) != {"schemaVersion", "kind", "target", "trigger", "duration", "timeDomainId"}
            or planned["timeDomainId"] != "simulation-time" or planned["trigger"]["kind"] != "time"):
            _reject("Use only the admitted experiment-lite timed fault-intent fields.")
        # Selected plan v1 normalizes time to nanoseconds. Preserve those exact
        # integer values; the owned source-clock codec admits whole microseconds.
        start_ns = planned["trigger"]["atTicks"]
        duration_ns = planned["duration"]["ticks"]
        if start_ns % 1000 or duration_ns % 1000:
            _reject("Fault quantities must resolve to exact whole source microseconds.")
        start, end = start_ns // 1000, (start_ns + duration_ns) // 1000
        if not 0 <= start < end < duration or start % step or end % step:
            _reject("Activation and recovery must be ordered sample boundaries before the run horizon.")
        intervals.append({"faultId": fault["id"], "targetRef": deepcopy(fault["targetRef"]),
                          "observerRef": binding["observerRef"], "field": binding["field"],
                          "clockDomainRef": planned["timeDomainId"],
                          "trigger": deepcopy(intent["trigger"]), "duration": deepcopy(intent["duration"]),
                          "planActivationTick": str(start_ns), "planDurationTick": str(duration_ns),
                          "planTickUnit": "ns", "sourceTickUnit": "us",
                          "activationTick": str(start), "recoveryTick": str(end)})
    intervals.sort(key=lambda item: (int(item["activationTick"]), item["faultId"]))
    for previous, current in zip(intervals, intervals[1:]):
        if int(current["activationTick"]) < int(previous["recoveryTick"]):
            _reject("Overlapping holds on the same measured field have no admitted precedence.", "FAULT_SCHEDULE_CONFLICT")
    def ref(resource):
        meta = resource["metadata"]
        return f"xdl://{meta['namespace']}/{resource['kind'].lower()}/{meta['name']}"
    return {"status": "compiled_intent", "executionAllowed": False,
            "limitation": "Offline intent only; the owned runtime does not yet admit scheduled faults.",
            "systemRef": ref(system), "scenarioRef": ref(scenario),
            "planDigest": compiled["planDigest"], "semanticDigest": compiled["semanticDigest"],
            "profile": {"namespace": NAMESPACE, "version": "1.0.0", "schemaRef": SCHEMA_ID,
                        "schemaDigest": "sha256:" + hashlib.sha256(SCHEMA_PATH.read_bytes()).hexdigest(),
                        "resourceDigest": digest(canonical(profiles[0]).encode())},
            "durationTick": str(duration), "timestepTick": str(step), "schedules": intervals}
