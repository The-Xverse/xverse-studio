"""Owned reservation crash host: timing hooks only, with durable fixture effects.

The JSON effect record simulates an external provider surviving backend death.
It is not production provider persistence or an actual device integration.
Application routes, operation payloads and durable writes remain unchanged.
"""

import argparse
from contextlib import asynccontextmanager
import importlib.util
import json
from pathlib import Path
import platform
import socket
import threading
import time

import uvicorn
from xverse_studio.api.app import create_app
from xverse_studio.lab.authority import LabAuthority
from xverse_studio.lab.configuration import (
    LabHostConfiguration,
    LeaseProviderInstallation,
)
from xverse_studio.storage.core import atomic


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--data", type=Path, required=True)
    parser.add_argument(
        "--boundary",
        required=True,
        choices=("before-delegation", "after-provider-effect", "before-final-receipt"),
    )
    parser.add_argument("--phase", required=True, choices=("initial", "restart"))
    args = parser.parse_args()
    args.data.parent.mkdir(parents=True, exist_ok=True)
    spec = importlib.util.spec_from_file_location(
        "owned_interruption_provider", Path(__file__).with_name("provider.py")
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    provider = module.PhysicalContractFixture(time.time)
    effect = args.data.parent / "provider-effect.private.json"
    marker = args.data.parent / "boundary.private.json"
    if args.phase == "restart" and effect.exists():
        value = json.loads(effect.read_text())
        assert value["scope"] == "owned durable fixture effect; no equipment"
        provider.held = value["held"]
        provider.sequence = value["reservationEffects"]
    paused = False

    def pause(operation=None):
        nonlocal paused
        assert args.phase == "initial" and not paused
        paused = True
        atomic(
            marker,
            json.dumps(
                {
                    "boundary": args.boundary,
                    "phase": args.phase,
                    "scope": "timing-only owned fixture pause",
                    "calls": provider.calls,
                    "reservationEffects": provider.sequence,
                    "operation": operation,
                }
            ).encode(),
        )
        # The controller kills this owned process before continuation. A bounded
        # fallback fails the fixture instead of delegating after a missed crash.
        threading.Event().wait(30)
        raise RuntimeError("Owned interruption fixture was not killed at its boundary")

    reserve = provider.reserve

    def recorded_reserve(*values):
        result = reserve(*values)
        atomic(
            effect,
            json.dumps(
                {
                    "scope": "owned durable fixture effect; no equipment",
                    "held": provider.held,
                    "reservationEffects": provider.sequence,
                }
            ).encode(),
        )
        if args.phase == "initial" and args.boundary == "after-provider-effect":
            pause()
        return result

    provider.reserve = recorded_reserve
    policy = LabAuthority({("local-operator", provider.asset_id): {"observe"}})
    installation = LeaseProviderInstallation(
        provider,
        provider.provider_id,
        "1.0.0",
        "sha256:" + "a" * 64,
        (platform.system(),),
        (platform.machine(),),
        "fixture",
        "owned-interruption-conformance",
        "fixture-no-equipment",
    )
    host = LabHostConfiguration((installation,), policy, call_timeout=5)
    with socket.socket() as listener:
        listener.bind(("127.0.0.1", 0))
        port = listener.getsockname()[1]
        app = create_app(args.data, allowed_hosts=[f"127.0.0.1:{port}"], lab_host=host)
        service = app.state.studio.lab_reservations
        original_put = service.store.put

        def paused_put(kind, identity, body, db=None):
            if (
                args.phase == "initial"
                and not paused
                and kind == "operation"
                and body.get("kind") == "lab_reserve"
            ):
                expected = {
                    "before-delegation": "delegated",
                    "before-final-receipt": "completed",
                }.get(args.boundary)
                if expected is not None and body.get("status") == expected:
                    pause(body)
            return original_put(kind, identity, body, db)

        service.store.put = paused_put
        original_lifespan = app.router.lifespan_context

        @asynccontextmanager
        async def observed_lifespan(application):
            try:
                async with original_lifespan(application):
                    yield
            finally:
                atomic(
                    args.data.parent / (args.phase + "-observation.json"),
                    json.dumps(
                        {
                            "scope": "owned durable fixture effect; no equipment",
                            "phase": args.phase,
                            "boundary": args.boundary,
                            "calls": provider.calls,
                            "reservationEffects": provider.sequence,
                            "heldLeases": len(provider.held),
                        }
                    ).encode(),
                )

        app.router.lifespan_context = observed_lifespan
        print(json.dumps({"origin": f"http://127.0.0.1:{port}"}), flush=True)
        uvicorn.Server(
            uvicorn.Config(
                app, host="127.0.0.1", port=port, log_level="error", access_log=False
            )
        ).run(sockets=[listener])


if __name__ == "__main__":
    main()
