"""Strict read-only interpretation from installed adapters, never imported code."""

from copy import deepcopy
from typing import Literal
from pydantic import Field, model_validator
from xverse_studio.security.models import Body


class FaultPosition(Body):
    faultId: str = Field(pattern=r"^[a-z][a-z0-9]*(?:-[a-z0-9]+)*$", max_length=63)
    activationTick: str = Field(pattern=r"^(?:0|[1-9][0-9]{0,30})$")
    recoveryTick: str = Field(pattern=r"^(?:0|[1-9][0-9]{0,30})$")

    @model_validator(mode="after")
    def ordered(self):
        if int(self.recoveryTick) <= int(self.activationTick):
            raise ValueError("Invalid interval")
        return self


class ClockContext(Body):
    contractVersion: Literal["1.0"]
    codec: str = Field(pattern=r"^[A-Za-z][A-Za-z0-9._/-]{0,127}$")
    clockDomain: str = Field(min_length=1, max_length=128)
    tickUnit: Literal["microsecond"]
    epoch: str = Field(pattern=r"^[a-z][a-z0-9-]{0,127}$")
    evidenceScope: str = Field(pattern=r"^[a-z][a-z0-9_]{0,127}$")
    sourceProviderId: str = Field(min_length=1, max_length=128)
    sourceVersion: str = Field(min_length=1, max_length=64)
    eventKinds: list[str] = Field(min_length=1, max_length=16)
    eventTickField: str = Field(pattern=r"^[a-zA-Z][a-zA-Z0-9_]{0,63}$")
    faults: list[FaultPosition] = Field(min_length=1, max_length=32)

    @model_validator(mode="after")
    def unique(self):
        if len(set(self.eventKinds)) != len(self.eventKinds) or any(
            not isinstance(k, str) or not k.startswith("fault.") or len(k) > 128
            for k in self.eventKinds
        ):
            raise ValueError("Invalid event kinds")
        if len({f.faultId for f in self.faults}) != len(self.faults):
            raise ValueError("Ambiguous faults")
        return self


def inspect_context(callback, run, snapshot, scenario, declared):
    if (
        callback is None
        or run.get("effectivePlanDigest") != snapshot.get("planDigest")
        or run.get("effectiveSemanticDigest") != snapshot.get("semanticDigest")
    ):
        return None, []
    try:
        value = callback(deepcopy(run), deepcopy(snapshot))
        if value is None:
            return None, []
        context = ClockContext.model_validate(value).model_dump()
        if (
            context["sourceProviderId"] != run.get("providerId")
            or context["sourceProviderId"] != snapshot.get("providerId")
            or context["sourceVersion"]
            != snapshot.get("providerIdentity", {}).get("providerVersion")
            or context["evidenceScope"] != run.get("evidenceScope")
            or context["clockDomain"] not in declared
            or {f["faultId"] for f in context["faults"]}
            != {f["id"] for f in scenario["spec"].get("faults", [])}
        ):
            raise ValueError("Foreign context")
        return context, []
    except Exception:
        return None, [{"code": "TIMELINE_PROVIDER_CLOCK_UNAVAILABLE"}]


def recorded_unit(context, record, tick, clock):
    source, original, payload = (
        record.get("source"),
        record.get("sourceTime"),
        record.get("payload"),
    )
    if not context or not all(isinstance(v, dict) for v in [source, original, payload]):
        return None
    if (
        source.get("providerId") == context["sourceProviderId"]
        and source.get("version") == context["sourceVersion"]
        and clock == context["clockDomain"]
        and original.get("resolution") == context["tickUnit"]
        and record.get("type") in context["eventKinds"]
        and payload.get("faultId") in {f["faultId"] for f in context["faults"]}
        and tick is not None
        and tick >= 0
        and original.get("tick") == str(tick)
        and payload.get(context["eventTickField"]) == str(tick)
    ):
        return context["tickUnit"]
    return None
