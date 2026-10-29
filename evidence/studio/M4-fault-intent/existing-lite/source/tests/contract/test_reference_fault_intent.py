"""Selected public XDL compilation plus owned fault intent; no execution claim."""
from copy import deepcopy
import json
import subprocess
import sys

import pytest

from xverse_studio.experiments.reference_faults import (
    ACTIVATION, RECOVERY, NAMESPACE, PROFILE_SPEC, SCHEMA_PATH,
    compile_reference_fault_intent,
)
from xverse_studio.xdl import XDLAdapter, XDLRejected, reference_configuration
from xverse_studio.xdl.examples import PROFILE_NAMESPACE, dump_yaml, reference_resources


def resources():
    result = reference_resources()
    result["fault-profile.xdl.yaml"] = {
        "apiVersion": "xverse.io/xdl/v1alpha1", "kind": "Profile",
        "metadata": {**deepcopy(result["evaluation-profile.xdl.yaml"]["metadata"]), "name": "reference-faults"},
        "spec": deepcopy(PROFILE_SPEC),
    }
    add_fault(result, "hold-one", 1_000_000, 1_000_000)
    return result


def add_fault(source, identifier, start, duration):
    scenario = source["scenario.xdl.yaml"]
    target = deepcopy(scenario["extensions"][PROFILE_NAMESPACE]["target"])
    target["element"] = identifier
    scenario["spec"].setdefault("faults", []).append({
        "id": identifier, "targetRef": deepcopy(scenario["spec"]["observers"][0]["targetRef"]),
        "faultKind": "measurement-hold", "activation": ACTIVATION, "recovery": RECOVERY, "maturity": "prototype",
        "extensions": {
            NAMESPACE: {"version": "1.0", "observerRef": "state-observer", "field": "measured"},
            PROFILE_NAMESPACE: {"schemaVersion": "0.1", "kind": "fault-intent", "target": target,
                                "trigger": {"kind": "time", "at": start, "unit": "us"},
                                "duration": {"value": duration, "unit": "us"}, "timeDomainId": "simulation-time"},
        },
    })


def documents(source):
    return {name: dump_yaml(value) for name, value in source.items()}


def fault(source):
    return source["scenario.xdl.yaml"]["spec"]["faults"][0]


def intent(source):
    return fault(source)["extensions"][PROFILE_NAMESPACE]


def test_explicit_profile_compiles_exact_full_sources_and_stays_inert():
    source = documents(resources())
    before = deepcopy(source)
    compiled = XDLAdapter((SCHEMA_PATH,)).compile(source)
    assert compiled["valid"], compiled["diagnostics"]
    report = compile_reference_fault_intent(source)
    assert source == before
    assert report["executionAllowed"] is False
    assert report["status"] == "compiled_intent"
    assert report["planDigest"] == compiled["planDigest"]
    assert report["semanticDigest"] == compiled["semanticDigest"]
    assert (report["durationTick"], report["timestepTick"]) == ("5000000", "100000")
    schedule = report["schedules"][0]
    assert schedule["trigger"] == {"kind": "time", "at": 1_000_000, "unit": "us"}
    assert schedule["duration"] == {"value": 1_000_000, "unit": "us"}
    assert schedule["activationTick"] == "1000000"
    assert schedule["recoveryTick"] == "2000000"
    assert schedule["planActivationTick"] == str(compiled["plan"]["faults"][0]["trigger"]["atTicks"]) == "1000000000"
    assert schedule["sourceTickUnit"] == "us" and schedule["planTickUnit"] == "ns"
    # Compiling intent grants no current worker support.
    with pytest.raises(XDLRejected):
        reference_configuration(source)


def test_profile_cli_and_library_compile_identical_authoritative_plans(tmp_path):
    source = documents(resources())
    paths = []
    for name, value in source.items():
        path = tmp_path / name
        path.write_text(value, encoding="utf-8")
        paths.append(str(path))
    adapter = XDLAdapter((SCHEMA_PATH,))
    schema_args = [arg for path in adapter.profile_schema_paths for arg in ("--profile-schema", path)]
    result = subprocess.run([sys.executable, "-I", "-m", "xverse_xdl", "experiment", "compile", "--format", "json",
                             *schema_args, *paths], capture_output=True, text=True, timeout=20)
    assert result.returncode == 0, result.stdout + result.stderr
    assert json.loads(result.stdout)["plan"] == adapter.compile(source)["plan"]


def test_adjacent_intervals_sort_without_mutating_authored_order():
    source = resources()
    add_fault(source, "hold-next", 2_000_000, 1_000_000)
    source["scenario.xdl.yaml"]["spec"]["faults"].reverse()
    assert [item["faultId"] for item in compile_reference_fault_intent(documents(source))["schedules"]] == ["hold-one", "hold-next"]
    assert fault(source)["id"] == "hold-next"


@pytest.mark.parametrize("start,duration", [(0, 100_000), (4_800_000, 100_000)])
def test_first_and_last_observable_boundaries_are_supported(start, duration):
    source = resources()
    intent(source)["trigger"]["at"], intent(source)["duration"]["value"] = start, duration
    schedule = compile_reference_fault_intent(documents(source))["schedules"][0]
    assert (schedule["activationTick"], schedule["recoveryTick"]) == (str(start), str(start + duration))


@pytest.mark.parametrize("start,duration", [
    (1_000_001, 1_000_000), (1_000_000, 1_000_001), (2_000_000, -1_000_000),
    (1_000_000, 0), (1_000_000, 4_000_000), (1_000_000, 4_100_000),
    (-1, 1_000_000), ("1e6", 1_000_000), (True, 1_000_000), (10**100, 1_000_000),
])
def test_quantization_nonempty_order_horizon_and_quantity_bounds(start, duration):
    source = resources()
    intent(source)["trigger"]["at"], intent(source)["duration"]["value"] = start, duration
    with pytest.raises(XDLRejected):
        compile_reference_fault_intent(documents(source))


