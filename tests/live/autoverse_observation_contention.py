"""Copied actual Autoverse sources and explicit stalled-reader callbacks only.

No runtime is registered, launched or stimulated. The input callback below is a
sentinel that must never run: terminal source states must reject driver input.
"""

from concurrent.futures import ThreadPoolExecutor
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import threading
from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient

from xverse_studio.api.app import create_app
from xverse_studio.runs import service
from xverse_studio.storage.core import Problem


@pytest.fixture
def copied(tmp_path, monkeypatch):
    saved = Path(os.environ["STUDIO_AUTOVERSE_PRESSURE_RECORDING"])
    report = json.loads((saved / "native-result.json").read_bytes())
    source = Path(json.loads((saved / "data-root.private.json").read_bytes())["dataRoot"])
    spec = importlib.util.spec_from_file_location(
        "contention_copy_tools", Path(__file__).with_name("autoverse_exchange_native.py")
    )
    tools = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(tools)
    before = hashlib.sha256((source / "studio.sqlite").read_bytes()).hexdigest()
    journals = {p: hashlib.sha256(p.read_bytes()).hexdigest() for p in (source / "runs").glob("*/evidence.jsonl")}
    data = tmp_path / "copied-autoverse"
    tools.clone(source, data)
    app = create_app(data, bootstrap_token="inert-contention-test", allowed_hosts=["testserver"])

    def forbidden(*args, **kwargs):
        pytest.fail("Offline contention test attempted native contact")

    for name in ("Popen", "run", "check_output"):
        monkeypatch.setattr(subprocess, name, forbidden)
    studio = app.state.studio
    studio._inert_contention_app = app
    left = report["sourceRunId"]
    right = report["runId"]
    assert all(studio.store.get("run", rid)["state"] == "stopped" for rid in (left, right))
    studio.runs.installed_providers["autoverse.demo"] = SimpleNamespace(input_request=forbidden)
    yield studio, left, right
    assert hashlib.sha256((source / "studio.sqlite").read_bytes()).hexdigest() == before
    assert {p: hashlib.sha256(p.read_bytes()).hexdigest() for p in journals} == journals


@pytest.mark.parametrize("stage", ["journal", "assessment"])
@pytest.mark.parametrize("same_run", [False, True])
def test_slow_presentation_does_not_hold_metadata_lock_or_delay_control(copied, monkeypatch, stage, same_run):
    studio, left, right = copied
    if same_run:
        right = left
    entered, release, control_done = threading.Event(), threading.Event(), threading.Event()
    read_journal, assessment = service.read_journal, studio.runs.assessment_summary

    def stalled_journal(root, state):
        if stage == "journal" and root.name == left:
            entered.set()
            assert release.wait(10), "Test did not release stalled journal acquisition"
        return read_journal(root, state)

    def stalled_assessment(run):
        if stage == "assessment" and run["runId"] == left:
            entered.set()
            assert release.wait(10), "Test did not release stalled assessment"
        return assessment(run)

    def terminal_control():
        try:
            with pytest.raises(Problem) as error:
                studio.runs.input_request(right, "acquire", {}, "inert-sentinel")
            assert error.value.code == "STATE_CONFLICT"
        finally:
            control_done.set()

    monkeypatch.setattr(service, "read_journal", stalled_journal)
    monkeypatch.setattr(studio.runs, "assessment_summary", stalled_assessment)
    with ThreadPoolExecutor(max_workers=2) as pool:
        observation = pool.submit(studio.runs.read, left)
        try:
            assert entered.wait(5)
            control = pool.submit(terminal_control)
            # This is a synchronization witness, not a claimed live latency SLA:
            # the blocked presentation callback cannot finish before release.
            assert control_done.wait(1), "Presentation work holds the control metadata lock"
            control.result(timeout=1)
        finally:
            release.set()
        assert observation.result(timeout=10)["runId"] == left


