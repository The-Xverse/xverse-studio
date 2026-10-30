"""Causality/clock guards over the enrolled classic Autoverse fault contract.

Controlled timestamp/bridge-value inputs are unit negatives, never live effects.
The complete native demo independently supplies positive effect evidence.
"""

from copy import deepcopy
import json
import os
from pathlib import Path

import pytest
from ruamel.yaml import YAML
from xverse_studio.blueprints.autoverse import resources
from xverse_studio.providers.autoverse.adapter import AutoverseProvider
from xverse_studio.providers.autoverse.input_loss import InputLoss
from xverse_studio.providers.registry import admit_descriptor
from xverse_studio.xdl import XDLAdapter
from xverse_studio.xdl.examples import dump_yaml
from autoverse_input_loss_sources import fault


@pytest.fixture(scope="module")
def actual_contract():
    receipt = os.environ.get("STUDIO_AUTOVERSE_TEST_INSTALLATION")
    if not receipt:
        pytest.fail("Actual enrolled classic Autoverse receipt required")
    provider = AutoverseProvider(json.loads(Path(receipt).read_bytes())["classic"])
    assert admit_descriptor(provider.descriptor())["providerId"] == "autoverse.demo"
    r = resources("studio-browser")
    r["scenario.xdl.yaml"]["spec"]["faults"] = [fault(r["scenario.xdl.yaml"])]
    source = {k: dump_yaml(v) for k, v in r.items()}
    adapter = XDLAdapter()
    compiled = adapter.compile(source)
    assert compiled["valid"]
    config = provider.configuration(source, compiled)
    assert config is not None
    return provider, source, config["inputLoss"]


def controller(actual_contract):
    events = []

    def emitted(kind, payload, clock, target):
        events.append(
            {
                "kind": kind,
                "payload": deepcopy(payload),
                "clock": clock,
                "target": target,
            }
        )

    return InputLoss(actual_contract[2], 0, emitted), events


@pytest.mark.parametrize("case", ["no-suppression", "stale-report", "unknown-report"])
def test_actual_contract_never_observes_activation_without_suppression_and_new_bridge_evidence(
    actual_contract, case
):
    c, events = controller(actual_contract)
    c.advance(5_000_000_000)
    if case != "no-suppression":
        assert c.suppress(10, 5_100_000_000, 5_100_000_000)
    produced = (
        None if case == "unknown-report" else 4.9 if case == "stale-report" else 5.2
    )
    c.observe(False, produced, 5_300_000_000)
    c.close(5_400_000_000)
    assert [v["kind"] for v in events] == [
        "fault.activation_requested",
        "fault.interrupted",
    ]
    assert (
        events[-1]["payload"]["activationObserved"] is False
        and events[-1]["payload"]["recoveryObserved"] is False
    )


def test_actual_contract_never_observes_recovery_from_old_ack_or_report(
    actual_contract,
):
    c, events = controller(actual_contract)
    c.acknowledge(5)
    c.advance(5_000_000_000)
    assert c.suppress(10, 5_100_000_000, 5_100_000_000)
    c.advance(8_000_000_000)
    c.acknowledge(9)
    c.observe(True, 8.1, 8_200_000_000)
    c.acknowledge(11)
    c.observe(True, 7.9, 8_300_000_000)
    c.close(8_400_000_000)
    assert not any(v["kind"] == "fault.recovery_observed" for v in events)
    assert (
        events[-1]["kind"] == "fault.interrupted"
        and events[-1]["payload"]["recoveryObserved"] is False
    )


def test_actual_contract_does_not_replay_pre_recovery_frames(actual_contract):
    c, _ = controller(actual_contract)
    c.advance(5_000_000_000)
    assert c.suppress(10, 5_100_000_000, 5_100_000_000)
    c.advance(8_000_000_000)
    assert c.suppress(11, 7_900_000_000, 8_100_000_000)
    assert not c.suppress(12, 8_100_000_000, 8_100_000_000)


def test_actual_contract_stalled_window_is_missed_not_executed(actual_contract):
    c, events = controller(actual_contract)
    c.advance(10_000_000_000)
    c.close(11_000_000_000)
    assert [v["kind"] for v in events] == ["fault.schedule_missed"]
    assert not c.suppress(1, 11_000_000_000, 11_000_000_000)


@pytest.mark.parametrize(
    "unit,multiple", [("s", 1), ("ms", 1000), ("us", 1000000), ("ns", 1000000000)]
)
def test_actual_contract_preserves_public_plan_and_original_typed_time_units(
    actual_contract, unit, multiple
):
    provider, source, _ = actual_contract
    source = deepcopy(source)
    scenario = YAML(typ="safe").load(source["scenario.xdl.yaml"])
    scenario["spec"]["faults"] = [
        fault(scenario, at=5 * multiple, duration=3 * multiple, unit=unit)
    ]
    source["scenario.xdl.yaml"] = dump_yaml(scenario)
    compiled = XDLAdapter().compile(source)
    assert compiled["valid"]
    config = provider.configuration(source, compiled)
    assert config is not None
    schedule = config["inputLoss"]["schedules"][0]
    assert schedule["trigger"] == {"kind": "time", "at": 5 * multiple, "unit": unit}
    assert schedule["duration"] == {"value": 3 * multiple, "unit": unit}
    assert (
        schedule["activationTick"] == "5000000"
        and schedule["recoveryTick"] == "8000000"
    )
    assert (
        schedule["planActivationTick"]
        == str(compiled["plan"]["faultSchedule"][0]["trigger"]["atTicks"])
        == "5000000000"
    )
