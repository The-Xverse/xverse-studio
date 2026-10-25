from copy import deepcopy

from .reservations import LabError


def validate_binding(logical_ref: str, asset: dict, required_interfaces: dict) -> dict:
    """A placement projection; never changes logical identity or grants authority."""
    if not isinstance(logical_ref, str) or not logical_ref or not isinstance(asset, dict) or not isinstance(required_interfaces, dict):
        raise LabError("INVALID_BINDING")
    actual = asset.get("interfaces", {})
    if any(actual.get(name) != contract for name, contract in required_interfaces.items()):
        raise LabError("INTERFACE_INCOMPATIBLE")
    diagnostics = []
    if not asset.get("identity"):
        diagnostics.append("ASSET_IDENTITY_UNRESOLVED")
    if asset.get("evidenceScope") != "admitted_integration":
        diagnostics.append("PHYSICAL_PROVIDER_NOT_ADMITTED" if asset.get("physical") else "FIXTURE_SCOPE_ONLY")
    if asset.get("available") is not True:
        diagnostics.append("ASSET_READINESS_UNPROVEN")
    return {"logicalRef": logical_ref, "assetId": asset.get("assetId"), "physical": bool(asset.get("physical")), "identity": deepcopy(asset.get("identity")), "ready": not diagnostics, "diagnostics": diagnostics, "capabilities": deepcopy(asset.get("capabilities", [])), "evidenceScope": asset.get("evidenceScope", "unknown")}