@pytest.mark.parametrize("field,value", [
    ("observerRef", "other-observer"), ("field", "value"), ("version", "2.0"), ("command", "never execute"),
])
def test_unknown_binding_version_or_executable_metadata_is_preserved_and_rejected(field, value):
    source = resources()
    fault(source)["extensions"][NAMESPACE][field] = value
    before = documents(source)
    with pytest.raises(XDLRejected):
        compile_reference_fault_intent(before)
    assert before == documents(source)


@pytest.mark.parametrize("unit,start,duration", [("s", 1, 1), ("ms", 1000, 1000), ("us", 1_000_000, 1_000_000), ("ns", 10**9, 10**9)])
def test_existing_lite_units_preserved_with_exact_platform_ticks(unit, start, duration):
    source = resources()
    intent(source)["trigger"].update(at=start, unit=unit)
    intent(source)["duration"].update(value=duration, unit=unit)
    schedule = compile_reference_fault_intent(documents(source))["schedules"][0]
    assert schedule["trigger"]["unit"] == unit and schedule["duration"]["unit"] == unit
    assert (schedule["activationTick"], schedule["recoveryTick"]) == ("1000000", "2000000")


@pytest.mark.parametrize("mutation", [
    "opaque-activation", "opaque-recovery", "kind", "target", "native-extension", "legacy-mix", "missing",
    "duplicate", "unbound", "misplaced", "clock", "declared-order", "unit", "submicrosecond", "extra-intent",
])
def test_native_binding_and_unknown_semantics_fail_closed(mutation):
    source = resources()
    selected = fault(source)
    if mutation.startswith("opaque-"):
        selected[mutation.removeprefix("opaque-")] = "at 1s; call anything"
    elif mutation == "kind":
        selected["faultKind"] = "physical-reset"
    elif mutation == "target":
        selected["targetRef"]["element"] = "command-flow"
    elif mutation == "native-extension":
        selected["extensions"]["org.unknown"] = {"keep": [1, "opaque"]}
    elif mutation == "legacy-mix":
        next(p for p in source["scenario.xdl.yaml"]["extensions"][PROFILE_NAMESPACE]["parameters"] if p["id"] == "fault")["value"] = "stuck-sensor"
    elif mutation == "missing":
        source["scenario.xdl.yaml"]["spec"]["faults"].clear()
    elif mutation == "duplicate":
        source["scenario.xdl.yaml"]["spec"]["faults"] *= 2
    elif mutation == "unbound":
        selected["extensions"].pop(NAMESPACE)
    elif mutation == "misplaced":
        source["scenario.xdl.yaml"]["extensions"][NAMESPACE] = selected["extensions"].pop(NAMESPACE)
    elif mutation == "clock":
        intent(source)["timeDomainId"] = "wall-time"
    elif mutation == "declared-order":
        intent(source)["trigger"] = {"kind": "declared-order", "order": 0}
        intent(source).pop("timeDomainId")
    elif mutation == "unit":
        intent(source)["duration"]["unit"] = "minutes"
    elif mutation == "submicrosecond":
        intent(source)["trigger"].update(at=1_000_000_001, unit="ns")
    else:
        intent(source)["parameters"] = []
    with pytest.raises(XDLRejected):
        compile_reference_fault_intent(documents(source))


def test_overlap_has_no_implicit_priority():
    source = resources()
    add_fault(source, "overlap", 1_900_000, 1_000_000)
    with pytest.raises(XDLRejected) as rejected:
        compile_reference_fault_intent(documents(source))
    assert rejected.value.code == "FAULT_SCHEDULE_CONFLICT"


@pytest.mark.parametrize("duration,step", [(5, 0.1000001), (5, 0.3), (31, 0.1), (5, True), (0.01, 0.01)])
def test_model_times_need_exact_whole_microseconds_and_bounds(duration, step):
    source = resources()
    for parameter in source["scenario.xdl.yaml"]["extensions"][PROFILE_NAMESPACE]["parameters"]:
        if parameter["id"] in ("duration", "timestep"):
            parameter["value"] = duration if parameter["id"] == "duration" else step
    with pytest.raises(XDLRejected):
        compile_reference_fault_intent(documents(source))


@pytest.mark.parametrize("version,schema", [("2.0.0", PROFILE_SPEC["schemaRef"]), ("1.0.0", "urn:unknown-schema")])
def test_profile_identity_is_exact(version, schema):
    source = resources()
    source["fault-profile.xdl.yaml"]["metadata"]["version"] = version
    source["fault-profile.xdl.yaml"]["spec"]["schemaRef"] = schema
    with pytest.raises(XDLRejected):
        compile_reference_fault_intent(documents(source))


def test_changed_timing_changes_authoritative_identity_and_unknown_payload_stays_intact():
    source = resources()
    before = compile_reference_fault_intent(documents(source))
    intent(source)["duration"]["value"] = 1_100_000
    after = compile_reference_fault_intent(documents(source))
    assert before["planDigest"] != after["planDigest"]
    assert before["semanticDigest"] != after["semanticDigest"]
    source["system.xdl.yaml"]["extensions"] = {"org.unknown": {"nested": ["must retain", 7]}}
    opaque = documents(source)
    with pytest.raises(XDLRejected):
        compile_reference_fault_intent(opaque)
    assert opaque == documents(source)
