from __future__ import annotations

import hashlib
import json
import math
import re
import time
from dataclasses import dataclass
from fractions import Fraction
from pathlib import Path
from typing import Any, Callable

EVALUATOR_VERSION = "1.0.0"
EVALUATOR_IMPLEMENTATION_DIGEST = "sha256:" + hashlib.sha256(Path(__file__).read_bytes()).hexdigest()


def evaluator_identity():
    return {"version": EVALUATOR_VERSION, "contractVersion": "1.0", "implementation": "io.xverse.studio.experiments.bounded-json-ast", "implementationDigest": EVALUATOR_IMPLEMENTATION_DIGEST}

LIMITS = {"maxNodes": 128, "maxDepth": 12, "maxSignals": 32, "maxMetricDependencies": 32, "maxSamples": 1_000_000, "maxBytes": 64 * 1024 * 1024}
_INT = re.compile(r"^-?(?:0|[1-9][0-9]*)$")


class EvaluationError(ValueError):
    """An invalid definition, unsupported operation, or exhausted job resource."""
    def __init__(self, code: str):
        self.code = code
        super().__init__(code)


class UnknownEvidence(Exception):
    def __init__(self, code: str):
        self.code = code


def _tick(value: Any) -> int:
    if not isinstance(value, str) or len(value) > 32 or not _INT.fullmatch(value):
        raise EvaluationError("INVALID_TICK")
    return int(value)


def _number(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value)


def _shape(value: Any, required: set[str], optional: set[str] = frozenset()) -> None:
    if not isinstance(value, dict) or not required <= value.keys() or value.keys() - required - optional:
        raise EvaluationError("INVALID_DEFINITION")


def _text(value: Any) -> bool:
    return isinstance(value, str) and 0 < len(value) <= 512


def _caps(overrides: dict | None) -> dict:
    if overrides is None:
        return dict(LIMITS)
    if not isinstance(overrides, dict) or overrides.keys() - LIMITS.keys():
        raise EvaluationError("INVALID_LIMITS")
    result = dict(LIMITS)
    for key, val in overrides.items():
        if not isinstance(val, int) or isinstance(val, bool) or not 0 < val <= LIMITS[key]:
            raise EvaluationError("INVALID_LIMITS")
        result[key] = val
    return result


