"""Owned local-file locks only; no model, provider, simulator or device execution."""

from contextlib import contextmanager
import errno
import os
import subprocess
import sys

import pytest

from xverse_studio.host.ownership import own_root, RootOwnedError, RootUnsafeError
from xverse_studio.security.managed_io import (
    AnchoredDirectory,
    SafeIOError,
    open_directory,
)

pytestmark = pytest.mark.skipif(
    not sys.platform.startswith("linux"),
    reason="Linux root ownership regression; Windows has explicit native cases",
)


def test_hardlinked_lock_cannot_confer_workspace_ownership(tmp_path):
    root, outside = tmp_path / "root", tmp_path / "outside"
    root.mkdir()
    outside.write_bytes(b"preserve outside bytes")
    os.link(outside, root / "studio.lock")
    with pytest.raises(RootUnsafeError, match="RECOVERY_UNSAFE_FILE"):
        with own_root(root):
            pytest.fail("hardlinked lock admitted")
    assert outside.read_bytes() == b"preserve outside bytes"


def test_symlinked_ancestor_cannot_create_an_outside_lock(tmp_path):
    outside = tmp_path / "outside"
    outside.mkdir()
    alias = tmp_path / "alias"
    alias.symlink_to(outside, target_is_directory=True)
    with pytest.raises(RootUnsafeError, match="RECOVERY_UNSAFE_FILE"):
        with own_root(alias):
            pytest.fail("link ancestor admitted")
    assert not (outside / "studio.lock").exists()


@pytest.mark.skipif(
    not sys.platform.startswith("linux"), reason="Native Linux acquisition race"
)
def test_replaced_lock_between_open_and_lock_cannot_report_ownership(
    tmp_path, monkeypatch
):
    import fcntl

    root = tmp_path / "root"
    root.mkdir()
    lock = root / "studio.lock"
    lock.write_bytes(b"original lock bytes")
    held = root / "original-lock"
    original = fcntl.flock
    swaps = []

    def raced(descriptor, flags):
        if not swaps:
            swaps.append(True)
            lock.rename(held)
            lock.write_bytes(b"replacement bytes")
        return original(descriptor, flags)

    monkeypatch.setattr(fcntl, "flock", raced)
    with pytest.raises(RootUnsafeError, match="RECOVERY_UNSAFE_FILE"):
        with own_root(root):
            pytest.fail("replaced lock admitted")
    assert swaps and held.read_bytes() == b"original lock bytes"
    assert lock.read_bytes() == b"replacement bytes"


def test_existing_lock_contents_and_identity_survive_refused_second_owner(tmp_path):
    root = tmp_path / "root"
    root.mkdir()
    lock = root / "studio.lock"
    lock.write_bytes(b"original metadata is never a lock payload")
    identity = lock.stat().st_ino
    with own_root(root):
        with pytest.raises(RootOwnedError, match="RECOVERY_ROOT_OWNED"):
            with own_root(root):
                pytest.fail("second owner admitted")
    assert lock.read_bytes() == b"original metadata is never a lock payload"
    assert lock.stat().st_ino == identity
    with own_root(root):
        pass


def test_real_child_process_refuses_while_original_owner_holds_lock(tmp_path):
    root = tmp_path / "root"
    root.mkdir()
    child = """import sys
from pathlib import Path
from xverse_studio.host.ownership import own_root, RootOwnedError
try:
    with own_root(Path(sys.argv[1])):
        raise SystemExit(9)
except RootOwnedError:
    raise SystemExit(0)
"""
    with own_root(root):
        completed = subprocess.run(
            [sys.executable, "-I", "-c", child, str(root)],
            capture_output=True,
            text=True,
            timeout=15,
        )
    assert completed.returncode == 0, completed.stderr
    assert (root / "studio.lock").read_bytes() == b""


@pytest.mark.skipif(
    not sys.platform.startswith("linux"), reason="Native Linux file locking error"
)
def test_unavailable_file_lock_is_not_reported_as_another_owner(tmp_path, monkeypatch):
    import fcntl

    def unsupported(*args):
        raise OSError(errno.EOPNOTSUPP, "controlled unsupported native primitive")

    monkeypatch.setattr(fcntl, "flock", unsupported)
    with pytest.raises(RootUnsafeError, match="RECOVERY_SECURE_IO_UNAVAILABLE"):
        with own_root(tmp_path):
            pytest.fail("unsupported primitive admitted")


@pytest.mark.skipif(
    not sys.platform.startswith("linux"), reason="Native Linux pinned directory rename"
)
def test_explicit_anchor_locks_original_directory_after_name_replacement(tmp_path):
    root, held = tmp_path / "root", tmp_path / "held"
    root.mkdir()
    with open_directory(tmp_path, root) as descriptor:
        anchor = AnchoredDirectory(root, descriptor)
        root.rename(held)
        root.mkdir()
        with own_root(anchor):
            assert (held / "studio.lock").is_file()
            assert not (root / "studio.lock").exists()
            with pytest.raises(RootOwnedError):
                with own_root(held):
                    pytest.fail("original root was not locked")


