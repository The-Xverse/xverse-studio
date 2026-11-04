"""Native anchored file acquisition. Unsupported hosts fail explicitly, never fall back.

Linux walks directory descriptors from the filesystem root with O_NOFOLLOW at
EVERY component. Opening only the final filename with O_NOFOLLOW is insufficient.
Windows delegates to native single-component handle acquisition. Its native
verification remains open (ADR-0067). No implementation resolves links or executes
imported content, and unavailable native primitives never select a weaker fallback.
"""

from contextlib import contextmanager
import ctypes
from dataclasses import dataclass
import errno
import io
import os
from pathlib import Path
import shutil
import stat
import sys
import uuid


_DIR_FD_AVAILABLE = os.open in os.supports_dir_fd


@dataclass(frozen=True)
class AnchoredDirectory:
    path: Path
    descriptor: int


class SafeIOError(OSError):
    def __init__(self, code):
        self.code = code
        super().__init__(code)


def _supported():
    if (
        not sys.platform.startswith("linux")
        or not hasattr(os, "O_NOFOLLOW")
        or not hasattr(os, "O_DIRECTORY")
        or not _DIR_FD_AVAILABLE
    ):
        raise SafeIOError("SECURE_IO_UNAVAILABLE")


def _absolute(path):
    path = Path(path).absolute()
    if ".." in path.parts or path.anchor != "/":
        raise SafeIOError("UNSAFE_PATH")
    return path


def _error(exc):
    if isinstance(exc, SafeIOError):
        return exc
    if isinstance(exc, FileNotFoundError):
        return SafeIOError("FILE_MISSING")
    if isinstance(exc, FileExistsError):
        return SafeIOError("TARGET_EXISTS")
    return SafeIOError("UNSAFE_PATH")


def _directory_flags():
    return os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW | getattr(os, "O_CLOEXEC", 0)


def _root_descriptor(root):
    _supported()
    root = _absolute(root)
    descriptor = os.open("/", _directory_flags())
    try:
        for name in root.parts[1:]:
            expected = os.stat(name, dir_fd=descriptor, follow_symlinks=False)
            next_descriptor = os.open(name, _directory_flags(), dir_fd=descriptor)
            if _identity(os.fstat(next_descriptor)) != _identity(expected):
                os.close(next_descriptor)
                raise SafeIOError("SOURCE_CHANGED")
            os.close(descriptor)
            descriptor = next_descriptor
        return descriptor
    except BaseException:
        os.close(descriptor)
        raise


@contextmanager
def _parent(root, path, *, create=False):
    descriptor = None
    caller_failed = False
    try:
        anchor = root if isinstance(root, AnchoredDirectory) else None
        root, path = _absolute(anchor.path if anchor else root), _absolute(path)
        try:
            relative = path.relative_to(root)
        except ValueError:
            raise SafeIOError("UNSAFE_PATH") from None
        if not relative.parts:
            raise SafeIOError("UNSAFE_PATH")
        descriptor = os.dup(anchor.descriptor) if anchor else _root_descriptor(root)
        for name in relative.parts[:-1]:
            if create:
                try:
                    os.mkdir(name, 0o700, dir_fd=descriptor)
                except FileExistsError:
                    pass
            expected = os.stat(name, dir_fd=descriptor, follow_symlinks=False)
            next_descriptor = os.open(name, _directory_flags(), dir_fd=descriptor)
            if _identity(os.fstat(next_descriptor)) != _identity(expected):
                os.close(next_descriptor)
                raise SafeIOError("SOURCE_CHANGED")
            os.close(descriptor)
            descriptor = next_descriptor
        try:
            yield descriptor, relative.parts[-1]
        except BaseException:
            caller_failed = True
            raise
    except OSError as exc:
        if caller_failed:
            raise
        raise _error(exc) from None
    finally:
        if descriptor is not None:
            os.close(descriptor)


def _identity(info):
    return info.st_dev, info.st_ino, stat.S_IFMT(info.st_mode), info.st_nlink


def _state(info):
    return (
        _identity(info),
        info.st_size,
        info.st_mtime_ns,
        info.st_ctime_ns,
        stat.S_IMODE(info.st_mode),
    )


