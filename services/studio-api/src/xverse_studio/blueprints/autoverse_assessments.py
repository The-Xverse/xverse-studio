"""Inert bounded assessment declarations for recorded bridge acknowledgements."""
from copy import deepcopy
from xverse_studio.xdl.examples import EVALUATION_NAMESPACE as NAMESPACE, EVALUATION_SCHEMA_ID as SCHEMA_ID

CONTRACT = "urn:xverse:studio:autoverse:fault-record-assessment:1.0"
OBSERVER = "autoverse-fault-records"
FIELDS = {"activationObserved": "fault.activation_observed", "recoveryObserved": "fault.recovery_observed"}


def observer(reference):
    return {"id": OBSERVER, "targetRef": reference("System", "autoverse-demo", "driver"),
            "timeDomainId": "host-runtime", "samplingIntent": "Retrospective enumeration of recorded bridge-lease acknowledgement events; not continuous state or vehicle effects.",
            "payloadSchema": CONTRACT, "unitSemantics": "boolean event fields; dimensionless counts",
            "evidenceSinkRef": "urn:xverse:studio:autoverse:journal"}


def definitions(reference):
    system = reference("System", "autoverse-demo")
    ns = system["namespace"]
    base = {"version": "1.0", "kind": "assertion", "systemRef": f"xdl://{ns}/system/autoverse-demo",
            "scenarioRef": f"xdl://{ns}/scenario/interactive-drive", "coveragePolicy": "complete",
            "window": {"clockDomainRef": "host-runtime", "startTick": "0", "endTick": "10000000"}}
    def signal(field):
        return {"kind": "signal", "observerRef": OBSERVER, "field": field}
    def aggregate(operator, field):
        return {"kind": "aggregate", "operator": operator, "input": signal(field)}
    def entry(identity, expression, **extra):
        return {**deepcopy(base), "evaluationId": identity, "name": identity.replace("-", " ").capitalize(), "expression": expression, **extra}
    return [entry("bridge-loss-acknowledged", aggregate("any", "activationObserved")),
            entry("two-recoveries-before-ten-seconds", {"kind": "compare", "operator": "ge", "left": aggregate("count", "recoveryObserved"), "right": {"kind": "literal", "value": 2, "unit": "1"}}),
            entry("recovery-through-thirty-seconds", aggregate("any", "recoveryObserved"), window={**base["window"], "endTick": "30000000"}),
            entry("recorded-activation-count", aggregate("count", "activationObserved"), kind="metric", resultUnit="1"),
            entry("unadmitted-count-unit", {"kind": "compare", "operator": "lt", "left": aggregate("count", "activationObserved"), "right": {"kind": "literal", "value": 2, "unit": "m"}}),
            entry("unmapped-simulation-clock", aggregate("any", "activationObserved"), window={**base["window"], "clockDomainRef": "simulation-time"})]


def extend(resources, reference, resource):
    result = deepcopy(resources)
    scenario = result["scenario.xdl.yaml"]
    scenario["spec"]["observers"].append(observer(reference))
    fault_contract = "urn:xverse:studio:autoverse:input-loss:1.0"
    scenario["spec"]["faults"] = [{"id": identity, "targetRef": reference("System", "autoverse-demo", "driver"),
        "faultKind": "driver-input-loss", "activation": fault_contract + ":activation", "recovery": fault_contract + ":recovery", "maturity": "prototype",
        "extensions": {"io.xverse.experiment": {"schemaVersion": "0.1", "kind": "fault-intent",
            "target": reference("Scenario", "interactive-drive", identity), "trigger": {"kind": "time", "at": at, "unit": "s"},
            "duration": {"value": 3, "unit": "s"}, "timeDomainId": "host-runtime"}}}
        for identity, at in [("first-loss", 5), ("second-loss", 13), ("interrupted-loss", 21)]]
    scenario["extensions"]["io.xverse.studio.native-runtime"]["durationSeconds"] = 30
    scenario.setdefault("extensions", {})[NAMESPACE] = {"version": "1.0", "definitions": definitions(reference)}
    profile = resource("Profile", "fault-record-assessments", {"extensionNamespace": NAMESPACE,
        "schemaRef": SCHEMA_ID, "compatibleApiVersions": [scenario["apiVersion"]],
        "documentationRef": "urn:xverse:studio:experiments:1.0", "conflictPolicy": "reject"},
        "Bounded retrospective assessments; no provider installation or execution authority.")
    result["assessment-profile.xdl.yaml"] = profile
    return result
