"""Native foreground launcher. No Bash, WSL, container, service-manager or shell dependency."""

from __future__ import annotations
import argparse
import json
import os
from pathlib import Path
import sqlite3
import sys
import uvicorn
from xverse_studio.storage.core import Problem


def default_root():
    if os.name == "nt":
        return (
            Path(os.environ.get("LOCALAPPDATA", str(Path.home() / "AppData/Local")))
            / "XVerseStudio"
        )
    return (
        Path(os.environ.get("XDG_DATA_HOME", str(Path.home() / ".local/share")))
        / "xverse-studio"
    )


def main():
    parser = argparse.ArgumentParser(description="Native local X-Verse Studio")
    parser.add_argument("--data-dir", type=Path, default=default_root())
    parser.add_argument("--port", type=int, default=8765)
    parser.add_argument("--static-dir", type=Path)
    parser.add_argument(
        "--backup",
        type=Path,
        help="Create a consistent metadata backup; stop Studio and copy the whole data root for full recovery.",
    )
    args = parser.parse_args()
    if not 1024 <= args.port <= 65535:
        parser.error("Choose an unprivileged loopback port 1024–65535.")
    root = args.data_dir.resolve()
    root.mkdir(parents=True, exist_ok=True)
    # OS-native advisory file lock prevents concurrent owners of the same data root.
    lockfile = (root / "studio.lock").open("a+b")
    try:
        if os.name == "nt":
            import msvcrt

            lockfile.seek(0)
            lockfile.write(b"0")
            lockfile.flush()
            lockfile.seek(0)
            msvcrt.locking(lockfile.fileno(), msvcrt.LK_NBLCK, 1)
        else:
            import fcntl

            fcntl.flock(lockfile.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
    except OSError:
        parser.error("This data root is owned by another running Studio launcher.")
    if args.backup:
        if args.backup.exists():
            parser.error("Refusing to overwrite an existing backup.")
        args.backup.parent.mkdir(parents=True, exist_ok=True)
        with (
            sqlite3.connect(root / "studio.sqlite") as source,
            sqlite3.connect(args.backup) as dest,
        ):
            source.backup(dest)
        print(
            "Metadata backup created. Full recovery also requires the matching project, snapshot and run files."
        )
        return
    from xverse_studio.api.app import create_app

    app = create_app(
        root,
        allowed_hosts=[f"127.0.0.1:{args.port}", f"localhost:{args.port}"],
        static_dir=args.static_dir,
    )
    print(f"Studio: http://127.0.0.1:{args.port}")
    print(
        f"One-use sign-in token: read {root / 'bootstrap.json'} locally. The token is never placed in a URL."
    )
    print(
        "Ctrl+C requests owned reference-run cancellation and shuts down the native backend."
    )
    try:
        uvicorn.run(
            app, host="127.0.0.1", port=args.port, log_level="warning", access_log=False
        )
    finally:
        lockfile.close()


if __name__ == "__main__":
    main()
