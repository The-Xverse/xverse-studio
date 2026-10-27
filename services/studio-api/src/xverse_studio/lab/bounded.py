"""Bounded calls to already-installed objects; no discovery, loading or device IO.

One outstanding call per adapter, with no queue. A timed-out provider thread is
not killed or replaced. Its capacity remains occupied until it really returns;
late observations are discarded and cannot grant ownership.
"""

from copy import deepcopy
import math
import threading
from xverse_studio.lab import LabError
from xverse_studio.lab.assets import project_asset


def _response(name, value):
    if name == "inventory":
        if type(value) is not list or len(value) > 1000:
            raise LabError("PROVIDER_RESPONSE_INVALID")
        projected = [project_asset(asset) for asset in value]
        if any(asset is None or asset["observationTruncated"] for asset in projected):
            raise LabError("PROVIDER_RESPONSE_INVALID")
        return projected
    if type(value) is not dict or value.get("status") not in {
        "owned",
        "unknown",
        "released",
        "expired",
    }:
        raise LabError("PROVIDER_RESPONSE_INVALID")
    projected = {"status": value["status"]}
    for key in ("owner", "scope", "fencingIdentity"):
        if key in value:
            if type(value[key]) is not str or not 0 < len(value[key]) <= 256:
                raise LabError("PROVIDER_RESPONSE_INVALID")
            projected[key] = value[key]
    if "expiry" in value:
        expiry = value["expiry"]
        if type(expiry) not in (int, float) or not math.isfinite(expiry):
            raise LabError("PROVIDER_RESPONSE_INVALID")
        projected["expiry"] = expiry
    return projected


class BoundedLeaseProvider:
    def __init__(self, provider, *, timeout=1.0, guard=None):
        if (
            type(timeout) not in (int, float)
            or not math.isfinite(timeout)
            or not 0 < timeout <= 5
        ):
            raise LabError("PROVIDER_CONFIG_INVALID")
        self._provider = provider
        self._timeout = timeout
        self._slot = threading.BoundedSemaphore(1)
        if guard is not None and not callable(guard):
            raise LabError("PROVIDER_CONFIG_INVALID")
        self._guard = guard

    def _call(self, name, *args):
        if not self._slot.acquire(blocking=False):
            raise LabError("PROVIDER_CALL_UNSETTLED")
        completed = threading.Event()
        result = {}
        try:
            copied = deepcopy(args)
            callback = getattr(self._provider, name)
        except BaseException:
            self._slot.release()
            raise

        def invoke():
            try:
                if self._guard is not None:
                    self._guard(name, copied)
                result["value"] = _response(name, callback(*copied))
            except BaseException as error:
                # Only the versioned code can leave the provider boundary.
                allowed = {
                    "RESOURCE_BUSY",
                    "STALE_FENCING_IDENTITY",
                    "CAPABILITY_UNSUPPORTED",
                    "FORBIDDEN",
                    "OWNERSHIP_UNCERTAIN",
                    "PROVIDER_RESPONSE_INVALID",
                }
                result["error"] = (
                    error.code
                    if isinstance(error, LabError)
                    and type(error.code) is str
                    and error.code in allowed
                    else "PROVIDER_OPERATION_UNKNOWN"
                )
            finally:
                self._slot.release()
                completed.set()

        worker = threading.Thread(target=invoke, name="studio-lease-call", daemon=True)
        try:
            worker.start()
        except BaseException:
            self._slot.release()
            raise
        if not completed.wait(self._timeout):
            raise LabError("PROVIDER_OPERATION_UNKNOWN")
        if "error" in result:
            raise LabError(result["error"])
        return result["value"]

    def inventory(self):
        return self._call("inventory")

    def reserve(self, asset, scope, owner, deadline):
        return self._call("reserve", asset, scope, owner, deadline)

    def renew(self, reservation, fence, deadline, authority):
        return self._call("renew", reservation, fence, deadline, authority)

    def release(self, reservation, authority):
        return self._call("release", reservation, authority)

    def inspect_reservation(self, reservation):
        return self._call("inspect_reservation", reservation)