def validate_definition(definition: dict, *, limits: dict | None = None) -> dict:
    caps = _caps(limits)
    _shape(definition, {"evaluationId", "version", "kind", "name", "systemRef", "scenarioRef", "expression", "window", "coveragePolicy"}, {"description", "traceability", "resultUnit", "maxUncertaintyTicks"})
    if definition["version"] != "1.0" or definition["kind"] not in {"metric", "assertion"} or definition["coveragePolicy"] != "complete":
        raise EvaluationError("UNSUPPORTED_DEFINITION_VERSION")
    if any(not _text(definition[k]) for k in ("evaluationId", "name", "systemRef", "scenarioRef")):
        raise EvaluationError("INVALID_DEFINITION")
    if definition["kind"] == "metric" and not _text(definition.get("resultUnit")):
        raise EvaluationError("RESULT_UNIT_REQUIRED")
    if definition["kind"] == "assertion" and "resultUnit" in definition:
        raise EvaluationError("INVALID_DEFINITION")
    window = definition["window"]
    _shape(window, {"clockDomainRef", "startTick", "endTick"})
    if not _text(window["clockDomainRef"]) or _tick(window["startTick"]) >= _tick(window["endTick"]):
        raise EvaluationError("INVALID_WINDOW")
    if "maxUncertaintyTicks" in definition and _tick(definition["maxUncertaintyTicks"]) < 0:
        raise EvaluationError("INVALID_UNCERTAINTY")
    nodes = 0
    signals: set[tuple] = set()
    metrics: set[str] = set()
    stack = [(definition["expression"], 1)]
    while stack:
        node, depth = stack.pop()
        nodes += 1
        if nodes > caps["maxNodes"] or depth > caps["maxDepth"]:
            raise EvaluationError("AST_LIMIT")
        if not isinstance(node, dict):
            raise EvaluationError("INVALID_EXPRESSION")
        kind = node.get("kind")
        children = []
        if kind == "literal":
            _shape(node, {"kind", "value"}, {"unit"})
            if isinstance(node["value"], bool):
                if "unit" in node:
                    raise EvaluationError("BOOLEAN_UNIT")
            elif not _number(node["value"]) or not _text(node.get("unit")):
                raise EvaluationError("INVALID_LITERAL")
        elif kind == "signal":
            _shape(node, {"kind", "observerRef", "field"})
            if not _text(node["observerRef"]) or not _text(node["field"]):
                raise EvaluationError("INVALID_SIGNAL")
            signals.add((node["observerRef"], node["field"]))
        elif kind == "metric":
            _shape(node, {"kind", "evaluationRef"})
            ref = node["evaluationRef"]
            _shape(ref, {"evaluationId", "version", "definitionDigest"})
            if any(not _text(v) for v in ref.values()):
                raise EvaluationError("UNPINNED_METRIC")
            if ref["evaluationId"] == definition["evaluationId"]:
                raise EvaluationError("METRIC_DEPENDENCY_CYCLE")
            metrics.add(ref["evaluationId"])
        elif kind == "convert":
            _shape(node, {"kind", "input", "conversionRef"})
            if not _text(node["conversionRef"]):
                raise EvaluationError("INVALID_CONVERSION")
            children = [node["input"]]
        elif kind == "compare":
            _shape(node, {"kind", "operator", "left", "right"}, {"tolerance"})
            if node["operator"] not in {"lt", "le", "gt", "ge", "eq", "ne"}:
                raise EvaluationError("UNKNOWN_OPERATOR")
            if "tolerance" in node:
                _shape(node["tolerance"], {"value", "unit"})
                if node["operator"] not in {"eq", "ne"} or not _number(node["tolerance"]["value"]) or node["tolerance"]["value"] < 0 or not _text(node["tolerance"]["unit"]):
                    raise EvaluationError("INVALID_TOLERANCE")
            children = [node["left"], node["right"]]
        elif kind == "boolean":
            _shape(node, {"kind", "operator", "inputs"})
            operands = node["inputs"]
            if node["operator"] not in {"and", "or", "not"} or not isinstance(operands, list) or len(operands) > caps["maxNodes"]:
                raise EvaluationError("UNKNOWN_OPERATOR")
            if len(operands) != 1 if node["operator"] == "not" else len(operands) < 2:
                raise EvaluationError("INVALID_ARITY")
            children = operands
        elif kind == "aggregate":
            _shape(node, {"kind", "operator", "input"})
            if node["operator"] not in {"min", "max", "mean", "last", "all", "any", "count"}:
                raise EvaluationError("UNKNOWN_OPERATOR")
            children = [node["input"]]
        else:
            raise EvaluationError("UNKNOWN_NODE")
        stack.extend((child, depth + 1) for child in children)
    if len(signals) > caps["maxSignals"] or len(metrics) > caps["maxMetricDependencies"]:
        raise EvaluationError("REFERENCE_LIMIT")
    return {"nodes": nodes, "signals": sorted(signals), "metricDependencies": sorted(metrics), "limits": caps}


@dataclass
class _Value:
    data: Any
    boolean: bool
    unit: str | None = None
    ticks: tuple | None = None
    clock: str | None = None


