from copy import deepcopy

import pytest

from xverse_studio.campaigns import CampaignPlanner, CampaignState, CampaignError


def test_finite_preview_binds_each_child_to_exact_parameters():
    source = {"snapshotId": "base", "semanticDigest": "sha256:base", "parameters": {"gain": 1}}
    preview = CampaignPlanner().preview(source, {"gain": [1, 2], "target": [3, 4]}, budget={"maxRuns": 4, "maxTotalSeconds": 100}, duration_seconds=10)
    assert preview["cardinality"] == 4
    assert len({c["childKey"] for c in preview["children"]}) == 4
    source["parameters"]["gain"] = 900
    assert preview["baseSnapshot"]["parameters"]["gain"] == 1
    assert preview["children"][0]["parameters"] == {"gain": 1, "target": 3}


@pytest.mark.parametrize("matrix,budget,concurrency", [({"gain": []}, {"maxRuns": 2}, 1), ({"gain": list(range(17))}, {"maxRuns": 20}, 1), ({"gain": [1, 2], "target": [1, 2]}, {"maxRuns": 3}, 1), ({"gain": [1]}, {"maxRuns": 2}, 2), ({"gain": [float('nan')]}, {"maxRuns": 2}, 1), ({"__import__": ["bad"]}, {"maxRuns": 2}, 1)])
def test_campaign_bounds_reject_before_dispatch(matrix, budget, concurrency):
    with pytest.raises(CampaignError):
        CampaignPlanner(allowed_parameters={"gain", "target"}).preview({"snapshotId": "base"}, matrix, budget=budget, concurrency=concurrency)


def test_total_time_budget_is_enforced():
    with pytest.raises(CampaignError, match="CAMPAIGN_BUDGET"):
        CampaignPlanner().preview({"snapshotId": "base"}, {"gain": [1, 2]}, budget={"maxRuns": 2, "maxTotalSeconds": 10}, duration_seconds=6)


def test_claim_is_persisted_before_launch_and_crash_never_replays_unknown_start():
    written = []
    p = CampaignPlanner().preview({"snapshotId": "base"}, {"gain": [1, 2]}, budget={"maxRuns": 2})
    state = CampaignState.create("campaign", p, persist=lambda r: written.append(deepcopy(r)))
    child = state.claim_next()
    assert child["state"] == "dispatching"
    assert written[-1]["children"][0]["state"] == "dispatching"
    restored = CampaignState.from_record(written[-1])
    restored.recover()
    assert restored.record["children"][0]["state"] == "unknown"
    assert restored.claim_next() is None
    restored.mark_started(child["childKey"], "run")
    assert restored.claim_next() is None
    restored.mark_terminal(child["childKey"], "stopped")
    assert restored.claim_next()["parameters"] == {"gain": 2}


def test_cancel_only_pending_and_reports_active_separately():
    p = CampaignPlanner().preview({"snapshotId": "base"}, {"gain": [1, 2]}, budget={"maxRuns": 2})
    state = CampaignState.create("campaign", p)
    child = state.claim_next(); state.mark_started(child["childKey"], "run")
    out = state.cancel(cancel_active=True)
    assert out["activeRunIds"] == ["run"]
    assert state.record["children"][0]["state"] == "running"
    assert state.record["children"][1]["state"] == "cancelled"
    assert state.claim_next() is None


def test_terminal_child_cannot_be_reassigned_to_another_run():
    p = CampaignPlanner().preview({"snapshotId": "base"}, {"gain": [1]}, budget={"maxRuns": 1})
    state = CampaignState.create("c", p); child = state.claim_next()
    state.mark_started(child["childKey"], "r1")
    state.mark_started(child["childKey"], "r1")
    with pytest.raises(CampaignError, match="CHILD_RUN_CONFLICT"):
        state.mark_started(child["childKey"], "r2")


def test_cancelled_campaign_stays_cancelled_after_active_child_stops():
    p = CampaignPlanner().preview({'snapshotId':'base'}, {'gain':[1,2]}, budget={'maxRuns':2})
    state = CampaignState.create('c', p)
    child = state.claim_next(); state.mark_started(child['childKey'],'run')
    state.cancel(cancel_active=True)
    state.mark_terminal(child['childKey'],'stopped')
    assert state.record['status'] == 'cancelled'
