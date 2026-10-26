"""Narrow adapters to the pinned platform's public offline XDL API."""

from __future__ import annotations

from copy import deepcopy
from collections import OrderedDict
import hashlib
from importlib.metadata import version
from importlib.resources import files
import json
import math
from pathlib import Path, PurePosixPath
from typing import Any
import threading

from ruamel.yaml import YAML
from xverse_xdl import (
    ExperimentLimits, LoadLimits, SUPPORTED_API_VERSIONS, __version__, canonical_json,
    compile_experiment_sources, plan_matches_digest, validate_sources,
)

from .examples import (API_VERSION, CONNECTIONS_NAMESPACE, CONVERTER_BOUND, CONVERTER_TEMPLATE, EVALUATION_NAMESPACE, EVALUATION_SCHEMA_ID, PARAMETERS,
                       PROFILE_NAMESPACE, examples, reference_resources)

PLATFORM_REVISION = "7fab6a290c3731533c2b88517158055c768b9d4e"
MAX_DOCUMENTS = 128
MAX_DOCUMENT_BYTES = 1024 * 1024
VALIDATION_CACHE_ENTRIES = 8
VALIDATION_CACHE_BYTES = 8 * 1024 * 1024
VALIDATION_CACHE_SINGLE_SOURCE_BYTES = 2 * 1024 * 1024


class XDLRejected(ValueError):
    """Authored content or provider semantics are not admitted; nothing was executed."""

    def __init__(self, message: str, code: str = "CAPABILITY_UNSUPPORTED") -> None:
        super().__init__(message)
        self.code = code


def _diagnostic(d: Any, document_ids: set[str]) -> dict:
    location = None
    if d.location:
        source = d.location.source
        location = {"documentId": source if source in document_ids else None,
                    "line": d.location.line, "column": d.location.column}
    return {"code": d.code, "severity": d.severity.value, "gate": int(d.gate), "message": d.message,
            "correction": d.correction, "pointer": d.pointer,
            "elementRef": d.resource.uri if d.resource else None, "location": location}


