"""Declared, resolved and observed communication as distinct projections (FR-036/FR-037).

* declared: what the authored System states for each flow (draft, or the run's frozen inputs);
* resolved: how the selected run's provider bound the flow, with its scope and limitations;
* observed: what the run's verified evidence shows for the flow, with source and freshness.

None is promoted into another: a declaration is not a route, a route is not traffic, and a flow
nobody observes is "not collected", not silent. Owned reference and Lite evidence are labelled as
such; neither is presented as native X-COM.
"""
from __future__ import annotations

import time

from ruamel.yaml import YAML

PROJECTION_VERSION = "1.0"
CONNECTIONS_NAMESPACE = "io.xverse.studio.connections"
# Transport labels by provider; native X-COM is not integrated in Studio 1.0.
TRANSPORT = {
    "studio.reference": ("in-process (owned reference worker)",
                         "Owned in-process reference evidence; no network transport, packet capture or native X-COM traffic."),
    "xverse.lite": ("Lite X-COM bridge",
                    "Lite evidence is identified as Lite; it is not activated native X-COM."),
}
LIVE_AGE_SECONDS = 5.0
ENDED = {"stopped", "failed", "cancelled"}
TRUSTED = {"valid", "verified_prefix"}


class ProjectionUnavailable(ValueError):
    """The run's frozen inputs cannot be projected; nothing falls back to the draft."""


def _ref(resource):
    meta = resource.get("metadata") or {}
    return f"xdl://{meta.get('namespace')}/{str(resource.get('kind', '')).lower()}/{meta.get('name')}"


def _target(reference):
    """Full element reference of an XDL elementRef, or None when it is not one."""
    if not isinstance(reference, dict) or not reference.get("element"):
        return None
    return f"xdl://{reference.get('namespace')}/{str(reference.get('kind', '')).lower()}/{reference.get('name')}#{reference.get('element')}"


def _parse(documents):
    yaml = YAML(typ="safe")
    parsed = []
    for source in documents.values():
        try:
            value = yaml.load(source)
        except Exception:  # The validator reports unparseable sources.
            continue
        if isinstance(value, dict) and isinstance(value.get("spec"), dict):
            parsed.append(value)
    return parsed


def declared_flows(documents):
    """Every System flow as authored, with its owned contract when declared."""
    result = []
    for resource in _parse(documents):
        if resource.get("kind") != "System":
            continue
        system_ref, spec = _ref(resource), resource["spec"]
        for flow in spec.get("flows", []) or []:
            if not isinstance(flow, dict):
                continue
            contract = ((flow.get("extensions") or {}).get(CONNECTIONS_NAMESPACE) or {}) if isinstance(flow.get("extensions"), dict) else {}
            result.append({"ref": f"{system_ref}#{flow.get('id')}", "flowId": flow.get("id"), "systemRef": system_ref,
                           "sourceEndpointId": flow.get("sourceEndpointId"),
                           "destinationEndpointIds": flow.get("destinationEndpointIds") or [],
                           "interfaceId": flow.get("interfaceId"), "deliveryIntent": flow.get("deliveryIntent"),
                           "timeDomainId": flow.get("timeDomainId") or spec.get("defaultTimeDomainId"),
                           "contract": contract, "source": "authored XDL"})
    return result


def _observers(documents, scenario_ref):
    """Observer id -> full flow reference, for the run's selected Scenario only."""
    observers = {}
    for resource in _parse(documents):
        if resource.get("kind") != "Scenario" or (scenario_ref and _ref(resource) != scenario_ref):
            continue
        for observer in resource["spec"].get("observers", []) or []:
            target = _target(observer.get("targetRef")) if isinstance(observer, dict) else None
            if target:
                observers[observer.get("id")] = target
    return observers


def _receipt(record):
    from xverse_studio.evidence.query import receipt_time

    seconds, _, _ = receipt_time(record)
    return None if seconds is None else float(seconds)


