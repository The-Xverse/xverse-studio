"""Owned native browser fixture host. No production loader, equipment or drivers.

Only fixed test scenarios are accepted. The actual application routes and
middleware are installed unchanged, with a typed in-memory lease provider.
"""

import argparse
import importlib.util
import json
from pathlib import Path
import platform
import socket
import time

import uvicorn

from xverse_studio.api.app import create_app
from xverse_studio.lab.authority import LabAuthority
from xverse_studio.lab.configuration import (
    LabHostConfiguration,
    LeaseProviderInstallation,
)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--data", type=Path, required=True)
    parser.add_argument(
        "--scenario",
        choices=(
            "observe",
            "scopes",
            "reserve-unknown",
            "release-unknown",
            "revoked",
            "restart",
            "history",
        ),
        required=True,
    )
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[4]
    spec = importlib.util.spec_from_file_location(
        "owned_physical_browser_fixture", Path(__file__).with_name("provider.py")
    )
    fixture = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(fixture)
    provider = fixture.PhysicalContractFixture(time.time)
    granted = {"observe"}
    if args.scenario == "scopes":
        provider.assets[0]["capabilities"].append("destructive")
        granted.update(("stimulate", "destructive"))
    policy = LabAuthority({("local-operator", provider.asset_id): granted})
    if args.scenario == "reserve-unknown":
        provider.lose_reserve_ack = True
    if args.scenario == "release-unknown":
        provider.release_observation = {"status": "unknown"}
    if args.scenario == "revoked":
        reserve = provider.reserve

        def revoke_after_ack(*values):
            result = reserve(*values)
            policy.revoke("local-operator", provider.asset_id)
            return result

        provider.reserve = revoke_after_ack
    installation = LeaseProviderInstallation(
        provider,
        provider.provider_id,
        "1.0.0",
        "sha256:" + "a" * 64,
        (platform.system(),),
        (platform.machine(),),
        "fixture",
        "owned-browser-conformance",
        "fixture-no-equipment",
    )
    host = LabHostConfiguration((installation,), policy)
    # Keep the actual listening socket from allocation through server shutdown.
    with socket.socket() as listener:
        listener.bind(("127.0.0.1", 0))
        port = listener.getsockname()[1]
        options = dict(
            allowed_hosts=[f"127.0.0.1:{port}"],
            static_dir=root / "apps/studio-web/dist",
            lab_host=host,
        )
        preparation_started = time.monotonic()
        app = create_app(args.data, **options)
        if args.scenario == "history":
            service = app.state.studio.lab_reservations
            for index in range(51):
                accepted = service.reserve(
                    provider.asset_id,
                    owner="local-operator",
                    key=f"owned-history-{index}",
                )
                service.release(
                    accepted["reservationId"],
                    owner="local-operator",
                    key=f"owned-release-{index}",
                )
        if args.scenario == "restart":
            service = app.state.studio.lab_reservations
            service.reserve(
                provider.asset_id,
                owner="local-operator",
                key="owned-seeded-original",
                duration=300,
            )
            app = create_app(args.data, **options)
        config = uvicorn.Config(
            app, host="127.0.0.1", port=port, log_level="error", access_log=False
        )
        preparation_seconds = time.monotonic() - preparation_started
        print(
            json.dumps(
                {
                    "origin": f"http://127.0.0.1:{port}",
                    "preparationSeconds": preparation_seconds,
                }
            ),
            flush=True,
        )
        try:
            uvicorn.Server(config).run(sockets=[listener])
        finally:
            # Counts/immutable fixture declarations only, never bootstrap/session data.
            (args.data / "fixture-observation.json").write_text(
                json.dumps(
                    {
                        "scope": "owned in-memory fixture; no equipment",
                        "scenario": args.scenario,
                        "calls": provider.calls,
                        "reservationCount": provider.sequence,
                        "remainingProviderLeases": len(provider.held),
                        "preparationSeconds": preparation_seconds,
                    }
                ),
                encoding="utf-8",
            )


if __name__ == "__main__":
    main()
