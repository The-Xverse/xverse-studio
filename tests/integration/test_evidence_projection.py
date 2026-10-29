"""Actual API projections over NEW inert fixtures; canonical bytes are never edited."""

from contextlib import contextmanager
import hashlib
import importlib.util
from pathlib import Path

import pytest

from xverse_studio.evidence.reader import read_journal

_PATH = (
    Path(__file__).resolve().parents[1]
    / "fixtures/evidence/create_recorded_evidence.py"
)
_spec = importlib.util.spec_from_file_location("trusted_evidence_api_fixture", _PATH)
_fixture = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_fixture)


@pytest.fixture
def recorded(client):
    project = client.post(
        "/api/v1/projects", json={"name": "Isolated recorded evidence query"}
    ).json()
    studio = client.app.state.studio
    return _fixture.create_recorded_evidence(
        studio.store, studio.projects, studio.runs, project["projectId"]
    )


def endpoint(recorded, kind):
    return f"/api/v1/runs/{recorded['runId']}/{kind}"


def test_api_exact_source_windows_and_missing_time_are_truthful(client, recorded):
    response = client.get(
        endpoint(recorded, "observations"),
        params={
            "clockDomain": "clock-alpha",
            "startTick": recorded["ticks"]["start"],
            "endTick": recorded["ticks"]["end"],
        },
    )
    assert response.status_code == 200, response.text
    result = response.json()
    assert result["projectionVersion"] == "1.0"
    assert [row["eventId"] for row in result["items"]] == [
        recorded["events"]["hugeInside"]
    ]
    assert result["items"][0]["tick"] == "9007199254740993"
    assert result["mapping"] is None and result["evidenceScope"] == "recorded_fixture"
    assert result["quality"]["otherClock"] >= 1
    default = client.get(endpoint(recorded, "observations")).json()
    rows = {row["eventId"]: row for row in default["items"]}
    assert rows[recorded["events"]["hugeBefore"]]["recordedAt"] == 1767225600.25
    assert rows[recorded["events"]["missingTime"]]["tick"] is None
    assert rows[recorded["events"]["malformedTime"]]["tick"] is None
    assert rows[recorded["events"]["zero"]]["values"]["value"] == 0
    assert rows[recorded["events"]["zero"]]["values"]["flag"] is False
    assert default["clockDomain"] is None
    assert (
        client.get(
            endpoint(recorded, "observations"),
            params={"startTick": "0", "endTick": "1"},
        ).status_code
        == 422
    )


def test_api_provider_observer_element_field_and_prefiltered_pages(client, recorded):
    snapshot = client.app.state.studio.store.get("snapshot", recorded["snapshotId"])
    element = snapshot["selection"]["systemRef"] + "#plant"
    selected = client.get(
        endpoint(recorded, "observations"),
        params={
            "sourceProviderId": "fixture.beta",
            "observerRef": "external-observer",
            "clockDomain": "clock-beta",
            "elementRef": element,
            "field": "value",
            "limit": 1,
        },
    )
    assert selected.status_code == 200, selected.text
    assert [row["eventId"] for row in selected.json()["items"]] == [
        recorded["events"]["otherClock"]
    ]
    late = client.get(
        endpoint(recorded, "observations"), params={"field": "selected", "limit": 1}
    )
    assert late.status_code == 200, late.text
    assert late.json()["items"][0]["eventId"] == recorded["events"]["late"]
    assert late.json()["items"][0]["values"] == {"selected": False}
    logs = client.get(
        endpoint(recorded, "history"),
        params={
            "type": "log.appended",
            "severity": "error",
            "sourceProviderId": "fixture.late",
            "limit": 1,
        },
    )
    assert logs.status_code == 200, logs.text
    assert [row["eventId"] for row in logs.json()["items"]] == [
        recorded["events"]["lateLog"]
    ]
    assert logs.json()["counts"]["matchedRecords"] == 1


