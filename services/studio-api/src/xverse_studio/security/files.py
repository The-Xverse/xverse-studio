"""Portable, inert import boundary. No archive name is a native command/path."""

import base64
import io
import json
from pathlib import PurePosixPath
import re
import stat
import zipfile
import unicodedata
from xverse_studio.storage.core import Problem

MAX_BYTES = 8 * 1024 * 1024
MAX_EXPANDED = 16 * 1024 * 1024
MAX_FILES = 256
RESERVED = {
    "CON",
    "PRN",
    "AUX",
    "NUL",
    *(f"COM{i}" for i in range(10)),
    *(f"LPT{i}" for i in range(10)),
}
SECRET = re.compile(
    r'(?i)(?:["\']?(?:password|passwd|access[_-]?token|api[_-]?key|private[_-]?key|client[_-]?secret)["\']?\s*[:=]\s*["\']?[^\s"\',}]+|-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----|gh[pousr]_[A-Za-z0-9]{20,})'
)


def safe_name(name):
    if (
        not isinstance(name, str)
        or not name
        or len(name) > 240
        or "\\" in name
        or ":" in name
        or "\x00" in name
    ):
        raise Problem(
            "UNSAFE_PATH",
            "Portable paths must be bounded relative slash-separated names.",
        )
    p = PurePosixPath(name)
    if (
        p.is_absolute()
        or name.startswith("/")
        or any(x in ("", ".", "..") for x in name.split("/"))
    ):
        raise Problem(
            "UNSAFE_PATH", "Absolute, empty and parent-relative paths are rejected."
        )
    for x in p.parts:
        if (
            x.endswith((".", " "))
            or x.split(".")[0].upper() in RESERVED
            or any(ord(c) < 32 or c in '<>"|?*' for c in x)
        ):
            raise Problem(
                "UNSAFE_PATH", "The path is ambiguous on a supported native filesystem."
            )
    return name


def check_text(content):
    if len(content.encode()) > 1024 * 1024:
        raise Problem("LIMIT_EXCEEDED", "A document is limited to 1 MiB.", 413)
    if SECRET.search(content) or re.search(
        r"(?i)\b[a-z][a-z0-9+.-]*://[^/\s?#]*@", content
    ):
        raise Problem(
            "CREDENTIAL_REJECTED",
            "Remove inline credentials and use an external secret reference.",
        )
    return content


def read_archive(encoded):
    try:
        data = base64.b64decode(encoded, validate=True)
    except (ValueError, TypeError):
        raise Problem("INVALID_ARCHIVE", "Supply a base64 ZIP archive.") from None
    if len(data) > MAX_BYTES:
        raise Problem("LIMIT_EXCEEDED", "Compressed archive limit is 8 MiB.", 413)
    files = {}
    seen = set()
    total = 0
    try:
        with zipfile.ZipFile(io.BytesIO(data)) as z:
            if len(z.infolist()) > MAX_FILES:
                raise Problem("LIMIT_EXCEEDED", "Archive file limit exceeded.", 413)
            for info in z.infolist():
                raw = info.filename.rstrip("/") if info.is_dir() else info.filename
                name = safe_name(raw)
                norm = unicodedata.normalize("NFC", name).casefold()
                if norm in seen:
                    raise Problem(
                        "UNSAFE_ARCHIVE", "Duplicate portable path or case collision."
                    )
                seen.add(norm)
                if info.flag_bits & 1 or stat.S_ISLNK(info.external_attr >> 16):
                    raise Problem(
                        "UNSAFE_ARCHIVE", "Encrypted entries and links are rejected."
                    )
                if info.is_dir():
                    continue
                total += info.file_size
                if (
                    total > MAX_EXPANDED
                    or info.file_size > 1024 * 1024
                    or info.file_size / max(1, info.compress_size) > 100
                ):
                    raise Problem(
                        "LIMIT_EXCEEDED",
                        "Expanded size or compression ratio limit exceeded.",
                        413,
                    )
                if not (
                    name in ("project.studio.json", "artifacts.lock.json", "README.md")
                    or name.startswith(("xdl/", "profiles/", "layout/"))
                ):
                    raise Problem(
                        "UNSAFE_ARCHIVE",
                        "Only declared project document kinds may be imported.",
                    )
                if PurePosixPath(name).suffix.lower() not in (
                    ".yaml",
                    ".yml",
                    ".json",
                    ".md",
                ):
                    raise Problem(
                        "UNSAFE_ARCHIVE",
                        "Executable and unsupported file kinds are rejected.",
                    )
                text = z.read(info).decode("utf-8")
                check_text(text)
                if name.startswith("profiles/") and re.search(
                    r'(?i)(<script|javascript:|"(?:script|onload|onerror|exec|hooks)"\s*:)',
                    text,
                ):
                    raise Problem(
                        "UNSAFE_PROFILE",
                        "Profile presentation must be declarative and inert.",
                    )
                files[name] = text
    except (zipfile.BadZipFile, UnicodeError, RuntimeError):
        raise Problem("INVALID_ARCHIVE", "The archive cannot be read safely.") from None
    return files


def check_portable_text(content):
    """Reject host-only material on portable output without rewriting historical bytes."""
    check_text(content)
    if re.search(
        r"(?i)(?:file://|(?:^|[\s\"'=])(?:[a-z]:[\\/]|/(?:home|Users|tmp|var|etc|opt|mnt|media)/)|\\\\[a-z0-9_.-]+\\)",
        content,
    ):
        raise Problem(
            "HOST_BINDING_NOT_PORTABLE",
            "Move host-local paths and private bindings to local environment references before portable export.",
        )
    return content
