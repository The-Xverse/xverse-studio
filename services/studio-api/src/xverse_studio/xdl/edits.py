"""Transactional semantic edits to authored XDL, using the public validator after editing."""

from copy import deepcopy
from io import StringIO
import re

from ruamel.yaml import YAML

from . import XDLAdapter, XDLRejected
from .examples import PROFILE_NAMESPACE

REGISTRY = {
    "set_parameter": {"documentId", "parameterId", "parameter", "value", "elementRef", "elementId"},
    "add_element": {"documentId", "templateId", "elementId", "nodeId"},
    "remove_element": {"documentId", "elementId", "elementRef", "removalSet"},
    "connect_endpoints": {"documentId", "flowId", "sourceEndpointId", "destinationEndpointIds", "interfaceId", "timeDomainId", "deliveryIntent"},
    "disconnect_flow": {"documentId", "flowId", "elementRef"},
    "set_binding": {"documentId", "bindingId", "targetId", "realizationClass", "artifactIds", "resourceIds"},
    "rename_display_label": {"documentId", "label", "name", "elementRef"},
}
IDENTIFIER = re.compile(r"^[a-z][a-z0-9]*(?:-[a-z0-9]+)*$")


def semantic_edits(documents: dict[str, str], edits: list[dict]) -> dict[str, str]:
    """Return a new complete source transaction, or refuse without altering the inputs.

    Semantic authoring requires an already valid set. Unknown/unresolved extensions remain
    available through exact source editing, but cannot be silently rewritten by this helper.
    """
    if not isinstance(edits, list) or not 0 < len(edits) <= 100:
        raise XDLRejected("A semantic transaction needs one to 100 edits.", "LIMIT_EXCEEDED")
    report = XDLAdapter().validate(documents)
    if not report["valid"]:
        raise XDLRejected("Resolve authoritative source diagnostics before applying semantic edits; original source is preserved.", "MODEL_INVALID")
    yaml = YAML()
    yaml.preserve_quotes = True
    parsed = {name: yaml.load(source) for name, source in documents.items()}
    touched = set()

    def resource_uri(resource):
        return f"xdl://{resource['metadata']['namespace']}/{resource['kind'].lower()}/{resource['metadata']['name']}"

    def check_target(edit, resource, identifier=None):
        target = edit.get("elementRef")
        allowed = {resource_uri(resource)}
        if identifier:
            allowed.add(resource_uri(resource) + "#" + identifier)
        if target is not None and target not in allowed:
            raise XDLRejected("The selected stable reference does not identify this edit target.", "SELECTION_UNRESOLVED")

    def select(kind: str, explicit: str | None) -> tuple[str, dict]:
        found = [(name, value) for name, value in parsed.items() if value.get("kind") == kind and (not explicit or name == explicit)]
        if len(found) != 1:
            raise XDLRejected("Select exactly one existing " + kind + " document.", "SELECTION_UNRESOLVED")
        return found[0]

    for edit in edits:
        if not isinstance(edit, dict) or edit.get("kind") not in REGISTRY:
            raise XDLRejected("This semantic edit operation is unsupported.")
        kind = edit["kind"]
        if set(edit) - REGISTRY[kind] - {"kind"}:
            raise XDLRejected("Unknown fields in the semantic edit envelope.", "INVALID_EDIT")
        explicit = edit.get("documentId")
        if explicit is not None and explicit not in parsed:
            raise XDLRejected("The requested document does not belong to this project.", "SELECTION_UNRESOLVED")
        if kind == "set_parameter":
            parameter_id = edit.get("parameterId", edit.get("parameter"))
            if not isinstance(parameter_id, str) or "value" not in edit:
                raise XDLRejected("A parameter edit requires its identifier and typed value.", "INVALID_EDIT")
            chosen = parsed.get(explicit) if explicit else None
            if chosen and chosen.get("kind") in {"System", "Component"}:
                name = explicit
                values = chosen["spec"].get("parameters", [])
                matches = [v for v in values if v.get("id") == parameter_id]
                if len(matches) != 1:
                    raise XDLRejected("The selected declaration has no unambiguous parameter.", "PARAMETER_UNRESOLVED")
                if matches[0].get("mutability") == "constant":
                    raise XDLRejected("A constant parameter declaration is immutable.", "PARAMETER_IMMUTABLE")
                matches[0]["default"] = deepcopy(edit["value"])
            else:
                name, resource = select("Scenario", explicit)
                matches = [p for p in resource.get("extensions", {}).get(PROFILE_NAMESPACE, {}).get("parameters", []) if p.get("id") == parameter_id]
                if len(matches) != 1:
                    raise XDLRejected("The selected scenario has no unambiguous admitted parameter.", "PARAMETER_UNRESOLVED")
                if matches[0].get("mutability") == "constant":
                    raise XDLRejected("A constant parameter is immutable.", "PARAMETER_IMMUTABLE")
                matches[0]["value"] = deepcopy(edit["value"])
            check_target(edit, parsed[name], parameter_id)
            if edit.get("elementId") not in (None, parameter_id):
                raise XDLRejected("Instance-targeted parameter editing is unavailable for this declaration.", "SELECTION_UNRESOLVED")
            touched.add(name)
        elif kind == "add_element":
            name, system = select("System", explicit)
            identifier = edit.get("elementId")
            template = edit.get("templateId")
            definitions = [v for v in parsed.values() if v.get("kind") == "Component" and
                           (v["metadata"]["name"] == template or f"xdl://{v['metadata']['namespace']}/component/{v['metadata']['name']}" == template)]
            if not isinstance(identifier, str) or not IDENTIFIER.fullmatch(identifier) or len(identifier) > 63 or len(definitions) != 1:
                raise XDLRejected("Choose an existing Component definition and a valid new element ID.", "INVALID_EDIT")
            if any(v.get("id") == identifier for values in system["spec"].values() if isinstance(values, list) for v in values if isinstance(v, dict)):
                raise XDLRejected("The element ID already belongs to this System.", "IDENTITY_CONFLICT")
            definition = definitions[0]
            instance = {"id": identifier, "componentRef": {"apiVersion": definition["apiVersion"], "kind": "Component",
                        "namespace": definition["metadata"]["namespace"], "name": definition["metadata"]["name"]}}
            if edit.get("nodeId"):
                instance["nodeId"] = edit["nodeId"]
            system["spec"].setdefault("componentInstances", []).append(instance)
            touched.add(name)
        elif kind in {"remove_element", "disconnect_flow"}:
            name, system = select("System", explicit)
            identifier = edit.get("elementId") if kind == "remove_element" else edit.get("flowId")
            identifier = identifier or str(edit.get("elementRef", "")).rsplit("#", 1)[-1]
            if not identifier:
                raise XDLRejected("Select an existing element.", "INVALID_EDIT")
            check_target(edit, system, identifier)
            removal_set = edit.get("removalSet", [])
            if not isinstance(removal_set, list) or any(not isinstance(item, str) for item in removal_set):
                raise XDLRejected("Explicit impacted removals must be element ID strings.", "INVALID_EDIT")
            system_uri = resource_uri(system)
            removals = {system_uri + "#" + identifier}
            removals.update(item if "#" in item else system_uri + "#" + item for item in removal_set)
            found = False
            for document_name, resource in parsed.items():
                uri = resource_uri(resource)
                for collection, values in resource["spec"].items():
                    if not isinstance(values, list):
                        continue
                    kept = [v for v in values if not isinstance(v, dict) or uri + "#" + str(v.get("id")) not in removals]
                    if len(kept) != len(values):
                        resource["spec"][collection] = kept
                        touched.add(document_name)
                        found = True
            if not found:
                raise XDLRejected("The requested element does not exist.", "SELECTION_UNRESOLVED")
            def references(value, current_uri, pointer=""):
                if isinstance(value, dict):
                    if all(k in value for k in ("namespace", "kind", "name", "element")):
                        ref = f"xdl://{value['namespace']}/{value['kind'].lower()}/{value['name']}#{value['element']}"
                        if ref in removals:
                            return [pointer]
                    return [p for key, child in value.items() if key != "id" for p in references(child, current_uri, pointer + "/" + str(key))]
                if isinstance(value, list):
                    return [p for index, child in enumerate(value) for p in references(child, current_uri, pointer + "/" + str(index))]
                return [pointer] if isinstance(value, str) and current_uri + "#" + value in removals else []
            impacts = [p for resource in parsed.values() for p in references(resource["spec"], resource_uri(resource))]
            if impacts:
                raise XDLRejected("The element is referenced; explicitly remove or replace the impacted references before removing it.", "REFERENCE_CONFLICT")
        elif kind == "connect_endpoints":
            name, system = select("System", explicit)
            spec = system["spec"]
            endpoints = {p["id"]: p for p in spec.get("endpoints", [])}
            source = endpoints.get(edit.get("sourceEndpointId"))
            destinations = edit.get("destinationEndpointIds")
            interface = edit.get("interfaceId")
            if not source or not isinstance(destinations, list) or not destinations or any(p not in endpoints for p in destinations):
                raise XDLRejected("Select existing source and destination endpoints.", "ENDPOINT_UNRESOLVED")
            if source["direction"] not in {"output", "bidirectional"} or any(endpoints[p]["direction"] not in {"input", "bidirectional"} for p in destinations):
                raise XDLRejected("Endpoint direction is incompatible.", "ENDPOINT_INCOMPATIBLE")
            if source["interfaceId"] != interface or any(endpoints[p]["interfaceId"] != interface for p in destinations):
                raise XDLRejected("Interfaces must match exactly; an explicit admitted converter is required for changes.", "ENDPOINT_INCOMPATIBLE")
            identifier = edit.get("flowId")
            if not isinstance(identifier, str) or not IDENTIFIER.fullmatch(identifier):
                raise XDLRejected("Choose a valid stable flow ID.", "INVALID_EDIT")
            flow = {"id": identifier, "sourceEndpointId": source["id"], "destinationEndpointIds": destinations,
                    "interfaceId": interface, "deliveryIntent": edit.get("deliveryIntent", "ordered")}
            clock = edit.get("timeDomainId", spec.get("defaultTimeDomainId"))
            if clock:
                flow["timeDomainId"] = clock
            spec.setdefault("flows", []).append(flow)
            touched.add(name)
        elif kind == "set_binding":
            name, resource = select("Deployment", explicit)
            bindings = [v for v in resource["spec"].get("bindings", []) if v.get("id") == edit.get("bindingId")]
            if len(bindings) != 1:
                raise XDLRejected("Select an existing deployment binding.", "SELECTION_UNRESOLVED")
            for field in ("targetId", "realizationClass", "artifactIds", "resourceIds"):
                if field in edit:
                    bindings[0][field] = deepcopy(edit[field])
            touched.add(name)
        elif kind == "rename_display_label":
            # XDL metadata.description is a display label; logical metadata.name is never renamed implicitly.
            if not explicit:
                raise XDLRejected("Choose the resource document whose display description should change.", "INVALID_EDIT")
            check_target(edit, parsed[explicit])
            label = edit.get("label", edit.get("name"))
            if not isinstance(label, str) or not 1 <= len(label) <= 500:
                raise XDLRejected("A display description must contain one to 500 characters.", "INVALID_EDIT")
            parsed[explicit]["metadata"]["description"] = label
            touched.add(explicit)

    result = dict(documents)
    for name in touched:
        stream = StringIO()
        yaml.dump(parsed[name], stream)
        result[name] = stream.getvalue()
    after = XDLAdapter().validate(result)
    if not after["valid"]:
        codes = ", ".join(dict.fromkeys(d["code"] for d in after["diagnostics"][:5]))
        raise XDLRejected("The authoritative validator rejected this edit transaction: " + codes, "MODEL_INVALID")
    return result
