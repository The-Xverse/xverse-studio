"""Windows managed-file implementation. See ADR-0067 for verification limits."""

from contextlib import contextmanager, ExitStack
import io
import os
from pathlib import Path
import stat
import uuid

from .managed_io import AnchoredDirectory, SafeIOError, _error, _identity, _state
from .windows_native import native
from .windows_paths import absolute as windows_absolute


def _absolute(path):
    try:
        return Path(windows_absolute(path))
    except (TypeError, ValueError):
        raise SafeIOError("UNSAFE_PATH") from None


@contextmanager
def _owned(descriptor):
    try:
        yield descriptor
    finally:
        os.close(descriptor)


@contextmanager
def _errors():
    """Normalize acquisition errors without rewriting exceptions from callers."""
    try:
        yield
    except OSError as exc:
        raise _error(exc) from None


def _child(parent, name, *, create=False):
    api = native()
    if create:
        try:
            return api.acquire(parent, name, directory=True, create=True)
        except SafeIOError as exc:
            if exc.code != "TARGET_EXISTS":
                raise
    return api.acquire(parent, name, directory=True)


@contextmanager
def _directory(root, path, *, parents=False):
    # Keep every ancestor open: an unshared-delete handle pins its name against
    # replacement until the *whole* operation ends, including caller IO.
    with ExitStack() as stack:
        with _errors():
            anchor = root if isinstance(root, AnchoredDirectory) else None
            root_path, path = (
                _absolute(anchor.path if anchor else root),
                _absolute(path),
            )
            try:
                relative = path.relative_to(root_path)
            except ValueError:
                raise SafeIOError("UNSAFE_PATH") from None
            if anchor:
                descriptor = stack.enter_context(_owned(os.dup(anchor.descriptor)))
                native().checked(descriptor, directory=True)
            else:
                descriptor = stack.enter_context(
                    _owned(native().drive(root_path.anchor))
                )
                for name in root_path.parts[1:]:
                    descriptor = stack.enter_context(_owned(_child(descriptor, name)))
            for name in relative.parts:
                descriptor = stack.enter_context(
                    _owned(_child(descriptor, name, create=parents))
                )
        yield descriptor


@contextmanager
def _parent(root, path, *, parents=False):
    path = _absolute(path)
    root_path = _absolute(root.path if isinstance(root, AnchoredDirectory) else root)
    if path == root_path:
        raise SafeIOError("UNSAFE_PATH")
    with _directory(root, path.parent, parents=parents) as descriptor:
        yield descriptor, path.name


@contextmanager
def open_directory(root, path):
    with _directory(root, path) as descriptor:
        yield descriptor


@contextmanager
def open_read(root, path):
    with _parent(root, path) as (parent, name):
        with _errors():
            descriptor = native().acquire(parent, name, directory=False)
        with _owned(descriptor):
            with _errors():
                opened = native().checked(descriptor, directory=False)
                stream = io.FileIO(descriptor, "rb", closefd=False)
            with stream:
                yield stream
                with _errors():
                    if _state(native().checked(descriptor, directory=False)) != _state(
                        opened
                    ):
                        raise SafeIOError("SOURCE_CHANGED")


@contextmanager
def open_write(root, path, *, parents=False):
    with _parent(root, path, parents=parents) as (parent, name):
        with _errors():
            descriptor = native().acquire(
                parent, name, directory=False, create=True, writable=True
            )
        with _owned(descriptor):
            with _errors():
                opened = native().checked(descriptor, directory=False)
                stream = io.FileIO(descriptor, "wb", closefd=False)
            with stream:
                yield stream
                with _errors():
                    stream.flush()
                    os.fsync(descriptor)
                    if _identity(
                        native().checked(descriptor, directory=False)
                    ) != _identity(opened):
                        raise SafeIOError("SOURCE_CHANGED")


def make_directory(root, path, *, exclusive=False, parents=False):
    with _parent(root, path, parents=parents) as (parent, name), _errors():
        try:
            descriptor = native().acquire(parent, name, directory=True, create=True)
        except SafeIOError as exc:
            if exc.code != "TARGET_EXISTS" or exclusive:
                raise
            # Existing directories must already be private. Do not propagate an
            # inherited ACL rewrite through a potentially unrelated subtree.
            descriptor = native().acquire(parent, name, directory=True)
            with _owned(descriptor):
                native().verify_private(descriptor)
            return
        os.close(descriptor)