def test_api_receipt_projection_keeps_raw_known_seconds_and_unknown_codec(
    client, recorded
):
    response = client.get(
        endpoint(recorded, "history"),
        params={
            "recordedFrom": "2026-01-01T00:00:00.250000Z",
            "recordedUntil": "2026-01-01T00:00:01Z",
        },
    )
    assert response.status_code == 200, response.text
    body = response.json()
    identifier = recorded["events"]["hugeBefore"]
    assert [row["eventId"] for row in body["items"]] == [identifier]
    assert body["items"][0]["recordedAt"] == 1767225600.25
    assert (
        body["presentation"][identifier]["receiptEncoding"]
        == "unix_seconds_reference_v1"
    )
    assert (
        body["presentation"][identifier]["recordedAtUtc"]
        == "2026-01-01T00:00:00.250000Z"
    )
    assert body["quality"]["unsupportedReceiptEncoding"] >= 1
    assert body["quality"]["missingReceiptTime"] >= 1


def test_api_cursors_reject_wrong_context_route_unknown_and_duplicate_selectors(
    client, recorded
):
    history = endpoint(recorded, "history")
    first = client.get(
        history, params={"type": "observation.available", "limit": 1}
    ).json()
    cursor = first["nextCursor"]
    next_page = client.get(
        history, params={"type": "observation.available", "limit": 1, "cursor": cursor}
    )
    assert next_page.status_code == 200, next_page.text
    assert next_page.json()["items"][0]["eventId"] != first["items"][0]["eventId"]
    for url, params in [
        (history, {"type": "log.appended", "cursor": cursor}),
        (endpoint(recorded, "observations"), {"cursor": cursor}),
        (history, {"sourceProviderId": "fixture.alpha", "cursor": "1"}),
        (history, {"unknownSelector": "discard"}),
        (endpoint(recorded, "observations"), {"severity": "info"}),
        (history, {"field": "value"}),
        (history, {"recordedFrom": "2026-01-01T00:00:00"}),
        (history, {"startTick": "0", "recordedUntil": "2026-01-01T00:00:01Z"}),
        (history, {"limit": 201}),
    ]:
        rejected = client.get(url, params=params)
        assert rejected.status_code == 422, (url, params, rejected.text)
    duplicate = client.get(history + "?clockDomain=clock-alpha&clockDomain=clock-beta")
    assert duplicate.status_code == 422, duplicate.text


def test_api_projection_preserves_journal_snapshot_and_declared_gap(client, recorded):
    studio = client.app.state.studio
    journal = studio.runs.directory(recorded["runId"]) / "evidence.jsonl"
    snapshot = (
        studio.store.root / "snapshots" / recorded["snapshotId"] / "snapshot.json"
    )
    before = {
        "journal": hashlib.sha256(journal.read_bytes()).hexdigest(),
        "snapshot": hashlib.sha256(snapshot.read_bytes()).hexdigest(),
    }
    filtered = client.get(
        endpoint(recorded, "observations"), params={"field": "selected", "limit": 1}
    ).json()
    assert filtered["integrity"] == "valid"
    assert any(
        gap.get("eventId") == recorded["events"]["gap"] for gap in filtered["gaps"]
    )
    assert filtered["gapCount"] == 1 and filtered["gapsComplete"] is True
    assert filtered["reduction"]["canonical"] is False and filtered["mapping"] is None
    client.get(
        endpoint(recorded, "history"),
        params={"type": "log.appended", "severity": "error"},
    ).raise_for_status()
    assert before == {
        "journal": hashlib.sha256(journal.read_bytes()).hexdigest(),
        "snapshot": hashlib.sha256(snapshot.read_bytes()).hexdigest(),
    }
    assert (
        client.get("/api/v1/runs/" + recorded["runId"]).json()["evidence"] == "partial"
    )
    catalog = client.get(endpoint(recorded, "evidence")).json()
    assert catalog["items"][0]["evidenceScope"] == recorded["evidenceScope"]


