"""Read-only project inspection: declared dependencies, example scope and unresolved authored content.

Nothing here fetches, installs or executes a dependency. Unresolved payloads are shown as a parsed
view; the exact authored bytes stay in their source document, unchanged and non-executable until a
matching Profile is authored and admitted.
"""
from __future__ import annotations

from io import StringIO

from ruamel.yaml import YAML

from xverse_studio.storage.core import digest

EXCERPT_LIMIT = 16 * 1024
# The positions where the XDL kind schemas allow extension maps (as the platform validator walks them).
EXTENSION_COLLECTIONS = {
    "Component": ("interfaces", "endpoints", "parameters"),
    "System": ("nodes", "componentInstances", "devices", "interfaces", "endpoints", "flows", "networks", "parameters"),
    "Deployment": ("targets", "bindings"),
    "Scenario": ("steps", "faults"),
}


def _pointer_token(value):
    return str(value).replace("~", "~0").replace("/", "~1")


def _extension_containers(resource):
    """Extension maps at the resource root and on schema-declared spec members, with JSON pointers."""
    if isinstance(resource.get("extensions"), dict):
        yield resource["extensions"], "/extensions"
    spec = resource.get("spec")
    if not isinstance(spec, dict):
        return
    for collection in EXTENSION_COLLECTIONS.get(resource.get("kind"), ()):
        members = spec.get(collection)
        if not isinstance(members, list):
            continue
        for index, member in enumerate(members):
            if isinstance(member, dict) and isinstance(member.get("extensions"), dict):
                yield member["extensions"], f"/spec/{collection}/{index}/extensions"


def _excerpt(payload):
    out = StringIO()
    YAML().dump(payload, out)
    text = out.getvalue()
    return (text, False) if len(text) <= EXCERPT_LIMIT else (text[:EXCERPT_LIMIT], True)


def inspect_project(project, registry):
    """Dependencies, scope and unresolved content of one project revision."""
    yaml = YAML(typ="safe")
    admitted = {entry["namespace"]: entry for entry in registry._entries()}
    parsed, unparsed = {}, []
    for document_id, document in project["documents"].items():
        try:
            resource = yaml.load(document["content"])
        except Exception:  # Parse errors are the validator's to report; keep the source listed.
            unparsed.append({"documentId": document_id, "path": document["path"]})
            continue
        if isinstance(resource, dict):
            parsed[document_id] = resource
    authored_profiles = {}
    for document_id, resource in parsed.items():
        if resource.get("kind") == "Profile" and isinstance(resource.get("spec"), dict):
            namespace = resource["spec"].get("extensionNamespace")
            if isinstance(namespace, str):
                authored_profiles.setdefault(namespace, []).append(document_id)
    conflicts = {finding["elementRef"]: finding for finding in registry.authored_findings(
        {document["path"]: document["content"] for document in project["documents"].values()})}
    unresolved = []
    for document_id, resource in parsed.items():
        for extensions, pointer in _extension_containers(resource):
            for key, payload in extensions.items():
                namespace = str(key)
                profiles = authored_profiles.get(namespace, []) if isinstance(key, str) else []
                if not profiles:
                    status, reason = "unresolved", "No Profile resource declares this extension namespace."
                elif len(profiles) > 1:
                    status, reason = "conflict", "More than one Profile resource declares this namespace."
                elif namespace not in admitted:
                    status, reason = "unadmitted", "A Profile is authored, but its namespace has no admitted schema or presentation."
                else:
                    metadata = parsed[profiles[0]].get("metadata")
                    metadata = metadata if isinstance(metadata, dict) else {}
                    ref = f"xdl://{metadata.get('namespace')}/profile/{metadata.get('name')}"
                    if ref in conflicts:
                        status, reason = "conflict", conflicts[ref]["message"]
                    else:
                        continue  # Admitted content is ordinary authored content.
                excerpt, truncated = _excerpt(payload)
                unresolved.append({"documentId": document_id, "path": project["documents"][document_id]["path"],
                                   "namespace": namespace, "pointer": f"{pointer}/{_pointer_token(namespace)}",
                                   "status": status, "reason": reason, "content": excerpt, "truncated": truncated,
                                   "executionAllowed": False})
    locks = registry.lock_statuses(project)
    supporting = project.get("supportingFiles", {}) or {}
    provenance = project.get("manifest", {}).get("provenance") or project.get("provenance") or {}
    example = None
    if provenance.get("blueprintRef"):
        from xverse_studio.xdl import examples

        entry = next((e for e in examples() if e["id"] == provenance["blueprintRef"]), None)
        if entry:
            example = {k: entry[k] for k in ("id", "name", "version", "scope", "maturity", "providerId", "limitations", "expectedObservations")}
    return {
        "projectId": project["projectId"], "revision": project["revision"],
        "provenance": provenance,
        "example": example,
        "dependencies": {
            "profileLocks": locks,
            "supportingFiles": [{"path": name, "bytes": len(content.encode()), "digest": digest(content.encode()),
                                 "executed": False} for name, content in sorted(supporting.items()) if isinstance(content, str)],
        },
        "unresolved": unresolved,
        "unparsed": unparsed,
        "sourceIntegrity": project.get("sourceIntegrity", "intact"),
        "executionBlocked": bool(unresolved or unparsed or project.get("sourceIntegrity", "intact") != "intact"
                                 or any(lock["status"] != "admitted" for lock in locks)),
        "limitations": ["Studio never downloads, installs or runs an undeclared or unadmitted dependency to open a project."],
    }
