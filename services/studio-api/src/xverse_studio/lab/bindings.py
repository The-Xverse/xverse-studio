from copy import deepcopy

from .reservations import LabError
from .assets import inventory_observation, opaque_id, public_contract, MAX_DIAGNOSTICS


def validate_binding(logical_ref: str, asset: dict, required_interfaces: dict) -> dict:
    """A placement projection; never changes logical identity or grants authority."""
    if (
        not isinstance(logical_ref, str)
        or not logical_ref
        or not isinstance(asset, dict)
        or not isinstance(required_interfaces, dict)
    ):
        raise LabError("INVALID_BINDING")
    actual = asset.get("interfaces", {})
    if not isinstance(actual, dict):
        raise LabError("INVALID_BINDING")
    if any(
        actual.get(name) != contract for name, contract in required_interfaces.items()
    ):
        raise LabError("INTERFACE_INCOMPATIBLE")
    diagnostics = []
    if not isinstance(asset.get("identity"), dict) or not asset.get("identity"):
        diagnostics.append("ASSET_IDENTITY_UNRESOLVED")
    if asset.get("physical") or asset.get("evidenceScope") != "admitted_integration":
        diagnostics.append(
            "PHYSICAL_PROVIDER_NOT_ADMITTED"
            if asset.get("physical")
            else "FIXTURE_SCOPE_ONLY"
        )
    if asset.get("available") is not True:
        diagnostics.append("ASSET_READINESS_UNPROVEN")
    return {
        "logicalRef": logical_ref,
        "assetId": asset.get("assetId"),
        "physical": bool(asset.get("physical")),
        "identity": deepcopy(asset.get("identity")),
        "ready": not diagnostics,
        "activeReady": False,
        "diagnostics": diagnostics,
        "capabilities": deepcopy(asset.get("capabilities", [])),
        "evidenceScope": asset.get("evidenceScope", "unknown"),
    }