@contextmanager
def open_directory(root, path):
    if sys.platform == "win32":
        from . import windows_io

        with windows_io.open_directory(root, path) as descriptor:
            yield descriptor
        return
    descriptor = None
    caller_failed = False
    try:
        anchor = root if isinstance(root, AnchoredDirectory) else None
        root_path, path = _absolute(anchor.path if anchor else root), _absolute(path)
        if path == root_path:
            descriptor = (
                os.dup(anchor.descriptor) if anchor else _root_descriptor(root_path)
            )
        else:
            with _parent(root, path) as (parent, name):
                expected = os.stat(name, dir_fd=parent, follow_symlinks=False)
                descriptor = os.open(name, _directory_flags(), dir_fd=parent)
                if _identity(os.fstat(descriptor)) != _identity(expected):
                    raise SafeIOError("SOURCE_CHANGED")
        try:
            yield descriptor
        except BaseException:
            caller_failed = True
            raise
    except OSError as exc:
        if caller_failed:
            raise
        raise _error(exc) from None
    finally:
        if descriptor is not None:
            os.close(descriptor)


@contextmanager
def open_read(root, path):
    """Yield a binary stream bound to a regular, unchanged, named inode."""
    if sys.platform == "win32":
        from . import windows_io

        with windows_io.open_read(root, path) as stream:
            yield stream
        return
    with _parent(root, path) as (parent, name):
        descriptor = None
        caller_failed = False
        try:
            expected = os.stat(name, dir_fd=parent, follow_symlinks=False)
            if not stat.S_ISREG(expected.st_mode) or expected.st_nlink != 1:
                raise SafeIOError("UNSAFE_PATH")
            descriptor = os.open(
                name,
                os.O_RDONLY
                | os.O_NOFOLLOW
                | getattr(os, "O_NONBLOCK", 0)
                | getattr(os, "O_CLOEXEC", 0),
                dir_fd=parent,
            )
            opened = os.fstat(descriptor)
            if _state(opened) != _state(expected):
                raise SafeIOError("SOURCE_CHANGED")
            with io.FileIO(descriptor, "rb", closefd=False) as stream:
                try:
                    yield stream
                except BaseException:
                    caller_failed = True
                    raise
                if _state(os.fstat(descriptor)) != _state(opened) or _identity(
                    os.stat(name, dir_fd=parent, follow_symlinks=False)
                ) != _identity(opened):
                    raise SafeIOError("SOURCE_CHANGED")
        except OSError as exc:
            if caller_failed:
                raise
            raise _error(exc) from None
        finally:
            if descriptor is not None:
                os.close(descriptor)


def read_bounded(root, path, maximum):
    """Capture one anchored regular file, including growth, within a byte cap."""
    with open_read(root, path) as stream:
        if os.fstat(stream.fileno()).st_size > maximum:
            raise SafeIOError("LIMIT_EXCEEDED")
        chunks, size = [], 0
        while True:
            chunk = stream.read(min(65536, maximum + 1 - size))
            if not chunk:
                break
            chunks.append(chunk)
            size += len(chunk)
            if size > maximum:
                raise SafeIOError("LIMIT_EXCEEDED")
        data = b"".join(chunks)
    return data


@contextmanager
def open_write(root, path, *, parents=False):
    """Exclusively create a private regular file through anchored directories."""
    if sys.platform == "win32":
        from . import windows_io

        with windows_io.open_write(root, path, parents=parents) as stream:
            yield stream
        return
    with _parent(root, path, create=parents) as (parent, name):
        descriptor = None
        caller_failed = False
        try:
            descriptor = os.open(
                name,
                os.O_WRONLY
                | os.O_CREAT
                | os.O_EXCL
                | os.O_NOFOLLOW
                | getattr(os, "O_CLOEXEC", 0),
                0o600,
                dir_fd=parent,
            )
            opened = os.fstat(descriptor)
            if not stat.S_ISREG(opened.st_mode) or opened.st_nlink != 1:
                raise SafeIOError("UNSAFE_PATH")
            os.fchmod(descriptor, 0o600)
            with io.FileIO(descriptor, "wb", closefd=False) as stream:
                try:
                    yield stream
                except BaseException:
                    caller_failed = True
                    raise
                stream.flush()
                os.fsync(descriptor)
                if _identity(os.fstat(descriptor)) != _identity(opened) or _identity(
                    os.stat(name, dir_fd=parent, follow_symlinks=False)
                ) != _identity(opened):
                    raise SafeIOError("SOURCE_CHANGED")
        except OSError as exc:
            if caller_failed:
                raise
            raise _error(exc) from None
        finally:
            if descriptor is not None:
                os.close(descriptor)


