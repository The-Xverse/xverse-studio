import platform
from pathlib import Path
from xverse_studio.storage.core import digest

REFERENCE = {
    "providerId": "studio.reference",
    "providerVersion": "1.0.0",
    "contractVersion": "1.0",
    "name": "Studio executable reference",
    "maturity": "fixture",
    "evidenceScope": "owned_reference",
    "supportedHostOS": ["Linux", "Windows"],
    "architectures": ["x86_64", "AMD64"],
    "realizationClasses": ["simulated"],
    "targetClasses": ["model-unit"],
    "hostExecutionClass": "native-process",
    "operations": ["start", "stop", "cancel"],
    "clockDomains": ["simulation-time"],
    # Contracts this provider actually executes (ADR-0016); nothing else is admitted.
    "connectionContracts": {"causality": ["unit-delay"], "converters": ["linear"]},
    "limits": {
        "maxDurationSeconds": 30,
        "maxSamples": 3000,
        "maxConcurrentRuns": 4,
        "maxElements": 200,
        "maxConnections": 400,
    },
    "limitations": [
        "Scalar first-order reference model only; no external simulator, physical device, native X-COM, or industrial fidelity claim.",
        "Pause, rewind, step, live mutation and physical coupling are unsupported.",
    ],
    "supportedXdlVersions": ["xverse.io/xdl/v1alpha1"],
    "capabilityRecords": [
        {
            "kind": op,
            "targetClass": "model-unit",
            "legalStates": ["ready"]
            if op == "start"
            else ["running", "preparing", "ready"],
            "parametersSchema": {
                "type": "object",
                "properties": {},
                "additionalProperties": False,
            },
            "authorityRequirements": ["native-backend-owned"],
            "physicalEffects": False,
            "maxDurationSeconds": 30,
            "completion": "observed_worker_state",
        }
        for op in ["start", "stop", "cancel"]
    ],
    "available": True,
}
LITE = {
    "providerId": "xverse.lite",
    "providerVersion": "unavailable",
    "contractVersion": "1.0",
    "name": "X-Verse Lite / CARLA",
    "maturity": "unavailable",
    "evidenceScope": "unavailable",
    "supportedHostOS": ["Linux"],
    "architectures": ["x86_64"],
    "available": False,
    "operations": [],
    "blockedReasons": [
        {
            "code": "DEP-RUN-CONFIG",
            "message": "The inspected Bash harness uses a private trusted-host path and generates its own XDL. An admitted public effective-input/plan contract and permitted live environment are required.",
        }
    ],
}


def descriptors():
    host = platform.system()
    source = Path(__file__).resolve().parent
    implementation = digest(
        (source / "worker.py").read_bytes()
        + (source.parent / "xdl/__init__.py").read_bytes()
        + (source.parent / "xdl/examples.py").read_bytes()
    )
    return [
        {
            **p,
            "hostCompatible": host in p["supportedHostOS"]
            and platform.machine() in p["architectures"],
            "implementationDigest": implementation
            if p["providerId"] == "studio.reference"
            else None,
        }
        for p in (REFERENCE, LITE)
    ]


def capability_digest():
    return digest(descriptors())


