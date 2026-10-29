"""Owned evaluator fixtures; these do not establish device or simulator evidence."""
from copy import deepcopy

import pytest

from xverse_studio.assertions import evaluate, aggregate_verdict, validate_definition

UNITS = {"1": {"quantity": "dimensionless", "definitionDigest": "sha256:one"}, "m": {"quantity": "length", "definitionDigest": "sha256:metre"}, "cm": {"quantity": "length", "definitionDigest": "sha256:centimetre"}, "s": {"quantity": "time", "definitionDigest": "sha256:second"}}

def definition(expression=None, **extra):
    return {"evaluationId": "limit", "version": "1.0", "kind": "assertion", "name": "Bound", "systemRef": "system", "scenarioRef": "scenario", "window": {"clockDomainRef": "sim", "startTick": "0", "endTick": "3"}, "coveragePolicy": "complete", "expression": expression or {"kind": "compare", "operator": "le", "left": {"kind": "aggregate", "operator": "max", "input": {"kind": "signal", "observerRef": "observer", "field": "value"}}, "right": {"kind": "literal", "value": 5, "unit": "m"}}, **extra}

def evidence(**extra):
    return [{"evidenceId": "owned-evidence", "digest": "sha256:owned", "snapshotId": "snapshot", "observerRef": "observer", "field": "value", "schema": {"type": "number", "unit": "m", "quantity": "length", "unitDefinitionDigest": "sha256:metre"}, "clockDomainRef": "sim", "integrity": "valid", "coverage": {"verified": True, "complete": True, "startTick": "0", "endTick": "3", "gaps": []}, "samples": [{"tick": "0", "value": 1}, {"tick": "1", "value": 2}, {"tick": "2", "value": 3}, {"tick": "3", "value": 999}], **extra}]

def run(d=None, e=None, **kwargs):
    return evaluate(d or definition(), evidence() if e is None else e, units=UNITS, profile_admitted=True, snapshot_id="snapshot", **kwargs)

def test_pass_fail_and_half_open_window():
    assert run()["verdict"] == "pass"
    d = definition(); d["expression"]["right"]["value"] = 2
    assert run(d)["verdict"] == "fail"

def test_profile_admission_is_required_and_opaque_strings_never_run():
    assert evaluate(definition(), evidence(), units=UNITS)["status"] == "unavailable"
    assert run(definition("__import__('os').system('false')"))["status"] == "error"

@pytest.mark.parametrize("patch,code", [({"integrity": "invalid"}, "EVIDENCE_INVALID"), ({"coverage": None}, "COVERAGE_UNPROVEN"), ({"samples": []}, "EMPTY_SERIES"), ({"coverage": {"verified": True, "complete": False, "gaps": [["1", "2"]], "startTick": "0", "endTick": "3"}}, "COVERAGE_INCOMPLETE")])
def test_bad_evidence_is_indeterminate(patch, code):
    r = run(e=evidence(**patch))
    assert (r["status"], r["verdict"]) == ("complete", "indeterminate")
    assert code in r["reasons"]

def test_missing_signal_or_field_never_proves_zero_count():
    d = definition({"kind": "compare", "operator": "eq", "left": {"kind": "aggregate", "operator": "count", "input": {"kind": "signal", "observerRef": "absent", "field": "value"}}, "right": {"kind": "literal", "value": 0, "unit": "1"}, "tolerance": {"value": 0, "unit": "1"}})
    assert run(d)["verdict"] == "indeterminate"

@pytest.mark.parametrize("samples", [[{"tick": "1", "value": 2}, {"tick": "0", "value": 1}], [{"tick": "0", "value": 1}, {"tick": "0", "value": 2}], [{"tick": "0", "value": float('nan')}], [{"tick": "0", "value": float('inf')}]])
def test_bad_samples_indeterminate(samples):
    assert run(e=evidence(samples=samples))["verdict"] == "indeterminate"

def test_unit_text_alone_is_not_admission():
    e = evidence(); e[0]["schema"]["unitDefinitionDigest"] = "sha256:other"
    assert run(e=e)["verdict"] == "indeterminate"
    d = definition(); d["expression"]["right"]["unit"] = "s"
    assert run(d)["status"] == "error"

def test_explicit_conversion_and_tolerance():
    d = definition({"kind": "compare", "operator": "eq", "left": {"kind": "convert", "conversionRef": "cm-to-m@1", "input": {"kind": "literal", "value": 100, "unit": "cm"}}, "right": {"kind": "literal", "value": 1, "unit": "m"}, "tolerance": {"value": 0.001, "unit": "m"}})
    assert run(d, conversions={"cm-to-m@1": {"fromUnit": "cm", "toUnit": "m", "scale": .01, "offset": 0, "definitionDigest": "sha256:conversion"}})["verdict"] == "pass"
    assert run(d)["status"] == "error"
    del d["expression"]["tolerance"]
    assert run(d)["status"] == "error"

def test_two_series_require_exact_ticks():
    d = definition({"kind": "aggregate", "operator": "all", "input": {"kind": "compare", "operator": "le", "left": {"kind": "signal", "observerRef": "observer", "field": "value"}, "right": {"kind": "signal", "observerRef": "other", "field": "value"}}})
    e = evidence(); other = deepcopy(e[0]); other["observerRef"] = "other"; other["samples"] = [{"tick": "0", "value": 3}, {"tick": "2", "value": 3}]; e.append(other)
    assert run(d, e)["verdict"] == "indeterminate"

