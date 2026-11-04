"""T089 campaign contracts anchored to an actual complete Autoverse recording.

Planner/state checks operate on decoded copies and a separate SQLite store. They
prove coordination semantics, not provider admission, native crash recovery,
reservations or applied seeds. HTTP checks prove refusal of an actual unsupported
provider before effects. No reference workload or original recording is modified.
"""

from contextlib import closing
from copy import deepcopy
import hashlib
import json
import os
from pathlib import Path
import sqlite3

import pytest
from pydantic import ValidationError

from autoverse_provider_admission import application, authenticated
from xverse_studio.api.models import Campaign
from xverse_studio.campaigns import CampaignError, CampaignPlanner, CampaignState
from xverse_studio.providers.autoverse.adapter import AutoverseProvider
from xverse_studio.storage.core import Store, digest


@pytest.fixture(scope="module")
def recording():
    source = Path(os.environ["STUDIO_AUTOVERSE_ASSESSMENT_RECORDING"])
    result = json.loads((source / "native-result.json").read_bytes())
    assert result["outcome"] == "passed" and result["fullAndroidAndSpeedObserved"]
    root = Path(
        json.loads((source / "data-root.private.json").read_bytes())["dataRoot"]
    )
    snapshot_path = root / "snapshots" / result["snapshotId"] / "snapshot.json"
    files = [
        snapshot_path,
        root / "runs" / result["runId"] / "evidence.jsonl",
        root / "studio.sqlite",
    ]

    def hashes():
        return {str(p): hashlib.sha256(p.read_bytes()).hexdigest() for p in files}

    before = hashes()
    snapshot = json.loads(snapshot_path.read_bytes())
    assert snapshot["providerId"] == "autoverse.demo"
    assert snapshot["snapshotDigest"] == digest(
        {k: v for k, v in snapshot.items() if k != "snapshotDigest"}
    )
    assert (
        snapshot["configuration"]["randomness"]
        == "external_uncontrolled_no_applied_seed"
    )
    with closing(
        sqlite3.connect((root / "studio.sqlite").as_uri() + "?mode=ro", uri=True)
    ) as db:
        preflights = [
            json.loads(row[0])
            for row in db.execute("SELECT body FROM records WHERE kind='preflight'")
        ]
    preflight = next(p for p in preflights if p["snapshotId"] == snapshot["snapshotId"])
    assert (
        preflight["status"] == "ready"
        and preflight["planDigest"] == snapshot["planDigest"]
    )
    yield snapshot, snapshot_path.read_bytes(), preflight
    assert hashes() == before


def preview(recording, **overrides):
    # These names describe inert matrix axes. Explicit seeds are not applied by
    # the actual provider and this pure planner must not suggest otherwise.
    args = {
        "matrix": {"durationSeconds": [30, 35], "seed": [11, 12]},
        "budget": {"maxRuns": 4, "maxTotalSeconds": 140},
        "duration_seconds": 35,
    }
    args.update(overrides)
    return CampaignPlanner(
        max_children=32, allowed_parameters={"durationSeconds", "seed"}
    ).preview(deepcopy(recording[0]), **args)


def test_cartesian_matrix_is_stable_bounded_and_preserves_actual_base(recording):
    original = deepcopy(recording[0])
    planned = preview(recording)
    assert planned["cardinality"] == 4 and planned["estimatedTotalSeconds"] == 140
    assert [c["parameters"] for c in planned["children"]] == [
        {"durationSeconds": 30, "seed": 11},
        {"durationSeconds": 30, "seed": 12},
        {"durationSeconds": 35, "seed": 11},
        {"durationSeconds": 35, "seed": 12},
    ]
    assert len({c["childKey"] for c in planned["children"]}) == 4
    assert (
        preview(recording, matrix={"seed": [11, 12], "durationSeconds": [30, 35]})
        == planned
    )
    assert all(
        c["state"] == "pending" and c["runId"] is None for c in planned["children"]
    )
    planned["baseSnapshot"]["configuration"]["durationSeconds"] = 999
    assert recording[0] == original
    assert (
        original["configuration"]["randomness"]
        == "external_uncontrolled_no_applied_seed"
    )


