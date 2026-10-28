"""Versioned controls of the owned model only; no physical pause semantics."""

REFERENCE_VERSION = "1.1.0"
MAX_PAUSED_WALL_SECONDS = 30
CONTROL_STATES = {
    "stop": ("running", "preparing", "ready", "paused"),
    "cancel": ("running", "preparing", "ready", "paused"),
    "pause": ("running",),
    "resume": ("paused",),
}


def admitted_controls(descriptor):
    """Intersect the frozen descriptor with implemented nonphysical contracts."""
    records = descriptor.get("capabilityRecords", [])
    if not isinstance(records, list):
        return []
    admitted = []
    for kind, states in CONTROL_STATES.items():
        matches = [r for r in records if isinstance(r, dict) and r.get("kind") == kind]
        if kind not in descriptor.get("operations", []) or len(matches) != 1:
            continue
        record = matches[0]
        if (
            record.get("targetClass") == "model-unit"
            and record.get("legalStates") == list(states)
            and record.get("authorityRequirements") == ["native-backend-owned"]
            and record.get("physicalEffects") is False
            and record.get("parametersSchema") == {
                "type": "object", "properties": {}, "additionalProperties": False,
            }
        ):
            admitted.append(kind)
    return admitted
