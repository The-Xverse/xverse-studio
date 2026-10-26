"""Transactional semantic edits to authored XDL, using the public validator after editing."""

from copy import deepcopy
from io import StringIO
import math
import re

from ruamel.yaml import YAML

from . import XDLAdapter, XDLRejected
from .examples import API_VERSION, CONNECTIONS_NAMESPACE, CONNECTIONS_SCHEMA_ID, PROFILE_NAMESPACE
from .edit_limits import check_edit_payload

REGISTRY = {
    "set_scenario_conditions": {"documentId", "elementRef", "properties"},
    "set_assessment_definitions": {"documentId", "elementRef", "definitions"},
    "add_scenario_item": {"documentId", "elementRef", "itemKind", "itemId", "properties"},
    "update_scenario_item": {"documentId", "elementRef", "itemKind", "itemId", "properties"},
    "remove_scenario_item": {"documentId", "elementRef", "itemKind", "itemId"},
    "set_parameter": {"documentId", "parameterId", "parameter", "value", "elementRef", "elementId"},
    "add_element": {"documentId", "templateId", "elementId", "nodeId", "parameterValues"},
    "add_logical_asset": {"documentId", "assetKind", "elementId", "elementRef", "properties", "endpoints"},
    "update_logical_asset": {"documentId", "assetKind", "elementId", "elementRef", "properties", "unsetProperties"},
    "remove_element": {"documentId", "elementId", "elementRef", "removalSet"},
    "connect_endpoints": {"documentId", "flowId", "sourceEndpointId", "destinationEndpointIds", "interfaceId", "timeDomainId", "deliveryIntent"},
    "disconnect_flow": {"documentId", "flowId", "elementRef"},
    "set_binding": {"documentId", "bindingId", "targetId", "realizationClass", "artifactIds", "resourceIds"},
    "add_binding": {"documentId", "bindingId", "elementId", "targetId", "realizationClass", "artifactIds"},
    "rename_display_label": {"documentId", "label", "name", "elementRef"},
    "set_time_mapping": {"documentId", "mappingId", "sourceTimeDomainId", "targetTimeDomainId", "mapping", "tolerance", "remove"},
    "set_flow_contract": {"documentId", "flowId", "causality", "converter"},
}
IDENTIFIER = re.compile(r"^[a-z][a-z0-9]*(?:-[a-z0-9]+)*$")
ASSET_COLLECTIONS = {"device": "devices", "sensor": "sensors", "actuator": "actuators", "model": "models"}
REALIZATION_CLASSES = ("simulated", "virtual", "physical", "hybrid")
# Only System members that can be realized by a deployment binding.
REALIZABLE = ("componentInstances", "devices", "sensors", "actuators", "models")
ASSET_OPTIONAL_FIELDS = {"device": {"nodeId", "extensions"}, "sensor": {"deviceId", "samplingIntent"},
                         "actuator": {"deviceId", "limits"}, "model": {"limitations"}}


def _has_identifier(spec, identifier):
    return any(value.get("id") == identifier for values in spec.values() if isinstance(values, list)
               for value in values if isinstance(value, dict))


def _check_asset_ports(spec, asset_kind, asset):
    """Guide typed authoring without replacing the public full-document validator."""
    ports = {value["id"]: value for value in spec.get("endpoints", []) if isinstance(value, dict) and "id" in value}
    references = []
    if asset_kind == "sensor":
        references = [(asset.get("outputEndpointId"), "output")]
    elif asset_kind == "actuator":
        references = [(asset.get("inputEndpointId"), "input")]
    # Model inputs/outputs reference interfaces, not endpoints; the public
    # validator checks their membership without inventing endpoint semantics.
    for identifier, direction in references:
        if not isinstance(identifier, str) or identifier not in ports:
            raise XDLRejected("Select an existing declared endpoint for this logical asset.", "ENDPOINT_UNRESOLVED")
        if ports[identifier].get("direction") not in (direction, "bidirectional"):
            raise XDLRejected("The selected endpoint direction is incompatible with this logical asset port.", "ENDPOINT_INCOMPATIBLE")


