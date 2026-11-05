"""Read-only cache regressions using actual saved Autoverse and declared load bytes.

No provider is registered or dispatched. Mutated/copy controls use new temporary
files only, never the saved source recording.
"""

from collections import Counter
from contextlib import closing
import hashlib
import json
import os
from pathlib import Path
import shutil
import sqlite3

import pytest

from xverse_studio.evidence import reader


@pytest.fixture
def sources():
    recording = Path(os.environ["STUDIO_AUTOVERSE_PRESSURE_RECORDING"])
    result = json.loads((recording / "native-result.json").read_bytes())
    root = Path(json.loads((recording / "data-root.private.json").read_bytes())["dataRoot"])
    with closing(sqlite3.connect((root / "studio.sqlite").as_uri() + "?mode=ro", uri=True)) as db:
        runs = [json.loads(r[0]) for r in db.execute("SELECT body FROM records WHERE kind='run'")]
    large_id = result["syntheticHistory"]["runId"]
    large = next(r for r in runs if r["runId"] == large_id)
    left = next(r for r in runs if r["runId"] == result["sourceRunId"])
    right, = [r for r in runs if r["providerId"] == "autoverse.demo" and r["runId"] not in {left["runId"], result["runId"]}]
    assert large["eventCount"] == 50000 and large["evidenceScope"] == "recorded_fixture"
    assert all(r["state"] == "stopped" for r in [large, left, right])
    paths = [root / "runs" / r["runId"] / "evidence.jsonl" for r in [large, left, right]]
    before = {p: hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}
    with reader._CACHE_LOCK:
        reader._CACHE.clear()
    yield [(p.parent, r) for p, r in zip(paths, [large, left, right])]
    assert {p: hashlib.sha256(p.read_bytes()).hexdigest() for p in paths} == before
    with reader._CACHE_LOCK:
        reader._CACHE.clear()


def test_small_comparison_sources_do_not_repeat_large_verified_decode(sources, monkeypatch):
    counts = Counter()
    verify = reader.verify_journal

    def counted(data, state):
        counts[state["runId"]] += 1
        return verify(data, state)

    monkeypatch.setattr(reader, "verify_journal", counted)
    for _ in range(3):
        for directory, state in sources:
            rows, integrity = reader.read_journal(directory, state)
            assert integrity == "valid" and len(rows) == state["eventCount"]
    assert counts[sources[0][1]["runId"]] == 1, dict(counts)
    with reader._CACHE_LOCK:
        assert len(reader._CACHE) <= 2
        assert sum(v[2] for v in reader._CACHE.values()) <= reader.MAX_JOURNAL_BYTES


def test_large_source_cache_still_rejects_changed_bytes(sources, tmp_path):
    directory, state = sources[0]
    copy = tmp_path / "changed-owned-copy"
    copy.mkdir()
    target = copy / "evidence.jsonl"
    shutil.copyfile(directory / target.name, target)
    assert reader.read_journal(copy, state)[1] == "valid"
    changed = target.read_bytes() + b"not a canonical record\n"
    target.write_bytes(changed)
    assert reader.read_journal(copy, state)[1] == "invalid"
    assert target.read_bytes() == changed


def test_cache_keeps_original_byte_and_entry_bounds_for_large_copies(sources, tmp_path):
    directory, state = sources[0]
    for n in range(3):
        copy = tmp_path / ("owned-copy-" + str(n))
        copy.mkdir()
        shutil.copyfile(directory / "evidence.jsonl", copy / "evidence.jsonl")
        assert reader.read_journal(copy, state)[1] == "valid"
        with reader._CACHE_LOCK:
            assert len(reader._CACHE) <= 2
            assert sum(v[2] for v in reader._CACHE.values()) <= reader.MAX_JOURNAL_BYTES
