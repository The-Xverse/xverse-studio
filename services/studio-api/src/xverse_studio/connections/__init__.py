"""Connection admission over declared XDL semantics; nothing is inferred or converted.

The authoritative validator decides structure (endpoint membership, direction capability,
interface identity, network and time-domain membership). This module adds only checks
over what the declarations state, and never reports an unevaluated declaration as a pass:

* ``pass``: Studio evaluated the declaration and it holds;
* ``declared``: a required intent (delivery intent, time domain) is recorded, not evaluated;
* ``unknown``: the facts needed are not established (e.g. the source set is invalid);
* ``unsupported``: declared semantics need a contract no provider/profile admits; blocking;
* ``fail``: the declaration is violated; blocking.

Explicit converters, backward version compatibility, declared quality, uninterpretable
multiplicity, model couplings and feedback cycles all need contracts that are not admitted
for the owned reference provider, so they block execution instead of being ignored.
"""

import re

from ruamel.yaml import YAML

ADMISSION_VERSION = "1.0"
MAX_CONNECTIONS = 400
# Studio's interpretation of the free-text XDL multiplicity; anything else is unsupported.
MULTIPLICITY = re.compile(r"^(?:(\d+)|(\d+)\.\.(\d+|\*)|\*)$")
# Contracts this Studio build can evaluate. Each is absent until a provider/profile admits one.
ADMITTED_CONTRACTS = {
    "converter": False,
    "versionCompatibility": False,
    "quality": False,
    "causality": False,
    "modelCoupling": False,
}
BLOCKING = ("fail", "unsupported")


def _bounds(text):
    match = MULTIPLICITY.fullmatch(text.strip()) if isinstance(text, str) else None
    if not match:
        return None
    if match.group(1) is not None:
        value = int(match.group(1))
        return value, value
    if match.group(2) is not None:
        upper = None if match.group(3) == "*" else int(match.group(3))
        if upper is not None and upper < int(match.group(2)):
            return None
        return int(match.group(2)), upper
    return 0, None


def _check(name, status, message, code=None, pointer=None):
    return {
        "check": name,
        "status": status,
        "code": code,
        "message": message,
        "pointer": pointer,
    }


def _cycles(edges):
    """Strongly connected components with more than one member, or a self loop."""
    index, low, stack, on, result, counter = {}, {}, [], set(), [], [0]
    nodes = sorted({a for a, _ in edges} | {b for _, b in edges})
    graph = {n: sorted({b for a, b in edges if a == n}) for n in nodes}

    def visit(start):
        work = [(start, iter(graph[start]))]
        index[start] = low[start] = counter[0]
        counter[0] += 1
        stack.append(start)
        on.add(start)
        while work:
            node, children = work[-1]
            for child in children:
                if child not in index:
                    index[child] = low[child] = counter[0]
                    counter[0] += 1
                    stack.append(child)
                    on.add(child)
                    work.append((child, iter(graph[child])))
                    break
                if child in on:
                    low[node] = min(low[node], index[child])
            else:
                work.pop()
                if work:
                    low[work[-1][0]] = min(low[work[-1][0]], low[node])
                if low[node] == index[node]:
                    component = []
                    while True:
                        item = stack.pop()
                        on.discard(item)
                        component.append(item)
                        if item == node:
                            break
                    if len(component) > 1 or node in graph[node]:
                        result.append(sorted(component))

    for node in nodes:
        if node not in index:
            visit(node)
    return result


def _admission(checks):
    statuses = {c["status"] for c in checks}
    return (
        "rejected"
        if "fail" in statuses
        else "unsupported"
        if "unsupported" in statuses
        else "unknown"
        if "unknown" in statuses
        else "admitted"
    )


