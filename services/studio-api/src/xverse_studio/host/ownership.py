"""One native launcher or maintenance operation owns a private data root."""

from contextlib import contextmanager, ExitStack
from pathlib import Path

from xverse_studio.security.managed_io import (
    AnchoredDirectory,
    SafeIOError,
    create_directory,
    lock_directory,
    open_directory,
)


class RootOwnedError(OSError):
    pass


class RootUnsafeError(OSError):
    pass


@contextmanager
def _native_context(manager):
    caller_failed = False
    try:
        with manager as anchor:
            try:
                yield anchor
            except BaseException:
                caller_failed = True
                raise
    except SafeIOError as exc:
        if caller_failed:
            raise
        if exc.code == "LOCK_HELD":
            raise RootOwnedError("RECOVERY_ROOT_OWNED") from None
        code = (
            "RECOVERY_SECURE_IO_UNAVAILABLE"
            if exc.code == "SECURE_IO_UNAVAILABLE"
            else "RECOVERY_UNSAFE_FILE"
        )
        raise RootUnsafeError(code) from None


def own_root(root):
    """Return an ownership context pinned to a Path or existing directory anchor."""
    return _native_context(lock_directory(root))


@contextmanager
def _prepared_root(root):
    path = Path(root).absolute()
    with ExitStack() as resources:
        try:
            anchor = resources.enter_context(
                create_directory(Path(path.anchor), path, parents=True)
            )
        except SafeIOError as exc:
            if exc.code != "TARGET_EXISTS":
                raise
            descriptor = resources.enter_context(
                open_directory(Path(path.anchor), path)
            )
            anchor = AnchoredDirectory(path, descriptor)
        yield anchor


def prepare_root(root):
    """Create a private root or acquire the original existing directory, never resolve links."""
    return _native_context(_prepared_root(root))
