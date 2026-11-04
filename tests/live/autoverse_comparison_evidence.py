"""Actual immutable Autoverse input and labelled decoded-copy counterexamples.

No source bytes are modified, no provider is installed/called and no execution
is requested. Reference-shaped copied values are not original observations.
"""

from copy import deepcopy
import hashlib
import json
import os
from pathlib import Path
import sqlite3

import pytest

from xverse_studio.comparison import compare_runs, recorded_input
from xverse_studio.evidence.reader import read_journal
from xverse_studio.storage.core import digest


@pytest.fixture(scope="module")
def actual():
    recording = Path(os.environ["STUDIO_AUTOVERSE_COMPARISON_RECORDING"])
    result = json.loads((recording / "native-result.json").read_text())
    assert result["outcome"] == "passed" and result["fullAndroidAndSpeedObserved"]
    root = Path(
        json.loads((recording / "data-root.private.json").read_text())["dataRoot"]
    )
    with sqlite3.connect(
        (root / "studio.sqlite").as_uri() + "?mode=ro", uri=True
    ) as db:
        run = json.loads(
            db.execute(
                "SELECT body FROM records WHERE kind='run' AND id=?", (result["runId"],)
            ).fetchone()[0]
        )
    frozen = root / "snapshots" / run["snapshotId"] / "snapshot.json"
    journal = root / "runs" / run["runId"] / "evidence.jsonl"
    snapshot = json.loads(frozen.read_bytes())
    assert (
        digest({k: v for k, v in snapshot.items() if k != "snapshotDigest"})
        == snapshot["snapshotDigest"]
    )
    records, integrity = read_journal(journal.parent, run)
    assert integrity == "valid" and len(records) == 93
    assert (
        run["providerId"] == "autoverse.demo"
        and run["evidenceScope"] == "external_demo"
    )
    assert snapshot["providerIdentity"]["providerVersion"] == "0.3.0"
    paths = [root / "studio.sqlite", frozen, journal]
    before = {str(p): hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}
    yield run, snapshot, records
    assert {str(p): hashlib.sha256(p.read_bytes()).hexdigest() for p in paths} == before


def test_actual_canonical_reader_keeps_integrity_but_has_no_numeric_comparison_mapping(
    actual,
):
    run, snapshot, records = actual
    original = deepcopy((run, snapshot, records))
    side = recorded_input(run, snapshot, records, "valid", snapshot_integrity="valid")
    assert side["evidence"] == {"integrity": "valid", "status": run["evidence"]}
    assert side["effectiveInputsMatch"] and side["observations"] == []
    assert "COMPARISON_EVIDENCE_UNSUPPORTED" in side["projectionDiagnostics"]
    report = compare_runs(side, side)
    assert (
        not report["compatible"]
        and "COMPARISON_EVIDENCE_UNSUPPORTED" in report["diagnostics"]
    )
    assert report["left"]["evidenceIntegrity"] == "valid"
    assert "EVIDENCE_INCOMPLETE" not in report["diagnostics"]
    assert (run, snapshot, records) == original


@pytest.mark.parametrize(
    "case",
    [
        "original-identity",
        "run-provider",
        "snapshot-provider",
        "frozen-provider",
        "run-scope",
        "frozen-scope",
        "reader",
        "journal-id",
        "legacy-reader-claim",
        "declared-support",
    ],
)
def test_reference_shaped_decoded_values_cannot_gain_owned_unit_or_coverage_semantics(
    actual, case
):
    run, snapshot, original_records = deepcopy(actual)
    if case == "run-provider":
        run["providerId"] = "studio.reference"
    elif case == "snapshot-provider":
        snapshot["providerId"] = "studio.reference"
    elif case == "frozen-provider":
        snapshot["providerIdentity"]["providerId"] = "studio.reference"
    elif case == "run-scope":
        run["evidenceScope"] = "owned_reference"
    elif case == "frozen-scope":
        snapshot["providerIdentity"]["evidenceScope"] = "owned_reference"
    elif case == "reader":
        run["journalReader"] = "studio.reference.hash-chain-v1"
    elif case == "journal-id":
        run["journalId"] = run["runId"] + ":reference-journal"
    elif case == "legacy-reader-claim":
        run.pop("journalReader")
        run.pop("journalId")
    elif case == "declared-support":
        run["comparisonSupported"] = True
        snapshot["comparisonContract"] = {"supported": True}
    observation = deepcopy(
        next(r for r in original_records if r["type"] == "observation.available")
    )
    observation["payload"] = {
        "observerRef": "autoverse-telemetry",
        "values": {"value": 1},
        "units": {"value": "1"},
    }
    observation["sourceTime"] = {
        "tick": "1",
        "clockDomain": "simulation-time",
        "resolution": "microsecond",
        "uncertainty": 0,
    }
    records = [
        observation,
        {
            "type": "evidence.updated",
            "payload": {
                "coverage": {
                    "clockDomain": "simulation-time",
                    "startTick": "0",
                    "endTick": "2",
                    "complete": True,
                }
            },
        },
    ]
    before = deepcopy((run, snapshot, records))
    side = recorded_input(run, snapshot, records, "valid", snapshot_integrity="valid")
    assert side["observations"] == []
    assert "COMPARISON_EVIDENCE_UNSUPPORTED" in side["projectionDiagnostics"]
    assert not compare_runs(side, side)["compatible"]
    assert (run, snapshot, records) == before