def test_reader_missing_and_changed_acquisition_are_unavailable(tmp_path, monkeypatch):
    from xverse_studio.evidence import reader

    state = {
        "runId": "recorded-reader-fixture",
        "snapshotId": "fixture-snapshot",
        "state": "stopped",
    }
    assert read_journal(tmp_path / "missing", state) == ([], "unavailable")
    records, _ = _fixture.fixture_records(noise=0)
    root = tmp_path / "new-changed-fixture"
    state["journalDigest"] = _fixture.write_journal(root, records)
    actual = reader.open_read

    @contextmanager
    def changed(directory, path):
        with actual(directory, path) as stream:
            yield stream
            with path.open("ab") as altered:
                altered.write(b"\n")

    monkeypatch.setattr(reader, "open_read", changed)
    assert read_journal(root, state) == ([], "unavailable")


def test_reader_reacquires_running_journal_after_bounded_concurrent_appends(
    tmp_path, monkeypatch
):
    from xverse_studio.evidence import reader

    records, _ = _fixture.fixture_records(noise=0)
    root = tmp_path / "new-running-append-fixture"
    _fixture.write_journal(root, records)
    state = {
        "runId": "recorded-reader-fixture",
        "snapshotId": "fixture-snapshot",
        "state": "running",
    }
    actual = reader.open_read
    attempts = []

    @contextmanager
    def appending(directory, path, *, transient):
        attempts.append(path)
        with actual(directory, path) as stream:
            yield stream
            if transient is None or len(attempts) <= transient:
                with path.open("ab") as appended:
                    appended.write(b"{")

    monkeypatch.setattr(
        reader, "open_read", lambda d, p: appending(d, p, transient=2)
    )
    rows, integrity = read_journal(root, state)
    assert integrity == "verified_prefix" and len(attempts) == 3
    assert [row["eventId"] for row in rows] == [row["eventId"] for row in records]

    # A source that changes on every acquisition stays unavailable after the bound.
    attempts.clear()
    monkeypatch.setattr(
        reader, "open_read", lambda d, p: appending(d, p, transient=None)
    )
    assert read_journal(root, state) == ([], "unavailable")
    assert len(attempts) == reader.MAX_ACQUIRE_ATTEMPTS


def test_reader_oversized_file_refuses_before_read(tmp_path, monkeypatch):
    from xverse_studio.evidence import reader

    root = tmp_path / "new-oversized-fixture"
    root.mkdir()
    (root / "evidence.jsonl").write_bytes(b"x" * 129)
    actual = reader.open_read

    @contextmanager
    def guarded(directory, path):
        with actual(directory, path) as stream:

            class NoRead:
                def fileno(self):
                    return stream.fileno()

                def read(self, *args):
                    raise AssertionError(
                        "Oversized source must refuse before allocation"
                    )

            yield NoRead()

    monkeypatch.setattr(reader, "MAX_JOURNAL_BYTES", 128)
    monkeypatch.setattr(reader, "open_read", guarded)
    assert read_journal(root, {"state": "stopped"}) == ([], "invalid")


def test_reader_hash_corruption_is_not_upgraded_by_projection(tmp_path):
    from xverse_studio.evidence.query import ObservationQuery, project_evidence

    records, _ = _fixture.fixture_records(noise=0)
    pristine = tmp_path / "new-pristine-fixture"
    source_digest = _fixture.write_journal(pristine, records)
    corrupted = tmp_path / "new-corrupt-fixture"
    corrupted.mkdir()
    (corrupted / "evidence.jsonl").write_bytes(
        (pristine / "evidence.jsonl").read_bytes() + b"corrupted-tail\n"
    )
    state = {
        "runId": "recorded-reader-fixture",
        "snapshotId": "fixture-snapshot",
        "state": "stopped",
        "journalDigest": source_digest,
    }
    rows, integrity = read_journal(corrupted, state)
    assert integrity == "invalid"
    projection = project_evidence(
        rows,
        integrity,
        ObservationQuery(field="value"),
        run_id=state["runId"],
        kind="observations",
    )
    assert projection["integrity"] == "invalid" and projection["gaps"]
    assert projection["mapping"] is None


