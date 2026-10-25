"""Bounded read projections. Selection never changes canonical evidence or coverage."""

import base64
from datetime import datetime, timedelta, timezone
from decimal import Decimal, InvalidOperation
import json
import math
import re

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from xverse_studio.storage.core import Problem, canonical, digest

MAX_IDENTIFIER = 512
MAX_TICK_CHARACTERS = 32
MAX_FACETS = 64
MAX_GAPS = 128
TICK_PATTERN = re.compile(r"-?(?:0|[1-9][0-9]*)\Z", re.ASCII)
UTC_PATTERN = re.compile(
    r"[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}"
    r"(?:\.[0-9]{1,6})?(?:Z|[+-][0-9]{2}:[0-9]{2})\Z"
)
EPOCH = datetime(1970, 1, 1, tzinfo=timezone.utc)


def invalid(message, code="EVIDENCE_FILTER_INVALID"):
    raise Problem(code, message)


def parse_tick(value):
    if (
        not isinstance(value, str)
        or len(value) > MAX_TICK_CHARACTERS
        or not TICK_PATTERN.fullmatch(value)
    ):
        invalid(
            "Source ticks must be canonical signed decimal integer strings of at most 32 characters."
        )
    return int(value)


def _utc(value):
    if (
        not isinstance(value, str)
        or len(value) > 64
        or not UTC_PATTERN.fullmatch(value)
    ):
        invalid(
            "Receipt bounds must be RFC3339 timestamps with an explicit timezone and at most six fractional digits."
        )
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(
            timezone.utc
        )
        delta = parsed - EPOCH
        seconds = (
            Decimal(delta.days * 86400 + delta.seconds)
            + Decimal(delta.microseconds) / 1000000
        )
        return seconds, parsed.isoformat(timespec="microseconds").replace("+00:00", "Z")
    except (ValueError, OverflowError):
        invalid("The receipt timestamp is outside the supported RFC3339 calendar.")


def receipt_time(record):
    """Decode only self-described text or the admitted reference-v1 seconds codec."""
    raw = record.get("recordedAt")
    if isinstance(raw, str):
        try:
            seconds, formatted = _utc(raw)
            return seconds, formatted, "rfc3339"
        except Problem:
            return None, None, "unavailable"
    source = record.get("source")
    if (
        isinstance(source, dict)
        and source.get("providerId") == "studio.reference"
        and source.get("version") == "1.0.0"
        and record.get("schemaVersion") == "1.0"
        and isinstance(raw, (int, float))
        and not isinstance(raw, bool)
    ):
        try:
            if isinstance(raw, float) and not math.isfinite(raw):
                return None, None, "unavailable"
            seconds = Decimal(str(raw))
            # Human UTC presentation truncates sub-microsecond encoded fractions;
            # filtering uses the original decimal seconds, never this projection.
            whole = int(seconds)
            parsed = EPOCH + timedelta(
                seconds=whole, microseconds=int((seconds - whole) * 1000000)
            )
            return (
                seconds,
                parsed.isoformat(timespec="microseconds").replace("+00:00", "Z"),
                "unix_seconds_reference_v1",
            )
        except (ValueError, InvalidOperation, OverflowError):
            pass
    return None, None, "unavailable"


