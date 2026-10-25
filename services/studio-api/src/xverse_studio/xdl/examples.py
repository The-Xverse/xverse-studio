"""Studio-owned declarative blueprints; these never claim external model fidelity."""

from __future__ import annotations

from copy import deepcopy
import hashlib
from io import StringIO

from ruamel.yaml import YAML

API_VERSION = "xverse.io/xdl/v1alpha1"
PROFILE_NAMESPACE = "io.xverse.experiment"
EVALUATION_NAMESPACE = "io.xverse.studio.experiments"
EVALUATION_SCHEMA_ID = "https://schemas.xverse.io/studio/experiments/1.0/evaluation.schema.json"
MODEL_CONTRACT = (
    "xverse.studio.reference.first-order.v1\n"
    "state[0]=initial; measured[n]=initial if stuck-sensor active else state[n];\n"
    "state[n+1]=state[n]+gain*(target-measured[n])*timestep;\n"
    "simulation-time seconds with microsecond source ticks; samples in [0,duration);\n"
    "stuck-sensor activates at floor(sample-count/2), freezes measured state for the remaining run;\n"
    "initialConditions.stateParameterRef=initial; no physical equipment or external simulator.\n"
)
MODEL_DIGEST = "sha256:" + hashlib.sha256(MODEL_CONTRACT.encode()).hexdigest()

PARAMETERS = [
    {"id": "target", "label": "Target", "valueType": "number", "unit": "1", "default": 1.0,
     "minimum": -100.0, "maximum": 100.0, "description": "Normalized reference setpoint, dimensionless."},
    {"id": "gain", "label": "Response gain", "valueType": "number", "unit": "1", "default": 0.8,
     "minimum": 0.01, "maximum": 10.0, "description": "First-order response coefficient; gain × timestep must be at most one."},
    {"id": "initial", "label": "Initial state", "valueType": "number", "unit": "1", "default": 0.0,
     "minimum": -100.0, "maximum": 100.0, "description": "Initial normalized scalar state."},
    {"id": "duration", "label": "Duration", "valueType": "number", "unit": "s", "default": 5.0,
     "minimum": 0.1, "maximum": 30.0, "description": "Requested simulation horizon, in seconds; at most 3,000 samples."},
    {"id": "timestep", "label": "Time step", "valueType": "number", "unit": "s", "default": 0.1,
     "minimum": 0.01, "maximum": 1.0, "description": "Fixed simulation step in seconds. Duration must be an integer number of steps."},
    {"id": "fault", "label": "Reference fault", "valueType": "string", "unit": "1", "default": "none",
     "enum": ["none", "stuck-sensor"], "description": "Owned model fault only; stuck-sensor freezes the reported observation."},
]


def _ref(kind: str, name: str, namespace: str, element: str | None = None) -> dict:
    value = {"apiVersion": API_VERSION, "kind": kind, "namespace": namespace, "name": name}
    if element:
        value["element"] = element
    return value


def _resource(kind: str, name: str, namespace: str, spec: dict, description: str = "") -> dict:
    return {
        "apiVersion": API_VERSION, "kind": kind,
        "metadata": {"namespace": namespace, "name": name, "version": "1.0.0",
                     "description": description or "Studio-owned reference fixture.",
                     "provenance": {"source": "urn:xverse:studio:reference", "revision": "1.0.0", "maturity": "prototype",
                                    "limitations": ["Owned executable reference only; no external simulator, device or scientific fidelity claim."]}},
        "spec": spec,
    }


def _interface(identifier: str, direction: str = "bidirectional") -> dict:
    return {"id": identifier, "direction": direction, "payloadSchema": "urn:xverse:studio:normalized-scalar:v1",
            "unitSemantics": "1", "compatibility": "exact"}


