"""Pure preparation of the actual Autoverse inputs for public Maestro.

This is not a runtime registration. No permit is issued, installation probed or
resource acquired here. The production dispatch/cleanup binding and native
communication adapter must be verified before Studio advertises this runtime.
"""
from dataclasses import dataclass
from pathlib import Path

from xverse.maestro.execution import (
    CanonicalSubmission, EffectiveConfiguration, ExecutionInputError,
    ExperimentSelection, InspectionHost, LifecycleGraph, LifecyclePhase,
    PreparedExecution, SchemaPin, TargetBinding, plan_lifecycle, prepare_execution,
)
from xverse_studio.blueprints.autoverse import REALIZATIONS, ROLES
from xverse_studio.storage.core import canonical, digest
from xverse_studio.xdl import XDLAdapter

from .adapter import AutoverseProvider, PROVIDER_ID


@dataclass(frozen=True)
class AutoversePreparation:
    """Verified inputs and a derived phase graph; no execution authority."""
    host: InspectionHost
    prepared: PreparedExecution
    lifecycle: LifecycleGraph


class AutoverseInputs:
    """Host-installed pure mapping; preserve the actual submitted source bytes."""
    provider_id = PROVIDER_ID

    def __init__(self, installation, *, runtime_adapter=None):
        self.runtime_adapter = runtime_adapter or AutoverseProvider(installation)
        descriptor = self.runtime_adapter.descriptor()
        self.provider_id = descriptor["providerId"]
        self.implementation_digest = descriptor["implementationDigest"]
        self._installation_digest = installation["identityDigest"]

    @property
    def installation_digest(self):
        return self._installation_digest

    def prepare_effective_configuration(self, submission, inspection):
        # The public compiler independently inspects these same immutable bytes.
        # This provider additionally admits every executable field against its
        # finite semantic contract; a compiled model alone is insufficient.
        documents = {name: raw.decode("utf-8") for name, raw in submission.documents}
        compiled = XDLAdapter().compile(documents)
        actual = self.runtime_adapter.configuration(documents, compiled)
        if actual is None:
            raise ExecutionInputError("AUTOVERSE-SOURCE-UNSUPPORTED")
        if (compiled["planDigest"] != submission.expected_plan_digest
                or compiled["semanticDigest"] != submission.expected_input_semantic_digest
                or inspection.to_data()["runId"] != submission.run_id):
            raise ExecutionInputError("AUTOVERSE-EFFECTIVE-INPUT-MISMATCH")
        return EffectiveConfiguration(submission.documents, canonical(actual).encode(), self.installation_digest)

    def lifecycle_phases(self, effective, prepared):
        """Expand the six actual bindings, without adding another System.

        Dependencies preserve the installed demo's startup order. Communication
        feedback edges do not determine lifecycle dependencies. Extra support
        acquisitions belong to an existing binding and feed its readiness.
        """
        units = {u["logicalRef"]["element"]: u for u in prepared.inspection.to_data()["units"]}
        if (set(units) != set(ROLES)
                or any(u["providerId"] != self.provider_id for u in units.values())
                or effective not in tuple(p.configuration for p in prepared.providers)):
            raise ExecutionInputError("AUTOVERSE-BINDINGS-UNSUPPORTED")
        definitions = (
            ("carla-router-prepare", "carla", "prepare", (), 20),
            ("carla-server-prepare", "carla", "prepare", ("carla-router-prepare",), 160),
            ("vcu-prepare", "vcu", "prepare", ("carla-server-prepare",), 10),
            ("vcu-start", "vcu", "start", ("vcu-prepare",), 10),
            ("vcu-ready", "vcu", "ready", ("vcu-start",), 10),
            ("someip-prepare", "someip-bridge", "prepare", ("vcu-ready",), 10),
            ("someip-start", "someip-bridge", "start", ("someip-prepare",), 30),
            ("someip-ready", "someip-bridge", "ready", ("someip-start",), 15),
            ("score-prepare", "score", "prepare", ("someip-ready",), 10),
            ("score-start", "score", "start", ("score-prepare",), 45),
            ("score-ready", "score", "ready", ("score-start",), 15),
            ("carla-vehicle-start", "carla", "start", ("score-ready", "carla-server-prepare"), 15),
            ("driver-observer-prepare", "driver", "prepare", ("carla-vehicle-start",), 15),
            ("carla-ready", "carla", "ready", ("carla-vehicle-start", "driver-observer-prepare"), 125),
            ("android-container-prepare", "android", "prepare", ("carla-ready",), 30),
            ("android-vm-start", "android", "start", ("android-container-prepare",), 40),
            # Boot polling owns transient adb children, so its attempt needs
            # cleanup even if a probe fails. It is an acquiring start phase.
            ("android-boot-start", "android", "start", ("android-vm-start",), 300),
            ("android-apk-start", "android", "start", ("android-boot-start",), 160),
            ("android-ready", "android", "ready", ("android-apk-start",), 15),
            ("driver-start", "driver", "start", ("driver-observer-prepare", "carla-ready", "android-ready"), 40),
            ("driver-ready", "driver", "ready", ("driver-start",), 10),
        )
        if self.provider_id == "autoverse.platform":
            definitions = (*definitions[:2],
                ("vcu-native-prepare", "vcu", "prepare", ("carla-router-prepare",), 20),
                *definitions[2:])
            definitions = tuple((i, r, o, (*n, "vcu-native-prepare") if i == "vcu-start" else n, t)
                                for i, r, o, n, t in definitions)
        return tuple(LifecyclePhase(identifier, units[role]["logicalId"], self.provider_id,
                                    operation, needs, timeout)
                     for identifier, role, operation, needs, timeout in definitions)


def prepare_snapshot(run_id, snapshot, *, installation, host_id, runtime_adapter=None):
    """Called by trusted host code with a frozen Studio snapshot and enrollment.

    Paths, schema pins, provider code and placement capabilities come from the
    installed adapter. The snapshot supplies original XDL and expected compiler
    identities. No browser/project field supplies a runtime permit.
    """
    adapter = XDLAdapter()
    provider = AutoverseInputs(installation, runtime_adapter=runtime_adapter)
    try:
        documents = snapshot["documents"]
        selection = snapshot["plan"]["selection"]
        submission = CanonicalSubmission(run_id, tuple((name, raw.encode("utf-8")) for name, raw in documents.items()),
            snapshot["planDigest"], snapshot["semanticDigest"],
            ExperimentSelection(*(selection[kind]["uri"] for kind in ("system", "deployment", "scenario"))))
    except (KeyError, TypeError, AttributeError, UnicodeError):
        raise ExecutionInputError("AUTOVERSE-SNAPSHOT-INVALID") from None
    host = InspectionHost(host_id, tuple(
        TargetBinding(role + "-target", provider.provider_id, provider.implementation_digest,
                      (REALIZATIONS[role],), ("container" if role in {"someip-bridge", "score", "android"} else "process",))
        for role in ROLES), tuple(SchemaPin(Path(path), digest(Path(path).read_bytes()))
                                 for path in adapter.profile_schema_paths))
    prepared = prepare_execution(submission, host, (provider,))
    graph = plan_lifecycle(prepared, provider.lifecycle_phases(prepared.providers[0].configuration, prepared))
    return AutoversePreparation(host, prepared, graph)
