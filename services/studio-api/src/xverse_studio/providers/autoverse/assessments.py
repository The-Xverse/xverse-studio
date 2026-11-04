"""Pure mapping of original, explicitly covered bridge acknowledgement events."""
from copy import deepcopy
import hashlib
from pathlib import Path
import re

from xverse_studio.assertions.snapshot import source_definitions
from xverse_studio.blueprints.autoverse_assessments import CONTRACT, OBSERVER, FIELDS, NAMESPACE
from xverse_studio.deployments import compile_selection
from xverse_studio.xdl import XDLAdapter
from .controls import MAX_INPUT_SEQUENCE
from .input_loss import CLOCK, CODEC, CONTRACT as FAULT_CONTRACT

VERSIONS = {"0.3.0", "0.4.0"}
DESCRIPTOR = {"contractVersion": "1.0", "contractRef": CONTRACT, "observerRef": OBSERVER,
              "clockDomain": CLOCK, "clockCodec": CODEC, "tickUnit": "microsecond",
              "fields": {field: {"type": "boolean", "eventKind": kind} for field, kind in FIELDS.items()},
              "coverage": "recorded-events-only", "maxSamples": 64, "physicalEffects": False}


def admit_sources(actual, expected, documents):
    """Only the installed Profile/observer and bounded definitions vary from template."""
    from xverse_studio.blueprints.autoverse import resources
    scenario = actual["scenario.xdl.yaml"]
    payload = scenario.get("extensions", {}).get(NAMESPACE)
    if payload is None:
        return None, expected
    if scenario["extensions"]["io.xverse.studio.native-runtime"]["inputSurface"] != "studio-browser":
        raise ValueError("Assessment observer requires the admitted browser fault producer")
    selected = source_definitions(documents, XDLAdapter())
    if not selected or len(selected) > 32:
        raise ValueError("An admitted bounded assessment definition is required")
    for entry in selected:
        def signals(value):
            if isinstance(value, dict):
                if value.get("kind") == "signal" and (value.get("observerRef") != OBSERVER or value.get("field") not in FIELDS):
                    raise ValueError("Unsupported assessment field")
                for child in value.values():
                    signals(child)
            elif isinstance(value, list):
                for child in value:
                    signals(child)
        signals(entry["definition"]["expression"])
    expected = resources("studio-browser", assessments=True)
    expected["scenario.xdl.yaml"]["extensions"][NAMESPACE] = deepcopy(payload)
    return {"contractRef": CONTRACT, "observerRef": OBSERVER, "contractVersion": "1.0"}, expected


def context(provider, run, snapshot):
    frozen = snapshot.get("providerIdentity", {})
    if (run.get("providerId") != "autoverse.demo" or snapshot.get("providerId") != run.get("providerId")
            or frozen.get("providerId") != run.get("providerId") or frozen.get("providerVersion") not in VERSIONS
            or frozen.get("assessmentContract") != DESCRIPTOR or run.get("evidenceScope") != "external_demo"
            or run.get("journalReader") != "studio.hash-chain-v1"
            or run.get("journalId") != run["runId"] + ":provider-journal"):
        return None
    compiled = compile_selection(snapshot["documents"], snapshot["selection"], XDLAdapter())
    if (not compiled["valid"] or compiled["planDigest"] != snapshot["planDigest"]
            or compiled["semanticDigest"] != snapshot["semanticDigest"]):
        return None
    config = provider.configuration(snapshot["documents"], compiled)
    if config != snapshot.get("configuration") or not config or config.get("assessment", {}).get("contractRef") != CONTRACT:
        return None
    return {"contractVersion": "1.0", "mappingId": CONTRACT,
            "mappingDigest": "sha256:" + hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
            "sourceProviderId": run["providerId"], "sourceVersion": frozen["providerVersion"],
            "clockDomain": CLOCK, "clockCodec": CODEC, "tickUnit": "microsecond",
            "epoch": "actual-running-transition", "observerRef": OBSERVER,
            "coverageScope": "recorded-events-only"}


def tick(value):
    if not isinstance(value, str) or not re.fullmatch(r"0|[1-9][0-9]{0,31}", value):
        raise ValueError("Unsupported source tick")
    return int(value)


class CoverageMissing(ValueError):
    pass

