"""Bounded revision-checked SQLite lease ledger; unknown payloads stay private."""

from copy import deepcopy
import json
import math
from threading import RLock
import time

from xverse_studio.lab import LabError, LabRegistry
from xverse_studio.lab.assets import opaque_id
from xverse_studio.storage.core import canonical


class LabLeaseBacking:
    KIND = "lab_registry"
    KEY = "leases"

    def __init__(self, store, *, max_records=1000, max_bytes=2 * 1024 * 1024):
        if (
            type(max_records) is not int
            or not 0 < max_records <= 1000
            or type(max_bytes) is not int
            or not 256 <= max_bytes <= 2 * 1024 * 1024
        ):
            raise LabError("LAB_STATE_UNAVAILABLE")
        self.store = store
        self.max_records = max_records
        self.max_bytes = max_bytes
        self._revision = None
        self._lock = RLock()

    def _validate(self, value):
        return validate_snapshot(value, max_records=self.max_records)

    def _read(self, db):
        rows = db.execute(
            "SELECT id,length(CAST(body AS BLOB)) FROM records WHERE kind=? LIMIT 2",
            (self.KIND,),
        ).fetchall()
        if not rows:
            return {"revision": 0, "records": []}
        if len(rows) != 1 or rows[0][0] != self.KEY or rows[0][1] > self.max_bytes:
            raise LabError("LAB_STATE_UNAVAILABLE")
        try:
            raw = db.execute(
                "SELECT body FROM records WHERE kind=? AND id=?", (self.KIND, self.KEY)
            ).fetchone()[0]
            return self._validate(json.loads(raw))
        except (ValueError, TypeError, RecursionError):
            raise LabError("LAB_STATE_UNAVAILABLE") from None

    def load(self):
        with self._lock:
            with self.store.tx() as db:
                value = self._read(db)
            self._revision = value["revision"]
            return deepcopy(value["records"])

    def save(self, records):
        with self._lock:
            if self._revision is None:
                raise LabError("LAB_STATE_UNAVAILABLE")
            value = self._validate(
                {
                    "contractVersion": "1.0",
                    "revision": self._revision + 1,
                    "records": deepcopy(records),
                }
            )
            try:
                encoded = canonical(value).encode()
            except (ValueError, TypeError, RecursionError):
                raise LabError("LAB_STATE_UNAVAILABLE") from None
            if len(encoded) > self.max_bytes:
                raise LabError("LIMIT_EXCEEDED")
            with self.store.tx() as db:
                if self._read(db)["revision"] != self._revision:
                    raise LabError("LAB_STATE_STALE")
                self.store.put(self.KIND, self.KEY, value, db)
            self._revision = value["revision"]

    def assert_current(self):
        with self._lock:
            with self.store.tx() as db:
                observed = self._read(db)["revision"]
            if self._revision is None or observed != self._revision:
                raise LabError("LAB_STATE_STALE")

    def registry(self, providers, *, clock=time.time):
        return LabRegistry(
            providers,
            clock=clock,
            records=self.load(),
            persist=self.save,
            max_reservations=self.max_records,
        )


def validate_snapshot(value, *, max_records=1000):
    if (
        type(value) is not dict
        or value.get("contractVersion") != "1.0"
        or type(value.get("revision")) is not int
        or value["revision"] < 1
    ):
        raise LabError("LAB_STATE_UNAVAILABLE")
    records = value.get("records")
    if type(records) is not list or len(records) > max_records:
        raise LabError("LAB_STATE_UNAVAILABLE")
    seen = set()
    for record in records:
        if type(record) is not dict or any(
            not opaque_id(record.get(key))
            for key in ["reservationId", "assetId", "providerId", "owner"]
        ):
            raise LabError("LAB_STATE_UNAVAILABLE")
        if record["reservationId"] in seen:
            raise LabError("LAB_STATE_UNAVAILABLE")
        seen.add(record["reservationId"])
        if record.get("scope") not in (
            "observe",
            "stimulate",
            "destructive",
        ) or record.get("status") not in ("owned", "unknown", "released", "expired"):
            raise LabError("LAB_STATE_UNAVAILABLE")
        expiry = record.get("expiry")
        if type(expiry) not in (int, float) or not math.isfinite(expiry):
            raise LabError("LAB_STATE_UNAVAILABLE")
        fence = record.get("fencingIdentity")
        if fence is not None and (type(fence) is not str or not 0 < len(fence) <= 256):
            raise LabError("LAB_STATE_UNAVAILABLE")
        if record["status"] == "owned" and fence is None:
            raise LabError("LAB_STATE_UNAVAILABLE")
    return value
