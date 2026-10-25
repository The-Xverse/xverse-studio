"""Explicit built-in profile locks and inert packaged presentation metadata."""
from __future__ import annotations

from importlib.resources import files
from copy import deepcopy
import json
from pathlib import Path

from ruamel.yaml import YAML

from xverse_studio.storage.core import Problem, canonical, digest, uid
from xverse_studio.security.files import safe_name
from xverse_studio.xdl.examples import API_VERSION, EVALUATION_NAMESPACE, EVALUATION_SCHEMA_ID, PROFILE_NAMESPACE, dump_yaml


class ProfileRegistry:
    def __init__(self, adapter):
        self.adapter = adapter

    def _entries(self):
        result = []
        sources = [
            (PROFILE_NAMESPACE, "0.1.0", "Declared experiment intent", str(files("xverse_xdl").joinpath("profiles", "experiment-lite-v0.1.schema.json")),
             "https://xverse.io/profiles/experiment-lite/v0.1/schema.json", "https://xverse.io/profiles/experiment-lite/v0.1/README.md"),
            (EVALUATION_NAMESPACE, "1.0.0", "Bounded experiment assessment", str(Path(__file__).parent.parent / "assertions" / "evaluation-v1.schema.json"),
             EVALUATION_SCHEMA_ID, "urn:xverse:studio:experiments:1.0"),
        ]
        for namespace, version, title, path, schema_ref, documentation in sources:
            raw = Path(path).read_bytes()
            presentation = {"name": title, "description": "Packaged declarative profile; provider execution is admitted independently.",
                            "labels": {"System": "System", "Element": "Element"}, "formGroups": [], "documentation": documentation}
            result.append({"profileId": namespace, "namespace": namespace, "version": version, "schemaRef": schema_ref,
                           "schemaDigest": digest(raw), "presentationDigest": digest(canonical(presentation).encode()),
                           "presentation": presentation, "schema": json.loads(raw), "schemaText": raw.decode(),
                           "documentationRef": documentation, "compatibleApiVersions": [API_VERSION], "conflictPolicy": "reject",
                           "maturity": "admitted_integration", "scope": "offline_schema_and_derived_assessment",
                           "executionAllowed": False, "limitations": ["Profile selection cannot install a provider or grant simulator/device authority."]})
        return result

    def list(self):
        return {"items": [{k: v for k, v in entry.items() if k not in {"schema", "schemaText"}} for entry in self._entries()], "nextCursor": None}

    def get(self, identifier):
        for entry in self._entries():
            if entry["profileId"] == identifier:
                return entry
        raise Problem("PROFILE_UNRESOLVED", "The requested profile namespace/version has not been admitted.", 404)

    def _verified_lock(self, lock):
        allowed = {"namespace", "version", "schemaPath", "schemaDigest", "presentationPath", "presentationDigest"}
        if not isinstance(lock, dict) or set(lock) - allowed or not {"namespace", "version", "schemaPath", "schemaDigest"} <= set(lock):
            raise Problem("PROFILE_CONFLICT", "The declared profile lock has unsupported or missing identity fields.")
        try:
            entry = self.get(lock["namespace"])
        except Problem:
            raise Problem("PROFILE_UNRESOLVED", "A declared profile namespace has no admitted schema/presentation identity.") from None
        if lock["version"] != entry["version"] or lock["schemaDigest"] != entry["schemaDigest"]:
            raise Problem("PROFILE_CONFLICT", "The declared profile version/schema digest differs from the admitted registry.")
        if bool(lock.get("presentationPath")) != bool(lock.get("presentationDigest")):
            raise Problem("PROFILE_CONFLICT", "A presentation lock needs both its explicit path and immutable digest.")
        if lock.get("presentationDigest") and lock["presentationDigest"] != entry["presentationDigest"]:
            raise Problem("PROFILE_CONFLICT", "The presentation digest is not an admitted declarative asset.")
        for field in ("schemaPath", "presentationPath"):
            if lock.get(field):
                path = safe_name(lock[field])
                if not path.startswith("profiles/") or not path.endswith(".json"):
                    raise Problem("PROFILE_CONFLICT", "Declared profile sidecars must be explicit portable JSON files under profiles/.")
        return entry

    def validate_project(self, project):
        locks = project.get("manifest", {}).get("profiles", [])
        if not isinstance(locks, list) or len(locks) > 16:
            raise Problem("PROFILE_CONFLICT", "The authored envelope exceeds the admitted profile-lock bound.")
        seen = set()
        for lock in locks:
            entry = self._verified_lock(lock)
            if lock["namespace"] in seen:
                raise Problem("PROFILE_CONFLICT", "A namespace has more than one declared profile lock.")
            seen.add(lock["namespace"])
            for path_field, digest_field in (("schemaPath", "schemaDigest"), ("presentationPath", "presentationDigest")):
                if not lock.get(path_field):
                    continue
                content = project.get("supportingFiles", {}).get(lock[path_field])
                if not isinstance(content, str) or digest(content.encode()) != lock[digest_field]:
                    raise Problem("PROFILE_CONFLICT", "A declared profile sidecar is absent or disagrees with its immutable digest.")
                if path_field == "presentationPath":
                    try:
                        if json.loads(content) != entry["presentation"]:
                            raise ValueError()
                    except (ValueError, TypeError, RecursionError):
                        raise Problem("PROFILE_CONFLICT", "Profile presentation must match the admitted inert metadata.") from None
        return deepcopy(locks)

    def validate_snapshot(self, snapshot):
        locks = snapshot.get("profileLocks", [])
        if not isinstance(locks, list) or len(locks) > 16:
            raise Problem("PROFILE_CONFLICT", "The frozen profile-lock identities are unavailable or exceed their bound.")
        seen = set()
        for lock in locks:
            self._verified_lock(lock)
            if lock["namespace"] in seen:
                raise Problem("PROFILE_CONFLICT", "Frozen profile locks repeat an extension namespace.")
            seen.add(lock["namespace"])
        return deepcopy(locks)

    def bind(self, projects, project_id, revision, bindings):
        if not isinstance(bindings, list) or not 1 <= len(bindings) <= 16:
            raise Problem("LIMIT_EXCEEDED", "Select one to 16 explicit profile locks.")
        selected, namespaces = [], set()
        for lock in bindings:
            if not isinstance(lock, dict) or set(lock) != {"profileId", "version", "schemaDigest", "presentationDigest"}:
                raise Problem("PROFILE_CONFLICT", "A profile lock requires its exact identifier, version and both immutable digests.")
            entry = self.get(lock["profileId"])
            if entry["namespace"] in namespaces or any(lock[k] != entry[k] for k in lock):
                raise Problem("PROFILE_CONFLICT", "A profile namespace, version or immutable digest conflicts with the admitted registry.")
            namespaces.add(entry["namespace"])
            selected.append(entry)
        yaml = YAML(typ="safe")
        def change(project):
            documents = project["documents"]
            initial = self.adapter.validate(projects.sources(project))
            if not initial["valid"] and any(d.get("gate", 0) < 3 for d in initial["diagnostics"] if d.get("severity") == "error"):
                raise Problem("PROFILE_CONFLICT", "Resolve parsing/schema/platform diagnostics before binding profile semantics; exact source is preserved.", diagnostics=initial["diagnostics"])
            existing = {}
            for document in documents.values():
                resource = yaml.load(document["content"])
                if isinstance(resource, dict) and resource.get("kind") == "Profile":
                    ns = resource.get("spec", {}).get("extensionNamespace")
                    if ns in existing:
                        raise Problem("PROFILE_CONFLICT", "Multiple resources claim the same extension namespace.")
                    existing[ns] = resource
            locks = {lock["namespace"]: lock for lock in project["manifest"].get("profiles", [])}
            for entry in selected:
                current = existing.get(entry["namespace"])
                if current and (current["metadata"]["version"] != entry["version"] or current["spec"].get("schemaRef") != entry["schemaRef"] or current["spec"].get("conflictPolicy") != "reject"):
                    raise Problem("PROFILE_CONFLICT", "The authored profile resource conflicts with the selected admitted semantics; source is preserved.")
                if not current:
                    name = "experiment-lite" if entry["namespace"] == PROFILE_NAMESPACE else "studio-experiments"
                    resource = {"apiVersion": API_VERSION, "kind": "Profile", "metadata": {"namespace": "org.xverse.studio", "name": name, "version": entry["version"],
                                "provenance": {"source": "urn:xverse:studio:profile-registry", "revision": entry["version"], "maturity": "prototype"}},
                                "spec": {"extensionNamespace": entry["namespace"], "compatibleApiVersions": [API_VERSION], "schemaRef": entry["schemaRef"],
                                         "documentationRef": entry["documentationRef"], "conflictPolicy": "reject"}}
                    documents[uid("doc-")] = {"path": "xdl/profile-" + name + ".xdl.yaml", "format": "yaml", "content": dump_yaml(resource)}
                stem = entry["namespace"] + "-" + entry["version"]
                schema_path, presentation_path = "profiles/" + stem + ".schema.json", "profiles/" + stem + ".presentation.json"
                project["supportingFiles"][schema_path] = entry["schemaText"]
                project["supportingFiles"][presentation_path] = canonical(entry["presentation"])
                locks[entry["namespace"]] = {"namespace": entry["namespace"], "version": entry["version"], "schemaPath": schema_path,
                                            "schemaDigest": entry["schemaDigest"], "presentationPath": presentation_path, "presentationDigest": entry["presentationDigest"]}
            project["manifest"]["profiles"] = list(locks.values())
            validated = self.adapter.validate({d["path"]: d["content"] for d in documents.values()})
            if not validated["valid"]:
                raise Problem("PROFILE_CONFLICT", "The authoritative validator rejected the selected profile composition.", diagnostics=validated["diagnostics"])
            return documents
        return projects.mutate(project_id, revision, change)