def semantic_edits(documents: dict[str, str], edits: list[dict]) -> dict[str, str]:
    """Return a new complete source transaction, or refuse without altering the inputs.

    Semantic authoring requires an already valid set. Unknown/unresolved extensions remain
    available through exact source editing, but cannot be silently rewritten by this helper.
    """
    if not isinstance(edits, list) or not 0 < len(edits) <= 100:
        raise XDLRejected("A semantic transaction needs one to 100 edits.", "LIMIT_EXCEEDED")
    adapter = XDLAdapter()
    report = adapter.validate(documents)
    if not report["valid"]:
        raise XDLRejected("Resolve authoritative source diagnostics before applying semantic edits; original source is preserved.", "MODEL_INVALID")
    yaml = YAML()
    yaml.preserve_quotes = True
    parsed = {name: yaml.load(source) for name, source in documents.items()}
    touched = set()
    asset_targets = []
    check_assessments = False

    def resource_uri(resource):
        return f"xdl://{resource['metadata']['namespace']}/{resource['kind'].lower()}/{resource['metadata']['name']}"

    def check_target(edit, resource, identifier=None):
        target = edit.get("elementRef")
        allowed = {resource_uri(resource)}
        if identifier:
            allowed.add(resource_uri(resource) + "#" + identifier)
        if target is not None and (not isinstance(target, str) or target not in allowed):
            raise XDLRejected("The selected stable reference does not identify this edit target.", "SELECTION_UNRESOLVED")

    def select(kind: str, explicit: str | None) -> tuple[str, dict]:
        found = [(name, value) for name, value in parsed.items() if value.get("kind") == kind and (not explicit or name == explicit)]
        if len(found) != 1:
            raise XDLRejected("Select exactly one existing " + kind + " document.", "SELECTION_UNRESOLVED")
        return found[0]

    for edit in edits:
        if not isinstance(edit, dict) or not isinstance(edit.get("kind"), str) or edit.get("kind") not in REGISTRY:
            raise XDLRejected("This semantic edit operation is unsupported.")
        kind = edit["kind"]
        check_edit_payload(edit)
        if set(edit) - REGISTRY[kind] - {"kind"}:
            raise XDLRejected("Unknown fields in the semantic edit envelope.", "INVALID_EDIT")
        explicit = edit.get("documentId")
        if explicit is not None and (not isinstance(explicit, str) or explicit not in parsed):
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
        elif kind in {"set_scenario_conditions", "set_assessment_definitions", "add_scenario_item", "update_scenario_item", "remove_scenario_item"}:
            from xverse_studio.experiments.authoring import edit_scenario
            name, resource = select("Scenario", explicit)
            check_target(edit, resource, edit.get("itemId"))
            edit_scenario(resource, edit)
            check_assessments = True
            touched.add(name)
        elif kind in {"add_logical_asset", "update_logical_asset"}:
            name, system = select("System", explicit)
            spec = system["spec"]
            asset_kind, identifier, properties = edit.get("assetKind"), edit.get("elementId"), edit.get("properties")
            if not isinstance(asset_kind, str) or asset_kind not in ASSET_COLLECTIONS:
                raise XDLRejected("Choose a supported logical device, sensor, actuator or model reference.", "INVALID_EDIT")
            if not isinstance(identifier, str) or not IDENTIFIER.fullmatch(identifier) or len(identifier) > 63:
                raise XDLRejected("Choose a valid stable logical asset ID.", "INVALID_EDIT")
            unset = edit.get("unsetProperties", [])
            if (not isinstance(unset, list) or len(unset) > 8 or any(not isinstance(field, str) for field in unset)
                    or len(set(unset)) != len(unset) or any(field not in ASSET_OPTIONAL_FIELDS[asset_kind] for field in unset)):
                raise XDLRejected("Only schema-optional properties of this asset kind can be explicitly unset.", "INVALID_EDIT")
            if not isinstance(properties, dict) or (not properties and not unset) or "id" in properties or any(field in properties for field in unset):
                raise XDLRejected("Supply XDL properties separately from the immutable element ID.", "INVALID_EDIT")
            check_target(edit, system, identifier)
            collection = ASSET_COLLECTIONS[asset_kind]
            if kind == "add_logical_asset":
                if _has_identifier(spec, identifier):
                    raise XDLRejected("The element ID already belongs to this System.", "IDENTITY_CONFLICT")
                asset = {"id": identifier, **deepcopy(properties)}
                spec.setdefault(collection, []).append(asset)
                endpoints = edit.get("endpoints", [])
                if not isinstance(endpoints, list) or len(endpoints) > 64 or (endpoints and asset_kind != "device"):
                    raise XDLRejected("Only a logical device can declare a bounded bundle of owned endpoints.", "INVALID_EDIT")
                for endpoint in endpoints:
                    if not isinstance(endpoint, dict) or endpoint.get("ownerId") != identifier:
                        raise XDLRejected("Bundled endpoints must belong to the new logical device.", "INVALID_EDIT")
                    endpoint_id = endpoint.get("id")
                    if not isinstance(endpoint_id, str) or not IDENTIFIER.fullmatch(endpoint_id) or len(endpoint_id) > 63:
                        raise XDLRejected("Choose a valid stable endpoint ID.", "INVALID_EDIT")
                    if _has_identifier(spec, endpoint_id):
                        raise XDLRejected("An endpoint ID already belongs to this System.", "IDENTITY_CONFLICT")
                    spec.setdefault("endpoints", []).append(deepcopy(endpoint))
            else:
                matches = [value for value in spec.get(collection, []) if value.get("id") == identifier]
                if len(matches) != 1:
                    raise XDLRejected("Select an existing logical asset of the specified kind.", "SELECTION_UNRESOLVED")
                asset = matches[0]
                asset.update(deepcopy(properties))
                for field in unset:
                    asset.pop(field, None)
            asset_targets.append((spec, asset_kind, asset))
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
            values = edit.get("parameterValues")
            if values is not None:
                # Configuration names declared definition parameters with values of their declared type.
                declared = {p.get("id"): p for p in definition["spec"].get("parameters", []) if isinstance(p, dict)}
                types = {"number": (int, float), "integer": (int,), "string": (str,), "boolean": (bool,)}
                if not isinstance(values, dict) or not values or not set(values) <= set(declared):
                    raise XDLRejected("Configure only parameters the definition declares.", "PARAMETER_UNRESOLVED")
                for key, value in values.items():
                    expected = types.get(declared[key].get("valueType"))
                    if expected and (not isinstance(value, expected) or (bool not in expected and isinstance(value, bool))):
                        raise XDLRejected(f"Parameter {key} needs a {declared[key].get('valueType')} value.", "INVALID_EDIT")
                    if declared[key].get("mutability") == "constant":
                        raise XDLRejected(f"Parameter {key} is constant.", "PARAMETER_IMMUTABLE")
                instance["parameterValues"] = deepcopy(values)
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
        elif kind == "add_binding":
            # Realization is a Deployment binding, chosen separately from role and placement.
            name, deployment = select("Deployment", explicit)
            spec = deployment["spec"]
            binding_id, element_id = edit.get("bindingId"), edit.get("elementId")
            if not all(isinstance(v, str) and IDENTIFIER.fullmatch(v) and len(v) <= 63 for v in (binding_id, element_id)):
                raise XDLRejected("A binding needs valid binding and element identifiers.", "INVALID_EDIT")
            if edit.get("realizationClass") not in REALIZATION_CLASSES:
                raise XDLRejected("Choose a declared realization class.", "INVALID_EDIT")
            if any(v.get("id") == binding_id for v in spec.get("bindings", []) if isinstance(v, dict)):
                raise XDLRejected("The binding ID already belongs to this Deployment.", "IDENTITY_CONFLICT")
            targets = [v for v in spec.get("targets", []) if isinstance(v, dict) and v.get("id") == edit.get("targetId")]
            if len(targets) != 1 or not isinstance(targets[0].get("lifecycle"), dict):
                raise XDLRejected("Select an existing deployment target with a declared lifecycle.", "SELECTION_UNRESOLVED")
            system_ref = spec.get("systemRef") or {}
            systems = [v for v in parsed.values() if v.get("kind") == "System"
                       and v["metadata"].get("namespace") == system_ref.get("namespace")
                       and v["metadata"].get("name") == system_ref.get("name")]
            if len(systems) != 1 or not any(
                isinstance(v, dict) and v.get("id") == element_id
                for collection in REALIZABLE for v in systems[0]["spec"].get(collection, []) or []
            ):
                raise XDLRejected("Choose a realizable element (component instance, device, sensor, actuator or model) "
                                  "declared by the Deployment's System.", "SELECTION_UNRESOLVED")
            if any(isinstance(v, dict) and (v.get("logicalRef") or {}).get("element") == element_id
                   and (v.get("logicalRef") or {}).get("name") == system_ref.get("name")
                   and (v.get("logicalRef") or {}).get("namespace") == system_ref.get("namespace")
                   for v in spec.get("bindings", [])):
                raise XDLRejected("This element is already realized in this Deployment; change that binding instead.",
                                  "REALIZATION_CONFLICT")
            artifacts = edit.get("artifactIds", [])
            known = {v.get("id") for v in spec.get("artifacts", []) if isinstance(v, dict)}
            if (not isinstance(artifacts, list) or not all(isinstance(a, str) for a in artifacts)
                    or len(set(artifacts)) != len(artifacts) or not set(artifacts) <= known):
                raise XDLRejected("Choose declared Deployment artifacts; requirement is not choice.", "SELECTION_UNRESOLVED")
            binding = {
                "id": binding_id,
                "logicalRef": {"apiVersion": system_ref.get("apiVersion"), "kind": "System",
                               "namespace": system_ref.get("namespace"), "name": system_ref.get("name"),
                               "element": element_id},
                "realizationClass": edit["realizationClass"],
                "targetId": targets[0]["id"],
                "lifecycle": deepcopy(targets[0]["lifecycle"]),
            }
            if artifacts:
                binding["artifactIds"] = list(artifacts)
            spec.setdefault("bindings", []).append(binding)
            touched.add(name)
        elif kind == "set_time_mapping":
            # Adds, replaces (by id) or removes one Deployment clock mapping; the validator checks the domains.
            name, deployment = select("Deployment", explicit)
            spec = deployment["spec"]
            mapping_id = edit.get("mappingId")
            if not isinstance(mapping_id, str) or not IDENTIFIER.fullmatch(mapping_id) or len(mapping_id) > 63:
                raise XDLRejected("A time mapping needs a valid identifier.", "INVALID_EDIT")
            mappings = spec.get("timeMappings", [])
            existing = [index for index, value in enumerate(mappings) if isinstance(value, dict) and value.get("id") == mapping_id]
            if edit.get("remove") is True:
                if set(edit) - {"kind", "documentId", "mappingId", "remove"}:
                    raise XDLRejected("Removing a time mapping takes only its identifier.", "INVALID_EDIT")
                if not existing:
                    raise XDLRejected("Select an existing time mapping to remove.", "SELECTION_UNRESOLVED")
                spec["timeMappings"] = [value for index, value in enumerate(mappings) if index not in existing]
                if not spec["timeMappings"]:
                    del spec["timeMappings"]
            else:
                source, target = edit.get("sourceTimeDomainId"), edit.get("targetTimeDomainId")
                tolerance, text = edit.get("tolerance"), edit.get("mapping")
                if "remove" in edit and edit["remove"] is not False:
                    raise XDLRejected("remove must be a boolean.", "INVALID_EDIT")
                if not all(isinstance(v, str) and IDENTIFIER.fullmatch(v) and len(v) <= 63 for v in (source, target)) or source == target:
                    raise XDLRejected("Choose two different declared time domains.", "INVALID_EDIT")
                if not isinstance(text, str) or not 1 <= len(text) <= 200:
                    raise XDLRejected("Describe the mapping in one to 200 characters.", "INVALID_EDIT")
                if (not isinstance(tolerance, dict) or set(tolerance) != {"value", "unit"} or isinstance(tolerance["value"], bool)
                        or not isinstance(tolerance["value"], (int, float)) or not math.isfinite(tolerance["value"]) or tolerance["value"] < 0
                        or not isinstance(tolerance["unit"], str) or not 1 <= len(tolerance["unit"]) <= 32):
                    raise XDLRejected("A tolerance is a finite non-negative value with a unit.", "INVALID_EDIT")
                system_ref = spec["systemRef"]
                ref = {"apiVersion": system_ref.get("apiVersion"), "kind": "System", "namespace": system_ref.get("namespace"), "name": system_ref.get("name")}
                value = {"id": mapping_id, "sourceTimeDomainRef": {**ref, "element": source}, "targetTimeDomainRef": {**ref, "element": target},
                         "mapping": text, "tolerance": {"value": tolerance["value"], "unit": tolerance["unit"]}}
                if existing:
                    mappings[existing[0]] = value
                else:
                    spec.setdefault("timeMappings", []).append(value)
            touched.add(name)
        elif kind == "set_flow_contract":
            # Declares (or removes) a flow's owned connection contract (ADR-0016). Admission and the
            # provider decide whether it is admitted; nothing is converted or delayed by this edit.
            name, system = select("System", explicit)
            flows = [f for f in system["spec"].get("flows", []) if isinstance(f, dict) and f.get("id") == edit.get("flowId")]
            if len(flows) != 1:
                raise XDLRejected("Select one existing flow.", "SELECTION_UNRESOLVED")
            payload = {}
            causality, converter = edit.get("causality"), edit.get("converter")
            if causality is not None:
                if causality != "unit-delay":
                    raise XDLRejected("The only declarable causality is unit-delay.", "INVALID_EDIT")
                payload["causality"] = {"kind": "unit-delay"}
            if converter is not None:
                if (not isinstance(converter, dict) or set(converter) != {"fromUnit", "toUnit", "scale", "offset"}
                        or not all(isinstance(converter[k], str) and 1 <= len(converter[k]) <= 64 for k in ("fromUnit", "toUnit"))
                        or not all(not isinstance(converter[k], bool) and isinstance(converter[k], (int, float)) and math.isfinite(converter[k])
                                   for k in ("scale", "offset"))):
                    raise XDLRejected("A linear converter needs fromUnit, toUnit, and finite scale and offset.", "INVALID_EDIT")
                payload["converter"] = {"kind": "linear", **{k: converter[k] for k in ("fromUnit", "toUnit", "scale", "offset")}}
            extensions = flows[0].get("extensions") or {}
            if payload:
                extensions[CONNECTIONS_NAMESPACE] = payload
                flows[0]["extensions"] = extensions
                if not any(value.get("kind") == "Profile" and (value.get("spec") or {}).get("extensionNamespace") == CONNECTIONS_NAMESPACE
                           for value in parsed.values()):
                    namespace = system["metadata"]["namespace"]
                    path = "xdl/connections-profile.xdl.yaml"
                    if path in parsed:
                        raise XDLRejected("A document already uses the connections profile path.", "IDENTITY_CONFLICT")
                    parsed[path] = {"apiVersion": API_VERSION, "kind": "Profile",
                                    "metadata": {"namespace": namespace, "name": "studio-connections", "version": "1.0.0",
                                                 "description": "Owned connection contracts (ADR-0016).",
                                                 "provenance": {"source": "urn:xverse:studio:connections", "revision": "1.0.0",
                                                                "maturity": "prototype",
                                                                "limitations": ["Admitted only where the selected provider declares and executes the contract."]}},
                                    "spec": {"extensionNamespace": CONNECTIONS_NAMESPACE, "compatibleApiVersions": [API_VERSION],
                                             "schemaRef": CONNECTIONS_SCHEMA_ID, "documentationRef": "urn:xverse:studio:connections:1.0",
                                             "conflictPolicy": "reject"}}
                    touched.add(path)
            else:
                extensions.pop(CONNECTIONS_NAMESPACE, None)
                if extensions:
                    flows[0]["extensions"] = extensions
                else:
                    flows[0].pop("extensions", None)
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

    for spec, asset_kind, asset in asset_targets:
        _check_asset_ports(spec, asset_kind, asset)
    result = dict(documents)
    for name in touched:
        stream = StringIO()
        yaml.dump(parsed[name], stream)
        result[name] = stream.getvalue()
    after = adapter.validate(result)
    if not after["valid"]:
        codes = ", ".join(dict.fromkeys(d["code"] for d in after["diagnostics"][:5]))
        raise XDLRejected("The authoritative validator rejected this edit transaction: " + codes, "MODEL_INVALID")
    if check_assessments:
        from xverse_studio.assertions.snapshot import source_definitions
        from xverse_studio.assertions import EvaluationError
        try:
            source_definitions(result, adapter)
        except EvaluationError as exc:
            raise XDLRejected("The retained assessment references are unresolved: " + str(exc), str(exc)) from None
    return result
