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
    parser.add_argument("--data-dir", type=Path)
    parser.add_argument("--port", type=int, default=8765)
    parser.add_argument("--static-dir", type=Path)
    parser.add_argument("--autoverse-root", type=Path, help="Enroll the explicitly selected existing Linux Autoverse demo installation; no downloads or builds.")
    parser.add_argument("--autoverse-native-bridge", type=Path,
        help="Explicit verified native bridge build directory; requires --autoverse-root and enables the separate platform simulation provider.")
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
    maintenance.add_argument("--migrate-from", type=Path,
        help="Copy known unversioned stopped metadata into a new --data-dir; requires --migration-backup and starts nothing.")
    parser.add_argument("--migration-backup", type=Path,
        help="New private backup directory required by --migrate-from; never overwritten.")
    args = parser.parse_args()
    if bool(args.migrate_from) != bool(args.migration_backup):
        parser.error("--migrate-from and --migration-backup must be selected together.")
    if args.migrate_from and args.data_dir is None:
        parser.error("--migrate-from requires an explicit new --data-dir candidate root.")
    args.data_dir = args.data_dir or default_root()
    if args.autoverse_native_bridge is not None and args.autoverse_root is None:
        parser.error("--autoverse-native-bridge requires the explicitly enrolled --autoverse-root.")
    if not 1024 <= args.port <= 65535:
        parser.error("Choose an unprivileged loopback port 1024–65535.")
    root = args.data_dir.absolute()
    if args.backup_full or args.restore_from or args.migrate_from:
        try:
            if args.migrate_from:
                from xverse_studio.host.migration import migrate_full
                result = migrate_full(args.migrate_from, args.migration_backup, root)
            else:
                result = (restore_full(args.restore_from, root)
                          if args.restore_from else backup_full(root, args.backup_full))
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

    installed = None
    if args.autoverse_root is not None:
        from xverse_studio.providers.autoverse.adapter import AutoverseProvider, PROVIDER_ID
        from xverse_studio.providers.autoverse.installation import InstallationError
        from xverse_studio.providers.autoverse.enrollment import load_or_enroll
        from xverse_studio.providers.descriptors import UnavailableProvider
        installed = {}
        prerequisite = None
        try:
            installed[PROVIDER_ID] = AutoverseProvider(load_or_enroll(root, args.autoverse_root))
        except Exception as error:
            # Enrollment is read-only. A requested integration failure must not
            # disable native authoring or expose private probe/path diagnostics.
            prerequisite = str(error) if isinstance(error, InstallationError) else "AUTOVERSE_ENROLLMENT_FAILED"
            installed[PROVIDER_ID] = UnavailableProvider(PROVIDER_ID, prerequisite)
        if args.autoverse_native_bridge is not None:
            try:
                if prerequisite:
                    installed["autoverse.platform"] = UnavailableProvider("autoverse.platform", prerequisite)
                else:
                    from xverse_studio.providers.autoverse.platform_adapter import PlatformProvider
                    from xverse_studio.providers.autoverse.platform_installation import enroll_platform
                    platform_installation = enroll_platform(args.autoverse_root, args.autoverse_native_bridge,
                        root / "platform-runtime" / "autoverse")
                    installed["autoverse.platform"] = PlatformProvider(platform_installation)
            except Exception as error:
                code = str(error) if isinstance(error, InstallationError) else "AUTOVERSE_PLATFORM_ENROLLMENT_FAILED"
                installed["autoverse.platform"] = UnavailableProvider("autoverse.platform", code)
    app = create_app(
        root,
        allowed_hosts=[f"127.0.0.1:{args.port}", f"localhost:{args.port}"],
        static_dir=args.static_dir,
        installed_providers=installed,
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
