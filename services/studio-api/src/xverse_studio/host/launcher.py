"""Native foreground launcher. No Bash, WSL, container, service-manager or shell dependency."""

from __future__ import annotations
import argparse
from contextlib import closing
import json
import os
from pathlib import Path
import sqlite3
import uvicorn
from xverse_studio.host.ownership import own_root, RootOwnedError, RootUnsafeError
from xverse_studio.host.recovery import backup_full, restore_full, RecoveryError


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
    maintenance = parser.add_mutually_exclusive_group()
    maintenance.add_argument(
        "--backup",
        type=Path,
        help="Create a consistent metadata backup; stop Studio and copy the whole data root for full recovery.",
    )
    maintenance.add_argument(
        "--backup-full",
        type=Path,
        help="Back up a stopped, settled private root into a new directory.",
    )
    maintenance.add_argument(
        "--restore-from",
        type=Path,
        help="Verify a private full backup and restore into a new --data-dir; never starts execution.",
    )
    args = parser.parse_args()
    if not 1024 <= args.port <= 65535:
        parser.error("Choose an unprivileged loopback port 1024–65535.")
    root = args.data_dir.absolute()
    if args.backup_full or args.restore_from:
        try:
            result = (
                restore_full(args.restore_from, root)
                if args.restore_from
                else backup_full(root, args.backup_full)
            )
        except (RecoveryError, OSError) as exc:
            parser.error(
                str(exc)
                if isinstance(exc, RecoveryError)
                else "RECOVERY_FILESYSTEM_FAILURE"
            )
        print(json.dumps(result, sort_keys=True))
        return
    root = root.resolve()
    root.mkdir(parents=True, exist_ok=True)
    if (root / ".recovery-incomplete").exists():
        parser.error(
            "RECOVERY_INCOMPLETE: restore into a new data root; do not start this partial root."
        )
    # OS-native advisory file lock prevents concurrent owners of the same data root.
    try:
        with own_root(root):
            _owned_main(args, root, parser)
    except RootOwnedError:
        parser.error("This data root is owned by another running Studio launcher.")
    except RootUnsafeError:
        parser.error(
            "RECOVERY_UNSAFE_FILE: the data root lock must be a regular local file."
        )


def _owned_main(args, root, parser):
    if args.backup:
        if not (root / "studio.sqlite").is_file():
            parser.error("RECOVERY_DATABASE_MISSING: select an existing data root.")
        args.backup.parent.mkdir(parents=True, exist_ok=True)
        try:
            with args.backup.open("xb"):
                args.backup.chmod(0o600)
        except FileExistsError:
            parser.error("Refusing to overwrite an existing backup.")
        with (
            closing(
                sqlite3.connect(
                    (root / "studio.sqlite").as_uri() + "?mode=ro", uri=True
                )
            ) as source,
            closing(sqlite3.connect(args.backup)) as dest,
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
    uvicorn.run(
        app, host="127.0.0.1", port=args.port, log_level="warning", access_log=False
    )


if __name__ == "__main__":
    main()
