"""Connection fixtures with declared expected semantics; trusted test inputs only.

Each variant edits the owned reference System and states what the authoritative validator
and Studio connection admission must conclude. Nothing here is executed.
"""

import io
import json

from ruamel.yaml import YAML

from xverse_studio.xdl import examples


def _variant(change):
    yaml = YAML(typ="safe")
    docs = dict(examples()[0]["documents"])
    system = yaml.load(docs["system.xdl.yaml"])
    change(system["spec"])
    out = io.StringIO()
    YAML().dump(json.loads(json.dumps(system)), out)
    docs["system.xdl.yaml"] = out.getvalue()
    return docs


def _flow(spec, flow_id):
    return next(f for f in spec["flows"] if f["id"] == flow_id)


def _interface(spec, interface_id):
    return next(i for i in spec["interfaces"] if i["id"] == interface_id)


def _endpoint(spec, endpoint_id):
    return next(e for e in spec["endpoints"] if e["id"] == endpoint_id)


def _second_command_flow(spec):
    _endpoint(spec, "plant-in")["multiplicity"] = "1"
    spec["flows"].append({**_flow(spec, "command-flow"), "id": "command-flow-2"})


def _clock_ambiguous(spec):
    spec["timeDomains"].append(
        {"id": "wall-time", "clockClass": "simulation", "epoch": "0", "rate": "1", "monotonic": True}
    )
    spec.pop("defaultTimeDomainId", None)
    _flow(spec, "command-flow").pop("timeDomainId", None)


def _feedback(spec):
    spec["endpoints"].append(
        {"id": "controller-in", "ownerId": "controller", "interfaceId": "state", "direction": "input"}
    )
    spec["flows"].append({
        "id": "feedback-flow", "sourceEndpointId": "plant-out", "destinationEndpointIds": ["controller-in"],
        "interfaceId": "state", "deliveryIntent": "latest-value", "timeDomainId": "simulation-time",
    })


def _spare_input(spec):
    spec["endpoints"].append(
        {"id": "spare-in", "ownerId": "plant", "interfaceId": "command", "direction": "input", "multiplicity": "1..*"}
    )


def _model_coupling(spec):
    # A System model consuming and producing declared interfaces: a model coupling.
    spec.setdefault("models", []).append({
        "id": "thermal-coupling", "modelKind": "physical", "externalRef": "urn:example:thermal:v1",
        "inputs": ["command"], "outputs": ["state"], "maturity": "prototype",
    })


def _network_link(spec):
    spec["networks"] = [{"id": "lab-bus", "scope": "local", "capabilities": ["message-transport"]}]
    spec["links"] = [{
        "id": "command-link", "networkId": "lab-bus",
        "participantEndpointIds": ["controller-out", "plant-in"], "connectivity": "directed",
    }]


# name → (change, expected). "admission" maps flow id → expected admission.
FIXTURES = {
    "compatible": (lambda spec: None, {
        "valid": True, "admission": {"command-flow": "admitted", "state-flow": "admitted"}, "codes": set(), "cycles": 0}),
    "direction-mismatch": (lambda spec: _flow(spec, "command-flow").update(sourceEndpointId="plant-in"), {
        "valid": False, "admission": {"command-flow": "rejected"}, "codes": set(), "cycles": 0}),
    "interface-mismatch": (lambda spec: _flow(spec, "command-flow").update(interfaceId="state"), {
        "valid": False, "admission": {"command-flow": "rejected"}, "codes": set(), "cycles": 0}),
    "explicit-converter": (lambda spec: _interface(spec, "command").update(compatibility="explicit-converter"), {
        "valid": True, "admission": {"command-flow": "unsupported", "state-flow": "admitted"},
        "codes": {"CONVERSION_UNSUPPORTED"}, "cycles": 0}),
    "backward-version": (lambda spec: _interface(spec, "state").update(compatibility="backward", versionRange=">=1.0.0 <2.0.0"), {
        "valid": True, "admission": {"command-flow": "admitted", "state-flow": "unsupported"},
        "codes": {"VERSION_COMPATIBILITY_UNSUPPORTED"}, "cycles": 0}),
    "multiplicity-satisfied": (lambda spec: _endpoint(spec, "plant-in").update(multiplicity="1"), {
        "valid": True, "admission": {"command-flow": "admitted"}, "codes": set(), "cycles": 0}),
    "multiplicity-violated": (_second_command_flow, {
        "valid": True, "admission": {"command-flow": "rejected", "command-flow-2": "rejected"},
        "codes": {"MULTIPLICITY_VIOLATED"}, "cycles": 0}),
    "multiplicity-uninterpreted": (lambda spec: _endpoint(spec, "plant-in").update(multiplicity="exactly-one"), {
        "valid": True, "admission": {"command-flow": "unsupported"}, "codes": {"MULTIPLICITY_UNSUPPORTED"}, "cycles": 0}),
    "multiplicity-inverted-range": (lambda spec: _endpoint(spec, "plant-in").update(multiplicity="3..1"), {
        "valid": True, "admission": {"command-flow": "unsupported"}, "codes": {"MULTIPLICITY_UNSUPPORTED"}, "cycles": 0}),
    "multiplicity-lower-bound-unmet": (_spare_input, {
        "valid": True, "admission": {"command-flow": "admitted", "state-flow": "admitted"},
        "codes": {"MULTIPLICITY_VIOLATED"}, "cycles": 0, "blocking": 1}),
    "clock-ambiguous": (_clock_ambiguous, {
        "valid": True, "admission": {"command-flow": "rejected", "state-flow": "admitted"},
        "codes": {"CLOCK_AMBIGUOUS"}, "cycles": 0}),
    "quality-declared": (lambda spec: _flow(spec, "command-flow").update(quality={"latencyBound": {"value": 10, "unit": "ms"}}), {
        "valid": True, "admission": {"command-flow": "unsupported"}, "codes": {"QUALITY_UNSUPPORTED"}, "cycles": 0}),
    "feedback-cycle": (_feedback, {
        "valid": True, "admission": {"command-flow": "unsupported", "feedback-flow": "unsupported", "state-flow": "admitted"},
        "codes": {"CAUSALITY_CONTRACT_UNSUPPORTED"}, "cycles": 1}),
    "model-coupling": (_model_coupling, {
        "valid": True, "admission": {"command-flow": "admitted"}, "codes": {"MODEL_COUPLING_UNSUPPORTED"},
        "cycles": 0, "couplings": 1}),
    # An unadmitted extension claiming coupling semantics is refused by the validator.
    "physical-coupling-extension": (
        lambda spec: _flow(spec, "state-flow").update(
            extensions={"org.example.coupling": {"kind": "thermal", "solver": "co-simulation"}}
        ),
        {"valid": False, "admission": {"state-flow": "rejected", "command-flow": "unknown"}, "codes": set(), "cycles": 0},
    ),
    "network-link": (_network_link, {
        "valid": True, "admission": {"command-flow": "admitted"}, "codes": set(), "cycles": 0, "links": 1}),
}


def fixture(name):
    change, expected = FIXTURES[name]
    return _variant(change), expected


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--variant", choices=sorted(FIXTURES), required=True)
    print(fixture(parser.parse_args().variant)[0]["system.xdl.yaml"], end="")
