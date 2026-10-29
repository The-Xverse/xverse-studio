"""Closed installed bridge mapping over the actual prepared canonical sources.

Zenoh remains the external transport. Native receipt only proves the explicit
X-COM FIFO boundary; publication and downstream application effects are separate.
"""
from ruamel.yaml import YAML
from xverse.maestro.execution import ExecutionInputError
from xverse_xdl import ResourceIdentity


from .native_signals import OBSERVED, SIGNALS


def native_configuration(prepared, *, operation_id, correlation_id, provider_id):
    """Return actual native identities and a separate fixed transport mapping.

    Caller is the registered host RuntimeProvider. This function neither grants
    authority nor probes a socket. Project bytes are read only as canonical data.
    """
    plan = prepared.inspection.to_data()["plan"]
    selection = prepared.submission.selection.system_ref
    systems = []
    for _, raw in prepared.submission.documents:
        item = YAML(typ="safe").load(raw)
        if item.get("kind") == "System" and ResourceIdentity.from_mapping(item).uri == selection:
            systems.append(item)
    if len(systems) != 1:
        raise ExecutionInputError("AUTOVERSE-NATIVE-SYSTEM-MISMATCH")
    system = systems[0]["spec"]
    interfaces = {i["id"]: i for i in system["interfaces"]}
    endpoints = {e["id"]: e for e in system["endpoints"]}
    flows = {f["id"]: f for f in plan["flows"]}
    bindings = [p for p in prepared.providers if p.provider_id == provider_id]
    if len(bindings) != 1 or bindings[0].configuration.installation_digest is None:
        raise ExecutionInputError("AUTOVERSE-NATIVE-INSTALLATION-MISSING")
    routes, transports = [], []
    for name, topic, direction in SIGNALS:
        flow = flows[name + "-flow"]
        source = endpoints[flow["sourceEndpointId"]]
        destinations = [endpoints[identifier] for identifier in flow["destinationEndpointIds"]]
        if direction == "to-vcu":
            candidates = [e for e in destinations if e["ownerId"] == "vcu"]
            if len(candidates) != 1 or source["ownerId"] == "vcu":
                raise ExecutionInputError("AUTOVERSE-NATIVE-ROUTE-MISMATCH")
            destination = candidates[0]
        else:
            if source["ownerId"] != "vcu" or not destinations:
                raise ExecutionInputError("AUTOVERSE-NATIVE-ROUTE-MISMATCH")
            destination = destinations[0]
        interface = interfaces[flow["interfaceId"]]
        routes.append({"routeId": selection + "#" + flow["id"],
            "interfaceId": selection + "#" + flow["interfaceId"],
            "schemaId": interface["payloadSchema"],
            "sourceEndpointId": selection + "#" + source["id"],
            "destinationEndpointId": selection + "#" + destination["id"],
            "observe": name in OBSERVED, "tapId": "studio.native." + name})
        transports.append({"topic": topic, "direction": direction, "flowId": flow["id"],
            "downstreamFanout": [selection + "#" + e["id"] for e in destinations],
            "downstreamConsumption": "unacknowledged"})
    return {"kind": "configure", "identity": {"runId": prepared.submission.run_id,
        "planDigest": prepared.submission.expected_plan_digest,
        "inputSemanticDigest": prepared.submission.expected_input_semantic_digest,
        "providerId": provider_id, "installationDigest": bindings[0].configuration.installation_digest,
        "operationId": operation_id, "correlationId": correlation_id,
        "clockDomain": "native-" + operation_id}, "routes": routes}, tuple(transports)


def collection_interval(duration_seconds):
    # At most 250 batches: three records + input facts + snapshots and two
    # Maestro import events each. Leave room within Argus's 4096-event budget
    # for startup, stop, diagnostics and one final quiescent collection.
    if type(duration_seconds) is not int or not 30 <= duration_seconds <= 1800:
        raise ExecutionInputError("AUTOVERSE-NATIVE-DURATION-INVALID")
    return max(2.5, duration_seconds / 250)
