"""Read-only, integrity-checked reference evidence; never claim Argus admission."""

import hashlib
import json
import os
import re
import threading
from collections import OrderedDict
from xverse_studio.storage.core import canonical, digest
from xverse_studio.security.managed_io import open_read, SafeIOError


_CACHE = OrderedDict()
_CACHE_LOCK = threading.RLock()
MAX_JOURNAL_BYTES = 64 * 1024 * 1024
MAX_JOURNAL_RECORDS = 100000


def read_journal(root, state):
    if not isinstance(state, dict):
        return [], "invalid"
    declared_digest = state.get("journalDigest")
    if declared_digest is not None and (
        not isinstance(declared_digest, str)
        or not re.fullmatch(r"sha256:[0-9a-f]{64}", declared_digest)
    ):
        return [], "invalid"
    if any(
        state.get(field) is not None
        and (not isinstance(state[field], str) or not 0 < len(state[field]) <= 512)
        for field in ("runId", "snapshotId")
    ):
        return [], "invalid"
    path = root / "evidence.jsonl"
    try:
        with open_read(root, path) as stream:
            info = os.fstat(stream.fileno())
            if info.st_size > MAX_JOURNAL_BYTES:
                return [], "invalid"
            key = (
                str(path.absolute()),
                info.st_dev,
                info.st_ino,
                info.st_size,
                info.st_mtime_ns,
                info.st_ctime_ns,
                state.get("journalDigest"),
                state.get("runId"),
                state.get("snapshotId"),
                state.get("state") in ("stopped", "failed"),
            )
            with _CACHE_LOCK:
                if key in _CACHE:
                    _CACHE.move_to_end(key)
                    return _CACHE[key][0], _CACHE[key][1]
            data = stream.read(MAX_JOURNAL_BYTES + 1)
            if len(data) > MAX_JOURNAL_BYTES:
                return [], "invalid"
    except SafeIOError as exc:
        # An append concurrent with acquisition is not proof of corruption.
        # Refuse that observation and retry later without upgrading integrity.
        return [], "unavailable" if exc.code in {
            "FILE_MISSING",
            "SOURCE_CHANGED",
            "SECURE_IO_UNAVAILABLE",
        } else "invalid"
    except OSError:
        return [], "unavailable"
    records = []
    identities = set()
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
            if (
                not isinstance(record, dict)
                or record.get("schemaVersion") != "1.0"
                or any(
                    not isinstance(record.get(field), str)
                    or not 0 < len(record[field]) <= 512
                    for field in ("eventId", "runId", "snapshotId", "type")
                )
                or not isinstance(record.get("payload"), dict)
                or not isinstance(record.get("elementRefs"), list)
                or record["eventId"] in identities
                or not isinstance(record.get("sequence"), str)
                or len(record["sequence"]) > 32
                or not re.fullmatch(r"(?:0|[1-9][0-9]*)", record["sequence"])
                or state.get("runId") is not None
                and record["runId"] != state["runId"]
                or state.get("snapshotId") is not None
                and record["snapshotId"] != state["snapshotId"]
            ):
                return records, "invalid"
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
            identities.add(record["eventId"])
            if len(records) > MAX_JOURNAL_RECORDS:
                return [], "invalid"
        if state.get("journalDigest") and digest(data) != state["journalDigest"]:
            return records, "invalid"
    except (ValueError, KeyError, TypeError, RecursionError):
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
    """Compatibility entry point using the same truthful, bounded projection."""
    from xverse_studio.evidence.query import ObservationQuery, project_evidence

    query = ObservationQuery(
        observerRef=observer,
        field=field,
        startTick=str(start) if start is not None else None,
        endTick=str(end) if end is not None else None,
    )
    run_ids = {
        record.get("runId")
        for record in records
        if isinstance(record.get("runId"), str)
    }
    run_id = next(iter(run_ids)) if len(run_ids) == 1 else "legacy-projection"
    return project_evidence(records, integrity, query, run_id, "observations")
