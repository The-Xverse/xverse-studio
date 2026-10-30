"""Timeline1.1 on immutable actual Autoverse records, plus controlled negatives."""

from copy import deepcopy
import json, os, sqlite3
from pathlib import Path
import pytest
from xverse_studio.evidence.reader import read_journal
from xverse_studio.providers.autoverse.adapter import AutoverseProvider
from xverse_studio.storage.core import digest
from xverse_studio.timeline import TimelineQuery, project_timeline
from xverse_studio.xdl import XDLAdapter


@pytest.fixture
def actual():
    out = Path(os.environ["STUDIO_AUTOVERSE_FAULT_RECORDING"])
    result = json.loads((out / "native-result.json").read_bytes())
    assert result["outcome"] == "passed"
    data = Path(json.loads((out / "data-root.private.json").read_bytes())["dataRoot"])
    directory = data / "runs" / result["runId"]
    snapfile = data / "snapshots" / result["snapshotId"] / "snapshot.json"
    before = (snapfile.read_bytes(), (directory / "evidence.jsonl").read_bytes())
    with sqlite3.connect(
        (data / "studio.sqlite").as_uri() + "?mode=ro", uri=True
    ) as db:
        run = json.loads(
            db.execute(
                "SELECT body FROM records WHERE kind='run' AND id=?", (result["runId"],)
            ).fetchone()[0]
        )
    state = json.loads((directory / "state.json").read_bytes())
    run.update(
        {k: state[k] for k in ["effectivePlanDigest", "effectiveSemanticDigest"]}
    )
    snapshot = json.loads(snapfile.read_bytes())
    records, integrity = read_journal(directory, state)
    assert integrity == "valid"
    provider = AutoverseProvider(
        json.loads(Path(os.environ["STUDIO_AUTOVERSE_TEST_INSTALLATION"]).read_bytes())[
            "classic"
        ]
    )
    yield run, snapshot, records, provider
    assert before == (
        snapfile.read_bytes(),
        (directory / "evidence.jsonl").read_bytes(),
    )


def project(actual, version="1.1", **kw):
    run, snap, records, provider = actual
    return project_timeline(
        run,
        snap,
        records,
        kw.pop("integrity", "valid"),
        [],
        XDLAdapter(),
        TimelineQuery(formatVersion=version, limit=200, **kw),
        provider_clock=provider.timeline_context,
    )


def test_actual_fault_timeline_places_only_declared_intent_and_matching_recorded_faults(
    actual,
):
    report = project(actual)
    rows = report["items"]
    intent = [r for r in rows if r["kind"] == "intent.fault"]
    faults = [
        r for r in rows if r["layer"] == "recorded" and r["kind"].startswith("fault.")
    ]
    assert (
        report["timelineVersion"] == "1.1"
        and report["tickUnit"] == "microsecond"
        and len(intent) == 3
        and len(faults) == 11
    )
    assert report["clockInterpretation"]["epoch"] == "actual-running-transition"
    assert all(r["position"]["status"] == "aligned" for r in intent + faults)
    assert all(
        r["position"]["status"] == "unplaced"
        for r in rows
        if r["layer"] == "recorded" and not r["kind"].startswith("fault.")
    )
    assert (
        next(r for r in intent if r["intentId"] == "first-loss")["position"]["tick"]
        == "5000000"
    )
    assert (
        next(r for r in intent if r["intentId"] == "first-loss")["position"]["endTick"]
        == "8000000"
    )
    assert all(r["evidenceScope"] == "declared_intent_only" for r in intent)


def test_actual_fault_timeline_legacy_and_version_bound_cursors(actual):
    legacy = project(actual, "1.0", cursor=None)
    assert legacy["intentClockCodec"] is None and "clockInterpretation" not in legacy
    assert all(r["position"]["status"] == "unplaced" for r in legacy["items"])
    run, snap, records, p = actual
    first = project_timeline(
        run,
        snap,
        records,
        "valid",
        [],
        XDLAdapter(),
        TimelineQuery(formatVersion="1.1", limit=1),
        provider_clock=p.timeline_context,
    )
    from xverse_studio.storage.core import Problem

    with pytest.raises(Problem) as e:
        project(actual, "1.0", cursor=first["nextCursor"])
    assert e.value.code == "TIMELINE_CURSOR_STALE"


@pytest.mark.parametrize(
    "case",
    [
        "provider",
        "version",
        "resolution",
        "payload-tick",
        "missing-time",
        "clock",
        "negative",
        "fault",
        "kind",
    ],
)
def test_actual_fault_event_counterexamples_do_not_gain_a_time_axis(actual, case):
    run, snap, records, p = actual
    records = deepcopy(records)
    row = next(r for r in records if r["type"] == "fault.activation_observed")
    if case == "provider":
        row["source"]["providerId"] = "foreign"
    elif case == "version":
        row["source"]["version"] = "unknown"
    elif case == "resolution":
        row["sourceTime"]["resolution"] = "nanosecond"
    elif case == "payload-tick":
        row["payload"]["actualTick"] = "0"
    elif case == "missing-time":
        row["sourceTime"] = None
    elif case == "clock":
        row["sourceTime"]["clockDomain"] = "foreign-clock"
    elif case == "negative":
        row["sourceTime"]["tick"] = row["payload"]["actualTick"] = "-1"
    elif case == "fault":
        row["payload"]["faultId"] = "foreign-fault"
    else:
        row["type"] = "fault.unadmitted"
    report = project((run, snap, records, p))
    assert (
        next(r for r in report["items"] if r.get("eventId") == row["eventId"])[
            "position"
        ]["status"]
        == "unplaced"
    )


@pytest.mark.parametrize(
    "case",
    [
        "effective-plan",
        "effective-semantic",
        "codec",
        "version",
        "configuration",
        "callback",
        "shape",
        "bounds",
    ],
)
def test_actual_fault_context_failures_remain_unknown_without_private_diagnostics(
    actual, case, monkeypatch
):
    run, snap, records, p = actual
    run, snap = deepcopy(run), deepcopy(snap)
    if case == "effective-plan":
        run["effectivePlanDigest"] = "sha256:" + "0" * 64
    elif case == "effective-semantic":
        run["effectiveSemanticDigest"] = "sha256:" + "0" * 64
    elif case == "codec":
        snap["providerIdentity"]["scenarioContracts"]["clockCodec"] = "unknown"
    elif case == "version":
        snap["providerIdentity"]["providerVersion"] = "unadmitted"
    elif case == "configuration":
        snap["configuration"]["inputLoss"]["schedules"][0]["activationTick"] = "1"
    elif case == "callback":

        def broken(*_):
            raise RuntimeError("PRIVATE-CALLBACK-DETAIL")

        monkeypatch.setattr(p, "timeline_context", broken)
    else:
        value = p.timeline_context(run, snap)
        if case == "shape":
            value["contractVersion"] = "unadmitted"
        else:
            value["faults"] *= 33
        monkeypatch.setattr(p, "timeline_context", lambda *_: value)
    snap["snapshotDigest"] = digest(
        {k: v for k, v in snap.items() if k != "snapshotDigest"}
    )
    report = project((run, snap, records, p))
    assert all(r["position"]["status"] == "unplaced" for r in report["items"])
    assert "PRIVATE-CALLBACK-DETAIL" not in json.dumps(report)


def test_actual_fault_integrity_failure_keeps_recorded_positions_unproven(actual):
    report = project(actual, integrity="invalid")
    assert all(
        r["position"]["reason"] == "EVIDENCE_INTEGRITY_UNPROVEN"
        for r in report["items"]
        if r["layer"] == "recorded"
    )