def project(run, snapshot, records, integrity):
    """The caller has already checked the installed mapping context and journal."""
    samples = {field: [] for field in FIELDS}
    coverage = {"verified": False, "complete": False, "startTick": "0", "endTick": "0", "gaps": [{"reason": "No verified recorded-event cutoff"}]}
    valid = integrity == "valid" and len(records) <= 50000
    closed = [r for r in records if r["type"] == "assessment.coverage"]
    evidence_id = run["journalId"]
    try:
        if not closed:
            raise CoverageMissing()
        if len(closed) != 1:
            raise ValueError("Missing/ambiguous recorded-event coverage")
        cutoff = closed[0]
        payload = cutoff["payload"]
        end = tick(payload["endTick"])
        if (set(payload) != {"contractRef", "observerRef", "clockDomain", "clockCodec", "tickUnit", "coverageScope", "startTick", "endTick", "complete", "prefixDigest", "prefixSequence", "sampleCounts"}
                or not isinstance(payload["sampleCounts"], dict) or set(payload["sampleCounts"]) != set(FIELDS)
                or any(type(v) is not int or not 0 <= v <= 64 for v in payload["sampleCounts"].values())
                or payload["contractRef"] != CONTRACT or payload["observerRef"] != OBSERVER
                or payload["startTick"] != "0" or payload["clockDomain"] != CLOCK or payload["clockCodec"] != CODEC
                or payload["tickUnit"] != "microsecond" or payload["coverageScope"] != "recorded-events-only"
                or payload["prefixDigest"] != cutoff["previousDigest"]
                or payload["prefixSequence"] != str(int(cutoff["sequence"]) - 1)
                or payload["complete"] is not True or end < 1):
            raise ValueError("Unsupported coverage")
        def source(record):
            if (record.get("runId") != run["runId"] or record.get("snapshotId") != snapshot["snapshotId"]
                    or record.get("source") != {"providerId": run["providerId"], "version": snapshot["providerIdentity"]["providerVersion"]}
                    or record.get("evidenceRefs") != [evidence_id]
                    or record.get("sourceTime", {}).get("clockDomain") != CLOCK
                    or record["sourceTime"].get("resolution") != "microsecond"):
                raise ValueError("Foreign source")
            return tick(record["sourceTime"]["tick"])
        if source(cutoff) != end - 1:
            raise ValueError("Cutoff source mismatch")
        fault_ids = {item["faultId"] for item in snapshot["configuration"]["inputLoss"]["schedules"]}
        previous = -1
        for record in records:
            if not record["type"].startswith("fault."):
                continue
            if record["type"] not in {"fault.activation_requested", "fault.activation_observed", "fault.recovery_requested", "fault.recovery_observed", "fault.interrupted", "fault.not_activated", "fault.effect_unobserved", "fault.schedule_missed"}:
                raise ValueError("Unsupported fault record kind")
            p = record["payload"]
            position = source(record)
            if (position < previous or position >= end or int(record["sequence"]) >= int(cutoff["sequence"])
                    or position != tick(p["actualTick"]) or p["faultId"] not in fault_ids
                    or p["contractRef"] != FAULT_CONTRACT or p["clockCodec"] != CODEC
                    or p["effectScope"] != "driver-bridge-publication-lease" or p["vehicleEffect"] != "not_attested"):
                raise ValueError("Unsupported fault record")
            previous = position
            for field, kind in FIELDS.items():
                if record["type"] != kind:
                    continue
                if p.get("bridgeLeaseActive") is not (field == "recoveryObserved"):
                    raise ValueError("Unconfirmed lease acknowledgement")
                if not (type(p.get("lastDroppedSequence")) is int and 0 < p["lastDroppedSequence"] <= MAX_INPUT_SEQUENCE):
                    raise ValueError("Unconfirmed dropped-frame sequence")
                if field == "activationObserved" and not (type(p.get("suppressedFrames")) is int and p["suppressedFrames"] > 0):
                    raise ValueError("Unconfirmed suppression")
                if field == "recoveryObserved" and not (type(p.get("publicationSequence")) is int
                        and p["lastDroppedSequence"] < p["publicationSequence"] <= MAX_INPUT_SEQUENCE):
                    raise ValueError("Unconfirmed recovery publication")
                samples[field].append({"tick": str(position), "value": True, "sequence": int(record["sequence"])})
        if sum(map(len, samples.values())) > 64 or payload["sampleCounts"] != {k: len(v) for k, v in samples.items()}:
            raise ValueError("Event coverage count mismatch")
        if valid:
            coverage = {"verified": True, "complete": True, "startTick": "0", "endTick": str(end), "gaps": []}
    except CoverageMissing:
        pass
    except (ValueError, TypeError, KeyError, AttributeError):
        valid = False
    return [{"evidenceId": evidence_id, "digest": run.get("journalDigest"), "snapshotId": snapshot["snapshotId"],
             "observerRef": OBSERVER, "field": field, "schema": {"type": "boolean"}, "clockDomainRef": CLOCK,
             "integrity": integrity if valid else "invalid", "coverage": deepcopy(coverage), "samples": values}
            for field, values in samples.items()]
