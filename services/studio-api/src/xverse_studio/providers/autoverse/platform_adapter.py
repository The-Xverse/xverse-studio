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
    worker_module = "xverse_studio.providers.autoverse.maestro_worker"
    configuration = staticmethod(platform_configuration)
    shutdown_timeout_seconds = 75

    def verify_installation(self):
        verify_platform(self.installation)

    def descriptor(self):
        value = super().descriptor()
        native = self.installation["nativeBridge"]
        value.update(providerId=PLATFORM_PROVIDER_ID, name="Autoverse with X-Verse platform",
            evidenceScope="platform_simulation", supportedInputSurfaces=["native-pygame"],
            implementationDigest=digest({"python": value["implementationDigest"], "sdkRevision": PLATFORM_REVISION,
                                         "nativeSources": native["nativeSources"]}),
            connectionContracts={"externalRuntime": {"version": "1.0", "kind": "communication",
                "providerId": PLATFORM_PROVIDER_ID, "contractRef": PLATFORM_CONTRACT_REF,
                "feedback": "externally-managed-asynchronous-communication"}},
            platformIntegration={"contractVersion": "1.0", "maestro": "public-execution", "xcom": "native-cpp-fifo",
                "argus": "original-public-evidence", "platformRevision": PLATFORM_REVISION},
            limitations=["Linux simulation only; native FIFO does not model network timing, reliability or physical coupling.",
                "Three native routes sampled with coalescing counters; original evidence may be incomplete.",
                "External publication, application consumption, vehicle effects and source simulator time remain distinct."])
        value["limits"].update(maxStartupSeconds=900, maxCleanupSeconds=60, maxNativeMessageBytes=128,
            maxNativeBatchBytes=32768, maxNativeQueueMessages=128, maxNativeNormalPulls=250,
            nativeSampledRoutes=3, maxEvidenceEvents=4096)
        return value
