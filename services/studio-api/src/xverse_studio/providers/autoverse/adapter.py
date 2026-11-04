"""Installed provider admission; never accepts executable instructions from XDL."""
from copy import deepcopy
from pathlib import Path
import platform
import subprocess
from ruamel.yaml import YAML
from xverse_studio.blueprints.autoverse import resources, NAMESPACE, CONTRACT_REF
from xverse_studio.storage.core import digest
from .installation import InstallationError, verify

PROVIDER_ID = "autoverse.demo"
PROVIDER_VERSION = "0.4.0"
EXTERNAL_CONTRACT = {"version": "1.0", "kind": "communication", "providerId": PROVIDER_ID,
                     "contractRef": CONTRACT_REF, "feedback": "externally-managed-asynchronous-communication"}


def configuration(documents, compiled):
    return configuration_for(documents, compiled, resources, CONTRACT_REF, allow_input_loss=True)


def configuration_for(documents, compiled, resource_factory, contract_ref, *, allow_input_loss=False):
    if not compiled.get("valid"):
        return None
    try:
        actual = {Path(name).name: YAML(typ="safe").load(source) for name, source in documents.items()}
        if len(actual) != len(documents):
            return None
        input_surface = actual["scenario.xdl.yaml"]["extensions"][NAMESPACE]["inputSurface"]
        expected = resource_factory(input_surface)
        assessment = None
        if allow_input_loss:
            from .assessments import admit_sources
            assessment, expected = admit_sources(actual, expected, documents)
        if set(actual) != set(expected):
            return None
        duration = actual["scenario.xdl.yaml"]["extensions"][NAMESPACE]["durationSeconds"]
        if type(duration) is not int or not 30 <= duration <= 1800:
            return None
        expected["scenario.xdl.yaml"]["extensions"][NAMESPACE]["durationSeconds"] = duration
        loss = None
        faults = actual["scenario.xdl.yaml"]["spec"].get("faults")
        if faults:
            if not allow_input_loss:
                return None
            from .input_loss import compile_input_loss
            loss = compile_input_loss(actual["scenario.xdl.yaml"], compiled, duration, input_surface)
            expected["scenario.xdl.yaml"]["spec"]["faults"] = deepcopy(faults)
        # Presentation/provenance text is inert. Every executable field and stable
        # metadata identity is compared, including unknown extension payloads.
        for name in actual:
            value = deepcopy(actual[name])
            for key in ("description", "provenance", "labels", "annotations"):
                value.get("metadata", {}).pop(key, None)
                expected[name]["metadata"].pop(key, None)
            if digest(value) != digest(expected[name]):
                return None
        return {"contractRef": contract_ref, "durationSeconds": duration, "physicalEffects": False, "inputSurface": input_surface,
                "simulatorAdvancement": "public-vehicle-cli-synchronous", "fixedDeltaSeconds": 0.05,
                "sourceClockMapping": "unavailable", "randomness": "external_uncontrolled_no_applied_seed", **({"inputLoss": loss} if loss else {}), **({"assessment": assessment} if assessment else {})}
    except (ValueError, KeyError, TypeError):
        return None


