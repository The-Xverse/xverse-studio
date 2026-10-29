"""Bounded memoization reuses only exact authoritative read-only validation results."""
from copy import deepcopy
from pathlib import Path

import pytest

import xverse_studio.xdl as module
from xverse_studio.xdl import XDLAdapter, XDLRejected, examples


def spy_public(monkeypatch):
    actual = module.validate_sources
    calls = []
    def spy(*args, **kwargs):
        calls.append(args)
        return actual(*args, **kwargs)
    monkeypatch.setattr(module, "validate_sources", spy)
    return calls


def test_cache_reuses_public_result_and_returned_mutations_are_isolated(monkeypatch):
    calls = spy_public(monkeypatch)
    adapter = XDLAdapter()
    documents = examples()[0]["documents"]
    first = adapter.validate(documents)
    expected = deepcopy(first)
    assert first["valid"]
    first["resources"].clear()
    first["valid"] = False
    assert adapter.validate(documents) == expected
    assert len(calls) == 1
    assert adapter.validation_cache_info()["hits"] == 1
    # Compilation is always a fresh public compiler call, never a cached plan.
    compile_actual, compiled_calls = module.compile_experiment_sources, []
    def compile_spy(*args, **kwargs):
        compiled_calls.append(args)
        return compile_actual(*args, **kwargs)
    monkeypatch.setattr(module, "compile_experiment_sources", compile_spy)
    assert adapter.compile(documents)["valid"]
    assert adapter.compile(documents)["valid"]
    assert len(compiled_calls) == 2


def test_comment_source_and_document_path_changes_all_miss_cache(monkeypatch):
    calls = spy_public(monkeypatch)
    adapter = XDLAdapter()
    original = examples()[0]["documents"]
    assert adapter.validate(original)["valid"]
    comment = {**original, "system.xdl.yaml": "# source location changed\n" + original["system.xdl.yaml"]}
    assert adapter.validate(comment)["valid"]
    changed = {**original, "scenario.xdl.yaml": original["scenario.xdl.yaml"].replace("value: 0.8", "value: 0.7")}
    assert adapter.validate(changed)["valid"]
    renamed = {("renamed-system.xdl.yaml" if name == "system.xdl.yaml" else name): source for name, source in original.items()}
    assert adapter.validate(renamed)["valid"]
    assert len(calls) == 4


def test_actual_admitted_schema_bytes_change_invalidates_cache(tmp_path, monkeypatch):
    calls = spy_public(monkeypatch)
    adapter = XDLAdapter()
    schema = tmp_path / "explicit-experiment.schema.json"
    schema.write_bytes(Path(adapter.profile_schema_paths[0]).read_bytes())
    adapter.profile_schema_paths = (str(schema), *adapter.profile_schema_paths[1:])
    documents = examples()[0]["documents"]
    assert adapter.validate(documents)["valid"]
    assert adapter.validate(documents)["valid"]
    schema.write_bytes(schema.read_bytes() + b"\n")
    assert adapter.validate(documents)["valid"]
    assert len(calls) == 2


def test_entry_eviction_and_resource_limits_remain_enforced_before_lookup(monkeypatch):
    calls = spy_public(monkeypatch)
    adapter = XDLAdapter()
    documents = examples()[0]["documents"]
    for number in range(9):
        edited = {**documents, "system.xdl.yaml": "# variant " + str(number) + "\n" + documents["system.xdl.yaml"]}
        assert adapter.validate(edited)["valid"]
    assert adapter.validation_cache_info()["entries"] == 8
    first = {**documents, "system.xdl.yaml": "# variant 0\n" + documents["system.xdl.yaml"]}
    assert adapter.validate(first)["valid"]
    assert len(calls) == 10
    with pytest.raises(XDLRejected) as error:
        adapter.validate({"too-large.yaml": "#" + "x" * (1024 * 1024)})
    assert error.value.code == "LIMIT_EXCEEDED"
    assert len(calls) == 10


def test_result_byte_budget_evicts_instead_of_growing_without_bound(monkeypatch):
    calls = spy_public(monkeypatch)
    adapter = XDLAdapter()
    documents = examples()[0]["documents"]
    first = adapter.validate(documents)
    import json
    weight = len(json.dumps(first, separators=(",", ":"), ensure_ascii=False).encode())
    # A smaller test budget exercises the same production quota without a large fixture.
    adapter.cache_result_limit = weight + 128
    alternate = {**documents, "system.xdl.yaml": "# another exact source\n" + documents["system.xdl.yaml"]}
    assert adapter.validate(alternate)["valid"]
    info = adapter.validation_cache_info()
    assert info["entries"] == 1
    assert info["resultBytes"] <= adapter.cache_result_limit
    assert adapter.validate(documents)["valid"]
    assert len(calls) == 3


def test_platform_failure_is_never_cached(monkeypatch):
    calls = []
    def unavailable(*args, **kwargs):
        calls.append(args)
        raise OSError("synthetic unavailable schema reader")
    monkeypatch.setattr(module, "validate_sources", unavailable)
    adapter = XDLAdapter()
    documents = examples()[0]["documents"]
    for _ in range(2):
        report = adapter.validate(documents)
        assert report["validationStatus"] == "unavailable"
        assert report["diagnostics"][0]["code"] == "XDL_PLATFORM_FAILURE"
    assert len(calls) == 2
    assert adapter.validation_cache_info()["entries"] == 0