def admit_connections(documents, validation):
    """Return the connection admission report for a complete source set."""
    yaml = YAML(typ="safe")
    resources = []
    for name, source in documents.items():
        try:
            value = yaml.load(source)
        except Exception:  # Unparseable sources are the validator's to report.
            continue
        if isinstance(value, dict):
            resources.append((name, value))
    valid = bool(validation.get("valid", True))
    rejected = {}
    for diagnostic in validation.get("diagnostics", []):
        pointer = diagnostic.get("pointer") or ""
        match = re.match(r"^/spec/flows/(\d+)", pointer)
        location = diagnostic.get("location") or {}
        if match and diagnostic.get("severity") == "error":
            rejected.setdefault(
                (location.get("documentId"), int(match.group(1))), []
            ).append(diagnostic)
    connections, cycles, links, couplings, limits, endpoint_checks = (
        [],
        [],
        [],
        [],
        [],
        [],
    )
    for name, resource in resources:
        if resource.get("kind") != "System":
            continue
        spec = resource.get("spec") or {}
        meta = resource.get("metadata") or {}
        system_ref = f"xdl://{meta.get('namespace')}/system/{meta.get('name')}"
        interfaces = {
            i.get("id"): i for i in spec.get("interfaces", []) if isinstance(i, dict)
        }
        endpoints = {
            e.get("id"): e for e in spec.get("endpoints", []) if isinstance(e, dict)
        }
        # Keep original indexes so pointers and validator diagnostics stay aligned.
        indexed = [
            (i, f)
            for i, f in enumerate(spec.get("flows", []) or [])
            if isinstance(f, dict)
        ]
        if len(indexed) > MAX_CONNECTIONS:
            limits.append(
                {
                    "systemRef": system_ref,
                    "code": "CONNECTION_LIMIT_EXCEEDED",
                    "message": f"{len(indexed)} flows exceed the {MAX_CONNECTIONS}-connection admission bound; the excess is not evaluated and execution is blocked.",
                }
            )
        domains = [
            d.get("id") for d in spec.get("timeDomains", []) if isinstance(d, dict)
        ]
        default_domain = spec.get("defaultTimeDomainId")
        # Distinct flows attached to each endpoint, over all flows (not just the evaluated ones).
        attached = {}
        for _, flow in indexed:
            for endpoint_id in {
                flow.get("sourceEndpointId"),
                *(flow.get("destinationEndpointIds") or []),
            }:
                attached.setdefault(endpoint_id, set()).add(flow.get("id"))
        multiplicity = {}
        for endpoint_id, endpoint in endpoints.items():
            if "multiplicity" not in endpoint:
                continue
            bounds = _bounds(endpoint["multiplicity"])
            count = len(attached.get(endpoint_id, ()))
            pointer = f"endpoint {endpoint_id}"
            if bounds is None:
                result = _check(
                    "multiplicity",
                    "unsupported",
                    f"Endpoint {endpoint_id} declares multiplicity '{endpoint['multiplicity']}', which has no admitted interpretation.",
                    "MULTIPLICITY_UNSUPPORTED",
                    pointer,
                )
            elif count < bounds[0] or (bounds[1] is not None and count > bounds[1]):
                result = _check(
                    "multiplicity",
                    "fail",
                    f"Endpoint {endpoint_id} allows {endpoint['multiplicity']} attached flows but has {count}.",
                    "MULTIPLICITY_VIOLATED",
                    pointer,
                )
            else:
                result = _check(
                    "multiplicity",
                    "pass",
                    f"Endpoint {endpoint_id} has {count} attached flows within {endpoint['multiplicity']}.",
                    pointer=pointer,
                )
            multiplicity[endpoint_id] = result
            endpoint_checks.append({"ref": f"{system_ref}#{endpoint_id}", **result})
        edges, flow_owners = [], {}
        for index, flow in indexed[:MAX_CONNECTIONS]:
            pointer = f"/spec/flows/{index}"
            checks = []
            problems = rejected.get((name, index), [])
            if problems:
                checks.append(
                    _check(
                        "structure",
                        "fail",
                        "; ".join(d.get("message", "") for d in problems),
                        problems[0].get("code"),
                        pointer,
                    )
                )
            elif not valid:
                checks.append(
                    _check(
                        "structure",
                        "unknown",
                        "The source set is invalid elsewhere; this flow's structure is not established.",
                        "SOURCE_INVALID",
                        pointer,
                    )
                )
            else:
                checks.append(
                    _check(
                        "structure",
                        "pass",
                        "Endpoints, direction capability and interface identity were accepted by the authoritative validator.",
                        pointer=pointer,
                    )
                )
            interface = interfaces.get(flow.get("interfaceId")) or {}
            compatibility = interface.get("compatibility")
            if compatibility == "explicit-converter":
                checks.append(
                    _check(
                        "conversion",
                        "unsupported",
                        "The interface requires an explicit converter; no converter contract is admitted, so nothing is converted.",
                        "CONVERSION_UNSUPPORTED",
                        pointer,
                    )
                )
            elif compatibility == "backward":
                checks.append(
                    _check(
                        "version",
                        "unsupported",
                        f"Backward compatibility within {interface.get('versionRange', 'an undeclared range')} needs an admitted version-compatibility contract.",
                        "VERSION_COMPATIBILITY_UNSUPPORTED",
                        pointer,
                    )
                )
            elif compatibility == "exact":
                checks.append(
                    _check(
                        "conversion",
                        "pass",
                        "Exact interface compatibility; no conversion is involved.",
                        pointer=pointer,
                    )
                )
            else:
                checks.append(
                    _check(
                        "conversion",
                        "unknown",
                        "The interface declares no compatibility rule.",
                        "COMPATIBILITY_UNDECLARED",
                        pointer,
                    )
                )
            for endpoint_id in dict.fromkeys(
                [
                    flow.get("sourceEndpointId"),
                    *(flow.get("destinationEndpointIds") or []),
                ]
            ):
                if endpoint_id in multiplicity:
                    checks.append({**multiplicity[endpoint_id], "pointer": pointer})
            if "timeDomainId" in flow:
                checks.append(
                    _check(
                        "clock",
                        "declared",
                        f"Declared in time domain {flow['timeDomainId']}; not evaluated against endpoint or execution clocks.",
                        pointer=pointer,
                    )
                )
            elif len(domains) > 1 and not default_domain:
                checks.append(
                    _check(
                        "clock",
                        "fail",
                        "Several time domains exist and neither the flow nor the System selects one.",
                        "CLOCK_AMBIGUOUS",
                        pointer,
                    )
                )
            else:
                where = (
                    "the System default time domain " + default_domain
                    if default_domain
                    else "the only declared time domain "
                    + (domains[0] if domains else "(none declared)")
                )
                checks.append(
                    _check(
                        "clock",
                        "declared",
                        f"Uses {where}; not evaluated.",
                        pointer=pointer,
                    )
                )
            checks.append(
                _check(
                    "quality",
                    "unsupported",
                    "Declared quality needs an admitted provider contract to be honoured; none is admitted.",
                    "QUALITY_UNSUPPORTED",
                    pointer,
                )
                if flow.get("quality")
                else _check(
                    "quality",
                    "declared",
                    f"Delivery intent {flow.get('deliveryIntent')} is recorded; no further quality is declared.",
                    pointer=pointer,
                )
            )
            source_owner = (endpoints.get(flow.get("sourceEndpointId")) or {}).get(
                "ownerId"
            )
            owners = []
            # A structurally rejected flow is not an executable edge.
            for destination in (
                [] if problems else flow.get("destinationEndpointIds") or []
            ):
                owner = (endpoints.get(destination) or {}).get("ownerId")
                if source_owner and owner:
                    edges.append((source_owner, owner))
                    owners.append((source_owner, owner))
            flow_owners[len(connections)] = owners
            connections.append(
                {
                    "ref": f"{system_ref}#{flow.get('id')}",
                    "kind": "data_flow",
                    "systemRef": system_ref,
                    "documentId": name,
                    "sourceEndpointId": flow.get("sourceEndpointId"),
                    "destinationEndpointIds": flow.get("destinationEndpointIds") or [],
                    "interfaceId": flow.get("interfaceId"),
                    "deliveryIntent": flow.get("deliveryIntent"),
                    "timeDomainId": flow.get("timeDomainId"),
                    "checks": checks,
                }
            )
        system_cycles = _cycles(edges)
        for members in system_cycles:
            cycles.append(
                {
                    "systemRef": system_ref,
                    "members": [f"{system_ref}#{m}" for m in members],
                    "status": "unsupported",
                    "code": "CAUSALITY_CONTRACT_UNSUPPORTED",
                    "message": "This feedback cycle needs an admitted timing/causality contract; none is admitted, so it cannot execute. A drawn edge or an acyclic graph is not proof of executable correctness.",
                }
            )
        # Flows inside an unsupported cycle are themselves not admitted.
        for position, owners in flow_owners.items():
            if any(
                a in members and b in members
                for a, b in owners
                for members in system_cycles
            ):
                connections[position]["checks"].append(
                    _check(
                        "causality",
                        "unsupported",
                        "This flow is part of a feedback cycle without an admitted causality contract.",
                        "CAUSALITY_CONTRACT_UNSUPPORTED",
                        connections[position]["checks"][0]["pointer"],
                    )
                )
        for link in spec.get("links", []) or []:
            if isinstance(link, dict):
                links.append(
                    {
                        "ref": f"{system_ref}#{link.get('id')}",
                        "kind": "network_link",
                        "networkId": link.get("networkId"),
                        "participantEndpointIds": link.get("participantEndpointIds")
                        or [],
                        "connectivity": link.get("connectivity"),
                        "scope": "declared communication connectivity; not physical coupling and not a solver",
                    }
                )
        # System models that consume or produce interfaces are model couplings.
        for model in spec.get("models", []) or []:
            if isinstance(model, dict) and (
                model.get("inputs") or model.get("outputs")
            ):
                couplings.append(
                    {
                        "ref": f"{system_ref}#{model.get('id')}",
                        "kind": "model_coupling",
                        "modelKind": model.get("modelKind"),
                        "inputs": model.get("inputs") or [],
                        "outputs": model.get("outputs") or [],
                        "status": "unsupported",
                        "code": "MODEL_COUPLING_UNSUPPORTED",
                        "message": "This model couples declared interfaces; no model-coupling provider or solver is admitted, so it cannot execute. Communication flows are not couplings.",
                    }
                )
    for connection in connections:
        connection["admission"] = _admission(connection["checks"])
    attached_refs = {
        f"{c['systemRef']}#{e}"
        for c in connections
        for e in [c["sourceEndpointId"], *c["destinationEndpointIds"]]
    }
    blocking = (
        sum(c["admission"] in ("rejected", "unsupported") for c in connections)
        + len(cycles)
        + len(couplings)
        + len(limits)
        # Endpoint violations without any evaluated flow (e.g. a lower bound with no flows).
        + sum(
            e["status"] in BLOCKING and e["ref"] not in attached_refs
            for e in endpoint_checks
        )
    )
    return {
        "admissionVersion": ADMISSION_VERSION,
        "sourceValid": valid,
        "admittedContracts": dict(ADMITTED_CONTRACTS),
        "connections": connections,
        "endpoints": endpoint_checks,
        "cycles": cycles,
        "links": links,
        "couplings": couplings,
        "limits": limits,
        "blocking": blocking,
        "complete": not limits,
    }


