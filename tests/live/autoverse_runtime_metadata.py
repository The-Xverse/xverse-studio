"""Read-boundary faults in fresh copies of a real stopped Autoverse recording."""

import json
import os
from contextlib import contextmanager

import pytest

import autoverse_exchange_boundary as recording
from xverse_studio.security import managed_io
from xverse_studio.storage.core import atomic, canonical

recorded_demo = recording.recorded_demo


@pytest.mark.parametrize(
    "fault", ["none", "file-link", "parent-link", "hardlink", "oversized", "duplicate-key", "invalid-utf8"]
)
def test_original_autoverse_report_acquisition_never_promotes_unsafe_bytes(recorded_demo, fault):
    app, run, root = recorded_demo
    service = app.state.studio.runs
    store = app.state.studio.store
    original = store.get("run", run["runId"])
    path = root / "state.json"
    report = json.loads(path.read_bytes())
    report["stateVersion"] = original["stateVersion"] + 1
    report["liveValues"] = {"controlledReportMarker": "owned-native-observation"}
    path.write_text(canonical(report))
    if fault == "file-link":
        alternate = root / "original-state.json"
        path.rename(alternate)
        path.symlink_to(alternate)
    elif fault == "parent-link":
        alternate = root.with_name("original-" + root.name)
        root.rename(alternate)
        root.symlink_to(alternate, target_is_directory=True)
    elif fault == "hardlink":
        os.link(path, root / "second-state.json")
    elif fault == "oversized":
        with path.open("ab") as stream:
            stream.write(b" " * (1024 * 1024 + 1))
    elif fault == "duplicate-key":
        path.write_text('{"stateVersion":0,' + canonical(report)[1:])
    elif fault == "invalid-utf8":
        path.write_bytes(b"\xff")
    observed = service.read(run["runId"])
    if fault == "none":
        assert observed["stateVersion"] == report["stateVersion"]
        assert observed["liveValues"] == report["liveValues"]
    else:
        assert observed["stateVersion"] == original["stateVersion"]
        assert observed.get("liveValues") == original.get("liveValues")
    assert observed["state"] == original["state"] == "stopped"
    assert len(store.all("run")) == 1
    assert not (root / "command.json").exists()


@pytest.mark.parametrize("fault", ["none", "file-link", "hardlink", "oversized", "duplicate-key"])
def test_terminal_reacquisition_uses_the_same_autoverse_native_boundary(recorded_demo, fault):
    app, run, root = recorded_demo
    path = root / "state.json"
    if fault == "file-link":
        alternate = root / "original-state.json"
        path.rename(alternate)
        path.symlink_to(alternate)
    elif fault == "hardlink":
        os.link(path, root / "second-state.json")
    elif fault == "oversized":
        with path.open("ab") as stream:
            stream.write(b" " * (1024 * 1024 + 1))
    elif fault == "duplicate-key":
        path.write_text('{"stateVersion":0,' + path.read_text()[1:])
    try:
        observed = app.state.studio.runs._terminal_after_exit(path, run)
    except (OSError, ValueError):
        observed = None
    assert (observed is not None) == (fault == "none")


@pytest.mark.parametrize("keep_replacing", [False, True])
def test_atomic_autoverse_report_replacement_reacquires_with_a_fixed_budget(
    recorded_demo, monkeypatch, keep_replacing
):
    app, run, root = recorded_demo
    path = root / "state.json"
    report = json.loads(path.read_bytes())
    original = managed_io.open_read
    replacements = []

    @contextmanager
    def publish_after_capture(anchor, selected):
        with original(anchor, selected) as stream:
            yield stream
            if selected == path and (not replacements or keep_replacing):
                replacements.append(True)
                report["stateVersion"] += 1
                atomic(path, canonical(report).encode())

    monkeypatch.setattr(managed_io, "open_read", publish_after_capture)
    observed = app.state.studio.runs.read(run["runId"])
    assert len(replacements) == (4 if keep_replacing else 1)
    assert observed["stateVersion"] == (run["stateVersion"] if keep_replacing else report["stateVersion"])
    assert not (root / "command.json").exists()