class _Job:
    def __init__(self, definition, evidence, units, conversions, metrics, snapshot_id, caps, budget_seconds, cancel):
        self.definition = definition
        self.evidence = evidence
        self.units = units
        self.conversions = conversions or {}
        self.metrics = metrics or {}
        self.snapshot_id = snapshot_id
        self.caps = caps
        self.deadline = time.monotonic() + max(0, budget_seconds)
        self.cancel = cancel
        self.window = definition["window"]
        self.start, self.end = _tick(self.window["startTick"]), _tick(self.window["endTick"])
        self.sample_count = 0
        self.byte_count = 0
        self.cache = {}
        self.digests = set()
        self.evidence_lookup = {}
        for record in evidence:
            self.check()
            if not isinstance(record, dict):
                raise UnknownEvidence("EVIDENCE_INVALID")
            samples = record.get("samples", [])
            if not isinstance(samples, list):
                raise UnknownEvidence("EVIDENCE_INVALID")
            self.sample_count += len(samples)
            if self.sample_count > caps["maxSamples"]:
                raise EvaluationError("SAMPLE_LIMIT")
            for chunk in json.JSONEncoder(allow_nan=True, separators=(",", ":"), ensure_ascii=False).iterencode(record):
                self.check()
                self.byte_count += len(chunk.encode())
                if self.byte_count > caps["maxBytes"]:
                    raise EvaluationError("INPUT_BYTE_LIMIT")
            key = record.get("observerRef"), record.get("field")
            if key in self.evidence_lookup:
                raise UnknownEvidence("AMBIGUOUS_EVIDENCE")
            self.evidence_lookup[key] = record
            if _text(record.get("digest")):
                self.digests.add(record["digest"])
        if len(self.metrics) > caps["maxMetricDependencies"]:
            raise EvaluationError("REFERENCE_LIMIT")
        self.check_metric_cycles()

    def check(self):
        if self.cancel is not None and self.cancel():
            raise EvaluationError("CANCELLED")
        if time.monotonic() >= self.deadline:
            raise EvaluationError("WALL_TIME_BUDGET")

    def check_metric_cycles(self):
        seen, active = set(), set()
        def visit(key, depth=0):
            if key in active:
                raise EvaluationError("METRIC_DEPENDENCY_CYCLE")
            if depth > self.caps["maxMetricDependencies"]:
                raise EvaluationError("REFERENCE_LIMIT")
            if key in seen:
                return
            active.add(key)
            value = self.metrics.get(key, {})
            deps = value.get("dependencyRefs", []) if isinstance(value, dict) else []
            if not isinstance(deps, list) or len(deps) > self.caps["maxMetricDependencies"]:
                raise EvaluationError("REFERENCE_LIMIT")
            for dep in deps:
                if not isinstance(dep, str):
                    raise EvaluationError("UNPINNED_METRIC")
                visit(dep, depth + 1)
            active.remove(key); seen.add(key)
        for key in self.metrics:
            visit(key)

    def unit(self, name):
        entry = self.units.get(name)
        if not isinstance(entry, dict) or not _text(entry.get("quantity")) or not _text(entry.get("definitionDigest")):
            raise EvaluationError("UNIT_UNADMITTED")
        return entry

    def align(self, a, b):
        if a.ticks is not None and b.ticks is not None:
            if a.clock != b.clock or a.ticks != b.ticks:
                raise UnknownEvidence("SERIES_MISALIGNED")
            return list(zip(a.data, b.data)), a.ticks, a.clock
        if a.ticks is not None:
            return [(v, b.data) for v in a.data], a.ticks, a.clock
        if b.ticks is not None:
            return [(a.data, v) for v in b.data], b.ticks, b.clock
        return [(a.data, b.data)], None, None

    def signal(self, node):
        key = node["observerRef"], node["field"]
        if key in self.cache:
            return self.cache[key]
        rec = self.evidence_lookup.get(key)
        if rec is None:
            raise UnknownEvidence("SIGNAL_UNAVAILABLE")
        if rec.get("integrity") != "valid" or not _text(rec.get("digest")):
            raise UnknownEvidence("EVIDENCE_INVALID")
        if self.snapshot_id is None or rec.get("snapshotId") != self.snapshot_id:
            raise UnknownEvidence("SNAPSHOT_MISMATCH")
        schema = rec.get("schema", {})
        boolean = schema.get("type") == "boolean"
        if schema.get("type") not in {"number", "boolean"}:
            raise UnknownEvidence("FIELD_UNAVAILABLE")
        unit = None if boolean else schema.get("unit")
        if not boolean:
            admitted = self.unit(unit)
            if schema.get("quantity") != admitted["quantity"] or schema.get("unitDefinitionDigest") != admitted["definitionDigest"]:
                raise UnknownEvidence("UNIT_IDENTITY_MISMATCH")
        mapping = None
        if rec.get("clockDomainRef") != self.window["clockDomainRef"]:
            mapping = rec.get("clockMapping")
            max_uncertainty = self.definition.get("maxUncertaintyTicks")
            if not isinstance(mapping, dict) or not mapping.get("admitted") or not _text(mapping.get("mappingId")) or not _text(mapping.get("digest")) or mapping.get("targetClockDomainRef") != self.window["clockDomainRef"] or max_uncertainty is None:
                raise UnknownEvidence("CLOCK_MAPPING_UNAVAILABLE")
            try:
                if _tick(mapping["uncertaintyTicks"]) < 0 or _tick(mapping["uncertaintyTicks"]) > _tick(max_uncertainty):
                    raise UnknownEvidence("CLOCK_UNCERTAINTY")
                offset = _tick(mapping["offsetTick"])
                numerator, denominator = mapping["numerator"], mapping["denominator"]
                if not isinstance(numerator, int) or not isinstance(denominator, int) or isinstance(numerator, bool) or isinstance(denominator, bool) or numerator <= 0 or denominator <= 0:
                    raise UnknownEvidence("CLOCK_MAPPING_INVALID")
            except (KeyError, EvaluationError):
                raise UnknownEvidence("CLOCK_MAPPING_INVALID") from None
        coverage = rec.get("coverage")
        if not isinstance(coverage, dict) or coverage.get("verified") is not True:
            raise UnknownEvidence("COVERAGE_UNPROVEN")
        if coverage.get("complete") is not True or coverage.get("gaps") != [] or rec.get("stale") is True:
            raise UnknownEvidence("COVERAGE_INCOMPLETE")
        try:
            covered_start, covered_end = _tick(coverage["startTick"]), _tick(coverage["endTick"])
            if mapping:
                covered_start = Fraction(covered_start * numerator, denominator) + offset
                covered_end = Fraction(covered_end * numerator, denominator) + offset
            if covered_start > self.start or covered_end < self.end:
                raise UnknownEvidence("COVERAGE_INCOMPLETE")
        except (KeyError, EvaluationError):
            raise UnknownEvidence("COVERAGE_UNPROVEN") from None
        ticks, values = [], []
        previous = None
        previous_sequence = None
        for item in rec["samples"]:
            self.check()
            if not isinstance(item, dict):
                raise UnknownEvidence("SAMPLE_INVALID")
            try:
                raw_tick = _tick(item["tick"])
            except (KeyError, EvaluationError):
                raise UnknownEvidence("SOURCE_TIME_UNAVAILABLE") from None
            tick = raw_tick
            if mapping:
                mapped = raw_tick * numerator
                if mapped % denominator:
                    raise UnknownEvidence("CLOCK_ALIGNMENT_UNPROVEN")
                tick = mapped // denominator + offset
            if previous is not None and tick < previous:
                raise UnknownEvidence("SOURCE_TIME_NON_MONOTONIC")
            val = item.get("value")
            if not (isinstance(val, bool) if boolean else _number(val)):
                raise UnknownEvidence("NON_FINITE_OR_INVALID_VALUE")
            sequence = item.get("sequence")
            if previous == tick:
                if sequence is None or previous_sequence is None or not isinstance(sequence, int) or sequence <= previous_sequence:
                    if self.start <= tick < self.end and values and val == values[-1] and sequence == previous_sequence:
                        continue
                    raise UnknownEvidence("DUPLICATE_TICK_AMBIGUOUS")
                if self.start <= tick < self.end and values:
                    values[-1] = val
            elif self.start <= tick < self.end:
                ticks.append(tick); values.append(val)
            previous, previous_sequence = tick, sequence
        if not values:
            raise UnknownEvidence("EMPTY_SERIES")
        result = _Value(values, boolean, unit, tuple(ticks), self.window["clockDomainRef"])
        self.cache[key] = result
        return result

    def node(self, node):
        self.check()
        kind = node["kind"]
        if kind == "literal":
            if isinstance(node["value"], bool):
                return _Value(node["value"], True)
            self.unit(node["unit"])
            return _Value(node["value"], False, node["unit"])
        if kind == "signal":
            return self.signal(node)
        if kind == "metric":
            ref = node["evaluationRef"]
            rec = self.metrics.get(ref["evaluationId"])
            if not isinstance(rec, dict) or any(rec.get(k) != v for k, v in ref.items()) or rec.get("snapshotId") != self.snapshot_id or set(rec.get("evidenceDigests", [])) != self.digests or rec.get("status") != "complete" or rec.get("coverage") != "complete" or rec.get("partial") is not False or rec.get("kind") != "metric" or not _number(rec.get("value")):
                raise UnknownEvidence("METRIC_UNAVAILABLE")
            self.unit(rec.get("unit"))
            return _Value(rec["value"], False, rec["unit"])
        if kind == "convert":
            value = self.node(node["input"])
            conversion = self.conversions.get(node["conversionRef"])
            if value.boolean or not isinstance(conversion, dict) or not _text(conversion.get("definitionDigest")) or conversion.get("fromUnit") != value.unit:
                raise EvaluationError("CONVERSION_UNADMITTED")
            dest = conversion.get("toUnit")
            if self.unit(value.unit)["quantity"] != self.unit(dest)["quantity"] or not _number(conversion.get("scale")) or not _number(conversion.get("offset", 0)) or conversion["scale"] == 0:
                raise EvaluationError("CONVERSION_INVALID")
            def conv(v):
                result = v * conversion["scale"] + conversion.get("offset", 0)
                if not _number(result):
                    raise UnknownEvidence("NON_FINITE_VALUE")
                return result
            return _Value([conv(v) for v in value.data] if value.ticks is not None else conv(value.data), False, dest, value.ticks, value.clock)
        if kind == "compare":
            a, b = self.node(node["left"]), self.node(node["right"])
            op = node["operator"]
            tolerance = node.get("tolerance")
            if a.boolean != b.boolean:
                raise EvaluationError("TYPE_MISMATCH")
            if a.boolean:
                if op not in {"eq", "ne"} or tolerance is not None:
                    raise EvaluationError("BOOLEAN_COMPARISON")
            else:
                if a.unit != b.unit or self.unit(a.unit) != self.unit(b.unit):
                    raise EvaluationError("UNIT_MISMATCH")
                if op in {"eq", "ne"} and (tolerance is None or tolerance["unit"] != a.unit):
                    raise EvaluationError("TOLERANCE_REQUIRED")
            pairs, ticks, clock = self.align(a, b)
            def compare(x, y):
                if op == "lt": return x < y
                if op == "le": return x <= y
                if op == "gt": return x > y
                if op == "ge": return x >= y
                equal = x == y if a.boolean else abs(x-y) <= tolerance["value"]
                return equal if op == "eq" else not equal
            values = [compare(x, y) for x, y in pairs]
            return _Value(values if ticks is not None else values[0], True, ticks=ticks, clock=clock)
        if kind == "boolean":
            values = [self.node(x) for x in node["inputs"]]
            if any(not x.boolean for x in values):
                raise EvaluationError("TYPE_MISMATCH")
            op = node["operator"]
            if op == "not":
                v = values[0]
                return _Value([not x for x in v.data] if v.ticks is not None else not v.data, True, ticks=v.ticks, clock=v.clock)
            result = values[0]
            for other in values[1:]:
                pairs, ticks, clock = self.align(result, other)
                computed = [(x and y) if op == "and" else (x or y) for x, y in pairs]
                result = _Value(computed if ticks is not None else computed[0], True, ticks=ticks, clock=clock)
            return result
        if kind == "aggregate":
            value = self.node(node["input"])
            op = node["operator"]
            if value.ticks is None:
                raise EvaluationError("SERIES_REQUIRED")
            if op == "count":
                self.unit("1")
                return _Value(len(value.data), False, "1")
            if op in {"all", "any"}:
                if not value.boolean: raise EvaluationError("TYPE_MISMATCH")
                return _Value(all(value.data) if op == "all" else any(value.data), True)
            if value.boolean: raise EvaluationError("TYPE_MISMATCH")
            if op == "min": result = min(value.data)
            elif op == "max": result = max(value.data)
            elif op == "last": result = value.data[-1]
            else: result = math.fsum(v / len(value.data) for v in value.data)
            if not _number(result): raise UnknownEvidence("NON_FINITE_VALUE")
            return _Value(result, False, value.unit)
        raise EvaluationError("UNKNOWN_NODE")