def reference_resources(namespace: str = "org.xverse.studio.reference") -> dict[str, dict]:
    """Return a fresh valid XDL set for the admitted finite reference-model contract."""
    controller = _resource("Component", "reference-controller", namespace, {
        "capabilities": ["reference-control"], "interfaces": [_interface("command")],
        "endpoints": [{"id": "command-out", "ownerId": "reference-controller", "interfaceId": "command", "direction": "output"}],
        "parameters": [],
    })
    plant = _resource("Component", "reference-plant", namespace, {
        "capabilities": ["reference-response"], "interfaces": [_interface("state")],
        "endpoints": [{"id": "state-out", "ownerId": "reference-plant", "interfaceId": "state", "direction": "output"}],
        "models": [{"id": "first-order", "modelKind": "behavioral", "externalRef": "urn:xverse:studio:reference:first-order:v1",
                    "inputs": [], "outputs": [], "maturity": "prototype"}],
    })
    system = _resource("System", "reference-loop", namespace, {
        "nodes": [{"id": "controller-node", "roles": ["controller"]}, {"id": "plant-node", "roles": ["plant"]},
                  {"id": "observer-node", "roles": ["observer"]}],
        "componentInstances": [
            {"id": "controller", "componentRef": _ref("Component", "reference-controller", namespace), "nodeId": "controller-node"},
            {"id": "plant", "componentRef": _ref("Component", "reference-plant", namespace), "nodeId": "plant-node"},
        ],
        "interfaces": [_interface("command"), _interface("state")],
        "endpoints": [
            {"id": "controller-out", "ownerId": "controller", "interfaceId": "command", "direction": "output"},
            {"id": "plant-in", "ownerId": "plant", "interfaceId": "command", "direction": "input"},
            {"id": "plant-out", "ownerId": "plant", "interfaceId": "state", "direction": "output"},
            {"id": "observer-in", "ownerId": "observer-node", "interfaceId": "state", "direction": "input"},
        ],
        "flows": [
            {"id": "command-flow", "sourceEndpointId": "controller-out", "destinationEndpointIds": ["plant-in"],
             "interfaceId": "command", "deliveryIntent": "ordered", "timeDomainId": "simulation-time"},
            {"id": "state-flow", "sourceEndpointId": "plant-out", "destinationEndpointIds": ["observer-in"],
             "interfaceId": "state", "deliveryIntent": "ordered", "timeDomainId": "simulation-time"},
        ],
        "timeDomains": [{"id": "simulation-time", "clockClass": "simulation", "epoch": "0", "rate": "1", "monotonic": True}],
        "defaultTimeDomainId": "simulation-time",
    })
    lifecycle = {"prepare": "verify-owned-reference", "ready": "reference-ready", "start": "start-reference", "stop": "stop-reference", "failure": "record-reference-failure"}
    deployment = _resource("Deployment", "local-reference", namespace, {
        "systemRef": _ref("System", "reference-loop", namespace),
        "targets": [{"id": "reference-target", "targetClass": "model-unit", "capabilities": ["reference-response"], "lifecycle": lifecycle}],
        "artifacts": [{"id": "reference-model", "artifactKind": "model", "version": "1.0.0", "digest": MODEL_DIGEST,
                       "sourceRef": "urn:xverse:studio:reference:first-order:v1", "maturity": "prototype"}],
        "bindings": [{"id": name + "-binding", "logicalRef": _ref("System", "reference-loop", namespace, name),
                      "realizationClass": "simulated", "targetId": "reference-target", "artifactIds": ["reference-model"], "lifecycle": lifecycle}
                     for name in ("controller", "plant")],
        "readiness": {"requiredConditions": ["owned-reference-provider-installed", "requested-input-equality"], "failurePolicy": "fail-fast"},
    })
    scenario = _resource("Scenario", "reference-response", namespace, {
        "systemRef": _ref("System", "reference-loop", namespace), "deploymentRef": _ref("Deployment", "local-reference", namespace),
        "initialConditions": {"stateParameterRef": "initial"},
        "steps": [{"id": "start-reference", "actionKind": "start", "targetRef": _ref("System", "reference-loop", namespace, "plant"),
                   "timeDomainId": "simulation-time", "schedule": {"at": 0, "unit": "s"}, "action": {"operation": "reference-response"}}],
        "observers": [{"id": "state-observer", "targetRef": _ref("System", "reference-loop", namespace, "state-flow"),
                       "timeDomainId": "simulation-time", "samplingIntent": "every fixed model step including initial state",
                       "payloadSchema": "urn:xverse:studio:normalized-scalar:v1", "unitSemantics": "1",
                       "evidenceSinkRef": "urn:xverse:studio:reference:evidence"}],
        "metrics": [{"id": "final-state", "observerIds": ["state-observer"], "calculationRef": "urn:xverse:studio:metric:last",
                     "unitSemantics": "1", "acceptance": "Opaque intent only; use an admitted bounded assertion definition to assess evidence."}],
        "acceptanceIntent": "Exercise the owned reference provider; completion alone is not an assertion pass.",
    })
    scenario["extensions"] = {PROFILE_NAMESPACE: {
        "schemaVersion": "0.1", "kind": "scenario-intent", "target": _ref("Scenario", "reference-response", namespace),
        "seed": {"value": 7, "unitSemantics": "reference-seed"},
        "parameters": [{"id": p["id"], "valueType": p["valueType"], "value": p["default"], "unitSemantics": p["unit"], "mutability": "configuration"}
                       for p in PARAMETERS],
        "fidelityLimitations": ["Normalized first-order scalar response only; no automotive, industrial, simulator or hardware fidelity."],
    }}
    system_uri = f"xdl://{namespace}/system/reference-loop"
    scenario_uri = f"xdl://{namespace}/scenario/reference-response"
    scenario["extensions"][EVALUATION_NAMESPACE] = {"version": "1.0", "definitions": [{
        "evaluationId": "state-within-bound", "version": "1.0", "kind": "assertion", "name": "Reference state within bound",
        "systemRef": system_uri, "scenarioRef": scenario_uri, "coveragePolicy": "complete",
        "window": {"clockDomainRef": "simulation-time", "startTick": "0", "endTick": "5000000"},
        "expression": {"kind": "compare", "operator": "le",
                       "left": {"kind": "aggregate", "operator": "max", "input": {"kind": "signal", "observerRef": "state-observer", "field": "value"}},
                       "right": {"kind": "literal", "value": 1.2, "unit": "1"}},
        "description": "Owned model check only. Changing the time horizon can make coverage indeterminate.",
    }]}
    profile = _resource("Profile", "experiment-lite", namespace, {
        "extensionNamespace": PROFILE_NAMESPACE, "compatibleApiVersions": [API_VERSION],
        "schemaRef": "https://xverse.io/profiles/experiment-lite/v0.1/schema.json",
        "documentationRef": "https://xverse.io/profiles/experiment-lite/v0.1/README.md", "conflictPolicy": "reject",
    })
    profile["metadata"]["version"] = "0.1.0"
    evaluation_profile = _resource("Profile", "studio-experiments", namespace, {
        "extensionNamespace": EVALUATION_NAMESPACE, "compatibleApiVersions": [API_VERSION],
        "schemaRef": EVALUATION_SCHEMA_ID, "documentationRef": "urn:xverse:studio:experiments:1.0", "conflictPolicy": "reject",
    })
    evaluation_profile["metadata"]["version"] = "1.0.0"
    return {"controller.xdl.yaml": controller, "plant.xdl.yaml": plant, "system.xdl.yaml": system,
            "deployment.xdl.yaml": deployment, "scenario.xdl.yaml": scenario, "profile.xdl.yaml": profile,
            "evaluation-profile.xdl.yaml": evaluation_profile}


