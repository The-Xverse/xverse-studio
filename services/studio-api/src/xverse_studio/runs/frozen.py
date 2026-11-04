"""Opt-in installed reruns of verified historical sources, with current admission."""

import platform
import re

from xverse_studio.storage.core import Problem, digest


CONTRACT = {
    "contractVersion": "1.0",
    "inputPolicy": "exact-frozen-sources",
    "admissionPolicy": "current-full-preflight",
    "physicalEffects": False,
    "reproducibility": "uncontrolled",
}


def installed_source(runs, source, snapshot):
    """No runtime contact: only a native registration can opt into this contract.

    A descriptor in an imported document cannot register an implementation. An
    unchanged installation identity is mandatory; current implementation/capacity
    changes still undergo full fresh preflight and Start's independent checks.
    """
    provider_id = source.get("providerId")
    provider = runs.installed_providers.get(provider_id)
    descriptor = next(
        (p for p in runs.provider_descriptors() if p["providerId"] == provider_id), {}
    )
    contract = descriptor.get("rerunContract")
    versions = contract.get("sourceVersions") if isinstance(contract, dict) else None
    frozen = snapshot.get("providerIdentity")
    if (
        not isinstance(versions, list)
        or not 0 < len(versions) <= 16
        or any(
            not isinstance(v, str) or not re.fullmatch(r"[0-9]+\.[0-9]+\.[0-9]+", v)
            for v in versions
        )
        or len(set(versions)) != len(versions)
        or digest(contract) != digest({**CONTRACT, "sourceVersions": versions})
        or provider is None
        or not isinstance(frozen, dict)
        or frozen.get("providerId") != provider_id
        or snapshot.get("providerId") != provider_id
        or frozen.get("providerVersion") not in versions
        or frozen.get("contractVersion") != descriptor.get("contractVersion")
        or not isinstance(frozen.get("installationDigest"), str)
        or not re.fullmatch(r"sha256:[0-9a-f]{64}", frozen["installationDigest"])
        or frozen["installationDigest"] != descriptor.get("installationDigest")
        or frozen.get("evidenceScope") != descriptor.get("evidenceScope")
        or source.get("evidenceScope") != frozen.get("evidenceScope")
        or not isinstance(snapshot.get("configuration"), dict)
        or snapshot["configuration"].get("physicalEffects") is not False
    ):
        raise Problem(
            "RERUN_UNSUPPORTED",
            "These historical inputs have no admitted rerun mapping for the current installation. Recorded playback confers no execution authority.",
        )
    if (
        descriptor.get("available") is not True
        or descriptor.get("hostCompatible") is not True
        or platform.system() not in descriptor.get("supportedHostOS", [])
        or platform.machine() not in descriptor.get("architectures", [])
        or "start" not in descriptor.get("operations", [])
    ):
        raise Problem(
            "PROVIDER_UNAVAILABLE",
            "The current host cannot admit a fresh execution of these historical inputs.",
            503,
        )
    compiled = runs.compilation(snapshot["documents"], snapshot["selection"])
    configuration = provider.configuration(snapshot["documents"], compiled)
    if (
        compiled.get("valid") is not True
        or compiled.get("planDigest") != snapshot.get("planDigest")
        or compiled.get("semanticDigest") != snapshot.get("semanticDigest")
        or configuration is None
        or digest(configuration) != digest(snapshot.get("configuration"))
    ):
        raise Problem(
            "RERUN_INPUT_INCOMPATIBLE",
            "The current compiler/provider does not reproduce the exact original plan, semantics and effective configuration.",
        )
    return compiled, configuration, descriptor