def evaluate(definition: dict, evidence: list[dict], *, units: dict | None = None, conversions: dict | None = None, metrics: dict | None = None, profile_admitted: bool = False, snapshot_id: str | None = None, budget_seconds: float = 2.0, cancel: Callable[[], bool] | None = None, limits: dict | None = None) -> dict:
    """Evaluate a snapshot-bound declaration; return separate execution/verdict states.

    `profile_admitted` must be established by the XDL adapter, never browser input.
    Unit/conversion identities must come from the same pinned admitted profile set.
    Evidence is an exact, integrity-checked, bounded canonical-reader projection.
    """
    identity = evaluator_identity()
    result = {"status": "unavailable", "verdict": None, "value": None, "unit": None, "coverage": "incomplete", "partial": False, "reasons": [], "evaluatorIdentity": identity, "snapshotId": snapshot_id, "evidenceDigests": []}
    if not profile_admitted:
        result["reasons"] = ["PROFILE_NOT_ADMITTED"]
        return result
    try:
        info = validate_definition(definition, limits=limits)
        encoded = json.dumps(definition, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False).encode()
        if len(encoded) > info["limits"]["maxBytes"]:
            raise EvaluationError("INPUT_BYTE_LIMIT")
        result.update(definitionDigest="sha256:" + hashlib.sha256(encoded).hexdigest(), evaluationId=definition["evaluationId"], version=definition["version"], kind=definition["kind"])
        job = _Job(definition, evidence, units or {}, conversions, metrics, snapshot_id, info["limits"], budget_seconds, cancel)
        result["evidenceDigests"] = sorted(job.digests)
        value = job.node(definition["expression"])
        job.check()
        if value.ticks is not None or (definition["kind"] == "assertion" and not value.boolean) or (definition["kind"] == "metric" and (value.boolean or value.unit != definition["resultUnit"])):
            raise EvaluationError("ROOT_TYPE_MISMATCH")
        result.update(status="complete", coverage="complete", verdict=("pass" if value.data else "fail") if definition["kind"] == "assertion" else None, value=value.data, unit=value.unit)
    except UnknownEvidence as exc:
        result.update(status="complete", verdict="indeterminate" if isinstance(definition, dict) and definition.get("kind") == "assertion" else None, coverage="invalid" if exc.code == "EVIDENCE_INVALID" else "incomplete", reasons=[exc.code])
    except EvaluationError as exc:
        result.update(status="error", verdict=None, reasons=[exc.code])
    except (ValueError, TypeError, KeyError, OverflowError, RecursionError):
        result.update(status="error", verdict=None, reasons=["INVALID_DEFINITION_OR_INPUT"])
    return result


def aggregate_verdict(required_assertions: list[dict]) -> str | None:
    if not required_assertions:
        return None
    if any(r.get("status") == "complete" and r.get("verdict") == "fail" for r in required_assertions):
        return "fail"
    if all(r.get("status") == "complete" and r.get("verdict") == "pass" for r in required_assertions):
        return "pass"
    return "indeterminate"
