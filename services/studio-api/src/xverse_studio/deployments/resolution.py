"""Deployment resolution 1.0 (ADR-0015): binding compatibility, placement constraints, effective values
and environment bindings for one selected Deployment.

The pinned XDL validator owns reference integrity (targets, artifacts, resources, networks and time
domains exist). It treats `parameterValues` as opaque and defines no precedence between instance and
binding values, does not compare Component requirements with bound artifacts/resources, and does not
interpret placement. This module evaluates only what declarations state; an undecidable requirement is
`unknown`, never a pass, and nothing here rewrites sources, converts units or resolves secrets.
"""
from __future__ import annotations

import math
import re
from urllib.parse import urlsplit

from copy import deepcopy
from ruamel.yaml import YAML

from xverse_studio.xdl.examples import PARAMETERS, PROFILE_NAMESPACE

RESOLUTION_VERSION = "1.0"
BLOCKING = {"fail", "unknown", "unsupported", "ambiguous", "unresolved"}


def declared_time_mappings(deployment, resources):
    """Project both selected v1alpha1 shapes without inventing Scenario mapping IDs."""

    def resource_ref(resource):
        return _authored({**resource["metadata"], "kind": resource["kind"]})

    deployment_ref = resource_ref(deployment)
    owners = [(deployment, "deployment")]
    owners.extend(
        (resource, "scenario")
        for resource in sorted(
            (r for r in resources if r.get("kind") == "Scenario"), key=resource_ref
        )
        if resource["spec"].get("deploymentRef")
        and _authored(resource["spec"]["deploymentRef"]) == deployment_ref
    )
    for owner, origin in owners:
        for index, mapping in enumerate(owner["spec"].get("timeMappings", []) or []):
            if origin == "deployment":
                source, target = (
                    mapping["sourceTimeDomainRef"],
                    mapping["targetTimeDomainRef"],
                )
                mapping_id = mapping["id"]
            else:
                source = {
                    **owner["spec"]["systemRef"],
                    "element": mapping["sourceTimeDomainId"],
                }
                target = {
                    **owner["spec"]["systemRef"],
                    "element": mapping["targetTimeDomainId"],
                }
                mapping_id = None
            yield dict(
                mappingId=mapping_id,
                origin=origin,
                ownerRef=resource_ref(owner),
                pointer=f"/spec/timeMappings/{index}",
                sourceTimeDomainRef=deepcopy(source),
                targetTimeDomainRef=deepcopy(target),
                mapping=mapping["mapping"],
                tolerance=deepcopy(mapping["tolerance"]),
            )


def clock_ref(reference):
    return _authored(reference) + "#" + reference.get("element", "")


_COLLECTIONS = ("componentInstances", "nodes", "devices", "sensors", "actuators", "models")
_EXACT_VERSION = re.compile(r"^\d+\.\d+\.\d+(?:[-+][0-9A-Za-z.+-]+)?$")
_WINDOWS_PATH = re.compile(r"^[A-Za-z]:[\\/]")
# Absolute POSIX text is only treated as a host path under conventional filesystem roots, so that
# topics, routes and other slash-separated names are never mistaken for host paths.
_POSIX_ROOTS = re.compile(r"^/(?:home|Users|opt|usr|var|etc|tmp|mnt|media|srv|root|private|Volumes)(?:/|$)")
_SECRET_KEYS = re.compile(r"(?:^|[?&#;])(?:password|passwd|pwd|secret|token|access_token|apikey|api_key|key|auth|credential)s?=",
                          re.IGNORECASE)
_URI = re.compile(r"^[A-Za-z][A-Za-z0-9+.-]*:")


def _ref(resource):
    return f"xdl://{resource['metadata']['namespace']}/{resource['kind'].lower()}/{resource['metadata']['name']}"


def _authored(reference):
    return f"xdl://{reference['namespace']}/{reference['kind'].lower()}/{reference['name']}"


def _check(check, status, message, code=None, **facts):
    return {"check": check, "status": status, "message": message, **({"code": code} if code else {}), **facts}


def _number(value):
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value)


