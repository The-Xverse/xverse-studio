"""Versioned descriptor core. Metadata is bounded JSON, never executable input."""

from __future__ import annotations

import json
import math
from typing import Annotated, Literal

from jsonschema import Draft202012Validator, SchemaError
from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    ValidationError,
    field_validator,
    model_validator,
)

from xverse_studio.security.files import check_text
from xverse_studio.storage.core import Problem, canonical

MAX_DESCRIPTOR_BYTES = 64 * 1024
MAX_DESCRIPTOR_NODES = 4096
MAX_DESCRIPTOR_DEPTH = 16
ProviderId = Annotated[str, Field(pattern=r"^[A-Za-z0-9][A-Za-z0-9._-]{0,127}$")]
Text = Annotated[str, Field(min_length=1, max_length=256)]
Names = Annotated[list[Text], Field(min_length=1, max_length=128)]
Number = Annotated[int | float, Field(ge=0)]


def invalid_descriptor():
    return Problem(
        "PROVIDER_DESCRIPTOR_INVALID",
        "The installed provider descriptor does not satisfy the bounded v1 contract. Repair its native installation before execution.",
    )


def bounded_json(value):
    nodes, content_bytes = 0, 0

    def visit(item, depth, ancestors):
        nonlocal nodes, content_bytes
        nodes += 1
        if nodes > MAX_DESCRIPTOR_NODES or depth > MAX_DESCRIPTOR_DEPTH:
            raise ValueError()
        kind = type(item)
        if kind in (dict, list):
            if id(item) in ancestors or len(item) > MAX_DESCRIPTOR_NODES:
                raise ValueError()
            ancestors = ancestors | {id(item)}
            if kind is dict:
                for key, child in item.items():
                    if type(key) is not str:
                        raise ValueError()
                    visit(key, depth + 1, ancestors)
                    visit(child, depth + 1, ancestors)
            else:
                for child in item:
                    visit(child, depth + 1, ancestors)
        elif kind is str:
            if len(item) > MAX_DESCRIPTOR_BYTES:
                raise ValueError()
            content_bytes += len(item.encode("utf-8"))
        elif kind in (int, float):
            if kind is float and not math.isfinite(item):
                raise ValueError()
            content_bytes += len(str(item))
        elif item is not None and kind is not bool:
            raise ValueError()
        if content_bytes > MAX_DESCRIPTOR_BYTES:
            raise ValueError()

    visit(value, 0, set())
    raw = canonical(value)
    if len(raw.encode("utf-8")) > MAX_DESCRIPTOR_BYTES:
        raise ValueError()
    check_text(raw)
    return raw


class DescriptorCore(BaseModel):
    # Provider extensions are retained; they have already passed bounded JSON
    # validation before admission. No coercion or execution is permitted here.
    model_config = ConfigDict(extra="allow", strict=True, allow_inf_nan=False)


class CapabilityDescriptor(DescriptorCore):
    kind: Text
    targetClass: Text
    legalStates: Names
    parametersSchema: dict
    authorityRequirements: Names
    physicalEffects: bool
    maxDurationSeconds: Annotated[int | float, Field(gt=0)] | None = None

    @field_validator("legalStates", "authorityRequirements")
    @classmethod
    def unique_names(cls, value):
        if len(value) != len(set(value)):
            raise ValueError("Repeated capability names are ambiguous.")
        return value

    @field_validator("parametersSchema")
    @classmethod
    def closed_object_schema(cls, value):
        if (
            value.get("type") != "object"
            or value.get("additionalProperties") is not False
            or value.get("$schema", Draft202012Validator.META_SCHEMA["$id"])
            != Draft202012Validator.META_SCHEMA["$id"]
        ):
            raise ValueError("Capabilities require a closed object parameter schema.")
        try:
            # Validate against this class's bundled meta-schema. This checks
            # schema syntax without resolving the provider's instance $refs.
            Draft202012Validator.check_schema(value)
        except SchemaError:
            raise ValueError("The capability parameter schema is invalid.") from None
        return value


class ProviderDescriptor(DescriptorCore):
    providerId: ProviderId
    providerVersion: Text
    contractVersion: Literal["1.0"]
    implementationDigest: str = Field(pattern=r"^sha256:[a-f0-9]{64}$")
    supportedHostOS: Names
    architectures: Names
    operations: Names
    capabilityRecords: list[CapabilityDescriptor] = Field(min_length=1, max_length=128)
    limits: dict[Text, Number] = Field(min_length=1, max_length=128)
    evidenceScope: Text
    available: bool
    hostCompatible: bool

    @field_validator("supportedHostOS", "architectures", "operations")
    @classmethod
    def unique_names(cls, value):
        if len(value) != len(set(value)):
            raise ValueError("Repeated provider names are ambiguous.")
        return value

    @model_validator(mode="after")
    def scoped_operations(self):
        scopes = [(c.kind, c.targetClass) for c in self.capabilityRecords]
        if len(scopes) != len(set(scopes)) or set(self.operations) != {
            c.kind for c in self.capabilityRecords
        }:
            raise ValueError(
                "Each declared operation requires unambiguous capability scopes."
            )
        duration, concurrent = (
            self.limits.get("maxDurationSeconds"),
            self.limits.get("maxConcurrentRuns"),
        )
        if (
            duration is None
            or duration <= 0
            or type(concurrent) is not int
            or concurrent < 1
        ):
            raise ValueError(
                "Execution requires a positive duration and integral concurrency bound."
            )
        return self


class UnavailableProviderDescriptor(DescriptorCore):
    providerId: ProviderId
    providerVersion: Text
    contractVersion: Text
    available: Literal[False]
    supportedHostOS: list[Text] = Field(max_length=128)
    architectures: list[Text] = Field(max_length=128)
    operations: list[Text] = Field(max_length=0)
    blockedReasons: list[dict[str, str]] = Field(min_length=1, max_length=32)


class ProviderPage(DescriptorCore):
    items: list[ProviderDescriptor | UnavailableProviderDescriptor]
    nextCursor: None


def admit_descriptor(descriptor):
    if not isinstance(descriptor, dict) or descriptor.get("contractVersion") != "1.0":
        raise Problem(
            "PROVIDER_VERSION_INCOMPATIBLE",
            "The installed provider contract is incompatible with Studio v1.",
        )
    try:
        observation = json.loads(bounded_json(descriptor))
        ProviderDescriptor.model_validate(observation)
    except (
        ValueError,
        TypeError,
        UnicodeError,
        OverflowError,
        RecursionError,
        ValidationError,
        Problem,
    ):
        raise invalid_descriptor() from None
    # An independent JSON observation cannot be changed through a provider's
    # returned mutable dictionary. Preserve every extension and exact JSON type.
    return observation


def unavailable_descriptor(provider_id, code):
    return {
        "providerId": provider_id,
        "providerVersion": "unavailable",
        "contractVersion": "unavailable",
        "discoveryVersion": "1.0",
        "name": provider_id,
        "available": False,
        "hostCompatible": False,
        "supportedHostOS": [],
        "architectures": [],
        "operations": [],
        "maturity": "unavailable",
        "evidenceScope": "unavailable",
        "blockedReasons": [
            {
                "code": code,
                "message": "The installed provider description cannot be verified. Repair its native installation and preflight again.",
            }
        ],
    }