class EvidenceQuery(BaseModel):
    model_config = ConfigDict(extra="forbid", allow_inf_nan=False)
    cursor: str | None = Field(default=None, max_length=2048)
    limit: int = Field(default=200, ge=1, le=200)
    elementRef: str | None = Field(
        default=None, min_length=1, max_length=MAX_IDENTIFIER
    )
    sourceProviderId: str | None = Field(
        default=None, min_length=1, max_length=MAX_IDENTIFIER
    )
    observerRef: str | None = Field(
        default=None, min_length=1, max_length=MAX_IDENTIFIER
    )
    clockDomain: str | None = Field(
        default=None, min_length=1, max_length=MAX_IDENTIFIER
    )
    startTick: str | None = Field(default=None, max_length=MAX_TICK_CHARACTERS)
    endTick: str | None = Field(default=None, max_length=MAX_TICK_CHARACTERS)
    recordedFrom: str | None = Field(default=None, max_length=64)
    recordedUntil: str | None = Field(default=None, max_length=64)

    @field_validator("startTick", "endTick")
    @classmethod
    def exact_ticks(cls, value):
        if value is not None:
            parse_tick(value)
        return value

    @model_validator(mode="after")
    def intervals(self):
        if (
            self.startTick is not None
            and self.endTick is not None
            and parse_tick(self.startTick) >= parse_tick(self.endTick)
        ):
            invalid("The source interval must have startTick < endTick ([start,end)).")
        lower = _utc(self.recordedFrom)[0] if self.recordedFrom is not None else None
        upper = _utc(self.recordedUntil)[0] if self.recordedUntil is not None else None
        if lower is not None and upper is not None and lower >= upper:
            invalid(
                "The receipt interval must have recordedFrom < recordedUntil ([from,until))."
            )
        if (lower is not None or upper is not None) and (
            self.startTick is not None or self.endTick is not None
        ):
            invalid("Choose either a source-clock interval or a receipt-time interval.")
        return self


class HistoryQuery(EvidenceQuery):
    type: str | None = Field(default=None, min_length=1, max_length=MAX_IDENTIFIER)
    severity: str | None = Field(default=None, min_length=1, max_length=MAX_IDENTIFIER)


class ObservationQuery(EvidenceQuery):
    field: str | None = Field(default=None, min_length=1, max_length=MAX_IDENTIFIER)


def _source_time(record):
    original = record.get("sourceTime")
    if original is None:
        return None, None, "missing"
    if not isinstance(original, dict):
        return None, None, "malformed"
    tick, clock = original.get("tick"), original.get("clockDomain")
    if tick is None:
        return None, clock if isinstance(clock, str) else None, "missing"
    try:
        parsed = parse_tick(tick)
    except Problem:
        return None, clock if isinstance(clock, str) else None, "malformed"
    if not isinstance(clock, str) or not 0 < len(clock) <= MAX_IDENTIFIER:
        return parsed, None, "malformed"
    return parsed, clock, "known"


def _facets(records):
    values = {
        key: set()
        for key in (
            "sourceProviderIds",
            "observerRefs",
            "fields",
            "elementRefs",
            "clockDomains",
        )
    }
    complete = True

    def add(key, value):
        nonlocal complete
        if value is None:
            return
        if not isinstance(value, str) or not 0 < len(value) <= MAX_IDENTIFIER:
            complete = False
            return
        if value in values[key]:
            return
        if len(values[key]) >= MAX_FACETS:
            complete = False
        else:
            values[key].add(value)

    for record in records:
        source, payload = record.get("source"), record.get("payload")
        add(
            "sourceProviderIds",
            source.get("providerId") if isinstance(source, dict) else None,
        )
        if isinstance(payload, dict):
            add("observerRefs", payload.get("observerRef"))
            if record.get("type") == "observation.available" and isinstance(
                payload.get("values"), dict
            ):
                for field in payload["values"]:
                    add("fields", field)
        for ref in (
            record.get("elementRefs", [])
            if isinstance(record.get("elementRefs"), list)
            else []
        ):
            add("elementRefs", ref)
        original = record.get("sourceTime")
        add(
            "clockDomains",
            original.get("clockDomain") if isinstance(original, dict) else None,
        )
    return {key: sorted(items) for key, items in values.items()}, complete


