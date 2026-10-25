"""Resolve exact evaluation definitions from authoritative frozen XDL inputs."""
from copy import deepcopy
from importlib.resources import files
import hashlib
import json
from ruamel.yaml import YAML

from .evaluator import EvaluationError, validate_definition
from .dependencies import definition_order

NAMESPACE = "io.xverse.studio.experiments"
SCHEMA_ID = "https://schemas.xverse.io/studio/experiments/1.0/evaluation.schema.json"
UNIT_DEFINITIONS = {"1": {"quantity": "dimensionless", "definitionDigest": "sha256:" + hashlib.sha256(b"studio.reference.dimensionless.v1").hexdigest()}}


def definition_digest(definition):
    return "sha256:" + hashlib.sha256(json.dumps(definition, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False).encode()).hexdigest()


def snapshot_definitions(snapshot: dict, adapter) -> list[dict]:
    """The adapter must be the server's admitted pinned validator, not user data."""
    expected_digest = snapshot.get("snapshotDigest")
    original = {k: v for k, v in snapshot.items() if k != "snapshotDigest"}
    if not isinstance(expected_digest, str) or definition_digest(original) != expected_digest:
        raise EvaluationError("SNAPSHOT_INTEGRITY_INVALID")
    documents = snapshot.get("documents")
    if not isinstance(documents, dict):
        raise EvaluationError("SNAPSHOT_INPUTS_UNAVAILABLE")
    report = adapter.validate(documents)
    if report.get("valid") is not True:
        raise EvaluationError("SNAPSHOT_XDL_INVALID")
    yaml = YAML(typ="safe")
    resources = [yaml.load(source) for source in documents.values()]
    profiles = [r for r in resources if r.get("kind") == "Profile" and r.get("spec", {}).get("extensionNamespace") == NAMESPACE]
    scenarios = [r for r in resources if r.get("kind") == "Scenario"]
    systems = [r for r in resources if r.get("kind") == "System"]
    if len(profiles) != 1:
        return []
    profile = profiles[0]
    if profile.get("metadata", {}).get("version") != "1.0.0" or profile["spec"].get("schemaRef") != SCHEMA_ID:
        raise EvaluationError("PROFILE_NOT_ADMITTED")
    schema_path = files("xverse_studio.assertions").joinpath("evaluation-v1.schema.json")
    profile_digest = "sha256:" + hashlib.sha256(schema_path.read_bytes()).hexdigest()
    result = []
    seen = set()
    for scenario in scenarios:
        ns = scenario["metadata"]["namespace"]
        scenario_ref = f"xdl://{ns}/scenario/{scenario['metadata']['name']}"
        matching = [r for r in systems if r["metadata"]["namespace"] == scenario["spec"]["systemRef"].get("namespace") and r["metadata"]["name"] == scenario["spec"]["systemRef"].get("name")]
        if len(matching) != 1:
            raise EvaluationError("SYSTEM_REFERENCE_UNRESOLVED")
        system_ref = f"xdl://{matching[0]['metadata']['namespace']}/system/{matching[0]['metadata']['name']}"
        payload = scenario.get("extensions", {}).get(NAMESPACE)
        if payload is None:
            continue
        if payload.get("version") != "1.0":
            raise EvaluationError("PROFILE_VERSION_UNSUPPORTED")
        observers = {o["id"] for o in scenario["spec"].get("observers", [])}
        for definition in payload["definitions"]:
            info = validate_definition(definition)
            if definition["systemRef"] != system_ref or definition["scenarioRef"] != scenario_ref or any(ref not in observers for ref, field in info["signals"]):
                raise EvaluationError("DEFINITION_REFERENCE_UNRESOLVED")
            if definition["evaluationId"] in seen:
                raise EvaluationError("DEFINITION_ID_AMBIGUOUS")
            seen.add(definition["evaluationId"])
            result.append({"definitionRef": definition["evaluationId"], "definitionDigest": definition_digest(definition), "profileNamespace": NAMESPACE, "profileVersion": "1.0.0", "schemaDigest": profile_digest, "definition": deepcopy(definition)})
    definition_order(result)
    return result