def dump_yaml(value: dict) -> str:
    stream = StringIO()
    yaml = YAML()
    yaml.default_flow_style = False
    yaml.dump(value, stream)
    return stream.getvalue()


def examples() -> list[dict]:
    """Discover data bundles; selecting one never installs or invokes provider code."""
    result = []
    for identifier, title, namespace, description in (
        ("reference-process-control", "Process control reference", "org.xverse.studio.process-control",
         "Explore a normalized process response, tune the setpoint and compare measured reference observations."),
        ("reference-automotive", "Automotive reference", "org.xverse.studio.automotive",
         "Explore a normalized controller and plant response using the same reference model; no vehicle dynamics claim."),
    ):
        resources = reference_resources(namespace)
        resources["system.xdl.yaml"]["metadata"]["description"] = description
        result.append({"id": identifier, "entryId": identifier, "name": title, "description": description,
                       "version": "1.0.0", "scope": "owned_reference", "maturity": "fixture", "providerId": "studio.reference",
                       "documents": {k: dump_yaml(v) for k, v in resources.items()}, "parameters": deepcopy(PARAMETERS),
                       "limitations": ["Owned executable reference only; external CARLA, native X-COM, process equipment and physical devices are not integrated."],
                       "expectedObservations": ["Normalized state, target, simulation time and reference fault markers."],
                       "profileRefs": [{"namespace": PROFILE_NAMESPACE, "version": "0.1.0"}, {"namespace": EVALUATION_NAMESPACE, "version": "1.0.0"}]})
    return result
