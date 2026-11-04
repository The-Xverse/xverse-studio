"""Owned temporary NTFS files only; MUST run natively on Windows, never emulated.

Linux collection skips are not native evidence. No provider/workload/device access.
"""

import ctypes as c
import os
from pathlib import Path
import struct
import sys

import pytest

from xverse_studio.security.managed_io import (
    SafeIOError,
    atomic_write,
    create_directory,
    make_directory,
    open_directory,
    open_read,
    open_write,
    publish_directory,
    read_bounded,
    remove_tree,
    stat_file,
    unlink,
)
from xverse_studio.security.windows_native import ObjectAttributes, native


pytestmark = pytest.mark.skipif(
    sys.platform != "win32",
    reason="Requires real native Windows/NTFS; NOT_RUN on Linux",
)


def test_private_create_read_replace_and_exact_binary_payload(tmp_path):
    path = tmp_path / "Original files Ω" / "🚙.bin"
    payload = b"original\r\n\0" + bytes(range(256))
    with open_write(tmp_path, path, parents=True) as stream:
        assert stream.write(payload) == len(payload)
        assert not os.get_inheritable(stream.fileno())
        native().verify_private(stream.fileno())
    assert read_bounded(tmp_path, path, len(payload)) == payload
    with pytest.raises(SafeIOError, match="LIMIT_EXCEEDED"):
        read_bounded(tmp_path, path, len(payload) - 1)
    with pytest.raises(SafeIOError, match="TARGET_EXISTS"):
        with open_write(tmp_path, path):
            pytest.fail("exclusive create replaced an existing file")
    atomic_write(tmp_path, path, b"replacement")
    assert read_bounded(tmp_path, path, 100) == b"replacement"
    unlink(tmp_path, path)
    assert not path.exists()


def test_all_held_ancestors_and_open_file_names_refuse_replacement(tmp_path):
    parent = tmp_path / "owned" / "sub"
    parent.mkdir(parents=True)
    path = parent / "value"
    path.write_bytes(b"owned")
    with open_read(tmp_path, path) as stream:
        for original in (path, parent, parent.parent):
            with pytest.raises(OSError):
                original.rename(original.with_name(original.name + ".foreign"))
        with pytest.raises(OSError):
            path.write_bytes(b"foreign")
        assert stream.read() == b"owned"
    assert path.read_bytes() == b"owned"


def test_acquired_directory_lifetime_and_identity_checked_publication(tmp_path):
    stage, target = tmp_path / "stage", tmp_path / "published"
    with create_directory(tmp_path, stage) as anchor:
        identity = os.fstat(anchor.descriptor)
        assert not os.get_inheritable(anchor.descriptor)
        native().verify_private(anchor.descriptor)
        atomic_write(anchor, stage / "value", b"owned")
        assert stat_file(anchor, stage / "value").st_size == 5
        with pytest.raises(OSError):
            stage.rename(tmp_path / "moved")
    wrong = (identity.st_dev, identity.st_ino + 1)
    with pytest.raises(SafeIOError, match="SOURCE_CHANGED"):
        publish_directory(tmp_path, stage, target, expected_identity=wrong)
    publish_directory(
        tmp_path, stage, target, expected_identity=(identity.st_dev, identity.st_ino)
    )
    assert not stage.exists() and (target / "value").read_bytes() == b"owned"
    with pytest.raises(SafeIOError, match="SOURCE_CHANGED"):
        remove_tree(tmp_path, target, expected_identity=wrong)
    assert target.is_dir()
    remove_tree(tmp_path, target, expected_identity=(identity.st_dev, identity.st_ino))
    assert not target.exists()


def test_publication_never_overwrites_an_existing_target(tmp_path):
    stage, target = tmp_path / "stage", tmp_path / "target"
    make_directory(tmp_path, stage, exclusive=True)
    make_directory(tmp_path, target, exclusive=True)
    atomic_write(tmp_path, target / "sentinel", b"preserve")
    info = stage.stat()
    with pytest.raises(SafeIOError, match="TARGET_EXISTS"):
        publish_directory(
            tmp_path, stage, target, expected_identity=(info.st_dev, info.st_ino)
        )
    assert stage.is_dir() and (target / "sentinel").read_bytes() == b"preserve"
    make_directory(tmp_path, target)  # Existing protected owner-only ACL accepted.


def test_hardlinks_and_outside_paths_are_never_consumed_or_deleted(tmp_path):
    root, outside = tmp_path / "root", tmp_path / "outside"
    root.mkdir()
    outside.write_bytes(b"outside original")
    linked = root / "linked"
    os.link(outside, linked)
    for action in (
        lambda: read_bounded(root, linked, 100),
        lambda: atomic_write(root, linked, b"changed"),
        lambda: unlink(root, linked),
        lambda: read_bounded(root, outside, 100),
        lambda: remove_tree(tmp_path, root),
    ):
        with pytest.raises(SafeIOError):
            action()
    assert outside.read_bytes() == b"outside original" and linked.exists()
    assert not list(root.glob(".*.tmp"))


