"""Authored deployment/scenario variants and explicit authoritative compiler contributors."""
from __future__ import annotations

from copy import deepcopy
import platform
import re

from ruamel.yaml import YAML

from xverse_studio.storage.core import Problem, digest, uid
from xverse_studio.xdl import XDLAdapter, reference_configuration, XDLRejected
from xverse_studio.xdl.edits import semantic_edits
from xverse_studio.xdl.examples import EVALUATION_NAMESPACE, PROFILE_NAMESPACE, dump_yaml

from .resolution import RESOLUTION_VERSION, resolution_diagnostics, resolve_deployment


def resource_ref(resource):
    return f"xdl://{resource['metadata']['namespace']}/{resource['kind'].lower()}/{resource['metadata']['name']}"


def authored_ref(reference):
    return f"xdl://{reference['namespace']}/{reference['kind'].lower()}/{reference['name']}"


def compile_selection(documents, selection=None, adapter=None):
    """Validate the complete authored set, then compile its explicitly selected closed contributors.

    No source is rewritten to satisfy selection. Other variants remain authored but are not
    competing inputs to the selected one-Deployment/one-Scenario platform compiler contract.
    """
    adapter = adapter or XDLAdapter()
    selection = {k: v for k, v in (selection or {}).items() if v is not None}
    if set(selection) - {"systemRef", "deploymentRef", "scenarioRef"}:
        raise Problem("SELECTION_UNRESOLVED", "Unknown compilation-selection fields.")
    full_digest = digest(documents)
    validation = adapter.validate(documents)
    if not validation["valid"]:
        return {"valid": False, "diagnostics": validation["diagnostics"], "plan": None, "planDigest": None, "semanticDigest": None,
                "compiler": adapter.identity, "contributingDocuments": {}, "projectRevisionInputsDigest": full_digest, "selection": selection}
    yaml = YAML(typ="safe")
    parsed = {name: yaml.load(source) for name, source in documents.items()}
    indexed = {resource_ref(resource): (name, resource) for name, resource in parsed.items()}
    for field, kind in (("systemRef", "System"), ("deploymentRef", "Deployment"), ("scenarioRef", "Scenario")):
        if field in selection and (selection[field] not in indexed or indexed[selection[field]][1]["kind"] != kind):
            raise Problem("SELECTION_UNRESOLVED", "A selected resource is absent or has the wrong XDL kind.")
    scenarios = [(name, resource) for name, resource in parsed.items() if resource["kind"] == "Scenario"]
    if selection.get("scenarioRef"):
        scenarios = [indexed[selection["scenarioRef"]]]
    elif selection.get("deploymentRef"):
        scenarios = [(name, resource) for name, resource in scenarios if resource["spec"].get("deploymentRef")
                     and authored_ref(resource["spec"]["deploymentRef"]) == selection["deploymentRef"]]
    if selection.get("systemRef"):
        scenarios = [(name, resource) for name, resource in scenarios if authored_ref(resource["spec"]["systemRef"]) == selection["systemRef"]]
    if len(scenarios) != 1:
        raise Problem("SELECTION_AMBIGUOUS", "Select one Scenario and its compatible Deployment explicitly.")
    scenario_name, scenario = scenarios[0]
    system_ref = authored_ref(scenario["spec"]["systemRef"])
    declared_deployment = scenario["spec"].get("deploymentRef")
    if not declared_deployment:
        raise Problem("SELECTION_UNRESOLVED", "The selected Scenario has no declared Deployment.")
    deployment_ref = authored_ref(declared_deployment)
    if selection.get("deploymentRef") and selection["deploymentRef"] != deployment_ref:
        raise Problem("SELECTION_INCOMPATIBLE", "The selected Scenario is authored for another Deployment; select or author a matching Scenario.")
    if deployment_ref not in indexed or system_ref not in indexed:
        raise Problem("SELECTION_UNRESOLVED", "The selected System/Deployment is absent from the explicit authored set.")
    system_name, _ = indexed[system_ref]
    deployment_name, deployment = indexed[deployment_ref]
    if authored_ref(deployment["spec"]["systemRef"]) != system_ref:
        raise Problem("SELECTION_INCOMPATIBLE", "The selected Deployment belongs to a different System.")
    included = {scenario_name, system_name, deployment_name}
    included.update(name for name, resource in parsed.items() if resource["kind"] in {"Component", "Profile"})
    contributors = {name: source for name, source in documents.items() if name in included}
    resolved = {"systemRef": system_ref, "deploymentRef": deployment_ref, "scenarioRef": resource_ref(scenario)}
    compiled = adapter.compile(contributors, resolved)
    return {**compiled, "contributingDocuments": contributors, "projectRevisionInputsDigest": full_digest, "selection": resolved}