@pytest.mark.parametrize(
    "override,code",
    [
        ({"matrix": {}}, "INVALID_MATRIX"),
        ({"matrix": {"unknown": [1]}}, "INVALID_MATRIX"),
        ({"matrix": {"seed": []}}, "MATRIX_LIMIT"),
        ({"matrix": {"seed": list(range(17))}}, "MATRIX_LIMIT"),
        ({"matrix": {"seed": [1, 1.0]}}, "DUPLICATE_MATRIX_VALUE"),
        ({"matrix": {"seed": [True]}}, "INVALID_PARAMETER"),
        ({"matrix": {"seed": ["11"]}}, "INVALID_PARAMETER"),
        ({"matrix": {"seed": [float("nan")]}}, "INVALID_PARAMETER"),
        ({"matrix": {"seed": [float("inf")]}}, "INVALID_PARAMETER"),
        ({"matrix": {"seed": [10**400]}}, "INVALID_PARAMETER"),
        ({"budget": {"maxRuns": 3}}, "CAMPAIGN_BUDGET"),
        ({"budget": {"maxRuns": True}}, "CAMPAIGN_BUDGET"),
        ({"budget": {"maxRuns": 33}}, "CAMPAIGN_BUDGET"),
        ({"budget": {"maxRuns": 4, "maxTotalSeconds": 139}}, "CAMPAIGN_BUDGET"),
        ({"budget": {"maxRuns": 4, "maxTotalSeconds": 10**400}}, "CAMPAIGN_BUDGET"),
        ({"budget": {"maxRuns": 4, "unadmitted": 1}}, "INVALID_BUDGET"),
        ({"duration_seconds": 0}, "INVALID_DURATION"),
        ({"duration_seconds": True}, "INVALID_DURATION"),
        ({"duration_seconds": 10**400}, "INVALID_DURATION"),
        ({"concurrency": True}, "CAMPAIGN_CONCURRENCY"),
        ({"concurrency": 2}, "CAMPAIGN_CONCURRENCY"),
        ({"stop_policy": "retry-forever"}, "INVALID_STOP_POLICY"),
        ({"stop_policy": []}, "INVALID_STOP_POLICY"),
    ],
)
def test_unbounded_or_untyped_campaign_inputs_have_declared_errors(
    recording, override, code
):
    with pytest.raises(CampaignError, match=code):
        preview(recording, **override)


@pytest.mark.parametrize("concurrency", [True, 1.0, "1"])
def test_http_campaign_schema_never_coerces_concurrency(recording, concurrency):
    with pytest.raises(ValidationError):
        Campaign.model_validate(
            {
                "snapshotId": recording[0]["snapshotId"],
                "matrix": {"seed": [11]},
                "budget": {"maxRuns": 1},
                "concurrency": concurrency,
            }
        )


def test_claim_is_durable_and_unknown_recovery_does_not_allocate_a_run(
    recording, tmp_path
):
    store = Store(tmp_path / "coordination only Ω")

    def persist(row):
        store.put("campaign", row["campaignId"], row)

    state = CampaignState.create(
        "contract-campaign", preview(recording), persist=persist
    )
    first = state.claim_next()
    saved = store.get("campaign", "contract-campaign")
    assert saved["children"][0] == first
    assert first["operationKey"] == f"contract-campaign:{first['childKey']}"
    # Reopening metadata models recovery of a dispatch intent. No native backend
    # is killed and no worker acknowledgement is fabricated as a live result.
    recovered = CampaignState.from_record(
        Store(store.root).get("campaign", "contract-campaign"), persist=persist
    )
    recovered.recover()
    assert recovered.record["children"][0]["state"] == "unknown"
    assert recovered.claim_next() is None
    assert store.all("run") == store.all("snapshot") == []
    assert recovered.record["children"][0]["operationKey"] == first["operationKey"]
    recovered.mark_started(first["childKey"], "semantic-run-identity")
    revision = recovered.record["revision"]
    recovered.mark_started(first["childKey"], "semantic-run-identity")
    assert recovered.record["revision"] == revision
    with pytest.raises(CampaignError, match="CHILD_RUN_CONFLICT"):
        recovered.mark_started(first["childKey"], "another-identity")
    assert recovered.claim_next() is None
    recovered.mark_terminal(first["childKey"], "stopped")
    second = recovered.claim_next()
    assert second["childKey"] != first["childKey"] and second["index"] == 1
    assert recovered.record["baseSnapshot"] == recording[0]


