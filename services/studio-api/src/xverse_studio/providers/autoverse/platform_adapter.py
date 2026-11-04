"""Explicit installed platform mode. Historical classic runs remain separate."""
from xverse_studio.blueprints.autoverse import PLATFORM_CONTRACT_REF, PLATFORM_PROVIDER_ID, platform_resources
from xverse_studio.storage.core import digest
from xverse_studio.xdl import PLATFORM_REVISION
from .adapter import AutoverseProvider, configuration_for
from .platform_installation import verify_platform


def platform_configuration(documents, compiled):
    config = configuration_for(documents, compiled, platform_resources, PLATFORM_CONTRACT_REF)
    if config is not None:
        config.update(platformIntegration="public-maestro-native-xcom-argus-v1", nativeBoundaryRoutes=11,
                      nativeSampledRoutes=3, nativeSourceClockMapping="unavailable")
    return config


class PlatformProvider(AutoverseProvider):
    provider_version = "0.1.0"
    input_loss_schedules = False
    campaigns_enabled = False
    reruns_enabled = False
    max_observers = 4
    observation_contract = None
    worker_module = "xverse_studio.providers.autoverse.maestro_worker"
    configuration = staticmethod(platform_configuration)
    shutdown_timeout_seconds = 75

    def __init__(self, installation):
        super().__init__(installation)
        import threading
        self._owner = None
        self._owner_lock = threading.RLock()

    def prepare_backend_task(self, root):
        from .platform_owner import PlatformOwner
        with self._owner_lock:
            if self._owner is None:
                self._owner = PlatformOwner(self.installation, self)
            return self._owner.prepare_task(root)

    def close_backend_owner(self):
        with self._owner_lock:
            return self._owner is None or self._owner.close()

    def readiness(self, documents, compiled, provider_id, provider, active_count):
        checks, errors, config, limits = super().readiness(documents, compiled, provider_id, provider, active_count)
        for error in errors:
            if error["code"] == "AUTOVERSE_PLATFORM_OWNER_RECOVERY_REQUIRED":
                error["message"] = "The original Maestro owner is unavailable; this registration cannot execute again."
                error["remediation"] = ("Retain its claims and evidence. Stop this backend and use the host recovery command "
                    "to inspect and explicitly retire released predecessor runs. Unknown cleanup remains blocked.")
        return checks, errors, config, limits

    def platform_evidence_binding(self, run, snapshot):
        """Host-selected historical source; never re-enroll assets just to read.

        The frozen descriptor records the run's installation/implementation, which
        can legitimately differ from today's installed reader wrapper.
        """
        import re
        from pathlib import Path
        from ruamel.yaml import YAML
        from xverse_xdl import ResourceIdentity
        from xverse_studio.platform_observability.argus import ArgusBinding
        from xverse_studio.platform_observability.views import PlatformEvidenceBinding
        from xverse_studio.storage.core import Problem

        rid = run["runId"]
        frozen = snapshot["providerIdentity"]
        if (not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]{0,127}", rid)
                or run["providerId"] != PLATFORM_PROVIDER_ID or frozen["providerId"] != PLATFORM_PROVIDER_ID
                or not frozen.get("platformIntegration")):
            raise Problem("PLATFORM_SOURCE_UNAVAILABLE", "This run has no admitted platform evidence binding.", 404)
        registered = Path(self.installation["nativeBridge"]["runtimeRoot"])
        root = registered / (rid + ".argus")
        if not root.exists():
            raise Problem("PLATFORM_SOURCE_UNAVAILABLE", "Platform evidence is not available yet for this run. Refresh after Maestro opens its evidence writer.", 404)
        if root.resolve() != root.absolute() or not root.resolve().is_relative_to(registered.resolve()):
            raise Problem("PLATFORM_SOURCE_CHANGED", "The registered platform evidence root changed.", 409)
        owners = []
        for raw in snapshot["documents"].values():
            document = YAML(typ="safe").load(raw)
            if document.get("kind") == "System":
                uri = ResourceIdentity.from_mapping(document).uri
                owners.extend((uri + "#" + e["id"], uri + "#" + e["ownerId"])
                              for e in document["spec"].get("endpoints", []))
        return PlatformEvidenceBinding(ArgusBinding("argus-" + digest(rid)[7:39], root, rid, snapshot["planDigest"]),
            snapshot["semanticDigest"], PLATFORM_PROVIDER_ID, frozen["installationDigest"],
            frozen["implementationDigest"], tuple(owners),
            (("urn:xverse:autoverse:wire-utf8-number:v1", "utf8-finite-number"),
             ("urn:xverse:autoverse:wire-utf8-boolean:v1", "utf8-boolean")))

    def verify_installation(self):
        from .platform_owner import PlatformOwner, prior_owner
        with self._owner_lock:
            if self._owner is not None:
                self._owner.assert_available()
            elif prior_owner(self.installation):
                self._owner = PlatformOwner(self.installation, self)
                self._owner.assert_available()
        verify_platform(self.installation)

    def descriptor(self):
        from pathlib import Path
        value = super().descriptor()
        native = self.installation["nativeBridge"]
        value.update(providerId=PLATFORM_PROVIDER_ID, name="Autoverse with X-Verse platform",
            evidenceScope="platform_simulation", supportedInputSurfaces=["native-pygame"],
            implementationDigest=digest({"python": value["implementationDigest"], "sdkRevision": PLATFORM_REVISION,
                "nativeSources": native["nativeSources"],
                "backendTask": digest(Path(__file__).parent.parent.joinpath("backend_task.py").read_bytes())}),
            connectionContracts={"externalRuntime": {"version": "1.0", "kind": "communication",
                "providerId": PLATFORM_PROVIDER_ID, "contractRef": PLATFORM_CONTRACT_REF,
                "feedback": "externally-managed-asynchronous-communication"}},
            platformIntegration={"contractVersion": "1.0", "maestro": "public-execution", "xcom": "native-cpp-fifo",
                "argus": "original-public-evidence", "platformRevision": PLATFORM_REVISION,
                "ownerLifetime": "native-backend", "lostOwnerRecovery": "explicit-host-released-retirement"},
            limitations=["Linux simulation only; native FIFO does not model network timing, reliability or physical coupling.",
                "Three native routes sampled with coalescing counters; original evidence may be incomplete.",
                "External publication, application consumption, vehicle effects and source simulator time remain distinct."])
        value["limits"].update(maxStartupSeconds=900, maxCleanupSeconds=60, maxNativeMessageBytes=128,
            maxNativeBatchBytes=32768, maxNativeQueueMessages=128, maxNativeNormalPulls=250,
            nativeSampledRoutes=3, maxEvidenceEvents=4096)
        value["inputSurface"] = self.run_metadata({"inputSurface": "native-pygame"})["inputSurface"]
        return value