class AutoverseProvider:
    worker_module = "xverse_studio.providers.autoverse.worker"
    controls = ["stop", "cancel"]
    provider_version = PROVIDER_VERSION
    input_loss_schedules = True
    campaigns_enabled = True
    reruns_enabled = True
    max_observers = 2
    observation_contract = {"contractVersion": "1.0", "observers": [{"observerId": "autoverse-telemetry",
        "costs": [{"value": 1, "unit": "observer-slot"}],
        "intrusiveness": "Interface subscriptions; driving publication is separately controlled by the input lease."},
        {"observerId": "autoverse-fault-records", "costs": [{"value": 0, "unit": "observer-slot"}],
         "intrusiveness": "Retrospective reads of existing recorded acknowledgement events; no new live subscription. CPU, storage and latency are not attested by subscription slots."}],
        "budgets": [{"unit": "observer-slot", "maximum": 1}]}

    configuration = staticmethod(configuration)

    def __init__(self, installation):
        self.installation = deepcopy(installation)

    def descriptor(self):
        implementation = digest(b"".join(p.read_bytes() for p in sorted(Path(__file__).parent.glob("*.py"))))
        from .input_loss import DESCRIPTOR
        from .assessments import DESCRIPTOR as ASSESSMENTS
        from .campaigns import CONTRACT as CAMPAIGNS
        from xverse_studio.runs.frozen import CONTRACT as RERUNS
        return {"providerId": PROVIDER_ID, "providerVersion": self.provider_version,
                **({"campaignContract": deepcopy(CAMPAIGNS)} if self.campaigns_enabled else {}),
                **({"rerunContract": {**RERUNS, "sourceVersions": ["0.3.0", "0.4.0"]}} if self.reruns_enabled else {}),
                **({"assessmentContract": deepcopy(ASSESSMENTS)} if self.input_loss_schedules else {}),
                **({"scenarioContracts": deepcopy(DESCRIPTOR)} if self.input_loss_schedules else {}),
                **({"observationContracts": deepcopy(self.observation_contract)} if self.observation_contract is not None else {}), "contractVersion": "1.0",
                "name": "Autoverse complete demo", "maturity": "prototype", "available": True,
                "hostCompatible": platform.system() == "Linux", "supportedHostOS": ["Linux"], "architectures": ["x86_64"],
                "evidenceScope": "external_demo", "implementationDigest": implementation,
                "installationDigest": self.installation["identityDigest"], "operations": ["start", *self.controls],
                "clockDomains": ["host-runtime"], "realizationClasses": ["simulated", "virtual"],
                "targetClasses": ["process", "container"], "hostExecutionClass": "native-process-and-existing-containers",
                "connectionContracts": {"externalRuntime": EXTERNAL_CONTRACT},
                "supportedInputSurfaces": ["native-pygame", "studio-browser"],
                "inputSurface": {"kind": "normalized-driver", "version": "1.0", "leaseSeconds": 0.75, "companionLabel": "Android digital cluster", "companionUrl": "https://localhost:8443"},
                "limits": {"maxObservers": self.max_observers, "maxDurationSeconds": 1800, "maxConcurrentRuns": 1, "maxElements": 6, "maxConnections": 32},
                "capabilityRecords": [{"kind": kind, "targetClass": "process", "legalStates": ["ready"] if kind == "start" else ["preparing", "running", "ready"],
                    "parametersSchema": {"type": "object", "additionalProperties": False},
                    "authorityRequirements": ["native-backend-owned", "exclusive-demo-installation"], "physicalEffects": False} for kind in ["start", *self.controls]],
                "limitations": ["Linux installation only; external simulation time and deterministic replay unavailable.",
                                "Input acceptance means publication, not vehicle acknowledgement. No native X-COM or physical vehicle."]}

    def campaign_documents(self, sources, parameters):
        from .campaigns import documents
        return documents(self, sources, parameters)

    def assessment_context(self, run, snapshot):
        from .assessments import context
        return context(self, run, snapshot)

    def assessment_projection(self, run, snapshot, records, integrity):
        from .assessments import project
        return project(run, snapshot, records, integrity)

    def timeline_context(self, run, snapshot):
        from .timeline import context
        return context(self, run, snapshot)

    def readiness(self, documents, compiled, provider_id, provider, active_count):
        config = self.configuration(documents, compiled)
        code = None
        if config is None:
            code = "AUTOVERSE_SOURCE_UNSUPPORTED"
        elif active_count:
            code = "RESOURCE_BUSY"
        else:
            try:
                self.verify_installation()
            except (InstallationError, OSError, subprocess.SubprocessError) as error:
                code = str(error) if isinstance(error, InstallationError) else "AUTOVERSE_INSTALLATION_UNAVAILABLE"
        fact = {"status": "blocked" if code else "available", "message": code or "Pinned existing installation is available; exclusive ownership is acquired only by the worker.",
                "facts": {"installationDigest": self.installation["identityDigest"], "reserved": False}}
        checks = {key: deepcopy(fact) for key in ("provider", "artifacts", "resources", "ownership", "target", "authority")}
        checks["backend"] = {"status": "available", "message": "The native Studio control service is available."}
        checks["model"] = {"status": "valid" if compiled.get("valid") else "invalid", "message": "Authoritative XDL compilation is evaluated separately from live readiness."}
        checks["capabilities"] = {"status": "compatible" if config else "unsupported", "message": "Exact supported source mapping evaluated; unsupported semantic edits block execution."}
        checks["clocks"] = {"status": "compatible", "message": "Host receipt time only; source simulation time remains unmapped.", "facts": {"sourceMapping": "unavailable"}}
        errors = [] if not code else [{"code": code, "severity": "error", "message": "The installed demo cannot start: " + code,
                                     "remediation": "Restore the pinned stopped installation or resolve the reported resource conflict, then preflight again."}]
        return checks, errors, config if not code else None, self.descriptor()["limits"]

    def verify_installation(self):
        verify(self.installation)

    def input_request(self, root, action, payload, session):
        from .input import input_request
        return input_request(root, action, payload, session)

    def run_metadata(self, config):
        if config["inputSurface"] == "native-pygame":
            return {"inputSurface": {"kind": "native-window", "version": "1.0", "title": "Vehicle Manual Control",
                "keyboardOnly": True, "location": "Studio host desktop",
                "instructions": "Use the original Pygame Vehicle Manual Control window on the computer running Studio. W/Up: throttle; S/Down: brake; A/D or Left/Right: steering; C: cruise; Z/X: cruise speed; Q: reverse.",
                "companionLabel": "Android digital cluster", "companionUrl": "https://localhost:8443"}}
        return {"inputSurface": self.descriptor()["inputSurface"]}
