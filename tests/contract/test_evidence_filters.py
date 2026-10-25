"""Read projection contract: original clocks/bytes remain authoritative."""

from copy import deepcopy
from datetime import datetime, timezone
from decimal import Decimal
import importlib.util
from pathlib import Path

import pytest
from pydantic import ValidationError

from xverse_studio.evidence.query import (
    HistoryQuery,
    ObservationQuery,
    parse_tick,
    project_evidence,
    receipt_time,
)
from xverse_studio.storage.core import Problem

_FIXTURE = (
    Path(__file__).resolve().parents[1]
    / "fixtures/evidence/create_recorded_evidence.py"
)
_spec = importlib.util.spec_from_file_location(
    "trusted_evidence_filter_fixture", _FIXTURE
)
_fixture = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_fixture)


@pytest.fixture
def recorded():
    return _fixture.fixture_records(noise=205)


def project(
    records,
    query,
    kind="observations",
    integrity="valid",
    run_id="recorded-reader-fixture",
):
    return project_evidence(records, integrity, query, run_id=run_id, kind=kind)


@pytest.mark.parametrize(
    "value,expected",
    [
        ("0", 0),
        ("-2", -2),
        ("9007199254740993", 9007199254740993),
        ("-9007199254740993", -9007199254740993),
    ],
)
def test_source_ticks_are_exact_decimal_integers(value, expected):
    assert parse_tick(value) == expected


@pytest.mark.parametrize(
    "value", [None, False, 0, 1.5, "", "+1", "01", "1.0", "1e3", " 1", "9" * 33]
)
def test_invalid_source_ticks_do_not_turn_into_zero(value):
    with pytest.raises(Problem, match="Source ticks"):
        parse_tick(value)


def test_half_open_large_source_interval_never_uses_float(recorded):
    records, ids = recorded
    result = project(
        records,
        ObservationQuery(
            clockDomain="clock-alpha",
            startTick="9007199254740993",
            endTick="9007199254740994",
        ),
    )
    assert [row["eventId"] for row in result["items"]] == [ids["hugeInside"]]
    assert result["items"][0]["tick"] == "9007199254740993"
    assert result["quality"]["otherClock"] >= 1
    assert result["quality"]["missingSourceTime"] >= 1
    assert result["quality"]["malformedSourceTime"] >= 1
    assert result["mapping"] is None


def test_signed_window_distinguishes_zero_from_missing(recorded):
    records, ids = recorded
    result = project(
        records,
        ObservationQuery(
            clockDomain="clock-alpha", startTick="-2", endTick="1", field="value"
        ),
    )
    assert [row["eventId"] for row in result["items"]] == [ids["negative"], ids["zero"]]
    assert result["items"][1]["values"] == {"value": 0}
    default = project(records, ObservationQuery())
    by_id = {row["eventId"]: row for row in default["items"]}
    assert by_id[ids["missingTime"]]["tick"] is None
    assert by_id[ids["malformedTime"]]["tick"] is None
    assert by_id[ids["missingTime"]]["values"] == {"value": 7}
    assert default["presentation"][ids["missingTime"]]["sourceTimeStatus"] == "missing"
    assert (
        default["presentation"][ids["malformedTime"]]["sourceTimeStatus"] == "malformed"
    )
    assert default["clockDomain"] is None


def test_field_selection_omits_absent_fields_but_preserves_false(recorded):
    records, ids = recorded
    result = project(records, ObservationQuery(field="flag"))
    assert {row["eventId"] for row in result["items"]} == {
        ids[name] for name in ("hugeBefore", "hugeInside", "zero")
    }
    assert all(row["values"] == {"flag": False} for row in result["items"])


def test_filters_apply_before_paging(recorded):
    records, ids = recorded
    result = project(records, ObservationQuery(field="selected", limit=1))
    assert result["items"][0]["eventId"] == ids["late"]
    assert result["items"][0]["values"] == {"selected": False}
    assert result["counts"]["matchedRecords"] == 1
    history = project(
        records, HistoryQuery(type="log.appended", severity="error", limit=1), "history"
    )
    assert [row["eventId"] for row in history["items"]] == [ids["lateLog"]]


def test_provider_observer_element_and_clock_are_independent_filters(recorded):
    records, ids = recorded
    result = project(
        records,
        ObservationQuery(
            sourceProviderId="fixture.beta",
            observerRef="external-observer",
            elementRef="xdl://org.example/system/reader-fixture#plant",
            clockDomain="clock-beta",
        ),
    )
    assert [row["eventId"] for row in result["items"]] == [ids["otherClock"]]
    assert result["items"][0]["source"]["providerId"] == "fixture.beta"
    assert result["clockDomain"] == "clock-beta" and result["mapping"] is None


def test_receipt_codec_uses_known_seconds_and_rfc3339_only(recorded):
    records, ids = recorded
    lookup = {row["eventId"]: row for row in records}
    seconds, utc, encoding = receipt_time(lookup[ids["hugeBefore"]])
    assert seconds == Decimal("1767225600.25")
    assert datetime.fromisoformat(utc.replace("Z", "+00:00")) == datetime(
        2026, 1, 1, microsecond=250000, tzinfo=timezone.utc
    )
    assert encoding == "unix_seconds_reference_v1"
    seconds, utc, encoding = receipt_time(lookup[ids["hugeInside"]])
    assert seconds == Decimal("1767225601") and encoding == "rfc3339"
    assert utc.endswith("Z")
    assert receipt_time(lookup[ids["unknownReceipt"]]) == (None, None, "unavailable")
    assert receipt_time(lookup[ids["missingReceipt"]]) == (None, None, "unavailable")
    assert receipt_time({**lookup[ids["hugeBefore"]], "recordedAt": False}) == (
        None,
        None,
        "unavailable",
    )


