from __future__ import annotations

from copy import deepcopy
import math
import threading
import time
import uuid

from xverse_studio.storage.core import digest


class LabError(ValueError):
    def __init__(self, code):
        self.code = code
        super().__init__(code)


class LabRegistry:
    """Explicit inventory and fenced leases over server-admitted providers.

    This registry neither discovers arbitrary endpoints nor installs providers.
    Registering a provider is a trusted backend operation. A nonterminal lease is
    unknown on restore until its provider confirms the same owner and fence.
    Confirmed released/expired records remain terminal and confer no authority.
    """
    def __init__(self, providers=None, *, clock=time.time, records=(), persist=None, max_assets=1000, max_reservations=1000, max_lease_seconds=300):
        self.providers = dict(providers or {})
        self.clock = clock
        self.persist = persist
        self.max_assets = max_assets
        self.max_reservations = max_reservations
        self.max_lease_seconds = max_lease_seconds
        self.records = {
            r["reservationId"]: {
                **deepcopy(r),
                "status": r.get("status")
                if r.get("status") in ("released", "expired")
                else "unknown",
            }
            for r in records
        }
        self._lock = threading.RLock()

    def _save(self):
        if self.persist:
            try:
                self.persist(deepcopy(list(self.records.values())))
            except Exception:
                # A failed durable acknowledgement must not leave memory with
                # usable authority that the caller was told is uncertain.
                for record in self.records.values():
                    if record['status'] == 'owned':
                        record.update(status='unknown', reason='LEASE_PERSISTENCE_UNCERTAIN')
                raise

    def inventory(self):
        assets = []
        seen = set()
        for provider_id, provider in self.providers.items():
            try:
                result = provider.inventory()
            except Exception:
                continue
            for asset in result:
                if len(assets) >= self.max_assets:
                    raise LabError("LIMIT_EXCEEDED")
                if not isinstance(asset, dict) or asset.get("providerId") != provider_id or not isinstance(asset.get("assetId"), str) or asset["assetId"] in seen:
                    raise LabError("PROVIDER_INVENTORY_INVALID")
                seen.add(asset["assetId"])
                assets.append(deepcopy(asset))
        return assets

    def _asset(self, asset_id):
        for asset in self.inventory():
            if asset["assetId"] == asset_id:
                return asset
        raise LabError("ASSET_UNAVAILABLE")

    def _duration(self, duration):
        if not isinstance(duration, (int, float)) or isinstance(duration, bool) or not math.isfinite(duration) or not 0 < duration <= self.max_lease_seconds:
            raise LabError("LEASE_LIMIT")
        return self.clock() + duration

    def _owned(self, reservation_id, owner):
        rec = self.records.get(reservation_id)
        if rec is None:
            raise LabError("RESERVATION_NOT_FOUND")
        if rec["owner"] != owner:
            raise LabError("FORBIDDEN")
        if rec["status"] == "owned" and self.clock() >= rec["expiry"]:
            rec["status"] = "expired"
            self._save()
        return rec

    def reserve(self, asset_id, *, owner, duration=60, scope="observe", granted_scopes=(), reservation_id=None, provider_identity=None, asset_identity=None):
        with self._lock:
            expiry = self._duration(duration)
            if not isinstance(owner, str) or not owner:
                raise LabError("FORBIDDEN")
            asset = self._asset(asset_id)
            if asset_identity is not None and digest(asset.get("identity")) != asset_identity:
                raise LabError("ASSET_IDENTITY_CHANGED")
            if scope not in {"observe", "stimulate", "destructive"}:
                raise LabError("CAPABILITY_UNSUPPORTED")
            if scope not in asset.get("capabilities", []):
                raise LabError("CAPABILITY_UNSUPPORTED")
            if scope != "observe" and scope not in granted_scopes:
                raise LabError("FORBIDDEN")
            if len(self.records) >= self.max_reservations:
                raise LabError("LIMIT_EXCEEDED")
            for current in self.records.values():
                if current["assetId"] == asset_id and current["status"] in {"owned", "unknown"} and current["expiry"] > self.clock():
                    raise LabError("RESOURCE_BUSY")
            provider = self.providers[asset["providerId"]]
            reservation_id = reservation_id or str(uuid.uuid4())
            if reservation_id in self.records:
                raise LabError("RESERVATION_ID_CONFLICT")
            # Intent is durable before delegation. If acknowledgement is lost it
            # must remain unknown and the provider reconciles this identity.
            rec = {"reservationId": reservation_id, "assetId": asset_id, "providerId": asset["providerId"], "owner": owner, "scope": scope, "expiry": expiry, "status": "unknown", "fencingIdentity": None, "lastRenewal": None, "evidenceScope": asset.get("evidenceScope", "unknown")}
            if provider_identity is not None:
                rec["providerIdentity"] = provider_identity
            if asset_identity is not None:
                rec["assetIdentity"] = asset_identity
            self.records[reservation_id] = rec
            self._save()
            try:
                observed = provider.reserve({**asset, "reservationId": reservation_id}, scope, owner, expiry)
            except Exception as exc:
                # RESOURCE_BUSY is the contract's refusal before allocating a
                # lease. A typed error alone does not prove that no effect took
                # place: uncertain or unclassified outcomes retain the intent.
                if isinstance(exc, LabError) and exc.code == "RESOURCE_BUSY":
                    del self.records[reservation_id]; self._save()
                    raise
                rec["reason"] = "RESERVATION_ACKNOWLEDGEMENT_LOST"
                self._save()
                raise LabError("OWNERSHIP_UNCERTAIN") from None
            if not self._matches(rec, observed, initial=True):
                rec["reason"] = "PROVIDER_RESERVATION_INVALID"
                self._save()
                raise LabError("OWNERSHIP_UNCERTAIN")
            rec.update(fencingIdentity=observed["fencingIdentity"], expiry=observed["expiry"], status="owned")
            self._save()
            return deepcopy(rec)

    def _matches(self, rec, observed, *, initial=False):
        return isinstance(observed, dict) and observed.get("status") == "owned" and isinstance(observed.get("fencingIdentity"), str) and bool(observed["fencingIdentity"]) and (initial or observed["fencingIdentity"] == rec["fencingIdentity"]) and observed.get("owner") == rec["owner"] and observed.get("scope") == rec["scope"] and isinstance(observed.get("expiry"), (int, float)) and math.isfinite(observed["expiry"]) and self.clock() < observed["expiry"] <= rec["expiry"]

    def get(self, reservation_id, *, owner):
        with self._lock:
            return deepcopy(self._owned(reservation_id, owner))

    def require_authority(self, reservation_id, *, owner, action, granted_scopes=()):
        with self._lock:
            rec = self._owned(reservation_id, owner)
            if rec["status"] != "owned":
                raise LabError("OWNERSHIP_UNCERTAIN")
            asset = self._asset(rec["assetId"])
            if action not in asset.get("capabilities", []):
                raise LabError("CAPABILITY_UNSUPPORTED")
            if action != "observe" and (rec["scope"] != action or action not in granted_scopes):
                raise LabError("FORBIDDEN")
            return deepcopy(rec)

    def renew(self, reservation_id, *, owner, expected_fencing_identity, duration=60, granted_scopes=()):
        with self._lock:
            rec = self._owned(reservation_id, owner)
            expiry = self._duration(duration)
            if rec["status"] != "owned":
                raise LabError("OWNERSHIP_UNCERTAIN")
            if expected_fencing_identity != rec["fencingIdentity"]:
                raise LabError("STALE_FENCING_IDENTITY")
            if rec["scope"] != "observe" and rec["scope"] not in granted_scopes:
                raise LabError("FORBIDDEN")
            if expiry <= rec["expiry"]:
                raise LabError("LEASE_NOT_EXTENSION")
            observed = None
            previous_expiry = rec["expiry"]
            rec.update(status="unknown", expiry=expiry)
            self._save()
            try:
                observed = self.providers[rec["providerId"]].renew(deepcopy(rec), expected_fencing_identity, expiry, {"owner": owner, "scopes": list(granted_scopes)})
            except Exception:
                rec.update(expiry=previous_expiry, reason="RENEWAL_UNCERTAIN"); self._save()
                raise LabError("OWNERSHIP_UNCERTAIN") from None
            if not self._matches(rec, observed):
                rec.update(expiry=previous_expiry, reason="RENEWAL_UNCERTAIN"); self._save()
                raise LabError("OWNERSHIP_UNCERTAIN")
            rec.update(status="owned", expiry=observed["expiry"], lastRenewal=self.clock())
            self._save()
            return deepcopy(rec)

    def release(self, reservation_id, *, owner):
        with self._lock:
            rec = self._owned(reservation_id, owner)
            if rec["status"] in {"released", "expired"}:
                return deepcopy(rec)
            if rec["status"] != "owned":
                raise LabError("OWNERSHIP_UNCERTAIN")
            rec["status"] = "unknown"; self._save()
            try:
                observed = self.providers[rec["providerId"]].release(deepcopy(rec), {"owner": owner})
            except Exception:
                rec["reason"] = "RELEASE_UNCERTAIN"; self._save()
                raise LabError("OWNERSHIP_UNCERTAIN") from None
            rec["status"] = "released" if isinstance(observed, dict) and observed.get("status") == "released" else "unknown"
            self._save()
            return deepcopy(rec)

    def reconcile(self, reservation_id, *, owner):
        with self._lock:
            rec = self._owned(reservation_id, owner)
            if rec["status"] in {"released", "expired"}:
                return deepcopy(rec)
            try:
                observed = self.providers[rec["providerId"]].inspect_reservation(deepcopy(rec))
                rec["status"] = "owned" if self._matches(rec, observed) else "unknown"
            except Exception:
                rec["status"] = "unknown"
            self._save()
            return deepcopy(rec)
