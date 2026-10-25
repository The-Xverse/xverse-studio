from copy import deepcopy

from xverse_studio.comparison import compare_runs


def run():
    return {"runId": "r", "snapshot": {"snapshotId": "s", "semanticDigest": "model", "planDigest": "plan", "parameters": {"gain": 1}, "providerIdentity": {"id": "owned"}, "clockDomainRef": "sim"}, "evidence": {"integrity": "valid", "status": "complete"}, "observations": [{"field": "state", "unit": "1", "quantity": "dimensionless", "unitDefinitionDigest": "one", "clockDomainRef": "sim", "coverage": {"complete": True, "gaps": []}}]}


def test_configuration_differences_precede_interpretation():
    left, right = run(), run(); right["runId"] = "other"; right["snapshot"]["parameters"]["gain"] = 2
    out = compare_runs(left, right)
    assert out["differences"][0]["field"] == "parameters"
    assert out["compatible"] is True
    assert out["mode"] == "recorded_observation_comparison"
    assert out["rerunRequiresFreshAdmission"] is True


def test_unit_identity_mismatch_and_clock_uncertainty_block_numeric_overlay():
    for key, value in [("unitDefinitionDigest", "other"), ("clockDomainRef", "device"), ("quantity", "distance")]:
        left, right = run(), run(); right["observations"][0][key] = value
        out = compare_runs(left, right)
        assert out["compatible"] is False


def test_missing_gapped_invalid_evidence_cannot_be_compared_as_complete():
    left, right = run(), run(); right["observations"][0]["coverage"]["gaps"] = [[1, 2]]
    assert compare_runs(left, right)["compatible"] is False
    right = run(); right["evidence"]["integrity"] = "invalid"
    assert compare_runs(left, right)["compatible"] is False
