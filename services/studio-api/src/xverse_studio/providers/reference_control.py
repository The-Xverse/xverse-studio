"""Versioned controls of the owned model only; no physical pause semantics."""

import math

REFERENCE_VERSION = "1.2.0"
MAX_PAUSED_WALL_SECONDS = 30
MAX_LIVE_MUTATIONS = 32
LIVE_PARAMETERS_SCHEMA = {
    "type": "object", "additionalProperties": False,
    "required": ["inputId", "expectedValue", "value"],
    "properties": {"inputId": {"const": "target"},
                   "expectedValue": {"type": "number", "minimum": -100, "maximum": 100},
                   "value": {"type": "number", "minimum": -100, "maximum": 100}},
}
CONTROL_STATES = {
    "stop": ("running", "preparing", "ready", "paused"),
    "cancel": ("running", "preparing", "ready", "paused"),
    "pause": ("running",),
    "resume": ("paused",),
    "set_parameter": ("running", "paused"),
}


def live_change(parameters, inputs, values, count):
    """Closed owned-model input contract, used independently by API and worker."""
    if not isinstance(parameters, dict) or set(parameters) != {"inputId", "expectedValue", "value"}:
        raise ValueError("LIVE_INPUT_INVALID")
    definition = inputs.get("target") if isinstance(inputs, dict) else None
    if parameters["inputId"] != "target" or not isinstance(definition, dict) or definition.get("mutable") is not True:
        raise ValueError("LIVE_INPUT_UNSUPPORTED")
    for key in ("value", "expectedValue"):
        value = parameters[key]
        if isinstance(value, bool) or not isinstance(value, (int, float)) or not -100 <= value <= 100 or not math.isfinite(value):
            raise ValueError("LIVE_INPUT_INVALID")
    if not isinstance(values, dict) or values.get("target") != parameters["expectedValue"]:
        raise ValueError("LIVE_INPUT_CONFLICT")
    if type(count) is not int or not 0 <= count < MAX_LIVE_MUTATIONS:
        raise ValueError("LIVE_INPUT_LIMIT")
    return float(parameters["value"])


def admitted_controls(descriptor, configuration=None):
    """Intersect the frozen descriptor with implemented nonphysical contracts."""
    records = descriptor.get("capabilityRecords", [])
    if not isinstance(records, list):
        return []
    admitted = []
    for kind, states in CONTROL_STATES.items():
        if kind == "set_parameter" and (not isinstance(configuration, dict) or not configuration.get("liveInputs")):
            continue
        if kind == "set_parameter" and (descriptor.get("providerVersion") != REFERENCE_VERSION
            or type(descriptor.get("limits", {}).get("maxLiveMutations")) is not int
            or descriptor["limits"]["maxLiveMutations"] != MAX_LIVE_MUTATIONS):
            continue
        matches = [r for r in records if isinstance(r, dict) and r.get("kind") == kind]
        if kind not in descriptor.get("operations", []) or len(matches) != 1:
            continue
        record = matches[0]
        if (
            record.get("targetClass") == "model-unit"
            and record.get("legalStates") == list(states)
            and record.get("authorityRequirements") == ["native-backend-owned"]
            and record.get("physicalEffects") is False
            and record.get("parametersSchema") == (LIVE_PARAMETERS_SCHEMA if kind == "set_parameter" else {
                "type": "object", "properties": {}, "additionalProperties": False,
            })
        ):
            admitted.append(kind)
    return admitted
