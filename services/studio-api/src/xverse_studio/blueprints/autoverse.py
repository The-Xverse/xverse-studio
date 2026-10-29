"""Canonical declarative Autoverse blueprint; discovery never starts the demo."""
from copy import deepcopy
import hashlib
from pathlib import Path

from xverse_studio.xdl.examples import (API_VERSION, PROFILE_NAMESPACE, dump_yaml,
    NATIVE_RUNTIME_NAMESPACE as NAMESPACE, NATIVE_RUNTIME_SCHEMA_ID as SCHEMA_ID)

CONTRACT_REF = "urn:xverse:studio:autoverse:classic:1.0"
RESOURCE_NAMESPACE = "org.xverse.studio.autoverse"
ROLES = {"carla": "Vehicle", "vcu": "Vehicle control unit", "someip-bridge": "Communication bridge",
         "score": "Cruise controller", "android": "Digital cluster", "driver": "Browser driver controls"}
SOFTWARE_COMPONENTS = {"score", "android", "driver"}
LOGICAL_DEVICES = {"carla", "vcu", "someip-bridge"}
REALIZATIONS = {"carla": "simulated", "vcu": "virtual", "someip-bridge": "virtual",
                "score": "virtual", "android": "virtual", "driver": "virtual"}
# External communication routes. Neither Zenoh nor SOME/IP is native X-COM.
ROUTES = [
    ("driver-throttle", "driver", ["vcu"], "number", "scalar"),
    ("driver-brake", "driver", ["vcu"], "number", "scalar"),
    ("driver-steering", "driver", ["carla"], "number", "scalar"),
    ("driver-cruise", "driver", ["vcu"], "boolean", "N/A"),
    ("driver-reverse", "driver", ["vcu"], "boolean", "N/A"),
    ("driver-speed-change", "driver", ["someip-bridge"], "number", "km/h"),
    ("vehicle-speed", "carla", ["vcu", "someip-bridge", "android", "driver"], "number", "km/h"),
    ("vcu-cruise-status", "vcu", ["someip-bridge", "carla", "android", "driver"], "boolean", "N/A"),
    ("vcu-throttle", "vcu", ["carla", "driver"], "number", "scalar"),
    ("vcu-brake", "vcu", ["carla", "driver"], "number", "scalar"),
    ("cruise-input", "someip-bridge", ["score"], "number", "km/h"),
    ("cruise-output", "score", ["someip-bridge"], "number", "scalar"),
    ("cruise-throttle", "someip-bridge", ["vcu"], "number", "scalar"),
    ("cruise-target", "someip-bridge", ["carla", "android", "driver"], "number", "km/h"),
    ("vcu-reverse-status", "vcu", ["carla", "android", "driver"], "boolean", "N/A"),
    ("vcu-brake-status", "vcu", ["carla", "android", "driver"], "boolean", "N/A"),
    ("vehicle-clock-seconds", "carla", ["someip-bridge", "driver"], "number", "s"),
    ("controller-clock-milliseconds", "someip-bridge", ["score"], "number", "ms"),
    ("controller-cruise-engagement", "someip-bridge", ["score"], "boolean", "N/A"),
    ("controller-speed-increment", "someip-bridge", ["score"], "number", "km/h"),
    ("controller-target-output", "score", ["someip-bridge"], "number", "km/h"),
    ("radar-distance", "carla", ["someip-bridge"], "number", "m"),
    ("controller-radar-distance", "someip-bridge", ["score"], "number", "m"),
    ("controller-obstacle-level", "score", ["someip-bridge"], "integer", "scalar"),
    ("obstacle-level", "someip-bridge", ["carla", "android"], "integer", "scalar"),
]


def reference(kind, name, element=None):
    value = {"apiVersion": API_VERSION, "kind": kind, "namespace": RESOURCE_NAMESPACE, "name": name}
    if element is not None:
        value["element"] = element
    return value


def resource(kind, name, spec, description):
    return {"apiVersion": API_VERSION, "kind": kind,
            "metadata": {"namespace": RESOURCE_NAMESPACE, "name": name, "version": "1.0.0", "description": description,
                         "provenance": {"source": CONTRACT_REF, "revision": "1.0.0", "maturity": "prototype",
                                        "limitations": ["Requires separately installed and admitted native Autoverse services; loading starts nothing.",
                                                        "External communication is not native X-COM or a coupled solver; simulation time remains unmapped."]}},
            "spec": spec}


