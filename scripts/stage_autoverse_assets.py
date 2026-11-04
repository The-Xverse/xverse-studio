"""Stage reusable Android artifacts into a NEW private test root, never guest state.

Native Linux provider preparation only. Requires an already provisioned Studio
Python environment. Does not start Docker, VMs, imported scripts or providers.
"""
from __future__ import annotations
import argparse
import errno
import hashlib
import json
import os
from pathlib import Path
import shutil
import stat

from xverse_studio.security.managed_io import open_read

FOLDERS = {"bin", "lib", "lib64", "etc", "usr", "share", "config"}
IMAGES = {name + ".img" for name in ["super", "boot", "init_boot", "vendor_boot", "vendor_kernel_boot", "userdata", "cache", "dtbo", "metadata", "misc", "system", "system_ext", "vendor", "product", "odm", "system_dlkm", "vendor_dlkm", "odm_dlkm", "vbmeta", "vbmeta_system", "vbmeta_vendor", "vbmeta_system_dlkm", "vbmeta_vendor_dlkm", "vbmeta_odm", "cuttlefish_example_custom", "ramdisk"]}
FILES = {"kernel", "initramfs.img", "bootloader", "android-info.txt", "bootconfig", "fetcher_config.json"}
MIN_FREE = 10 * 1024**3
MAX_FILES = 10000
MAX_LOGICAL = 64 * 1024**3
BLOCK = 1024 * 1024


def signature(value):
    return value.st_dev, value.st_ino, value.st_size, value.st_mtime_ns


