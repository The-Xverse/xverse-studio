"""Coherent read-only comparison of declarations, never physical/runtime admission."""

from copy import deepcopy
from itertools import islice

from ruamel.yaml import YAML

from xverse_studio.lab.assets import public_text
from xverse_studio.providers.registry import descriptors
from xverse_studio.storage.core import Problem, canonical, digest
from .resolution import declared_time_mappings, clock_ref

COMPARISON_LIMITS = dict(
    bindingsPerVariant=1000,
    targetsPerVariant=1000,
    mappingsPerVariant=1000,
    targetCapabilities=64,
    responseBytes=2097152,
)


def require_revision(project, revision):
    if type(revision) is not int or not 1 <= revision <= 9007199254740991:
        raise Problem("REVISION_REQUIRED", "Supply a positive project revision.")
    if project["revision"] != revision:
        raise Problem(
            "REVISION_CONFLICT",
            "Reopen the current project before comparing deployments.",
            412,
            currentRevision=project["revision"],
        )


def compare(deployments, project_id, left_id, right_id, revision, provider_id):
    from . import authored_ref, resource_ref

    if left_id == right_id:
        raise Problem(
            "COMPARISON_SELECTION_INVALID", "Select two distinct Deployment documents."
        )
    project = deployments.projects.read(project_id)
    require_revision(project, revision)
    deployments.projects.assert_intact(project)
    documents = deployments.projects.sources(project)
    validation = deployments.adapter.validate(documents)
    if not validation["valid"]:
        raise Problem(
            "MODEL_INVALID",
            "Resolve authoritative source diagnostics before comparing deployments.",
        )
    yaml = YAML(typ="safe")
    parsed = {
        identifier: yaml.load(document["content"])
        for identifier, document in project["documents"].items()
    }
    selected = []
    for identifier in (left_id, right_id):
        item = parsed.get(identifier)
        if item is None or item.get("kind") != "Deployment":
            raise Problem(
                "NOT_FOUND", "A selected Deployment document was not found.", 404
            )
        selected.append(item)
    left_ref, right_ref = [authored_ref(item["spec"]["systemRef"]) for item in selected]
    if left_ref != right_ref:
        raise Problem(
            "SELECTION_INCOMPATIBLE",
            "Compare variants of the same authored System; different Systems do not share logical identities.",
        )
    systems = [
        identifier
        for identifier, item in parsed.items()
        if item.get("kind") == "System" and resource_ref(item) == left_ref
    ]
    if len(systems) != 1:
        raise Problem(
            "SELECTION_UNRESOLVED", "The shared authored System must resolve uniquely."
        )
    provider = next(
        (deepcopy(p) for p in descriptors() if p["providerId"] == provider_id), None
    )
    if provider is None:
        raise Problem(
            "PROVIDER_UNAVAILABLE", "No provider descriptor has this identity.", 404
        )
    provider_digest = digest(provider)

    def side(identifier, deployment):
        ref = resource_ref(deployment)
        mappings = list(
            islice(
                declared_time_mappings(deployment, parsed.values()),
                COMPARISON_LIMITS["mappingsPerVariant"] + 1,
            )
        )
        if (
            len(deployment["spec"].get("bindings", []))
            > COMPARISON_LIMITS["bindingsPerVariant"]
            or len(deployment["spec"].get("targets", []))
            > COMPARISON_LIMITS["targetsPerVariant"]
            or len(mappings) > COMPARISON_LIMITS["mappingsPerVariant"]
            or any(
                len(t.get("capabilities", [])) > COMPARISON_LIMITS["targetCapabilities"]
                for t in deployment["spec"].get("targets", [])
            )
        ):
            raise Problem(
                "LIMIT_EXCEEDED",
                "The deployment comparison exceeds its advertised bounds.",
                413,
            )
        report = deployments._resolve(documents, ref, provider_id, provider=provider)
        # This view carries only fields needed for the comparison. Environment paths,
        # external asset handles, arbitrary target metadata and artifact sources stay out.
        projection = {
            key: deepcopy(report[key])
            for key in (
                "resolutionVersion",
                "deploymentRef",
                "systemRef",
                "sourceValid",
                "providerId",
                "parameters",
            )
        }
        projection.update(
            documentId=identifier,
            revision=revision,
            bindings=[
                {
                    key: deepcopy(row.get(key))
                    for key in (
                        "bindingId",
                        "elementId",
                        "realizationClass",
                        "targetId",
                        "targetClass",
                        "status",
                    )
                }
                for row in report["bindings"]
            ],
            portableIntent={"bindings": deepcopy(report["portableIntent"]["bindings"])},
            diagnostics=[{"code": row["code"]} for row in report["diagnostics"]],
        )
        return dict(
            resolution=projection,
            declaredTargets=[
                dict(
                    targetId=t["id"],
                    targetClass=t["targetClass"],
                    capabilities=[
                        s
                        for c in t.get("capabilities", [])
                        if (s := public_text(c)) is not None
                    ],
                    omittedCapabilities=sum(
                        public_text(c) is None for c in t.get("capabilities", [])
                    ),
                )
                for t in deployment["spec"].get("targets", [])
            ],
            declaredMappings=[
                dict(
                    mappingId=m["mappingId"],
                    origin=m["origin"],
                    ownerRef=m["ownerRef"],
                    pointer=m["pointer"],
                    sourceClock=clock_ref(m["sourceTimeDomainRef"]),
                    targetClock=clock_ref(m["targetTimeDomainRef"]),
                    tolerance=deepcopy(m["tolerance"]),
                )
                for m in mappings
            ],
        )

    left, right = side(left_id, selected[0]), side(right_id, selected[1])
    if digest(provider) != provider_digest:
        raise Problem(
            "PROVIDER_CHANGED",
            "Provider declarations changed during comparison. Read them again.",
            409,
        )
    result = dict(
        comparisonVersion="1.0",
        scope="static_deployment_comparison",
        projectId=project_id,
        revision=revision,
        providerId=provider_id,
        providerDigest=provider_digest,
        provider={
            key: deepcopy(provider.get(key))
            for key in (
                "providerId",
                "providerVersion",
                "implementationDigest",
                "maturity",
                "evidenceScope",
                "available",
                "hostCompatible",
                "operations",
                "clockDomains",
                "realizationClasses",
                "targetClasses",
                "supportedHostOS",
                "architectures",
                "limitations",
            )
        },
        sharedSystem=dict(
            ref=left_ref,
            documentId=systems[0],
            sourceDigest=project["documents"][systems[0]]["digest"],
        ),
        left=left,
        right=right,
        synchronization=dict(status="unmeasured", preciseLatencyAvailable=False),
        physicalState="unknown",
        cleanup="unknown",
        fidelity="unverified",
        runtimeAdmission="preflight_required",
        limits=deepcopy(COMPARISON_LIMITS),
        limitations=[
            "Both variants use one captured authored revision and one provider descriptor; comparison changes no source or run.",
            "Declared target capabilities and mapping tolerances are not provider permission or measured synchronization evidence.",
            "Shared System source is not behavioural equivalence, fidelity or a physical-device admission.",
            "Physical state and cleanup require actual provider evidence; comparison requests no probe, reservation or command.",
        ],
    )
    if len(canonical(result).encode()) > COMPARISON_LIMITS["responseBytes"]:
        raise Problem(
            "LIMIT_EXCEEDED",
            "The deployment comparison exceeds its advertised response bound.",
            413,
        )
    return result
