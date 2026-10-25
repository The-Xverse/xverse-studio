"""Read-only, integrity-checked reference evidence; never claim Argus admission."""

import hashlib
import json
import threading
from collections import OrderedDict
from xverse_studio.storage.core import canonical, digest, Problem


_CACHE = OrderedDict()
_CACHE_LOCK = threading.RLock()
MAX_JOURNAL_BYTES = 64 * 1024 * 1024
MAX_JOURNAL_RECORDS = 100000


def read_journal(root, state):
    path = root / "evidence.jsonl"
    if not path.exists():
        return [], "unavailable"
    stat = path.stat()
    if stat.st_size > MAX_JOURNAL_BYTES:
        return [], "invalid"
    key = (
        str(path.resolve()),
        stat.st_dev,
        stat.st_ino,
        stat.st_size,
        stat.st_mtime_ns,
        stat.st_ctime_ns,
        state.get("journalDigest"),
        state.get("state") in ("stopped", "failed"),
    )
    with _CACHE_LOCK:
        if key in _CACHE:
            _CACHE.move_to_end(key)
            return _CACHE[key][0], _CACHE[key][1]
    data = path.read_bytes()
    records = []
    previous = "0" * 64
    try:
        lines = data.splitlines(keepends=True)
        for i, line in enumerate(lines):
            if not line.endswith(b"\n") and state.get("state") not in (
                "stopped",
                "failed",
            ):
                break
            record = json.loads(line)
            expected = record.pop("digest")
            if (
                record["previousDigest"] != previous
                or hashlib.sha256(canonical(record).encode()).hexdigest() != expected
            ):
                return records, "invalid"
            record["digest"] = expected
            previous = expected
            if int(record["sequence"]) != len(records) + 1:
                return records, "invalid"
            records.append(record)
            if len(records) > MAX_JOURNAL_RECORDS:
                return [], "invalid"
        if state.get("journalDigest") and digest(data) != state["journalDigest"]:
            return records, "invalid"
    except (ValueError, KeyError, TypeError):
        return records, "invalid"
    integrity = "valid" if state.get("journalDigest") else "verified_prefix"
    with _CACHE_LOCK:
        # At most two source projections and 64MiB of contributing source bytes.
        _CACHE[key] = (records, integrity, len(data))
        while (
            len(_CACHE) > 2
            or sum(value[2] for value in _CACHE.values()) > MAX_JOURNAL_BYTES
        ):
            _CACHE.popitem(last=False)
    return records, integrity


def observation_projection(
    records, integrity, observer=None, field=None, start=None, end=None
):
    items = []
    for r in records:
        if r["type"] != "observation.available":
            continue
        p = r["payload"]
        t = r.get("sourceTime") or {}
        if observer and observer != p.get("observerRef"):
            continue
        tick = int(t.get("tick", "0"))
        if start is not None and tick < start or end is not None and tick >= end:
            continue
        items.append(
            {
                "eventId": r["eventId"],
                "observerRef": p.get("observerRef"),
                "sourceTime": t,
                "tick": str(tick),
                "values": p["values"]
                if not field
                else {field: p["values"][field]}
                if field in p["values"]
                else {},
                "units": p.get("units", {}),
                "elementRefs": r["elementRefs"],
            }
        )
    return {
        "items": items[:10000],
        "integrity": integrity,
        "clockDomain": "simulation-time",
        "tickUnit": "microsecond",
        "mapping": {"mappingId": "reference-us-v1", "uncertainty": 0},
        "reduction": {"method": "none", "canonical": True},
        "gaps": []
        if integrity == "valid"
        else [{"reason": "Coverage is not yet proven complete."}],
        "evidenceScope": "owned_reference",
    }
