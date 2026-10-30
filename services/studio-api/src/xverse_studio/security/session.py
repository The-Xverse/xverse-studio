"""Closed native session facts and exact opaque-secret comparison."""

import hmac
import math


def matches_secret(provided, expected):
    try:
        return (
            isinstance(provided, str)
            and isinstance(expected, str)
            and len(provided) <= 256
            and len(expected) <= 256
            and hmac.compare_digest(provided.encode("utf-8"), expected.encode("utf-8"))
        )
    except UnicodeError:
        return False


def valid_session(value, now):
    if not isinstance(value, dict) or set(value) != {"csrfToken", "expiresAt"}:
        return False
    expires, csrf = value["expiresAt"], value["csrfToken"]
    try:
        return (
            type(expires) in (int, float)
            and math.isfinite(expires)
            and expires > now
            and isinstance(csrf, str)
            and 1 <= len(csrf) <= 256
            and bool(csrf.encode("utf-8"))
        )
    except (UnicodeError, OverflowError):
        return False