def make_directory(root, path, *, exclusive=False, parents=False):
    if sys.platform == "win32":
        from . import windows_io

        return windows_io.make_directory(root, path, exclusive=exclusive, parents=parents)
    with _parent(root, path, create=parents) as (parent, name):
        try:
            os.mkdir(name, 0o700, dir_fd=parent)
        except FileExistsError:
            if exclusive:
                raise SafeIOError("TARGET_EXISTS") from None
        descriptor = None
        try:
            descriptor = os.open(name, _directory_flags(), dir_fd=parent)
            os.fchmod(descriptor, 0o700)
        except OSError as exc:
            raise _error(exc) from None
        finally:
            if descriptor is not None:
                os.close(descriptor)


def unlink(root, path):
    if sys.platform == "win32":
        from . import windows_io

        return windows_io.unlink(root, path)
    with _parent(root, path) as (parent, name):
        os.unlink(name, dir_fd=parent)


def stat_file(root, path):
    if sys.platform == "win32":
        from . import windows_io

        return windows_io.stat_file(root, path)
    with _parent(root, path) as (parent, name):
        try:
            return os.stat(name, dir_fd=parent, follow_symlinks=False)
        except OSError as exc:
            raise _error(exc) from None


def atomic_write(root, path, data):
    """Replace a regular file through retained native directory descriptors."""
    if sys.platform == "win32":
        from . import windows_io

        return windows_io.atomic_write(root, path, data)
    path = _absolute(path)
    with _parent(root, path, create=True) as (parent, name):
        temporary = "." + uuid.uuid4().hex + ".tmp"
        descriptor = None
        created = False
        try:
            descriptor = os.open(
                temporary,
                os.O_WRONLY
                | os.O_CREAT
                | os.O_EXCL
                | os.O_NOFOLLOW
                | getattr(os, "O_CLOEXEC", 0),
                0o600,
                dir_fd=parent,
            )
            created = True
            temporary_identity = _identity(os.fstat(descriptor))
            os.fchmod(descriptor, 0o600)
            with io.FileIO(descriptor, "wb", closefd=False) as stream:
                if stream.write(data) != len(data):
                    raise SafeIOError("WRITE_FAILED")
                stream.flush()
                os.fsync(descriptor)
            with open_directory(root, path.parent) as current:
                if _identity(os.fstat(current)) != _identity(os.fstat(parent)):
                    raise SafeIOError("SOURCE_CHANGED")
                try:
                    existing = os.stat(name, dir_fd=parent, follow_symlinks=False)
                except FileNotFoundError:
                    existing = None
                if existing is not None and (
                    not stat.S_ISREG(existing.st_mode) or existing.st_nlink != 1
                ):
                    raise SafeIOError("UNSAFE_PATH")
                if (
                    _identity(os.fstat(descriptor)) != temporary_identity
                    or _identity(
                        os.stat(temporary, dir_fd=parent, follow_symlinks=False)
                    )
                    != temporary_identity
                ):
                    raise SafeIOError("SOURCE_CHANGED")
                os.replace(temporary, name, src_dir_fd=parent, dst_dir_fd=parent)
                created = False
                os.fsync(parent)
        except OSError as exc:
            raise _error(exc) from None
        finally:
            if descriptor is not None:
                os.close(descriptor)
            if created:
                try:
                    if (
                        _identity(
                            os.stat(temporary, dir_fd=parent, follow_symlinks=False)
                        )
                        == temporary_identity
                    ):
                        os.unlink(temporary, dir_fd=parent)
                except OSError:
                    pass


def publish_directory(root, source, target, *, expected_identity):
    """Publish the original prepared directory without replacing another entry."""
    if sys.platform == "win32":
        from . import windows_io

        return windows_io.publish_directory(root, source, target, expected_identity=expected_identity)
    source, target = _absolute(source), _absolute(target)
    if source.parent != target.parent:
        raise SafeIOError("UNSAFE_PATH")
    _supported()
    try:
        rename = ctypes.CDLL(None, use_errno=True).renameat2
    except (AttributeError, OSError):
        raise SafeIOError("SECURE_IO_UNAVAILABLE") from None
    rename.argtypes = [
        ctypes.c_int,
        ctypes.c_char_p,
        ctypes.c_int,
        ctypes.c_char_p,
        ctypes.c_uint,
    ]
    rename.restype = ctypes.c_int
    with _parent(root, target) as (parent, name):
        try:
            info = os.stat(source.name, dir_fd=parent, follow_symlinks=False)
            if (
                not stat.S_ISDIR(info.st_mode)
                or (info.st_dev, info.st_ino) != expected_identity
            ):
                raise SafeIOError("SOURCE_CHANGED")
            # Linux RENAME_NOREPLACE; never downgrade to an overwriting rename.
            if (
                rename(parent, os.fsencode(source.name), parent, os.fsencode(name), 1)
                != 0
            ):
                code = ctypes.get_errno()
                if code in (errno.ENOSYS, errno.EINVAL, errno.ENOTSUP):
                    raise SafeIOError("SECURE_IO_UNAVAILABLE")
                raise OSError(code, "Native directory publication refused")
            os.fsync(parent)
        except OSError as exc:
            raise _error(exc) from None


