from copy import deepcopy

from xverse_studio.experiments import validate_provider_scenario, scenario_timeline


def scenario():
    return {"kind": "Scenario", "spec": {"steps": [{"id": "start", "actionKind": "start", "targetRef": {"element": "plant"}, "timeDomainId": "simulation-time", "schedule": {"at": 0, "unit": "s"}, "action": {"operation": "reference-response"}}], "faults": [], "observers": [{"id": "state", "timeDomainId": "simulation-time"}]}}


CAPABILITIES = {"actions": {"start": {"operations": ["reference-response"], "targets": ["plant"], "clockDomains": ["simulation-time"], "scheduleUnits": ["s"]}}, "faults": {}, "maxSteps": 64, "maxObservers": 32, "maxDurationSeconds": 30}


def test_provider_checks_do_not_execute_schedules():
    result = validate_provider_scenario(scenario(), CAPABILITIES)
    assert result["ready"] is True
    assert scenario_timeline(scenario())[0]["state"] == "requested"


def test_unsupported_action_target_clock_and_fault_stay_blocked():
    for field, val in [("actionKind", "flash"), ("targetRef", {"element": "unknown"}), ("timeDomainId", "wall")]:
        source = scenario(); source["spec"]["steps"][0][field] = val
        assert validate_provider_scenario(source, CAPABILITIES)["ready"] is False
    source = scenario(); source["spec"]["faults"] = [{"id": "f", "faultKind": "physical-fault", "targetRef": {"element": "plant"}, "activation": "opaque", "recovery": "opaque"}]
    assert validate_provider_scenario(source, CAPABILITIES)["ready"] is False


def test_same_target_same_time_conflicts_are_explicit():
    source = scenario(); duplicate = deepcopy(source["spec"]["steps"][0]); duplicate["id"] = "other"; source["spec"]["steps"].append(duplicate)
    assert "SCHEDULE_CONFLICT" in [d["code"] for d in validate_provider_scenario(source, CAPABILITIES)["diagnostics"]]


def test_unbounded_or_invalid_schedule_is_rejected():
    source = scenario(); source["spec"]["steps"][0]["schedule"]["at"] = float('inf')
    assert validate_provider_scenario(source, CAPABILITIES)["ready"] is False
