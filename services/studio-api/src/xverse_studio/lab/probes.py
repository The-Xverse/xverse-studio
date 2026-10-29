"""Durable explicit observation requests; no discovery, lease or runtime authority."""

from copy import deepcopy
import json
import math
import re
import threading

from xverse_studio.lab import LabError
from xverse_studio.lab.assets import opaque_id, public_text
from xverse_studio.lab.probe_configuration import (
    LabProbeConfiguration,
    ProbeAuthority,
    sha256_identity,
)
from xverse_studio.storage.core import Problem, canonical, digest, uid

MAX_OPERATION_BYTES = 16384
STATUSES = {"accepted", "delegated", "completed", "rejected", "unknown"}


def finite(value):
    return type(value) in (int, float) and math.isfinite(value)


def observation(value, identity, allowed_resources):
    """Closed public projection; neither unknown fields nor private bindings leave host code."""
    if type(value) is not dict or value.get("status") not in (
        "observed",
        "unavailable",
        "unknown",
    ):
        raise LabError("PROBE_RESPONSE_INVALID")
    if value.get("identityDigest") != identity:
        raise LabError("ASSET_IDENTITY_CHANGED")
    resources = value.get("contactedResources")
    if (
        type(resources) is not list
        or len(resources) > 8
        or any(
            not opaque_id(item) or item not in allowed_resources for item in resources
        )
        or len(set(resources)) != len(resources)
    ):
        raise LabError("PROBE_RESPONSE_INVALID")
    source = value.get("sourceTime")
    if source is not None:
        if (
            type(source) is not dict
            or not opaque_id(source.get("clockDomain"))
            or type(source.get("tick")) is not str
            or re.fullmatch(r"-?(?:0|[1-9][0-9]{0,38})", source["tick"]) is None
            or source.get("unit") not in ("ns", "us", "ms", "s")
        ):
            raise LabError("PROBE_RESPONSE_INVALID")
        uncertainty = source.get("uncertaintySeconds")
        if uncertainty is not None and (not finite(uncertainty) or uncertainty < 0):
            raise LabError("PROBE_RESPONSE_INVALID")
        source = {key: source[key] for key in ("clockDomain", "tick", "unit")}
        source["uncertaintySeconds"] = uncertainty
    metadata = value.get("metadata", {})
    if type(metadata) is not dict:
        raise LabError("PROBE_RESPONSE_INVALID")
    codes = value.get("diagnostics", [])
    if (
        type(codes) is not list
        or len(codes) > 16
        or any(
            type(code) is not str or re.fullmatch(r"[A-Z][A-Z0-9_]{0,63}", code) is None
            for code in codes
        )
    ):
        raise LabError("PROBE_RESPONSE_INVALID")
    return dict(
        status=value["status"],
        identityDigest=identity,
        contactedResources=list(resources),
        sourceTime=source,
        metadata={
            key: public_text(metadata.get(key))
            for key in ("firmwareVersion", "artifactRevision")
        },
        diagnostics=list(codes),
    )