def junction(root, link, target, *, existing=False):
    """Create only this owned inert junction, without cmd/mklink or privileges."""
    if not existing:
        make_directory(root, link, exclusive=True)
    api = native()
    device_io = api.kernel.DeviceIoControl
    device_io.argtypes = [
        c.c_void_p,
        c.c_uint32,
        c.c_void_p,
        c.c_uint32,
        c.c_void_p,
        c.c_uint32,
        c.POINTER(c.c_uint32),
        c.c_void_p,
    ]
    device_io.restype = c.c_int32
    substitute = ("\\??\\" + str(target)).encode("utf-16-le")
    printable = str(target).encode("utf-16-le")
    names = substitute + b"\0\0" + printable + b"\0\0"
    data = (
        struct.pack(
            "<IHHHHHH",
            0xA0000003,
            8 + len(names),
            0,
            0,
            len(substitute),
            len(substitute) + 2,
            len(printable),
        )
        + names
    )
    buffer = c.create_string_buffer(data)
    with open_directory(root, link.parent) as parent:
        descriptor = api.acquire(parent, link.name, directory=True, writable=True)
        try:
            returned = c.c_uint32()
            if not device_io(
                api.handle(descriptor),
                0x900A4,
                buffer,
                len(data),
                None,
                0,
                c.byref(returned),
                None,
            ):
                api.fail()
        finally:
            os.close(descriptor)


def test_real_junctions_block_every_path_component_and_recursive_delete(tmp_path):
    root, outside = tmp_path / "root", tmp_path / "outside"
    root.mkdir()
    outside.mkdir()
    (outside / "sentinel").write_bytes(b"preserve outside")
    link = root / "redirect"
    junction(tmp_path, link, outside)
    try:
        for action in (
            lambda: read_bounded(root, link / "sentinel", 100),
            lambda: atomic_write(root, link / "new", b"foreign"),
            lambda: stat_file(root, link),
            lambda: remove_tree(tmp_path, root),
        ):
            with pytest.raises(SafeIOError, match="UNSAFE_PATH"):
                action()
        assert (outside / "sentinel").read_bytes() == b"preserve outside"
        assert sorted(p.name for p in outside.iterdir()) == ["sentinel"]
    finally:
        os.rmdir(link)  # Removes only the owned junction entry, never its target.


def test_existing_inherited_acl_is_refused_without_broadening_it(tmp_path):
    parent = tmp_path / "protected"
    make_directory(tmp_path, parent, exclusive=True)
    inherited = parent / "inherited"
    inherited.mkdir()
    with pytest.raises(SafeIOError, match="UNSAFE_PATH"):
        make_directory(tmp_path, inherited)
    assert inherited.is_dir()


def test_parent_reparse_mutation_at_native_acquisition_cannot_supply_outside_bytes(
    tmp_path, monkeypatch
):
    root, outside = tmp_path / "root", tmp_path / "outside"
    root.mkdir()
    outside.mkdir()
    (outside / "sentinel").write_bytes(b"outside bytes must not be consumed")
    parent = root / "inside"
    make_directory(tmp_path, parent, exclusive=True)
    api, delivered = native(), []
    acquire = api.NtCreateFile

    def raced(handle, access, attributes, *arguments):
        info = c.cast(attributes, c.POINTER(ObjectAttributes)).contents
        text = info.ObjectName.contents
        name = c.string_at(text.Buffer, text.Length).decode("utf-16-le")
        if name == "sentinel" and not delivered:
            delivered.append(True)
            # Delivered after the parent's type/tag check, before the actual
            # single-component NT call. Refusal or original-directory lookup is
            # safe; following the newly attached target must fail this test.
            junction(tmp_path, parent, outside, existing=True)
        return acquire(handle, access, attributes, *arguments)

    monkeypatch.setattr(api, "NtCreateFile", raced)
    try:
        with pytest.raises(SafeIOError):
            read_bounded(root, parent / "sentinel", 100)
        assert delivered == [True]
        assert (
            outside / "sentinel"
        ).read_bytes() == b"outside bytes must not be consumed"
    finally:
        if parent.is_junction():
            os.rmdir(parent)


def test_stream_context_keeps_the_callers_original_exception(tmp_path):
    path = tmp_path / "value"
    atomic_write(tmp_path, path, b"owned")
    marker = OSError("controlled caller failure")
    with pytest.raises(OSError) as failure:
        with open_read(tmp_path, path):
            raise marker
    assert failure.value is marker


def test_recursive_cleanup_enumerates_more_than_one_native_page(tmp_path):
    root = tmp_path / "many owned files"
    make_directory(tmp_path, root, exclusive=True)
    for index in range(700):
        atomic_write(tmp_path, root / f"owned-{index:04}.json", b"inert bytes")
    with open_directory(tmp_path, root) as descriptor:
        names = list(native().names(descriptor))
    assert len(names) == 700 and len(set(names)) == 700
    assert "owned-0000.json" in names and "owned-0699.json" in names
    remove_tree(tmp_path, root)
    assert not root.exists()


def test_drive_root_is_taken_from_the_destination(tmp_path, monkeypatch):
    from xverse_studio.storage import core

    path = tmp_path / "stored value Ω"
    calls = []
    from xverse_studio.security import managed_io

    original = managed_io.atomic_write

    def observed(root, destination, data):
        calls.append((root, destination))
        return original(root, destination, data)

    monkeypatch.setattr(managed_io, "atomic_write", observed)
    core.atomic(path, b"persisted")
    assert calls == [(Path(path.anchor), path)]
    assert path.read_bytes() == b"persisted"
