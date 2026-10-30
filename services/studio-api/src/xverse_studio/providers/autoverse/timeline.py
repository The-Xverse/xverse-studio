"""Read-only admission of the existing classic0.2.0 host fault clock."""

from xverse_studio.deployments import compile_selection
from xverse_studio.xdl import XDLAdapter
from .input_loss import CLOCK, CODEC, CONTRACT


def context(provider, run, snapshot):
    frozen = snapshot.get("providerIdentity", {})
    declared = frozen.get("scenarioContracts", {})
    if (
        run.get("providerId") != "autoverse.demo"
        or snapshot.get("providerId") != run.get("providerId")
        or frozen.get("providerId") != run.get("providerId")
        or frozen.get("providerVersion") != "0.2.0"
        or run.get("evidenceScope") != "external_demo"
        or declared.get("contractVersion") != "1.0"
        or declared.get("contractRef") != CONTRACT
        or declared.get("clockCodec") != CODEC
    ):
        return None
    compiled = compile_selection(
        snapshot["documents"], snapshot["selection"], XDLAdapter()
    )
    if (
        not compiled["valid"]
        or compiled["planDigest"] != snapshot.get("planDigest")
        or compiled["semanticDigest"] != snapshot.get("semanticDigest")
        or run.get("effectivePlanDigest") != compiled["planDigest"]
        or run.get("effectiveSemanticDigest") != compiled["semanticDigest"]
    ):
        return None
    configuration = provider.configuration(snapshot["documents"], compiled)
    if not configuration or configuration != snapshot.get("configuration"):
        return None
    loss = configuration.get("inputLoss")
    if (
        not loss
        or loss.get("contractRef") != CONTRACT
        or loss.get("clockCodec") != CODEC
        or loss.get("clockDomain") != CLOCK
        or loss.get("tickUnit") != "microsecond"
    ):
        return None
    return {
        "contractVersion": "1.0",
        "codec": CODEC,
        "clockDomain": CLOCK,
        "tickUnit": "microsecond",
        "epoch": "actual-running-transition",
        "evidenceScope": "external_demo",
        "sourceProviderId": run["providerId"],
        "sourceVersion": "0.2.0",
        "eventTickField": "actualTick",
        "eventKinds": [
            "fault.activation_requested",
            "fault.activation_observed",
            "fault.recovery_requested",
            "fault.recovery_observed",
            "fault.interrupted",
            "fault.not_activated",
        ],
        "faults": [
            {k: s[k] for k in ["faultId", "activationTick", "recoveryTick"]}
            for s in loss["schedules"]
        ],
    }
