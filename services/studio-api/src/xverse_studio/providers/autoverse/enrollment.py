"""Owner-only native receipt; projects and portable imports cannot select it."""

import json
import os
import platform
from pathlib import Path
import stat

from xverse_studio.security.managed_io import open_read, SafeIOError
from xverse_studio.storage.core import atomic, canonical, digest
from .installation import enroll, verify_identity, InstallationError

NAME = "autoverse-installation.private.json"
MAX_BYTES = 1024 * 1024


def _unique_fields(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("Duplicate receipt field")
        result[key] = value
    return result


def load_or_enroll(data_root, selected_root):
    if platform.system() != "Linux" or platform.machine() != "x86_64":
        raise InstallationError("AUTOVERSE_LINUX_PROVIDER_REQUIRED")
    data_root = Path(data_root).resolve(strict=True)
    selected_root = Path(selected_root).resolve(strict=True)
    path = data_root / NAME
    try:
        path.lstat()
    except FileNotFoundError:
        installation = enroll(selected_root)
        if installation.get("root") != str(selected_root):
            raise InstallationError("AUTOVERSE_ENROLLMENT_ROOT_MISMATCH")
        record = {
            "version": "1.0",
            "root": str(selected_root),
            "installation": installation,
            "receiptDigest": digest(installation),
        }
        raw = canonical(record).encode("utf-8")
        if len(raw) > MAX_BYTES:
            raise InstallationError("AUTOVERSE_ENROLLMENT_RECEIPT_INVALID")
        atomic(path, raw)
        path.chmod(0o600)
        return installation
    try:
        with open_read(data_root, path) as stream:
            info = os.fstat(stream.fileno())
            if (
                not stat.S_ISREG(info.st_mode)
                or info.st_uid != os.getuid()
                or info.st_mode & 0o077
                or not 0 < info.st_size <= MAX_BYTES
            ):
                raise ValueError()
            raw = stream.read(MAX_BYTES + 1)
            if len(raw) > MAX_BYTES:
                raise ValueError()
        record = json.loads(raw, object_pairs_hook=_unique_fields)
        if (
            not isinstance(record, dict)
            or set(record) != {"version", "root", "installation", "receiptDigest"}
            or record["version"] != "1.0"
            or record["root"] != str(selected_root)
            or not isinstance(record["installation"], dict)
            or record["installation"].get("root") != str(selected_root)
            or record["receiptDigest"] != digest(record["installation"])
        ):
            raise ValueError()
    except (
        OSError,
        SafeIOError,
        ValueError,
        KeyError,
        TypeError,
        RecursionError,
        OverflowError,
    ):
        raise InstallationError("AUTOVERSE_ENROLLMENT_RECEIPT_INVALID") from None
    installation = record["installation"]
    verify_identity(installation)
    return installation
