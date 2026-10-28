"""Explicit native observation installation and grants, separate from lease pins."""

from copy import deepcopy
from dataclasses import dataclass, field
import json
import math
import platform
import re
import threading
import time

from xverse_studio.lab import LabError
from xverse_studio.lab.assets import opaque_id, public_text
from xverse_studio.storage.core import digest


def sha256_identity(value):
    return (
        type(value) is str and re.fullmatch(r"sha256:[a-f0-9]{64}", value) is not None
    )


class ProbeAuthority:
    """Exact permission to request observation; reservation scope grants do not apply."""

    def __init__(self, grants=(), *, max_grants=1000):
        if type(max_grants) is not int or not 1 <= max_grants <= 1000:
            raise LabError("PROBE_CONFIG_INVALID")
        if (
            type(grants) not in (set, frozenset, tuple, list)
            or len(grants) > max_grants
        ):
            raise LabError("PROBE_CONFIG_INVALID")
        self._lock = threading.RLock()
        self._max_grants = max_grants
        self._generation = 0
        self._grants = {}
        for grant in grants:
            if type(grant) is not tuple or len(grant) != 2:
                raise LabError("PROBE_CONFIG_INVALID")
            self.grant(*grant)

    @staticmethod
    def _key(principal, asset_id):
        if not opaque_id(principal) or not opaque_id(asset_id):
            raise LabError("PROBE_CONFIG_INVALID")
        return principal, asset_id

    def grant(self, principal, asset_id):
        key = self._key(principal, asset_id)
        with self._lock:
            if key not in self._grants and len(self._grants) >= self._max_grants:
                raise LabError("LIMIT_EXCEEDED")
            self._generation += 1
            self._grants[key] = self._generation

    def revoke(self, principal, asset_id):
        key = self._key(principal, asset_id)
        with self._lock:
            self._generation += 1
            self._grants.pop(key, None)

    def require(self, principal, asset_id):
        with self._lock:
            generation = self._grants.get((principal, asset_id))
            if generation is None:
                raise LabError("FORBIDDEN")
            return generation


@dataclass(frozen=True)
class ProbeInstallation:
    provider: object
    provider_id: str
    asset_id: str
    binding_ref: str
    identity_digest: str
    implementation_digest: str
    version: str
    supported_os: tuple[str, ...]
    architectures: tuple[str, ...]
    evidence_scope: str
    conformance_ref: str
    authorization_ref: str
    contacted_resources: tuple[str, ...]
    private_binding: dict = field(default_factory=dict, repr=False)

    def __post_init__(self):
        if (
            not all(
                opaque_id(value)
                for value in (
                    self.provider_id,
                    self.asset_id,
                    self.binding_ref,
                    self.conformance_ref,
                    self.authorization_ref,
                )
            )
            or public_text(self.version) is None
        ):
            raise LabError("PROBE_CONFIG_INVALID")
        if not sha256_identity(self.identity_digest) or not sha256_identity(
            self.implementation_digest
        ):
            raise LabError("PROBE_CONFIG_INVALID")
        if self.evidence_scope not in ("fixture", "admitted_integration"):
            raise LabError("PROBE_CONFIG_INVALID")
        if (
            type(self.supported_os) is not tuple
            or not 1 <= len(self.supported_os) <= 2
            or any(value not in ("Linux", "Windows") for value in self.supported_os)
            or type(self.architectures) is not tuple
            or not 1 <= len(self.architectures) <= 8
            or any(not opaque_id(value) for value in self.architectures)
        ):
            raise LabError("PROBE_CONFIG_INVALID")
        if (
            platform.system() not in self.supported_os
            or platform.machine() not in self.architectures
        ):
            raise LabError("PROVIDER_HOST_UNSUPPORTED")
        if (
            type(self.contacted_resources) is not tuple
            or not 1 <= len(self.contacted_resources) <= 8
            or any(not opaque_id(value) for value in self.contacted_resources)
            or len(set(self.contacted_resources)) != len(self.contacted_resources)
            or not callable(getattr(self.provider, "probe", None))
        ):
            raise LabError("PROBE_CONFIG_INVALID")
        try:
            if type(self.private_binding) is not dict:
                raise ValueError()
            encoded = json.dumps(
                self.private_binding, allow_nan=False, ensure_ascii=False
            )
            if len(encoded.encode()) > 4096:
                raise ValueError()
            object.__setattr__(self, "private_binding", json.loads(encoded))
        except (ValueError, TypeError, RecursionError):
            raise LabError("PROBE_CONFIG_INVALID") from None

    def _public_identity(self):
        return dict(
            contractVersion="1.0",
            providerId=self.provider_id,
            providerVersion=self.version,
            assetId=self.asset_id,
            bindingRef=self.binding_ref,
            identityDigest=self.identity_digest,
            implementationDigest=self.implementation_digest,
            declaredSupportedOS=list(self.supported_os),
            declaredArchitectures=list(self.architectures),
            hostOS=platform.system(),
            hostArchitecture=platform.machine(),
            evidenceScope=self.evidence_scope,
            conformanceRef=self.conformance_ref,
            authorizationRef=self.authorization_ref,
            contactedResources=list(self.contacted_resources),
            scopes=["observe"],
            runtimeAdmission="unavailable",
            physicalCommands=[],
        )

    def binding_digest(self):
        return digest(
            {
                **self._public_identity(),
                "privateBindingDigest": digest(self.private_binding),
            }
        )

    def descriptor(self):
        return {**self._public_identity(), "bindingDigest": self.binding_digest()}

    def provider_binding(self):
        return dict(
            assetId=self.asset_id,
            providerId=self.provider_id,
            bindingRef=self.binding_ref,
            identityDigest=self.identity_digest,
            contactedResources=list(self.contacted_resources),
            private=deepcopy(self.private_binding),
        )


@dataclass(frozen=True)
class LabProbeConfiguration:
    installations: tuple[ProbeInstallation, ...]
    authority: ProbeAuthority
    call_timeout: float = 1.0
    max_operations: int = 1000
    clock: object = time.time

    def __post_init__(self):
        if (
            type(self.installations) is not tuple
            or len(self.installations) > 32
            or any(
                not isinstance(item, ProbeInstallation) for item in self.installations
            )
            or len({item.asset_id for item in self.installations})
            != len(self.installations)
            or not isinstance(self.authority, ProbeAuthority)
            or not callable(self.clock)
        ):
            raise LabError("PROBE_CONFIG_INVALID")
        providers = {}
        for item in self.installations:
            previous = providers.setdefault(item.provider_id, item)
            if previous.provider is not item.provider or (
                previous.implementation_digest,
                previous.version,
            ) != (item.implementation_digest, item.version):
                raise LabError("PROBE_CONFIG_INVALID")
        if (
            type(self.call_timeout) not in (int, float)
            or not math.isfinite(self.call_timeout)
            or not 0 < self.call_timeout <= 5
            or type(self.max_operations) is not int
            or not 1 <= self.max_operations <= 1000
        ):
            raise LabError("PROBE_CONFIG_INVALID")

    def bind(self, store):
        from .probes import LabProbes

        return LabProbes(store, self)
