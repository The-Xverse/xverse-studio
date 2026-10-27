"""Host object configuration never installs from browser/project metadata."""

import platform
from types import SimpleNamespace
import pytest

from xverse_studio.api.app import create_app
from xverse_studio.lab import LabError
from xverse_studio.lab.authority import LabAuthority
from xverse_studio.lab.configuration import (
    LabHostConfiguration,
    LeaseProviderInstallation,
)


def installation(**changes):
    provider = SimpleNamespace(
        **{
            name: lambda *args: None
            for name in (
                "inventory",
                "reserve",
                "renew",
                "release",
                "inspect_reservation",
            )
        }
    )
    values = dict(
        provider=provider,
        provider_id="fixture",
        version="1.0.0",
        implementation_digest="sha256:" + "c" * 64,
        supported_os=(platform.system(),),
        architectures=(platform.machine(),),
        evidence_scope="fixture",
        conformance_ref="fixture-conformance",
        authorization_ref="fixture-no-equipment",
    )
    values.update(changes)
    return LeaseProviderInstallation(**values)


def test_plain_host_metadata_is_rejected_before_creating_data_root(tmp_path):
    root = tmp_path / "must remain absent"
    with pytest.raises(LabError, match="^PROVIDER_CONFIG_INVALID$"):
        create_app(
            root, lab_host={"providerId": "fixture", "permissionScope": "destructive"}
        )
    assert not root.exists()


@pytest.mark.parametrize(
    "changes",
    [
        {"call_timeout": True},
        {"call_timeout": 0},
        {"call_timeout": 6},
        {"call_timeout": float("inf")},
        {"max_operations": True},
        {"max_operations": 0},
        {"max_operations": 1001},
    ],
)
def test_host_bounds_are_validated_before_binding_store_or_provider(changes):
    with pytest.raises(LabError, match="^PROVIDER_CONFIG_INVALID$"):
        LabHostConfiguration((installation(),), LabAuthority(), **changes)


def test_duplicate_installations_cannot_create_ambiguous_provider_identity():
    item = installation()
    with pytest.raises(LabError, match="^PROVIDER_CONFIG_INVALID$"):
        LabHostConfiguration((item, item), LabAuthority())


def test_unsupported_host_refuses_without_calling_any_provider_method():
    unsupported = "Windows" if platform.system() == "Linux" else "Linux"
    with pytest.raises(LabError, match="^PROVIDER_HOST_UNSUPPORTED$"):
        installation(supported_os=(unsupported,))


@pytest.mark.parametrize(
    "changes",
    [
        {"implementation_digest": "unidentified"},
        {"evidence_scope": "available"},
        {"authorization_ref": ""},
        {"conformance_ref": "../outside"},
    ],
)
def test_incomplete_or_unsafe_installation_identity_is_not_admitted(changes):
    with pytest.raises(LabError, match="^PROVIDER_CONFIG_INVALID$"):
        installation(**changes)
