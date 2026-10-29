"""Read-only reference admission facts, separate from observed runtime health."""

from copy import deepcopy
import math
import platform

from xverse_studio.providers.registry import admit_descriptor
from xverse_studio.providers.reference_control import MAX_PAUSED_WALL_SECONDS, MAX_LIVE_MUTATIONS
from xverse_studio.storage.core import Problem
from xverse_studio.xdl import XDLRejected, reference_configuration
from xverse_studio.xdl.examples import API_VERSION, MODEL_DIGEST, LIVE_MODEL_DIGEST

REQUIRED_LIMITS = (
    "maxDurationSeconds",
    "maxSamples",
    "maxConcurrentRuns",
    "maxElements",
    "maxConnections",
    "maxPausedWallSeconds",
)


def reference_readiness(documents, compiled, provider_id, provider, active_count):
    """Return facts only; this function never reserves, starts or probes equipment."""
    plan = compiled.get("plan") or {}
    system = compiled.get("selection", {}).get("systemRef")
    refs = [system] if system else []
    checks, diagnostics = {}, []

    def fact(
        name,
        status,
        message,
        *,
        code=None,
        remediation="",
        element_refs=None,
        facts=None,
    ):
        checks[name] = {
            "status": status,
            "message": message,
            "elementRefs": refs if element_refs is None else element_refs,
            "diagnosticCodes": [code] if code else [],
            "remediation": remediation,
        }
        if facts is not None:
            checks[name]["facts"] = facts
        if code:
            diagnostics.append(
                {
                    "code": code,
                    "severity": "error",
                    "message": message,
                    "elementRef": (element_refs or refs or [None])[0],
                    "elementRefs": element_refs or refs,
                    "remediation": remediation,
                }
            )

    fact(
        "backend",
        "available",
        "The authenticated native Studio backend is responding; no runtime liveness is inferred.",
        facts={
            "probe": "local_control_service",
            "hostOS": platform.system(),
            "hostArchitecture": platform.machine(),
        },
    )
    fact(
        "model",
        "valid" if compiled["valid"] else "invalid",
        "Public XDL validation and declared-intent compilation succeeded."
        if compiled["valid"]
        else "The public XDL validator/compiler rejected these inputs.",
        remediation="Correct the reported source diagnostics before execution."
        if not compiled["valid"]
        else "",
    )
    limits = (
        deepcopy(provider.get("limits", {}))
        if isinstance(provider, dict) and isinstance(provider.get("limits"), dict)
        else {}
    )
    host_matches = bool(
        provider
        and isinstance(provider.get("supportedHostOS"), list)
        and platform.system() in provider["supportedHostOS"]
        and isinstance(provider.get("architectures"), list)
        and platform.machine() in provider["architectures"]
    )
    provider_available = bool(
        provider
        and provider.get("available") is True
        and provider.get("hostCompatible") is True
        and host_matches
        and provider_id == "studio.reference"
    )
    if not provider_available:
        reason = (
            "The selected provider has no admitted native execution path on this host."
        )
        if provider and provider.get("blockedReasons"):
            reason = str(provider["blockedReasons"][0].get("message", reason))
        fact(
            "provider",
            "unavailable",
            reason,
            code="PROVIDER_UNAVAILABLE",
            remediation="Select an admitted provider on its supported native host; source authoring remains available.",
            facts={
                "providerId": provider_id,
                "hostCompatible": provider.get("hostCompatible") if provider else None,
                "supportedHostOS": provider.get("supportedHostOS", [])
                if provider
                else [],
                "architectures": provider.get("architectures", []) if provider else [],
            },
        )
        for name in (
            "artifacts",
            "capabilities",
            "target",
            "resources",
            "ownership",
            "clocks",
            "authority",
        ):
            fact(
                name,
                "unknown",
                "This fact has no admitted read-only check for the selected unavailable provider.",
                remediation="Admit the selected provider before checking this dimension.",
            )
        return checks, diagnostics, None, limits
    fact(
        "provider",
        "available",
        "The installed owned reference provider declares compatibility with this native OS/architecture.",
        facts={
            "providerId": provider_id,
            "hostCompatible": True,
            "supportedHostOS": provider["supportedHostOS"],
            "architectures": provider["architectures"],
            "evidenceScope": "owned_reference",
        },
    )
    descriptor_ok = True
    try:
        admit_descriptor(provider)
    except (Problem, TypeError, ValueError, KeyError):
        descriptor_ok = False
    starts = [
        c
        for c in provider.get("capabilityRecords", [])
        if isinstance(c, dict) and c.get("kind") == "start"
    ]
    authority = (
        len(starts) == 1
        and starts[0].get("authorityRequirements") == ["native-backend-owned"]
        and starts[0].get("physicalEffects") is False
    )
    compatible = (
        descriptor_ok
        and authority
        and "start" in provider.get("operations", [])
        and "model-unit" in provider.get("targetClasses", [])
        and "simulated" in provider.get("realizationClasses", [])
        and "ready" in starts[0].get("legalStates", [])
        and starts[0].get("targetClass") == "model-unit"
        and isinstance(provider.get("supportedXdlVersions"), list)
        and API_VERSION in provider["supportedXdlVersions"]
    )
    fact(
        "authority",
        "available" if authority else "unknown",
        "Backend-owned reference execution is admitted; no physical permit is acquired."
        if authority
        else "The selected descriptor requires an unverified authority scope.",
        code=None if authority else "AUTHORITY_UNAVAILABLE",
        remediation="Use an independently admitted nonphysical backend authority contract."
        if not authority
        else "",
        facts={"physicalEffects": False if authority else None},
    )
    configuration = None
    config_error = None
    if compiled["valid"] and compatible:
        try:
            configuration = reference_configuration(documents, compiled)
        except XDLRejected as exc:
            config_error = exc
    unsupported_refs = []
    if config_error and system:
        from ruamel.yaml import YAML

        baseline = {"controller", "plant"}
        for source in documents.values():
            resource = YAML(typ="safe").load(source)
            if resource.get("kind") != "System":
                continue
            for key in (
                "devices",
                "sensors",
                "actuators",
                "models",
                "componentInstances",
            ):
                for entry in resource["spec"].get(key, []):
                    if key != "componentInstances" or entry.get("id") not in baseline:
                        unsupported_refs.append(system + "#" + entry["id"])
    supported = compatible and configuration is not None
    fact(
        "capabilities",
        "compatible" if supported else "unsupported",
        "The exact source/configuration matches the admitted owned reference contract."
        if supported
        else str(
            config_error or "The descriptor does not admit this model/control contract."
        ),
        code=None
        if supported
        else (config_error.code if config_error else "CAPABILITY_UNSUPPORTED"),
        remediation="Select the owned reference template or another independently admitted compatible provider."
        if not supported
        else "",
        element_refs=unsupported_refs or refs,
    )
    bindings = plan.get("bindings", [])
    artifacts = [a for b in bindings for a in b.get("artifactRefs", [])]
    live_controls = bool(configuration and configuration.get("liveInputs"))
    model_digest = LIVE_MODEL_DIGEST if live_controls else MODEL_DIGEST
    model_ref = "urn:xverse:studio:reference:first-order:live-target:v1" if live_controls else "urn:xverse:studio:reference:first-order:v1"
    artifacts_ok = (
        bool(bindings)
        and all(b.get("artifactRefs") for b in bindings)
        and all(
            a.get("digest") == model_digest
            and a.get("sourceRef") == model_ref
            for a in artifacts
        )
    )
    models = [
        model
        for component in plan.get("components", [])
        for model in component.get("modelRefs", [])
    ]
    artifacts_ok = (
        artifacts_ok
        and bool(models)
        and all(
            model.get("externalRef") == model_ref
            for model in models
        )
    )
    fact(
        "artifacts",
        "available" if artifacts_ok else "unknown",
        "Every selected artifact reference matches the installed owned model contract digest; no external download was performed."
        if artifacts_ok
        else "Artifact availability/integrity cannot be established for all selected references.",
        code=None if artifacts_ok else "ARTIFACT_UNAVAILABLE",
        remediation="Supply admitted exact artifact identities; registration metadata alone is not availability."
        if not artifacts_ok
        else "",
        facts={"artifacts": artifacts},
    )
    clocks_ok = (
        bool(plan.get("timeDomains"))
        and all(
            c.get("id") in provider.get("clockDomains", [])
            for c in plan.get("timeDomains", [])
        )
        and not plan.get("timeMappings")
        and all(
            clock.get("epoch") == "0"
            and clock.get("rate") == "1"
            and clock.get("monotonic") is True
            and clock.get("canonicalUnit") == "tick"
            for clock in plan.get("timeDomains", [])
        )
    )
    fact(
        "clocks",
        "compatible" if clocks_ok else "unknown",
        "The owned simulation clock is declared; no cross-clock mapping or physical synchronization is claimed."
        if clocks_ok
        else "An admitted clock or mapping is missing for this provider.",
        code=None if clocks_ok else "CLOCK_MAPPING_UNAVAILABLE",
        remediation="Declare an admitted clock/mapping before execution."
        if not clocks_ok
        else "",
        facts={"domains": [c.get("id") for c in plan.get("timeDomains", [])]},
    )
    limits_known = all(
        isinstance(limits.get(key), (int, float))
        and not isinstance(limits[key], bool)
        and math.isfinite(limits[key])
        and limits[key] > 0
        for key in REQUIRED_LIMITS
    )
    limits_known = limits_known and all(
        isinstance(limits.get(key), int) and not isinstance(limits[key], bool)
        for key in REQUIRED_LIMITS
        if key != "maxDurationSeconds"
    )
    limits_known = limits_known and limits.get("maxPausedWallSeconds") == MAX_PAUSED_WALL_SECONDS
    if configuration and configuration.get("liveInputs"):
        limits_known = limits_known and type(limits.get("maxLiveMutations")) is int and limits.get("maxLiveMutations") == MAX_LIVE_MUTATIONS
    budget_ok = limits_known and configuration is not None
    if configuration and limits_known:
        budget_ok = (
            configuration["duration"] <= limits["maxDurationSeconds"]
            and configuration["duration"] / configuration["timestep"]
            <= limits["maxSamples"]
        )
    if limits_known:
        components = sum(
            c.get("scope") == "component-instance" for c in plan.get("components", [])
        )
        budget_ok = (
            budget_ok
            and components <= limits["maxElements"]
            and len(plan.get("flows", [])) <= limits["maxConnections"]
            and active_count < limits["maxConcurrentRuns"]
        )
    resource_code = (
        None
        if budget_ok
        else "LIMITS_UNKNOWN"
        if not limits_known
        else "RESOURCE_BUSY"
        if active_count >= limits["maxConcurrentRuns"]
        else "LIMIT_EXCEEDED"
        if configuration is not None
        else None
    )
    fact(
        "resources",
        "available"
        if budget_ok
        else "unknown"
        if not limits_known or configuration is None
        else "blocked",
        "Advertised reference budgets have capacity at this read-only check."
        if budget_ok
        else "Required provider limits are unknown."
        if not limits_known
        else "Workload requirements cannot be established for the unadmitted configuration."
        if configuration is None
        else "An advertised budget or concurrency bound is exceeded.",
        code=resource_code,
        remediation="Wait for owned runs to finish or reduce the authored workload within advertised limits."
        if limits_known and not budget_ok
        else "Admit explicit finite provider limits."
        if not limits_known
        else "",
        facts={"activeOwnedRuns": active_count, "reserved": False},
    )
    fact(
        "ownership",
        "available",
        "A new reference run will be owned by the native backend; browser disconnection does not own its lifetime.",
        facts={"owner": "native_backend", "reservationAcquired": False},
    )
    ready = (
        compiled["valid"]
        and supported
        and artifacts_ok
        and clocks_ok
        and budget_ok
        and authority
    )
    fact(
        "target",
        "ready" if ready else "blocked",
        "The owned executable can accept these inputs; it has not been started and no liveness/health is asserted."
        if ready
        else "This target cannot accept execution under the current source/provider/resource facts.",
        remediation="Resolve the independent blocked/unknown dimensions, then recheck."
        if not ready
        else "",
    )
    return checks, diagnostics, configuration if ready else None, limits
