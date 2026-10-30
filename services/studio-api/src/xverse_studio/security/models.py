"""Strict base for untrusted request bodies, shared by every layer that validates input."""

import json
from typing import Annotated, Any

from pydantic import AfterValidator, BaseModel, ConfigDict


class Body(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True, allow_inf_nan=False)


def finite_json(value):
    """Inspect opaque JSON without coercion, before any resource lookup/effect."""
    try:
        json.dumps(value, ensure_ascii=False, allow_nan=False).encode("utf-8")
    except (TypeError, ValueError, RecursionError, OverflowError):
        raise ValueError("Use finite UTF-8 JSON values.") from None
    return value


JsonObject = Annotated[dict[str, Any], AfterValidator(finite_json)]