def test_clock_mapping_uncertainty_and_missing_clock():
    e = evidence(clockDomainRef="device")
    assert run(e=e)["verdict"] == "indeterminate"
    e[0]["clockMapping"] = {"admitted": True, "mappingId": "map", "digest": "sha256:map", "targetClockDomainRef": "sim", "offsetTick": "0", "numerator": 1, "denominator": 1, "uncertaintyTicks": "2"}
    d = definition(maxUncertaintyTicks="1")
    assert run(d, e)["verdict"] == "indeterminate"
    d["maxUncertaintyTicks"] = "2"
    assert run(d, e)["verdict"] == "pass"

def test_metric_results_do_not_have_assertion_verdict():
    d = definition({"kind": "aggregate", "operator": "mean", "input": {"kind": "signal", "observerRef": "observer", "field": "value"}}, kind="metric", resultUnit="m")
    r = run(d)
    assert (r["status"], r["verdict"], r["value"], r["unit"]) == ("complete", None, 2, "m")

def test_metric_dependencies_require_version_snapshot_and_same_evidence():
    ref = {"evaluationId": "metric", "version": "1.0", "definitionDigest": "sha256:def"}
    d = definition({"kind": "compare", "operator": "le", "left": {"kind": "metric", "evaluationRef": ref}, "right": {"kind": "literal", "value": 3, "unit": "m"}})
    metric = {**ref, "status": "complete", "kind": "metric", "value": 2, "unit": "m", "coverage": "complete", "partial": False, "snapshotId": "snapshot", "evidenceDigests": ["sha256:owned"]}
    assert run(d, metrics={"metric": metric})["verdict"] == "pass"
    metric["snapshotId"] = "different"
    assert run(d, metrics={"metric": metric})["verdict"] == "indeterminate"

@pytest.mark.parametrize("mutate", [lambda d: d.update(unknown="x"), lambda d: d["window"].update(endTick="0"), lambda d: d["expression"].update(operator="exec"), lambda d: d["expression"].update(tolerance={"value": 1, "unit": "m"})])
def test_invalid_definitions_are_execution_errors(mutate):
    d = definition(); mutate(d)
    assert run(d)["status"] == "error"

def test_limits_depth_node_sample_bytes_budget_and_cancel():
    node = {"kind": "literal", "value": True}
    for _ in range(13): node = {"kind": "boolean", "operator": "not", "inputs": [node]}
    assert run(definition(node))["status"] == "error"
    assert run(cancel=lambda: True)["reasons"] == ["CANCELLED"]
    assert run(budget_seconds=0)["reasons"] == ["WALL_TIME_BUDGET"]
    assert run(limits={"maxSamples": 2})["status"] == "error"
    assert run(limits={"maxBytes": 10})["status"] == "error"

def test_root_type_is_enforced_and_boolean_operators_are_eager():
    assert run(definition({"kind": "literal", "value": 1, "unit": "1"}))["status"] == "error"
    d = definition({"kind": "boolean", "operator": "and", "inputs": [{"kind": "literal", "value": False}, {"kind": "aggregate", "operator": "all", "input": {"kind": "signal", "observerRef": "missing", "field": "enabled"}}]})
    assert run(d)["verdict"] == "indeterminate"

def test_aggregate_does_not_pass_empty_or_unavailable_assertions():
    assert aggregate_verdict([]) is None
    assert aggregate_verdict([{"status": "complete", "verdict": "pass"}]) == "pass"
    assert aggregate_verdict([{"status": "unavailable", "verdict": None}]) == "indeterminate"
    assert aggregate_verdict([{"status": "complete", "verdict": "fail"}, {"status": "unavailable"}]) == "fail"


def test_unicode_definition_digest_uses_the_same_canonical_bytes():
    from xverse_studio.assertions import definition_digest
    d = definition(); d['name'] = 'Limite de pressão'
    assert run(d)['definitionDigest'] == definition_digest(d)


def test_large_clock_ticks_keep_exact_rational_coverage_boundaries():
    big = 10**25
    d = definition(); d['window'].update(startTick=str(big), endTick=str(big+3)); d['maxUncertaintyTicks'] = '0'
    e = evidence(clockDomainRef='device')
    e[0]['coverage'].update(startTick='0', endTick='3')
    e[0]['samples'] = [{'tick':'0','value':1}, {'tick':'1','value':2}, {'tick':'2','value':3}]
    e[0]['clockMapping'] = {'admitted':True,'mappingId':'exact','digest':'sha256:exact','targetClockDomainRef':'sim','offsetTick':str(big),'numerator':1,'denominator':1,'uncertaintyTicks':'0'}
    assert run(d,e)['verdict'] == 'pass'
    e[0]['coverage']['startTick'] = '1'
    assert run(d,e)['verdict'] == 'indeterminate'


def test_hard_ast_reference_and_nested_boundaries():
    from xverse_studio.assertions import EvaluationError
    node = {'kind':'literal','value':True}
    for _ in range(11): node = {'kind':'boolean','operator':'not','inputs':[node]}
    assert validate_definition(definition(node))['nodes'] == 12
    node = {'kind':'boolean','operator':'not','inputs':[node]}
    with pytest.raises(EvaluationError, match='AST_LIMIT'):
        validate_definition(definition(node))
    many = {'kind':'boolean','operator':'and','inputs':[{'kind':'signal','observerRef':str(i),'field':'value'} for i in range(33)]}
    with pytest.raises(EvaluationError, match='REFERENCE_LIMIT'):
        validate_definition(definition(many))
    many['inputs'] = [{'kind':'literal','value':True} for _ in range(128)]
    with pytest.raises(EvaluationError, match='AST_LIMIT'):
        validate_definition(definition(many))