@pytest.mark.parametrize("stage", ["journal", "assessment"])
def test_late_derived_read_cannot_overwrite_newer_persisted_observation(copied, monkeypatch, stage):
    studio, left, _ = copied
    entered, release = threading.Event(), threading.Event()
    original_journal, original_assessment = service.read_journal, studio.runs.assessment_summary
    calls = []

    def pause_once():
        calls.append(True)
        if len(calls) == 1:
            entered.set()
            assert release.wait(10)

    def journal(root, state):
        if stage == "journal" and root.name == left:
            pause_once()
        return original_journal(root, state)

    def assessment(run):
        if stage == "assessment" and run["runId"] == left:
            pause_once()
        return original_assessment(run)

    def newer_observation():
        with studio.store.lock:
            row = studio.store.get("run", left)
            row.update(lateObservationMarker="newer-inert-metadata", observationVersion=row.get("observationVersion", 0) + 1)
            studio.store.put("run", left, row)

    monkeypatch.setattr(service, "read_journal", journal)
    monkeypatch.setattr(studio.runs, "assessment_summary", assessment)
    with ThreadPoolExecutor(max_workers=2) as pool:
        old = pool.submit(studio.runs.read, left)
        try:
            assert entered.wait(5)
            writer = pool.submit(newer_observation)
            writer.result(timeout=1)
        finally:
            release.set()
        result = old.result(timeout=10)
    assert result["lateObservationMarker"] == "newer-inert-metadata"
    assert studio.store.get("run", left) == result
    assert len(calls) >= 2, "A stale derivation must be retried against the newer observation"


def test_terminal_input_refusal_never_runs_presentation_derivation(copied, monkeypatch):
    studio, _, right = copied

    def forbidden(*args, **kwargs):
        pytest.fail("Lifecycle control attempted presentation derivation")

    monkeypatch.setattr(service, "read_journal", forbidden)
    monkeypatch.setattr(studio.runs, "assessment_summary", forbidden)
    with pytest.raises(Problem) as error:
        studio.runs.input_request(right, "acquire", {}, "inert-sentinel")
    assert error.value.code == "STATE_CONFLICT"


def test_terminal_command_refusal_never_runs_presentation_derivation(copied, monkeypatch):
    studio, _, right = copied
    before = studio.store.all("operation")

    def forbidden(*args, **kwargs):
        pytest.fail("Lifecycle command attempted presentation derivation")

    monkeypatch.setattr(service, "read_journal", forbidden)
    monkeypatch.setattr(studio.runs, "assessment_summary", forbidden)
    with pytest.raises(Problem) as error:
        studio.runs.command(right, "inert-sentinel", "terminal-no-command", {
            "kind": "stop", "expectedStateVersion": studio.store.get("run", right)["stateVersion"],
        })
    assert error.value.code == "STATE_CONFLICT"
    assert studio.store.all("operation") == before


def test_conflict_retry_is_bounded_and_never_publishes_stale_derived_fields(copied, monkeypatch):
    studio, left, _ = copied
    calls = []
    before = studio.store.get("run", left)

    def changing_assessment(run):
        calls.append(True)
        with studio.store.lock:
            current = studio.store.get("run", left)
            current.update(lateObservationMarker=len(calls), observationVersion=current.get("observationVersion", 0) + 1)
            studio.store.put("run", left, current)
        return {"evaluationSummary": {"diagnostics": ["must-not-be-published"]}}

    monkeypatch.setattr(studio.runs, "assessment_summary", changing_assessment)
    with pytest.raises(Problem) as error:
        studio.runs.read(left)
    assert error.value.code == "RUN_OBSERVATION_UNAVAILABLE" and error.value.status == 503
    assert error.value.details["retryable"] is True
    assert len(calls) == service.MAX_DERIVED_OBSERVATION_ATTEMPTS == 4
    current = studio.store.get("run", left)
    assert current["lateObservationMarker"] == 4
    assert current.get("evaluationSummary") == before.get("evaluationSummary")


