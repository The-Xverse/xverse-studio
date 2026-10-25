from copy import deepcopy


def compare_runs(left: dict, right: dict) -> dict:
    """Compare recorded provenance first; no interpolation, new run, or verdict."""
    if not isinstance(left, dict) or not isinstance(right, dict):
        raise ValueError("INVALID_COMPARISON")
    result = {"leftRunId": left.get("runId"), "rightRunId": right.get("runId"), "mode": "recorded_observation_comparison", "rerunRequiresFreshAdmission": True, "differences": [], "compatible": True, "diagnostics": [], "fields": []}
    def block(code):
        result["compatible"] = False
        if code not in result["diagnostics"]: result["diagnostics"].append(code)
    a, b = left.get("snapshot", {}), right.get("snapshot", {})
    for key in ("semanticDigest", "planDigest", "parameters", "artifactIdentities", "profileIdentities", "providerIdentity", "capabilityDigest", "clockDomainRef"):
        if a.get(key) != b.get(key):
            result["differences"].append({"field": key, "left": deepcopy(a.get(key)), "right": deepcopy(b.get(key))})
    for run in (left, right):
        evidence = run.get("evidence", {})
        if evidence.get("integrity") != "valid": block("EVIDENCE_INTEGRITY_UNPROVEN")
        if evidence.get("status") != "complete": block("EVIDENCE_INCOMPLETE")
    obs_a, obs_b = left.get("observations", []), right.get("observations", [])
    if not isinstance(obs_a, list) or not isinstance(obs_b, list) or len(obs_a) > 32 or len(obs_b) > 32:
        raise ValueError("COMPARISON_LIMIT")
    key = lambda item: (item.get("observerRef"), item.get("field"))
    by_a = {key(o): o for o in obs_a}; by_b = {key(o): o for o in obs_b}
    if len(by_a) != len(obs_a) or len(by_b) != len(obs_b): block("AMBIGUOUS_OBSERVER")
    if not by_a or by_a.keys() != by_b.keys(): block("OBSERVATIONS_UNAVAILABLE")
    for field in by_a.keys() & by_b.keys():
        x, y = by_a[field], by_b[field]
        reasons = []
        if any(x.get(k) != y.get(k) or x.get(k) is None for k in ("unit", "quantity", "unitDefinitionDigest")):
            reasons.append("QUANTITY_INCOMPATIBLE")
        if x.get("clockDomainRef") != y.get("clockDomainRef") or x.get("clockDomainRef") is None:
            reasons.append("CLOCK_INCOMPATIBLE")
        for value in (x, y):
            coverage = value.get("coverage", {})
            if coverage.get("complete") is not True or coverage.get("gaps") != []:
                reasons.append("OBSERVATION_COVERAGE_INCOMPLETE")
        for reason in reasons: block(reason)
        result["fields"].append({"observerRef": field[0], "field": field[1], "compatible": not reasons, "reasons": list(dict.fromkeys(reasons))})
    return result
