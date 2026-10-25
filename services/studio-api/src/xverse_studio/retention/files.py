"""Bounded managed-file proofs for local retention; no origin URL is opened."""

from __future__ import annotations

import hashlib
import os
from pathlib import Path
import stat

from xverse_studio.storage.core import canonical

MAX_PROOF_BYTES = 64 * 1024 * 1024
MAX_PROOF_FILES = 20_000
MAX_DEPENDENCY_RECORDS = 10_000


class ProofLimit(ValueError):
    pass


class ProofBudget:
    def __init__(self):
        self.bytes = 0
        self.files = 0
        self.records = 0

    def record(self):
        self.records += 1
        if self.records > MAX_DEPENDENCY_RECORDS:
            raise ProofLimit("RETENTION_PROOF_LIMIT")

    def file(self):
        self.files += 1
        if self.files > MAX_PROOF_FILES:
            raise ProofLimit("RETENTION_PROOF_LIMIT")

    def read(self, amount):
        self.bytes += amount
        if self.bytes > MAX_PROOF_BYTES:
            raise ProofLimit("RETENTION_PROOF_LIMIT")


def managed_path(root: Path, target: Path) -> Path:
    """Reject both external and within-root symlink/junction redirection."""
    root = root.resolve()
    if not target.is_absolute():
        target = root / target
    relative = target.relative_to(root)
    current = root
    for part in relative.parts:
        if part in {"", ".", ".."}:
            raise ValueError("UNSAFE_RETAINED_PATH")
        current = current / part
        if current.is_symlink() or getattr(current, "is_junction", lambda: False)():
            raise ValueError("UNSAFE_RETAINED_PATH")
    if not target.resolve().is_relative_to(root):
        raise ValueError("UNSAFE_RETAINED_PATH")
    return target


def inspect_tree(
    root: Path, target: Path, budget: ProofBudget, *, collect_names=False
) -> dict:
    entries, reasons, total_bytes, file_count = [], [], 0, 0
    try:
        target = managed_path(root, target)
        device = root.stat().st_dev
        if not target.exists():
            return {
                "exists": False,
                "fingerprint": "sha256:" + hashlib.sha256(b"missing").hexdigest(),
                "byteCount": 0,
                "fileCount": 0,
                "blockedReasons": [],
            }
        budget.file()
        pending = [(target, ".")]
        while pending:
            path, relative = pending.pop()
            current = path.lstat()
            if stat.S_ISLNK(current.st_mode) or current.st_dev != device:
                reasons.append("UNSAFE_RETAINED_PATH")
                entries.append({"path": relative, "type": "unsafe"})
                continue
            if stat.S_ISDIR(current.st_mode):
                entries.append(
                    {
                        "path": relative,
                        "type": "directory",
                        "mode": stat.S_IMODE(current.st_mode),
                        "inode": current.st_ino,
                    }
                )
                with os.scandir(path) as scan:
                    children = []
                    for child in scan:
                        budget.file()
                        children.append(child)
                    children.sort(key=lambda item: item.name)
                for child in reversed(children):
                    child_relative = (
                        child.name if relative == "." else relative + "/" + child.name
                    )
                    pending.append((Path(child.path), child_relative))
            elif stat.S_ISREG(current.st_mode) and current.st_nlink == 1:
                flags = (
                    os.O_RDONLY
                    | getattr(os, "O_NOFOLLOW", 0)
                    | getattr(os, "O_NONBLOCK", 0)
                )
                descriptor = os.open(path, flags)
                try:
                    opened = os.fstat(descriptor)
                    if not stat.S_ISREG(opened.st_mode) or (
                        opened.st_dev,
                        opened.st_ino,
                    ) != (current.st_dev, current.st_ino):
                        raise ValueError("UNSAFE_RETAINED_PATH")
                    checksum = hashlib.sha256()
                    budget.read(opened.st_size)  # Reserve before any allocation/read.
                    remaining = opened.st_size
                    while remaining:
                        chunk = os.read(descriptor, min(1024 * 1024, remaining))
                        if not chunk:
                            raise ValueError("FILES_CHANGED_DURING_PROOF")
                        checksum.update(chunk)
                        remaining -= len(chunk)
                    after = os.fstat(descriptor)
                    if (opened.st_size, opened.st_mtime_ns, opened.st_ctime_ns) != (
                        after.st_size,
                        after.st_mtime_ns,
                        after.st_ctime_ns,
                    ):
                        raise ValueError("FILES_CHANGED_DURING_PROOF")
                finally:
                    os.close(descriptor)
                total_bytes += opened.st_size
                file_count += 1
                entries.append(
                    {
                        "path": relative,
                        "type": "file",
                        "size": opened.st_size,
                        "mtime": opened.st_mtime_ns,
                        "ctime": opened.st_ctime_ns,
                        "mode": stat.S_IMODE(opened.st_mode),
                        "inode": opened.st_ino,
                        "digest": "sha256:" + checksum.hexdigest(),
                    }
                )
            else:
                reasons.append("UNSAFE_RETAINED_PATH")
                entries.append({"path": relative, "type": "unsupported"})
    except ProofLimit:
        raise
    except (OSError, ValueError):
        reasons.append("FILESYSTEM_INSPECTION_UNAVAILABLE")
    fingerprint = "sha256:" + hashlib.sha256(canonical(entries).encode()).hexdigest()
    result = {
        "exists": True,
        "fingerprint": fingerprint,
        "byteCount": total_bytes,
        "fileCount": file_count,
        "blockedReasons": sorted(set(reasons)),
    }
    if collect_names:
        result["fileNames"] = [
            entry["path"] for entry in entries if entry["type"] == "file"
        ]
    return result


def read_bounded(
    root: Path, path: Path, budget: ProofBudget, *, limit=16 * 1024 * 1024
) -> bytes:
    path = managed_path(root, path)
    descriptor = os.open(
        path, os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0) | getattr(os, "O_NONBLOCK", 0)
    )
    try:
        opened = os.fstat(descriptor)
        if (
            not stat.S_ISREG(opened.st_mode)
            or opened.st_nlink != 1
            or opened.st_dev != root.stat().st_dev
        ):
            raise ValueError("UNSAFE_RETAINED_PATH")
        if opened.st_size > limit:
            raise ProofLimit("RETENTION_PROOF_LIMIT")
        budget.file()
        budget.read(opened.st_size)  # Charge before allocation.
        remaining, chunks = opened.st_size, []
        while remaining:
            chunk = os.read(descriptor, min(1024 * 1024, remaining))
            if not chunk:
                raise ValueError("FILES_CHANGED_DURING_PROOF")
            chunks.append(chunk)
            remaining -= len(chunk)
        after = os.fstat(descriptor)
        if (opened.st_size, opened.st_mtime_ns, opened.st_ctime_ns) != (
            after.st_size,
            after.st_mtime_ns,
            after.st_ctime_ns,
        ):
            raise ValueError("FILES_CHANGED_DURING_PROOF")
        return b"".join(chunks)
    finally:
        os.close(descriptor)
