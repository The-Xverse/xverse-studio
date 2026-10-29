"""Strict base for untrusted request bodies, shared by every layer that validates input."""
from pydantic import BaseModel, ConfigDict


class Body(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True, allow_inf_nan=False)
