"""Bounded derived browser views of one original public Argus capture.

No writer, raw logs, host paths, executable metadata or arbitrary payload bytes
cross this boundary. Correlation links assert membership, never physical cause.
"""

from collections import OrderedDict
from copy import deepcopy
from dataclasses import dataclass
import base64
import hashlib
import hmac
import json
import math
import re
import secrets
import threading
import time

from pydantic import BaseModel, ConfigDict, Field
from typing import Literal

from xverse_studio.storage.core import Problem, canonical, digest
from .argus import ArgusBinding, ArgusSources

VIEWS = ("orchestration", "communications", "evidence")
MAX_CAPTURE_BYTES = 4 * 1024 * 1024
MAX_CACHE_BYTES = 16 * 1024 * 1024
_CODE = re.compile(r"^[A-Z][A-Z0-9_.:-]{0,127}$")


class PlatformQuery(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=False)
    view: Literal["orchestration", "communications", "evidence"] = "orchestration"
    snapshot: str | None = Field(default=None, min_length=1, max_length=128)
    cursor: str | None = Field(default=None, min_length=1, max_length=2048)
    eventId: str | None = Field(default=None, min_length=1, max_length=128)
    correlationId: str | None = Field(default=None, min_length=1, max_length=128)
    logicalId: str | None = Field(default=None, min_length=1, max_length=512)
    limit: int = Field(default=50, ge=1, le=100)


@dataclass(frozen=True)
class PlatformEvidenceBinding:
    source: ArgusBinding
    input_semantic_digest: str
    provider_id: str
    installation_digest: str
    implementation_digest: str
    endpoint_owners: tuple[tuple[str, str], ...] = ()
    # Host-installed schema/codec pairs. Imported metadata cannot register codecs.
    payload_codecs: tuple[tuple[str, str], ...] = ()

    def __post_init__(self):
        if type(self.source) is not ArgusBinding:
            raise ValueError("PLATFORM_BINDING_INVALID")
        for value in (
            self.input_semantic_digest,
            self.installation_digest,
            self.implementation_digest,
        ):
            if not re.fullmatch(r"sha256:[a-f0-9]{64}", value):
                raise ValueError("PLATFORM_BINDING_INVALID")
        if (
            type(self.endpoint_owners) is not tuple
            or len(self.endpoint_owners) > 512
            or type(self.payload_codecs) is not tuple
            or len(self.payload_codecs) > 32
            or any(
                codec not in ("utf8-finite-number", "utf8-boolean")
                for _, codec in self.payload_codecs
            )
        ):
            raise ValueError("PLATFORM_BINDING_INVALID")

    def context(self):
        # In-memory binding key only. Never expose a filesystem path to HTTP.
        return digest(
            {
                "source": self.source.source_id,
                "root": str(self.source.root),
                "run": self.source.run_id,
                "plan": self.source.plan_digest,
                "input": self.input_semantic_digest,
                "provider": self.provider_id,
                "installation": self.installation_digest,
                "implementation": self.implementation_digest,
                "owners": self.endpoint_owners,
                "codecs": self.payload_codecs,
            }
        )