class XDLAdapter:
    """Authoritative validation/compilation; presentation projections do not add semantics."""

    def __init__(self, profile_schema_paths: tuple = ()) -> None:
        packaged = files("xverse_xdl").joinpath("profiles", "experiment-lite-v0.1.schema.json")
        evaluation = Path(__file__).parent.parent / "assertions" / "evaluation-v1.schema.json"
        connections = Path(__file__).parent.parent / "connections" / "connections-v1.schema.json"
        domain = Path(__file__).parent.parent / "profiles" / "domain-presentation-v1.schema.json"
        self.profile_schema_paths = (str(packaged), str(evaluation), str(connections), str(domain), *tuple(str(p) for p in profile_schema_paths))
        self._validation_cache = OrderedDict()
        self._validation_cache_lock = threading.RLock()
        self._cache_result_bytes = self._cache_source_bytes = 0
        self._cache_hits = self._cache_misses = 0
        self.cache_result_limit = VALIDATION_CACHE_BYTES
        self._validator_dependencies = tuple((name, version(name)) for name in ("jsonschema", "referencing", "ruamel.yaml"))

    @property
    def identity(self) -> dict:
        return {"package": "xverse-xdl", "version": __version__, "revision": PLATFORM_REVISION,
                "apiVersions": list(SUPPORTED_API_VERSIONS), "compilerPlanVersion": "1",
                "scope": "offline_validation_and_declared_intent_compilation"}

    def _sources(self, documents: dict[str, str]) -> tuple:
        if not isinstance(documents, dict) or not 0 < len(documents) <= MAX_DOCUMENTS:
            raise XDLRejected("Supply between one and 128 explicitly named XDL documents.", "LIMIT_EXCEEDED")
        result = []
        for name, value in documents.items():
            if not isinstance(name, str) or not isinstance(value, str):
                raise XDLRejected("Document identifiers and content must be strings.", "INVALID_DOCUMENT")
            # Names are source locators, never filesystem access requests.
            if PurePosixPath(name).is_absolute() or "\\" in name or ":" in name or ".." in PurePosixPath(name).parts or len(name) > 240:
                raise XDLRejected("Use a portable relative source identifier.", "INVALID_DOCUMENT")
            data = value.encode("utf-8")
            if len(data) > MAX_DOCUMENT_BYTES:
                raise XDLRejected("An XDL document exceeds the one MiB bound.", "LIMIT_EXCEEDED")
            result.append((name, data))
        return tuple(result)

    def _validation_identity(self):
        """Fingerprint the installed validator closure and exact local schema bytes."""
        library = files("xverse_xdl")
        source_names = ("__init__.py", "models.py", "loader.py", "validate.py", "normalize.py", "diagnostics.py", "schema.py", "semantics.py")
        schema_names = ("common", "component", "deployment", "profile", "scenario", "system", "xdl")
        hasher = hashlib.sha256(b"studio.authoritative-validation-cache.v1\x00")
        try:
            hasher.update(json.dumps([self.identity, self._validator_dependencies], sort_keys=True).encode())
            paths = [("source:" + name, library.joinpath(name)) for name in source_names]
            paths.extend(("core:" + name, library.joinpath("schemas", "v1alpha1", name + ".schema.json")) for name in schema_names)
            paths.extend(("admitted:" + str(path), Path(path)) for path in self.profile_schema_paths)
            for name, path in paths:
                label, raw = name.encode(), path.read_bytes()
                hasher.update(len(label).to_bytes(8, "big"))
                hasher.update(label)
                hasher.update(len(raw).to_bytes(8, "big"))
                hasher.update(raw)
        except (OSError, ValueError):
            return None
        return hasher.digest(), id(validate_sources), id(canonical_json)

    def _validation_key(self, sources, identity):
        hasher = hashlib.sha256()
        for name, raw in sorted(sources):
            label = name.encode()
            hasher.update(len(label).to_bytes(8, "big"))
            hasher.update(label)
            hasher.update(len(raw).to_bytes(8, "big"))
            hasher.update(raw)
        return identity, hasher.digest()

    def _evict_validation(self, key):
        _, source_bytes, result_bytes = self._validation_cache.pop(key)
        self._cache_source_bytes -= source_bytes
        self._cache_result_bytes -= result_bytes

    def validation_cache_info(self):
        with self._validation_cache_lock:
            return {"entries": len(self._validation_cache), "sourceBytes": self._cache_source_bytes,
                    "resultBytes": self._cache_result_bytes, "hits": self._cache_hits, "misses": self._cache_misses,
                    "limits": {"entries": VALIDATION_CACHE_ENTRIES, "resultBytes": VALIDATION_CACHE_BYTES,
                               "sourceBytes": VALIDATION_CACHE_BYTES, "singleSourceBytes": VALIDATION_CACHE_SINGLE_SOURCE_BYTES}}

    def validate(self, documents: dict[str, str]) -> dict:
        # Authored-data bounds always precede hashing or a cache lookup.
        sources = self._sources(documents)
        source_bytes = sum(len(raw) for _, raw in sources)
        before = self._validation_identity()
        key = self._validation_key(sources, before)
        with self._validation_cache_lock:
            cached = self._validation_cache.get(key) if before is not None else None
            if cached is not None:
                report = deepcopy(cached[0])
                if self._validation_identity() == before:
                    self._validation_cache.move_to_end(key)
                    self._cache_hits += 1
                    return report
                self._evict_validation(key)
                before = self._validation_identity()
                key = self._validation_key(sources, before)
            self._cache_misses += 1
            report = self._validate_public(sources, set(documents))
            after = self._validation_identity()
            if before is not None and before == after and report.get("validationStatus") != "unavailable":
                result_bytes = len(json.dumps(report, separators=(",", ":"), ensure_ascii=False).encode())
                result_limit = min(VALIDATION_CACHE_BYTES, self.cache_result_limit)
                if source_bytes <= VALIDATION_CACHE_SINGLE_SOURCE_BYTES and result_bytes <= result_limit:
                    while self._validation_cache and (len(self._validation_cache) >= VALIDATION_CACHE_ENTRIES or self._cache_result_bytes + result_bytes > result_limit or self._cache_source_bytes + source_bytes > VALIDATION_CACHE_BYTES):
                        self._evict_validation(next(iter(self._validation_cache)))
                    self._validation_cache[key] = (deepcopy(report), source_bytes, result_bytes)
                    self._cache_source_bytes += source_bytes
                    self._cache_result_bytes += result_bytes
            return report

    def _validate_public(self, sources, document_ids):
        try:
            result = validate_sources(sources, profile_schema_paths=self.profile_schema_paths,
                                      limits=LoadLimits(max_resources=MAX_DOCUMENTS, max_bytes_per_file=MAX_DOCUMENT_BYTES))
            normalized = json.loads(canonical_json(result, include_source_map=True))
        except (OSError, AttributeError, TypeError, ValueError, RecursionError):
            # Known selected-baseline defect: malformed metadata can fail before
            # its public validator emits diagnostics. Do not invent a replacement
            # semantic judgement or expose raw exception/source values.
            return self._platform_failure("validator")
        return {"valid": result.is_valid, "diagnostics": [_diagnostic(d, document_ids) for d in result.diagnostics],
                "resources": normalized.get("resources", []), "staticReadiness": dict(result.readiness),
                "validator": self.identity}

    def _platform_failure(self, operation):
        return {"valid": False, "validationStatus": "unavailable", "diagnostics": [{
                    "code": "XDL_PLATFORM_FAILURE", "severity": "error",
                    "message": "The pinned platform could not return a validation/compilation result for these authored inputs.",
                    "correction": "Inspect the authored resource/metadata types or install an admitted corrected validator. Source is preserved and execution remains blocked."}],
                "resources": [], "staticReadiness": {}, "plan": None, "planDigest": None, "semanticDigest": None,
                "validator": self.identity, "compiler": self.identity, "failedOperation": operation}

    def compile(self, documents: dict[str, str], selection: dict | None = None) -> dict:
        # The selected compiler accepts a closed contributing set, not browser-side model selectors.
        # Caller selection must identify the set's sole System/Deployment/Scenario without discarding data.
        if selection:
            if set(selection) - {"systemRef", "deploymentRef", "scenarioRef"}:
                raise XDLRejected("Unknown compilation selection fields.", "SELECTION_UNRESOLVED")
            projected = self.project(documents)
            known = {r["ref"] for r in projected["resources"]}
            if any(ref not in known for ref in selection.values() if ref is not None):
                raise XDLRejected("The selection does not identify a supplied XDL resource.", "SELECTION_UNRESOLVED")
            for key, ref in selection.items():
                if ref is not None and f"/{key.removesuffix('Ref').lower()}/" not in ref:
                    raise XDLRejected("The selection resource kind is incompatible.", "SELECTION_UNRESOLVED")
        sources = self._sources(documents)
        try:
            result = compile_experiment_sources(sources, profile_schema_paths=self.profile_schema_paths,
                                                limits=ExperimentLimits(max_resources=MAX_DOCUMENTS, max_bytes_per_file=MAX_DOCUMENT_BYTES))
        except (AttributeError, TypeError, ValueError, RecursionError):
            return self._platform_failure("compiler")
        plan = result.plan
        return {"valid": result.is_valid, "diagnostics": [_diagnostic(d, set(documents)) for d in result.diagnostics],
                "semanticDigest": "sha256:" + plan["provenance"]["inputSemanticDigest"]["value"] if plan else None,
                "planDigest": "sha256:" + plan["digest"]["value"] if plan else None,
                "plan": plan, "compiler": self.identity}

    def project(self, documents: dict[str, str]) -> dict:
        """Return non-executable display data, retaining source IDs and exact authored content elsewhere."""
        validation = self.validate(documents)
        resources, elements, connections, parameters = [], [], [], []
        if not validation["valid"]:
            return {"resources": [], "elements": [], "connections": [], "parameters": [], "systemRef": None,
                    "valid": False, "diagnostics": validation["diagnostics"]}
        yaml = YAML(typ="safe")
        for name, source in documents.items():
            try:
                value = yaml.load(source)
            except Exception:
                continue
            if not isinstance(value, dict) or not isinstance(value.get("metadata"), dict) or not isinstance(value.get("spec"), dict):
                continue
            metadata, spec = value["metadata"], value["spec"]
            ref = f"xdl://{metadata.get('namespace', '')}/{str(value.get('kind', '')).lower()}/{metadata.get('name', '')}"
            resources.append({"ref": ref, "kind": value.get("kind"), "name": metadata.get("name"),
                              "namespace": metadata.get("namespace"), "documentId": name, "description": metadata.get("description", "")})
            if value.get("kind") == "System":
                for collection in ("nodes", "componentInstances", "devices", "sensors", "actuators", "models"):
                    for element in spec.get(collection, []):
                        if isinstance(element, dict):
                            elements.append({**deepcopy(element), "ref": ref + "#" + element.get("id", ""),
                                             "kind": collection, "documentId": name, "systemRef": ref})
                endpoints = {p.get("id"): p for p in spec.get("endpoints", []) if isinstance(p, dict)}
                for flow in spec.get("flows", []):
                    if not isinstance(flow, dict):
                        continue
                    source_endpoint = endpoints.get(flow.get("sourceEndpointId"), {})
                    for target in flow.get("destinationEndpointIds", []):
                        target_endpoint = endpoints.get(target, {})
                        connections.append({**deepcopy(flow), "ref": ref + "#" + flow.get("id", ""), "kind": "communication",
                                            "source": source_endpoint.get("ownerId"), "target": target_endpoint.get("ownerId"),
                                            "sourceEndpoint": source_endpoint, "targetEndpoint": target_endpoint,
                                            "projection": "declared", "observation": "unobserved"})
            if value.get("kind") == "Scenario":
                extension = value.get("extensions", {}).get(PROFILE_NAMESPACE, {})
                for parameter in extension.get("parameters", []):
                    if isinstance(parameter, dict):
                        schema = next((p for p in PARAMETERS if p["id"] == parameter.get("id")), {})
                        parameters.append({**deepcopy(schema), **deepcopy(parameter), "source": "scenario",
                                           "scenarioRef": ref, "documentId": name})
        return {"resources": resources, "elements": elements, "connections": connections, "parameters": parameters,
                "systemRef": next((r["ref"] for r in resources if r["kind"] == "System"), None),
                "valid": validation["valid"], "diagnostics": validation["diagnostics"]}


