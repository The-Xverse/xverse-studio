"""Actual Scenario fault fragments for both API and native Autoverse checks."""

ACTIVATION = "urn:xverse:studio:autoverse:input-loss:1.0:activation"
RECOVERY = "urn:xverse:studio:autoverse:input-loss:1.0:recovery"
PROFILE = "io.xverse.experiment"


def fault(scenario, identifier="input-loss", at=5, duration=3, unit="s"):
    target = {**scenario["spec"]["systemRef"], "element": "driver"}
    owner = {
        "apiVersion": scenario["apiVersion"],
        "kind": "Scenario",
        **{k: scenario["metadata"][k] for k in ["namespace", "name"]},
        "element": identifier,
    }
    return {
        "id": identifier,
        "targetRef": target,
        "faultKind": "driver-input-loss",
        "activation": ACTIVATION,
        "recovery": RECOVERY,
        "maturity": "prototype",
        "extensions": {
            PROFILE: {
                "schemaVersion": "0.1",
                "kind": "fault-intent",
                "target": owner,
                "trigger": {"kind": "time", "at": at, "unit": unit},
                "duration": {"value": duration, "unit": unit},
                "timeDomainId": "host-runtime",
            }
        },
    }