def capabilities():
    from xverse_studio.deployments.comparison import COMPARISON_LIMITS
    from xverse_studio.xdl.edit_limits import MAX_EDIT_BYTES, MAX_EDIT_DEPTH, MAX_EDIT_NODES
    from xverse_studio.experiments.authoring import COLLECTIONS, SCENARIO_ITEM_BYTES, SCENARIO_ITEM_LIMITS
    from xverse_studio.assertions.evaluator import LIMITS
    from xverse_studio.evidence.query import MAX_FACETS, MAX_GAPS, MAX_IDENTIFIER, MAX_TICK_CHARACTERS
    from xverse_studio.events import (
        REPLAY_WINDOW, PENDING_EVENTS, PENDING_BYTES, MAX_FRAME_BYTES,
        GLOBAL_SUBSCRIBERS, PER_RUN_SUBSCRIBERS, EVENT_KINDS, CONTROL_RESERVE,
    )
    from xverse_studio.xdl import SUPPORTED_API_VERSIONS
    from xverse_studio.xdl import (
        VALIDATION_CACHE_ENTRIES,
        VALIDATION_CACHE_BYTES,
        VALIDATION_CACHE_SINGLE_SOURCE_BYTES,
    )

    return {
        "apiVersion": "1.0",
        "schemaVersion": "1.0",
        "contracts": {"readiness": "1.0", "annotations": "1.1", "evidenceQuery": "1.0", "events": "1.1"},
        # XDL resource API versions the authoritative adapter admits for authoring.
        "xdl": {"apiVersions": list(SUPPORTED_API_VERSIONS)},
        "host": {
            "os": platform.system(),
            "release": platform.release(),
            "architecture": platform.machine(),
            "python": platform.python_version(),
        },
        "studio": {
            "nativeTargets": ["Linux", "Windows"],
            "verifiedNativeOS": ["Linux"],
            "windowsAcceptance": "BLOCKED_USER_REQUEST",
        },
        "providers": descriptors(),
        "limits": {
            "deploymentComparison": dict(COMPARISON_LIMITS),
            "requestBytes": 8 * 1024 * 1024,
            "documentBytes": 1024 * 1024,
            "typedEditPayloadBytes": MAX_EDIT_BYTES,
            "typedEditDepth": MAX_EDIT_DEPTH,
            "typedEditNodes": MAX_EDIT_NODES,
            "archiveExpandedBytes": 16 * 1024 * 1024,
            "archiveFiles": 256,
            "pageSize": 200,
            "maxElements": 200,
            "maxConnections": 400,
            "eventPageSize": 200,
            "eventStream": {
                "replayRecords": REPLAY_WINDOW,
                "pendingCanonicalEvents": PENDING_EVENTS,
                "reservedControlSlots": 1,
                "pendingBytes": PENDING_BYTES,
                "controlReserveBytes": CONTROL_RESERVE,
                "frameBytes": MAX_FRAME_BYTES,
                "globalSubscribers": GLOBAL_SUBSCRIBERS,
                "perRunSubscribers": PER_RUN_SUBSCRIBERS,
                "cursorCharacters": 2048,
                "recoveryRecords": 200,
                "recoveryBytes": PENDING_BYTES,
                "legacyDefault": "1.0; current clients explicitly request 1.1",
                "canonicalKinds": sorted(EVENT_KINDS),
            },
            "evidenceQuery": {
                "pageSize": 200,
                "identifierCharacters": MAX_IDENTIFIER,
                "tickCharacters": MAX_TICK_CHARACTERS,
                "facetsPerKind": MAX_FACETS,
                "gapDescriptors": MAX_GAPS,
                "timeInterval": "half_open",
                "sourceClockMapping": "none; select the original clock domain",
            },
            "journalBytes": 64 * 1024 * 1024,
            "journalRecords": 100000,
            "evidenceProjectionCacheSourceBytes": 64 * 1024 * 1024,
            "evidenceProjectionCacheEntries": 2,
            "validationCache": {
                "entries": VALIDATION_CACHE_ENTRIES,
                "resultBytes": VALIDATION_CACHE_BYTES,
                "sourceBytes": VALIDATION_CACHE_BYTES,
                "singleSourceBytes": VALIDATION_CACHE_SINGLE_SOURCE_BYTES,
            },
            "preflightTTLSeconds": 60,
            "campaignRuns": 32,
            "campaignConcurrency": 1,
            "scenarioAuthoring": {
                **{COLLECTIONS[kind]: limit for kind, limit in SCENARIO_ITEM_LIMITS.items()},
                "editPayloadBytes": SCENARIO_ITEM_BYTES,
                "scope": "authored_intent; execution requires separate provider admission",
            },
            "evaluator": {
                **LIMITS,
                "budgetSeconds": 2,
                "admittedUnits": ["1"],
                "conversionTables": [],
            },
        },
        "supportedOperations": [
            "create_project",
            "validate",
            "compile",
            "source_edit",
            "layout",
            "preflight",
            "start",
            "stop",
            "cancel",
            "export",
            "evaluate",
            "campaign",
            "compare",
            "annotate",
            "retention",
            "rerun",
        ],
        "deferred": ["M5 distributed execution", "native X-COM", "remote access"],
        "evidenceScope": "owned_reference",
        "capabilityDigest": capability_digest(),
    }


def admit_descriptor(descriptor):
    """Trusted administrative integration gate; projects never register executable providers."""
    from xverse_studio.storage.core import Problem

    if not isinstance(descriptor, dict) or descriptor.get("contractVersion") != "1.0":
        raise Problem(
            "PROVIDER_VERSION_INCOMPATIBLE",
            "The installed provider contract is incompatible with Studio v1.",
        )
    required = [
        "providerId",
        "providerVersion",
        "implementationDigest",
        "supportedHostOS",
        "architectures",
        "capabilityRecords",
        "limits",
        "evidenceScope",
    ]
    if (
        any(key not in descriptor for key in required)
        or not isinstance(descriptor["implementationDigest"], str)
        or not descriptor["implementationDigest"].startswith("sha256:")
    ):
        raise Problem(
            "PROVIDER_DESCRIPTOR_INVALID",
            "An installed provider must declare exact implementation, authority, host and limit identities.",
        )
    for capability in descriptor["capabilityRecords"]:
        if not isinstance(capability, dict) or any(
            k not in capability
            for k in (
                "kind",
                "targetClass",
                "legalStates",
                "parametersSchema",
                "authorityRequirements",
                "physicalEffects",
            )
        ):
            raise Problem(
                "PROVIDER_DESCRIPTOR_INVALID",
                "Provider capabilities require scoped operation, state, parameter and authority contracts.",
            )
    return descriptor