class Deployments:
    def __init__(self, projects, adapter):
        self.projects, self.adapter = projects, adapter

    def list(self, project_id):
        project = self.projects.read(project_id)
        validation = self.adapter.validate(self.projects.sources(project))
        if not validation["valid"]:
            return {"items": [], "revision": project["revision"], "diagnostics": validation["diagnostics"], "nextCursor": None}
        yaml = YAML(typ="safe")
        resources = {identifier: yaml.load(document["content"]) for identifier, document in project["documents"].items()}
        scenarios = [resource for resource in resources.values() if resource["kind"] == "Scenario"]
        systems = {resource_ref(resource): resource for resource in resources.values() if resource["kind"] == "System"}
        result = []
        for identifier, resource in resources.items():
            if resource["kind"] != "Deployment":
                continue
            ref = resource_ref(resource)
            matches = [resource_ref(scenario) for scenario in scenarios if scenario["spec"].get("deploymentRef") and authored_ref(scenario["spec"]["deploymentRef"]) == ref]
            result.append({"variantId": identifier, "documentId": identifier, "ref": ref, "name": resource["metadata"]["name"],
                           "description": resource["metadata"].get("description", ""), "systemRef": authored_ref(resource["spec"]["systemRef"]),
                           "bindings": resource["spec"].get("bindings", []), "targets": resource["spec"].get("targets", []),
                           "artifacts": resource["spec"].get("artifacts", []), "resources": resource["spec"].get("resources", []),
                           "timeMappings": resource["spec"].get("timeMappings", []),
                           "timeDomains": [d.get("id") for d in systems.get(authored_ref(resource["spec"]["systemRef"]), {}).get("spec", {}).get("timeDomains", []) or []],
                           "scenarioRefs": matches,
                           "readiness": "preflight_required", "limitations": ["Static XDL compatibility does not establish artifact availability, provider support or behavioural equivalence."]})
        return {"items": result, "revision": project["revision"], "diagnostics": [], "nextCursor": None}

    def resolution(self, project_id, document_id, provider_id="studio.reference", *, revision=None):
        """Deployment resolution 1.0 (ADR-0015) for one authored Deployment document; read-only."""
        project = self.projects.read(project_id)
        if revision is not None:
            from .comparison import require_revision
            require_revision(project, revision)
        self.projects.assert_intact(project)
        document = project["documents"].get(document_id)
        if document is None:
            raise Problem("NOT_FOUND", "Deployment document not found.", 404)
        documents = self.projects.sources(project)
        validation = self.adapter.validate(documents)
        if not validation["valid"]:
            return {"resolutionVersion": RESOLUTION_VERSION, "documentId": document_id, "revision": project["revision"],
                    "sourceValid": False, "diagnostics": validation["diagnostics"], "bindings": [], "constraints": [],
                    "parameters": [], "environment": [], "portability": [], "portableIntent": None}
        resource = YAML(typ="safe").load(document["content"])
        if not isinstance(resource, dict) or resource.get("kind") != "Deployment":
            raise Problem("NOT_FOUND", "Deployment document not found.", 404)
        return {**self._resolve(documents, resource_ref(resource), provider_id), "documentId": document_id,
                "revision": project["revision"]}

    def comparison(self, project_id, left_id, right_id, revision, provider_id="studio.reference"):
        from .comparison import compare
        return compare(self, project_id, left_id, right_id, revision, provider_id)

    def _resolve(self, documents, deployment_ref, provider_id="studio.reference", *, provider=None):
        from xverse_studio.connections import admit_connections
        from xverse_studio.providers.registry import descriptors

        if provider is None:
            provider = next((value for value in descriptors() if value["providerId"] == provider_id), None)
        if provider is None:
            raise Problem("PROVIDER_UNAVAILABLE", "No provider descriptor has this identity.", 404)
        report = resolve_deployment(documents, deployment_ref, host_os=platform.system(), provider=provider)
        # Connection compatibility also depends on the provider's declared contracts (ADR-0016).
        # Summarized here for rebinding; preflight reports its blocking diagnostics itself.
        admission = admit_connections(documents, self.adapter.validate(documents), provider)
        connections = {"providerId": provider_id, "blocking": admission["blocking"],
                       "admittedContracts": admission["admittedContracts"],
                       "notAdmitted": sorted(c["ref"] for c in admission["connections"] if c["admission"] != "admitted"),
                       "cycles": [{"members": c["members"], "status": c["status"]} for c in admission["cycles"]]}
        return {**report, "sourceValid": True, "diagnostics": resolution_diagnostics(report), "connections": connections}

    def create(self, project_id, revision, value):
        if not isinstance(value, dict) or set(value) - {"name", "sourceDeploymentId", "sourceScenarioId"}:
            raise Problem("VARIANT_INVALID", "Unsupported deployment-variant fields.")
        label = value.get("name")
        if not isinstance(label, str) or not 1 <= len(label) <= 120:
            raise Problem("VARIANT_INVALID", "Choose a bounded deployment name.")
        slug = re.sub(r"[^a-z0-9]+", "-", label.casefold()).strip("-")
        if not slug or not slug[0].isalpha() or len(slug) > 54:
            raise Problem("VARIANT_INVALID", "The variant name must yield a portable letter-starting XDL identifier of at most 54 characters.")
        created = {}
        yaml = YAML(typ="safe")
        def change(project):
            self.projects.assert_intact(project)
            documents = project["documents"]
            if not self.adapter.validate(self.projects.sources(project))["valid"]:
                raise Problem("MODEL_INVALID", "Resolve authoritative diagnostics before cloning a variant.")
            parsed = {identifier: yaml.load(document["content"]) for identifier, document in documents.items()}
            deployments = [(identifier, resource) for identifier, resource in parsed.items() if resource["kind"] == "Deployment"
                           and (not value.get("sourceDeploymentId") or identifier == value["sourceDeploymentId"])]
            if len(deployments) != 1:
                raise Problem("SELECTION_AMBIGUOUS", "Select one existing source Deployment document.")
            _, source = deployments[0]
            if sum(resource["kind"] == "Deployment" for resource in parsed.values()) >= 16:
                raise Problem("LIMIT_EXCEEDED", "A project retains at most 16 authored deployment variants.")
            scenarios = [(identifier, resource) for identifier, resource in parsed.items() if resource["kind"] == "Scenario"
                         and resource["spec"].get("deploymentRef") and authored_ref(resource["spec"]["deploymentRef"]) == resource_ref(source)
                         and (not value.get("sourceScenarioId") or identifier == value["sourceScenarioId"])]
            if len(scenarios) != 1:
                raise Problem("SELECTION_AMBIGUOUS", "Select one Scenario authored for the source Deployment.")
            deployment = deepcopy(source)
            scenario = deepcopy(scenarios[0][1])
            assessment = scenario.get("extensions", {}).get(EVALUATION_NAMESPACE, {}).get("definitions", [])
            assessment_order = []
            if assessment:
                from xverse_studio.assertions.dependencies import definition_order
                from xverse_studio.assertions.snapshot import definition_digest
                from xverse_studio.assertions.evaluator import EvaluationError
                try:
                    assessment_order = [entry["definition"]["evaluationId"] for entry in definition_order([
                        {"definition": definition, "definitionDigest": definition_digest(definition)} for definition in assessment])]
                except EvaluationError as error:
                    raise Problem("ASSESSMENT_CONFLICT", "Resolve the source Scenario's named assessment dependency identities before cloning.", diagnostics=[{"code": error.code}]) from None
            namespace = deployment["metadata"]["namespace"]
            deployment["metadata"].update(name=slug, description=label)
            scenario["metadata"].update(name=slug + "-scenario", description=label + " scenario")
            new_ref = resource_ref(deployment)
            if any(resource_ref(resource) in {new_ref, resource_ref(scenario)} for resource in parsed.values()):
                raise Problem("IDENTITY_CONFLICT", "This deployment/scenario identity already exists.")
            scenario["spec"]["deploymentRef"]["name"] = slug
            for extension in scenario.get("extensions", {}).values():
                if isinstance(extension, dict) and isinstance(extension.get("target"), dict) and extension["target"].get("kind") == "Scenario":
                    extension["target"]["name"] = scenario["metadata"]["name"]
            for step in [*scenario["spec"].get("steps", []), *scenario["spec"].get("faults", [])]:
                payload = step.get("extensions", {}).get(PROFILE_NAMESPACE)
                if payload:
                    payload["target"]["name"] = scenario["metadata"]["name"]
            for definition in scenario.get("extensions", {}).get(EVALUATION_NAMESPACE, {}).get("definitions", []):
                definition["scenarioRef"] = resource_ref(scenario)
            if assessment_order:
                from xverse_studio.assertions.dependencies import metric_references
                from xverse_studio.assertions.snapshot import definition_digest
                by_id = {definition["evaluationId"]: definition for definition in assessment}
                for identifier in assessment_order:
                    for reference in metric_references(by_id[identifier]["expression"]):
                        referenced = by_id[reference["evaluationId"]]
                        reference["definitionDigest"] = definition_digest(referenced)
                        reference["version"] = referenced["version"]
            document_id, scenario_id = uid("doc-"), uid("doc-")
            documents[document_id] = {"path": "xdl/deployment-" + slug + ".xdl.yaml", "format": "yaml", "content": dump_yaml(deployment)}
            documents[scenario_id] = {"path": "xdl/scenario-" + slug + ".xdl.yaml", "format": "yaml", "content": dump_yaml(scenario)}
            candidate = {document["path"]: document["content"] for document in documents.values()}
            validation = self.adapter.validate(candidate)
            if not validation["valid"]:
                raise Problem("VARIANT_INVALID", "The authoritative validator rejected the cloned variant.", diagnostics=validation["diagnostics"])
            created.update(documentId=document_id, ref=new_ref, namespace=namespace)
            return documents
        project = self.projects.mutate(project_id, revision, change)
        variant = next(item for item in self.list(project_id)["items"] if item["documentId"] == created["documentId"])
        return {"project": project, "variant": variant}

    def update_binding(self, project_id, revision, document_id, value, provider_id="studio.reference"):
        if not isinstance(value, dict) or set(value) - {"bindingId", "targetId", "realizationClass", "artifactIds", "resourceIds", "scenarioRef"}:
            raise Problem("BINDING_INVALID", "Unsupported binding fields.")
        readiness, resolution = {}, {}
        def change(project):
            if document_id not in project["documents"]:
                raise Problem("NOT_FOUND", "Deployment document not found.", 404)
            source = self.projects.sources(project)
            try:
                updated = semantic_edits(source, [{"kind": "set_binding", "documentId": project["documents"][document_id]["path"], **{key: item for key, item in value.items() if key != "scenarioRef"}}])
            except XDLRejected as error:
                raise Problem(error.code, str(error)) from None
            resource = YAML(typ="safe").load(updated[project["documents"][document_id]["path"]])
            selection = {"deploymentRef": resource_ref(resource)}
            if value.get("scenarioRef"):
                selection["scenarioRef"] = value["scenarioRef"]
            # Resolve every fallible selection/admission operation before committing
            # authored bytes. An ambiguous request never advances the revision.
            compiled = compile_selection(updated, selection, self.adapter)
            readiness.update(status="blocked", diagnostics=compiled["diagnostics"])
            if compiled["valid"]:
                resolution.update(self._resolve(updated, selection["deploymentRef"], provider_id))
            if compiled["valid"]:
                try:
                    reference_configuration(compiled["contributingDocuments"], compiled)
                    readiness.update(status="preflight_required", diagnostics=[])
                except XDLRejected as error:
                    readiness["diagnostics"] = [{"code": error.code, "severity": "error", "message": str(error)}]
                if resolution["diagnostics"]:
                    readiness.update(status="blocked", diagnostics=[*readiness["diagnostics"], *resolution["diagnostics"]])
            return {identifier: {**document, "content": updated[document["path"]]} for identifier, document in project["documents"].items()}
        project = self.projects.mutate(project_id, revision, change)
        variant = next(item for item in self.list(project_id)["items"] if item["documentId"] == document_id)
        return {"project": project, "variant": variant, "compatibility": readiness, "resolution": resolution or None}