def copy_sparse(source_root: Path, source: Path, target: Path, *, max_bytes=MAX_LOGICAL):
    """Acquire through Studio's safe reader; copy independent sparse extents."""
    with open_read(source_root, source) as reader:
        before = os.fstat(reader.fileno())
        if not stat.S_ISREG(before.st_mode):
            raise ValueError("ASSET_NOT_REGULAR")
        if before.st_size > max_bytes:
            raise ValueError("ASSET_LOGICAL_BYTE_LIMIT")
        if shutil.disk_usage(target.parent).free < MIN_FREE + before.st_blocks * 512:
            raise ValueError("ASSET_FREE_SPACE_REQUIRED")
        fd = os.open(target, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
        hashed = hashlib.sha256()
        try:
            os.ftruncate(fd, before.st_size)
            position = 0
            while position < before.st_size:
                try:
                    data = os.lseek(reader.fileno(), position, os.SEEK_DATA)
                except OSError as exc:
                    if exc.errno == errno.ENXIO:
                        data = before.st_size
                    elif exc.errno in {errno.EINVAL, errno.ENOTSUP}:
                        data = position  # Bounded zero-block fallback on older filesystems.
                    else:
                        raise
                while position < data:
                    amount = min(BLOCK, data - position)
                    hashed.update(bytes(amount))
                    position += amount
                if position == before.st_size:
                    break
                chunk = os.pread(reader.fileno(), min(BLOCK, before.st_size - position), position)
                if not chunk:
                    raise ValueError("ASSET_CHANGED_DURING_READ")
                hashed.update(chunk)
                if any(chunk):
                    written = 0
                    while written < len(chunk):
                        amount = os.pwrite(fd, chunk[written:], position + written)
                        if amount <= 0:
                            raise OSError("ASSET_WRITE_INCOMPLETE")
                        written += amount
                position += len(chunk)
            if signature(os.fstat(reader.fileno())) != signature(before) or signature(source.stat(follow_symlinks=False)) != signature(before):
                raise ValueError("ASSET_CHANGED_DURING_READ")
            os.fchmod(fd, stat.S_IMODE(before.st_mode) & 0o755)
            os.fsync(fd)
        finally:
            os.close(fd)
    return {"sha256": "sha256:" + hashed.hexdigest(), "logicalBytes": before.st_size,
            "allocatedBytes": target.stat().st_blocks * 512}


def stage(source_root: Path, destination: Path):
    if os.name != "posix" or not hasattr(os, "O_NOFOLLOW"):
        raise ValueError("ASSET_STAGING_LINUX_REQUIRED")
    source_root = source_root.resolve(strict=True)
    destination = destination.absolute()
    destination = destination.parent.resolve(strict=True) / destination.name
    if destination.exists() or destination.is_symlink() or destination.is_relative_to(source_root):
        raise ValueError("ASSET_DESTINATION_MUST_BE_NEW_AND_SEPARATE")
    destination.mkdir(mode=0o700)
    marker = destination / ".incomplete"
    marker.write_text("Staging not verified; never enroll or execute this partial root.\n")
    runtime = destination / "android-runtime"
    runtime.mkdir(mode=0o755)
    original = (source_root / "aaos_digital_cluster/cuttlefish_emulator/runtime").resolve(strict=True)
    if not original.is_dir():
        raise ValueError("ANDROID_ARTIFACTS_UNAVAILABLE")
    entries = []
    for item in original.iterdir():
        # Exclude every existing assembly, guest instance, log, socket and overlay.
        if item.name in FOLDERS or item.name in FILES or item.name in IMAGES:
            entries.append(item)
    manifest = {}
    pending = sorted(entries, reverse=True)
    logical = 0
    visited = 0
    while pending:
        item = pending.pop()
        visited += 1
        if visited > MAX_FILES:
            raise ValueError("ASSET_FILE_LIMIT")
        relative = item.relative_to(original)
        target = runtime / relative
        if item.is_symlink():
            resolved = item.resolve(strict=True)
            if not resolved.is_relative_to(original) or resolved.parts[len(original.parts)] not in FOLDERS:
                raise ValueError("ASSET_LINK_ESCAPE")
            projected = runtime / resolved.relative_to(original)
            target.symlink_to(os.path.relpath(projected, target.parent))
            manifest[relative.as_posix()] = {"linkTarget": os.readlink(target)}
        elif item.is_dir():
            target.mkdir(mode=0o755)
            pending.extend(sorted(item.iterdir(), reverse=True))
        else:
            logical += item.stat(follow_symlinks=False).st_size
            if logical > MAX_LOGICAL:
                raise ValueError("ASSET_LOGICAL_BYTE_LIMIT")
            manifest[relative.as_posix()] = copy_sparse(original, item, target)
    for name in ("bin/launch_cvd", "bin/stop_cvd", "super.img", "boot.img", "userdata.img"):
        if not (runtime / name).is_file():
            raise ValueError("ANDROID_REQUIRED_ARTIFACT_MISSING")
    apk = source_root / "aaos_digital_cluster/cuttlefish_emulator/apk/digital-cluster-app-debug.apk"
    apk = apk.resolve(strict=True)
    manifest["digital-cluster-app-debug.apk"] = copy_sparse(apk.parent, apk, destination / "digital-cluster-app-debug.apk", max_bytes=MAX_LOGICAL - logical)
    result = {"formatVersion": "1.0", "scope": "new isolated simulation test assets; no execution or live admission",
              "guestStateCopied": False, "logicalBytes": sum(row.get("logicalBytes", 0) for row in manifest.values()),
              "allocatedBytes": sum(row.get("allocatedBytes", 0) for row in manifest.values()), "files": manifest}
    (destination / "asset-manifest.json").write_text(json.dumps(result, indent=2) + "\n")
    (destination / "source-binding.private.json").write_text(json.dumps({"sourceRoot": str(source_root), "resolvedAndroidArtifactRoot": str(original), "resolvedApk": str(apk), "destination": str(destination)}, indent=2) + "\n")
    marker.unlink()
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-root", type=Path, required=True)
    parser.add_argument("--destination", type=Path, required=True)
    args = parser.parse_args()
    try:
        result = stage(args.source_root, args.destination)
    except (OSError, ValueError) as error:
        parser.exit(1, "Asset staging refused; preserve the original and any incomplete new root: " + str(error) + "\n")
    print(json.dumps({"files": len(result["files"]), "logicalBytes": result["logicalBytes"], "allocatedBytes": result["allocatedBytes"], "guestStateCopied": False}))


if __name__ == "__main__":
    main()
