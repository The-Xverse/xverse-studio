"""Native observation configuration cannot arise from imported/browser metadata."""

from dataclasses import replace
import platform

import pytest

from test_lab_probe_http import configured
from xverse_studio.api.app import create_app
from xverse_studio.lab import LabError
from xverse_studio.lab.authority import LabAuthority
from xverse_studio.lab.probe_configuration import LabProbeConfiguration, ProbeAuthority


def test_plain_configuration_rejected_before_data_root_creation(tmp_path):
    root = tmp_path / "must remain absent"
    with pytest.raises(LabError, match="^PROBE_CONFIG_INVALID$"):
        create_app(
            root, lab_probe_host={"providerId": "imported-provider", "scope": "observe"}
        )
    assert not root.exists()


@pytest.mark.parametrize(
    "change",
    [
        {"call_timeout": True},
        {"call_timeout": 0},
        {"call_timeout": 6},
        {"call_timeout": float("nan")},
        {"max_operations": True},
        {"max_operations": 0},
        {"max_operations": 1001},
        {"authority": LabAuthority()},
        {"clock": "a command"},
    ],
)
def test_host_bounds_and_separate_policy_are_required_before_bind(change):
    values = dict(installations=(), authority=ProbeAuthority())
    values.update(change)
    with pytest.raises(LabError, match="^PROBE_CONFIG_INVALID$"):
        LabProbeConfiguration(**values)


@pytest.mark.parametrize(
    "grants",
    [
        {"local-operator": ["observe"]},
        [("local-operator",)],
        [("local-operator", "../asset")],
        [("local-operator", "asset", "observe")],
    ],
)
def test_reservation_style_or_malformed_grants_cannot_grant_observation(grants):
    with pytest.raises(LabError, match="^PROBE_CONFIG_INVALID$"):
        ProbeAuthority(grants)


def test_exact_grants_are_bounded_revocable_and_generation_sensitive():
    authority = ProbeAuthority(max_grants=1)
    authority.grant("operator", "asset")
    original = authority.require("operator", "asset")
    for principal, asset in [("another", "asset"), ("operator", "another")]:
        with pytest.raises(LabError, match="^FORBIDDEN$"):
            authority.require(principal, asset)
    with pytest.raises(LabError, match="^LIMIT_EXCEEDED$"):
        authority.grant("another", "asset")
    authority.revoke("operator", "asset")
    with pytest.raises(LabError, match="^FORBIDDEN$"):
        authority.require("operator", "asset")
    authority.grant("operator", "asset")
    assert authority.require("operator", "asset") != original


@pytest.mark.parametrize(
    "changes",
    [
        {"identity_digest": "not-identified"},
        {"implementation_digest": "not-pinned"},
        {"asset_id": "../endpoint"},
        {"contacted_resources": ()},
        {"contacted_resources": ("resource", "resource")},
        {"contacted_resources": ("private?credential=value",)},
        {"private_binding": {"x": float("inf")}},
        {"private_binding": {"x": "a" * 4096}},
        {"provider": object()},
        {"evidence_scope": "available"},
        {"conformance_ref": ""},
    ],
)
def test_incomplete_installations_are_refused_without_callbacks(tmp_path, changes):
    bench = configured(tmp_path / "configuration fixture")
    with pytest.raises(LabError, match="^PROBE_CONFIG_INVALID$"):
        replace(bench.installation, **changes)
    assert bench.provider.calls == []


def test_unsupported_native_host_does_not_contact_provider(tmp_path):
    bench = configured(tmp_path / "host fixture")
    unsupported = "Windows" if platform.system() == "Linux" else "Linux"
    with pytest.raises(LabError, match="^PROVIDER_HOST_UNSUPPORTED$"):
        replace(bench.installation, supported_os=(unsupported,))
    assert bench.provider.calls == []


def test_ambiguous_assets_and_different_objects_with_same_provider_id_are_refused(
    tmp_path,
):
    bench = configured(tmp_path / "duplicate fixture")
    item = bench.installation
    with pytest.raises(LabError, match="^PROBE_CONFIG_INVALID$"):
        LabProbeConfiguration((item, item), bench.authority)
    changed = replace(item, asset_id="other-asset", provider=type(bench.provider)())
    with pytest.raises(LabError, match="^PROBE_CONFIG_INVALID$"):
        LabProbeConfiguration((item, changed), bench.authority)
    assert bench.provider.calls == []