def _safe(value):
    """Keep exact integers across JavaScript, including source clock readings."""
    if isinstance(value, dict):
        return {key: _safe(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_safe(item) for item in value]
    if type(value) is int and abs(value) > 2**53 - 1:
        return str(value)
    return value


def _fields(source, names):
    return {key: deepcopy(source[key]) for key in names if key in source}


def _extension_shape(value, string_fields, *, containers=()):
    # Argus validates envelopes, but namespaced annotations are extensible data.
    # A malformed extension is unsupported, never arbitrary nested browser JSON.
    if (
        type(value) is not dict
        or any(
            value.get(key) is not None
            and (type(value[key]) is not str or len(value[key]) > 512)
            for key in string_fields
        )
        or any(
            value.get(key) is not None and type(value[key]) is not expected
            for key, expected in containers
        )
    ):
        raise Problem(
            "PLATFORM_RECORD_UNSUPPORTED",
            "A retained platform extension has an unsupported metadata shape.",
            422,
        )


def _payload(observation, codecs):
    result = {"policy": "metadata-only", "value": None}
    codec = codecs.get(observation.get("schemaId"))
    if not codec:
        return result
    result["policy"] = codec
    try:
        size = observation.get("sourcePayloadSize")
        visible = observation.get("visibleByteCount")
        raw = observation.get("visibleBytesHex")
        if (
            type(size) is not int
            or not 0 < size <= 128
            or visible != size
            or observation.get("payloadViewState") != "complete"
            or type(raw) is not str
            or len(raw) != size * 2
        ):
            raise ValueError()
        text = bytes.fromhex(raw).decode("utf-8")
        if codec == "utf8-finite-number":
            if not re.fullmatch(
                r"-?(?:0|[1-9][0-9]*)(?:\.[0-9]+)?(?:[eE][+-]?[0-9]+)?", text
            ):
                raise ValueError()
            number = float(text)
            if not math.isfinite(number):
                raise ValueError()
            # Keep exact visible decimal, not a rounded JavaScript float.
            result["value"] = text
        elif codec == "utf8-boolean" and text in ("true", "false"):
            result["value"] = text == "true"
        else:
            raise ValueError()
        result["decoding"] = "derived-from-original-visible-bytes"
    except (ValueError, UnicodeError, OverflowError):
        result["decoding"] = "unavailable"
    return result


def project_capture(captured, binding):
    """Return only the declared read projection, retaining canonical references."""
    owners, codecs = dict(binding.endpoint_owners), dict(binding.payload_codecs)
    rows, input_seen = [], False
    for original in captured["items"]:
        if original.get("runId") != binding.source.run_id:
            raise Problem(
                "PLATFORM_RECORD_IDENTITY_MISMATCH",
                "An original record belongs to another run.",
                409,
            )
        row = _fields(
            original,
            (
                "eventId",
                "eventKind",
                "producerId",
                "producerSequence",
                "ingestionOrdinal",
                "correlationId",
                "causationId",
                "clocks",
            ),
        )
        row["sourceRef"] = {
            "sourceId": binding.source.source_id,
            "runId": binding.source.run_id,
            "eventId": original["eventId"],
            "ingestionOrdinal": original["ingestionOrdinal"],
        }
        row["views"] = ["evidence"]
        exts = original.get("extensions", {})
        maestro = exts.get("io.xverse.maestro.execution")
        if maestro is not None:
            _extension_shape(
                maestro,
                (
                    "runId",
                    "planDigest",
                    "inputSemanticDigest",
                    "kind",
                    "logicalId",
                    "phaseId",
                    "operation",
                    "operationId",
                    "outcome",
                    "readinessKind",
                    "providerId",
                    "preparationDigest",
                ),
                containers=(
                    ("observation", dict),
                    ("resources", list),
                    ("sourceDigests", dict),
                ),
            )
            if any(
                type(r) is not str or len(r) > 512 for r in (maestro.get("resources") or [])
            ) or any(
                type(v) is not str or not re.fullmatch(r"sha256:[a-f0-9]{64}", v)
                for v in (maestro.get("sourceDigests") or {}).values()
            ):
                raise Problem(
                    "PLATFORM_RECORD_UNSUPPORTED",
                    "A retained platform extension has unsupported resource metadata.",
                    422,
                )
            if (
                maestro.get("runId") != binding.source.run_id
                or maestro.get("planDigest") != binding.source.plan_digest
                or maestro.get("inputSemanticDigest") != binding.input_semantic_digest
            ):
                raise Problem(
                    "PLATFORM_INPUT_IDENTITY_MISMATCH",
                    "Maestro's original input identities differ from the frozen run.",
                    409,
                )
            input_seen = True
            row["views"].append("orchestration")
            row["maestro"] = _fields(
                maestro,
                (
                    "kind",
                    "logicalId",
                    "phaseId",
                    "operation",
                    "operationId",
                    "outcome",
                    "readinessKind",
                    "providerId",
                    "preparationDigest",
                    "sourceDigests",
                    "resources",
                ),
            )
            # Only contract-defined structured status; no free-form reason/log text.
            observation = maestro.get("observation") or {}
            _extension_shape(
                observation,
                ("cleanup", "failureCode"),
                containers=(("argusOrdinals", list),),
            )
            if any(
                type(n) is not int or n < 0
                for n in observation.get("argusOrdinals", [])
            ) or any(
                observation.get(k) is not None
                and (type(observation[k]) is not int or observation[k] < 0)
                for k in ("missingSourceBatches", "observationTransportGaps")
            ):
                raise Problem(
                    "PLATFORM_RECORD_UNSUPPORTED",
                    "A retained platform extension has unsupported observation metadata.",
                    422,
                )
            row["maestro"]["observation"] = _fields(
                observation,
                (
                    "cleanup",
                    "observationTransportGaps",
                    "argusOrdinals",
                    "missingSourceBatches",
                ),
            )
            code = observation.get("failureCode")
            if code is None or (type(code) is str and _CODE.fullmatch(code)):
                row["maestro"]["observation"]["failureCode"] = code
            row["logicalId"] = maestro.get("logicalId")
        native_input = exts.get("io.xverse.native.input")
        if native_input is not None:
            _extension_shape(
                native_input,
                (
                    "eventId",
                    "producerId",
                    "routeId",
                    "endpointId",
                    "correlationId",
                    "upstreamCausationId",
                    "origin",
                ),
                containers=(("sourceClock", dict),),
            )
            row["views"].append("communications")
            row["input"] = _fields(
                native_input,
                (
                    "eventId",
                    "producerId",
                    "routeId",
                    "endpointId",
                    "sourceClock",
                    "correlationId",
                    "upstreamCausationId",
                    "sourcePayloadSize",
                    "origin",
                ),
            )
            row["logicalId"] = owners.get(native_input.get("endpointId"))
        observation = original.get("observation")
        if observation is not None:
            row["views"].append("communications")
            row["communication"] = _fields(
                observation,
                (
                    "contractId",
                    "contractVersion",
                    "interfaceId",
                    "endpointId",
                    "routeId",
                    "schemaId",
                    "schemaVersion",
                    "interactionKind",
                    "providerId",
                    "providerOutcome",
                    "origin",
                    "sourceClock",
                    "observationClock",
                    "sequence",
                    "counters",
                    "tapId",
                    "sourcePayloadSize",
                    "visibleByteCount",
                    "payloadSchemaState",
                    "payloadViewState",
                ),
            )
            row["communication"]["payload"] = _payload(observation, codecs)
            row["logicalId"] = owners.get(observation.get("endpointId"))
        snapshot = original.get("snapshot")
        if snapshot is not None:
            row["views"].append("communications")
            row["tapSnapshot"] = _fields(
                snapshot,
                (
                    "snapshotVersion",
                    "declaredTapId",
                    "accepted",
                    "backpressureRejections",
                    "coalesced",
                    "dropped",
                    "queued",
                    "handle",
                    "intervalProvenance",
                    "experimentValidityDegraded",
                    "validityEffect",
                    "validityState",
                ),
            )
        rows.append(_safe(row))
    # Argus reasons are not necessarily safe log strings. Original diagnostic
    # codes remain visible; all free-text reason messages remain in the source.
    verdicts = {name: captured["evidence"][name] for name in ("recorded", "assessed")}
    for name in ("recordedReasons", "assessedReasons"):
        reasons = captured["evidence"].get(name) or []
        verdicts[name] = [r for r in reasons if type(r) is str and _CODE.fullmatch(r)]
        verdicts[name + "Withheld"] = len(reasons) - len(verdicts[name])
    return {
        "projectionVersion": "1.0",
        "sourceId": binding.source.source_id,
        "sourceWitness": captured["sourceWitness"],
        "reader": captured["reader"],
        "identity": {
            "runId": binding.source.run_id,
            "planDigest": binding.source.plan_digest,
            "inputSemanticDigest": binding.input_semantic_digest,
            "providerId": binding.provider_id,
            "installationDigest": binding.installation_digest,
            "implementationDigest": binding.implementation_digest,
        },
        "identityVerified": {
            "runAndPlan": captured["identityVerified"],
            "maestroInputs": input_seen,
            "installation": "frozen-host-binding; not independently attested by Argus",
        },
        "evidence": verdicts,
        "diagnostics": captured["diagnostics"],
        "items": rows,
        "policy": {
            "payload": "host-allowlisted-scalars-only",
            "logs": "withheld",
            "clockMapping": "not-inferred",
            "integerEncoding": "unsafe-integers-as-decimal-strings",
            "links": "explicit-correlation-and-causation-only",
        },
        "counts": {
            "retained": len(rows),
            **{view: sum(view in r["views"] for r in rows) for view in VIEWS},
        },
    }


class PlatformViews:
    """Finite immutable captures, shared by every tab, never a lifecycle owner."""

    def __init__(self, *, clock=time.monotonic):
        self._clock = clock
        self._captures = OrderedDict()
        self._bytes = 0
        self._lock = threading.RLock()
        self._secret = secrets.token_bytes(32)

    def _discard(self, key):
        self._bytes -= self._captures.pop(key)["bytes"]

    def _prune(self):
        for key, entry in list(self._captures.items()):
            if self._clock() - entry["created"] >= 300:
                self._discard(key)

    def read(self, binding, query):
        if (
            type(binding) is not PlatformEvidenceBinding
            or type(query) is not PlatformQuery
        ):
            raise ValueError("PLATFORM_VIEW_ARGUMENT_INVALID")
        with self._lock:
            self._prune()
            context = binding.context()
            if query.snapshot:
                entry = self._captures.get(query.snapshot)
                if entry is None or entry["context"] != context:
                    raise Problem(
                        "PLATFORM_SNAPSHOT_EXPIRED",
                        "This evidence snapshot expired or belongs to another run. Refresh all three views.",
                        409,
                    )
                snapshot_id = query.snapshot
            else:
                if query.cursor:
                    raise Problem(
                        "PLATFORM_CURSOR_INVALID",
                        "A page requires its original evidence snapshot.",
                        409,
                    )
                source = ArgusSources((binding.source,))
                captured = source.capture(binding.source.source_id)
                projection = project_capture(captured, binding)
                size = len(canonical(projection).encode())
                if size > MAX_CAPTURE_BYTES:
                    raise Problem(
                        "PLATFORM_VIEW_LIMIT",
                        "The browser evidence snapshot exceeds its byte budget.",
                        413,
                    )
                snapshot_id = "platform-" + secrets.token_hex(16)
                for key in [
                    k for k, e in self._captures.items() if e["context"] == context
                ][:-1]:
                    self._discard(key)
                while self._captures and (
                    len(self._captures) >= 8 or self._bytes + size > MAX_CACHE_BYTES
                ):
                    self._discard(next(iter(self._captures)))
                entry = {
                    "context": context,
                    "projection": projection,
                    "bytes": size,
                    "created": self._clock(),
                    "capturedAt": time.time(),
                }
                self._captures[snapshot_id] = entry
                self._bytes += size
            self._captures.move_to_end(snapshot_id)
            projection = entry["projection"]
            filters = {
                "eventId": query.eventId,
                "correlationId": query.correlationId,
                "logicalId": query.logicalId,
            }
            cursor_context = digest(
                {
                    "snapshot": snapshot_id,
                    "view": query.view,
                    "filters": filters,
                    "limit": query.limit,
                }
            )
            offset = 0
            if query.cursor:
                try:
                    body, signature = query.cursor.rsplit(".", 1)
                    expected = hmac.new(
                        self._secret, body.encode(), hashlib.sha256
                    ).hexdigest()
                    if not hmac.compare_digest(signature, expected):
                        raise ValueError()
                    value = json.loads(
                        base64.urlsafe_b64decode(body + "=" * (-len(body) % 4))
                    )
                    if (
                        value["context"] != cursor_context
                        or type(value["offset"]) is not int
                        or value["offset"] <= 0
                    ):
                        raise ValueError()
                    offset = value["offset"]
                except (ValueError, KeyError, TypeError):
                    raise Problem(
                        "PLATFORM_CURSOR_INVALID",
                        "This page belongs to another snapshot, view or filter.",
                        409,
                    ) from None
            selected = [
                r
                for r in projection["items"]
                if query.view in r["views"]
                and all(v is None or r.get(k) == v for k, v in filters.items())
            ]
            if offset and offset >= len(selected):
                raise Problem(
                    "PLATFORM_CURSOR_INVALID",
                    "The selected evidence page is outside this snapshot.",
                    409,
                )
            following = offset + query.limit
            cursor = None
            if following < len(selected):
                body = (
                    base64.urlsafe_b64encode(
                        canonical(
                            {"context": cursor_context, "offset": following}
                        ).encode()
                    )
                    .decode()
                    .rstrip("=")
                )
                cursor = (
                    body
                    + "."
                    + hmac.new(self._secret, body.encode(), hashlib.sha256).hexdigest()
                )
            return deepcopy(
                {
                    **projection,
                    "items": selected[offset:following],
                    "snapshotId": snapshot_id,
                    "capturedAt": entry["capturedAt"],
                    "expiresInSeconds": max(
                        0, int(300 - (self._clock() - entry["created"]))
                    ),
                    "view": query.view,
                    "effectiveFilter": filters,
                    "matchedCount": len(selected),
                    "offset": offset,
                    "nextCursor": cursor,
                }
            )
