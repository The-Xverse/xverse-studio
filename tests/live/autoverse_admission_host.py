"""Closed native Autoverse browser validation host; only describe can be faulted."""

import argparse
import json
from pathlib import Path
import sys


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--receipt", type=Path, required=True)
    parser.add_argument("--data-dir", type=Path, required=True)
    parser.add_argument("--static-dir", type=Path, required=True)
    parser.add_argument("--port", type=int, required=True)
    parser.add_argument(
        "--fault", choices=["valid", "invalid", "mutable"], required=True
    )
    args = parser.parse_args()
    if not args.data_dir.parent.name == "browser-tests":
        parser.error("A dedicated Studio browser-tests root is required.")
    enrolled = json.loads(args.receipt.read_bytes())["classic"]
    if args.fault in ("invalid", "mutable"):
        from xverse_studio.providers.autoverse.adapter import AutoverseProvider

        describe = AutoverseProvider.descriptor

        def invalid(provider):
            fault = "invalid"
            if args.fault == "mutable":
                state = args.data_dir / "descriptor-fault.txt"
                fault = state.read_text() if state.exists() else "valid"
            value = describe(provider)
            if fault == "valid":
                return value
            if fault == "invalid":
                return {**value, "implementationDigest": "sha256:invalid"}
            if fault == "changed":
                return {**value, "implementationDigest": "sha256:" + "0" * 64}
            if fault == "unavailable":
                return {**value, "available": False}
            if fault == "host":
                return {**value, "supportedHostOS": ["unavailable-host"]}
            if fault == "broken":
                raise RuntimeError("owned-private-marker: descriptor read failure")
            raise ValueError("Unknown controlled native descriptor fault")

        AutoverseProvider.descriptor = invalid
    sys.argv = [
        sys.argv[0],
        "--data-dir",
        str(args.data_dir),
        "--port",
        str(args.port),
        "--static-dir",
        str(args.static_dir),
        "--autoverse-root",
        enrolled["root"],
    ]
    from xverse_studio.host.launcher import main as launch

    launch()


if __name__ == "__main__":
    main()
