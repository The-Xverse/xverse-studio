"""Bounded, inert v1 evaluator. Call only for admitted snapshot-bound profile data.

The evaluator never reads files, fetches resources, calls providers, or interprets code.
It consumes authoritative evidence projections supplied by the backend.
"""
from .evaluator import EvaluationError, aggregate_verdict, evaluate, validate_definition

__all__ = ["EvaluationError", "aggregate_verdict", "evaluate", "validate_definition"]

from .snapshot import snapshot_definitions, definition_digest, UNIT_DEFINITIONS