@pytest.mark.parametrize("native_error", [False, True])
def test_ownership_context_preserves_callers_original_exception_and_releases(
    tmp_path, native_error
):
    marker = (
        SafeIOError("UNSAFE_PATH")
        if native_error
        else OSError("controlled caller failure")
    )
    with pytest.raises(OSError) as failure:
        with own_root(tmp_path):
            raise marker
    assert failure.value is marker
    with own_root(tmp_path):
        pass


def test_lock_name_change_during_operation_is_a_workspace_error(tmp_path):
    with pytest.raises(RootUnsafeError, match="RECOVERY_UNSAFE_FILE"):
        with own_root(tmp_path):
            lock = tmp_path / "studio.lock"
            lock.rename(tmp_path / "retained-lock")
            lock.write_bytes(b"unrelated replacement")
    assert (tmp_path / "studio.lock").read_bytes() == b"unrelated replacement"


def test_lock_descriptor_is_private_and_not_inherited(tmp_path, monkeypatch):
    if not sys.platform.startswith("linux"):
        pytest.skip("Linux descriptor observation; Windows has separate native cases")
    import fcntl

    observed = []
    original = fcntl.flock

    def inspect(descriptor, flags):
        observed.append(
            (os.get_inheritable(descriptor), os.fstat(descriptor).st_mode & 0o777)
        )
        return original(descriptor, flags)

    monkeypatch.setattr(fcntl, "flock", inspect)
    with own_root(tmp_path):
        pass
    assert observed == [(False, 0o600)]


def test_recovery_passes_the_acquired_directory_to_ownership(tmp_path, monkeypatch):
    from xverse_studio.host import recovery
    from xverse_studio.storage.core import Store

    root = tmp_path / "source"
    Store(root).put("marker", "owned", {"value": "original"})
    observed = []

    @contextmanager
    def checked(root):
        assert isinstance(root, AnchoredDirectory)
        observed.append(root.path)
        with own_root(root) as anchor:
            yield anchor

    monkeypatch.setattr(recovery, "own_root", checked)
    recovery.backup_full(root, tmp_path / "backup")
    assert observed == [root]


def test_launcher_refuses_a_linked_root_before_constructing_the_application(
    tmp_path, monkeypatch
):
    from xverse_studio.host import launcher

    outside, alias = tmp_path / "outside", tmp_path / "alias"
    outside.mkdir()
    alias.symlink_to(outside, target_is_directory=True)

    def forbidden(*args):
        pytest.fail("application constructed through a linked root")

    monkeypatch.setattr(launcher, "_owned_main", forbidden)
    monkeypatch.setattr(sys, "argv", ["studio", "--data-dir", str(alias)])
    with pytest.raises(SystemExit) as failure:
        launcher.main()
    assert failure.value.code == 2
    assert not (outside / "studio.lock").exists()


@pytest.mark.parametrize("existing", [False, True])
def test_launcher_prepares_a_private_root_and_holds_it_before_application(
    tmp_path, monkeypatch, existing
):
    from xverse_studio.host import launcher

    root = tmp_path / "new private root Ω"
    if existing:
        root.mkdir(mode=0o755)
    observed = []

    def checked(args, path, parser):
        assert path == root
        if os.name != "nt":
            assert root.stat().st_mode & 0o777 == 0o700
        with pytest.raises(RootOwnedError):
            with own_root(root):
                pytest.fail("launcher did not own the workspace")
        observed.append(True)

    monkeypatch.setattr(launcher, "_owned_main", checked)
    monkeypatch.setattr(sys, "argv", ["studio", "--data-dir", str(root)])
    launcher.main()
    assert observed == [True]


def test_refused_contender_does_not_change_root_permissions(tmp_path):
    with own_root(tmp_path):
        tmp_path.chmod(0o750)
        try:
            with pytest.raises(RootOwnedError):
                with own_root(tmp_path):
                    pytest.fail("contender admitted")
            assert tmp_path.stat().st_mode & 0o777 == 0o750
        finally:
            tmp_path.chmod(0o700)


def test_launcher_checks_incomplete_restore_under_the_acquired_root_lock(
    tmp_path, monkeypatch
):
    from xverse_studio.host import launcher

    root = tmp_path / "incomplete"
    root.mkdir()
    (root / ".recovery-incomplete").write_bytes(b"preserve incomplete restore")
    observed = []

    @contextmanager
    def checked(root):
        assert isinstance(root, AnchoredDirectory)
        with own_root(root) as anchor:
            observed.append(True)
            yield anchor

    monkeypatch.setattr(launcher, "own_root", checked)
    monkeypatch.setattr(sys, "argv", ["studio", "--data-dir", str(root)])
    with pytest.raises(SystemExit) as failure:
        launcher.main()
    assert failure.value.code == 2 and observed == [True]
    assert (
        root / ".recovery-incomplete"
    ).read_bytes() == b"preserve incomplete restore"