def project_communication(documents, *, run=None, snapshot=None, records=(), integrity=None, now=None):
    """Return the three projections for a draft (no run) or for one run's frozen inputs and evidence."""
    now = time.time() if now is None else now
    if run is not None:
        source_documents = (snapshot or {}).get("documents")
        if not isinstance(source_documents, dict) or not source_documents:
            raise ProjectionUnavailable("The run's frozen inputs are unavailable; its communication cannot be projected.")
        if not ((snapshot.get("selection") or {}).get("scenarioRef")):
            raise ProjectionUnavailable("The run's frozen selection names no Scenario, so its observers cannot be attributed.")
    else:
        source_documents = documents
    flows = declared_flows(source_documents)
    provider_id = (run or {}).get("providerId") or (snapshot or {}).get("providerId")
    transport, transport_limit = TRANSPORT.get(provider_id, ("not integrated", "No admitted transport for this provider."))
    resolved_refs = set(((snapshot or {}).get("configuration") or {}).get("resolvedFlows") or [])
    observers = _observers(source_documents, ((snapshot or {}).get("selection") or {}).get("scenarioRef"))
    trusted = integrity in TRUSTED
    samples = {}
    for record in records if trusted else ():
        if record.get("type") != "observation.available":
            continue
        payload = record.get("payload") if isinstance(record.get("payload"), dict) else {}
        target = observers.get(payload.get("observerRef"))
        if target:
            samples.setdefault(target, []).append(record)
    state = (run or {}).get("state")
    result = []
    for flow in flows:
        if run is None:
            resolved = {"status": "pending", "reason": "Routes are resolved by a provider when a run starts; select a run to inspect one."}
            observed = {"status": "no_run", "reason": "Nothing is observed without a run."}
        else:
            resolved = ({"status": "resolved", "providerId": provider_id, "transport": transport,
                         "evidenceScope": run.get("evidenceScope", "unknown"), "limitations": [transport_limit]}
                        if flow["ref"] in resolved_refs else
                        {"status": "not_resolved", "providerId": provider_id,
                         "reason": "The provider's frozen configuration does not resolve this flow."})
            observed_by = sorted(observer for observer, target in observers.items() if target == flow["ref"])
            mine = samples.get(flow["ref"], [])
            if not observed_by:
                observed = {"status": "not_collected",
                            "reason": "No observer of the run's Scenario targets this flow, so its traffic is not collected; silence is not a fault."}
            elif not trusted:
                observed = {"status": "unverified", "observerIds": observed_by, "integrity": integrity,
                            "reason": f"The run's evidence journal is {integrity or 'unavailable'}; nothing is presented as observed."}
            elif not mine:
                observed = ({"status": "not_observed", "observerIds": observed_by,
                             "reason": "The run ended and its observer recorded no sample for this flow: an expectation was not met; investigate the provider or observer."}
                            if state in ENDED and integrity == "valid" else
                            {"status": "collected_none", "observerIds": observed_by,
                             "reason": "An observer targets this flow, but the verified evidence holds no sample for it yet."})
            else:
                last = mine[-1]
                first_time = mine[0].get("sourceTime") if isinstance(mine[0].get("sourceTime"), dict) else {}
                last_time = last.get("sourceTime") if isinstance(last.get("sourceTime"), dict) else {}
                last_source = last.get("source") if isinstance(last.get("source"), dict) else {}
                last_payload = last.get("payload") if isinstance(last.get("payload"), dict) else {}
                received = _receipt(last)
                if received is None or received > now:
                    freshness = "unknown"  # Missing, undecodable or future receipt time (clock skew).
                elif state in ENDED:
                    freshness = "final" if integrity == "valid" else "partial"
                elif state in {"running", "starting", "stopping"}:
                    freshness = "live" if now - received <= LIVE_AGE_SECONDS else "stale"
                else:
                    freshness = "unknown"
                observed = {"status": "observed", "observerIds": observed_by, "samples": len(mine),
                            "firstTick": first_time.get("tick"),
                            "lastTick": last_time.get("tick"),
                            "clockDomain": last_time.get("clockDomain"),
                            "lastRecordedAt": received, "ageSeconds": None if received is None or received > now else round(now - received, 3),
                            "freshness": freshness,
                            "source": {"providerId": last_source.get("providerId"), "evidenceClass": last.get("evidenceClass")},
                            "evidenceScope": last_payload.get("evidenceScope", "unknown"),
                            "integrity": integrity, "limitations": [transport_limit]}
        result.append({**flow, "declared": {"status": "declared", "source": flow["source"]}, "resolved": resolved, "observed": observed})
    return {"projectionVersion": PROJECTION_VERSION, "runId": (run or {}).get("runId"), "runState": state,
            "providerId": provider_id, "transport": transport if run else None, "integrity": integrity if run else None,
            "flows": result,
            "limitations": ["Declared, resolved and observed are separate facts; none implies another.",
                            "Native X-COM is not integrated; owned reference and Lite evidence are labelled as such."]}
