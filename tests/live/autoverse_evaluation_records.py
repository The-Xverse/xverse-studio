"""Verify protected source records while allowing their truthful derived index."""
from copy import deepcopy


def verify_protected_records(before, after, run_id, snapshot_id):
    """Only latest-evaluation IDs and the monotonic observation version may vary.

    Lifecycle, verdicts, source evidence and old evaluation/operation receipts
    remain exact. The run's derived summary must reference the actual latest
    immutable row for the same frozen definition, not a fabricated result.
    """
    derived_version_delta = 0
    for key, old in before.items():
        current = after.get(key)
        assert current is not None
        if key != ("run", run_id):
            assert current == old, key
            continue
        assert current["snapshotId"] == snapshot_id
        fields = {"observationVersion", "evaluationSummary"}
        assert {k:v for k,v in current.items() if k not in fields} == {k:v for k,v in old.items() if k not in fields}
        start, end = old.get("observationVersion", 0), current.get("observationVersion", 0)
        assert type(end) is int and start <= end <= 2**53 - 1
        derived_version_delta = end - start
        summaries = [deepcopy(old["evaluationSummary"]), deepcopy(current["evaluationSummary"])]
        for summary in summaries:
            for group in ("definitions", "metricJobs"):
                for entry in summary[group]:
                    entry.pop("evaluationId", None)
        assert summaries[0] == summaries[1]
        for group in ("definitions", "metricJobs"):
            for entry in current["evaluationSummary"][group]:
                rows = [row for (kind, _), row in after.items() if kind == "evaluation"
                        and row["runId"] == run_id and row["snapshotId"] == snapshot_id
                        and row["definitionRef"] == entry["definitionRef"] and row["definitionDigest"] == entry["definitionDigest"]]
                latest = max(rows, key=lambda row: (row["createdAt"], row["evaluationId"]))
                assert entry["evaluationId"] == latest["evaluationId"]
    return {"oldRecordsAndLifecyclePreserved": True, "derivedSummaryLatestIdsVerified": True,
            "derivedObservationVersionDelta": derived_version_delta}