class LabProbes:
    def __init__(self, store, configuration=None):
        if configuration is None:
            configuration = LabProbeConfiguration((), ProbeAuthority())
        if not isinstance(configuration, LabProbeConfiguration):
            raise LabError("PROBE_CONFIG_INVALID")
        self.store, self.configuration = store, configuration
        self._lock = threading.RLock()
        self._installations = {
            item.asset_id: item for item in configuration.installations
        }
        self._pins = {
            item.asset_id: item.binding_digest() for item in configuration.installations
        }
        self._slots = {
            item.provider_id: threading.BoundedSemaphore(1)
            for item in configuration.installations
        }
        self._uncertain = set()
        with store.tx() as db:
            rows = db.execute(
                "SELECT id FROM records WHERE kind='operation' AND json_extract(body,'$.kind')='lab_probe' LIMIT ?",
                (configuration.max_operations + 1,),
            ).fetchall()
            if len(rows) > configuration.max_operations:
                raise LabError("LIMIT_EXCEEDED")
            for (identity,) in rows:
                record = self._read(identity, db)
                if record["status"] in ("accepted", "delegated"):
                    record.update(
                        status="unknown", result=None, code="PROBE_INTERRUPTED"
                    )
                    store.put("operation", identity, record, db)

    def discovery(self):
        return dict(
            contractVersion="1.0",
            status="configured" if self._installations else "unavailable",
            installations=[
                item.descriptor() for item in self.configuration.installations
            ],
            scope="observe",
            grants="server_owned_exact_observation_permission",
            runtimeAdmission="unavailable",
            physicalCommands=[],
            limits=dict(
                installations=32,
                resourcesPerBinding=8,
                providerCallSeconds=self.configuration.call_timeout,
                outstandingCallsPerObservationProvider=1,
                queuedCalls=0,
                operations=self.configuration.max_operations,
                operationBytes=MAX_OPERATION_BYTES,
            ),
        )

    def _installed(self, asset_id):
        item = self._installations.get(asset_id)
        if item is None:
            raise LabError("PROBE_NOT_ADMITTED")
        if item.binding_digest() != self._pins.get(asset_id):
            raise LabError("PROBE_BINDING_CHANGED")
        return item

    def options(self, asset_id, *, owner):
        if not opaque_id(asset_id) or not opaque_id(owner):
            raise LabError("FORBIDDEN")
        result = dict(
            contractVersion="1.0",
            assetId=asset_id,
            principal=owner,
            scope="observe",
            observedAt=self._now(),
            allowed=False,
            installation=None,
            runtimeAdmission="unavailable",
            physicalCommands=[],
        )
        try:
            item = self._installed(asset_id)
            result["installation"] = item.descriptor()
            self.configuration.authority.require(owner, asset_id)
        except LabError as error:
            result["reason"] = error.code
        else:
            result.update(allowed=True, reason=None)
        return result

    def _now(self):
        value = self.configuration.clock()
        if not finite(value):
            raise LabError("PROBE_CLOCK_UNAVAILABLE")
        return value

    def _read(self, identity, db):
        row = db.execute(
            "SELECT body FROM records WHERE kind='operation' AND id=?", (identity,)
        ).fetchone()
        if row is None:
            raise Problem("NOT_FOUND", "The observation operation was not found.", 404)
        if len(row[0].encode()) > MAX_OPERATION_BYTES:
            raise LabError("PROBE_STATE_UNAVAILABLE")
        try:
            record = json.loads(row[0])
            if (
                type(record) is not dict
                or record.get("kind") != "lab_probe"
                or record.get("operationId") != identity
                or record.get("status") not in STATUSES
                or any(
                    not opaque_id(record.get(key))
                    for key in ("operationId", "principal", "assetId", "providerId")
                )
                or record.get("scope") != "observe"
                or not sha256_identity(record.get("bindingDigest"))
                or not sha256_identity(record.get("identityDigest"))
                or record.get("evidenceScope")
                not in ("fixture", "admitted_integration")
                or record.get("route")
                != "POST /assets/" + record["assetId"] + "/probes"
                or not finite(record.get("createdAt"))
                or not finite(record.get("deadline"))
                or not 0 < record["deadline"] - record["createdAt"] <= 5
                or "result" not in record
                or type(record.get("contactedResources")) is not list
                or not 1 <= len(record["contactedResources"]) <= 8
                or any(not opaque_id(value) for value in record["contactedResources"])
                or len(set(record["contactedResources"]))
                != len(record["contactedResources"])
            ):
                raise ValueError()
            if record.get("result") is not None:
                projected = observation(
                    record["result"],
                    record["identityDigest"],
                    record["contactedResources"],
                )
                if not finite(record["result"].get("receivedAt")):
                    raise ValueError()
                projected["receivedAt"] = record["result"]["receivedAt"]
                record["result"] = projected
            if record["status"] == "completed" and (
                record.get("result") is None or record["result"]["status"] == "unknown"
            ):
                raise ValueError()
            if (
                record["status"] in ("accepted", "delegated", "rejected")
                and record["result"] is not None
            ):
                raise ValueError()
            if (
                record["status"] == "unknown"
                and record["result"] is not None
                and record["result"]["status"] != "unknown"
            ):
                raise ValueError()
            return record
        except (ValueError, KeyError, TypeError, RecursionError, LabError):
            raise LabError("PROBE_STATE_UNAVAILABLE") from None

    def _view(self, record):
        result = {
            key: deepcopy(record[key])
            for key in (
                "operationId",
                "kind",
                "principal",
                "assetId",
                "providerId",
                "scope",
                "bindingDigest",
                "identityDigest",
                "evidenceScope",
                "createdAt",
                "deadline",
                "status",
                "result",
            )
        }
        if "code" in record:
            code = record["code"]
            result["code"] = (
                code
                if type(code) is str and re.fullmatch(r"[A-Z][A-Z0-9_]{0,63}", code)
                else "PROBE_UNKNOWN"
            )
        if record["operationId"] in self._uncertain:
            result.update(status="unknown", result=None, code="PROBE_RECORD_UNCERTAIN")
        result.update(runtimeAdmission="unavailable", physicalCommands=[])
        return result

    def get_operation(self, identity, *, owner):
        with self.store.tx() as db:
            record = self._read(identity, db)
        if record["principal"] != owner:
            raise LabError("FORBIDDEN")
        return self._view(record)

    def _prior(self, owner, route, key, payload):
        if type(key) is not str or not 1 <= len(key) <= 128:
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
                        "This key identifies a different observation request.",
                        409,
                    )
                identity = json.loads(row[1])["operationId"]
                record = self._read(identity, db)
                if record["principal"] != owner or record["route"] != route:
                    raise LabError("PROBE_STATE_UNAVAILABLE")
                return self._view(record)

    def request(self, asset_id, *, owner, key, expected_binding, scope="observe"):
        if (
            not opaque_id(asset_id)
            or not opaque_id(owner)
            or scope != "observe"
            or not sha256_identity(expected_binding)
        ):
            raise LabError("PROBE_REQUEST_INVALID")
        route = "POST /assets/" + asset_id + "/probes"
        payload = dict(scope=scope, expectedBindingDigest=expected_binding)
        # Exact historical receipt remains readable without a current installation/grant.
        # It never delegates again or becomes current authority.
        with self._lock:
            prior = self._prior(owner, route, key, payload)
            if prior is not None:
                return prior
            item = self._installed(asset_id)
            if expected_binding != self._pins[asset_id]:
                raise LabError("PROBE_BINDING_CHANGED")
            generation = self.configuration.authority.require(owner, asset_id)
            created = self._now()
            deadline = created + self.configuration.call_timeout
            if not finite(deadline) or not 0 < deadline - created <= 5:
                raise LabError("PROBE_CLOCK_UNAVAILABLE")

            def accept(db):
                count = db.execute(
                    "SELECT count(*) FROM records WHERE kind='operation' AND json_extract(body,'$.kind')='lab_probe'"
                ).fetchone()[0]
                if count >= self.configuration.max_operations:
                    raise LabError("LIMIT_EXCEEDED")
                record = dict(
                    operationId=uid("op-"),
                    kind="lab_probe",
                    principal=owner,
                    route=route,
                    assetId=asset_id,
                    providerId=item.provider_id,
                    scope="observe",
                    bindingDigest=expected_binding,
                    identityDigest=item.identity_digest,
                    evidenceScope=item.evidence_scope,
                    contactedResources=list(item.contacted_resources),
                    createdAt=created,
                    deadline=deadline,
                    status="accepted",
                    result=None,
                )
                self.store.put("operation", record["operationId"], record, db)
                return dict(operationId=record["operationId"])

            receipt, is_new = self.store.idempotent(owner, route, key, payload, accept)
            with self.store.tx() as db:
                record = self._read(receipt["operationId"], db)
            if not is_new:
                return self._view(record)
        return self._perform(record, item, generation)

    def _guard(self, record, item, generation):
        if (
            self._installed(item.asset_id) is not item
            or item.binding_digest() != record["bindingDigest"]
        ):
            raise LabError("PROBE_BINDING_CHANGED")
        if (
            self.configuration.authority.require(record["principal"], item.asset_id)
            != generation
        ):
            raise LabError("PROBE_AUTHORITY_CHANGED")
        if self._now() >= record["deadline"]:
            raise LabError("PROBE_DEADLINE_EXCEEDED")

    def _call(self, record, item, generation):
        slot = self._slots[item.provider_id]
        if not slot.acquire(blocking=False):
            raise LabError("PROVIDER_CALL_UNSETTLED")
        completed, outcome = threading.Event(), {}

        def invoke():
            try:
                binding = item.provider_binding()
                self._guard(record, item, generation)
                raw = item.provider.probe(binding, "observe", record["deadline"])
                outcome["result"] = observation(
                    raw, item.identity_digest, item.contacted_resources
                )
            except BaseException as error:
                allowed = {
                    "FORBIDDEN",
                    "RESOURCE_BUSY",
                    "CAPABILITY_UNSUPPORTED",
                    "PROBE_BINDING_CHANGED",
                    "PROBE_AUTHORITY_CHANGED",
                    "PROBE_DEADLINE_EXCEEDED",
                    "ASSET_IDENTITY_CHANGED",
                    "PROBE_RESPONSE_INVALID",
                }
                code = error.code if isinstance(error, LabError) else None
                outcome["code"] = (
                    code if type(code) is str and code in allowed else "PROBE_UNKNOWN"
                )
            finally:
                slot.release()
                completed.set()

        worker = threading.Thread(
            target=invoke, name="studio-observation-call", daemon=True
        )
        try:
            worker.start()
        except BaseException:
            slot.release()
            raise
        if not completed.wait(self.configuration.call_timeout):
            raise LabError("PROBE_UNKNOWN")
        if "code" in outcome:
            raise LabError(outcome["code"])
        self._guard(record, item, generation)
        return {**outcome["result"], "receivedAt": self._now()}

    def _perform(self, record, item, generation):
        try:
            record.update(status="delegated")
            self.store.put("operation", record["operationId"], record)
            result = self._call(record, item, generation)
            record.update(
                status="unknown" if result["status"] == "unknown" else "completed",
                result=result,
            )
            if len(canonical(record).encode()) > MAX_OPERATION_BYTES:
                raise LabError("PROBE_RESPONSE_INVALID")
        except Exception as error:
            code = error.code if isinstance(error, LabError) else "PROBE_UNKNOWN"
            record.update(
                status="rejected" if code == "PROVIDER_CALL_UNSETTLED" else "unknown",
                result=None,
                code=code,
            )
        try:
            self.store.put("operation", record["operationId"], record)
        except Exception:
            # A failed final write may have committed; verify the exact stored result.
            try:
                with self.store.tx() as db:
                    observed = self._read(record["operationId"], db)
                if observed == record:
                    return self._view(observed)
            except Exception:
                pass
            self._uncertain.add(record["operationId"])
            record.update(status="unknown", result=None, code="PROBE_RECORD_UNCERTAIN")
            try:
                self.store.put("operation", record["operationId"], record)
            except Exception:
                pass
        return self._view(record)
