"""Opt-in contributor-only bounded timings; no payloads or authority changes."""

from collections import deque
from contextlib import asynccontextmanager
from contextvars import ContextVar
from functools import wraps
import json
import re
import time


def install(app, data):
    from xverse_studio.providers.autoverse import input as input_api

    target = data / "input-timing.private.json"
    assert not target.exists()
    active = ContextVar("contributor_input_timing", default=None)
    samples, restore = deque(maxlen=256), []

    def timed(owner, name, label):
        original = getattr(owner, name)

        @wraps(original)
        def wrapper(*args, **kwargs):
            sample = active.get()
            if sample is None:
                return original(*args, **kwargs)
            begin = time.monotonic()
            try:
                return original(*args, **kwargs)
            except Exception as error:
                code = getattr(error, "code", None)
                sample["failureCode"] = code if isinstance(code, str) and re.fullmatch(r"[A-Z][A-Z0-9_]{0,127}", code) else type(error).__name__[:128]
                raise
            finally:
                sample[label] = sample.get(label, 0) + time.monotonic() - begin

        setattr(owner, name, wrapper)
        restore.append((owner, name, original, wrapper))

    runs = app.state.studio.runs
    timed(runs, "input_request", "inputRequestSeconds")
    timed(runs, "read", "lifecycleReadSeconds")
    timed(runs, "_require_active_provider", "providerAdmissionSeconds")
    for provider in runs.installed_providers.values():
        if callable(getattr(provider, "input_request", None)):
            timed(provider, "input_request", "providerInputSeconds")

    original_atomic = input_api.atomic

    @wraps(original_atomic)
    def atomic(path, raw):
        sample = active.get()
        if sample is None:
            return original_atomic(path, raw)
        begin = time.monotonic()
        try:
            return original_atomic(path, raw)
        finally:
            label = {"input-owner.json": "ownerAtomicSeconds", "input.json": "mailboxAtomicSeconds"}.get(path.name, "otherAtomicSeconds")
            sample[label] = sample.get(label, 0) + time.monotonic() - begin

    input_api.atomic = atomic
    restore.append((input_api, "atomic", original_atomic, atomic))

    @app.middleware("http")
    async def measure(request, call_next):
        parts = request.url.path.split("/")
        if len(parts) != 7 or parts[1:4] != ["api", "v1", "runs"] or parts[5] != "input" or parts[6] not in {"frame", "acquire", "release"}:
            return await call_next(request)
        sample = {"action": parts[6], "receivedMonotonic": time.monotonic()}
        token = active.set(sample)
        try:
            response = await call_next(request)
            sample["statusCode"] = response.status_code
            return response
        finally:
            sample["httpSeconds"] = time.monotonic() - sample["receivedMonotonic"]
            active.reset(token)
            samples.append(sample)

    original_lifespan = app.router.lifespan_context

    @asynccontextmanager
    async def lifespan(application):
        try:
            async with original_lifespan(application):
                yield
        finally:
            for owner, name, original, wrapper in reversed(restore):
                if getattr(owner, name) is wrapper:
                    setattr(owner, name, original)
            target.write_text(json.dumps({"scope": "Bounded contributor instrumented timings; no payloads, tokens, session identities or acceptance inference", "maximumSamples": 256, "samples": list(samples)}, indent=2) + "\n")

    app.router.lifespan_context = lifespan