@pytest.mark.parametrize("phase", ["claim", "acknowledge", "cancel", "terminal"])
def test_persistence_failure_rolls_back_before_any_delegation(recording, phase):
    state = CampaignState.create("rollback-contract", preview(recording))
    if phase != "claim":
        first = state.claim_next()
        if phase != "acknowledge":
            state.mark_started(first["childKey"], "semantic-run-identity")
    before = deepcopy(state.record)

    def fail(_):
        raise OSError("controlled private-store commit failure")

    state._persist = fail
    with pytest.raises(OSError, match="commit failure"):
        if phase == "claim":
            state.claim_next()
        elif phase == "acknowledge":
            state.mark_started(first["childKey"], "semantic-run-identity")
        elif phase == "cancel":
            state.cancel(cancel_active=True)
        else:
            state.mark_terminal(first["childKey"], "failed")
    assert state.record == before


@pytest.mark.parametrize(
    "policy,expected", [("continue", "pending"), ("stop_on_failure", "cancelled")]
)
def test_failure_policy_retains_failed_child_without_success_verdict(
    recording, policy, expected
):
    state = CampaignState.create(
        "failure-policy", preview(recording, stop_policy=policy)
    )
    first = state.claim_next()
    state.mark_started(first["childKey"], "semantic-failed-identity")
    state.mark_terminal(first["childKey"], "failed")
    assert state.record["children"][0]["state"] == "failed"
    assert all(c["state"] == expected for c in state.record["children"][1:])
    assert (
        "verdict" not in state.record and "verdict" not in state.record["children"][0]
    )


@pytest.mark.parametrize("unknown", [False, True])
def test_cancellation_retains_active_or_ambiguous_identity_and_never_reschedules(
    recording, unknown
):
    state = CampaignState.create("cancel-contract", preview(recording))
    first = state.claim_next()
    if unknown:
        state.mark_unknown(first["childKey"])
    else:
        state.mark_started(first["childKey"], "semantic-active-identity")
    response = state.cancel(cancel_active=True)
    assert response["activeRunIds"] == ([] if unknown else ["semantic-active-identity"])
    assert state.record["status"] == "cancelling"
    assert state.record["children"][0]["state"] == ("unknown" if unknown else "running")
    assert all(c["state"] == "cancelled" for c in state.record["children"][1:])
    recovered = CampaignState.from_record(state.record)
    recovered.recover()
    assert recovered.claim_next() is None
    if unknown:
        recovered.mark_started(first["childKey"], "semantic-active-identity")
    recovered.mark_terminal(first["childKey"], "stopped")
    assert recovered.record["status"] == "cancelled"


@pytest.mark.parametrize("route", ["/api/v1/campaigns/preview", "/api/v1/campaigns"])
@pytest.mark.parametrize("matrix", [{"seed": [11, 12]}, {"duration": [30, 35]}])
def test_actual_ready_autoverse_snapshot_cannot_gain_reference_campaign_authority(
    recording, tmp_path, monkeypatch, route, matrix
):
    receipt = json.loads(
        Path(os.environ["STUDIO_AUTOVERSE_TEST_INSTALLATION"]).read_bytes()
    )
    provider = AutoverseProvider(receipt["classic"])
    app = application(tmp_path / "actual provider refusal Ω", provider)
    store = app.state.studio.store
    snapshot, raw, preflight = deepcopy(recording)
    store.put("snapshot", snapshot["snapshotId"], snapshot)
    store.put("preflight", preflight["preflightId"], preflight)
    directory = store.root / "snapshots" / snapshot["snapshotId"]
    directory.mkdir(parents=True)
    (directory / "snapshot.json").write_bytes(raw)

    def forbidden(*args, **kwargs):
        pytest.fail("Unsupported campaign reached mutable provider/worker admission")

    monkeypatch.setattr(provider, "readiness", forbidden)
    monkeypatch.setattr(app.state.studio.runs, "_dispatch", forbidden)
    with authenticated(app) as api:
        with store.tx() as db:
            before = db.execute("SELECT count(*) FROM idempotency").fetchone()[0]
        for _ in range(2):
            response = api.post(
                route,
                headers={"Idempotency-Key": "unsupported-autoverse-campaign"},
                json={
                    "snapshotId": snapshot["snapshotId"],
                    "matrix": matrix,
                    "budget": {"maxRuns": 2, "maxTotalSeconds": 70},
                    "concurrency": 1,
                },
            )
            assert (
                response.status_code == 422
                and response.json()["code"] == "ADMISSION_REJECTED"
            )
        assert store.all("campaign") == store.all("run") == store.all("operation") == []
        assert store.all("snapshot") == [snapshot] and store.all("preflight") == [
            preflight
        ]
        with store.tx() as db:
            assert (
                db.execute("SELECT count(*) FROM idempotency").fetchone()[0] == before
            )
        assert (directory / "snapshot.json").read_bytes() == raw