def _typed(value, value_type):
    """JSON Schema type semantics: an integer is any number with a zero fractional part."""
    if value_type == "integer":
        return _number(value) and float(value).is_integer()
    if value_type == "number":
        return _number(value)
    return isinstance(value, {"boolean": bool, "string": str, "object": dict, "array": list}.get(value_type, ()))


def _same(left, right):
    """JSON value equality: 1 and 1.0 are the same number; booleans are not numbers."""
    if _number(left) and _number(right):
        return float(left) == float(right)
    if isinstance(left, dict) and isinstance(right, dict):
        return left.keys() == right.keys() and all(_same(left[k], right[k]) for k in left)
    if isinstance(left, list) and isinstance(right, list):
        return len(left) == len(right) and all(_same(a, b) for a, b in zip(left, right))
    return type(left) is type(right) and left == right


def credential_free(text):
    """(display text, carried credentials) for one reference; userinfo and secret-like query or
    fragment parameters are credential material and are never echoed."""
    if not isinstance(text, str):
        return text, False
    if not _URI.match(text):
        # Connection strings such as `user=a;password=b` carry credentials without a URI.
        return ("[redacted]", True) if _SECRET_KEYS.search(";" + text) else (text, False)
    try:
        parts = urlsplit(text)
    except ValueError:
        return "[redacted]", True
    userinfo = "@" in parts.netloc
    secret = bool(_SECRET_KEYS.search("?" + parts.query)) or bool(_SECRET_KEYS.search("#" + parts.fragment))
    if not (userinfo or secret):
        return text, False
    host = parts.netloc.rsplit("@", 1)[-1]
    return f"{parts.scheme}://{host}{parts.path}" if parts.netloc else f"{parts.scheme}:{parts.path}", True


def _scrub(value, pointer, findings):
    """Copy of an authored value with credential material removed; findings name its location."""
    if isinstance(value, str):
        shown, carried = credential_free(value)
        if carried:
            findings.append(pointer)
        return shown
    if isinstance(value, dict):
        return {key: _scrub(item, f"{pointer}/{key}", findings) for key, item in value.items()}
    if isinstance(value, list):
        return [_scrub(item, f"{pointer}/{index}", findings) for index, item in enumerate(value)]
    return value


def _host_style(text):
    """`windows`, `posix` or `network` for host-specific path text; None for anything else."""
    if not isinstance(text, str):
        return None
    if _WINDOWS_PATH.match(text) or text.startswith("\\\\"):
        return "network" if text.startswith("\\\\") else "windows"
    if text.lower().startswith("file:"):
        parts = urlsplit(text)
        if parts.netloc and parts.netloc.lower() != "localhost":
            return "network"
        path = parts.path
        return "windows" if re.match(r"^/?[A-Za-z]:[\\/]", path) else "posix" if path.startswith("/") else None
    if _POSIX_ROOTS.match(text):
        return "posix"
    return None


def _os_style(name):
    return "windows" if name == "Windows" else "posix" if name else None


def _strings(value, pointer):
    if isinstance(value, str):
        yield pointer, value
    elif isinstance(value, dict):
        for key, item in value.items():
            yield from _strings(item, f"{pointer}/{key}")
    elif isinstance(value, list):
        for index, item in enumerate(value):
            yield from _strings(item, f"{pointer}/{index}")