@pytest.mark.parametrize("declared", [[], {}, True, False, "", "sha256:bad"])
def test_reader_malformed_declared_digest_is_invalid_not_exception(tmp_path, declared):
    records, _ = _fixture.fixture_records(noise=0)
    root = tmp_path / "new-declared-digest-fixture"
    _fixture.write_journal(root, records)
    before = (root / "evidence.jsonl").read_bytes()
    state = {
        "runId": "recorded-reader-fixture",
        "snapshotId": "fixture-snapshot",
        "state": "stopped",
        "journalDigest": declared,
    }
    _, integrity = read_journal(root, state)
    assert integrity == "invalid"
    assert (root / "evidence.jsonl").read_bytes() == before


@pytest.mark.parametrize("declared", [[], {}, True, False, "", "sha256:bad"])
def test_api_malformed_digest_metadata_does_not_change_original_journal(
    client, recorded, declared
):
    studio = client.app.state.studio
    path = studio.runs.directory(recorded["runId"]) / "evidence.jsonl"
    before = hashlib.sha256(path.read_bytes()).hexdigest()
    record = studio.store.get("run", recorded["runId"])
    record["journalDigest"] = declared
    studio.store.put("run", recorded["runId"], record)
    for kind in ("history", "observations", "evidence"):
        response = client.get(endpoint(recorded, kind))
        assert response.status_code == 200, response.text
        assert response.json()["integrity"] == "invalid"
    assert studio.store.get("run", recorded["runId"])["journalDigest"] == declared
    assert hashlib.sha256(path.read_bytes()).hexdigest() == before


def test_reader_duplicate_event_identity_cannot_overwrite_receipt_presentation(
    tmp_path,
):
    from copy import deepcopy
    from xverse_studio.evidence.query import (
        HistoryQuery,
        project_evidence,
        receipt_time,
    )

    base, _ = _fixture.fixture_records(noise=0)
    rows = [deepcopy(base[0]), deepcopy(base[1])]
    rows[1]["eventId"] = rows[0]["eventId"]
    root = tmp_path / "new-duplicate-event-fixture"
    declared = _fixture.write_journal(root, rows)
    original = (root / "evidence.jsonl").read_bytes()
    read, integrity = read_journal(
        root,
        {
            "runId": "recorded-reader-fixture",
            "snapshotId": "fixture-snapshot",
            "state": "stopped",
            "journalDigest": declared,
        },
    )
    assert integrity == "invalid"
    projected = project_evidence(
        read,
        integrity,
        HistoryQuery(),
        run_id="recorded-reader-fixture",
        kind="history",
    )
    for event in projected["items"]:
        assert (
            projected["presentation"][event["eventId"]]["recordedAtUtc"]
            == receipt_time(event)[1]
        )
    assert (root / "evidence.jsonl").read_bytes() == original


@pytest.mark.parametrize("sequence", [True, 1, 1.5, "01", "+1", " 1 "])
def test_reader_sequence_requires_canonical_decimal_string(tmp_path, sequence):
    rows, _ = _fixture.fixture_records(noise=0)
    first = {**rows[0], "sequence": sequence}
    root = tmp_path / "new-sequence-fixture"
    declared = _fixture.write_journal(root, [first])
    original = (root / "evidence.jsonl").read_bytes()
    _, integrity = read_journal(
        root,
        {
            "runId": "recorded-reader-fixture",
            "snapshotId": "fixture-snapshot",
            "state": "stopped",
            "journalDigest": declared,
        },
    )
    assert integrity == "invalid"
    assert (root / "evidence.jsonl").read_bytes() == original
