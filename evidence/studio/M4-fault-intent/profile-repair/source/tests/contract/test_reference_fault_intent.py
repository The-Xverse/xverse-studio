"""Full selected XDL compilation plus owned schedule interpretation, not execution."""
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
    add_fault(result, "hold-one", "1000000", "2000000")
    return result


def add_fault(source, identifier, start, end):
    scenario = source["scenario.xdl.yaml"]
    scenario["spec"].setdefault("faults", []).append({
        "id": identifier, "targetRef": deepcopy(scenario["spec"]["observers"][0]["targetRef"]),
        "faultKind": "measurement-hold", "activation": ACTIVATION, "recovery": RECOVERY, "maturity": "prototype",
    })
    scenario["extensions"].setdefault(NAMESPACE, {"version": "1.0", "schedules": []})["schedules"].append({
        "faultId": identifier, "observerRef": "state-observer", "field": "measured", "clockDomainRef": "simulation-time",
        "activation": {"tick": start, "unit": "us"}, "recovery": {"tick": end, "unit": "us"},
    })


def documents(source):
    return {name: dump_yaml(value) for name, value in source.items()}


def test_explicit_profile_compiles_exact_full_sources_and_stays_inert():
    source = documents(resources())
    before = deepcopy(source)
    compiled = XDLAdapter((SCHEMA_PATH,)).compile(source)
    assert compiled["valid"], compiled["diagnostics"]
    intent = compile_reference_fault_intent(source)
    assert source == before
    assert intent["executionAllowed"] is False
    assert intent["status"] == "compiled_intent"
    assert intent["planDigest"] == compiled["planDigest"]
    assert intent["semanticDigest"] == compiled["semanticDigest"]
    assert intent["durationTick"] == "5000000"
    assert intent["timestepTick"] == "100000"
    assert intent["schedules"][0]["activation"] == {"tick": "1000000", "unit": "us"}
    # Installing a schema or compiling intent never grants current worker support.
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
    assert result.returncode == 0, result.stderr
    assert json.loads(result.stdout)["plan"] == adapter.compile(source)["plan"]


def test_adjacent_intervals_sorted_without_mutating_authored_order():
    source = resources()
    add_fault(source, "hold-next", "2000000", "3000000")
    source["scenario.xdl.yaml"]["extensions"][NAMESPACE]["schedules"].reverse()
    assert [item["faultId"] for item in compile_reference_fault_intent(documents(source))["schedules"]] == ["hold-one", "hold-next"]
    assert source["scenario.xdl.yaml"]["extensions"][NAMESPACE]["schedules"][0]["faultId"] == "hold-next"


@pytest.mark.parametrize("start,end", [("0", "100000"), ("4800000", "4900000")])
def test_first_and_last_observable_boundaries_are_supported(start, end):
    source = resources()
    schedule = source["scenario.xdl.yaml"]["extensions"][NAMESPACE]["schedules"][0]
    schedule["activation"]["tick"], schedule["recovery"]["tick"] = start, end
    intent = compile_reference_fault_intent(documents(source))
    assert (intent["schedules"][0]["activationTick"], intent["schedules"][0]["recoveryTick"]) == (start, end)


@pytest.mark.parametrize("start,end", [
    ("1000001", "2000000"), ("1000000", "2000001"), ("2000000", "1000000"),
    ("1000000", "1000000"), ("1000000", "5000000"), ("1000000", "5100000"),
    ("-1", "1000000"), ("01", "1000000"), ("1e6", "2000000"),
    ("1.0", "2000000"), (True, "2000000"), ("9" * 100, "2000000"),
])
def test_quantization_order_horizon_and_bounded_tick_encoding(start, end):
    source = resources()
    schedule = source["scenario.xdl.yaml"]["extensions"][NAMESPACE]["schedules"][0]
    schedule["activation"]["tick"], schedule["recovery"]["tick"] = start, end
    with pytest.raises(XDLRejected):
        compile_reference_fault_intent(documents(source))


@pytest.mark.parametrize("field,value", [
    ("clockDomainRef", "wall-time"), ("observerRef", "other-observer"), ("field", "value"),
    ("faultId", "not-declared"), ("version", "2.0"), ("command", "never execute"),
])
def test_unknown_binding_clock_version_or_executable_metadata_is_not_interpreted(field, value):
    source = resources()
    payload = source["scenario.xdl.yaml"]["extensions"][NAMESPACE]
    (payload if field == "version" else payload["schedules"][0])[field] = value
    before = documents(source)
    with pytest.raises(XDLRejected):
        compile_reference_fault_intent(before)
    assert before == documents(source)


@pytest.mark.parametrize("phase,unit", [("activation", "s"), ("recovery", "ms"), ("activation", "1")])
def test_units_require_explicit_profile_codec(phase, unit):
    source = resources()
    source["scenario.xdl.yaml"]["extensions"][NAMESPACE]["schedules"][0][phase]["unit"] = unit
    with pytest.raises(XDLRejected):
        compile_reference_fault_intent(documents(source))


@pytest.mark.parametrize("mutation", ["opaque-activation", "opaque-recovery", "kind", "target", "native-extension", "legacy-mix", "missing", "duplicate", "unbound"])
def test_native_fault_binding_and_unknown_semantics_fail_closed(mutation):
    source = resources()
    scenario = source["scenario.xdl.yaml"]
    fault = scenario["spec"]["faults"][0]
    if mutation.startswith("opaque-"):
        fault[mutation.removeprefix("opaque-")] = "at 1s; call anything"
    elif mutation == "kind":
        fault["faultKind"] = "physical-reset"
    elif mutation == "target":
        fault["targetRef"]["element"] = "command-flow"
    elif mutation == "native-extension":
        fault["extensions"] = {"org.unknown": {"keep": [1, "opaque"]}}
    elif mutation == "legacy-mix":
        next(p for p in scenario["extensions"][PROFILE_NAMESPACE]["parameters"] if p["id"] == "fault")["value"] = "stuck-sensor"
    elif mutation == "missing":
        scenario["spec"]["faults"].clear()
    elif mutation == "duplicate":
        scenario["extensions"][NAMESPACE]["schedules"] *= 2
    else:
        add_fault(source, "unbound", "3000000", "4000000")
        scenario["extensions"][NAMESPACE]["schedules"].pop()
    with pytest.raises(XDLRejected):
        compile_reference_fault_intent(documents(source))


def test_overlap_has_no_implicit_priority():
    source = resources()
    add_fault(source, "overlap", "1900000", "3000000")
    with pytest.raises(XDLRejected) as rejected:
        compile_reference_fault_intent(documents(source))
    assert rejected.value.code == "FAULT_SCHEDULE_CONFLICT"


@pytest.mark.parametrize("duration,step", [(5, 0.1000001), (5, 0.3), (31, 0.1), (5, True), (0.01, 0.01)])
def test_time_parameters_require_exact_whole_microseconds_and_model_bounds(duration, step):
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


def test_changed_schedule_changes_authoritative_identity_and_preserves_unknown_payload():
    source = resources()
    before = compile_reference_fault_intent(documents(source))
    source["scenario.xdl.yaml"]["extensions"][NAMESPACE]["schedules"][0]["recovery"]["tick"] = "2100000"
    after = compile_reference_fault_intent(documents(source))
    assert before["planDigest"] != after["planDigest"]
    assert before["semanticDigest"] != after["semanticDigest"]
    source["system.xdl.yaml"]["extensions"] = {"org.unknown": {"nested": ["must retain", 7]}}
    opaque = documents(source)
    with pytest.raises(XDLRejected):
        compile_reference_fault_intent(opaque)
    assert opaque == documents(source)