def resolve_physical_bindings(
    projects, adapter, registry, project_id, document_id, revision=None
):
    """Observe authored placements, never amend deployment admission or grant authority."""
    from ruamel.yaml import YAML
    from xverse_studio.storage.core import Problem

    project = projects.read(project_id)
    if revision is not None and revision != project["revision"]:
        raise Problem("REVISION_CONFLICT", "Reload the current project revision.", 412)
    projects.assert_intact(project)
    document = project["documents"].get(document_id)
    if document is None:
        raise Problem("NOT_FOUND", "Deployment document not found.", 404)
    documents = projects.sources(project)
    validation = adapter.validate(documents)
    report = {
        "bindingObservationVersion": "1.0",
        "projectId": project_id,
        "documentId": document_id,
        "revision": project["revision"],
        "sourceValid": validation["valid"],
        "scope": "read_only_placement_observation",
        "activeReady": False,
        "runtimeAdmission": "unavailable",
        "bindings": [],
        "diagnostics": [],
        "limitations": [
            "Does not change deployment resolution or runtime admission.",
            "Physical controls and reservations remain unadmitted.",
        ],
    }
    if not validation["valid"]:
        report["diagnostics"] = [
            {"code": d.get("code", "MODEL_INVALID")}
            for d in validation["diagnostics"][:MAX_DIAGNOSTICS]
        ]
        return report
    yaml = YAML(typ="safe")
    resources = [yaml.load(source) for source in documents.values()]
    deployment = yaml.load(document["content"])
    if deployment["kind"] != "Deployment":
        raise Problem("SELECTION_UNRESOLVED", "Select a Deployment document.")
    reference = deployment["spec"]["systemRef"]
    systems = [
        r
        for r in resources
        if r["kind"] == "System"
        and all(r["metadata"][k] == reference[k] for k in ("namespace", "name"))
    ]
    if len(systems) != 1:
        raise Problem("SELECTION_UNRESOLVED", "The Deployment System is unresolved.")
    system = systems[0]
    system_ref = f"xdl://{reference['namespace']}/system/{reference['name']}"
    report.update(
        systemRef=system_ref,
        deploymentRef=f"xdl://{deployment['metadata']['namespace']}/deployment/{deployment['metadata']['name']}",
    )
    interfaces = {i["id"]: i for i in system["spec"].get("interfaces", [])}
    targets = {t["id"]: t for t in deployment["spec"].get("targets", [])}
    inventory = inventory_observation(registry)
    report["diagnostics"] = inventory["diagnostics"]
    report["inventoryTruncated"] = inventory["truncated"]
    report["inventoryComplete"] = inventory["complete"]
    assets = {a["assetId"]: a for a in inventory["items"]}
    physical = [
        b
        for b in deployment["spec"].get("bindings", [])
        if b["realizationClass"] in ("physical", "hybrid")
    ]
    for binding in physical[:1000]:
        logical = binding["logicalRef"]
        element_id = logical.get("element")
        logical_system_matches = logical.get("kind") == "System" and all(
            logical.get(key) == reference[key] for key in ("namespace", "name")
        )
        logical_ref = (
            f"xdl://{logical['namespace']}/{logical['kind'].lower()}/{logical['name']}"
            + ("#" + element_id if element_id else "")
        )
        required = {
            e["interfaceId"]: interfaces[e["interfaceId"]]
            for e in system["spec"].get("endpoints", [])
            if logical_system_matches and e.get("ownerId") == element_id
        }
        target = targets[binding["targetId"]]
        external = target.get("externalAssetRef")
        asset = assets.get(external) if opaque_id(external) else None
        diagnostics = ["PHYSICAL_PROVIDER_NOT_ADMITTED"]
        if not logical_system_matches:
            diagnostics.append("LOGICAL_BINDING_UNRESOLVED")
        if (
            asset
            and binding["realizationClass"] == "physical"
            and not asset["physical"]
        ):
            diagnostics.append("ASSET_REALIZATION_INCOMPATIBLE")
        compatible = (
            bool(asset)
            and bool(required)
            and all(asset["interfaces"].get(k) == v for k, v in required.items())
        )
        if not asset:
            diagnostics.append(
                "ASSET_UNAVAILABLE"
                if opaque_id(external)
                else "ASSET_REFERENCE_UNRESOLVED"
            )
        if asset and not asset["identity"]:
            diagnostics.append("ASSET_IDENTITY_UNRESOLVED")
        if not required:
            diagnostics.append("INTERFACE_REQUIREMENTS_UNKNOWN")
        elif asset and not compatible:
            diagnostics.append("INTERFACE_INCOMPATIBLE")
        if asset and not asset["available"]:
            diagnostics.append("ASSET_READINESS_UNPROVEN")
        report["bindings"].append(
            {
                "bindingId": binding["id"],
                "logicalRef": logical_ref,
                "targetId": target["id"],
                "realizationClass": binding["realizationClass"],
                "assetId": asset["assetId"]
                if asset
                else external
                if opaque_id(external)
                else None,
                "asset": deepcopy(asset),
                "requiredInterfaces": {
                    key: public_contract(value)
                    for key, value in list(required.items())[:64]
                },
                "requiredInterfacesTruncated": len(required) > 64,
                "evidenceScope": asset["evidenceScope"] if asset else "unknown",
                "ready": False,
                "activeReady": False,
                "diagnostics": diagnostics,
                "readiness": {
                    "identity": "resolved"
                    if asset and asset["identity"]
                    else "unknown",
                    "interfaces": "compatible"
                    if compatible
                    else "incompatible"
                    if asset and required
                    else "unknown",
                    "availability": "observed"
                    if asset and asset["available"]
                    else "unknown",
                    "metadata": asset["metadata"]["status"] if asset else "unknown",
                    "providerAdmission": "unavailable",
                    "permission": "unknown",
                    "activeOperation": "blocked",
                },
            }
        )
    if len(physical) > 1000:
        report["diagnostics"] = report["diagnostics"][: MAX_DIAGNOSTICS - 1] + [
            {"code": "BINDING_LIMIT_EXCEEDED"}
        ]
    return report