def admission_diagnostics(report):
    """Blocking preflight diagnostics for declarations that cannot execute as declared."""
    result, seen = [], set()

    def add(code, message, refs, remediation):
        if (code, message) in seen:
            return
        seen.add((code, message))
        result.append(
            {
                "code": code,
                "severity": "error",
                "message": message,
                "elementRef": refs[0],
                "elementRefs": refs,
                "remediation": remediation,
            }
        )

    for connection in report["connections"]:
        for check in connection["checks"]:
            if check["status"] in BLOCKING and check["check"] not in (
                "structure",
                "causality",
            ):
                add(
                    check["code"],
                    check["message"],
                    [connection["ref"]],
                    "Declare an admitted compatible connection or remove it; Studio never converts or infers semantics.",
                )
    for endpoint in report["endpoints"]:
        if endpoint["status"] in BLOCKING:
            add(
                endpoint["code"],
                endpoint["message"],
                [endpoint["ref"]],
                "Correct the endpoint multiplicity or its attached flows.",
            )
    for cycle in report["cycles"]:
        add(
            cycle["code"],
            cycle["message"],
            cycle["members"],
            "Break the cycle or use a provider that admits its declared timing/causality contract.",
        )
    for coupling in report["couplings"]:
        add(
            coupling["code"],
            coupling["message"],
            [coupling["ref"]],
            "Use a provider that admits this model coupling, or remove it.",
        )
    for limit in report["limits"]:
        add(
            limit["code"],
            limit["message"],
            [limit["systemRef"]],
            "Reduce the number of declared flows.",
        )
    return result
