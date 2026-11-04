"""Bounded frozen dependency references, never package availability or authority."""

from copy import deepcopy

from xverse_studio.storage.core import Problem


def dependency_summary(snapshot, *, version="1.1"):
    """Summarize only recorded pins. Do not inspect paths, fetch or install.

    Runtime/compiler/profile/artifact payloads are outside an evidence bundle.
    Their metadata is preserved, but no current-host availability is inferred.
    """
    items = []

    def add(kind, identity):
        if len(items) >= 256:
            raise Problem(
                "LIMIT_EXCEEDED", "The dependency summary limit is 256 references.", 413
            )
        items.append(
            {
                "kind": kind,
                "identity": deepcopy(identity),
                "availability": "not_included" if identity else "unavailable",
                "contentIncluded": False,
                "identityStatus": "frozen_declaration",
            }
        )

    provider = snapshot.get("providerIdentity")
    add(
        "provider",
        {
            k: provider[k]
            for k in (
                "providerId",
                "providerVersion",
                "contractVersion",
                "implementationDigest",
                "installationDigest",
            )
            if k in provider
        }
        if isinstance(provider, dict)
        else None,
    )
    add("compiler", snapshot.get("compiler"))
    locks = snapshot.get("profileLocks")
    if isinstance(locks, list):
        for lock in locks:
            add("profile", lock)
    else:
        add("profile", None)
    plan = snapshot.get("plan")
    if version == "1.1":
        compiled_profile = plan.get("profile") if isinstance(plan, dict) else None
        provenance = plan.get("provenance") if isinstance(plan, dict) else None
        resources = (
            provenance.get("resources") if isinstance(provenance, dict) else None
        )
        profiles = (
            [r for r in resources if isinstance(r, dict) and r.get("kind") == "Profile"]
            if isinstance(resources, list)
            else None
        )
        add(
            "profile",
            {"compiledProfile": compiled_profile, "resources": profiles}
            if compiled_profile or profiles
            else None,
        )
    bindings = plan.get("bindings") if isinstance(plan, dict) else None
    if isinstance(bindings, list):
        for binding in bindings:
            refs = binding.get("artifactRefs") if isinstance(binding, dict) else None
            if not isinstance(refs, list):
                add("artifact", None)
            else:
                for ref in refs:
                    add("artifact", {"bindingId": binding.get("id"), "artifact": ref})
    else:
        add("artifact", None)
    return {
        "dependenciesVersion": version,
        "snapshotDigest": snapshot.get("snapshotDigest"),
        "resolution": "not_attempted",
        "items": items,
        "limitations": [
            "Only frozen identity metadata is included. Runtime, compiler, profile and artifact payloads are not embedded, fetched or installed.",
            "A frozen declaration does not establish current-host availability, distribution permission or execution authority. Inspect portable project locks for additional declared restrictions.",
        ],
    }
