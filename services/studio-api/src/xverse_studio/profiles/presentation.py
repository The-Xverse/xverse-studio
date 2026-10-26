"""Inert profile presentation (T062): sanitized terminology, icons, form groups and documentation.

Presentation never carries executable content. Every value is plain text within bounds; icon names
come from the shared allowlist; documentation is an `https:` or `urn:` reference that Studio shows but
never fetches. Domain terms relabel the shared workflows; they never change semantics, and when
bound domains disagree the core term is kept.
"""
from __future__ import annotations

import re

from xverse_studio.storage.core import Problem
from xverse_studio.xdl.examples import DOMAIN_PROFILES, DOMAIN_SCHEMA_ID  # noqa: F401  (re-exported)

CORE_LABELS = {"System": "System", "Element": "Element", "Flow": "Flow", "Deployment": "Deployment", "Scenario": "Scenario"}
ICONS = {"home", "model", "connection", "deployment", "experiment", "results", "catalog", "lab", "code", "search",
         "download", "upload", "refresh", "info", "settings"}
# Plain text only: no control (C0/C1), zero-width, bidirectional-override or BOM characters, and no markup.
_UNSAFE = "\\x00-\\x1f\\x7f-\\x9f\\u200b-\\u200f\\u202a-\\u202e\\u2066-\\u2069\\ufeff<>`"
_TEXT = re.compile(rf"^[^{_UNSAFE}]{{1,60}}$")
_LONG_TEXT = re.compile(rf"^[^{_UNSAFE}]{{1,240}}$")
_IDENTIFIER = re.compile(r"^[a-z][a-z0-9]*(?:-[a-z0-9]+)*$")
_REFERENCE = re.compile(r"^(?:https://[A-Za-z0-9.-]+(?:/[A-Za-z0-9._~/-]*)?|urn:[a-z0-9][a-z0-9-]{0,31}:[A-Za-z0-9._:~-]{1,160})$")


def sanitize_presentation(value):
    """Return a validated copy of inert presentation metadata, or refuse it as a whole."""
    def refuse(reason):
        raise Problem("PROFILE_CONFLICT", "Profile presentation is not admissible inert metadata: " + reason)
    if not isinstance(value, dict) or set(value) - {"name", "description", "labels", "icons", "formGroups", "documentation",
                                                     "domain", "namespaces"}:
        refuse("unknown fields")
    result = {}
    for field, pattern in (("name", _TEXT), ("domain", _TEXT), ("description", _LONG_TEXT)):
        if field in value:
            if not isinstance(value[field], str) or not pattern.fullmatch(value[field]):
                refuse(f"{field} must be bounded plain text")
            result[field] = value[field]
    labels = value.get("labels", {})
    if not isinstance(labels, dict) or set(labels) - set(CORE_LABELS) or not all(isinstance(v, str) and _TEXT.fullmatch(v) for v in labels.values()):
        refuse("labels must map core terms to bounded plain text")
    result["labels"] = dict(labels)
    icons = value.get("icons", {})
    if not isinstance(icons, dict) or set(icons) - set(CORE_LABELS) or not all(v in ICONS for v in icons.values()):
        refuse("icons must name allowlisted shared icons")
    result["icons"] = dict(icons)
    groups = value.get("formGroups", [])
    if not isinstance(groups, list) or len(groups) > 8:
        refuse("at most eight form groups")
    seen = set()
    result["formGroups"] = []
    for group in groups:
        if (not isinstance(group, dict) or set(group) != {"id", "label", "parameters"} or not isinstance(group["id"], str)
                or not _IDENTIFIER.fullmatch(group["id"]) or group["id"] in seen or not isinstance(group["label"], str)
                or not _TEXT.fullmatch(group["label"]) or not isinstance(group["parameters"], list) or len(group["parameters"]) > 12
                or not all(isinstance(p, str) and _IDENTIFIER.fullmatch(p) for p in group["parameters"])):
            refuse("form groups need an identifier, a plain-text label and parameter identifiers")
        seen.add(group["id"])
        result["formGroups"].append({"id": group["id"], "label": group["label"], "parameters": list(group["parameters"])})
    if "documentation" in value:
        if not isinstance(value["documentation"], str) or not _REFERENCE.fullmatch(value["documentation"]):
            refuse("documentation must be an https: or urn: reference")
        result["documentation"] = value["documentation"]
    namespaces = value.get("namespaces", [])
    if not isinstance(namespaces, list) or len(namespaces) > 16 or not all(isinstance(n, str) and re.fullmatch(r"[a-z0-9]+(?:[.-][a-z0-9]+)*", n) for n in namespaces):
        refuse("namespaces must be XDL namespaces")
    result["namespaces"] = list(namespaces)
    return result


def effective_presentation(project, registry):
    """Terms for this project: bound domain profiles, else the blueprint's declared default, else core."""
    domain = {entry["namespace"]: entry for entry in registry._entries() if entry.get("kind") == "domain-presentation"}
    bound = [lock["namespace"] for lock in project.get("manifest", {}).get("profiles", []) or []
             if isinstance(lock, dict) and lock.get("namespace") in domain]
    source = "bound"
    if not bound:
        provenance = project.get("manifest", {}).get("provenance") or project.get("provenance") or {}
        blueprint = provenance.get("blueprintRef")
        if blueprint:
            from xverse_studio.xdl import examples

            entry = next((e for e in examples() if e["id"] == blueprint), None)
            bound = [ref["namespace"] for ref in (entry or {}).get("profileRefs", []) if ref["namespace"] in domain]
            source = "blueprint default (not bound)"
    presentations = [sanitize_presentation(domain[namespace]["presentation"]) for namespace in bound]
    labels, icons, groups, conflicts = dict(CORE_LABELS), {}, [], []
    for term in CORE_LABELS:
        values = {p["labels"][term] for p in presentations if term in p["labels"]}
        if len(values) == 1:
            labels[term] = values.pop()
        elif len(values) > 1:
            conflicts.append(term)  # Bound domains disagree: keep the core term.
        icon_values = {p["icons"][term] for p in presentations if term in p["icons"]}
        if len(icon_values) == 1:
            icons[term] = icon_values.pop()
    if len(presentations) == 1:
        groups = presentations[0]["formGroups"]
    domains = [{"namespace": namespace, "domain": p.get("domain"), "name": p.get("name"), "documentation": p.get("documentation"),
                "namespaces": p["namespaces"], "maturity": domain[namespace]["maturity"]}
               for namespace, p in zip(bound, presentations)]
    # Every admitted domain, so definitions from any industry can be labelled for cross-industry selection.
    known = [{"namespace": namespace, "domain": entry["presentation"].get("domain"),
              "namespaces": entry["presentation"].get("namespaces", [])} for namespace, entry in domain.items()]
    return {"presentationVersion": "1.0", "source": source if bound else "core", "labels": labels, "icons": icons,
            "formGroups": groups, "conflicts": conflicts, "domains": domains, "knownDomains": known,
            "limitations": ["Domain terms relabel the shared workflows; they never change semantics, execution or fidelity.",
                            "Documentation references are shown, never fetched."]}
