"""History API projections over copied actual sources; no runtime dispatch."""

from copy import deepcopy
import hashlib
import importlib.util
import json
from pathlib import Path
from types import SimpleNamespace

import pytest
from starlette.datastructures import QueryParams

from xverse_studio.evidence import query
from xverse_studio.storage.core import canonical, digest


spec = importlib.util.spec_from_file_location("history_contention_sources", Path(__file__).with_name("autoverse_observation_contention.py"))
tools = importlib.util.module_from_spec(spec)
spec.loader.exec_module(tools)
copied = tools.copied


@pytest.fixture
def history(copied, monkeypatch):
    studio, left, _ = copied
    run, = [r for r in studio.store.all("run") if r.get("evidenceScope") == "recorded_fixture" and r.get("eventCount") == 50000]
    endpoint = next(route.endpoint for route in studio._inert_contention_app.routes if getattr(route, "path", None) == "/api/v1/runs/{runId}/history")
    calls, original = [], query._facets

    def counted(records):
        calls.append(len(records))
        return original(records)

    monkeypatch.setattr(query, "_facets", counted)

    def request(run_id=None, **values):
        return endpoint(run_id or run["runId"], query.HistoryQuery(**values), SimpleNamespace(query_params=QueryParams()))

    return studio, left, run["runId"], request, calls


def rewrite_copy(studio, run_id, value):
    """Controlled new-copy content, never the original recording or a live claim."""
    root = studio.runs.directory(run_id)
    journal = root / "evidence.jsonl"
    rows = [json.loads(line) for line in journal.read_bytes().splitlines()]
    rows[0]["payload"]["controlledProjectionFixture"] = value
    previous, lines = "0" * 64, []
    for record in rows:
        record["previousDigest"] = previous
        previous = hashlib.sha256(canonical({k: v for k, v in record.items() if k != "digest"}).encode()).hexdigest()
        record["digest"] = previous
        lines.append((canonical(record) + "\n").encode())
    journal.write_bytes(b"".join(lines))
    current = studio.store.get("run", run_id)
    current["journalDigest"] = digest(journal.read_bytes())
    studio.store.put("run", run_id, current)
    path = root / "state.json"
    if path.exists():
        state = json.loads(path.read_bytes())
        state["journalDigest"] = current["journalDigest"]
        path.write_text(json.dumps(state))


def test_repeated_verified_terminal_history_does_not_repeat_full_source_scan(history):
    _, _, _, request, calls = history
    first = request(limit=200, type="log.appended", severity="info")
    assert first["integrity"] == "valid" and first["counts"]["totalRecords"] == 50000
    assert len(first["items"]) == 200
    for _ in range(2):
        assert request(limit=200, type="log.appended", severity="info") == first
    assert calls == [50000]


def test_current_corruption_cannot_use_a_previously_valid_projection(history):
    studio, _, run_id, request, calls = history
    assert request()["integrity"] == "valid"
    journal = studio.runs.directory(run_id) / "evidence.jsonl"
    journal.write_bytes(journal.read_bytes() + b"invalid-controlled-copy-line\n")
    current = request()
    assert current["integrity"] == "invalid" and current["gaps"]
    assert calls == [50000, 50000]


def test_changed_valid_source_with_same_record_count_cannot_reuse_old_results(history):
    studio, left, _, request, calls = history
    first = deepcopy(request(left))
    rewrite_copy(studio, left, "new-controlled-copy-content")
    current = request(left)
    assert current["integrity"] == "valid" and current["counts"] == first["counts"]
    assert current["items"][0]["payload"]["controlledProjectionFixture"] == "new-controlled-copy-content"
    assert current["items"][0]["digest"] != first["items"][0]["digest"]
    assert len(calls) == 2


def test_filter_and_evidence_scope_stay_bound_to_each_projection(history):
    studio, _, run_id, request, calls = history
    first = request(limit=200, severity="info")
    empty = request(limit=200, severity="error")
    assert empty["items"] == [] and empty["counts"]["matchedRecords"] == 0
    assert request(limit=200, severity="info") == first
    assert len(calls) == 2
    row = studio.store.get("run", run_id)
    row["evidenceScope"] = "unverified_recorded"
    studio.store.put("run", run_id, row)
    assert request(limit=200, severity="info")["evidenceScope"] == "unverified_recorded"
    assert len(calls) == 3


def test_history_projection_retention_evicts_old_filters(history):
    _, _, _, request, calls = history
    for limit in range(1, 11):
        assert len(request(limit=limit)["items"]) == limit
    assert len(calls) == 10
    request(limit=10)
    assert len(calls) == 10
    request(limit=1)
    assert len(calls) == 11


def test_oversized_projection_is_returned_without_retaining_it(history):
    studio, left, _, request, calls = history
    value = "owned-large-projection-fixture" * 20000
    rewrite_copy(studio, left, value)
    for _ in range(2):
        result = request(left)
        assert result["integrity"] == "valid"
        assert result["items"][0]["payload"]["controlledProjectionFixture"] == value
    assert len(calls) == 2


def test_serialized_byte_budget_evicts_before_the_entry_limit(history):
    studio, left, _, request, calls = history
    # JSON escaping makes each result exceed1MiB while staying cacheable. Four
    # such entries exceed the4MiB total even though fewer than eight filters exist.
    rewrite_copy(studio, left, "\x01" * 190000)
    for limit in range(1, 5):
        assert request(left, limit=limit)["integrity"] == "valid"
    assert len(calls) == 4
    request(left, limit=4)
    assert len(calls) == 4
    request(left, limit=1)
    assert len(calls) == 5


def test_returned_projection_cannot_mutate_another_result_or_canonical_capture(history):
    from xverse_studio.evidence.reader import read_journal

    studio, _, run_id, request, calls = history
    first = request(limit=200)
    original = deepcopy(first)
    first["items"][0]["payload"]["message"] = "changed-return-value-only"
    assert request(limit=200) == original and len(calls) == 1
    records, integrity = read_journal(studio.runs.directory(run_id), studio.store.get("run", run_id))
    assert integrity == "valid" and records[0] == original["items"][0]
