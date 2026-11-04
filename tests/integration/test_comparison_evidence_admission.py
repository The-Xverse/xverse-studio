"""Inert source-codec fixtures; no Start, worker, provider or device operation."""

from copy import deepcopy

import pytest

from xverse_studio.comparison import compare_runs, recorded_input


def source_fixture():
    # Reuse the existing frozen-fact fixture. These claims are controlled input
    # to the decoder, not proof of a native execution or of protected snapshots.
    from test_comparison_report import fixture_run

    snapshot = deepcopy(fixture_run()["snapshot"])
    snapshot["providerId"] = "studio.reference"
    snapshot["providerIdentity"].update(
        providerId="studio.reference", evidenceScope="owned_reference"
    )
    run = {
        "runId": "fixture-run",
        "snapshotId": snapshot["snapshotId"],
        "projectId": snapshot["projectId"],
        "providerId": "studio.reference",
        "evidenceScope": "owned_reference",
        "state": "stopped",
        "cleanup": "complete",
        "evidence": "complete",
        "journalReader": "studio.reference.hash-chain-v1",
        "journalId": "fixture-run:reference-journal",
        "effectivePlanDigest": snapshot["planDigest"],
        "effectiveSemanticDigest": snapshot["semanticDigest"],
    }
    records = [
        {
            "type": "observation.available",
            "payload": {
                "observerRef": "fixture-observer",
                "values": {"state": 1.0},
                "units": {"state": "1"},
            },
            "sourceTime": {
                "tick": tick,
                "clockDomain": "simulation-time",
                "resolution": "microsecond",
                "uncertainty": 0,
            },
        }
        for tick in ("0", "5")
    ]
    records.append(
        {
            "type": "evidence.updated",
            "payload": {
                "coverage": {
                    "clockDomain": "simulation-time",
                    "startTick": "0",
                    "endTick": "10",
                    "complete": True,
                }
            },
        }
    )
    return run, snapshot, records


def project(run, snapshot, records):
    return recorded_input(run, snapshot, records, "valid", snapshot_integrity="valid")


def test_known_codec_and_its_legacy_reader_omission_remain_comparable():
    run, snapshot, records = source_fixture()
    original = deepcopy((run, snapshot, records))
    healthy = project(run, snapshot, records)
    assert compare_runs(healthy, healthy)["compatible"] is True
    run.pop("journalId")
    run.pop("journalReader")
    legacy = project(run, snapshot, records)
    assert compare_runs(healthy, legacy)["compatible"] is True
    assert snapshot == original[1] and records == original[2]


def test_unknown_side_keeps_known_baseline_values_and_configuration_differences():
    run, snapshot, records = source_fixture()
    known = project(run, snapshot, records)
    run, snapshot, records = deepcopy((run, snapshot, records))
    run["providerId"] = snapshot["providerId"] = snapshot["providerIdentity"][
        "providerId"
    ] = "external-fixture"
    run["evidenceScope"] = snapshot["providerIdentity"]["evidenceScope"] = (
        "external_demo"
    )
    snapshot["configuration"]["gain"] = 2
    unknown = project(run, snapshot, records)
    report = compare_runs(known, unknown)
    assert not report["compatible"]
    assert (
        next(row for row in report["configuration"] if row["field"] == "parameters")[
            "status"
        ]
        == "different"
    )
    assert (
        report["left"]["evidenceIntegrity"]
        == report["right"]["evidenceIntegrity"]
        == "valid"
    )
    assert report["fields"][0]["left"]["summary"]["lastValue"] == 1.0
    assert report["fields"][0]["right"]["available"] is False
    assert "COMPARISON_EVIDENCE_UNSUPPORTED" in report["fields"][0]["reasons"]


def test_known_codec_incomplete_evidence_still_blocks_every_field():
    run, snapshot, records = source_fixture()
    run["evidence"] = "partial"
    side = project(run, snapshot, records)
    report = compare_runs(side, side)
    assert report["left"]["evidenceStatus"] == "partial"
    assert not report["compatible"]
    assert "EVIDENCE_INCOMPLETE" in report["diagnostics"]
    assert all("EVIDENCE_INCOMPLETE" in field["reasons"] for field in report["fields"])


@pytest.mark.parametrize(
    "case",
    [
        "external-source",
        "run-provider",
        "snapshot-provider",
        "frozen-provider",
        "run-scope",
        "frozen-scope",
        "reader",
        "journal-id",
        "snapshot-id",
        "project-id",
        "missing-context",
        "malformed-identity",
        "forged-declarations",
        "null-context",
        "empty-context",
        "numeric-context",
        "missing-digest",
    ],
)
def test_record_shape_and_integrity_cannot_admit_an_unknown_numeric_interpretation(
    case,
):
    run, snapshot, records = source_fixture()
    if case in ("external-source", "forged-declarations"):
        run["providerId"] = snapshot["providerId"] = snapshot["providerIdentity"][
            "providerId"
        ] = "external-fixture"
        run["evidenceScope"] = snapshot["providerIdentity"]["evidenceScope"] = (
            "external_demo"
        )
    elif case == "run-provider":
        run["providerId"] = "external-fixture"
    elif case == "snapshot-provider":
        snapshot["providerId"] = "external-fixture"
    elif case == "frozen-provider":
        snapshot["providerIdentity"]["providerId"] = "external-fixture"
    elif case == "run-scope":
        run["evidenceScope"] = "external_demo"
    elif case == "frozen-scope":
        snapshot["providerIdentity"]["evidenceScope"] = "external_demo"
    elif case == "reader":
        run["journalReader"] = "unreviewed-codec"
    elif case == "journal-id":
        run["journalId"] = "some-other-journal"
    elif case == "snapshot-id":
        run["snapshotId"] = "other-snapshot"
    elif case == "project-id":
        run["projectId"] = "other-project"
    elif case == "missing-context":
        run.pop("snapshotId")
    elif case == "malformed-identity":
        snapshot["providerIdentity"] = []
    elif case == "null-context":
        run["snapshotId"] = snapshot["snapshotId"] = None
    elif case == "empty-context":
        run["projectId"] = snapshot["projectId"] = ""
    elif case == "numeric-context":
        run["projectId"] = snapshot["projectId"] = 1
    elif case == "missing-digest":
        snapshot["snapshotDigest"] = None
    if case == "forged-declarations":
        run["comparisonSupported"] = True
        snapshot["comparisonContract"] = {
            "supported": True,
            "mappingId": "studio.reference",
        }
        records[0]["payload"]["comparisonSupported"] = True
    original = deepcopy((run, snapshot, records))
    side = project(run, snapshot, records)
    assert side["evidence"] == {"integrity": "valid", "status": "complete"}
    assert side["observations"] == []
    assert "COMPARISON_EVIDENCE_UNSUPPORTED" in side["projectionDiagnostics"]
    result = compare_runs(side, side)
    assert result["compatible"] is False
    assert "COMPARISON_EVIDENCE_UNSUPPORTED" in result["diagnostics"]
    assert (
        next(r for r in result["configuration"] if r["field"] == "parameters")["status"]
        == "same"
    )
    assert (run, snapshot, records) == original
