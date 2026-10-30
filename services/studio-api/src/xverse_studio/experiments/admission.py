"""Coherent read-only Scenario authoring inspection, separate from live readiness."""

from copy import deepcopy

from xverse_studio.deployments import compile_selection
from xverse_studio.storage.core import Problem, digest
from xverse_studio.xdl import XDLRejected
from .observations import observation_admission, selected_scenario, text


class ScenarioAdmission:
    def __init__(self, projects, adapter, descriptor_source, configuration_for):
        self.projects, self.adapter = projects, adapter
        self.descriptor_source, self.configuration_for = (
            descriptor_source,
            configuration_for,
        )

    def inspect(self, project_id, revision, provider_id, scenario_ref=None):
        project = self.projects.read(project_id)
        if project["revision"] != revision:
            raise Problem(
                "REVISION_CONFLICT",
                "Select the current authored project revision.",
                412,
                currentRevision=project["revision"],
            )
        self.projects.assert_intact(project)
        documents = deepcopy(self.projects.sources(project))
        provider = next(
            (
                deepcopy(v)
                for v in self.descriptor_source()
                if v["providerId"] == provider_id
            ),
            None,
        )
        if provider is None:
            raise Problem(
                "PROVIDER_UNAVAILABLE",
                "No installed descriptor has the selected identity.",
                404,
            )
        compiled = compile_selection(
            documents,
            {"scenarioRef": scenario_ref} if scenario_ref else None,
            self.adapter,
        )
        contributing = (
            compiled["contributingDocuments"] if compiled["valid"] else documents
        )
        scenario = selected_scenario(contributing, compiled)
        observations = observation_admission(scenario, provider)
        diagnostics = deepcopy(compiled["diagnostics"]) + observations["diagnostics"]
        mapping = "unsupported"
        if compiled["valid"]:
            try:
                self.configuration_for(provider_id, provider, contributing, compiled)
                mapping = "supported"
            except XDLRejected as error:
                diagnostics.append(
                    {"code": error.code, "severity": "error", "message": str(error)}
                )
            except Exception:
                mapping = "unknown"
                diagnostics.append(
                    {
                        "code": "SCENARIO_INSPECTION_UNAVAILABLE",
                        "severity": "error",
                        "message": "The installed provider source inspection is unavailable; no readiness or runtime call was made.",
                    }
                )
        spec = (scenario or {}).get("spec", {})
        steps = []
        faults = []
        for item in spec.get("steps", [])[:64]:
            steps.append(
                {
                    "stepId": item["id"],
                    "targetRef": deepcopy(item["targetRef"]),
                    "clockDomain": item["timeDomainId"],
                    "actionKind": text(item["actionKind"]),
                    "schedule": deepcopy(item["schedule"]),
                    "effectStatus": "declared_intent_only",
                }
            )
        for item in spec.get("faults", [])[:32]:
            faults.append(
                {
                    "faultId": item["id"],
                    "targetRef": deepcopy(item["targetRef"]),
                    "faultKind": text(item["faultKind"]),
                    "activation": "opaque_declared_intent",
                    "recovery": "opaque_declared_intent",
                    "effectStatus": "declared_intent_only",
                }
            )
        return {
            "scenarioAdmissionVersion": "1.0",
            "readOnly": True,
            "projectId": project_id,
            "revision": revision,
            "providerId": provider_id,
            "providerVersion": provider["providerVersion"],
            "providerIdentityDigest": digest(provider),
            "selection": compiled["selection"],
            "projectRevisionInputsDigest": compiled["projectRevisionInputsDigest"],
            "sourceValid": compiled["valid"],
            "semanticDigest": compiled["semanticDigest"],
            "planDigest": compiled["planDigest"],
            "sourceMapping": mapping,
            "status": "blocked"
            if diagnostics or mapping != "supported"
            else "preflight_required",
            "diagnostics": diagnostics[:100],
            "diagnosticsComplete": len(diagnostics) <= 100,
            "steps": steps,
            "stepsComplete": len(spec.get("steps", [])) <= 64,
            "faults": faults,
            "faultsComplete": len(spec.get("faults", [])) <= 32,
            "observations": observations,
            "limitations": [
                "Static source support is not live readiness; fresh preflight and Start remain required.",
                "Declared intent does not establish observed effects, clock synchronization or assertion verdicts.",
            ],
        }
