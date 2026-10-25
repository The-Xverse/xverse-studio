"""Bounded source edits, followed by the existing authoritative full-XDL validation.

These helpers author intent only. Provider admission and execution are separate.
"""

from copy import deepcopy
import re

from xverse_studio.xdl import XDLRejected
from xverse_studio.xdl.edit_limits import check_edit_payload, MAX_EDIT_BYTES

SCENARIO_ITEM_LIMITS = {"step": 64, "fault": 32, "observer": 32, "metric": 64}
SCENARIO_ITEM_BYTES = MAX_EDIT_BYTES
COLLECTIONS = {
    "step": "steps",
    "fault": "faults",
    "observer": "observers",
    "metric": "metrics",
}
IDENTIFIER = re.compile(r"^[a-z][a-z0-9]*(?:-[a-z0-9]+)*$")


def edit_scenario(resource, edit):
    """Modify the transaction-local parsed Scenario, never source files or a runtime."""
    properties = edit.get("properties")
    kind = edit["kind"]
    check_edit_payload(edit)
    if kind == "set_assessment_definitions":
        from xverse_studio.assertions.snapshot import NAMESPACE

        definitions = edit.get("definitions")
        if (
            not isinstance(definitions, list)
            or len(definitions) > 32
            or any(not isinstance(value, dict) for value in definitions)
        ):
            raise XDLRejected(
                "Supply at most 32 inert assessment definition objects.", "INVALID_EDIT"
            )
        payload = resource.setdefault("extensions", {}).setdefault(
            NAMESPACE, {"version": "1.0", "definitions": []}
        )
        if payload.get("version") != "1.0":
            raise XDLRejected(
                "The assessment profile version is not admitted; preserve its original source.",
                "PROFILE_NOT_ADMITTED",
            )
        payload["definitions"] = deepcopy(definitions)
        return
    if kind != "remove_scenario_item":
        if not isinstance(properties, dict) or not properties or "id" in properties:
            raise XDLRejected(
                "Supply nonempty XDL properties separately from the immutable item ID.",
                "INVALID_EDIT",
            )
    spec = resource["spec"]
    if kind == "set_scenario_conditions":
        if set(properties) - {"initialConditions", "acceptanceIntent"}:
            raise XDLRejected(
                "Only initialConditions and acceptanceIntent belong to this operation.",
                "INVALID_EDIT",
            )
        spec.update(deepcopy(properties))
        return
    item_kind, identifier = edit.get("itemKind"), edit.get("itemId")
    if not isinstance(item_kind, str) or item_kind not in COLLECTIONS:
        raise XDLRejected("Select a step, fault, observer or metric.", "INVALID_EDIT")
    if (
        not isinstance(identifier, str)
        or len(identifier) > 63
        or not IDENTIFIER.fullmatch(identifier)
    ):
        raise XDLRejected(
            "Choose a stable scenario item ID of at most 63 characters.", "INVALID_EDIT"
        )
    collection = COLLECTIONS[item_kind]
    items = spec.get(collection, [])
    matches = [item for item in items if item.get("id") == identifier]
    if kind == "add_scenario_item":
        if any(
            item.get("id") == identifier
            for key in COLLECTIONS.values()
            for item in spec.get(key, [])
        ):
            raise XDLRejected(
                "This item ID already belongs to the Scenario.", "IDENTITY_CONFLICT"
            )
        if len(items) >= SCENARIO_ITEM_LIMITS[item_kind]:
            raise XDLRejected(
                "The bounded scenario item count limit is exceeded.", "LIMIT_EXCEEDED"
            )
        spec.setdefault(collection, []).append(
            {"id": identifier, **deepcopy(properties)}
        )
    elif kind in {"update_scenario_item", "remove_scenario_item"}:
        if len(matches) != 1:
            raise XDLRejected(
                "Select one existing Scenario item of the chosen kind.",
                "SELECTION_UNRESOLVED",
            )
        if kind == "remove_scenario_item":
            items.remove(matches[0])
        else:
            matches[0].update(deepcopy(properties))
    else:
        raise XDLRejected(
            "This scenario edit operation is unsupported.", "INVALID_EDIT"
        )
