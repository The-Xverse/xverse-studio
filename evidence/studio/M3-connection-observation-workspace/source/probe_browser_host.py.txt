"""Explicit native observation browser fixture; no equipment, scan or driver IO."""

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
from xverse_studio.lab.probe_configuration import (
    LabProbeConfiguration,
    ProbeAuthority,
    ProbeInstallation,
)
from xverse_studio.storage.core import atomic, canonical, digest


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--data", type=Path, required=True)
    parser.add_argument(
        "--scenario",
        choices=[
            "observe",
            "forbidden",
            "unavailable",
            "unknown",
            "revoked",
            "timeout",
            "stale-binding",
        ],
        required=True,
    )
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[4]
    spec = importlib.util.spec_from_file_location(
        "owned_probe_browser_fixture", Path(__file__).with_name("provider.py")
    )
    fixture = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(fixture)
    provider = fixture.PhysicalContractFixture(time.time)
    probe_calls = []
    app = None
    authority = ProbeAuthority(
        () if args.scenario == "forbidden" else {("local-operator", provider.asset_id)}
    )

    def probe(binding, scope, deadline):
        assert (
            scope == "observe"
            and binding["assetId"] == provider.asset_id
            and time.time() < deadline
        )
        pending = [
            value
            for value in app.state.studio.store.find("operation", "kind", "lab_probe")
            if value["status"] == "delegated"
        ]
        assert len(pending) == 1 and pending[0]["assetId"] == provider.asset_id
        probe_calls.append(pending[0]["operationId"])
        atomic(
            args.data / "probe-call-count.json", canonical(len(probe_calls)).encode()
        )
        if args.scenario == "unknown":
            raise ConnectionError(
                "Owned fixture acknowledgement uncertainty, no external contact"
            )
        if args.scenario == "timeout":
            threading.Event().wait(10)
        if args.scenario == "revoked":
            authority.revoke("local-operator", provider.asset_id)
        unavailable = args.scenario == "unavailable"
        return dict(
            status="unavailable" if unavailable else "observed",
            identityDigest=binding["identityDigest"],
            contactedResources=[] if unavailable else binding["contactedResources"],
            sourceTime=None
            if unavailable
            else dict(
                clockDomain="fixture-probe-clock",
                tick="-9007199254740993",
                unit="ns",
                uncertaintySeconds=None,
            ),
            metadata={}
            if unavailable
            else dict(
                firmwareVersion="fixture-observation-r3",
                artifactRevision="fixture-image-v2",
            ),
            diagnostics=["FIXTURE_UNAVAILABLE"] if unavailable else [],
            private="owned-fixture-private-payload-never-public",
        )

    provider.probe = probe
    native = dict(
        supported_os=(platform.system(),), architectures=(platform.machine(),)
    )
    lease = LeaseProviderInstallation(
        provider=provider,
        provider_id=provider.provider_id,
        version="1.0.0",
        implementation_digest="sha256:" + "a" * 64,
        evidence_scope="fixture",
        conformance_ref="owned-browser-conformance",
        authorization_ref="fixture-no-equipment",
        **native,
    )
    observation = ProbeInstallation(
        provider=provider,
        provider_id=provider.provider_id,
        asset_id=provider.asset_id,
        binding_ref="owned-observation-binding",
        identity_digest=digest(provider.assets[0]["identity"]),
        implementation_digest="sha256:" + "c" * 64,
        version="1.0.0",
        evidence_scope="fixture",
        conformance_ref="owned-probe-browser-conformance",
        authorization_ref="fixture-no-equipment",
        contacted_resources=("owned-observation-resource",),
        private_binding={"nativeHandle": "owned-loopback-fixture-handle"},
        **native,
    )
    with socket.socket() as listener:
        listener.bind(("127.0.0.1", 0))
        port = listener.getsockname()[1]
        app = create_app(
            args.data,
            allowed_hosts=[f"127.0.0.1:{port}"],
            static_dir=root / "apps/studio-web/dist",
            lab_host=LabHostConfiguration(
                (lease,),
                LabAuthority({("local-operator", provider.asset_id): {"observe"}}),
            ),
            lab_probe_host=LabProbeConfiguration(
                (observation,),
                authority,
                call_timeout=0.05 if args.scenario == "timeout" else 1,
            ),
        )
        if args.scenario == "stale-binding":
            # Declared test-only host change after the original pure options read.
            original = app.state.studio.lab_probes.options

            def options(asset_id, *, owner):
                result = original(asset_id, owner=owner)
                observation.private_binding["nativeHandle"] = (
                    "owned-changed-fixture-handle"
                )
                return result

            app.state.studio.lab_probes.options = options
        original_lifespan = app.router.lifespan_context

        @asynccontextmanager
        async def observed_lifespan(application):
            try:
                async with original_lifespan(application):
                    yield
            finally:
                atomic(
                    args.data / "probe-fixture-observation.json",
                    canonical(
                        dict(
                            scope="owned native observation fixture; no equipment",
                            scenario=args.scenario,
                            leaseCalls=provider.calls,
                            probeCalls=probe_calls,
                            reservationCount=provider.sequence,
                            remainingProviderLeases=len(provider.held),
                            operations=[
                                {
                                    key: value[key]
                                    for key in (
                                        "operationId",
                                        "assetId",
                                        "principal",
                                        "status",
                                        "bindingDigest",
                                    )
                                }
                                for value in app.state.studio.store.find(
                                    "operation", "kind", "lab_probe"
                                )
                            ],
                        )
                    ).encode(),
                )

        app.router.lifespan_context = observed_lifespan
        print(json.dumps(dict(origin=f"http://127.0.0.1:{port}")), flush=True)
        uvicorn.Server(
            uvicorn.Config(
                app, host="127.0.0.1", port=port, log_level="error", access_log=False
            )
        ).run(sockets=[listener])


if __name__ == "__main__":
    main()