def test_exact_child_limit_is_accepted_without_allocating_runs(recording):
    planned = preview(
        recording,
        matrix={"seed": list(range(16)), "durationSeconds": [30, 35]},
        budget={"maxRuns": 32, "maxTotalSeconds": 1120},
    )
    assert planned["cardinality"] == len(planned["children"]) == 32
    assert len({c["childKey"] for c in planned["children"]}) == 32
    assert all(c["runId"] is None for c in planned["children"])


@pytest.mark.parametrize("kind", ["child-limit", "time-limit", "axes-limit"])
def test_excess_budget_is_rejected_before_cartesian_expansion(
    recording, monkeypatch, kind
):
    def forbidden(*args, **kwargs):
        pytest.fail("Over-budget matrix reached Cartesian allocation")

    monkeypatch.setattr("xverse_studio.campaigns.planner.itertools.product", forbidden)
    with pytest.raises(
        CampaignError,
        match="INVALID_MATRIX" if kind == "axes-limit" else "CAMPAIGN_BUDGET",
    ):
        if kind == "axes-limit":
            CampaignPlanner(
                max_axes=1, allowed_parameters={"seed", "durationSeconds"}
            ).preview(
                deepcopy(recording[0]),
                {"seed": [1], "durationSeconds": [30]},
                budget={"maxRuns": 1},
            )
        elif kind == "child-limit":
            preview(
                recording,
                matrix={"seed": list(range(16)), "durationSeconds": [30, 35, 40]},
                budget={"maxRuns": 32, "maxTotalSeconds": 2000},
            )
        else:
            preview(recording, budget={"maxRuns": 4, "maxTotalSeconds": 139})


def test_generic_parallel_slots_are_occupied_by_unknown_and_running_claims(recording):
    from concurrent.futures import ThreadPoolExecutor

    # Abstract coordination capacity only. Actual API/provider capacity stays one
    # or unavailable; no device reservation or execution authority is granted.
    planned = CampaignPlanner(max_concurrency=2, allowed_parameters={"seed"}).preview(
        deepcopy(recording[0]),
        {"seed": [11, 12, 13, 14]},
        budget={"maxRuns": 4},
        concurrency=2,
    )
    state = CampaignState.create("parallel-semantic-contract", planned)
    with ThreadPoolExecutor(max_workers=8) as pool:
        claims = [
            v for v in pool.map(lambda _: state.claim_next(), range(8)) if v is not None
        ]
    assert len(claims) == 2 and len({c["childKey"] for c in claims}) == 2
    state.mark_unknown(claims[0]["childKey"])
    state.mark_started(claims[1]["childKey"], "semantic-slot-identity")
    assert state.claim_next() is None
    state.mark_terminal(claims[1]["childKey"], "failed")
    third = state.claim_next()
    assert third["index"] == 2 and state.claim_next() is None
    assert state.record["children"][0]["state"] == "unknown"


def test_child_identity_changes_with_actual_frozen_base_or_explicit_seed(recording):
    first = preview(recording)
    altered = deepcopy(recording)
    altered[0]["configuration"]["durationSeconds"] = 35
    other = preview(altered)
    assert {c["childKey"] for c in first["children"]}.isdisjoint(
        c["childKey"] for c in other["children"]
    )
    assert (
        len(
            {
                c["childKey"]
                for c in first["children"]
                if c["parameters"]["durationSeconds"] == 30
            }
        )
        == 2
    )
    assert recording[0]["configuration"]["durationSeconds"] == 30
