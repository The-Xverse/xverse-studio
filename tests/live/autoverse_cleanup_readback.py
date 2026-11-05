"""Actual retained container identity, simulated acknowledgement/readback timing.

Only new in-memory observations are changed. No Docker command is dispatched;
the failed actual cancellation and later separate stopped readback stay distinct.
"""

from copy import deepcopy
import hashlib
import json
import os
from pathlib import Path
import subprocess
from types import SimpleNamespace

import pytest

from xverse_studio.providers.autoverse import cleanup
from xverse_studio.providers.autoverse.installation import container_fact


@pytest.fixture
def source():
    state = Path(os.environ["STUDIO_AUTOVERSE_CLEANUP_RECORDING"])
    saved = state / "pressure-cancel"
    result = json.loads((saved / "native-result.json").read_bytes())
    data = Path(json.loads((saved / "data-root.private.json").read_bytes())["dataRoot"])
    root = data / "runs" / result["runId"]
    rows = state / "cancel-current-container-rows.private.json"
    paths = [rows, root / "state.json", root / "evidence.jsonl", root / "containers.private.json"]
    before = {p: hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}
    claim = json.loads((root / "containers.private.json").read_bytes())["score"]
    row = json.loads(rows.read_bytes())["score"]
    assert container_fact(row) == claim["identity"] and row["State"]["StartedAt"] == claim["startedAt"]
    assert row["State"]["Running"] is False
    assert json.loads((root / "state.json").read_bytes())["cleanup"] == "unknown"
    installation = json.loads((state / "installation-verified.private.json").read_bytes())["classic"]
    yield installation, claim, row
    assert {p: hashlib.sha256(p.read_bytes()).hexdigest() for p in paths} == before


def simulate(source, monkeypatch, states, *, fault=None, deadline=None):
    installation, claim, actual = source
    clock, calls, observations = [100.0], [], []

    def inspect(docker, identifier, **options):
        assert docker == installation["docker"] and identifier == claim["identity"]["id"]
        observations.append(options["timeout"])
        row = deepcopy(actual)
        row["State"]["Running"] = states[min(len(observations) - 1, len(states) - 1)]
        if len(observations) >= 3:
            if fault == "start":
                row["State"]["StartedAt"] = "another-inert-start"
            elif fault == "configuration":
                row["Config"]["Image"] = "another-inert-image"
            elif fault == "unavailable":
                raise OSError("inert-private-marker")
        return row

    def stop(argv, **options):
        assert argv == [installation["docker"], "stop", "--time", "10", claim["identity"]["id"]]
        calls.append(options["timeout"])
        clock[0] += options["timeout"]
        raise subprocess.TimeoutExpired(argv, options["timeout"])

    monkeypatch.setattr(cleanup, "inspect", inspect)
    monkeypatch.setattr(cleanup, "time", SimpleNamespace(monotonic=lambda: clock[0], sleep=lambda seconds: clock.__setitem__(0, clock[0] + seconds)))
    monkeypatch.setattr(cleanup, "subprocess", SimpleNamespace(run=stop, TimeoutExpired=subprocess.TimeoutExpired, CalledProcessError=subprocess.CalledProcessError, SubprocessError=subprocess.SubprocessError))
    result = cleanup.cleanup_container(installation, "score", claim, deadline=deadline)
    return result, calls, observations, clock[0] - 100


def test_late_original_release_is_observed_without_replaying_stop(source, monkeypatch):
    result, calls, observations, seconds = simulate(source, monkeypatch, [True, True, False])
    assert result == {"resourceId": "score", "kind": "container", "status": "released", "diagnostics": ["AUTOVERSE_CONTAINER_STOP_TIMEOUT"]}
    assert len(calls) == 1 and len(observations) == 3 and 20 < seconds <= 50


@pytest.mark.parametrize("fault", ["start", "configuration", "unavailable"])
def test_later_changed_or_unavailable_identity_never_confirms_release(source, monkeypatch, fault):
    result, calls, observations, seconds = simulate(source, monkeypatch, [True], fault=fault)
    assert result["status"] == "unknown" and len(calls) == 1 and len(observations) == 3
    code = "AUTOVERSE_CONTAINER_INSPECTION_UNAVAILABLE" if fault == "unavailable" else "AUTOVERSE_CONTAINER_OWNERSHIP_UNKNOWN"
    assert code in result["diagnostics"] and "inert-private-marker" not in json.dumps(result)
    assert seconds <= 50


def test_still_running_source_exhausts_original_budget_without_another_stop(source, monkeypatch):
    result, calls, observations, seconds = simulate(source, monkeypatch, [True])
    assert result["status"] == "unknown" and len(calls) == 1
    assert 2 < len(observations) <= 282 and seconds <= 50
    assert "AUTOVERSE_CLEANUP_DEADLINE" in result["diagnostics"]


def test_shorter_caller_deadline_is_preserved(source, monkeypatch):
    result, calls, observations, seconds = simulate(source, monkeypatch, [True], deadline=105)
    assert result["status"] == "unknown" and calls == [5] and len(observations) == 1
    assert seconds == 5 and "AUTOVERSE_CLEANUP_DEADLINE" in result["diagnostics"]


def test_initially_stopped_target_that_reappears_is_never_stopped_or_polled(source, monkeypatch):
    result, calls, observations, _ = simulate(source, monkeypatch, [False, True])
    assert result["status"] == "unknown" and not calls and len(observations) == 2
    assert result["diagnostics"] == ["AUTOVERSE_CONTAINER_STOP_UNCONFIRMED"]