def stat_file(root, path):
    with _parent(root, path) as (parent, name), _errors():
        with _owned(native().acquire(parent, name)) as descriptor:
            return native().checked(descriptor)


def unlink(root, path):
    with _parent(root, path) as (parent, name), _errors():
        with _owned(
            native().acquire(parent, name, directory=False, delete=True)
        ) as descriptor:
            native().discard(descriptor)


def atomic_write(root, path, data):
    with _parent(root, path, parents=True) as (parent, name), _errors():
        temporary = "." + uuid.uuid4().hex + ".tmp"
        descriptor = native().acquire(
            parent, temporary, directory=False, create=True, writable=True, delete=True
        )
        with _owned(descriptor):
            published = False
            try:
                opened = native().checked(descriptor, directory=False)
                with io.FileIO(descriptor, "wb", closefd=False) as stream:
                    if stream.write(data) != len(data):
                        raise SafeIOError("WRITE_FAILED")
                    stream.flush()
                    os.fsync(descriptor)
                try:
                    existing = native().acquire(parent, name, directory=False)
                except SafeIOError as exc:
                    if exc.code != "FILE_MISSING":
                        raise
                else:
                    os.close(existing)
                if _identity(
                    native().checked(descriptor, directory=False)
                ) != _identity(opened):
                    raise SafeIOError("SOURCE_CHANGED")
                native().rename(descriptor, parent, name, replace=True)
                published = True
                # Flush the renamed file as well. Windows provides no equivalent
                # of the Linux unprivileged directory fsync contract here. Do not
                # claim volume-wide/power-loss durability or elevate privileges.
                os.fsync(descriptor)
            finally:
                if not published:
                    try:
                        native().discard(descriptor)
                    except OSError:
                        pass  # Preserve an uncertain temporary object for recovery.


def publish_directory(root, source, target, *, expected_identity):
    source, target = _absolute(source), _absolute(target)
    if source.parent != target.parent:
        raise SafeIOError("UNSAFE_PATH")
    with _parent(root, target) as (parent, name), _errors():
        with _owned(
            native().acquire(parent, source.name, directory=True, delete=True)
        ) as descriptor:
            info = native().checked(descriptor, directory=True)
            if (info.st_dev, info.st_ino) != expected_identity:
                raise SafeIOError("SOURCE_CHANGED")
            native().rename(descriptor, parent, name)


def remove_tree(root, path, *, expected_identity=None):
    remaining = 100_000

    def remove(descriptor, depth):
        nonlocal remaining
        if depth > 128:
            raise SafeIOError("LIMIT_EXCEEDED")
        # Capture names before deleting: mutating an in-flight enumeration can
        # omit entries. Each child is independently reacquired and validated.
        names = []
        for name in native().names(descriptor):
            remaining -= 1
            if remaining < 0:
                raise SafeIOError("LIMIT_EXCEEDED")
            names.append(name)
        for name in names:
            with _owned(native().acquire(descriptor, name, delete=True)) as child:
                if stat.S_ISDIR(native().checked(child).st_mode):
                    remove(child, depth + 1)
                else:
                    native().discard(child)
        native().discard(descriptor)

    with _parent(root, path) as (parent, name), _errors():
        with _owned(
            native().acquire(parent, name, directory=True, delete=True)
        ) as descriptor:
            info = native().checked(descriptor, directory=True)
            if (
                expected_identity is not None
                and (info.st_dev, info.st_ino) != expected_identity
            ):
                raise SafeIOError("SOURCE_CHANGED")
            remove(descriptor, 0)


@contextmanager
def create_directory(root, path, *, parents=False):
    with _parent(root, path, parents=parents) as (parent, name):
        with _errors():
            descriptor = native().acquire(parent, name, directory=True, create=True)
        with _owned(descriptor):
            yield AnchoredDirectory(_absolute(path), descriptor)
