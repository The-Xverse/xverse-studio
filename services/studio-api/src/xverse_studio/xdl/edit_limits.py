"""Iterative bounds before copying untrusted typed edit payloads."""

import json

from . import XDLRejected

MAX_EDIT_BYTES = 64 * 1024
MAX_EDIT_DEPTH = 64
MAX_EDIT_NODES = 10_000


def check_edit_payload(value):
    stack, count = [(value, 0)], 0
    while stack:
        item, depth = stack.pop()
        count += 1
        if depth > MAX_EDIT_DEPTH or count > MAX_EDIT_NODES:
            raise XDLRejected(
                "The typed edit depth or node limit is exceeded.", "LIMIT_EXCEEDED"
            )
        if isinstance(item, dict):
            if any(not isinstance(key, str) for key in item):
                raise XDLRejected(
                    "Typed edit object keys must be strings.", "INVALID_EDIT"
                )
            stack.extend((child, depth + 1) for child in item.values())
        elif isinstance(item, list):
            stack.extend((child, depth + 1) for child in item)
        elif item is not None and not isinstance(item, (str, bool, int, float)):
            raise XDLRejected(
                "Typed edits contain only inert JSON values.", "INVALID_EDIT"
            )
    try:
        size = len(json.dumps(value, allow_nan=False, ensure_ascii=False).encode())
    except (ValueError, TypeError, RecursionError):
        raise XDLRejected(
            "Typed edits must be finite bounded JSON data.", "INVALID_EDIT"
        ) from None
    if size > MAX_EDIT_BYTES:
        raise XDLRejected(
            "The typed edit exceeds its 64 KiB payload limit.", "LIMIT_EXCEEDED"
        )
