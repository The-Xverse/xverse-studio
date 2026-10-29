"""Bounded summaries of original canonical observations; no resampling or evaluator."""
from __future__ import annotations

import math
import re

from xverse_studio.assertions import UNIT_DEFINITIONS

MAX_FIELDS = 32
MAX_RECORDS = 100000


class ComparisonError(ValueError):
    def __init__(self, code):
        self.code = code
        super().__init__(code)


def text(value):
    return isinstance(value, str) and 0 < len(value) <= 512


def tick(value):
    # Tick identity remains exact across languages, including signed source epochs.
    if isinstance(value, str) and len(value) <= 32 and re.fullmatch(r'-?(?:0|[1-9][0-9]*)', value):
        return int(value)
    return None


def number(value):
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return False
    # Do not round exact JSON integers when the browser cannot represent them.
    if isinstance(value, int) and abs(value) > 9007199254740991:
        return False
    try:
        return math.isfinite(value)
    except OverflowError:
        return False


def window(coverage):
    if not isinstance(coverage, dict):
        return None
    start, end = (tick(coverage.get(k)) for k in ('startTick', 'endTick'))
    return (start, end) if start is not None and end is not None and start <= end else None


def recorded_input(run, snapshot, records, integrity, *, snapshot_integrity='unknown'):
    """Caller verifies the protected snapshot; journal reader supplies its own verdict."""
    if not isinstance(records, list) or len(records) > MAX_RECORDS:
        raise ComparisonError('COMPARISON_LIMIT')
    effective = bool(snapshot.get('planDigest') and snapshot.get('semanticDigest')) and (
        run.get('effectivePlanDigest') == snapshot.get('planDigest')
        and run.get('effectiveSemanticDigest') == snapshot.get('semanticDigest')
        and run.get('providerId') == snapshot.get('providerId')
    )
    plan = snapshot.get('plan')
    declarations = plan.get('observers') if isinstance(plan, dict) else None
    declarations = declarations if isinstance(declarations, list) and len(declarations) <= MAX_FIELDS else []
    groups = {}
    coverage = None
    gap_count = 0
    payload_invalid = False
    for record in records:
        payload = record.get('payload')
        if not isinstance(payload, dict):
            payload_invalid = True
            continue
        if record.get('type') == 'evidence.updated' and isinstance(payload.get('coverage'), dict):
            coverage = payload['coverage']
        if record.get('type') == 'observation.gap':
            gap_count += 1
        if record.get('type') != 'observation.available':
            continue
        values, units = payload.get('values'), payload.get('units')
        if not isinstance(values, dict) or not isinstance(units, dict) or len(values) > MAX_FIELDS:
            payload_invalid = True
            continue
        source = record.get('sourceTime')
        source = source if isinstance(source, dict) else {}
        source_tick = tick(source.get('tick'))
        observer = payload.get('observerRef')
        observer = observer if text(observer) else None
        for field, value in values.items():
            field = field if text(field) else None
            key = observer, field
            unit, clock = units.get(field), source.get('clockDomain')
            unit = unit if text(unit) else None
            clock = clock if text(clock) else None
            resolution = source.get('resolution')
            resolution = resolution if text(resolution) else None
            uncertainty = source.get('uncertainty')
            uncertainty = uncertainty if number(uncertainty) and uncertainty >= 0 else None
            if key not in groups:
                if len(groups) >= MAX_FIELDS:
                    raise ComparisonError('COMPARISON_LIMIT')
                definition = UNIT_DEFINITIONS.get(unit, {})
                groups[key] = {
                    'observerRef': observer, 'field': field, 'unit': unit,
                    'quantity': definition.get('quantity'), 'unitDefinitionDigest': definition.get('definitionDigest'),
                    'clockDomainRef': clock, 'sourceTime': {'resolution': resolution, 'uncertainty': uncertainty},
                    'metadataConsistent': True, 'identityVerified': True, 'samplesValid': True,
                    'summary': {'status': 'available', 'sampleCount': 0, 'firstTick': None, 'lastTick': None,
                                'minimum': None, 'maximum': None, 'lastValue': None},
                }
            group = groups[key]
            matches = [d for d in declarations if isinstance(d, dict) and d.get('observerId') == observer]
            policy = matches[0].get('payloadPolicy') if len(matches) == 1 else None
            if (observer is None or len(matches) != 1 or not isinstance(policy, dict)
                    or not text(policy.get('unitSemantics')) or policy['unitSemantics'] != unit
                    or not text(matches[0].get('timeDomainId')) or matches[0]['timeDomainId'] != clock):
                group['identityVerified'] = False
            if group['unit'] != unit or group['clockDomainRef'] != clock or group['sourceTime'] != {'resolution': resolution, 'uncertainty': uncertainty}:
                group['metadataConsistent'] = False
            summary = group['summary']
            previous = tick(summary['lastTick'])
            if not number(value) or source_tick is None or previous is not None and source_tick < previous:
                group['samplesValid'] = False
            summary['sampleCount'] += 1
            if source_tick is not None:
                if summary['firstTick'] is None:
                    summary['firstTick'] = str(source_tick)
                summary['lastTick'] = str(source_tick)
            if number(value):
                summary['minimum'] = value if summary['minimum'] is None else min(summary['minimum'], value)
                summary['maximum'] = value if summary['maximum'] is None else max(summary['maximum'], value)
                summary['lastValue'] = value
    for group in groups.values():
        original = coverage or {}
        complete = (integrity == 'valid' and effective and run.get('state') == 'stopped'
                    and original.get('complete') is True and gap_count == 0 and not payload_invalid
                    and original.get('clockDomain') == group['clockDomainRef'])
        group['coverage'] = {
            'verified': integrity == 'valid' and coverage is not None,
            'complete': complete, 'startTick': original.get('startTick'), 'endTick': original.get('endTick'),
            'gaps': [] if complete else [{'reason': 'Canonical coverage is incomplete, gapped or unavailable.'}],
            'gapCount': gap_count,
        }
        if (integrity != 'valid' or not group.pop('samplesValid') or not group['metadataConsistent']
                or not group['summary']['sampleCount'] or payload_invalid):
            group['summary'].update(status='unavailable', minimum=None, maximum=None, lastValue=None)
    return {
        'runId': run.get('runId'), 'snapshot': snapshot, 'snapshotIntegrity': snapshot_integrity,
        'state': run.get('state'), 'cleanup': run.get('cleanup'), 'effectiveInputsMatch': effective,
        'evidence': {'integrity': integrity, 'status': run.get('evidence')},
        'projectionDiagnostics': ['OBSERVATION_PAYLOAD_UNAVAILABLE'] if payload_invalid else [],
        'observations': list(groups.values()),
    }
