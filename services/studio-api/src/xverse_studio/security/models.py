"""Strict base for untrusted request bodies, shared by every layer that validates input."""

import json
from typing import Annotated, Any

from pydantic import AfterValidator, BaseModel, ConfigDict, model_validator


class Body(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True, allow_inf_nan=False)

    @model_validator(mode="after")
    def finite_values(self):
        # Any-valued objects and dictionary keys require the same JSON boundary
        # as typed scalars. Inspect without rewriting opaque authored values.
        finite_json(self.model_dump())
        return self


def finite_json(value):
    """Inspect opaque JSON without coercion, before any resource lookup/effect."""
    try:
        json.dumps(value, ensure_ascii=False, allow_nan=False).encode("utf-8")
    except (TypeError, ValueError, RecursionError, OverflowError):
        raise ValueError("Use finite UTF-8 JSON values.") from None
    return value


JsonObject = Annotated[dict[str, Any], AfterValidator(finite_json)]