def test_receipt_window_is_half_open_without_unknown_codec_guess(recorded):
    records, ids = recorded
    result = project(
        records,
        HistoryQuery(
            recordedFrom="2026-01-01T00:00:00.250000Z",
            recordedUntil="2026-01-01T00:00:01Z",
        ),
        "history",
    )
    assert [row["eventId"] for row in result["items"]] == [ids["hugeBefore"]]
    assert result["items"][0]["recordedAt"] == 1767225600.25
    assert result["quality"]["unsupportedReceiptEncoding"] >= 1
    assert result["quality"]["missingReceiptTime"] >= 1


@pytest.mark.parametrize(
    "values",
    [
        {"startTick": "2", "endTick": "2"},
        {"startTick": "3", "endTick": "2"},
        {"startTick": "0", "recordedFrom": "2026-01-01T00:00:00Z"},
        {"recordedFrom": "2026-01-01T00:00:00"},
        {
            "recordedFrom": "2026-01-01T00:00:02Z",
            "recordedUntil": "2026-01-01T00:00:01Z",
        },
        {"limit": 0},
        {"limit": 201},
        {"sourceKind": "invented"},
    ],
)
def test_malformed_or_mixed_query_shapes_reject(values):
    with pytest.raises((ValidationError, Problem)):
        ObservationQuery.model_validate(values)


def test_explicit_clock_required_for_history_or_multiple_valid_observation_clocks(
    recorded,
):
    records, _ = recorded
    for model, kind in ((HistoryQuery, "history"), (ObservationQuery, "observations")):
        with pytest.raises(Problem) as caught:
            project(records, model(startTick="0", endTick="1"), kind)
        assert caught.value.code == "CLOCK_SELECTION_REQUIRED"


def test_legacy_observation_clock_inference_uses_valid_source_clocks_only(recorded):
    records, ids = recorded
    lookup = {row["eventId"]: deepcopy(row) for row in records}
    known = lookup[ids["zero"]]
    malformed = lookup[ids["malformedTime"]]
    malformed["sourceTime"]["clockDomain"] = "malformed-other-clock"
    result = project([known, malformed], ObservationQuery(startTick="0", endTick="1"))
    assert [row["eventId"] for row in result["items"]] == [known["eventId"]]
    assert result["effectiveFilter"]["clockDomain"] == "clock-alpha"
    assert result["quality"]["malformedSourceTime"] == 1


def test_cursor_is_bound_to_run_route_and_canonical_filters(recorded):
    records, _ = recorded
    first = project(
        records, HistoryQuery(type="observation.available", limit=1), "history"
    )
    cursor = first["nextCursor"]
    assert isinstance(cursor, str) and not cursor.isdecimal()
    next_page = project(
        records,
        HistoryQuery(type="observation.available", limit=1, cursor=cursor),
        "history",
    )
    assert next_page["items"][0]["eventId"] != first["items"][0]["eventId"]
    for query, kind, rid in [
        (
            HistoryQuery(type="log.appended", cursor=cursor),
            "history",
            "recorded-reader-fixture",
        ),
        (
            HistoryQuery(type="observation.available", cursor=cursor),
            "history",
            "other-run",
        ),
        (ObservationQuery(cursor=cursor), "observations", "recorded-reader-fixture"),
    ]:
        with pytest.raises(Problem) as caught:
            project(records, query, kind, run_id=rid)
        assert caught.value.code == "CURSOR_INVALID"
    assert project(
        records, HistoryQuery(type="log.appended", cursor="1", limit=1), "history"
    )["items"]
    with pytest.raises(Problem):
        project(
            records,
            HistoryQuery(sourceProviderId="fixture.alpha", cursor="1"),
            "history",
        )


def test_gap_integrity_and_source_records_survive_filtered_projection(recorded):
    records, ids = recorded
    before = deepcopy(records)
    result = project(
        records, ObservationQuery(field="selected", limit=1), integrity="invalid"
    )
    assert result["integrity"] == "invalid"
    assert any(gap.get("eventId") == ids["gap"] for gap in result["gaps"])
    assert any(gap.get("integrity") == "invalid" for gap in result["gaps"])
    assert result["mapping"] is None and result["reduction"]["canonical"] is False
    assert records == before


def test_gap_and_facet_reports_remain_bounded(recorded):
    records, ids = recorded
    gap = next(row for row in records if row["eventId"] == ids["gap"])
    gaps = [{**deepcopy(gap), "eventId": f"gap-{index}"} for index in range(130)]
    result = project(gaps, ObservationQuery(), integrity="invalid")
    assert result["gapCount"] == 130 and result["gapsComplete"] is False
    assert len(result["gaps"]) <= 128
    observations = [
        {
            **deepcopy(records[0]),
            "eventId": f"source-{index}",
            "source": {"providerId": f"fixture-{index}"},
        }
        for index in range(70)
    ]
    facets = project(observations, ObservationQuery())
    assert (
        len(facets["facets"]["sourceProviderIds"]) == 64
        and facets["facetsComplete"] is False
    )
