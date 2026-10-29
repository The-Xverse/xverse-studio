"""Durable reservation operations over explicitly installed host providers.

Trusted host code supplies already-installed providers, pinned binding identities
and server-owned policy. Browser/project data cannot create these objects.
"""

from copy import deepcopy
import json
import math
import re
import threading
import time

from xverse_studio.lab import LabError
from xverse_studio.lab.assets import opaque_id
from xverse_studio.storage.core import Problem, digest, uid
from .authority import LabAuthority
from .bounded import BoundedLeaseProvider
from .persistence import LabLeaseBacking
from .reservations import LabRegistry

KINDS = ("lab_reserve", "lab_renew", "lab_release", "lab_reconcile")
MAX_OPERATION_BYTES = 8192


def _lease_view(record):
    shown = {
        key: deepcopy(record[key])
        for key in (
            "reservationId",
            "assetId",
            "providerId",
            "owner",
            "scope",
            "expiry",
            "status",
            "fencingIdentity",
        )
    }
    renewed = record.get("lastRenewal")
    shown["lastRenewal"] = (
        renewed if type(renewed) in (int, float) and math.isfinite(renewed) else None
    )
    scope = record.get("evidenceScope")
    shown["evidenceScope"] = (
        scope
        if scope in ("fixture", "prototype", "admitted_integration", "unavailable")
        else "unknown"
    )
    reason = record.get("reason")
    if reason is not None:
        shown["reason"] = (
            reason
            if type(reason) is str and re.fullmatch(r"[A-Z][A-Z0-9_]{0,63}", reason)
            else "LEASE_STATE_UNAVAILABLE"
        )
    return shown


def _operation_view(record):
    shown = {
        key: deepcopy(record[key])
        for key in (
            "operationId",
            "kind",
            "principal",
            "route",
            "status",
            "reservationId",
            "createdAt",
        )
    }
    shown["result"] = {
        key: deepcopy(record["result"][key])
        for key in ("reservationId", "status")
        if key in record["result"]
    }
    if "code" in record:
        code = record["code"]
        shown["code"] = (
            code
            if type(code) is str and re.fullmatch(r"[A-Z][A-Z0-9_]{0,63}", code)
            else "LAB_OPERATION_UNCERTAIN"
        )
    return shown