def _offset(query, run_id, kind, filters):
    context = digest({"runId": run_id, "route": kind, "filter": filters})
    if query.cursor is None:
        return 0, context
    legacy = kind == "history" and not set(filters) - {"type", "severity", "elementRef"}
    if legacy and re.fullmatch(r"[0-9]{1,6}", query.cursor):
        offset = int(query.cursor)
        if offset <= 100000:
            return offset, context
    try:
        if not query.cursor.startswith("eq1."):
            raise ValueError()
        encoded = query.cursor[4:]
        data = json.loads(
            base64.b64decode(
                encoded + "=" * (-len(encoded) % 4), altchars=b"-_", validate=True
            )
        )
        if (
            set(data) != {"context", "offset"}
            or data["context"] != context
            or type(data["offset"]) is not int
            or not 0 <= data["offset"] <= 100000
        ):
            raise ValueError()
        return data["offset"], context
    except (ValueError, TypeError, KeyError, UnicodeError):
        invalid(
            "The evidence cursor belongs to another run, route or selection, or is malformed.",
            "CURSOR_INVALID",
        )


def _cursor(offset, context):
    raw = canonical({"context": context, "offset": offset}).encode()
    return "eq1." + base64.urlsafe_b64encode(raw).decode().rstrip("=")


def project_evidence(
    records,
    integrity,
    query,
    run_id,
    kind="history",
    *,
    evidence_scope="unverified_recorded",
):
    """Project immutable records in their original order, filtering before paging."""
    filters = query.model_dump(exclude_none=True, exclude={"cursor", "limit"})
    facets, facets_complete = _facets(records)
    source_window = query.startTick is not None or query.endTick is not None
    if source_window and query.clockDomain is None:
        observation_clocks = set()
        if kind == "observations":
            for record in records:
                if record.get("type") == "observation.available":
                    _, domain, status = _source_time(record)
                    if status == "known":
                        observation_clocks.add(domain)
                    if len(observation_clocks) > 1:
                        break
        if len(observation_clocks) == 1:
            filters["clockDomain"] = next(iter(observation_clocks))
        else:
            invalid(
                "Select the original clockDomain for this source-time interval.",
                "CLOCK_SELECTION_REQUIRED",
            )
    clock = filters.get("clockDomain")
    start = parse_tick(query.startTick) if query.startTick is not None else None
    end = parse_tick(query.endTick) if query.endTick is not None else None
    lower = _utc(query.recordedFrom)[0] if query.recordedFrom is not None else None
    upper = _utc(query.recordedUntil)[0] if query.recordedUntil is not None else None
    offset, context = _offset(query, run_id, kind, filters)
    selected, candidate_count = [], 0
    quality = {
        key: 0
        for key in (
            "missingSourceTime",
            "malformedSourceTime",
            "otherClock",
            "missingReceiptTime",
            "unsupportedReceiptEncoding",
        )
    }
    gaps = []
    gap_count = 0
    for record in records:
        payload = record.get("payload")
        payload = payload if isinstance(payload, dict) else {}
        source = record.get("source")
        source = source if isinstance(source, dict) else {}
        if record.get("type") == "observation.gap":
            gap_count += 1
            if len(gaps) < MAX_GAPS:
                gaps.append(
                    {
                        key: record.get(key)
                        for key in ("eventId", "sourceTime", "elementRefs", "payload")
                    }
                )
        if kind == "observations" and record.get("type") != "observation.available":
            continue
        if filters.get("type") and filters["type"] != record.get("type"):
            continue
        if filters.get("severity") and filters["severity"] != payload.get("severity"):
            continue
        if query.elementRef and query.elementRef not in (
            record.get("elementRefs") or []
        ):
            continue
        if query.sourceProviderId and query.sourceProviderId != source.get(
            "providerId"
        ):
            continue
        if query.observerRef and query.observerRef != payload.get("observerRef"):
            continue
        values = payload.get("values")
        if kind == "observations" and not isinstance(values, dict):
            continue
        if filters.get("field") and filters["field"] not in values:
            continue
        candidate_count += 1
        tick, domain, time_status = _source_time(record)
        quality["missingSourceTime"] += time_status == "missing"
        quality["malformedSourceTime"] += time_status == "malformed"
        seconds, _, encoding = receipt_time(record)
        quality["missingReceiptTime"] += record.get("recordedAt") is None
        quality["unsupportedReceiptEncoding"] += (
            record.get("recordedAt") is not None and encoding == "unavailable"
        )
        if clock and domain != clock:
            quality["otherClock"] += 1
            continue
        if source_window and (
            time_status != "known"
            or start is not None
            and tick < start
            or end is not None
            and tick >= end
        ):
            continue
        if (lower is not None or upper is not None) and (
            seconds is None
            or lower is not None
            and seconds < lower
            or upper is not None
            and seconds >= upper
        ):
            continue
        selected.append(record)
    page = selected[offset : offset + query.limit]
    items, presentation = [], {}
    for record in page:
        tick, _, status = _source_time(record)
        _, utc, encoding = receipt_time(record)
        presentation[record["eventId"]] = {
            "recordedAtUtc": utc,
            "receiptEncoding": encoding,
            "receiptDisplayResolution": "microsecond" if utc else None,
            "sourceTimeStatus": status,
        }
        if kind == "history":
            items.append(record)
        else:
            payload = record["payload"]
            field = filters.get("field")
            items.append(
                {
                    "eventId": record["eventId"],
                    "observerRef": payload.get("observerRef"),
                    "sourceTime": record.get("sourceTime"),
                    "source": record.get("source"),
                    "recordedAt": record.get("recordedAt"),
                    "tick": record["sourceTime"]["tick"] if tick is not None else None,
                    "values": payload["values"]
                    if field is None
                    else {field: payload["values"][field]},
                    "units": payload.get("units", {}),
                    "elementRefs": record.get("elementRefs", []),
                }
            )
    if integrity != "valid":
        if len(gaps) == MAX_GAPS:
            gaps.pop()
        gaps.append(
            {
                "reason": "Canonical coverage is not established by this reader integrity verdict.",
                "integrity": integrity,
            }
        )
    result = {
        "projectionVersion": "1.0",
        "evidenceScope": evidence_scope,
        "items": items,
        "nextCursor": _cursor(offset + len(page), context)
        if offset + len(page) < len(selected)
        else None,
        "integrity": integrity,
        "effectiveFilter": filters,
        "counts": {
            "totalRecords": len(records),
            "candidateRecords": candidate_count,
            "matchedRecords": len(selected),
            "returnedRecords": len(page),
            "omittedRecords": len(selected) - len(page),
        },
        "quality": quality,
        "facets": facets,
        "facetsComplete": facets_complete,
        "presentation": presentation,
        "gaps": gaps,
        "gapCount": gap_count,
        "gapsComplete": gap_count <= MAX_GAPS - (integrity != "valid"),
        "reduction": {
            "method": "page",
            "canonical": False,
            "pageStart": offset,
            "pageSize": query.limit,
        },
    }
    if kind == "observations":
        domains = {
            item["sourceTime"].get("clockDomain")
            for item in items
            if isinstance(item.get("sourceTime"), dict)
            and _source_time(item)[2] == "known"
        }
        units = {
            item["sourceTime"].get("resolution")
            for item in items
            if isinstance(item.get("sourceTime"), dict)
            and isinstance(item["sourceTime"].get("resolution"), str)
        }
        result.update(
            clockDomain=clock or next(iter(domains)) if len(domains) == 1 else clock,
            # Resolution is retained as reported metadata. It is not a generic
            # conversion table or proof of the tick encoding's unit.
            tickUnit="microsecond"
            if (
                evidence_scope == "owned_reference"
                and bool(items)
                and all(
                    isinstance(item.get("source"), dict)
                    and item["source"].get("providerId") == "studio.reference"
                    and item["source"].get("version") == "1.0.0"
                    and isinstance(item.get("sourceTime"), dict)
                    and item["sourceTime"].get("clockDomain") == "simulation-time"
                    and item["sourceTime"].get("resolution") == "microsecond"
                    for item in items
                )
            )
            else None,
            reportedResolutions=sorted(units),
            mapping=None,
        )
    return result
