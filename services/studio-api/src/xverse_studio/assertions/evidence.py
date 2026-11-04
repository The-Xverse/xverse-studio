"""Explicit evidence-reader admission for the installed bounded evaluator.

Canonical integrity alone does not admit field, unit, clock or coverage semantics.
This module grants no provider operation and never interprets project commands.
"""
from copy import deepcopy
import json
import re
from xverse_studio.assertions.evaluator import EvaluationError

UNSUPPORTED = "EVALUATION_EVIDENCE_UNSUPPORTED"
REFERENCE_READER = "studio.reference.hash-chain-v1"


def evidence_support(run: dict, snapshot: dict, provider=None) -> dict:
    """Caller supplies protected run/snapshot records, never browser declarations.

    The owned reference decoder and explicit installed provider mappings have
    separate admission. Sharing an envelope does not admit field, unit, clock or
    coverage semantics. Historical reference runs omitted the redundant
    reader/journal-ID metadata.
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
    mapping = None
    if (not supported and provider is not None and callable(getattr(provider, "assessment_context", None))
            and callable(getattr(provider, "assessment_projection", None))
            and run.get("providerId") == snapshot.get("providerId") == identity.get("providerId")
            and run.get("evidenceScope") == identity.get("evidenceScope")
            and run.get("snapshotId") == snapshot.get("snapshotId")
            and run.get("projectId") == snapshot.get("projectId")
            and isinstance(reader, str) and isinstance(evidence_id, str)):
        try:
            candidate = provider.assessment_context(deepcopy(run), deepcopy(snapshot))
            if (isinstance(candidate, dict) and len(candidate) <= 16
                    and len(json.dumps(candidate, allow_nan=False).encode()) <= 8192
                    and candidate.get("contractVersion") == "1.0"
                    and candidate.get("sourceProviderId") == run["providerId"]
                    and candidate.get("sourceVersion") == identity.get("providerVersion")
                    and all(isinstance(candidate.get(k), str) and 0 < len(candidate[k]) <= 512
                            for k in ["mappingId", "mappingDigest", "clockDomain", "clockCodec", "tickUnit", "epoch", "observerRef", "coverageScope"])
                    and re.fullmatch(r"sha256:[a-f0-9]{64}", candidate["mappingDigest"])):
                mapping, supported = candidate, True
        except Exception:
            pass  # Installed callback errors confer no mapping or private diagnostics.
    return {"formatVersion": "1.0", "runId": run["runId"], "snapshotId": run["snapshotId"],
            "projectId": snapshot["projectId"], "snapshotDigest": snapshot["snapshotDigest"],
            "providerId": run.get("providerId"), "evidenceScope": run.get("evidenceScope"),
            "evidenceId": evidence_id if isinstance(evidence_id, str) and len(evidence_id) <= 512 else None,
            "evidenceReader": reader if isinstance(reader, str) and len(reader) <= 128 else None,
            "status": "supported" if supported else "unsupported",
            "reasons": [] if supported else [UNSUPPORTED], **({"mapping": mapping} if mapping else {})}


def require_evidence_support(run: dict, snapshot: dict) -> dict:
    result = evidence_support(run, snapshot)
    if result["status"] != "supported":
        raise EvaluationError(UNSUPPORTED)
    return result
