"""Explicit native-host provider objects and policy; never deserialized from HTTP/XDL.

The host integrator owns installation, conformance and permission review. These
records do not perform installation, scan an endpoint or grant a user permission.
"""

from dataclasses import dataclass
import math
import platform
import re
import time

from xverse_studio.lab import LabError
from .assets import opaque_id, public_text
from .authority import LabAuthority
from xverse_studio.storage.core import digest


@dataclass(frozen=True)
class LeaseProviderInstallation:
    provider: object
    provider_id: str
    version: str
    implementation_digest: str
    supported_os: tuple[str, ...]
    architectures: tuple[str, ...]
    evidence_scope: str
    conformance_ref: str
    authorization_ref: str

    def __post_init__(self):
        if not opaque_id(self.provider_id) or public_text(self.version) is None:
            raise LabError("PROVIDER_CONFIG_INVALID")
        if type(self.implementation_digest) is not str or not re.fullmatch(
            r"sha256:[a-f0-9]{64}", self.implementation_digest
        ):
            raise LabError("PROVIDER_CONFIG_INVALID")
        if self.evidence_scope not in ("fixture", "admitted_integration") or not all(
            opaque_id(ref) for ref in (self.conformance_ref, self.authorization_ref)
        ):
            raise LabError("PROVIDER_CONFIG_INVALID")
        if (
            type(self.supported_os) is not tuple
            or not 1 <= len(self.supported_os) <= 2
            or any(value not in ("Linux", "Windows") for value in self.supported_os)
        ):
            raise LabError("PROVIDER_CONFIG_INVALID")
        if (
            type(self.architectures) is not tuple
            or not 1 <= len(self.architectures) <= 8
            or any(not opaque_id(value) for value in self.architectures)
        ):
            raise LabError("PROVIDER_CONFIG_INVALID")
        if (
            platform.system() not in self.supported_os
            or platform.machine() not in self.architectures
        ):
            raise LabError("PROVIDER_HOST_UNSUPPORTED")
        if not all(
            callable(getattr(self.provider, name, None))
            for name in (
                "inventory",
                "reserve",
                "renew",
                "release",
                "inspect_reservation",
            )
        ):
            raise LabError("PROVIDER_CONFIG_INVALID")

    def descriptor(self):
        return {
            "providerId": self.provider_id,
            "providerVersion": self.version,
            "implementationDigest": self.implementation_digest,
            "contractVersion": "1.0",
            "declaredSupportedOS": list(self.supported_os),
            "declaredArchitectures": list(self.architectures),
            "hostOS": platform.system(),
            "hostArchitecture": platform.machine(),
            "evidenceScope": self.evidence_scope,
            "conformanceRef": self.conformance_ref,
            "authorizationRef": self.authorization_ref,
            "operations": ["reserve", "renew", "release", "reconcile"],
            "runtimeAdmission": "unavailable",
            "physicalCommands": [],
        }


@dataclass(frozen=True)
class LabHostConfiguration:
    installations: tuple[LeaseProviderInstallation, ...]
    authority: LabAuthority
    clock: object = time.time
    call_timeout: float = 1.0
    max_operations: int = 1000

    def __post_init__(self):
        if (
            type(self.installations) is not tuple
            or not 1 <= len(self.installations) <= 32
            or not all(
                isinstance(value, LeaseProviderInstallation)
                for value in self.installations
            )
        ):
            raise LabError("PROVIDER_CONFIG_INVALID")
        if len({value.provider_id for value in self.installations}) != len(
            self.installations
        ):
            raise LabError("PROVIDER_CONFIG_INVALID")
        if not isinstance(self.authority, LabAuthority) or not callable(self.clock):
            raise LabError("PROVIDER_CONFIG_INVALID")
        if (
            type(self.call_timeout) not in (int, float)
            or not math.isfinite(self.call_timeout)
            or not 0 < self.call_timeout <= 5
        ):
            raise LabError("PROVIDER_CONFIG_INVALID")
        if type(self.max_operations) is not int or not 0 < self.max_operations <= 1000:
            raise LabError("PROVIDER_CONFIG_INVALID")

    def bind(self, store):
        from .operations import LabOperations

        service = LabOperations(
            store,
            {item.provider_id: item.provider for item in self.installations},
            {
                item.provider_id: digest(item.descriptor())
                for item in self.installations
            },
            self.authority,
            clock=self.clock,
            timeout=self.call_timeout,
            max_operations=self.max_operations,
        )
        service.installation_descriptors = [
            item.descriptor() for item in self.installations
        ]
        return service
