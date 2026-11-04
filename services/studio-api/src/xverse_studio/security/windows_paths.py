"""Lexical policy for the local Windows secure-file backend; no filesystem IO."""

from pathlib import PureWindowsPath


_DEVICES = {"CON", "PRN", "AUX", "NUL", "CONIN$", "CONOUT$", "CLOCK$"}
_DEVICES.update(
    f"{prefix}{number}" for prefix in ("COM", "LPT") for number in "123456789¹²³"
)


def component(name):
    """Reject alternate streams, namespace syntax and Win32 aliases before NT IO."""
    if (
        not isinstance(name, str)
        or not name
        or name in {".", ".."}
        or name[-1] in " ."
        or any(ord(char) < 32 or char in '<>:"/\\|?*' for char in name)
        or name.split(".", 1)[0].rstrip(" ").upper() in _DEVICES
    ):
        raise ValueError("UNSAFE_PATH")
    try:
        if len(name.encode("utf-16-le")) > 510:
            raise ValueError("UNSAFE_PATH")
    except UnicodeEncodeError:
        raise ValueError("UNSAFE_PATH") from None
    return name


def absolute(path):
    """Only explicit local drive roots; never UNC, devices or drive-relative names."""
    raw = str(path).replace("/", "\\")
    if (
        len(raw) < 3
        or not raw[0].isascii()
        or not raw[0].isalpha()
        or raw[1:3] != ":\\"
        or any(part in {".", ".."} for part in raw[3:].split("\\"))
    ):
        raise ValueError("UNSAFE_PATH")
    result = PureWindowsPath(raw)
    for part in result.parts[1:]:
        component(part)
    if len(raw.encode("utf-16-le")) > 65520:
        raise ValueError("UNSAFE_PATH")
    return result