def _parameter_chain(element, definition, bindings, system_path, deployment_path, leaked):
    parameters = (definition or {}).get("spec", {}).get("parameters", []) or []
    declared = {p["id"]: (index, p) for index, p in enumerate(parameters) if isinstance(p, dict) and "id" in p}
    layers = {}
    if element.get("_collection"):
        base = f"/spec/{element['_collection']}/{element['_index']}/parameterValues"
        for key, value in (element.get("parameterValues") or {}).items():
            layers.setdefault(key, []).append({"layer": "system-instance", "documentId": system_path,
                                               "pointer": f"{base}/{key}", "value": value})
    for index, binding in bindings:
        for key, value in (binding.get("parameterValues") or {}).items():
            layers.setdefault(key, []).append({"layer": "deployment-binding", "documentId": deployment_path, "bindingId": binding["id"],
                                               "pointer": f"/spec/bindings/{index}/parameterValues/{key}", "value": value})
    result = []
    for identifier in sorted(set(declared) | set(layers)):
        index, schema = declared.get(identifier, (None, None))
        authored = layers.get(identifier, [])
        chain = ([{"layer": "definition-default", "documentId": definition.get("_path"),
                   "pointer": f"/spec/parameters/{index}/default", "value": schema["default"]}]
                 if schema and "default" in schema else []) + authored
        entry = {"elementId": element["id"], "parameterId": identifier, "chain": chain,
                 "valueType": schema.get("valueType") if schema else None, "unitSemantics": schema.get("unitSemantics") if schema else None,
                 "mutability": schema.get("mutability") if schema else None, "effective": None}
        if schema is None:
            entry.update(status="unsupported", code="PARAMETER_UNDECLARED",
                         message=f"{identifier} is not declared by a definition of this element; its value is preserved but not interpreted.")
        elif len(authored) > 1:
            entry.update(status="ambiguous", code="PRECEDENCE_UNDEFINED",
                         message=f"{identifier} is authored in {len(authored)} places ({', '.join(a['layer'] for a in authored)}); "
                                 "XDL defines no precedence between them. Keep exactly one authored value.")
        elif authored:
            value = authored[0]["value"]
            if not _typed(value, schema["valueType"]):
                entry.update(status="fail", code="PARAMETER_INVALID", message=f"{identifier} must be a {schema['valueType']} value.")
            elif schema["mutability"] == "constant" and "default" in schema and not _same(value, schema["default"]):
                entry.update(status="fail", code="PARAMETER_IMMUTABLE", message=f"{identifier} is declared constant; its default cannot be replaced.")
            else:
                entry.update(status="overridden" if "default" in schema else "authored", effective=value,
                             source=authored[0]["layer"],
                             message="The single authored value applies; a declared default applies only when no value is authored.")
        elif "default" in schema:
            entry.update(status="default", effective=schema["default"], source="definition-default", message="No value is authored; the declared default applies.")
        else:
            entry.update(status="unset", message="No value or default is declared; the provider's behaviour for this parameter is not established.")
        for layer in entry["chain"]:
            layer["value"] = _scrub(layer["value"], f"{layer['documentId']}#{layer['pointer']}", leaked)
        entry["effective"] = _scrub(entry["effective"], "effective", [])
        result.append(entry)
    return result


