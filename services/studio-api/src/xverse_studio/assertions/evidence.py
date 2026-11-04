"""Explicit evidence-reader admission for the installed bounded evaluator.

Canonical integrity alone does not admit field, unit, clock or coverage semantics.
This module grants no provider operation and never interprets project commands.
"""
from xverse_studio.assertions.evaluator import EvaluationError

UNSUPPORTED = "EVALUATION_EVIDENCE_UNSUPPORTED"
REFERENCE_READER = "studio.reference.hash-chain-v1"


def evidence_support(run: dict, snapshot: dict) -> dict:
    """Caller supplies protected run/snapshot records, never browser declarations.

Only the existing owned reference measurement decoder is installed. Other readers
need a separately reviewed mapping, even if they share a hash-chain envelope.
Historical reference runs omitted the redundant reader/journal-ID metadata.
"""
    identity = snapshot.get("providerIdentity", {})
    if not isinstance(identity, dict):
        identity = {}
    reference = (run.get("providerId") == snapshot.get("providerId") == "studio.reference"
                 and identity.get("providerId") == "studio.reference"
                 and run.get("evidenceScope") == identity.get("evidenceScope") == "owned_reference")
    evidence_id = run.get("journalId", run["runId"] + ":reference-journal" if reference else None)
    reader = run.get("journalReader", REFERENCE_READER if reference else None)
    supported = (reference and reader == REFERENCE_READER
                 and evidence_id == run["runId"] + ":reference-journal"
                 and run.get("snapshotId") == snapshot.get("snapshotId")
                 and run.get("projectId") == snapshot.get("projectId"))
    return {"formatVersion": "1.0", "runId": run["runId"], "snapshotId": run["snapshotId"],
            "projectId": snapshot["projectId"], "snapshotDigest": snapshot["snapshotDigest"],
            "providerId": run.get("providerId"), "evidenceScope": run.get("evidenceScope"),
            "evidenceId": evidence_id if isinstance(evidence_id, str) and len(evidence_id) <= 512 else None,
            "evidenceReader": reader if isinstance(reader, str) and len(reader) <= 128 else None,
            "status": "supported" if supported else "unsupported",
            "reasons": [] if supported else [UNSUPPORTED]}


def require_evidence_support(run: dict, snapshot: dict) -> dict:
    result = evidence_support(run, snapshot)
    if result["status"] != "supported":
        raise EvaluationError(UNSUPPORTED)
    return result