def remove_tree(root, path, *, expected_identity=None):
    if sys.platform == "win32":
        from . import windows_io

        return windows_io.remove_tree(root, path, expected_identity=expected_identity)
    if not getattr(shutil.rmtree, "avoids_symlink_attacks", False):
        raise SafeIOError("SECURE_IO_UNAVAILABLE")
    with _parent(root, path) as (parent, name):
        actual = os.stat(name, dir_fd=parent, follow_symlinks=False)
        if (
            not stat.S_ISDIR(actual.st_mode)
            or expected_identity is not None
            and (actual.st_dev, actual.st_ino) != expected_identity
        ):
            raise SafeIOError("SOURCE_CHANGED")
        shutil.rmtree(name, dir_fd=parent)


@contextmanager
def create_directory(root, path, *, parents=False):
    """Reserve a new directory and retain the acquired identity until exit."""
    if sys.platform == "win32":
        from . import windows_io

        with windows_io.create_directory(root, path, parents=parents) as anchor:
            yield anchor
        return
    with _parent(root, path, create=parents) as (parent, name):
        descriptor = None
        try:
            os.mkdir(name, 0o700, dir_fd=parent)
            expected = os.stat(name, dir_fd=parent, follow_symlinks=False)
            descriptor = os.open(name, _directory_flags(), dir_fd=parent)
            if _identity(os.fstat(descriptor)) != _identity(expected):
                raise SafeIOError("SOURCE_CHANGED")
            os.fchmod(descriptor, 0o700)
        except OSError as exc:
            if descriptor is not None:
                os.close(descriptor)
            raise _error(exc) from None
        try:
            yield AnchoredDirectory(_absolute(path), descriptor)
        finally:
            os.close(descriptor)


@contextmanager
def lock_directory(root):
    """Hold one native owner lock through the original acquired directory.

    LOCK_HELD is a contention result; unavailable primitives remain separate.
    Existing lock bytes are never written, truncated or used as authority.
    """
    if sys.platform == "win32":
        from . import windows_io

        with windows_io.lock_directory(root) as anchor:
            yield anchor
        return
    _supported()
    import fcntl

    path = _absolute(root.path if isinstance(root, AnchoredDirectory) else root)
    with _parent(root, path / "studio.lock") as (parent, name):
        descriptor, caller_failed = None, False
        try:
            if os.fstat(parent).st_uid != os.geteuid():
                raise SafeIOError("UNSAFE_PATH")
            flags = os.O_RDWR | os.O_NOFOLLOW | os.O_NONBLOCK | getattr(os, "O_CLOEXEC", 0)
            try:
                descriptor = os.open(name, flags | os.O_CREAT | os.O_EXCL, 0o600, dir_fd=parent)
            except FileExistsError:
                descriptor = os.open(name, flags, dir_fd=parent)

            def check():
                info = os.fstat(descriptor)
                named = os.stat(name, dir_fd=parent, follow_symlinks=False)
                if (
                    not stat.S_ISREG(info.st_mode)
                    or info.st_nlink != 1
                    or info.st_uid != os.geteuid()
                    or _identity(info) != _identity(named)
                ):
                    raise SafeIOError("UNSAFE_PATH")

            check()
            try:
                fcntl.flock(descriptor, fcntl.LOCK_EX | fcntl.LOCK_NB)
            except OSError as exc:
                if exc.errno in (errno.EAGAIN, errno.EWOULDBLOCK):
                    raise SafeIOError("LOCK_HELD") from None
                if exc.errno in (errno.ENOSYS, errno.ENOTSUP):
                    raise SafeIOError("SECURE_IO_UNAVAILABLE") from None
                raise
            check()
            # The selected data root becomes private only after this owner wins.
            # A refused contender must not alter the original owner's metadata.
            os.fchmod(parent, 0o700)
            try:
                yield AnchoredDirectory(path, parent)
            except BaseException:
                caller_failed = True
                raise
            check()
        except OSError as exc:
            if caller_failed:
                raise
            raise _error(exc) from None
        finally:
            if descriptor is not None:
                os.close(descriptor)
