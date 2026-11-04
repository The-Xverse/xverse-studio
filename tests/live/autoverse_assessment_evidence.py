"""Actual recorded Autoverse evidence must not inherit reference measurement rules."""
from copy import deepcopy
import pytest

import autoverse_fault_timeline as recording
from xverse_studio.api.advanced import _journal_projection
from xverse_studio.assertions import EvaluationError
from xverse_studio.assertions.evidence import evidence_support, UNSUPPORTED


actual = recording.actual

def test_actual_canonical_autoverse_reader_is_explicitly_unavailable_for_evaluation(actual):
    run, snapshot, records, _ = actual
    assert records and run["effectivePlanDigest"] == snapshot["planDigest"]
    result = evidence_support(run, snapshot)
    assert result == {"formatVersion": "1.0", "runId": run["runId"], "snapshotId": run["snapshotId"],
                      "projectId": run["projectId"], "snapshotDigest": snapshot["snapshotDigest"],
                      "providerId": "autoverse.demo", "evidenceScope": "external_demo",
                      "evidenceId": run["runId"] + ":provider-journal", "evidenceReader": "studio.hash-chain-v1",
                      "status": "unsupported", "reasons": [UNSUPPORTED]}
    with pytest.raises(EvaluationError) as failure:
        _journal_projection(run, snapshot, records, "valid")
    assert failure.value.code == UNSUPPORTED


@pytest.mark.parametrize("case", ["run-provider", "snapshot-provider", "frozen-provider", "run-scope", "frozen-scope",
                                 "reader", "journal-id", "missing-reader", "missing-journal", "malformed-provider"])
def test_partial_reference_metadata_does_not_admit_actual_external_evidence(actual, case):
    run, snapshot, records, _ = actual
    run, snapshot = deepcopy(run), deepcopy(snapshot)
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
    elif case == "missing-reader":
        run.pop("journalReader")
    elif case == "missing-journal":
        run.pop("journalId")
    else:
        snapshot["providerIdentity"] = []
    assert evidence_support(run, snapshot)["status"] == "unsupported"
    with pytest.raises(EvaluationError) as failure:
        _journal_projection(run, snapshot, records, "valid")
    assert failure.value.code == UNSUPPORTED


def test_reference_shaped_payload_does_not_grant_external_producer_coverage(actual):
    run, snapshot, records, _ = actual
    records = deepcopy(records)
    observation = next(r for r in records if r["type"] == "observation.available")
    # Controlled decoder counterexample only. Original canonical bytes never change.
    observation["payload"].update(observerRef="autoverse-telemetry", values={"value": 1}, units={"value": "1"})
    observation["sourceTime"] = {"tick": "1", "clockDomain": "simulation-time", "resolution": "microsecond"}
    records.append({"type": "evidence.updated", "payload": {"coverage": {"complete": True, "startTick": "0", "endTick": "2"}}})
    with pytest.raises(EvaluationError) as failure:
        _journal_projection(run, snapshot, records, "valid")
    assert failure.value.code == UNSUPPORTED