def resolve_deployment(documents, deployment_ref, host_os=None, provider=None):
    """Return the resolution report for one Deployment of a structurally valid source set."""
    yaml = YAML(typ="safe")
    parsed = {}
    for path, source in documents.items():
        try:
            resource = yaml.load(source)
        except Exception:
            continue
        if isinstance(resource, dict) and isinstance(resource.get("metadata"), dict) and isinstance(resource.get("spec"), dict):
            resource["_path"] = path
            parsed[_ref(resource)] = resource
    deployment = parsed.get(deployment_ref)
    if deployment is None or deployment.get("kind") != "Deployment":
        return None
    spec = deployment["spec"]
    system = parsed.get(_authored(spec["systemRef"])) or {"spec": {}, "_path": None}
    system_spec = system["spec"]
    elements = {}
    for collection in _COLLECTIONS:
        for index, element in enumerate(system_spec.get(collection, []) or []):
            if isinstance(element, dict) and "id" in element:
                elements[element["id"]] = {**element, "_collection": collection, "_index": index}
    targets = {t["id"]: t for t in spec.get("targets", [])}
    artifacts = {a["id"]: a for a in spec.get("artifacts", [])}
    resources = {r["id"]: r for r in spec.get("resources", [])}
    leaked = []
    binding_rows = []
    for binding in spec.get("bindings", []):
        element = elements.get(binding["logicalRef"].get("element"))
        target = targets.get(binding["targetId"], {})
        definition = parsed.get(_authored(element["componentRef"])) if element and element.get("componentRef") else None
        realization, target_class = binding["realizationClass"], target.get("targetClass")
        # Realization and placement are independent XDL dimensions; only a selected provider's
        # declared realization/target classes can rule on them.
        offered_classes = {"realization": ((provider or {}).get("realizationClasses"), realization),
                           "target": ((provider or {}).get("targetClasses"), target_class)}
        if provider is None or not any(declared is not None for declared, _ in offered_classes.values()):
            checks = [_check("realization", "declared", f"{realization} realization placed on a {target_class} target; no selected provider declares which classes it supports.")]
        else:
            missing = [f"{kind} class {value}" for kind, (declared, value) in offered_classes.items() if declared is not None and value not in declared]
            checks = [_check("realization", "unsupported", f"Provider {provider.get('providerId')} does not declare support for {' or '.join(missing)}.", "CAPABILITY_UNSUPPORTED")
                      if missing else
                      _check("realization", "pass", f"Provider {provider.get('providerId')} declares support for {realization} realization on {target_class} targets.")]
        if binding.get("resourceIds") and "offeredResourceIds" not in target:
            checks.append(_check("placement", "unknown", f"Target {binding['targetId']} does not declare the resources it offers.", "COMPATIBILITY_UNKNOWN"))
        else:
            offered = set(target.get("offeredResourceIds", []))
            for resource_id in binding.get("resourceIds", []):
                if resource_id in offered:
                    checks.append(_check("placement", "pass", f"Target {binding['targetId']} offers resource {resource_id}.", resourceId=resource_id))
                else:
                    checks.append(_check("placement", "fail", f"Target {binding['targetId']} does not offer resource {resource_id}.", "RESOURCE_NOT_OFFERED", resourceId=resource_id))
        bound_artifacts = [artifacts[a] for a in binding.get("artifactIds", []) if a in artifacts]
        bound_resources = [resources[r] for r in binding.get("resourceIds", []) if r in resources]
        for requirement in (definition or {}).get("spec", {}).get("artifactRequirements", []) or []:
            kind = [a for a in bound_artifacts if a["artifactKind"] == requirement["artifactKind"]]
            constraint = requirement["versionConstraint"]
            facts = {"requirementId": requirement["id"]}
            if not kind:
                checks.append(_check("artifact", "fail", f"No bound {requirement['artifactKind']} artifact satisfies requirement {requirement['id']}.", "ARTIFACT_REQUIREMENT_UNMET", **facts))
            elif constraint == "*" or any(a["version"] == constraint for a in kind):
                checks.append(_check("artifact", "pass", f"Requirement {requirement['id']} is met by an exact or unconstrained version.", **facts))
            elif _EXACT_VERSION.match(constraint):
                checks.append(_check("artifact", "fail", f"Requirement {requirement['id']} needs exactly {constraint}; bound {', '.join(a['version'] for a in kind)}.", "ARTIFACT_REQUIREMENT_UNMET", **facts))
            else:
                checks.append(_check("artifact", "unknown", f"Version constraint {constraint!r} has no admitted evaluator; compatibility is not established.", "COMPATIBILITY_UNKNOWN", **facts))
        for requirement in (definition or {}).get("spec", {}).get("resourceRequirements", []) or []:
            minimum = requirement["minimum"]
            facts = {"requirementId": requirement["id"]}
            same_class = [r for r in bound_resources if r["resourceClass"] == requirement["resourceClass"]]
            comparable = [r for r in same_class if r["capacity"]["unit"] == minimum["unit"]]
            if not same_class:
                checks.append(_check("resource", "fail", f"No bound {requirement['resourceClass']} resource satisfies requirement {requirement['id']}.", "RESOURCE_REQUIREMENT_UNMET", **facts))
            elif any(r["capacity"]["value"] >= minimum["value"] for r in comparable):
                checks.append(_check("resource", "pass", f"Requirement {requirement['id']} is met in {minimum['unit']}.", **facts))
            elif len(comparable) < len(same_class):
                checks.append(_check("resource", "unknown", f"Some bound capacity uses a unit other than {minimum['unit']}; no unit conversion is admitted.", "COMPATIBILITY_UNKNOWN", **facts))
            else:
                checks.append(_check("resource", "fail", f"Bound capacity is below the required {minimum['value']} {minimum['unit']}.", "RESOURCE_REQUIREMENT_UNMET", **facts))
        statuses = {c["status"] for c in checks}
        status = next((s for s in ("fail", "unsupported", "unknown") if s in statuses), "compatible")
        binding_rows.append({"bindingId": binding["id"], "elementId": binding["logicalRef"].get("element"),
                             "elementRef": _authored(binding["logicalRef"]) + "#" + str(binding["logicalRef"].get("element")),
                             "realizationClass": realization, "targetId": binding["targetId"], "targetClass": target_class,
                             "definitionRef": _authored(element["componentRef"]) if element and element.get("componentRef") else None,
                             "status": status, "checks": checks})
    constraints = []
    for resource in spec.get("resources", []):
        users = [b["id"] for b in spec.get("bindings", []) if resource["id"] in b.get("resourceIds", [])]
        if resource["allocationPolicy"] == "exclusive" and len(users) > 1:
            constraints.append(_check("resource", "fail", f"Exclusive resource {resource['id']} is bound by {', '.join(users)}.", "RESOURCE_CONFLICT", resourceId=resource["id"]))
        else:
            constraints.append(_check("resource", "declared", f"Resource {resource['id']} ({resource['allocationPolicy']}) is bound by {len(users)} binding(s); availability is checked at admission by the provider.", resourceId=resource["id"]))
    # Time: a simulator clock must be related to the System's reference clock through declared mappings
    # (this Deployment's, or a Scenario's authored for it); accuracy of a mapping is never evaluated.
    domains = [d.get("id") for d in system_spec.get("timeDomains", []) or [] if isinstance(d, dict)]
    reference = system_spec.get("defaultTimeDomainId") or (domains[0] if len(domains) == 1 else None)
    mappings = declared_time_mappings(deployment, parsed.values())
    links = {}
    for mapping in mappings:
        source, target = clock_ref(mapping['sourceTimeDomainRef']), clock_ref(mapping['targetTimeDomainRef'])
        links.setdefault(source, set()).add(target)
        links.setdefault(target, set()).add(source)
        label = mapping['mappingId'] or mapping['ownerRef'] + mapping['pointer']
        origin = {key: mapping[key] for key in ('mappingId', 'origin', 'ownerRef', 'pointer')}
        if _number(mapping["tolerance"]["value"]) and mapping["tolerance"]["value"] < 0:
            constraints.append(_check("time", "fail", f"Time mapping {label} declares a negative tolerance.", "CLOCK_MAPPING_INVALID", **origin))
        else:
            constraints.append(_check("time", "declared", f"Time mapping {label} ({mapping['mapping']}) is recorded; its accuracy is not evaluated.", **origin))

    def related(domain, goal):
        seen, frontier = {domain}, [domain]
        while frontier:
            current = frontier.pop()
            if current == goal:
                return True
            for nxt in links.get(current, ()):
                if nxt not in seen:
                    seen.add(nxt)
                    frontier.append(nxt)
        return False
    for simulator in spec.get("simulators", []):
        domain = simulator["timeDomainId"]
        qualified_domain = _authored(spec['systemRef']) + '#' + domain
        if reference is None:
            if not links.get(qualified_domain):
                constraints.append(_check("time", "unknown", f"Simulator {simulator['id']} runs in {domain}, but the System has no default time domain to relate it to.", "COMPATIBILITY_UNKNOWN", simulatorId=simulator["id"]))
        elif domain != reference and not related(qualified_domain, _authored(spec['systemRef']) + '#' + reference):
            constraints.append(_check("time", "fail", f"Simulator {simulator['id']} runs in {domain} with no mapping path to {reference}.", "CLOCK_MAPPING_MISSING", simulatorId=simulator["id"]))
    bound_networks = {}
    for network_binding in spec.get("networkBindings", []):
        bound_networks.setdefault(network_binding["logicalNetworkRef"].get("element"), []).append(network_binding["id"])
    for network in system_spec.get("networks", []) or []:
        ids = bound_networks.get(network["id"], [])
        if len(ids) > 1:
            constraints.append(_check("network", "fail", f"Network {network['id']} has {len(ids)} bindings ({', '.join(ids)}).", "NETWORK_BINDING_CONFLICT", networkId=network["id"]))
        elif ids:
            constraints.append(_check("network", "declared", f"Network {network['id']} is bound by {ids[0]}; transport behaviour is not evaluated.", networkId=network["id"]))
        else:
            constraints.append(_check("network", "declared", f"Network {network['id']} has no network binding in this deployment; only its logical declaration applies.", networkId=network["id"]))
    parameters = []
    bound_ids = {b["logicalRef"].get("element") for b in spec.get("bindings", [])}
    for element_id in [*(e for e, v in elements.items() if v["_collection"] == "componentInstances"), *sorted(bound_ids - set(elements))]:
        element = elements.get(element_id) or {"id": element_id}
        definition = parsed.get(_authored(element["componentRef"])) if element.get("componentRef") else None
        bindings = [(i, b) for i, b in enumerate(spec.get("bindings", [])) if b["logicalRef"].get("element") == element_id]
        parameters.extend(_parameter_chain(element, definition or {}, bindings, system.get("_path"), deployment["_path"], leaked))
    for element_id, element in elements.items():
        if element["_collection"] == "componentInstances":
            continue
        # Bound non-component members have no parameter declarations; any binding values are uninterpretable.
        bindings = [(i, b) for i, b in enumerate(spec.get("bindings", [])) if b["logicalRef"].get("element") == element_id and b.get("parameterValues")]
        if bindings or element.get("parameterValues"):
            parameters.extend(_parameter_chain(element, {}, bindings, system.get("_path"), deployment["_path"], leaked))
    for resource in parsed.values():
        if resource.get("kind") != "Scenario" or not resource["spec"].get("deploymentRef") or _authored(resource["spec"]["deploymentRef"]) != deployment_ref:
            continue
        for parameter in resource.get("extensions", {}).get(PROFILE_NAMESPACE, {}).get("parameters", []) or []:
            schema = next((p for p in PARAMETERS if p["id"] == parameter.get("id")), None)
            chain = ([{"layer": "profile-default", "value": schema["default"]}] if schema else []) + [
                {"layer": "scenario", "documentId": resource["_path"], "scenarioRef": _ref(resource), "value": parameter.get("value")}]
            parameters.append({"elementId": None, "scenarioRef": _ref(resource), "parameterId": parameter.get("id"), "chain": chain,
                               "valueType": parameter.get("valueType"), "unitSemantics": parameter.get("unitSemantics"),
                               "mutability": parameter.get("mutability"), "effective": parameter.get("value"), "source": "scenario",
                               "status": "overridden" if schema and not _same(parameter.get("value"), schema["default"]) else "default" if schema else "authored",
                               "message": "Declared by the owned reference profile: a Scenario value replaces the admitted parameter default."})
    environment, portability = [], []
    for target in spec.get("targets", []):
        if target.get("externalAssetRef"):
            shown, carried = credential_free(target["externalAssetRef"])
            environment.append({"kind": "asset", "ownerId": target["id"], "reference": shown,
                                "status": "fail" if carried else "unresolved", "code": "SECRET_INLINE" if carried else "BINDING_UNRESOLVED",
                                "message": "An asset reference may not carry credential material; keep it in a secret handle." if carried
                                else "No environment binding admits this asset reference; Studio does not resolve it."})
    for binding in spec.get("bindings", []):
        for reference in binding.get("secretRefs", []):
            shown, carried = credential_free(reference)
            environment.append({"kind": "secret", "ownerId": binding["id"], "reference": shown, "status": "fail" if carried else "unresolved",
                                "code": "SECRET_INLINE" if carried else "BINDING_UNRESOLVED",
                                "message": "A secret reference may not carry credential material; replace it with a handle." if carried
                                else "No environment binding resolves this secret handle; Studio never stores secret values."})
    for location in leaked:
        environment.append({"kind": "value", "ownerId": location, "reference": "[redacted]", "status": "fail", "code": "SECRET_INLINE",
                            "message": "An authored value carries credential material; replace it with a secret handle."})
    host_style = _os_style(host_os)
    supported = {_os_style(name) for name in (provider or {}).get("supportedHostOS", [])}
    scanned = [(f"/spec/artifacts/{i}/sourceRef", a["sourceRef"]) for i, a in enumerate(spec.get("artifacts", []))]
    for index, binding in enumerate(spec.get("bindings", [])):
        scanned.extend(_strings(binding.get("parameterValues") or {}, f"/spec/bindings/{index}/parameterValues"))
    for index, target in enumerate(spec.get("targets", [])):
        scanned.extend(_strings(target.get("extensions") or {}, f"/spec/targets/{index}/extensions"))
    for pointer, text in scanned:
        style = _host_style(text)
        if style is None:
            continue
        if style == "network":
            portability.append(_check("host-path", "declared", "A network share path is environment-specific; reference it through an environment binding.", pointer=pointer, hostStyle=style))
        elif (host_style and style != host_style) or (supported and style not in supported):
            portability.append(_check("host-path", "fail", f"A {style} host path cannot resolve on {host_os or 'the selected provider host'}.", "HOST_PATH_INCOMPATIBLE", pointer=pointer, hostStyle=style))
        else:
            portability.append(_check("host-path", "declared", f"A {style} host path is environment-specific; portable intent should reference it through an environment binding.", pointer=pointer, hostStyle=style))
    intent = {"targets": [{k: t[k] for k in ("id", "targetClass", "capabilities")} for t in spec.get("targets", [])],
              "bindings": [{"bindingId": b["id"], "elementId": b["logicalRef"].get("element"), "realizationClass": b["realizationClass"],
                            "targetId": b["targetId"], "artifactIds": b.get("artifactIds", []), "resourceIds": b.get("resourceIds", [])}
                           for b in spec.get("bindings", [])],
              "resources": spec.get("resources", []), "timeMappings": spec.get("timeMappings", []), "networkBindings": spec.get("networkBindings", [])}
    return {"resolutionVersion": RESOLUTION_VERSION, "deploymentRef": deployment_ref, "systemRef": _authored(spec["systemRef"]),
            "documentId": deployment["_path"], "bindings": binding_rows, "constraints": constraints, "parameters": parameters,
            "portableIntent": intent, "environment": environment, "portability": portability, "hostOS": host_os,
            "providerId": (provider or {}).get("providerId"),
            "provider": {k: provider.get(k) for k in ("providerId", "maturity", "realizationClasses", "targetClasses", "limitations")} if provider else None,
            "limitations": ["Compatibility covers declared requirements only; a preserved logical identity never implies behavioural equivalence or fidelity.",
                            "Values without an admitted precedence are rejected, never ordered by Studio."]}


def resolution_diagnostics(report):
    """Blocking preflight diagnostics for a resolution report."""
    if report is None:
        return []
    found = []

    def add(code, message, ref):
        found.append({"code": code, "severity": "error", "elementRef": ref, "elementRefs": [ref], "message": message,
                      "remediation": "Correct the deployment declaration; Studio never reorders, converts or resolves it implicitly."})
    for row in report["bindings"]:
        for check in row["checks"]:
            if check["status"] in BLOCKING:
                add(check["code"], f"{row['bindingId']}: {check['message']}", row["elementRef"])
    for check in [*report["constraints"], *report["portability"]]:
        if check["status"] in BLOCKING:
            add(check["code"], check["message"], report["deploymentRef"])
    for entry in report["parameters"]:
        if entry["status"] in BLOCKING:
            add(entry["code"], f"{entry['elementId']}.{entry['parameterId']}: {entry['message']}", report["systemRef"] + "#" + str(entry["elementId"]))
    for item in report["environment"]:
        if item["status"] in BLOCKING:
            add(item["code"], f"{item['ownerId']}: {item['message']}", report["deploymentRef"])
    return found
