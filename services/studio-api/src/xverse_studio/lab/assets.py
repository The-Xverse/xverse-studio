"""Bounded public inventory observations. No discovery, probes or active admission."""

from itertools import islice
import re
import unicodedata

MAX_ASSETS = 1000
MAX_PROVIDERS = 32
MAX_DIAGNOSTICS = 100
_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9:._-]{0,252}$")
_PRIVATE = re.compile(
    r"password|passwd|token|secret|credential|api.?key|authorization", re.I
)


def public_text(value):
    """Metadata text is bounded, inert, and never an endpoint or credential reference."""
    if not isinstance(value, str) or not value or len(value) > 256:
        return None
    if any(unicodedata.category(c).startswith("C") for c in value):
        return None
    if (
        _PRIVATE.search(value)
        or any(c in value for c in "@?&#=\\")
        or value.startswith("/")
        or re.match(r"^[A-Za-z]:/", value)
    ):
        return None
    return value


def opaque_id(value):
    return (
        isinstance(value, str)
        and _ID.fullmatch(value) is not None
        and public_text(value) is not None
    )


def _record(value, fields):
    if not isinstance(value, dict):
        return None
    return {
        key: shown
        for key in fields
        if (shown := public_text(value.get(key))) is not None
    } or None


def _revision(value):
    record = _record(value, ("version", "digest", "observedAt"))
    return {
        "status": "observed"
        if record and value.get("status") == "observed"
        else "unknown",
        **(record or {}),
    }


def public_contract(value):
    return _record(
        value, ("id", "direction", "payloadSchema", "unitSemantics", "compatibility")
    )


def project_asset(asset):
    """Allowlist public identity/contracts; private provider payloads are never serialized."""
    if (
        not isinstance(asset, dict)
        or not opaque_id(asset.get("assetId"))
        or not opaque_id(asset.get("providerId"))
    ):
        return None
    identity = _record(
        asset.get("identity"),
        ("serial", "deviceId", "digest", "model", "manufacturer", "hardwareRevision"),
    )
    # A model name by itself does not identify a particular physical asset.
    identified = bool(
        identity and any(identity.get(key) for key in ("serial", "deviceId", "digest"))
    )
    interfaces = {}
    source = asset.get("interfaces")
    if isinstance(source, dict):
        for name, contract in islice(source.items(), 64):
            if not opaque_id(name):
                continue
            if isinstance(contract, str):
                if public_text(contract):
                    interfaces[name] = contract
            elif isinstance(contract, dict):
                projected = public_contract(contract)
                if projected:
                    interfaces[name] = projected
    raw_capabilities = asset.get("capabilities")
    capability_sample = (
        raw_capabilities[:64] if isinstance(raw_capabilities, list) else []
    )
    raw_os = asset.get("supportedOS")
    os_sample = raw_os[:16] if isinstance(raw_os, list) else []
    metadata_truncated = (
        (isinstance(raw_capabilities, list) and len(raw_capabilities) > 64)
        or (isinstance(source, dict) and len(source) > 64)
        or (isinstance(raw_os, list) and len(raw_os) > 16)
    )
    capabilities = [
        c for c in ("observe", "stimulate", "destructive") if c in capability_sample
    ]
    scope = asset.get("evidenceScope")
    scope = (
        scope
        if scope in ("fixture", "prototype", "admitted_integration", "unavailable")
        else "unknown"
    )
    return {
        "assetId": asset["assetId"],
        "providerId": asset["providerId"],
        "providerVersion": public_text(asset.get("providerVersion")),
        "physical": asset.get("physical") is True,
        "identity": identity if identified else None,
        "identityStatus": "observed" if identified else "unknown",
        "firmware": _revision(asset.get("firmware")),
        "artifactRevision": _revision(asset.get("artifactRevision")),
        "metadata": {
            "status": "partial" if identified else "unknown",
            "limitations": [
                "Only allowlisted identity and revision observations are exposed."
            ],
        },
        "interfaces": interfaces,
        "interfacesStatus": "declared"
        if isinstance(source, dict) and len(source) <= 64
        else "unknown",
        "supportedOS": [value for value in ("Linux", "Windows") if value in os_sample],
        "observationTruncated": metadata_truncated,
        "capabilities": capabilities,
        "permissionScope": "unknown",
        "available": asset.get("available") is True,
        "evidenceScope": scope,
        "providerAdmission": "unavailable",
        "activeReady": False,
        "reservable": False,
        "diagnostics": [{"code": "PHYSICAL_PROVIDER_NOT_ADMITTED"}],
    }


def inventory_observation(registry):
    """Only contact registered provider inventory methods, bounded by registry and facade limits."""
    items, diagnostics, seen = [], [], set()
    maximum = max(0, min(registry.max_assets, MAX_ASSETS))
    examined = 0

    def diagnostic(code, provider_id=None):
        if len(diagnostics) < MAX_DIAGNOSTICS:
            diagnostics.append(
                {
                    "code": code,
                    **({"providerId": provider_id} if opaque_id(provider_id) else {}),
                }
            )

    providers = list(islice(registry.providers.items(), MAX_PROVIDERS + 1))
    for provider_id, provider in providers[:MAX_PROVIDERS]:
        if not opaque_id(provider_id):
            diagnostic("PROVIDER_INVENTORY_INVALID")
            continue
        try:
            result = provider.inventory()
            if isinstance(result, (str, bytes, dict)):
                raise ValueError("invalid inventory shape")
            for raw in result:
                if examined >= maximum:
                    diagnostic("INVENTORY_LIMIT_EXCEEDED", provider_id)
                    return {
                        "items": items,
                        "diagnostics": diagnostics,
                        "truncated": True,
                        "complete": False,
                    }
                examined += 1
                asset = project_asset(raw)
                if asset is None or asset["providerId"] != provider_id:
                    diagnostic("PROVIDER_INVENTORY_INVALID", provider_id)
                    continue
                if asset["assetId"] in seen:
                    # Ambiguous identities cannot resolve to whichever provider happened to be first.
                    items[:] = [
                        old for old in items if old["assetId"] != asset["assetId"]
                    ]
                    diagnostic("ASSET_IDENTITY_AMBIGUOUS", provider_id)
                    continue
                if asset["observationTruncated"]:
                    diagnostic("ASSET_METADATA_LIMIT_EXCEEDED", provider_id)
                seen.add(asset["assetId"])
                items.append(asset)
        except Exception:
            diagnostic("PROVIDER_INVENTORY_UNAVAILABLE", provider_id)
    if len(providers) > MAX_PROVIDERS:
        diagnostic("PROVIDER_LIMIT_EXCEEDED")
    return {
        "items": items,
        "diagnostics": diagnostics,
        "truncated": len(providers) > MAX_PROVIDERS,
        "complete": not diagnostics and len(providers) <= MAX_PROVIDERS,
    }
