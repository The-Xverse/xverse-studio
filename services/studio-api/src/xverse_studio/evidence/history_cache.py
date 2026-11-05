"""Bounded derived history; current canonical verification remains mandatory."""

from collections import OrderedDict
import json
import math
import re
import threading

from xverse_studio.evidence.query import project_evidence
from xverse_studio.storage.core import canonical, digest

MAX_ENTRIES = 8
MAX_BYTES = 4 * 1024 * 1024
MAX_ENTRY_BYTES = 2 * 1024 * 1024
MAX_ENTRY_NODES = 32768


def bounded_bytes(value):
    # Bound escaping and container traversal before allocating a serialized copy.
    # Six UTF-8 bytes per character bounds both JSON escapes and Unicode scalars.
    stack, nodes, maximum = [value], 0, 0
    while stack:
        item = stack.pop()
        nodes += 1
        if nodes > MAX_ENTRY_NODES:
            return None
        kind = type(item)
        if kind is str:
            maximum += 2 + 6 * len(item)
        elif kind in (dict, list):
            added = len(item) * (2 if kind is dict else 1)
            if nodes + len(stack) + added > MAX_ENTRY_NODES:
                return None
            maximum += 2 + 2 * len(item)
            if kind is dict:
                stack.extend(item.keys())
                stack.extend(item.values())
            else:
                stack.extend(item)
        elif item is None or kind is bool:
            maximum += 5
        elif kind is int or kind is float and math.isfinite(item):
            maximum += len(str(item))
        else:
            return None
        if maximum > MAX_ENTRY_BYTES:
            return None
    raw = canonical(value).encode()
    return raw if len(raw) <= MAX_ENTRY_BYTES else None


class HistoryCache:
    """One application's projections, admitted only after each source acquisition."""

    def __init__(self):
        self.entries = OrderedDict()
        self.size = 0
        self.lock = threading.RLock()

    def project(self, records, integrity, query, run, run_id):
        key = None
        source_digest = run.get("journalDigest")
        last_digest = records[-1].get("digest") if records and isinstance(records[-1], dict) else None
        if (integrity == "valid" and run.get("state") in {"stopped", "failed"}
                and run.get("runId") == run_id and isinstance(run.get("snapshotId"), str)
                and isinstance(source_digest, str) and isinstance(last_digest, str)
                and re.fullmatch(r"sha256:[0-9a-f]{64}", source_digest)
                and re.fullmatch(r"[0-9a-f]{64}", last_digest)):
            # The caller has just acquired and verified this exact declared
            # terminal digest, including run/snapshot identity. No authority,
            # validation or file acquisition is skipped by this derived cache.
            key = digest({"runId": run["runId"], "snapshotId": run["snapshotId"],
                          "journalDigest": source_digest, "lastRecordDigest": last_digest,
                          "recordCount": len(records), "state": run["state"],
                          "evidenceScope": run.get("evidenceScope", "unknown"),
                          "query": query.model_dump(mode="json")})
            with self.lock:
                raw = self.entries.get(key)
                if raw is not None:
                    self.entries.move_to_end(key)
            if raw is not None:
                return json.loads(raw)
        result = project_evidence(records, integrity, query, run_id, "history",
                                  evidence_scope=run.get("evidenceScope", "unknown"))
        if key is not None and (raw := bounded_bytes(result)) is not None:
            with self.lock:
                previous = self.entries.pop(key, None)
                if previous is not None:
                    self.size -= len(previous)
                self.entries[key] = raw
                self.size += len(raw)
                while len(self.entries) > MAX_ENTRIES or self.size > MAX_BYTES:
                    _, removed = self.entries.popitem(last=False)
                    self.size -= len(removed)
            # A fresh JSON observation cannot mutate the reader's cached records
            # or another caller's projection through shared nested references.
            return json.loads(raw)
        return result