def resources():
    interfaces = [{"id": name, "direction": "bidirectional", "payloadSchema": "urn:xverse:autoverse:wire-utf8-" + value_type + ":v1",
                   "unitSemantics": unit, "compatibility": "exact"} for name, _, _, value_type, unit in ROUTES]
    endpoints, flows = [], []
    for name, source, destinations, _, _ in ROUTES:
        source_id = name + "-out"
        endpoints.append({"id": source_id, "ownerId": source, "interfaceId": name, "direction": "output"})
        targets = []
        for destination in destinations:
            identifier = name + "-" + destination + "-in"
            endpoints.append({"id": identifier, "ownerId": destination, "interfaceId": name, "direction": "input"})
            targets.append(identifier)
        flows.append({"id": name + "-flow", "sourceEndpointId": source_id, "destinationEndpointIds": targets,
                      "interfaceId": name, "deliveryIntent": "best-effort", "timeDomainId": "host-runtime"})
    result = {}
    for identifier, role in ROLES.items():
        if identifier not in SOFTWARE_COMPONENTS:
            continue
        used = {name for name, source, destinations, _, _ in ROUTES if identifier == source or identifier in destinations}
        result[identifier + ".xdl.yaml"] = resource("Component", identifier, {
            "capabilities": ["autoverse-" + identifier], "interfaces": [deepcopy(i) for i in interfaces if i["id"] in used],
            "endpoints": [], "parameters": [],
        }, role)
    system = resource("System", "autoverse-demo", {
        "nodes": [{"id": key + "-node", "roles": [label]} for key, label in ROLES.items()],
        "componentInstances": [{"id": key, "componentRef": reference("Component", key), "nodeId": key + "-node"} for key in ROLES if key in SOFTWARE_COMPONENTS],
        "devices": [{"id": key, "capabilities": ["autoverse-" + key],
                     "supportedRealizationClasses": [REALIZATIONS[key]],
                     "nodeId": key + "-node"} for key in ROLES if key in LOGICAL_DEVICES],
        "interfaces": interfaces, "endpoints": endpoints, "flows": flows,
        "timeDomains": [{"id": "host-runtime", "clockClass": "monotonic", "epoch": "run-start", "rate": "1", "monotonic": True}],
        "defaultTimeDomainId": "host-runtime",
    }, "The complete Autoverse demo with Studio replacing the manual input surface through its existing signals.")
    system["extensions"] = {NAMESPACE: {"version": "1.0", "kind": "communication", "providerId": "autoverse.demo",
                                        "contractRef": CONTRACT_REF, "feedback": "externally-managed-asynchronous-communication"}}
    lifecycle = {name: "autoverse-" + name for name in ("prepare", "ready", "start", "stop", "failure")}
    deployment = resource("Deployment", "local-autoverse", {
        "systemRef": reference("System", "autoverse-demo"),
        "targets": [{"id": key + "-target", "targetClass": "container" if key in {"someip-bridge", "score", "android"} else "process",
                     "capabilities": ["autoverse-" + key], "lifecycle": lifecycle} for key in ROLES],
        "artifacts": [{"id": "autoverse-contract", "artifactKind": "integration-contract", "version": "1.0.0",
                       "sourceRef": CONTRACT_REF, "digest": "sha256:" + hashlib.sha256(Path(__file__).with_name("autoverse-contract.json").read_bytes()).hexdigest(),
                       "maturity": "prototype", "limitations": ["The contract file is packaged; actual images, binaries and services require separately pinned installation identities."]}],
        "bindings": [{"id": key + "-binding", "logicalRef": reference("System", "autoverse-demo", key),
                      "realizationClass": REALIZATIONS[key], "targetId": key + "-target",
                      "artifactIds": ["autoverse-contract"], "lifecycle": lifecycle} for key in ROLES],
        "readiness": {"requiredConditions": ["autoverse-installation-pinned", "docker-and-components-available", "exclusive-demo-ownership"], "failurePolicy": "fail-fast"},
    }, "Native Linux Autoverse installation; other Studio hosts remain independently supported.")
    scenario = resource("Scenario", "interactive-drive", {
        "systemRef": reference("System", "autoverse-demo"), "deploymentRef": reference("Deployment", "local-autoverse"),
        "initialConditions": {"driverSurface": "studio-browser", "initialBrakingRequest": 1, "initialCruiseRequest": False, "initialReverseRequest": False, "simulatorAdvancement": "public-vehicle-cli-synchronous", "fixedDeltaSeconds": 0.05},
        "steps": [{"id": "start-autoverse", "actionKind": "start", "targetRef": reference("System", "autoverse-demo", "carla"),
                   "timeDomainId": "host-runtime", "schedule": {"at": 0, "unit": "s"}, "action": {"operation": "run-autoverse-classic"}}],
        "observers": [{"id": "autoverse-telemetry", "targetRef": reference("System", "autoverse-demo", "vehicle-speed-flow"),
                       "timeDomainId": "host-runtime", "samplingIntent": "Bounded latest interface observations; source simulation time unavailable and receipt age separate.",
                       "payloadSchema": "urn:xverse:studio:autoverse:telemetry:v1", "unitSemantics": "per-field",
                       "evidenceSinkRef": "urn:xverse:studio:autoverse:journal"}],
        "metrics": [{"id": "reported-speed", "observerIds": ["autoverse-telemetry"],
                     "calculationRef": "urn:xverse:studio:autoverse:reported-speed-intent:v1", "unitSemantics": "km/h",
                     "acceptance": "Opaque metric intent only; no compatible evaluator or verdict is claimed."}],
        "acceptanceIntent": "Load, start, drive and stop the actual complete stack; process startup alone is not successful vehicle control.",
    }, "Interactive browser driving with immutable source and a bounded native session.")
    scenario["extensions"] = {
        PROFILE_NAMESPACE: {"schemaVersion": "0.1", "kind": "scenario-intent", "target": reference("Scenario", "interactive-drive"),
                            "seed": {"value": 0, "unitSemantics": "not-a-determinism-claim"},
                            "parameters": [],
                            "fidelityLimitations": ["An interactive external runtime; no deterministic replay or scientific model equivalence is claimed."]},
        NAMESPACE: {"version": "1.0", "kind": "scenario", "providerId": "autoverse.demo", "contractRef": CONTRACT_REF,
                    "durationSeconds": 600, "inputSurface": "studio-browser"},
    }
    result.update({"system.xdl.yaml": system, "deployment.xdl.yaml": deployment, "scenario.xdl.yaml": scenario})
    for name, namespace, schema, version, documentation in [
        ("experiment-lite", PROFILE_NAMESPACE, "https://xverse.io/profiles/experiment-lite/v0.1/schema.json", "0.1.0", "https://xverse.io/profiles/experiment-lite/v0.1/README.md"),
        ("native-runtime", NAMESPACE, SCHEMA_ID, "1.0.0", "urn:xverse:studio:native-runtime:1.0"),
    ]:
        profile = resource("Profile", name, {"extensionNamespace": namespace, "schemaRef": schema,
            "compatibleApiVersions": [API_VERSION], "documentationRef": documentation, "conflictPolicy": "reject"}, "Declarative profile; no installation or execution authority.")
        profile["metadata"]["version"] = version
        result[name + "-profile.xdl.yaml"] = profile
    return result


def documents():
    return {name: dump_yaml(value) for name, value in resources().items()}


def example():
    return {"id": "autoverse-classic", "entryId": "autoverse-classic", "name": "Autoverse complete demo",
            "description": "Load the real CARLA, VCU, SOME/IP, S-CORE and Android topology with browser driving controls.",
            "version": "1.0.0", "scope": "external_demo", "maturity": "prototype", "providerId": "autoverse.demo",
            "documents": documents(), "parameters": [],
            "profileRefs": [{"namespace": PROFILE_NAMESPACE, "version": "0.1.0"}, {"namespace": NAMESPACE, "version": "1.0.0"}],
            "expectedObservations": ["Vehicle speed, VCU and cruise-controller status from the admitted actual demo interfaces."],
            "limitations": ["Loading the declaration starts nothing. Native Autoverse provider installation and readiness are required.",
                            "Linux provider with CARLA, Zenoh, Docker, S-CORE and Android dependencies; no Windows demo claim.",
                            "Source simulation time and deterministic replay remain unavailable; command publication is separate from observed vehicle effect."]}