def test_unchanged_and_corrupt_journal_reads_keep_write_and_integrity_semantics(copied, monkeypatch):
    studio, left, _ = copied
    first = studio.runs.read(left)
    writes, put = [], studio.store.put

    def counted(kind, identity, body, db=None):
        if db is not None:
            writes.append((kind, identity))
        return put(kind, identity, body, db)

    monkeypatch.setattr(studio.store, "put", counted)
    for _ in range(3):
        assert studio.runs.read(left) == first
    assert not writes
    journal = studio.runs.directory(left) / "evidence.jsonl"
    journal.write_bytes(journal.read_bytes() + b"invalid-inert-copy-record\n")
    current = studio.runs.read(left)
    assert current["evidence"] == "invalid" and writes == [("run", left)]
    writes.clear()
    assert studio.runs.read(left) == current and not writes


def test_new_cleanup_observation_is_persisted_once(copied, monkeypatch):
    studio, left, _ = copied
    baseline = studio.runs.read(left)
    report = studio.runs.directory(left) / "state.json"
    observation = json.loads(report.read_bytes())
    observation.update(cleanup="unknown", stateVersion=baseline["stateVersion"] + 1)
    report.write_text(json.dumps(observation))
    writes, put = [], studio.store.put

    def counted(kind, identity, body, db=None):
        if db is not None and kind == "run":
            writes.append(identity)
        return put(kind, identity, body, db)

    monkeypatch.setattr(studio.store, "put", counted)
    current = studio.runs.read(left)
    assert current["cleanup"] == "unknown" and current["stateVersion"] == observation["stateVersion"]
    assert writes == [left]
    writes.clear()
    assert studio.runs.read(left) == current and not writes


def test_waiting_session_lookup_does_not_block_the_http_event_loop(copied, monkeypatch):
    studio, _, _ = copied
    entered, public_done = threading.Event(), threading.Event()
    get = studio.store.get

    def observed_get(kind, identity, db=None):
        if kind == "session":
            entered.set()
        return get(kind, identity, db)

    with TestClient(studio._inert_contention_app) as api:
        api.headers["Origin"] = "http://testserver"
        assert api.post("/api/v1/session", json={"bootstrapToken": "inert-contention-test"}).status_code == 200
        monkeypatch.setattr(studio.store, "get", observed_get)

        def public_request():
            try:
                response = api.get("/inert-missing-static-resource.txt")
                assert response.status_code == 404
            finally:
                public_done.set()

        with ThreadPoolExecutor(max_workers=2) as pool:
            with studio.store.lock:
                authenticated = pool.submit(api.get, "/api/v1/session")
                assert entered.wait(5)
                public = pool.submit(public_request)
                assert public_done.wait(1), "Synchronous authentication blocks the ASGI event loop"
                public.result(timeout=1)
            assert authenticated.result(timeout=5).status_code == 200


def test_optional_input_timings_preserve_refusal_and_exclude_private_values(copied):
    studio, _, right = copied
    spec = importlib.util.spec_from_file_location("inert_input_timing", Path(__file__).with_name("autoverse_input_timing.py"))
    timing = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(timing)
    original_read = studio.runs.read
    timing.install(studio._inert_contention_app, studio.store.root)
    with TestClient(studio._inert_contention_app) as api:
        api.headers["Origin"] = "http://testserver"
        login = api.post("/api/v1/session", json={"bootstrapToken": "inert-contention-test"})
        assert login.status_code == 200
        csrf = login.json()["csrfToken"]
        cookie = api.cookies.get("studio_session")
        api.headers["X-CSRF-Token"] = csrf
        response = api.post(f"/api/v1/runs/{right}/input/frame", json={"leaseToken": "owned-private-input-marker", "generation": 1, "frame": {}})
        assert response.status_code == 409 and response.json()["code"] == "STATE_CONFLICT"
    raw = (studio.store.root / "input-timing.private.json").read_text()
    report = json.loads(raw)
    assert len(report["samples"]) == 1 and report["maximumSamples"] == 256
    sample, = report["samples"]
    assert sample["failureCode"] == "STATE_CONFLICT" and sample["statusCode"] == 409
    assert sample["inputRequestSeconds"] >= sample["lifecycleReadSeconds"] >= 0
    assert "providerInputSeconds" not in sample
    assert all(secret not in raw for secret in [csrf, cookie, "owned-private-input-marker"])
    assert studio.runs.read == original_read
