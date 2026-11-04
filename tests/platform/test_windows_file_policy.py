"""Portable lexical/ABI checks only; these do not exercise Windows native IO."""

import ctypes as c
from pathlib import PureWindowsPath
import struct
import sys

import pytest

from xverse_studio.security.managed_io import SafeIOError
from xverse_studio.security.windows_native import (
    DirectoryInfo,
    IOStatus,
    Native,
    ObjectAttributes,
    RenameInfo,
    UnicodeString,
    directory_names,
    rename_buffer,
)
from xverse_studio.security.windows_paths import absolute, component


@pytest.mark.parametrize(
    "name",
    [
        "",
        ".",
        "..",
        "x/y",
        "x\\y",
        "stream:data",
        "NUL.txt",
        "con",
        "COM1.yaml",
        "LPT¹",
        "COM².txt",
        "CONIN$",
        "x.",
        "x ",
        "x\0y",
        "x\ny",
        'x"y',
        "x?",
        "x*",
        "x|",
        "\ud800",
        "a" * 256,
        "🚙" * 128,
    ],
)
def test_unsafe_component_never_reaches_native_name_resolution(name):
    with pytest.raises(ValueError, match="UNSAFE_PATH"):
        component(name)


@pytest.mark.parametrize(
    "path",
    [
        "relative/file",
        "C:file",
        "\\file",
        "\\\\server\\share\\file",
        "\\\\?\\C:\\file",
        "\\\\.\\PhysicalDrive0",
        "C:\\a\\..\\file",
        "C:\\a\\.\\file",
        "C:\\a:stream",
        "C:\\NUL.txt",
        "C:\\space ",
        "C:\\link\\..\\outside",
        "Ä:\\file",
    ],
)
def test_only_explicit_local_drive_paths_are_admitted(path):
    with pytest.raises(ValueError, match="UNSAFE_PATH"):
        absolute(path)


def test_unicode_spaces_and_distinct_drives_retain_lexical_identity():
    assert absolute("D:/Native files Ω/🚙.json") == PureWindowsPath(
        "D:/Native files Ω/🚙.json"
    )
    assert component("a" * 255) == "a" * 255
    assert component("🚙" * 127 + "a") == "🚙" * 127 + "a"
    assert absolute("c:\\") == PureWindowsPath("C:/")


def test_native_abi_uses_windows_widths_on_this_architecture():
    if c.sizeof(c.c_void_p) == 8:
        assert (c.sizeof(UnicodeString), UnicodeString.Buffer.offset) == (16, 8)
        assert (
            c.sizeof(ObjectAttributes),
            ObjectAttributes.RootDirectory.offset,
            ObjectAttributes.SecurityDescriptor.offset,
        ) == (48, 8, 32)
        assert c.sizeof(IOStatus) == 16
        assert (
            RenameInfo.RootDirectory.offset,
            RenameInfo.FileNameLength.offset,
            RenameInfo.FileName.offset,
        ) == (8, 16, 20)
    else:
        assert (c.sizeof(UnicodeString), UnicodeString.Buffer.offset) == (8, 4)
        assert c.sizeof(ObjectAttributes) == 24
        assert c.sizeof(IOStatus) == 8
        assert (
            RenameInfo.RootDirectory.offset,
            RenameInfo.FileNameLength.offset,
            RenameInfo.FileName.offset,
        ) == (4, 8, 12)
    assert (DirectoryInfo.FileId.offset, DirectoryInfo.FileName.offset) == (96, 104)


def test_rename_abi_counts_utf16_bytes_and_keeps_a_single_relative_name():
    buffer = rename_buffer(1234, "Recorded Ω 🚙.json", False)
    info = RenameInfo.from_buffer(buffer)
    assert info.RootDirectory == 1234 and info.ReplaceIfExists == 0
    encoded = "Recorded Ω 🚙.json".encode("utf-16-le")
    assert info.FileNameLength == len(encoded)
    assert (
        buffer.raw[
            RenameInfo.FileName.offset : RenameInfo.FileName.offset + len(encoded) + 2
        ]
        == encoded + b"\0\0"
    )
    assert RenameInfo.from_buffer(rename_buffer(1234, "new", True)).ReplaceIfExists == 1
    with pytest.raises(ValueError):
        rename_buffer(1234, "other\\new", True)


def page(names):
    entries = []
    for index, name in enumerate(names):
        encoded = name.encode("utf-16-le")
        size = (104 + len(encoded) + 7) // 8 * 8
        entry = bytearray(size)
        struct.pack_into("<I", entry, 0, size if index + 1 < len(names) else 0)
        struct.pack_into("<I", entry, 60, len(encoded))
        entry[104 : 104 + len(encoded)] = encoded
        entries.append(entry)
    return b"".join(entries)


def test_native_enumeration_pages_are_bounded_and_preserve_unicode():
    assert directory_names(page([".", "..", "Original Ω 🚙.json", "sub"])) == [
        "Original Ω 🚙.json",
        "sub",
    ]


@pytest.mark.parametrize(
    "corruption",
    [
        "truncated-header",
        "odd-name",
        "past-buffer",
        "backward-entry",
        "unaligned-entry",
        "stream",
        "surrogate",
    ],
)
def test_malformed_native_directory_pages_are_refused(corruption):
    data = bytearray(page(["one", "two"]))
    if corruption == "truncated-header":
        data = data[:90]
    elif corruption == "odd-name":
        struct.pack_into("<I", data, 60, 3)
    elif corruption == "past-buffer":
        struct.pack_into("<I", data, 60, 510)
    elif corruption == "backward-entry":
        struct.pack_into("<I", data, 0, 8)
    elif corruption == "unaligned-entry":
        struct.pack_into("<I", data, 0, 111)
    elif corruption == "stream":
        data = bytearray(page(["a:b"]))
    else:
        data[104:106] = b"\0\xd8"
    with pytest.raises(ValueError):
        directory_names(bytes(data))


@pytest.mark.skipif(sys.platform == "win32", reason="Non-Windows refusal only")
def test_native_engine_cannot_be_instantiated_as_a_linux_simulation():
    with pytest.raises(SafeIOError) as failure:
        Native()
    assert failure.value.code == "SECURE_IO_UNAVAILABLE"
