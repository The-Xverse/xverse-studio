"""Immutable local discovery and inert artifact registration; no provider installation."""
from __future__ import annotations

from copy import deepcopy
import time
from typing import Literal
from urllib.parse import urlsplit

from pydantic import Field

from xverse_studio.security.models import Body
from xverse_studio.providers.registry import descriptors
from xverse_studio.security.files import check_text
from xverse_studio.storage.core import Problem, canonical, digest
from xverse_studio.xdl import examples
from xverse_studio.xdl.examples import reference_resources


class ArtifactRegistration(Body):
    name: str = Field(min_length=1, max_length=120)
    version: str = Field(min_length=1, max_length=64, pattern=r"^[0-9]+\.[0-9]+\.[0-9]+(?:[-+][A-Za-z0-9.-]+)?$")
    artifactKind: Literal["model", "executable-component", "firmware", "container-image", "data"]
    digest: str = Field(pattern=r"^sha256:[a-f0-9]{64}$")
    originRef: str = Field(min_length=1, max_length=512)
    providerIds: list[str] = Field(default_factory=list, max_length=16)
    apiVersions: list[str] = Field(default_factory=list, max_length=16)
    license: str | None = Field(default=None, max_length=200)
    limitations: list[str] = Field(default_factory=list, max_length=16)


class Catalog:
    def __init__(self, store):
        self.store = store

    def _builtins(self):
        entries = []
        for example in examples():
            public = deepcopy(example)
            public.update(entryId=example["id"], kind="blueprint", digest=digest(example["documents"]),
                          provenance={"originRef": "urn:xverse:studio:reference-blueprint", "version": example["version"]},
                          profiles=[p["namespace"] for p in example["profileRefs"]], roles=["controller", "plant", "observer"],
                          realizationClasses=["simulated"], executionAllowed=False,
                          availability="available", providerIds=["studio.reference"])
            entries.append(public)
        for resource in reference_resources().values():
            if resource["kind"] != "Component":
                continue
            name = resource["metadata"]["name"]
            identity = digest(resource)
            role = "controller" if name == "reference-controller" else "plant"
            entries.append({"id": "component-" + identity[7:23], "entryId": "component-" + identity[7:23],
                            "name": name, "kind": "component", "templateId": name, "version": resource["metadata"]["version"],
                            "digest": identity, "resource": resource, "description": resource["metadata"]["description"],
                            "provenance": resource["metadata"]["provenance"], "maturity": "fixture", "scope": "owned_reference",
                            "limitations": ["Reusable logical definition only; adding an instance does not grant executable provider support."],
                            "roles": [role], "interfaces": resource["spec"]["interfaces"], "profiles": [],
                            "realizationClasses": ["simulated"], "providerIds": ["studio.reference"], "availability": "available",
                            "executionAllowed": False})
        return entries

    def list(self, *, kind=None, role=None, profile=None, interface=None, providerId=None, query=None, cursor=None, limit=200):
        try:
            offset = int(cursor or "0")
        except ValueError:
            raise Problem("CURSOR_INVALID", "Choose a valid catalog cursor.") from None
        if offset < 0 or not 1 <= limit <= 200:
            raise Problem("LIMIT_EXCEEDED", "Choose a catalog page of one to 200 records.")
        entries = self._builtins() + self.store.all("catalogArtifact")
        entries = [entry for entry in entries if (not kind or entry["kind"] == kind)
                   and (not role or role in entry.get("roles", []))
                   and (not profile or profile in entry.get("profiles", []))
                   and (not interface or any(p.get("id") == interface or p.get("payloadSchema") == interface for p in entry.get("interfaces", [])))
                   and (not providerId or providerId in entry.get("providerIds", []))
                   and (not query or query.casefold() in (entry["name"] + " " + entry.get("description", "")).casefold())]
        selected = [{k: v for k, v in entry.items() if k != "documents"} for entry in entries[offset:offset + limit]]
        return {"items": selected, "nextCursor": str(offset + limit) if offset + limit < len(entries) else None}

    def get(self, entry_id):
        for entry in self._builtins() + self.store.all("catalogArtifact"):
            if entry["entryId"] == entry_id:
                return entry
        raise Problem("NOT_FOUND", "This immutable catalog entry is unavailable.", 404)

    def register(self, value, principal, key):
        body = ArtifactRegistration.model_validate(value).model_dump()
        check_text(canonical(body))
        try:
            origin = urlsplit(body["originRef"])
        except ValueError:
            raise Problem("ARTIFACT_ORIGIN_UNSUPPORTED", "The portable artifact URI is malformed.") from None
        if origin.scheme not in {"urn", "https", "http"} or origin.username or origin.password or (origin.scheme == "urn" and not origin.path) or (origin.scheme in {"http", "https"} and not origin.netloc):
            raise Problem("ARTIFACT_ORIGIN_UNSUPPORTED", "Use an inert portable URN or HTTP reference without credentials; host file paths are not portable metadata.")
        if any(len(x) > 200 for x in body["limitations"]) or any(len(x) > 253 for x in body["providerIds"] + body["apiVersions"]):
            raise Problem("LIMIT_EXCEEDED", "Artifact compatibility metadata exceeds its text bounds.")
        def accepted(db):
            identity = digest(body)
            entry_id = "artifact-" + identity[7:31]
            try:
                return self.store.get("catalogArtifact", entry_id, db)
            except Problem:
                pass
            if len(self.store.all("catalogArtifact", db)) >= 128:
                raise Problem("LIMIT_EXCEEDED", "This workspace retains at most 128 registered artifacts.")
            providers = {p["providerId"]: p for p in descriptors()}
            entry = {**body, "entryId": entry_id, "id": entry_id, "kind": "artifact", "metadataDigest": identity,
                     "createdAt": time.time(), "provenance": {"originRef": body["originRef"], "registration": "metadata_only"},
                     "maturity": "unavailable", "scope": "registered_reference", "availability": "unavailable", "executionAllowed": False,
                     "providerAvailability": [{"providerId": pid, "available": providers.get(pid, {}).get("available", False)} for pid in body["providerIds"]],
                     "limitations": body["limitations"] + ["Registration never downloads, builds, installs, flashes or executes the artifact. Provider admission remains separate."]}
            self.store.put("catalogArtifact", entry_id, entry, db)
            return entry
        result, _ = self.store.idempotent(principal, "POST /catalog/artifacts", key, body, accepted)
        return result