class LabOperations:
    def __init__(
        self,
        store,
        providers,
        identities,
        policy,
        *,
        clock=time.time,
        timeout=1.0,
        max_operations=1000,
    ):
        if (
            not isinstance(policy, LabAuthority)
            or type(providers) is not dict
            or not 0 <= len(providers) <= 32
        ):
            raise LabError("PROVIDER_CONFIG_INVALID")
        if type(identities) is not dict or set(identities) != set(providers):
            raise LabError("PROVIDER_CONFIG_INVALID")
        if any(
            not opaque_id(key)
            or type(value) is not str
            or not re.fullmatch(r"sha256:[a-f0-9]{64}", value)
            for key, value in identities.items()
        ):
            raise LabError("PROVIDER_CONFIG_INVALID")
        if type(max_operations) is not int or not 0 < max_operations <= 1000:
            raise LabError("PROVIDER_CONFIG_INVALID")
        self.store, self.policy = store, policy
        self.identities = deepcopy(identities)
        self._max_operations = max_operations
        self.enabled = bool(providers)
        self.installation_descriptors = []
        self.call_timeout = timeout
        self._lock = threading.RLock()
        self._uncertain_receipts = set()
        self.backing = LabLeaseBacking(store)
        wrapped = {
            key: BoundedLeaseProvider(
                value, timeout=timeout, guard=self._provider_guard
            )
            for key, value in providers.items()
        }
        self.registry = LabRegistry(
            wrapped, clock=clock, records=self.backing.load(), persist=self.backing.save
        )
        # Recovered accepted/delegated work is inspected, never reissued.
        with store.tx() as db:
            rows = db.execute(
                "SELECT id,length(CAST(body AS BLOB)) FROM records WHERE kind='operation' AND json_extract(body,'$.kind') IN (?,?,?,?) LIMIT ?",
                (*KINDS, self._max_operations + 1),
            ).fetchall()
            if len(rows) > self._max_operations:
                raise LabError("LIMIT_EXCEEDED")
            operations = [self._read_operation(identity, db) for identity, size in rows]
            for operation in operations:
                if operation["status"] in {"accepted", "delegated"}:
                    operation.update(status="unknown", code="LAB_OPERATION_INTERRUPTED")
                    store.put("operation", operation["operationId"], operation, db)

    def discovery(self):
        return {
            "contractVersion": "1.0",
            "status": "configured" if self.enabled else "unavailable",
            "providers": deepcopy(self.installation_descriptors),
            "scopes": ["observe", "stimulate", "destructive"],
            "grants": "server_owned_exact_principal_and_asset",
            "runtimeAdmission": "unavailable",
            "physicalCommands": [],
            "automaticRunRenewal": False,
            "limits": {
                "providers": 32,
                "leases": self.backing.max_records,
                "ledgerBytes": self.backing.max_bytes,
                "operations": self._max_operations,
                "operationBytes": MAX_OPERATION_BYTES,
                "leaseSeconds": self.registry.max_lease_seconds,
                "providerCallSeconds": self.call_timeout,
                "outstandingCallsPerProvider": 1,
                "queuedCalls": 0,
            },
            "diagnostics": []
            if self.enabled
            else [{"code": "PHYSICAL_PROVIDER_NOT_ADMITTED"}],
        }

    def _read_operation(self, identity, db):
        size = db.execute(
            "SELECT length(CAST(body AS BLOB)) FROM records WHERE kind='operation' AND id=?",
            (identity,),
        ).fetchone()
        if size is None or size[0] > MAX_OPERATION_BYTES:
            raise LabError("LAB_STATE_UNAVAILABLE")
        try:
            record = self.store.get("operation", identity, db)
            if (
                type(record) is not dict
                or record.get("kind") not in KINDS
                or record.get("operationId") != identity
            ):
                raise LabError("LAB_STATE_UNAVAILABLE")
            if not all(
                opaque_id(record.get(key))
                for key in ("operationId", "principal", "reservationId")
            ):
                raise LabError("LAB_STATE_UNAVAILABLE")
            route = record.get("route")
            if type(route) is not str or not re.fullmatch(
                r"(?:POST /assets/[A-Za-z0-9:._-]{1,253}/reservations|POST /reservations/[A-Za-z0-9:._-]{1,253}/(?:renewals|reconciliations)|DELETE /reservations/[A-Za-z0-9:._-]{1,253})",
                route,
            ):
                raise LabError("LAB_STATE_UNAVAILABLE")
            if record.get("status") not in (
                "accepted",
                "delegated",
                "completed",
                "rejected",
                "failed",
                "unknown",
            ):
                raise LabError("LAB_STATE_UNAVAILABLE")
            if type(record.get("createdAt")) not in (int, float) or not math.isfinite(
                record["createdAt"]
            ):
                raise LabError("LAB_STATE_UNAVAILABLE")
            result = record.get("result")
            if (
                type(result) is not dict
                or result.get("reservationId") != record["reservationId"]
                or (
                    "status" in result
                    and result["status"]
                    not in ("owned", "unknown", "released", "expired")
                )
            ):
                raise LabError("LAB_STATE_UNAVAILABLE")
            return record
        except (KeyError, TypeError, ValueError, RecursionError):
            raise LabError("LAB_STATE_UNAVAILABLE") from None

    def _provider_guard(self, name, args):
        if name == "inventory":
            return
        self.backing.assert_current()
        if name == "reserve":
            asset, scope, owner, deadline = args
            self.policy.require(owner, asset["assetId"], scope)
        elif name == "renew":
            record, fence, deadline, authority = args
            self.policy.require(record["owner"], record["assetId"], record["scope"])
        else:
            return  # Owned cleanup/reconciliation does not require a new active grant.
        if self.registry.clock() >= deadline:
            raise LabError("LEASE_EXPIRED")

    def _prior(self, owner, route, key, payload):
        if type(key) is not str or not 0 < len(key) <= 128:
            raise Problem(
                "IDEMPOTENCY_REQUIRED",
                "Supply an Idempotency-Key of at most 128 characters.",
                428,
            )
        with self.store.tx() as db:
            row = db.execute(
                "SELECT fingerprint,result FROM idempotency WHERE scope=? AND key=?",
                (owner + ":" + route, key),
            ).fetchone()
            if row:
                if row[0] != digest(payload):
                    raise Problem(
                        "IDEMPOTENCY_CONFLICT",
                        "This key already identifies a different request.",
                        409,
                    )
                receipt = json.loads(row[1])
                operation = self._read_operation(receipt["operationId"], db)
                if (
                    operation.get("principal") != owner
                    or operation.get("route") != route
                ):
                    raise LabError("LAB_STATE_UNAVAILABLE")
                return self._receipt_view(operation)

    def _accept(self, owner, route, key, payload, kind, reservation_id):
        def accept(db):
            count = db.execute(
                "SELECT count(*) FROM records WHERE kind='operation' AND json_extract(body,'$.kind') IN ('lab_reserve','lab_renew','lab_release','lab_reconcile')"
            ).fetchone()[0]
            if count >= self._max_operations:
                raise LabError("LIMIT_EXCEEDED")
            operation = {
                "operationId": uid("op-"),
                "kind": kind,
                "principal": owner,
                "route": route,
                "status": "accepted",
                "reservationId": reservation_id,
                "createdAt": time.time(),
                "result": {"reservationId": reservation_id},
            }
            self.store.put("operation", operation["operationId"], operation, db)
            return {
                "operationId": operation["operationId"],
                "reservationId": reservation_id,
            }

        receipt, is_new = self.store.idempotent(owner, route, key, payload, accept)
        with self.store.tx() as db:
            return self._read_operation(receipt["operationId"], db), is_new

    def _perform(self, operation, callback):
        operation.update(status="delegated")
        self.store.put("operation", operation["operationId"], operation)
        try:
            result = callback()
        except Exception as error:
            code = (
                error.code if isinstance(error, LabError) else "LAB_OPERATION_UNCERTAIN"
            )
            operation.update(
                status="rejected" if code == "RESOURCE_BUSY" else "unknown", code=code
            )
        else:
            operation.update(
                status="completed"
                if result["status"] in {"owned", "released", "expired"}
                else "unknown",
                result={
                    "reservationId": result["reservationId"],
                    "status": result["status"],
                },
            )
        try:
            self.store.put("operation", operation["operationId"], operation)
        except Exception:
            # A store may raise after committing. Read back the exact record
            # before downgrading it; never delegate the provider operation again.
            try:
                with self.store.tx() as db:
                    observed = self._read_operation(operation["operationId"], db)
                if observed == operation:
                    return _operation_view(observed)
            except Exception:
                pass
            operation.update(status="unknown", code="LAB_OPERATION_RECORD_UNCERTAIN")
            if len(self._uncertain_receipts) < self._max_operations:
                self._uncertain_receipts.add(operation["operationId"])
            try:
                self.store.put("operation", operation["operationId"], operation)
            except Exception:
                pass  # The accepted mapping is durable; restart retains unknown.
        return self._receipt_view(operation)

    def _receipt_view(self, operation):
        if operation["operationId"] in self._uncertain_receipts:
            operation = {
                **operation,
                "status": "unknown",
                "code": "LAB_OPERATION_RECORD_UNCERTAIN",
            }
        return _operation_view(operation)

    def _bound(self, record):
        if record.get("providerIdentity") != self.identities.get(record["providerId"]):
            raise LabError("PROVIDER_IDENTITY_CHANGED")
        asset = self.registry._asset(record["assetId"])
        if record.get("assetIdentity") != self._asset_identity(asset):
            raise LabError("ASSET_IDENTITY_CHANGED")

    @staticmethod
    def _asset_identity(asset):
        identity = asset.get("identity")
        if type(identity) is not dict or not any(
            identity.get(key) for key in ("serial", "deviceId", "digest")
        ):
            raise LabError("ASSET_IDENTITY_UNRESOLVED")
        return digest(identity)

    def _record(self, reservation_id, *, owner):
        with self._lock:
            self.backing.assert_current()
            return self.registry.get(reservation_id, owner=owner)

    def get(self, reservation_id, *, owner):
        return _lease_view(self._record(reservation_id, owner=owner))

    def options(self, asset_id, *, owner):
        """An observation of request eligibility, never a lease or runtime grant."""
        if not opaque_id(asset_id) or not opaque_id(owner):
            raise LabError("FORBIDDEN")
        with self._lock:
            self.backing.assert_current()
            base = {
                "contractVersion": "1.0",
                "assetId": asset_id,
                "principal": owner,
                "observedAt": self.registry.clock(),
                "runtimeAdmission": "unavailable",
                "physicalCommands": [],
                "maximumDurationSeconds": self.registry.max_lease_seconds,
            }
            if not self.enabled:
                return {
                    **base,
                    "status": "unavailable",
                    "providerId": None,
                    "evidenceScope": "unavailable",
                    "scopes": [
                        {
                            "scope": scope,
                            "eligible": False,
                            "reasons": ["PROVIDER_RESERVATION_NOT_ADMITTED"],
                        }
                        for scope in ("observe", "stimulate", "destructive")
                    ],
                }
            asset = self.registry._asset(asset_id)
            try:
                self._asset_identity(asset)
                identified = True
            except LabError:
                identified = False
            granted = self.policy.scopes_for(owner, asset_id)
            descriptor = next(
                (
                    d
                    for d in self.installation_descriptors
                    if d["providerId"] == asset["providerId"]
                ),
                {},
            )
            scopes = []
            for scope in ("observe", "stimulate", "destructive"):
                reasons = []
                if scope not in granted:
                    reasons.append("FORBIDDEN")
                if scope not in asset.get("capabilities", []):
                    reasons.append("CAPABILITY_UNSUPPORTED")
                if not identified:
                    reasons.append("ASSET_IDENTITY_UNRESOLVED")
                if asset.get("available") is not True:
                    reasons.append("ASSET_AVAILABILITY_UNCONFIRMED")
                scopes.append(
                    {"scope": scope, "eligible": not reasons, "reasons": reasons}
                )
            return {
                **base,
                "status": "configured",
                "providerId": asset["providerId"],
                "evidenceScope": descriptor.get("evidenceScope", "unknown"),
                "scopes": scopes,
            }

    def history(self, *, owner):
        """Bounded local ownership history; reading never inspects a provider."""
        if not opaque_id(owner):
            raise LabError("FORBIDDEN")
        with self._lock, self.registry._lock:
            self.backing.assert_current()
            observed_at = self.registry.clock()
            owned_records = [
                self.registry.records[identity]
                for identity in sorted(self.registry.records)
                if self.registry.records[identity]["owner"] == owner
            ]
            expired = [
                record
                for record in owned_records
                if record["status"] == "owned" and observed_at >= record["expiry"]
            ]
            for record in expired:
                record["status"] = "expired"
            if expired:
                # The ledger is bounded but a write per elapsed lease would
                # rewrite it up to 1,000 times during one read. Commit once.
                self.registry._save()
            records = []
            for record in owned_records:
                terminal = record["status"] in {"released", "expired"}
                installed = record.get("providerIdentity") is not None and record.get(
                    "providerIdentity"
                ) == self.identities.get(record["providerId"])
                grant = record["scope"] in self.policy.scopes_for(
                    owner, record["assetId"]
                )
                records.append(
                    {
                        **_lease_view(record),
                        "requests": {
                            "renew": installed
                            and grant
                            and record["status"] == "owned",
                            "release": self.enabled
                            and (
                                terminal or (installed and record["status"] == "owned")
                            ),
                            "reconcile": installed and not terminal,
                        },
                    }
                )
            return {
                "contractVersion": "1.0",
                "principal": owner,
                "observedAt": observed_at,
                "items": records,
                "runtimeAdmission": "unavailable",
                "physicalCommands": [],
            }

    def get_operation(self, operation_id, *, owner):
        with self.store.tx() as db:
            record = self._read_operation(operation_id, db)
            if record["principal"] != owner:
                raise LabError("FORBIDDEN")
            return self._receipt_view(record)

    def reserve(self, asset_id, *, owner, key, scope="observe", duration=30):
        route, payload = (
            "POST /assets/" + asset_id + "/reservations",
            {"scope": scope, "durationSeconds": duration},
        )
        with self._lock:
            previous = self._prior(owner, route, key, payload)
            if previous is not None:
                return previous
            self.backing.assert_current()
            self.policy.require(owner, asset_id, scope)
            self.registry._duration(duration)
            asset = self.registry._asset(asset_id)
            asset_identity = self._asset_identity(asset)
            if scope not in asset.get("capabilities", []):
                raise LabError("CAPABILITY_UNSUPPORTED")
            identity = self.identities[asset["providerId"]]
            operation, is_new = self._accept(
                owner, route, key, payload, "lab_reserve", uid()
            )
            if not is_new:
                return operation

            def delegate():
                self.backing.assert_current()
                current = self.policy.require(owner, asset_id, scope)
                return self.registry.reserve(
                    asset_id,
                    owner=owner,
                    duration=duration,
                    scope=scope,
                    granted_scopes=current,
                    reservation_id=operation["reservationId"],
                    provider_identity=identity,
                    asset_identity=asset_identity,
                )

            return self._perform(operation, delegate)

    def renew(self, reservation_id, *, owner, key, fence, duration=30):
        route = "POST /reservations/" + reservation_id + "/renewals"
        payload = {"fencingIdentity": fence, "durationSeconds": duration}
        with self._lock:
            previous = self._prior(owner, route, key, payload)
            if previous is not None:
                return previous
            record = self._record(reservation_id, owner=owner)
            self.policy.require(owner, record["assetId"], record["scope"])
            self._bound(record)
            if record["status"] != "owned":
                raise LabError("OWNERSHIP_UNCERTAIN")
            if fence != record["fencingIdentity"]:
                raise LabError("STALE_FENCING_IDENTITY")
            if self.registry._duration(duration) <= record["expiry"]:
                raise LabError("LEASE_NOT_EXTENSION")
            operation, is_new = self._accept(
                owner, route, key, payload, "lab_renew", reservation_id
            )
            if not is_new:
                return operation

            def delegate():
                self.backing.assert_current()
                scopes = self.policy.require(owner, record["assetId"], record["scope"])
                self._bound(record)
                return self.registry.renew(
                    reservation_id,
                    owner=owner,
                    expected_fencing_identity=fence,
                    duration=duration,
                    granted_scopes=scopes,
                )

            return self._perform(operation, delegate)

    def release(self, reservation_id, *, owner, key):
        route = "DELETE /reservations/" + reservation_id
        with self._lock:
            previous = self._prior(owner, route, key, {})
            if previous is not None:
                return previous
            record = self._record(reservation_id, owner=owner)
            if record["status"] not in {"released", "expired"}:
                self._bound(record)
            if record["status"] not in {"owned", "released", "expired"}:
                raise LabError("OWNERSHIP_UNCERTAIN")
            operation, is_new = self._accept(
                owner, route, key, {}, "lab_release", reservation_id
            )
            if not is_new:
                return operation

            def delegate():
                self.backing.assert_current()
                if record["status"] not in {"released", "expired"}:
                    self._bound(record)
                return self.registry.release(reservation_id, owner=owner)

            return self._perform(operation, delegate)

    def reconcile(self, reservation_id, *, owner, key):
        route = "POST /reservations/" + reservation_id + "/reconciliations"
        with self._lock:
            previous = self._prior(owner, route, key, {})
            if previous is not None:
                return previous
            record = self._record(reservation_id, owner=owner)
            if record["status"] not in {"released", "expired"}:
                self._bound(record)
            operation, is_new = self._accept(
                owner, route, key, {}, "lab_reconcile", reservation_id
            )
            if not is_new:
                return operation

            def delegate():
                self.backing.assert_current()
                if record["status"] not in {"released", "expired"}:
                    self._bound(record)
                return self.registry.reconcile(reservation_id, owner=owner)

            return self._perform(operation, delegate)

    def require_authority(self, reservation_id, *, owner, action):
        with self._lock:
            record = self._record(reservation_id, owner=owner)
            if record["status"] != "owned":
                raise LabError("OWNERSHIP_UNCERTAIN")
            scopes = self.policy.require(owner, record["assetId"], action)
            observed = self.registry.require_authority(
                reservation_id, owner=owner, action=action, granted_scopes=scopes
            )
            self._bound(record)
            return _lease_view(observed)