def reference_configuration(documents: dict[str, str], compiled: dict | None = None) -> dict:
    """Admit exactly the owned reference model; unsupported executable edits reject before launch."""
    adapter = XDLAdapter()
    actual_compile = adapter.compile(documents)
    if not actual_compile["valid"]:
        raise XDLRejected("The authoritative compiler rejected the requested inputs.", "MODEL_INVALID")
    if compiled is not None and (compiled.get("planDigest") != actual_compile["planDigest"] or compiled.get("semanticDigest") != actual_compile["semanticDigest"]):
        raise XDLRejected("Requested and effective compiled identities disagree.", "PREFLIGHT_STALE")
    plan = actual_compile["plan"]
    if not plan_matches_digest(plan):
        raise XDLRejected("The compiled plan's digest cannot be verified.", "PLAN_INTEGRITY")
    yaml = YAML(typ="safe")
    authored = [yaml.load(source) for source in documents.values()]
    systems = [r for r in authored if r.get("kind") == "System"]
    if len(systems) != 1:
        raise XDLRejected("The reference provider needs exactly one System.")
    namespace = systems[0]["metadata"]["namespace"]
    # The feedback template (ADR-0016) is admitted only as a whole: its declared loop and converter
    # are what the worker executes.
    feedback = any(isinstance(f, dict) and f.get("id") == "feedback-flow" for f in systems[0].get("spec", {}).get("flows", []) or [])
    expected = reference_resources(namespace, feedback)
    converter = None
    if feedback:
        flows = {f.get("id"): f for f in systems[0]["spec"].get("flows", []) if isinstance(f, dict)}
        converter = deepcopy(((flows.get("state-flow") or {}).get("extensions") or {}).get(CONNECTIONS_NAMESPACE, {}).get("converter"))
        if not isinstance(converter, dict):
            raise XDLRejected("The feedback reference observes its state only through its declared linear converter.", "CONVERSION_INVALID")
        for field in ("scale", "offset"):
            value = converter.get(field)
            if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) or (field == "scale" and value == 0):
                raise XDLRejected("The linear converter needs a finite non-zero scale and a finite offset.", "CONVERSION_INVALID")
            if abs(value) > CONVERTER_BOUND:
                raise XDLRejected(f"Converter coefficients are bounded by ±{CONVERTER_BOUND:g} so converted samples stay finite.", "LIMIT_EXCEEDED")
        for resource in authored:
            if resource.get("kind") == "Profile" and resource.get("spec", {}).get("extensionNamespace") == CONNECTIONS_NAMESPACE \
                    and resource.get("metadata", {}).get("version") != "1.0.0":
                raise XDLRejected("The connections profile identity is incompatible.", "PROFILE_UNRESOLVED")
    system_ref = f"xdl://{namespace}/system/reference-loop"
    deployments = [r for r in authored if r.get("kind") == "Deployment"]
    scenarios = [r for r in authored if r.get("kind") == "Scenario"]
    if len(deployments) != 1 or len(scenarios) != 1:
        raise XDLRejected("Select exactly one authored Deployment and Scenario for the reference provider.")
    scenario_ref = f"xdl://{scenarios[0]['metadata']['namespace']}/scenario/{scenarios[0]['metadata']['name']}"
    # Variant identity is independent of model behaviour. Only adjust expected
    # typed identity references for admission comparison; authored sources and
    # actual platform semantic/plan digests above remain completely unchanged.
    identity_names = {"Deployment": deployments[0]["metadata"], "Scenario": scenarios[0]["metadata"]}
    def expected_variant_identities(value):
        if isinstance(value, dict):
            if value.get("apiVersion") == API_VERSION and value.get("kind") in identity_names and "name" in value and "namespace" in value:
                chosen = identity_names[value["kind"]]
                value["name"], value["namespace"] = chosen["name"], chosen["namespace"]
            for child in value.values():
                expected_variant_identities(child)
        elif isinstance(value, list):
            for child in value:
                expected_variant_identities(child)
    for resource in expected.values():
        expected_variant_identities(resource)
    def assessment_profile(resource: dict) -> bool:
        if resource.get("kind") != "Profile" or resource.get("spec", {}).get("extensionNamespace") != EVALUATION_NAMESPACE:
            return False
        expected_spec = {"extensionNamespace": EVALUATION_NAMESPACE, "compatibleApiVersions": [API_VERSION],
                         "schemaRef": EVALUATION_SCHEMA_ID, "documentationRef": "urn:xverse:studio:experiments:1.0", "conflictPolicy": "reject"}
        if resource["metadata"]["version"] != "1.0.0" or resource["spec"] != expected_spec:
            raise XDLRejected("The assessment profile identity is incompatible.", "PROFILE_UNRESOLVED")
        return True

    def presentation_profile(resource: dict) -> bool:
        # Owned presentation-only domain profiles (T062) are inert terminology, pinned to their identity.
        from xverse_studio.profiles.presentation import DOMAIN_PROFILES, DOMAIN_SCHEMA_ID

        domains = {item["namespace"]: item for item in DOMAIN_PROFILES}
        namespace = resource.get("spec", {}).get("extensionNamespace") if resource.get("kind") == "Profile" else None
        if namespace not in domains:
            return False
        expected_spec = {"extensionNamespace": namespace, "compatibleApiVersions": [API_VERSION], "schemaRef": DOMAIN_SCHEMA_ID,
                         "documentationRef": domains[namespace]["presentation"]["documentation"], "conflictPolicy": "reject"}
        if resource.get("metadata", {}).get("version") != "1.0.0" or resource.get("spec") != expected_spec:
            raise XDLRejected("The domain presentation profile identity is incompatible.", "PROFILE_UNRESOLVED")
        return True

    authored = [r for r in authored if not presentation_profile(r)]
    assessment_profiles = [r for r in authored if assessment_profile(r)]
    for resource in authored:
        payload = resource.get("extensions", {}).get(EVALUATION_NAMESPACE)
        if payload is None:
            continue
        if resource.get("kind") != "Scenario" or len(assessment_profiles) != 1:
            raise XDLRejected("Assessment definitions require one admitted Scenario profile.", "PROFILE_UNRESOLVED")
        identifiers = set()
        for definition in payload["definitions"]:
            if definition["systemRef"] != system_ref or definition["scenarioRef"] != scenario_ref or definition["evaluationId"] in identifiers:
                raise XDLRejected("Assessment definition references do not identify this snapshot.", "PROFILE_UNRESOLVED")
            identifiers.add(definition["evaluationId"])
            def check_signals(node):
                if isinstance(node, dict):
                    if node.get("kind") == "signal" and node.get("observerRef") != "state-observer":
                        raise XDLRejected("Assessment observer is not declared by this reference model.", "PROFILE_UNRESOLVED")
                    for child in node.values():
                        check_signals(child)
                elif isinstance(node, list):
                    for child in node:
                        check_signals(child)
            check_signals(definition["expression"])
    # Compare semantic source bodies, independent of document names, comments, display metadata and ordering.
    def body(resource: dict) -> dict:
        resource = deepcopy(resource)
        resource.pop("metadata", None)
        if resource.get("kind") == "System" and feedback:
            # Converter scale/offset are run inputs; every other part of the template must match.
            for flow in resource.get("spec", {}).get("flows", []) or []:
                payload = (flow.get("extensions") or {}).get(CONNECTIONS_NAMESPACE, {}) if isinstance(flow, dict) else {}
                if isinstance(payload.get("converter"), dict):
                    payload["converter"].update(scale=CONVERTER_TEMPLATE["scale"], offset=CONVERTER_TEMPLATE["offset"])
        if resource.get("kind") == "Scenario":
            # Assessment definitions are admitted inert consumers, preserved in full platform identities.
            resource.get("extensions", {}).pop(EVALUATION_NAMESPACE, None)
            payload = resource["extensions"][PROFILE_NAMESPACE]
            payload["seed"]["value"] = 7
            for p in payload["parameters"]:
                p["value"] = next((s["default"] for s in PARAMETERS if s["id"] == p.get("id")), None)
            payload["parameters"].sort(key=lambda p: p["id"])
        return resource
    expected_bodies = sorted((body(v) for v in expected.values() if not assessment_profile(v)), key=lambda v: json.dumps(v, sort_keys=True))
    try:
        actual_bodies = sorted((body(v) for v in authored if not assessment_profile(v)), key=lambda v: json.dumps(v, sort_keys=True))
    except (KeyError, TypeError, AttributeError):
        raise XDLRejected("The selected source set is not the admitted reference blueprint.") from None
    if actual_bodies != expected_bodies:
        raise XDLRejected("The owned reference provider cannot execute this topology, deployment, schedule or extension. Select its admitted template or another compatible provider.")
    parameters = {p["id"]: p for p in plan["parameters"]}
    if set(parameters) != {p["id"] for p in PARAMETERS}:
        raise XDLRejected("The reference parameter selection is incomplete or unsupported.")
    config = {}
    for schema in PARAMETERS:
        p = parameters[schema["id"]]
        value = p["value"]
        if p.get("unitSemantics") != schema["unit"] or p.get("valueType") != schema["valueType"]:
            raise XDLRejected("Reference parameter types and units must match the admitted model.")
        if "enum" in schema:
            if value not in schema["enum"]:
                raise XDLRejected("The selected reference fault is unsupported.")
        elif isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) or not schema["minimum"] <= value <= schema["maximum"]:
            raise XDLRejected("A reference parameter exceeds its advertised finite bounds.", "LIMIT_EXCEEDED")
        config[schema["id"]] = value
    if config["gain"] * config["timestep"] > 1 or config["duration"] < config["timestep"] or config["duration"] / config["timestep"] > 3000:
        raise XDLRejected("Require gain × timestep ≤ 1 and timestep ≤ duration ≤ 3,000 steps.", "LIMIT_EXCEEDED")
    ratio = config["duration"] / config["timestep"]
    if abs(ratio - round(ratio)) > 1e-9:
        raise XDLRejected("Duration must be an integer number of reference time steps.", "LIMIT_EXCEEDED")
    config.update(seed=plan["seed"]["value"], elementRefs=[systems[0]["metadata"]["namespace"]],
                  observerRef="state-observer", clockDomain="simulation-time", planDigest=actual_compile["planDigest"],
                  semanticDigest=actual_compile["semanticDigest"])
    config["elementRefs"] = [system_ref + "#controller", system_ref + "#plant", system_ref + "#state-flow"]
    # Flows the owned worker executes; projections resolve these routes (evidence refs stay as above).
    config["resolvedFlows"] = [system_ref + "#command-flow", system_ref + "#state-flow"]
    if feedback:
        config["elementRefs"] += [system_ref + "#sensor-device", system_ref + "#state-sensor", system_ref + "#measurement-flow",
                                  system_ref + "#feedback-flow"]
        config["resolvedFlows"] += [system_ref + "#measurement-flow", system_ref + "#feedback-flow"]
        config["causality"] = {"flowRef": system_ref + "#command-flow", "kind": "unit-delay"}
        config["converter"] = {"flowRef": system_ref + "#state-flow", **{k: converter[k] for k in ("kind", "fromUnit", "toUnit")},
                               "scale": float(converter["scale"]), "offset": float(converter["offset"])}
    return config


__all__ = ["XDLAdapter", "XDLRejected", "examples", "reference_configuration"]
