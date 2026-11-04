"""Semantic decoder counterexamples derived from an actual completed demo.

These mutate decoded copies only. They deliberately exercise the mapping after
the raw-reader boundary; they are not raw-integrity or live-execution evidence.
The original canonical recording, snapshot and stored results remain unchanged.
"""
from copy import deepcopy
import hashlib
import json
import os
from pathlib import Path
import sqlite3

import pytest

from xverse_studio.evidence.reader import read_journal
from xverse_studio.providers.autoverse.adapter import AutoverseProvider


@pytest.fixture(scope="module")
def recorded():
    source = Path(os.environ["STUDIO_AUTOVERSE_ASSESSMENT_RECORDING"])
    result = json.loads((source / "native-result.json").read_bytes())
    assert result["outcome"] == "passed" and result["fullAndroidAndSpeedObserved"]
    root = Path(json.loads((source / "data-root.private.json").read_bytes())["dataRoot"])
    directory = root / "runs" / result["runId"]
    with sqlite3.connect((root / "studio.sqlite").as_uri() + "?mode=ro", uri=True) as db:
        run = json.loads(db.execute("SELECT body FROM records WHERE kind='run' AND id=?", (result["runId"],)).fetchone()[0])
    snapshot_file = root / "snapshots" / result["snapshotId"] / "snapshot.json"
    snapshot = json.loads(snapshot_file.read_bytes())
    records, integrity = read_journal(directory, run)
    assert integrity == "valid"
    files = [snapshot_file, directory / "evidence.jsonl", root / "studio.sqlite"]
    before = {str(f): hashlib.file_digest(f.open("rb"), "sha256").hexdigest() for f in files}
    receipt = json.loads(Path(os.environ["STUDIO_AUTOVERSE_TEST_INSTALLATION"]).read_bytes())
    provider = AutoverseProvider(receipt["classic"])
    mapping = provider.assessment_context(run, snapshot)
    assert mapping["coverageScope"] == "recorded-events-only"
    assert snapshot["providerIdentity"]["providerVersion"] == "0.3.0"
    yield provider, run, snapshot, records
    assert {str(f): hashlib.file_digest(f.open("rb"), "sha256").hexdigest() for f in files} == before


def project(recorded, mutate=None):
    provider, run, snapshot, original = recorded
    records = deepcopy(original)
    if mutate is not None:
        mutate(records)
    return provider.assessment_projection(deepcopy(run), deepcopy(snapshot), records, "valid")


def event(records, kind):
    return next(row for row in records if row["type"] == kind)


def test_actual_event_enumeration_keeps_original_evidence_identity(recorded):
    series = project(recorded)
    _, run, snapshot, _ = recorded
    assert {row["field"]: len(row["samples"]) for row in series} == {"activationObserved": 3, "recoveryObserved": 2}
    for row in series:
        assert row["integrity"] == "valid" and row["coverage"]["verified"] and row["coverage"]["complete"]
        assert row["evidenceId"] == run["journalId"] and row["digest"] == run["journalDigest"]
        assert row["snapshotId"] == snapshot["snapshotId"] and row["clockDomainRef"] == "host-runtime"


@pytest.mark.parametrize("kind", ["fault.activation_observed", "fault.recovery_observed"])
@pytest.mark.parametrize("value", [False, -1, 0, 1.5, 2**53])
def test_acknowledgement_cannot_certify_an_invalid_dropped_frame_identifier(recorded, kind, value):
    def corrupt(records):
        event(records, kind)["payload"]["lastDroppedSequence"] = value
    assert all(row["integrity"] == "invalid" and not row["coverage"]["verified"] for row in project(recorded, corrupt))


@pytest.mark.parametrize("value", [False, -1, 1.5, 2**53])
def test_recovery_publication_obeys_the_admitted_frame_identifier_range(recorded, value):
    def corrupt(records):
        event(records, "fault.recovery_observed")["payload"]["publicationSequence"] = value
    assert all(row["integrity"] == "invalid" and not row["coverage"]["verified"] for row in project(recorded, corrupt))


@pytest.mark.parametrize("case", ["prefix", "counts", "boolean-count", "foreign-clock", "foreign-run", "duplicate-cutoff", "unconfirmed-recovery"])
def test_changed_producer_proof_never_establishes_complete_coverage(recorded, case):
    def corrupt(records):
        coverage = event(records, "assessment.coverage")
        observed = event(records, "fault.recovery_observed")
        if case == "prefix":
            coverage["payload"]["prefixDigest"] = "sha256:" + "0" * 64
        elif case == "counts":
            coverage["payload"]["sampleCounts"]["activationObserved"] += 1
        elif case == "boolean-count":
            coverage["payload"]["sampleCounts"]["activationObserved"] = True
        elif case == "foreign-clock":
            observed["sourceTime"]["clockDomain"] = "simulation-time"
        elif case == "foreign-run":
            observed["runId"] = "foreign-run"
        elif case == "duplicate-cutoff":
            records.append(deepcopy(coverage))
        elif case == "unconfirmed-recovery":
            observed["payload"]["publicationSequence"] = observed["payload"]["lastDroppedSequence"]
    assert all(row["integrity"] == "invalid" and not row["coverage"]["verified"] for row in project(recorded, corrupt))


def test_absent_cutoff_does_not_invent_event_coverage(recorded):
    def remove_cutoff(records):
        records[:] = [row for row in records if row["type"] != "assessment.coverage"]
    rows = project(recorded, remove_cutoff)
    assert all(row["integrity"] == "valid" and not row["coverage"]["verified"] and not row["coverage"]["complete"] for row in rows)
