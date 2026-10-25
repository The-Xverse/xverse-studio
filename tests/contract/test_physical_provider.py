"""Contract fixtures establish no hardware access or admission claim."""
from xverse_studio.lab import LabRegistry, validate_binding


def test_unresolved_identity_is_inspectable_but_not_active_ready():
    result = validate_binding("system#device", {"assetId": "unresolved", "physical": True, "interfaces": {}}, {})
    assert result["ready"] is False
    assert "ASSET_IDENTITY_UNRESOLVED" in result["diagnostics"]
    assert LabRegistry().inventory() == []
